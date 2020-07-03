import asyncio
import datetime
import logging
import os
import sys
import time

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '../'))
import heartbeat_agent


logging.basicConfig(level=logging.INFO, format="[%(asctime)s] [%(levelname)s] - %(message)s")


def test_init():
    logging.info("test_init")
    assert heartbeat_agent.init_kafka_producer()
    logging.info("test_init done")


def _call_poll(service):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(heartbeat_agent.poll_service(service))


def _timestamp_str_between(before, after, between_str):
    timestamp = datetime.datetime.fromisoformat(between_str)
    assert timestamp > before
    assert timestamp < after


def test_poll_ok():
    service = {}
    url = "https://is.fi"
    service["service_url"] = url
    service["heartbeat_interval_seconds"] = 3
    service["regex"] = "Etusivu"
    
    before_poll = datetime.datetime.now(datetime.timezone.utc)
    time.sleep(1)
    heartbeat = _call_poll(service)
    time.sleep(1)
    after_poll = datetime.datetime.now(datetime.timezone.utc)

    assert heartbeat["service_url"] == url
    assert 0 < heartbeat["response_time_millis"] < 1000
    assert heartbeat["status_code"] == 200
    assert heartbeat["regex_match"] == True
       
    _timestamp_str_between(before_poll, after_poll, heartbeat["timestamp"])


def test_poll_redirect_301():
    service = {}
    url = "http://yle.fi"
    service["service_url"] = url
    service["heartbeat_interval_seconds"] = 300
    service["regex"] = "_icannotbefound_"
    
    before_poll = datetime.datetime.now(datetime.timezone.utc)
    time.sleep(1)
    heartbeat = _call_poll(service)
    time.sleep(1)
    after_poll = datetime.datetime.now(datetime.timezone.utc)

    assert heartbeat["service_url"] == url
    assert 0 < heartbeat["response_time_millis"] < 1000
    assert heartbeat["status_code"] == 200 # requests follows 301 redirect
    assert heartbeat["regex_match"] == False
    
    _timestamp_str_between(before_poll, after_poll, heartbeat["timestamp"])


def test_poll_nonexistent_url():
    service = {}
    url = "http://thisisanurlthatdoesnotexist_aaaaaaaaaaaaaaaaa.org"
    service["service_url"] = url 
    service["heartbeat_interval_seconds"] = 3
    
    before_poll = datetime.datetime.now(datetime.timezone.utc)
    time.sleep(1)
    heartbeat = _call_poll(service)
    time.sleep(1)
    after_poll = datetime.datetime.now(datetime.timezone.utc)

    assert heartbeat["service_url"] == url
    assert 0 <= heartbeat["response_time_millis"] < 1000
    assert heartbeat["status_code"] == -1
    assert heartbeat["regex_match"] == None
    
    _timestamp_str_between(before_poll, after_poll, heartbeat["timestamp"])


def test_poll_nonresponding_url():
    service = {}
    url = "http://localhost"
    service["service_url"] = url
    service["heartbeat_interval_seconds"] = 1
    
    before_poll = datetime.datetime.now(datetime.timezone.utc)
    time.sleep(1)
    heartbeat = _call_poll(service)
    time.sleep(1)
    after_poll = datetime.datetime.now(datetime.timezone.utc)

    assert heartbeat["service_url"] == url
    assert 1000 < heartbeat["response_time_millis"] < 10000
    assert heartbeat["status_code"] == -1
    assert heartbeat["regex_match"] == None
    
    _timestamp_str_between(before_poll, after_poll, heartbeat["timestamp"])


def test_poll_nonexisting_resource():
    service = {}
    url = "https://yle.fi/idonotexist"
    service["service_url"] = url
    service["heartbeat_interval_seconds"] = 300
    
    before_poll = datetime.datetime.now(datetime.timezone.utc)
    time.sleep(1)
    heartbeat = _call_poll(service)
    time.sleep(1)
    after_poll = datetime.datetime.now(datetime.timezone.utc)

    assert heartbeat["service_url"] == url
    assert 0 < heartbeat["response_time_millis"] < 1000
    assert heartbeat["status_code"] == 404
    assert heartbeat["regex_match"] == None
    
    _timestamp_str_between(before_poll, after_poll, heartbeat["timestamp"])


if __name__ == "__main__":
    test_init()
    test_poll_ok()
    test_poll_redirect_301()
    test_poll_nonexistent_url()
    test_poll_nonresponding_url()
    test_poll_nonexisting_resource()