# putting-demo-summit
Demo material for Red Hat Summit demonstration with BLE golf ball

`connect.py` is designed to connect to a BLE-enabled golf ball, write a command to activate data collection, and listen to notifications from various characteristics that provide information about the golf ball's movements and interactions

`scan.py` is a helper app that allows somebody to search for a BLE device by regex match and print out the characteristics of that device

Event-Driven Ansible (EDA) is able to subscribe to messaging layer components like MQTT which allows EDA to pick up all events published to any topics:
```
colin@colin-desktop:~$ mosquitto_sub -h localhost -t '#' -v
golfball/ball1/battery {"battery_level": 100}
golfball/ball2/battery {"battery_level": 100}
golfball/ball1/RollCount {"characteristic": "RollCount", "data": [0, 1]}
golfball/ball1/Velocity {"characteristic": "Velocity", "data": [0, 8]}
golfball/ball1/Ready {"characteristic": "Ready", "data": [0]}
golfball/ball1/BallStopped {"characteristic": "BallStopped", "data": [0]}
golfball/ball1/Velocity {"characteristic": "Velocity", "data": [0, 0]}
golfball/ball1/Ready {"characteristic": "Ready", "data": [1]}
golfball/ball1/RollCount {"characteristic": "RollCount", "data": [0, 0]}
golfball/ball1/BallStopped {"characteristic": "BallStopped", "data": [1]}
golfball/ball2/RollCount {"characteristic": "RollCount", "data": [0, 1]}
golfball/ball2/Velocity {"characteristic": "Velocity", "data": [0, 8]}
golfball/ball2/Ready {"characteristic": "Ready", "data": [0]}
golfball/ball2/BallStopped {"characteristic": "BallStopped", "data": [0]}
golfball/ball2/RollCount {"characteristic": "RollCount", "data": [0, 2]}
```

... or just the ones that will immediately trigger an action:
```
colin@colin-desktop:~$ mosquitto_sub -h localhost -t 'golfball/+/PuttMade' -v
golfball/ball1/PuttMade {"characteristic": "PuttMade", "data": [1]}
golfball/ball2/PuttMade {"characteristic": "PuttMade", "data": [1]}
```

## Diagram

```mermaid
graph LR
    A[BLE Golf Ball] -->|BLE| B["Python BLE Script<br>(connect.py)"]
    B -->|MQTT| C["MQTT Broker<br>(e.g., Mosquitto)"]
    C -->|MQTT| D["MQTT Subscriber<br>(e.g., EDA and Web App)"]

```

## Requirements

- Python 3.7+
- `bleak` library for Bluetooth Low Energy communication

## Setup

1. Ensure you have Python 3.7 or higher installed.
2. Install the `bleak` library using `pip`:
3. Configure the DEVICE_NAME in the script to match the name of your BLE golf ball.


## Notes:

### Hole in one
```
(venv) ➜  putting-demo-summit git:(main) ✗ python3 ble/connect.py -m localhost -g PL2B2418:golfball1
INFO: Connected to: PL2B2418 (Address: 68720155-8DD9-AE6A-8855-881CF69A1F4E)
INFO: Battery Level: 100%
INFO: golfball1 application is running. Press Ctrl+C to exit...
INFO: BLE Notification: {"data": 1, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.8, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 0, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_PUTT_STARTED", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 8, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 4.4, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 12, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 3.5, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 16, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 20, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 23, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 2.6, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 24, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.8, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 25, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 26, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.0, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": "ST_PUTT_STOPPING", "characteristic": "ballState"}
INFO: BLE Notification: {"data": "ST_MAGNET_STOP", "characteristic": "ballState"}
INFO: ST_PUTT_COMPLETE detected. Attempting to toggle Ready state to wake the ball.
INFO: BLE Notification: {"data": 1, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_READY", "characteristic": "ballState"}
INFO: BLE Notification: {"data": "ST_PUTT_COMPLETE", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 0, "characteristic": "ballRollCount"}
```

### Hole in four
```
venv) ➜  putting-demo-summit git:(main) ✗ python3 ble/connect.py -m localhost -g PL2B2418:golfball1
INFO: Connected to: PL2B2418 (Address: 68720155-8DD9-AE6A-8855-881CF69A1F4E)
INFO: Battery Level: 100%
INFO: golfball1 application is running. Press Ctrl+C to exit...
INFO: BLE Notification: {"data": 2, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 1.7, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 0, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_PUTT_STARTED", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 0.0, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": "ST_PUTT_NOT_COUNTED", "characteristic": "ballState"}
INFO: BLE Notification: {"data": "ST_READY", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 1, "characteristic": "Ready"}
INFO: BLE Notification: {"data": 1, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.8, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 0, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_PUTT_STARTED", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 0.0, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": "ST_PUTT_NOT_COUNTED", "characteristic": "ballState"}
INFO: BLE Notification: {"data": "ST_READY", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 1, "characteristic": "Ready"}
INFO: BLE Notification: {"data": 2, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 1.7, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 0, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_PUTT_STARTED", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 4, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 8, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 9, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.8, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 10, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.0, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": "ST_PUTT_STOPPING", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 11, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.8, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 0.0, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": "ST_BALL_STOPPED", "characteristic": "ballState"}
INFO: ST_PUTT_COMPLETE detected. Attempting to toggle Ready state to wake the ball.
INFO: BLE Notification: {"data": 1, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_READY", "characteristic": "ballState"}
INFO: BLE Notification: {"data": "ST_PUTT_COMPLETE", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 0, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 3, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 2.6, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 0, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_PUTT_STARTED", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 4, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.8, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 7, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 8, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 9, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 10, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.0, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": "ST_PUTT_STOPPING", "characteristic": "ballState"}
INFO: BLE Notification: {"data": "ST_BALL_STOPPED", "characteristic": "ballState"}
INFO: ST_PUTT_COMPLETE detected. Attempting to toggle Ready state to wake the ball.
INFO: BLE Notification: {"data": 1, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_READY", "characteristic": "ballState"}
INFO: BLE Notification: {"data": "ST_PUTT_COMPLETE", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 0, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 2, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 1.7, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 0, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_PUTT_STARTED", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 3, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.8, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 4, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 7, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.0, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": "ST_PUTT_STOPPING", "characteristic": "ballState"}
INFO: BLE Notification: {"data": "ST_BALL_STOPPED", "characteristic": "ballState"}
INFO: ST_PUTT_COMPLETE detected. Attempting to toggle Ready state to wake the ball.
INFO: BLE Notification: {"data": 1, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_READY", "characteristic": "ballState"}
INFO: BLE Notification: {"data": "ST_PUTT_COMPLETE", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 0, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 1, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.8, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 0, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_PUTT_STARTED", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 7, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 3.5, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 10, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 2.6, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 11, "characteristic": "ballRollCount"}
INFO: BLE Notification: {"data": 0.8, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": 0.0, "characteristic": "Velocity"}
INFO: BLE Notification: {"data": "ST_MAGNET_STOP", "characteristic": "ballState"}
INFO: ST_PUTT_COMPLETE detected. Attempting to toggle Ready state to wake the ball.
INFO: BLE Notification: {"data": 1, "characteristic": "Ready"}
INFO: BLE Notification: {"data": "ST_READY", "characteristic": "ballState"}
INFO: BLE Notification: {"data": "ST_PUTT_COMPLETE", "characteristic": "ballState"}
INFO: BLE Notification: {"data": 0, "characteristic": "ballRollCount"}
```