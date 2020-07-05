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
logging.basicConfig(level=logging.INFO,
                    format="[%(asctime)s] [%(levelname)s] - %(message)s")


def test_e2e():
    logging.info("e2e_test")

    config = configparser.ConfigParser()
    exporter_test_configuration_file =
        os.path.join(current_dir, "heartbeat_exporter_test.cfg")
    config.read(exporter_test_configuration_file)
    database_table_name = config["heartbeat_exporter"]["database_table_name"]

    psql_conf_dir = os.path.join(current_dir, "..", "psql_conf")
    psql_urifile_path = os.path.join(psql_conf_dir, "psql_uri.txt")
    psql_cafile_path = os.path.join(psql_conf_dir, "ca.pem")

    heartbeat_agent_dir =
        os.path.join(current_dir, "..",
                     "heartbeat_agent", "heartbeat_agent")

    heartbeat_exporter_dir =
        os.path.join(current_dir, "..",
                     "heartbeat_exporter", "heartbeat_exporter")

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

        agent_path =
            os.path.join(heartbeat_agent_dir, "heartbeat_agent.py")
        agent_config_path =
            os.path.join(current_dir, "heartbeat_agent_test.cfg")

        agent_args =
            [sys.executable, agent_path, "--config", agent_config_path]

        agent_proc = subprocess.Popen(agent_args)
        time.sleep(5)
        agent_proc.kill()

        exporter_path =
            os.path.join(heartbeat_exporter_dir, "heartbeat_exporter.py")
        exporter_config_path =
            os.path.join(current_dir, "heartbeat_exporter_test.cfg")

        logging.info("Starting exporter ...")
        exporter_args =
            [sys.executable, exporter_path, "--config", exporter_config_path]
        exporter_proc = subprocess.Popen(exporter_args)

        time.sleep(10)
        exporter_proc.kill()

        cursor.execute("SELECT * FROM " + database_table_name + ";")
        heartbeat_rows = cursor.fetchall()
        heartbeat_rows = [hb for hb in heartbeat_rows if
                          hb["timestamp"] > time_at_test_start]

        assert len(heartbeat_rows) == 3

        heartbeat_rows_xkcd = [hb for hb in heartbeat_rows if
                               hb["service_url"] == "https://xkcd.com/"]

        assert len(heartbeat_rows_xkcd) == 2
        assert heartbeat_rows_xkcd[0]["status_code"] == 200
        assert 10 < heartbeat_rows_xkcd[0]["response_time_millis"] < 1000
        assert heartbeat_rows_xkcd[0]["regex_match"] is None
        assert heartbeat_rows_xkcd[1]["status_code"] == 200
        assert 10 < heartbeat_rows_xkcd[1]["response_time_millis"] < 1000
        assert heartbeat_rows_xkcd[1]["regex_match"] is None

        heartbeat_rows_example = [hb for hb in heartbeat_rows if
                                  hb["service_url"] == "https://example.com"]

        assert len(heartbeat_rows_example) == 1
        assert heartbeat_rows_example[0]["status_code"] == 200
        assert 10 < heartbeat_rows_example[0]["response_time_millis"] < 1000
        assert heartbeat_rows_example[0]["regex_match"] is True

        logging.info("e2e_test done")


if __name__ == "__main__":
    test_e2e()
