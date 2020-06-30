import asyncio
import configparser
import datetime
import logging
import os
import sys
import subprocess
import time

import psycopg2
from psycopg2.extras import RealDictCursor


current_dir = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] - %(message)s")


if len(sys.argv) > 1:
    python_to_use = sys.argv[1]
else:
    python_to_use = "../venv/Scripts/python"


def test_e2e():
    logging.info("e2e_test")

    config = configparser.ConfigParser()
    configuration_file = "heartbeat_exporter_test.cfg"
    config.read(configuration_file)

    database_table_name = config["heartbeat-exporter"]["database_table_name"]

    psql_conf_dir = os.path.join(current_dir, "..", "psql_conf")
    psql_urifile_path = os.path.join(psql_conf_dir, "psql_uri.txt")
    psql_cafile_path = os.path.join(psql_conf_dir, "ca.pem")

    heartbeat_agent_dir = os.path.join(current_dir, "..", "heartbeat_agent")
    heartbeat_exporter_dir = os.path.join(current_dir, "..", "heartbeat_exporter")

    def get_psql_uri():
        with open(psql_urifile_path, "r") as file:
            return file.read().strip()

    psql_uri = get_psql_uri()

    with (psycopg2.connect(psql_uri)) as db_conn:
        db_conn.autocommit = True
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)

        logging.info("Emptying DB table " + database_table_name)
        cursor.execute("DELETE FROM " + database_table_name + ";")

        logging.info("Starting agent ...")
        time_at_test_start = datetime.datetime.now(datetime.timezone.utc)

        agent_args = [python_to_use, os.path.join(heartbeat_agent_dir, "heartbeat_agent.py"), os.path.join(current_dir, "heartbeat_agent_test.cfg")]
        agent_proc = subprocess.Popen(agent_args)
        time.sleep(5)
        agent_proc.kill()

        logging.info("Starting exporter ...")
        exporter_args = [python_to_use, os.path.join(heartbeat_exporter_dir, "heartbeat_exporter.py"), os.path.join(current_dir, "heartbeat_exporter_test.cfg")]
        exporter_proc = subprocess.Popen(exporter_args)

        time.sleep(10)
        exporter_proc.kill()

        cursor.execute("SELECT * FROM " + database_table_name + ";")
        heartbeat_rows = cursor.fetchall()
        heartbeat_rows = [ hb for hb in heartbeat_rows if hb["timestamp"] > time_at_test_start ]

        assert len(heartbeat_rows) == 3

        assert heartbeat_rows[0]["service_url"] == "https://xkcd.com/"
        assert heartbeat_rows[0]["status_code"] == 200
        assert 10 < heartbeat_rows[0]["response_time_millis"] < 1000
        assert heartbeat_rows[0]["regex_match"] == None

        assert heartbeat_rows[1]["service_url"] == "https://example.com"
        assert heartbeat_rows[1]["status_code"] == 200
        assert 10 < heartbeat_rows[1]["response_time_millis"] < 1000
        assert heartbeat_rows[1]["regex_match"] == True

        assert heartbeat_rows[2]["service_url"] == "https://xkcd.com/"
        assert heartbeat_rows[2]["status_code"] == 200
        assert 10 < heartbeat_rows[2]["response_time_millis"] < 1000
        assert heartbeat_rows[2]["regex_match"] == None

if __name__ == "__main__":
    test_e2e()

