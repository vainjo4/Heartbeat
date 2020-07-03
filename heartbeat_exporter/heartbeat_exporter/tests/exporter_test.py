import logging
import sys
sys.path.append('../')
import heartbeat_exporter

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] - %(message)s")

def test_init():
    logging.info("test_init")
    assert heartbeat_exporter.init_kafka_consumer()
    logging.info("test_init done")

if __name__ == "__main__":
    test_init()
