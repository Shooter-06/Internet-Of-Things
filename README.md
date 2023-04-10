# IoT Dashboard Project

## Phase 3: Data Capture, Communication, and Presentation

![IoT Sensors](https://your-image-url-here.png)

In this phase of the final project, each group works on the IoT dashboard structure and data presentation.

### Requirements
- Photoresistor
- Resistors
- Wires
- Breadboard
- Raspberry-Pi
- ESP8266 or ESP32
- LED

### Steps
1. Data Capture
2. Data Communication
3. Data Presentation

#### Data Capture

Connect a photoresistor sensor to the ESP8266/ESP32 boards to capture light intensity.

![Photoresistor](https://your-image-url-here.png)

#### Data Communication

Transfer the captured data to the RPi via Wi-Fi connection and to the MQTT broker. Turn on the LED (connected to the RPi) and send a notification email if the current light intensity is less than 400.

#### Data Presentation

Display the current light intensity, light status, and an "Email has been sent" message on the dashboard.

![Dashboard](https://your-image-url-here.png)

### Database Design

Design a database with a table containing the following fields:

- User ID
- Name
- Temp. Threshold
- Humidity Threshold
- Light intensity Threshold

SQLite is recommended for the database application.

## Phase 4: User Profiles and Bluetooth Device Counting

![RFID and Bluetooth](https://your-image-url-here.png)

In this phase of the final project, each group works on the IoT dashboard structure and data presentation.

### Requirements
- Raspberry Pi
- RC522 RFID Module
- Wires
- Breadboard
- RFID tags

### Task 1

#### Data Capture

Create a user profile with RFID tag number, temperature threshold, and light intensity threshold.

![RFID tag](https://your-image-url-here.png)

#### Data Communication

Transfer RFID tag information over the MQTT broker. Send an email when a tag is read, mentioning the user and time of entry.

#### Data Presentation

Display user profile information on the dashboard.

### Task 2

#### Data Capture

Find the Bluetooth address and RSSI of all Bluetooth-enabled devices around the Raspberry-Pi.

![Bluetooth devices](https://your-image-url-here.png)

#### Data Communication

Implemented on the RPi with the built-in Bluetooth card. Any programming languages are acceptable (e.g., JavaScript, Python) to read the BL packets.

#### Data Presentation

Display the number of devices on the dashboard. Optionally, count devices with RSSI greater than a specified threshold.

![Dashboard](https://your-image-url-here.png)

