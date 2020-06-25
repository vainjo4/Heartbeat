
import os
from kafka import KafkaProducer
import asyncio
import requests

import sys

kafka_conf_dir = sys.argv[1] #"../kafka_conf" 
topic_name = sys.argv[2] # "heartbeat-1"

kafka_urlfile_path = os.path.join(kafka_conf_dir, "kafka_url.txt")
kafka_cafile_path = os.path.join(kafka_conf_dir, "ca.pem")
kafka_certfile_path = os.path.join(kafka_conf_dir, "service.cert")
kafka_keyfile_path = os.path.join(kafka_conf_dir, "service.key")

kafka_security_protocol = "SSL"
heartbeat_timeout_millis = 5000
heartbeat_config_filename = "heartbeat_config.json"

keep_running = True

def get_kafka_url():
	with open(kafka_urlfile_path, "r") as file:
		return file.readlines().strip()

kafka_url = get_kafka_url()	

def init_kafka_producer():
	return KafkaProducer(
		bootstrap_servers=kafka_url,
		security_protocol=kafka_security_protocol,
		ssl_cafile=kafka_cafile_path,
		ssl_certfile=kafka_certfile_path,
		ssl_keyfile=kafka_keyfile_path,
	)

# ### config file json format:
# [{
#   "service_url": str
#   "service_port": int
#   "heartbeat_interval_seconds": int
#   "regex": str [optional]
# },
# ...
# ]

# <empty line>

def read_config_file(config_filename):
    with open(config_filename) as config_file:
	    lines = config_file.readlines()
		configs = json.loads(lines)
		
		assert isinstance(configs, list)
		for service_config in configs:
			assert isinstance(service_config, dict)			

			assert "service_url" in service_config			
			assert "service_port" in service_config
			assert "heartbeat_interval_seconds" in service_config

			assert isinstance(service_config["service_url"], str)						
			assert isinstance(service_config["service_port"], int)			
			assert isinstance(service_config["heartbeat_interval_seconds"], int)

			if "regex" in service_config:
				assert isinstance(service_config["regex"], str)
				
		return configs
		
def run():
	service_dicts_list = read_config_file(heartbeat_config_filename)
	producer = init_kafka_producer()

    for service in service_dicts_list:
	    asyncio.run(poll_service(service))

	async def poll_service(service):
	    url = service["service_url"]  
	    port = service["service_port"]
		interval = service["heartbeat_interval_seconds"]
	
		r = requests.get(url)
		asyncio.sleep(interval)

	def write_to_kafka():
	
    for()
