import socket
import subprocess
import argparse
import json

import yaml
import paho.mqtt.publish as mqtt_publish
import jc


def get_certificate_info():
    output = subprocess.check_output(["certbot", "certificates"], text=True)
    certs = jc.parse('certbot', output)
    return certs['certificates']


def publish_to_mqtt(cert):
    print(f'Publish info for {cert["name"]} to MQTT')
    mqtt_publish.single(
        topic=f'{config["mqtt"]["topic_prefix"]}/{cert["name"]}', 
        payload=json.dumps(cert), 
        qos=config["mqtt"]["qos"], 
        retain=config["mqtt"]["retain"],
        hostname=config["mqtt"]["broker"], 
        auth={'username': config["mqtt"]["username"], 'password': config["mqtt"]["password"]})


def load_config(config_file):
    """Load the configuration from config yaml file and use it to override the defaults."""
    with open(config_file, "r") as f:
        config_override = yaml.safe_load(f)

    default_config = {
        "mqtt": {
            "broker": "127.0.0.1",
            "port": 1883,
            "username": None,
            "password": None,
            "topic_prefix": "certstat/$HOSTNAME",
            "retain": True,
            "qos": 1
        }
    }

    config = {**default_config, **config_override}
    return config

# command line info
parser = argparse.ArgumentParser(description="Report Letsencrypt certificate status to MQTT")
parser.add_argument(
    "-c",
    "--config",
    default="config.yaml",
    help="Configuration yaml file, defaults to `config.yaml`",
    dest="config_file",
)
args = parser.parse_args()


# load configuration
config = load_config(args.config_file)


# get device host name - used in mqtt topic
hostname = socket.gethostname()
base_topic = config["mqtt"]["topic_prefix"]
base_topic = base_topic.replace("$HOSTNAME", hostname)

# get certificate info
certs = get_certificate_info()

for cert in certs:
    publish_to_mqtt(cert)