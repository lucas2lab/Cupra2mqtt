import json
import time
import signal
import sys
from datetime import datetime

import paho.mqtt.client as mqtt

from weconnect_cupra import weconnect_cupra
from weconnect_cupra.service import Service
from weconnect_cupra.elements.control_operation import ControlOperation

with open("src/config.json") as f:
    cfg = json.load(f)

def signal_handler(sig, frame):
    print('Closing service...')
    mqttc.disconnect()
    mqttc.loop_stop()
    sys.exit(0)

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe("{}/#".format(cfg["mqtt_broker_topic"]))
    #client.subscribe("$SYS/#")

def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    if msg.topic == "{}/clima/set".format(cfg["mqtt_broker_topic"]):
        try:   
            state = json.loads(msg.payload.decode())["state"]
            print(f"Setting clima to {state}")
        except json.JSONDecodeError:
            print("Error decoding JSON {}".format(msg.payload.decode()))
            return
        if state == "on":
            weConnect.vehicles[cfg['cupra_vin']].controls.climatizationControl.value = ControlOperation(value='start')
        elif state == "off":
            weConnect.vehicles[cfg['cupra_vin']].controls.climatizationControl.value = ControlOperation(value='stop')

def on_publish(client, userdata, mid, reason_code, properties):
    try:
        print(f"mid: {mid} reason_code: {reason_code}")
        userdata.remove(mid)
    except KeyError:
        print("on_publish() is called with a mid not present in unacked_publish")

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
    print(last_update, _last_update)
    if last_update >= _last_update:
        print("No new data to send to MQTT. Skipping...")
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

        print("Sending car data to MQTT: ", car)
        msg_info = mqttc.publish(cfg["mqtt_broker_topic"], json.dumps(car), qos=1)
        unacked_publish.add(msg_info.mid)

        while len(unacked_publish):
            time.sleep(0.1)

        msg_info.wait_for_publish()

    time.sleep(cfg["cupra_refresh"])

