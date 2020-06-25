import asyncio
import datetime
import json
import logging
import os
import re
import sys

from kafka import KafkaProducer
import requests

kafka_conf_dir = sys.argv[1] #"../kafka_conf" 
kafka_topic = sys.argv[2] # "heartbeat-1"

kafka_urlfile_path = os.path.join(kafka_conf_dir, "kafka_url.txt")
kafka_cafile_path = os.path.join(kafka_conf_dir, "ca.pem")
kafka_certfile_path = os.path.join(kafka_conf_dir, "service.cert")
kafka_keyfile_path = os.path.join(kafka_conf_dir, "service.key")

kafka_security_protocol = "SSL"
heartbeat_timeout_seconds = 5.0
heartbeat_config_filename = "services.json"

event_loop = asyncio.get_event_loop()
keep_running = True

def get_kafka_url():
    with open(kafka_urlfile_path, "r") as file:
        url = file.read().strip()
        print(url)
        return url

kafka_url = get_kafka_url()    

def init_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=kafka_url,
        security_protocol=kafka_security_protocol,
        ssl_cafile=kafka_cafile_path,
        ssl_certfile=kafka_certfile_path,
        ssl_keyfile=kafka_keyfile_path,
    )

def read_config_file(config_filename):
    
    # # config file json format:
    #
    # [{
    #   "service_url": str
    #   "heartbeat_interval_seconds": int
    #   "regex": str [optional]
    # },
    # ...
    # ]
    #

    with open(config_filename) as config_file:
        lines = config_file.read()
        configs = json.loads(lines)
        
        assert isinstance(configs, list)
        for service_config in configs:
            assert isinstance(service_config, dict)            

            assert "service_url" in service_config            
            assert "heartbeat_interval_seconds" in service_config

            assert isinstance(service_config["service_url"], str)                        
            assert isinstance(service_config["heartbeat_interval_seconds"], int)

            if "regex" in service_config:
                assert isinstance(service_config["regex"], str)
                
        return configs

async def poll_service(service):
        url = service["service_url"]   
        
        print("Polling " + url)
        
        time_before = datetime.datetime.now()        
        
        # TODO: what should we do on timeout?
        r = requests.get(url, timeout=heartbeat_timeout_seconds)
        
        # https://stackoverflow.com/questions/1905403/python-timemilli-seconds-calculation
        time_after = datetime.datetime.now()
        diff = time_after - time_before
        duration_millis = diff.total_seconds() * 1000

        regex_match = None    
        try:
            if "regex" in service and service["regex"]:
                regex = re.compile(service["regex"])
                if regex.match(r.text):
                    regex_match = True
                else:
                    regex_match = False
        except Exception as e:
            logging.exception(e)
            raise e
        
        heartbeat = {}
        heartbeat["service_url"]          = str(url)
        heartbeat["timestamp"]            = str(datetime.datetime.now(datetime.timezone.utc).isoformat())
        heartbeat["response_time_millis"] = int(duration_millis)
        heartbeat["status_code"]          = int(r.status_code)
        heartbeat["regex_match"]          = regex_match
        return heartbeat

async def write_to_kafka(producer, kafka_topic, heartbeat_dict):    
    as_string = json.dumps(heartbeat_dict)
    print(as_string)    
    #producer.send(kafka_topic, as_string)
    #producer.flush()

async def poll_and_write(service, producer, kafka_topic):
    heartbeat_dict = await poll_service(service)
    await write_to_kafka(producer, kafka_topic, heartbeat_dict)
    interval = service["heartbeat_interval_seconds"]
    print(str(service["service_url"]) + " should sleep for " + str(interval) + " seconds")
    await asyncio.sleep(interval)   
    await poll_and_write(service, producer, kafka_topic)

async def run_agent():
    service_dicts_list = read_config_file(heartbeat_config_filename)
    producer = init_kafka_producer()

    tasks = []
    for service in service_dicts_list:
        tasks.append( poll_and_write(service, producer, kafka_topic) )
    await asyncio.wait(tasks)

if __name__ == "__main__":
    event_loop.run_until_complete(run_agent())
