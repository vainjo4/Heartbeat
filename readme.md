## Intro

Heartbeat contains two components:

- `heartbeat_agent` polls urls on the internet and produces results to Kafka.
- `heartbeat_exporter` reads the same Kafka and exports the messages to PostgreSQL.

## Requirements

Works at least with Python 3.8 and Pip 20.0.02. Possibly also on Python 3.7.


Has been tested on Ubuntu 20.04 LTS (Windows Subsystem for Linux).


## Configuration

Some manual configuration is required.

1. Create a directory for kafka configuration. To be able to run tests, name it `kafka_conf` and put it in repository root. It should contain:
- `kafka_url.txt` : Url to the Kafka instance. Format `[host]:[port]`
- `ca.pem` : CA file to use.
- `service.cert` : Client certificate to use.
- `service.key` : Client certificate private key.

2. Create another directory for psql configuration. To be able to run tests, name it `psql_conf` and put it in repository root. It should contain:
- `psql_uri.txt` : Uri to PostgreSQL instance to use. Format `postgres://[username]:[password]@[host]:[port]/defaultdb?sslmode=require`
- `ca.pem` : CA file to use.

3. A default configuration file for services to poll is found in `heartbeat_agent/heartbeat_agent/conf/services.json`.
To configure the services to poll, write a valid json file in similar format to pass to the agent.

## Building & Testing

Repository contains `tool.sh`. Commands can't be chained.

- `bash tool.sh setup` setups a virtualenv at `test/venv` needed by the script.
- `bash tool.sh build` creates wheels from the components.
- `bash tool.sh test` runs the tests. Produces a report in xUnit format.
- `bash tool.sh style-analysis` runs style analysis on the repo. Produces a report.
- `bash tool.sh install_agent`  installs the respective wheel in the `test/venv` virtualenv.
- `bash tool.sh install_exporter` installs the respective wheel in the `test/venv` virtualenv.


Note that having the wheels installed may cause name conflicts with the tests.


To run the installed components, activate the virtualenv created by `tool.sh` in `test/venv` and run:
`
heartbeat_agent --kafka_conf=[path to kafka_conf] --services_json=[optional; path to custom polling configuration]
`

`
heartbeat_exporter --kafka_conf=[path_to_kafka_conf] --psql_conf=[path_to_psql_conf]
`


#### Manual running

In case the install goes wrong and you need to run the components manually, you can run in repo root:

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


Kafka and PSQL configuration need to be manually handled, and passed to the binary as command line arguments. More automation is TODO.


Systemd service files are TODO.


## TODO
- Configuration is clunky. Should be able to overwrite any setting from the command line without hardcoding each option.
- Systemd service files, for smoother running in production.
- Logging configuration (minimum: log to a rolling file).
- Next level: Fetch Kafka and PSQL configuration from the service provider.