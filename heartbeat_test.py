import psycopg2
from psycopg2.extras import RealDictCursor

import asyncio
import sys
import time
import subprocess
import os

def test_e2e():
    print("e2e_test")

    
    psql_conf_dir = "psql_conf"
    psql_urifile_path = os.path.join(psql_conf_dir, "psql_uri.txt")
    psql_cafile_path = os.path.join(psql_conf_dir, "ca.pem")

    def get_psql_uri():
        with open(psql_urifile_path, "r") as file:
            return file.read().strip()

    psql_uri = get_psql_uri()    
    print(psql_uri)
    
    with (psycopg2.connect(psql_uri)) as db_conn:
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("SELECT COUNT(*) FROM heartbeat;")        
        count_before = cursor.fetchone()["count"]
        print("count_before: " + str(count_before))
        
        print("Starting agent ...")
        
        agent_args = ["venv\\Scripts\\python", "heartbeat_agent\\heartbeat_agent.py", ".\\kafka_conf", "heartbeat-1", ".\\testservices.json"]
        agent_cwd = ""    
        agent_proc = subprocess.Popen(agent_args)    
        time.sleep(10)
        agent_proc.kill()
        
        print("Starting exporter ...")

        exporter_args = ["venv\\Scripts\\python", "heartbeat_exporter\\heartbeat_exporter.py", ".\\kafka_conf", ".\\psql_conf", "heartbeat-1"]
        exporter_cwd = "heartbeat_exporter"    
        exporter_proc = subprocess.Popen(exporter_args)    
        
        time.sleep(10)
        exporter_proc.kill()
        
        cursor.execute("SELECT COUNT(*) FROM heartbeat;")        
        count_after = cursor.fetchone()["count"]
        print("count_before: " + str(count_before))
        print("count_after: " + str(count_after))       
        assert count_after == count_before + 3
       
if __name__ == "__main__":
    test_e2e()
