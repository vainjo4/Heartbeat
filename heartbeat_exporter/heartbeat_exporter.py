import configparser
import json
import logging
import os
import sys
import time
import re

from kafka import KafkaConsumer
import psycopg2
from psycopg2.extras import RealDictCursor

current_dir = os.path.dirname(os.path.realpath(__file__))

config = configparser.ConfigParser()
configuration_file = sys.argv[1] if len(sys.argv) > 1 else os.path.join(current_dir, "conf", "heartbeat_agent.cfg")
config.read(configuration_file)

kafka_conf_dir = os.path.join(current_dir, config["heartbeat-exporter"]["kafka_conf_dir"])
psql_conf_dir = os.path.join(current_dir, config["heartbeat-exporter"]["psql_conf_dir"])

topic_name = config["heartbeat-exporter"]["topic_name"]
database_table_name = config["heartbeat-exporter"]["database_table_name"]

kafka_consumer_timeout_millis = int(config["heartbeat-exporter"]["kafka_consumer_timeout_millis"])
kafka_client_id = config["heartbeat-exporter"]["kafka_client_id"]
kafka_group_id = config["heartbeat-exporter"]["kafka_group_id"]
kafka_auto_offset_reset = config["heartbeat-exporter"]["kafka_auto_offset_reset"]
kafka_security_protocol = config["heartbeat-exporter"]["kafka_security_protocol"]

kafka_urlfile_path = os.path.join(kafka_conf_dir, "kafka_url.txt")
kafka_cafile_path = os.path.join(kafka_conf_dir, "ca.pem")
kafka_certfile_path = os.path.join(kafka_conf_dir, "service.cert")
kafka_keyfile_path = os.path.join(kafka_conf_dir, "service.key")
psql_urifile_path = os.path.join(psql_conf_dir, "psql_uri.txt")
psql_cafile_path = os.path.join(psql_conf_dir, "ca.pem")

keep_running = True

def get_kafka_url():
    with open(kafka_urlfile_path, "r") as file:
        return file.read().strip()

def get_psql_uri():
    with open(psql_urifile_path, "r") as file:
        return file.read().strip()

kafka_url = get_kafka_url()
psql_uri = get_psql_uri()      

console = logging.StreamHandler()
console.setLevel(logging.INFO)

def init_kafka_consumer():
    logging.info("init_kafka_consumer ...")
    return KafkaConsumer(
        topic_name,
        enable_auto_commit=True,
        auto_offset_reset=kafka_auto_offset_reset,
        bootstrap_servers=kafka_url,
        client_id=kafka_client_id,
        group_id=kafka_group_id,        
        security_protocol=kafka_security_protocol,
        ssl_cafile=kafka_cafile_path,
        ssl_certfile=kafka_certfile_path,
        ssl_keyfile=kafka_keyfile_path
    )
    logging.info("init_kafka_consumer done")

def init_db(cursor):  
    logging.info("init_db ...")
    table_schema = """
      service_url varchar NOT NULL,
      timestamp timestamptz NOT NULL,
      response_time_millis integer,
      status_code integer,
      regex_match boolean,
      PRIMARY KEY(service_url, timestamp)
    """

    creation_sql = "CREATE TABLE IF NOT EXISTS " + database_table_name + " (" + table_schema + ");"
    cursor.execute(creation_sql);
    logging.info("init_db done")
    
def write_heartbeat_to_db(cursor, heartbeat_as_dict):
    logging.info("write_heartbeat_to_db: " + str(heartbeat_as_dict))
    
    ####
    print("Writing to DB: " + str(heartbeat_as_dict))    
    val = cursor.execute("SELECT COUNT(*) FROM " + database_table_name + ";")
    row = cursor.fetchone()
    print(str(row))
    ####
    
    service_url          = heartbeat_as_dict["service_url"]
    timestamp            = heartbeat_as_dict["timestamp"]
    response_time_millis = heartbeat_as_dict["response_time_millis"]
    status_code          = heartbeat_as_dict["status_code"]
    regex_match          = heartbeat_as_dict["regex_match"]

    cursor.execute("INSERT INTO " + database_table_name + " (service_url, timestamp, response_time_millis, status_code, regex_match) " + \
               "VALUES(%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING;", (service_url, timestamp, response_time_millis, status_code, regex_match))

def run():

    # allowed characters: alphanumeric and underscore
    database_name_regex = re.compile("[\\w_]")
    assert database_name_regex.match(database_table_name)

    logging.info(str(sys.argv[0]) + " started")
    with (psycopg2.connect(psql_uri)) as db_conn:
        db_conn.autocommit = True
        cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        init_db(cursor)
   
        consumer = init_kafka_consumer()
        logging.info("Begin Kafka polling loop")
        while keep_running:
            raw_msgs = consumer.poll(timeout_ms=kafka_consumer_timeout_millis)        
            for topic, msgs in raw_msgs.items():
                for msg in msgs:
                    print(str(msg))
                    heartbeat = json.loads(msg.value)
                    write_heartbeat_to_db(cursor, heartbeat)

if __name__ == "__main__":
    run()
