import psycopg2
import time
from kafka import KafkaConsumer
from psycopg2.extras import RealDictCursor
import sys

kafka_conf_dir = sys.argv[1] #"../kafka_conf" 
psql_conf_dir = sys.argv[2] #"../psql_conf" 
topic_name = sys.argv[3] # "heartbeat-1"

kafka_urlfile_path = os.path.join(kafka_conf_dir, "kafka_url.txt")
kafka_cafile_path = os.path.join(kafka_conf_dir, "ca.pem")
kafka_certfile_path = os.path.join(kafka_conf_dir, "service.cert")
kafka_keyfile_path = os.path.join(kafka_conf_dir, "service.key")

psql_urifile_path = os.path.join(kafka_conf_dir, "psql_uri.txt")
psql_cafile_path = os.path.join(psql_conf_dir, "ca.pem")

def get_kafka_url():
	with open(kafka_urlfile_path, "r") as file:
		return file.readlines().strip()

def get_psql_uri():
	with open(psql_urifile_path, "r") as file:
		return file.readlines().strip()
		
kafka_url = get_kafka_url()
psql_uri = get_psql_uri()

kafka_client_id = "heartbeat-client-1"
kafka_group_id = "heartbeat-group"
kafka_auto_offset_reset = "earliest"
kafka_security_protocol = "SSL"

keep_running = True

def init_kafka_consumer():
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
		ssl_keyfile=kafka_keyfile_path,
	)

def init_db(cursor):  
	table_schema = """
	  service_url varchar NOT NULL,
	  service_port integer NOT NULL,
	  timestamp timestamptz NOT NULL,
	  response_time_millis integer,
	  status_code integer,
	  regex_match boolean
	  PRIMARY KEY(service_url, service_port, timestamp)
	"""

	creation_sql = "CREATE TABLE heartbeat IF NOT EXISTS (" + table_schema + ");"
	cursor.execute(creation_sql);
	
def write_heartbeat(cursor, heartbeat_as_dict):
    service_url          = heartbeat_as_dict["service_url"]
	service_port         = heartbeat_as_dict["service_port"]
	timestamp            = heartbeat_as_dict["timestamp"]
	response_time_millis = heartbeat_as_dict["response_time_millis"]
	status_code          = heartbeat_as_dict["status_code"]
	regex_match          = heartbeat_as_dict["regex_match"]

	cursor.execute("INSERT INTO heartbeat (service_url, service_port, timestamp, response_time_millis, status_code, regex_match) " + \
	           "VALUES(%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING;", (service_url, service_port, timestamp, response_time_millis, status_code, regex_match))

def run():
    with (psycopg2.connect(psql_uri)) as db_conn:
       cursor = db_conn.cursor(cursor_factory=RealDictCursor)
	   init_db(cursor)
   
		consumer = init_kafka_consumer()
		while keep_running:
			raw_msgs = consumer.poll(timeout_ms=10000)		
			for topic, msgs in raw_msgs.items():
				for msg in msgs:
					heartbeat = json.loads(msg)
			        write_heartbeat(cursor, heartbeat)

