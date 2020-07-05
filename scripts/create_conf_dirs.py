#!/usr/bin/python3

import os
import sys

import requests

# This is an utility script for creating the Kafka and PostgreSQL conf
# directories needed by Heartbeat.

email = sys.argv[1]
password = sys.argv[2]
project = sys.argv[3]
psql_service_name = sys.argv[4]
kafka_service_name = sys.argv[5]

outdir_kafka = "kafka_conf"
outdir_psql = "psql_conf"


def _get_token(email, password):
    login_url = "https://console.aiven.io/v1/userauth"
    post_obj = {"email": email, "password": password, "otp": ""}

    r = requests.post(login_url,
                      headers={"content-type": "application/json"},
                      json=post_obj)

    json_obj = r.json()

    return json_obj["token"]


def _make_service_url(project, service):
    return "https://console.aiven.io/v1/project/" + \
           project + "/service/" + service


def _get_headers(auth_token):
    headers = {}
    headers["content-type"] = "application/json"
    headers["Authorization"] = "aivenv1 " + auth_token
    return headers


def _get_ca_file(project, auth_token):
    api_url = "https://console.aiven.io/v1/project/" + project + "/kms/ca"
    r = requests.get(api_url, headers=_get_headers(auth_token))
    json_obj = r.json()

    return json_obj["certificate"]


def _write_to_file(dir, filename, contents):
    with open(os.path.join(dir, filename), "w") as file:
        file.write(contents)


def create_kafka_files(project, service, auth_token):
    api_url = _make_service_url(project, service)
    r = requests.get(api_url, headers=_get_headers(auth_token))
    json_obj = r.json()

    print(str(json_obj))

    uri = json_obj["service"]["service_uri"]
    access_cert = json_obj["service"]["connection_info"]["kafka_access_cert"]
    access_key = json_obj["service"]["connection_info"]["kafka_access_key"]
    ca_cert = _get_ca_file(project, auth_token)

    os.mkdir(outdir_kafka)

    _write_to_file(outdir_kafka, "kafka_url.txt", uri)
    _write_to_file(outdir_kafka, "service.cert", access_cert)
    _write_to_file(outdir_kafka, "service.key", access_key)
    _write_to_file(outdir_kafka, "ca.pem", ca_cert)


def create_psql_files(project, service, auth_token):
    api_url = _make_service_url(project, service)
    r = requests.get(api_url, headers=_get_headers(auth_token))
    json_obj = r.json()

    uri = json_obj["service"]["service_uri"]

    ca_cert = _get_ca_file(project, auth_token)

    os.mkdir(outdir_psql)

    _write_to_file(outdir_psql, "psql_uri.txt", uri)
    _write_to_file(outdir_psql, "ca.pem", ca_cert)


if __name__ == "__main__":
    auth_token = _get_token(email, password)
    create_kafka_files(project, kafka_service_name, auth_token)
    create_psql_files(project, psql_service_name, auth_token)
