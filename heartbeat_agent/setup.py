from setuptools import setup, find_packages

setup(
    name="heartbeat_agent",
    version="0.1",
    packages=find_packages(),
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