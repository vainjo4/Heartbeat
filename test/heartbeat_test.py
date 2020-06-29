import psycopg2
from psycopg2.extras import RealDictCursor

import configparser
import asyncio
import sys
import time
import subprocess
import os

current_dir = os.path.dirname(os.path.realpath(__file__))

if len(sys.argv) > 1:
    python_to_use = sys.argv[1]    
else:
    python_to_use = "..\\venv\\Scripts\\python"

def test_e2e():
    print("e2e_test")

    database_table_name = "heartbeat_test"

    config = configparser.ConfigParser()
    configuration_file = "heartbeat_exporter_test.cfg"
    config.read(configuration_file)

    psql_conf_dir = os.path.join(current_dir, "..", "psql_conf")
    psql_urifile_path = os.path.join(psql_conf_dir, "psql_uri.txt")
    psql_cafile_path = os.path.join(psql_conf_dir, "ca.pem")
    
    heartbeat_agent_dir = os.path.join(current_dir, "..", "heartbeat_agent")
    heartbeat_exporter_dir = os.path.join(current_dir, "..", "heartbeat_exporter")

    def get_psql_uri():
        with open(psql_urifile_path, "r") as file:
            return file.read().strip()

    psql_uri = get_psql_uri()    
    print(psql_uri)
    
    with (psycopg2.connect(psql_uri)) as db_conn:
        db_conn.autocommit = True
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("DELETE FROM " + database_table_name + ";")
        cursor.execute("SELECT COUNT(*) FROM " + database_table_name + ";")
        
        count_before = cursor.fetchone()["count"]
        print("count_before: " + str(count_before))
        
        print("Starting agent ...")
        agent_args = [python_to_use, os.path.join(heartbeat_agent_dir, "heartbeat_agent.py"), os.path.join(current_dir, "heartbeat_agent_test.cfg")]
        agent_proc = subprocess.Popen(agent_args)
        time.sleep(5)
        agent_proc.kill()

        print("Starting exporter ...")

        exporter_args = [python_to_use, os.path.join(heartbeat_exporter_dir, "heartbeat_exporter.py"), os.path.join(current_dir, "heartbeat_exporter_test.cfg")]
        exporter_proc = subprocess.Popen(exporter_args)    
        
        time.sleep(5)
        exporter_proc.kill()
        
        cursor.execute("SELECT COUNT(*) FROM " + database_table_name + ";")        
        
        count_after = cursor.fetchone()["count"]
        
        print("count_before: " + str(count_before))
        print("count_after: " + str(count_after))       
        assert count_before == 0
        assert count_after == 2
       
if __name__ == "__main__":
    test_e2e()

