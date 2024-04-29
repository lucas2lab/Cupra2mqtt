import json
import time
import signal
import sys
from datetime import datetime

import logging
from sys import stdout

import paho.mqtt.client as mqtt

from weconnect_cupra import weconnect_cupra
from weconnect_cupra.service import Service
from weconnect_cupra.elements.control_operation import ControlOperation

def setup_logging():
    log = logging.getLogger('logger')
    log.setLevel(logging.DEBUG) # set logger level
    logFormatter = logging.Formatter("%(name)-12s %(asctime)s %(levelname)-8s %(filename)s:%(funcName)s %(message)s")
    consoleHandler = logging.StreamHandler(stdout) #set streamhandler to stdout
    consoleHandler.setFormatter(logFormatter)
    log.addHandler(consoleHandler)
    return log

log = setup_logging()

def load_config():
    try:
        with open("src/config.json") as f:
            cfg = json.load(f)
            log.info("Config loaded")
    except Exception as e:
        log.error("Failed to load config: %s", e)
        sys.exit(1)

    return cfg

cfg = load_config()

def signal_handler(sig, frame):
    log.info("Received signal {}. Exiting...".format(sig))
    mqttc.disconnect()
    mqttc.loop_stop()
    sys.exit(0)

def on_connect(client, userdata, flags, reason_code, properties):
    log.info(f"Connected with result code {reason_code}")
    client.subscribe("{}/#".format(cfg["mqtt_broker_topic"]))
    #client.subscribe("$SYS/#")

def on_message(client, userdata, msg):
    log.info(msg.topic+" "+str(msg.payload))
    if msg.topic == "{}/clima/set".format(cfg["mqtt_broker_topic"]):
        try:   
            state = json.loads(msg.payload.decode())["state"]
            log.info(f"Setting clima to {state}")
        except json.JSONDecodeError:
            log.error("Error decoding JSON {}".format(msg.payload.decode()))
            return
        if state == "on":
            weConnect.vehicles[cfg['cupra_vin']].controls.climatizationControl.value = ControlOperation(value='start')
        elif state == "off":
            weConnect.vehicles[cfg['cupra_vin']].controls.climatizationControl.value = ControlOperation(value='stop')

def on_publish(client, userdata, mid, reason_code, properties):
    try:
        log.debug(f"mid: {mid} reason_code: {reason_code}")
        userdata.remove(mid)
    except KeyError:
        log.error("on_publish() is called with a mid not present in unacked_publish")

# signal handling
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Setup WeConnect Cupra
weConnect = weconnect_cupra.WeConnect(username=cfg['cupra_username'], password=cfg['cupra_password'],
    updateAfterLogin=False, loginOnInit=False,
    service=Service.MY_CUPRA, tokenfile='token.txt')

weConnect.login()
last_update = datetime(2020,1,1)

# Setup MQTT
unacked_publish = set()

mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_publish = on_publish
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.user_data_set(unacked_publish)
mqttc.username_pw_set(cfg["mqtt_broker_user"], cfg["mqtt_broker_pass"])
mqttc.connect(cfg["mqtt_broker_ip"], cfg["mqtt_broker_port"], 60)
mqttc.loop_start()

while True:
    weConnect.update()

    _car = json.loads(weConnect.vehicles[cfg['cupra_vin']].toJSON())

    _last_update = datetime.strptime(_car['domains']['charging']['chargingStatus']['carCapturedTimestamp'], '%Y-%m-%dT%H:%M:%S+00:00')
    if last_update >= _last_update:
        log.info("No new data to send to MQTT. Skipping (Internal {}, Api returned {})...".format(last_update, _last_update))
    else:
        last_update = _last_update
        car = {'connectivity':{}, 'charging':{}, 'battery':{}, 'clima':{}}
        car['nickname']                    = _car['nickname']
        car['connectivity']['state']       = _car['domains']['status']['connectionStatus']['mode']   
        car['connectivity']['last_update'] = _car['domains']['charging']['chargingStatus']['carCapturedTimestamp']
        car['charging']['state']           = _car['domains']['charging']['chargingStatus']['chargingState']
        if 'remainingChargingTimeToComplete_min' in _car['domains']['charging']['chargingStatus']:
            car['charging']['est_time_comp']   = _car['domains']['charging']['chargingStatus']['remainingChargingTimeToComplete_min']
        car['battery']['percentage']       = _car['domains']['charging']['batteryStatus']['currentSOC_pct']
        car['clima']['state']              = _car['domains']['climatisation']['climatisationStatus']['climatisationState'] # ventilation / off

        log.info("Sending car data to MQTT: ", car)
        msg_info = mqttc.publish(cfg["mqtt_broker_topic"], json.dumps(car), qos=1)
        unacked_publish.add(msg_info.mid)

        while len(unacked_publish):
            time.sleep(0.1)

        msg_info.wait_for_publish()

    time.sleep(cfg["cupra_refresh"])

