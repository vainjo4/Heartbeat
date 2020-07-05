#!/usr/bin/python3

from setuptools import setup

setup(
    name="heartbeat_exporter",
    version="0.1",
    packages=["heartbeat_exporter"],
    entry_points={
        "console_scripts": [
            "heartbeat_exporter = heartbeat_exporter.heartbeat_exporter:run"
        ]
    },
    install_requires=[
        "kafka-python==2.0.1",
        "psycopg2-binary==2.8.5"
    ],
    package_data={
        "heartbeat_exporter": ["conf/heartbeat_exporter.cfg"]
    }
)
