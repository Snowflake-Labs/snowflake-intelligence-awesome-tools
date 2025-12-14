CREATE OR REPLACE PROCEDURE "CORTEX_AGENT_RUN"("DB_NAME" VARCHAR, "SCHEMA_NAME" VARCHAR, "AGENT_NAME" VARCHAR, "PROMPT" VARCHAR, "API_TIMEOUT" NUMBER(38,0) DEFAULT 50000, "AGENT_RESPONSE_ONLY" BOOLEAN DEFAULT TRUE)
RETURNS STRING
LANGUAGE PYTHON
RUNTIME_VERSION = '3.12'
PACKAGES = ('snowflake-snowpark-python')
HANDLER = 'cortex_agent_run'
EXECUTE AS OWNER
AS '
import json
import logging
import _snowflake

logger = logging.getLogger("cortex_agent_run")
logger.setLevel(logging.ERROR)

def _is_sql_null(x):
    """
    Snowflake represents SQL NULL as an internal wrapper type.
    """
    return type(x).__name__ == "sqlNullWrapper"

def _parse_events(content_bytes):
    """
    Agents run API returns a line-delimited JSON (event stream).
    parsing it and extract the final text, while also allowing streaming deltas.
    """
    if content_bytes is None:
        return {"text": "", "events": []}

    if isinstance(content_bytes, (bytes, bytearray)):
        try:
            s = content_bytes.decode("utf-8", errors="ignore")
        except Exception:
            s = str(content_bytes)
    elif isinstance(content_bytes, str):
        s = content_bytes
    else:
        # Last resort
        s = str(content_bytes)

    events = []
    text = ""
    # Try to load as a JSON array first; if that fails, fall back to ndjson
    try:
        maybe_list = json.loads(s)
        if isinstance(maybe_list, list):
            events = maybe_list
        else:
            events = [maybe_list]
    except Exception:
        # ndjson: one JSON obj per line
        for line in s.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except Exception:
                # ignore bad lines
                pass

    for ev in events:
        ev_type = ev.get("event")
        if ev_type == "response.text":
            text = ev.get("data", {}).get("text", "") or text
        elif ev_type == "response.text.delta":
            delta = ev.get("data", {}).get("delta", {})
            piece = delta.get("text", "")
            if piece:
                text += piece

    return {"text": text, "events": events}

def _send_api_request(method, api_endpoint, payload, api_timeout):
    """
    Send a request to the Snowflake API using built in method.
    """
    resp = _snowflake.send_snow_api_request(
        method,
        api_endpoint,
        {},    # headers
        {},    # params
        payload,
        None,  # files
        int(api_timeout) if api_timeout is not None else 50000
    )
    return resp

def cortex_agent_run(db_name: str, schema_name: str, agent_name: str, prompt: str, 
                     api_timeout: int = 50000, agent_response_only: bool = False):
    """
    Run a Cortex Agent with the given prompt and optional tool choice. 
    """
    api_endpoint = f"/api/v2/databases/{db_name}/schemas/{schema_name}/agents/{agent_name}:run"

    payload = {
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}]
            }
        ]
    }

    resp = None
    try:
        resp = _send_api_request(
            "POST",
            api_endpoint,
            payload,
            int(api_timeout) if api_timeout is not None else 50000
        )

        status = resp.get("status")
        if status != 200:
            # Avoid f-string key with double quotes bug and keep it simple
            logger.error(f"API call failed with status {status}")
            return {
                "ok": False,
                "status": status,
                "response": resp,
                "payload": payload,
                "api_endpoint": api_endpoint
            }

        # Parse content safely
        content = resp.get("content")
        parsed = _parse_events(content)

        if agent_response_only:
            return parsed.get("text", "") or "No response returned by the agent."
        else:
            return {
                "ok": True,
                "status": status,
                "agent_response": parsed.get("text", "") or "No response returned by the agent.",
                "response.events": parsed.get("events", []),
            }

    except Exception as e:
        # Do NOT reference resp if it is still None
        status = resp.get("status") if isinstance(resp, dict) else None
        logger.error(f"Exception during API call: {str(e)}")
        return {
            "ok": False,
            "status": status,
            "response": resp,
            "payload": payload,
            "api_endpoint": api_endpoint
        }
';