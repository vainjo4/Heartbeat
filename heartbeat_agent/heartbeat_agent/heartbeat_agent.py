import argparse
import asyncio
import configparser
import datetime
import json
import logging
import os
import re
import sys

from kafka import KafkaProducer
import requests

parser=argparse.ArgumentParser()

parser.add_argument('--config', help='General configuration')
parser.add_argument('--kafka_conf', help='Kafka configuration')

args=parser.parse_args()

current_dir = os.path.dirname(os.path.realpath(__file__))
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] - %(message)s")

# --- Configuration ---

config = configparser.ConfigParser()
configuration_file = args.config if hasattr(args, "config") and args.config else os.path.join(current_dir, "conf", "heartbeat_agent.cfg")
config.read(configuration_file)

kafka_conf_dir = args.kafka_conf if hasattr(args, "kafka_conf") and args.kafka_conf else os.path.join(current_dir, config["heartbeat_agent"]["kafka_conf_dir"])

heartbeat_services_filepath = os.path.join(current_dir, config["heartbeat_agent"]["heartbeat_services_filepath"])
heartbeat_timeout_seconds = float(config["heartbeat_agent"]["heartbeat_timeout_seconds"])

kafka_topic = config["heartbeat_agent"]["kafka_topic"]
kafka_security_protocol = config["heartbeat_agent"]["kafka_security_protocol"]

kafka_urlfile_path = os.path.join(kafka_conf_dir, "kafka_url.txt")
kafka_cafile_path = os.path.join(kafka_conf_dir, "ca.pem")
kafka_certfile_path = os.path.join(kafka_conf_dir, "service.cert")
kafka_keyfile_path = os.path.join(kafka_conf_dir, "service.key")


#event_loop = asyncio.get_event_loop()


def get_kafka_url():
    with open(kafka_urlfile_path, "r") as file:
        url = file.read().strip()
        return url


kafka_url = get_kafka_url()


def read_services_file(config_filename):

    # # services file json format:
    #
    # [{
    #   "service_url": str
    #   "heartbeat_interval_seconds": int
    #   "regex": str [optional]
    # },
    # ...
    # ]

    with open(config_filename) as config_file:
        configs = json.loads(config_file.read())

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


services_list = read_services_file(heartbeat_services_filepath)


# --- Functions ---


def init_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=kafka_url,
        security_protocol=kafka_security_protocol,
        ssl_cafile=kafka_cafile_path,
        ssl_certfile=kafka_certfile_path,
        ssl_keyfile=kafka_keyfile_path,
    )


async def poll_service(service):
        url = service["service_url"]

        logging.info("Polling " + url)

        time_before = datetime.datetime.now()

        # TODO: what should we do on timeout?
        r = requests.get(url, timeout=heartbeat_timeout_seconds)

        time_after = datetime.datetime.now()
        diff = time_after - time_before
        duration_millis = diff.total_seconds() * 1000

        regex_match = None
        try:
            if "regex" in service and service["regex"]:
                if re.search(service["regex"], r.text):
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
    logging.debug("write_to_kafka: " + as_string)
    producer.send(kafka_topic, as_string.encode("utf-8"))
    producer.flush()


async def poll_and_write(service, producer, kafka_topic):
    heartbeat_dict = await poll_service(service)
    await write_to_kafka(producer, kafka_topic, heartbeat_dict)
    interval = service["heartbeat_interval_seconds"]
    logging.info(str(service["service_url"]) + " sleeping for " + str(interval) + " seconds")
    await asyncio.sleep(interval)
    await poll_and_write(service, producer, kafka_topic)


async def run_agent():
    producer = init_kafka_producer()
    tasks = []
    for service in services_list:
        tasks.append( poll_and_write(service, producer, kafka_topic) )
    await asyncio.wait(tasks)


# --- Entry point ---

# wheel commandline entry point
def run():
    asyncio.run(run_agent())

if __name__ == "__main__":
    run()
