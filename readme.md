## Intro

Heartbeat contains two components:

- heartbeat_agent polls urls on the internet and produces results to Kafka.
- heartbeat_exporter reads the same Kafka and exports the messages to PostgreSQL.

## Requirements

Works at least on Python 3.8. Possibly also on 3.7.

## Configuration

Some manual configuration is required.

1. Create directory for kafka configuration. To be able to run tests, name it "kafka_conf" and put it in repository root. It should contain:
- kafka_url.txt : Url to the Kafka instance. Format "<host>:<port>"
- ca.pem : CA file to use.
- service.cert : Client certificate to use.
- service.key : Client certificate private key.

2. Create a similar directory for psql configuration called "psql_conf" and put it in repository root. It should contain:
- psql_uri.txt : Uri to PostgreSQL instance to use. Format "postgres://<username>:<password>@<host>:<port>/defaultdb?sslmode=require"
- ca.pem : CA file to use.

3. Configuration for services to poll is found in heartbeat_agent/heartbeat_agent/conf/services.json.

## Deployment

Repository contains `tool.sh` but it does not work as it should.

`tool.sh setup` setups a virtualenv.
`tool.sh build` creates wheels from the components.
`tool.sh test` runs pytest. Exporter unit test does not work.
`tool.sh style-analysis` is unimplemented. Should run flake8 or other python static analysis tool.
`tool.sh install_agent` and `tool.sh install_agent` install the respective wheels in the current virtualenv. However, running the installed wheels does not work currently.

To run the components manually, run in repo root:
`
python heartbeat_agent/heartbeat_agent.py --kafka_conf=../../kafka_conf
python heartbeat_exporter/heartbeat_exporter.py --kafka_conf=../../kafka_conf --psql_conf=../../psql_conf
`

To run the end-to-end test manually, run in test/:
`
python heartbeat_e2e_test.py
`

## TODO
- Wheels installed using `tool.sh install_` do not work.
- Exporter unit test using `tool.sh test` also does not work. Other tests do.
- Flake8 static analysis integration.
- Configuration is clunky.