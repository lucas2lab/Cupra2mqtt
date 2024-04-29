# Cupra2mqtt

## Introduction

Cupra2mqtt is a Python-based service designed to establish a bidirectional communication link between a the CUpra cloud and an MQTT broker. For now it relay information related to the battery charging state and send commands to control the clima system. This project utilizes Docker for easy deployment and management.

## Features

- **Battery Publishing:** Automatically publish battery and charging readings to MQTT.
- **Clima mode Command:** Send command to control the clima mode.
- **Docker Support:** Run as a container for easy setup and scalability.

## Prerequisites

The script can run with python or docker.

Before you begin, ensure you have Docker installed on your system. You can download it from [Docker's official website](https://www.docker.com/get-started).

## Installation

### Setup the service using the config.json

To start using Cupra2mqtt, configure your MQTT broker details and Wiser gateway settings in the configuration file (config.json). You can do so by renaming the config.json.example file and editing your configuration:

```
{
    "cupra_vin"      : "VSSZZZXXXXXXXXXXXX",
    "cupra_username" : "xxxxxxxx@xxxxxxxxxxxx.xxx",
    "cupra_password" : "xxxxxxxxx",
    "cupra_refresh"  : 300,

    "mqtt_broker_ip"    : "1.11.1.1",
    "mqtt_broker_port"  : 1883,
    "mqtt_broker_user"  : "xxxxxxxxxxxxx",
    "mqtt_broker_pass"  : "xxxxxxxxxxxxx",
    "mqtt_broker_topic" : "cupra"
}
```

* VIN is the vehicule identification number, your can find it on your windshield and car documentation
* Username is the email address you use to connect to the cupra app
* password is the password you use to connect to the cupra app

After setting up your configuration run it following the python or docker instructions.

### Using Python

```
pip install --no-cache-dir -r requirements.txt
python src/main.py
```

### Using Docker

1. Build the Docker image:

```
docker build -t cupra2mqtt .
```

2. Run the Docker container:

```
docker run -d cupra2mqtt
```

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any contributions you make are greatly appreciated.

##Fork the Project

Create your Feature Branch (git checkout -b feature/AmazingFeature)
Commit your Changes (git commit -m 'Add some AmazingFeature')
Push to the Branch (git push origin feature/AmazingFeature)
Open a Pull Request

## License

BSD 3-Clause License

## Acknowledgements

* Cupra WeConnect Fork https://github.com/daernsinstantfortress/WeConnect-Cupra-python
* Paho MQTT Python https://github.com/eclipse/paho.mqtt.python 

## ToDo

* [x] Complete and extend this Readme
* [ ] Implement best practice https://testdriven.io/blog/docker-best-practices/#run-only-one-process-per-container
* [ ] Improve not charging state management
* [ ] Add more command handling

