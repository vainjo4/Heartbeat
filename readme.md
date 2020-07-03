## Intro

Heartbeat contains two components:

- `heartbeat_agent` polls urls on the internet and produces results to Kafka.
- `heartbeat_exporter` reads the same Kafka and exports the messages to PostgreSQL.

## Requirements

Works at least on Python 3.8. Possibly also on 3.7. Has been tested on Ubuntu 20.04 LTS (Windows Subsystem for Linux).

## Configuration

Some manual configuration is required.

1. Create directory for kafka configuration. To be able to run tests, name it `kafka_conf` and put it in repository root. It should contain:
- `kafka_url.txt` : Url to the Kafka instance. Format `[host]:[port]`
- `ca.pem` : CA file to use.
- `service.cert` : Client certificate to use.
- `service.key` : Client certificate private key.

2. Create a similar directory for psql configuration called `psql_conf` and put it in repository root. It should contain:
- `psql_uri.txt` : Uri to PostgreSQL instance to use. Format `postgres://[username]:[password]@[host]:[port]/defaultdb?sslmode=require`
- `ca.pem` : CA file to use.

3. Configuration for services to poll is found in `heartbeat_agent/heartbeat_agent/conf/services.json`.

## Building & Testing

Repository contains `tool.sh`. Commands can't be chained.

- `bash tool.sh setup` setups a virtualenv at `test/venv` needed by the script.
- `bash tool.sh build` creates wheels from the components.
- `bash tool.sh test` runs pytest on the repo.
- `bash tool.sh style-analysis` is unimplemented. Should run flake8 or other python static analysis tool.
- `bash tool.sh install_agent`  installs the respective wheel in the `test/venv` virtualenv.
- `bash tool.sh install_exporter` installs the respective wheel in the `test/venv` virtualenv.


Note that having the wheels installed may cause name conflicts with the tests.


To run the installed components, activate the virtualenv created by `tool.sh` in `test/venv` and run:
`
heartbeat_agent --kafka_conf=[path_to_kafka_conf]
`

`
heartbeat_exporter --kafka_conf=[path_to_kafka_conf] --psql_conf=[path_to_psql_conf]
`


#### Manual running

In case the install goes wrong and you need to run the components manually, run in repo root:

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

The wheels created by `tool.sh build` can be installed normally using `pip`.


Kafka and PSQL configuration need to be manually handled. More automation is TODO.


## TODO
- Exporter unit test does not work when using `tool.sh test`; other tests work.
- Flake8 static analysis integration.
- Configuration is clunky. Should add option to pass new services.json on command line.
- Next level: manage Kafka and PSQL configuration automatically