CREATE COMPUTE POOL compute_pool
  MIN_NODES = 1
  MAX_NODES = 1
  INSTANCE_FAMILY = CPU_X64_XS
  AUTO_RESUME = TRUE;

CREATE IMAGE REPOSITORY images;

SHOW IMAGE REPOSTORIES;

-- copy the `repository_url`

-- Clone the code locally, navigate to the `python_sandbox` directory, and run the following command:

-- docker build --platform linux/amd64 -t <repository_url>/python_sandbox
-- snow spcs image-registry login -c <name-of-connection-in-config.toml>
-- docker push <repository_url>/python_sandbox


-- replace the <values> with your own
CREATE SERVICE python_executor
  IN COMPUTE POOL compute_pool
  FROM SPECIFICATION $$
    spec:
      containers:
      - name: python-executor
        image: /<database>/<schema>/<image_repository>/python_executor:latest
      endpoints:
      - name: execute
        port: 8080
        public: true
  $$
  MIN_INSTANCES=1
  MAX_INSTANCES=1;

CREATE FUNCTION execute_python (PythonScript varchar)
  RETURNS object
  SERVICE=python_executor
  ENDPOINT=execute
  AS '/execute';