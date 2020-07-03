#!/usr/bin/python3

from setuptools import setup

setup(
    name="heartbeat_agent",
    version="0.1",
    packages=["heartbeat_agent"],
    entry_points={
        "console_scripts": [
            "heartbeat_agent = heartbeat_agent.heartbeat_agent:run"
        ]
    },
    install_requires=[
        "kafka-python==2.0.1",
        "requests==2.24.0"
    ],
    package_data={
        "heartbeat_agent": ["conf/heartbeat_agent.cfg", "conf/services.json"]
    }
)