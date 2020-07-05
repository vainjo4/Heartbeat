## Intro

Heartbeat contains two components:

- `heartbeat_agent` polls urls on the internet and produces results to Kafka based on responses.
- `heartbeat_exporter` reads the same Kafka and exports the messages to PostgreSQL.

## Requirements

Works at least with Python 3.8 and Pip 20.0.02. Possibly also on Python 3.7.


Has been tested on Ubuntu 20.04 LTS (Windows Subsystem for Linux).


## Configuration

Some manual steps are required.


NOTE: If you are running your services on Aiven, you can use the utility script `scripts/create_conf_dirs.py` to generate the directories in 1) and 2) using the Aiven API.


1. Create a directory for kafka configuration. To be able to run tests, name it `kafka_conf` and put it in repository root. It should contain:
- `kafka_url.txt` : Url to the Kafka instance. Format `[host]:[port]`
- `ca.pem` : CA file to use.
- `service.cert` : Client certificate to use.
- `service.key` : Client certificate private key.


2. Create another directory for psql configuration. To be able to run tests, name it `psql_conf` and put it in repository root. It should contain:
- `psql_uri.txt` : Uri to PostgreSQL instance to use. Format `postgres://[username]:[password]@[host]:[port]/defaultdb?sslmode=require`
- `ca.pem` : CA file to use.


3. A default configuration file for services to poll is found in `heartbeat_agent/heartbeat_agent/conf/services.json`.
To configure the services to poll, write a valid json file in similar format, and pass it to the agent as `--services_json` parameter.


4. Kafka topics should exist; automatic creation is TODO. Default topics used are `heartbeat-1` and for tests `heartbeat-test`.


## Building & Testing

Repository contains `tool.sh`. Commands can't be chained.

- `bash tool.sh setup` setups a virtualenv at `test/venv` needed by the script.
- `bash tool.sh build` creates wheels from the components.
- `bash tool.sh test` runs the tests. Produces a report in xUnit format.
- `bash tool.sh style-analysis` runs style analysis on the repo. Produces a report.
- `bash tool.sh install_agent`  installs the respective wheel in the local `test/venv` virtualenv.
- `bash tool.sh install_exporter` installs the respective wheel in the local `test/venv` virtualenv.


Note that having the wheels installed may cause name conflicts with the tests.


To run the locally installed components, activate the virtualenv created by `tool.sh` in `test/venv` and run:
`
source test/venv/bin/activate
heartbeat_agent --kafka_conf=[path to kafka_conf] --services_json=[optional; path to custom polling configuration]
`

`
source test/venv/bin/activate
heartbeat_exporter --kafka_conf=[path_to_kafka_conf] --psql_conf=[path_to_psql_conf]
`


#### Manual running

In case the install goes wrong for any reason and you want to run the components from source, you can run in repo root:

`
python heartbeat_agent/heartbeat_agent.py --kafka_conf=../../kafka_conf
`

`
python heartbeat_exporter/heartbeat_exporter.py --kafka_conf=../../kafka_conf --psql_conf=../../psql_conf
`

To run the end-to-end test manually, run in `test/`:

`
python heartbeat_e2e_test.py
`

## Deployment

The wheels created by `tool.sh build` can be installed normally using `pip` anywhere with correct python and pip versions.


Kafka and PSQL configuration need to be passed to the binary as command line arguments.
If your services are on Aiven, you can use `create_conf_dirs.py` to generate the directories.


To get the services running on a new machine, first run
`
python create_conf_dirs.py <aiven_email> <aiven_password> <project_name> <postgresql_service_name> <kafka_service_name>
`
and then respectively either
`
rm -rf psql_conf
pip install <agent_wheel.whl>
heartbeat_agent --kafka_conf=kafka_conf
`
or
`
pip install <exporter_wheel.whl>
heartbeat_exporter --kafka_conf=kafka_conf --psql_conf=psql_conf
`


Systemd service files are a priority TODO.


One-click packaging and deployment scripts are TODO.


## TODO
- Systemd service files, for simpler running in production.
- Logging configuration (at minimum: log to a rolling file).
- Deployment script
- Configuration is clunky. Should be able to overwrite any setting from the command line without hardcoding each option.
- More 'unit' tests, especially for exporter (e.g. DB table creation).
- CI integration: parse the test and style analysis reports; produce the wheels as artifacts.
- Automatic Kafka topic creation.
