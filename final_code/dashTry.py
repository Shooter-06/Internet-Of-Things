import logging
import os
import subprocess
from dash import Dash, html, dcc, Input, Output, State
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import dash_bootstrap_components as dbc
import dash_extensions as de
import dash_daq as daq
import RPi.GPIO as GPIO
import time
from time import sleep
import Freenove_DHT as DHT
import smtplib, ssl, getpass, imaplib, email
import random
from paho.mqtt import client as mqtt_client
from datetime import datetime
import pymysql
import pymysql.cursors


# Removes the post update component in the terminal
logging.getLogger('werkzeug').setLevel(logging.ERROR)

app = Dash(__name__,  meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1.0",
        }
    ])
theme_change = ThemeChangerAIO(aio_id="theme", radio_props={"persistence": True}, button_props={"color": "danger","children": "Change Theme"}) 
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(theme_change),
    ],
    brand="IOT SMART HOME",
    color="dark",
    dark=True,
    sticky="top"
)

#---------User Information Variables-------
user_id = "Default"
temp_threshold = 25.0
light_threshold = 0
humidity = 40
path_to_picture = 'assets/minion.jpg'
#-----------------------------------------

#MQTT connection variables
broker = '192.168.72.248' #ip in Lab class
port = 1883
topic1 = "lightintensity"
topic2 = "IoTLab /rfid"
client_id = f'python-mqtt-{random.randint(0, 100)}'
esp_message = 0
esp_rfid_message = "000000"

# counters and checkers
temp_email_sent = False
fan_status_checker=False
email_counter = 0    # just checks if email has been sent at some stage

# For Phase02 temperature (used in temperature callback)
temperature = 0

# RPI GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
DHTPin = 40 # equivalent to GPIO21
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
Motor1 = 35 # Enable Pin
Motor2 = 37 # Input Pin
Motor3 = 33 # Input Pin
LedPin = 38
GPIO.setup(Motor1, GPIO.IN)
GPIO.setup(Motor2, GPIO.IN)
GPIO.setup(Motor3, GPIO.IN)
GPIO.setup(LedPin, GPIO.OUT)

#Images and GIFs
light_bulb_off = 'assets/lightbulbOFF.png'        
light_bulb_on = 'assets/lightbulbON.png'       
url="https://media2.giphy.com/media/l4hLVfpZQf1Ca0bhm/giphy.gif?cid=ecf05e47rjd0u85axrbyopsbvfp4vcsi3a8sgjvmbf2p2iwh&ep=v1_gifs_search&rid=giphy.gif&ct=g"

options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))


# Dashboard Components
daq_Gauge = daq.Gauge(
                id='my-gauge-1',
                label="Humidity",
                showCurrentValue=True,
                size=250,
                max=100,
                min=0)

daq_Thermometer = daq.Thermometer(
                    id='my-thermometer-1',
                    min=-40,
                    max=60,
                    scale={'start': -40, 'interval': 10},
                    label="Temperature",
                    showCurrentValue=True,
                    height=150,
                    units="C",
                    color="red")

daq_Fahrenheit_ToggleSwitch = daq.ToggleSwitch(
                    id='fahrenheit-switch',
                    value=False)

daq_Led_Light_Intensity_LEDDisplay = daq.LEDDisplay(
                                        id='light-intensity',
                                        label="Light Intensity Value",
                                        labelPosition='bottom',
                                        value = 0,
                                        size = 50)

# MQTT functions
def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")
    client.subscribe(topic1)
    client.subscribe(topic2)

def on_message(client, userdata, msg):
    global esp_message, esp_rfid_message
    if msg.topic == topic1:
        esp_message = int(msg.payload.decode("utf-8"))
    elif msg.topic == topic2:
        esp_rfid_message = msg.payload.decode("utf-8")

# MQTT client setup
# client = mqtt.Client(client_id)
client.on_connect = on_connect
client.on_message = on_message
client.connect(broker, port)

client.loop_start()

# Main layout
app.layout = html.Div([
    dcc.Location(id="url"),
    dbc.Row([
        dbc.Col(navbar, width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardImg(src=path_to_picture),
                dbc.CardBody([
                    html.P([
                        "UserID: ", html.Span(user_id, id="user_id"),
                    ]),
                    dbc.Button("Log Out", id="logout", color="danger", className="mt-auto"),
                ]),
            ]),
        ], width=3),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Temperature and Humidity"),
                dbc.CardBody([
                    daq_Gauge,
                    daq_Thermometer,
                    html.Div([
                        daq.Fahrenheit_ToggleSwitch,
                        html.Span(" °C/°F", style={"font-size": "20px"})
                    ])
                ]),
            ]),
            dbc.Card([
                dbc.CardHeader("Light Intensity"),
                dbc.CardBody([
                    daq_Led_Light_Intensity_LEDDisplay,
                    html.Img(src=light_bulb_off, id="light-bulb-img", style={"width": "70%"})
                ]),
            ]),
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("Fan Control"),
                dbc.CardBody([
                    daq.PowerButton(
                        id='fan-power-button',
                        on=False,
                        size=100,
                        color="danger"
                    )
                ]),
            ]),
            dbc.Card([
                dbc.CardHeader("Email Alerts"),
                dbc.CardBody([
                    dbc.FormGroup([
                        dbc.Label("Threshold Temperature (°C):"),
                        dbc.Input(
                            id="temperature-threshold-input",
                            type="number",
                            value=25,
                            min=-40,
                            max=60
                        ),
                    ]),
                    dbc.FormGroup([
                        dbc.Label("Recipient Email Address:"),
                        dbc.Input(
                            id="email-address-input",
                            type="email",
                            placeholder="example@example.com"
                        ),
                    ]),
                    dbc.Button("Send Email", id="send-email", color="primary", className="mt-auto"),
                ]),
            ]),
        ], width=3),
    ]),
    dcc.Interval(id="update-components-interval", interval=1000, n_intervals=0)
])

# Callbacks

# Update Temperature and Humidity
@app.callback(
    [Output("my-gauge-1", "value"), Output("my-thermometer-1", "value")],
    [Input("update-components-interval", "n_intervals")]
)
def update_temperature_and_humidity(n):
    global temperature, humidity
    humidity, temperature = Adafruit_DHT.read_retry(11, DHTPin)
    return humidity, temperature

# Fahrenheit Toggle Switch
@app.callback(
    Output("my-thermometer-1", "units"),
    [Input("fahrenheit-switch", "value")]
)
def switch_temperature_unit(fahrenheit_switch):
    if fahrenheit_switch:
        return "F"
    else:
        return "C"

# Update Light Intensity
@app.callback(
    Output("light-intensity", "value"),
    [Input("update-components-interval", "n_intervals")]
)
def update_light_intensity(n):
    global esp_message
    return esp_message

# Update Light Bulb Image
@app.callback(
    Output("light-bulb-img", "src"),
    [Input("light-intensity", "value")]
)
def update_light_bulb_img(light_intensity):
    if light_intensity > light_threshold:
        return light_bulb_on
    else:
        return light_bulb_off

# Fan Control
@app.callback(
    Output("fan-power-button", "on"),
    [Input("my-thermometer-1", "value"), Input("temperature-threshold-input", "value")]
)
def fan_control(temperature, threshold_temperature):
    global fan_status_checker
    if temperature >= threshold_temperature:
        fan_status_checker = True
        return True
    else:
        fan_status_checker = False
        return False

# Email Alert
@app.callback(
    Output("send-email", "children"),
    [Input("send-email", "n_clicks"), Input("email-address-input", "value")]
)
def email_alert(n_clicks, email_address):
    global email_counter, temp_email_sent
    if n_clicks:
        if email_address is not None and email_address != "":
            if temp_email_sent is False:
                send_email(email_address)
                email_counter += 1
                temp_email_sent = True
                return "Email Sent!"
            else:
                return "Email Already Sent!"
        else:
            return "Invalid Email Address!"
    else:
        return "Send Email"

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port="8080")
