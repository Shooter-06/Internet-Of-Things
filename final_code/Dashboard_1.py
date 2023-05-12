import random
import smtplib
from email.message import EmailMessage

import time
from time import sleep
import Freenove_DHT as DHT
import smtplib
import ssl
import getpass
import imaplib
import email
import random
from paho.mqtt import client as mqtt_client
import datetime

from datetime import datetime
import RPi.GPIO as GPIO
from dash import Dash, html, dcc, Input, Output, State
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import dash_bootstrap_components as dbc
import dash_extensions as de
import dash_daq as daq
import os
import sqlite3

from dash import Dash, html, Input, Output
import dash_daq as daq
import dash
import dash_bootstrap_components as dbc
import Freenove_DHT as DHT
import time
import paho.mqtt.client as mqtt
from dash import dcc
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import paho.mqtt.client as mqtt_client

from email.header import decode_header
import paho.mqtt.subscribe as subscribe

import imaplib
from datetime import datetime
import threading
import email
import time
import sqlite3


import RPi.GPIO as GPIO
from time import sleep

from dash import Dash, html, Input, Output
import dash_daq as daq
import dash
import dash_bootstrap_components as dbc
import Freenove_DHT as DHT
import time
import paho.mqtt.client as mqtt
from dash import dcc
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import paho.mqtt.client as mqtt_client

from email.header import decode_header
import paho.mqtt.subscribe as subscribe

import imaplib
from datetime import datetime
import threading
import email
import time
import sqlite3


import RPi.GPIO as GPIO
from time import sleep

rfid_message = None
light_value_received = 100
temp_email_sent = False
received = False

sent = False
sent2 = False
user_profiles = {}  # Store user profiles
user_data = {}  # Store user data

GPIO.setmode(GPIO.BCM)

light_intensity_value = 0
light_intensity_state = "OFF"
GPIO.setwarnings(False)
LedPin = 26
GPIO.setup(LedPin, GPIO.OUT)
led_email_sent_count = 0
esp_message = 0
email_counter = 0


message = 0
DHTPin = 25
fan_status_checker = False

id = "Default"
temp_threshold = 20.0
light_threshold = 500
humidity = 30
profile = 'https://images.immediate.co.uk/production/volatile/sites/3/2021/12/miles-morales-Spider-Man-Into-The-Spider-Verse-9e2bb6e.jpg?quality=90&resize=620,414'

GPIO.setwarnings(False)

Motor1 = 27  
LedPin = 19

GPIO.setup(Motor1, GPIO.OUT)
GPIO.setup(LedPin, GPIO.OUT)


bulb_off = 'assets/lightbulbOFF.png'
bulb_on = 'assets/lightbulbON.png'

fan_off = 'assets/fanOff.png'
fan_on = 'assets/fanON.png'
url = "https://assets3.lottiefiles.com/packages/lf20_acmgs9pi.json"
options = dict(loop=True, autoplay=True, rendererSettings=dict(
    preserveAspectRatio='xMidYMid slice'))

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


def on_message(client, userdata, msg):
    print("mqtt connection")
    global light_value_received, rfid_message
    if msg.topic == "photo_resistor/lightintensity":
        light_value_received = int(msg.payload.decode("utf-8"))
        print("lighh")
    elif msg.topic == "esp/rfid":
        rfid_message = msg.payload.decode("utf-8")
        print(rfid_message)


mqtt_client_instance = mqtt_client.Client()
mqtt_client_instance.on_message = on_message
mqtt_client_instance.connect("192.168.72.197")
mqtt_client_instance.subscribe("photo_resistor/lightintensity")
mqtt_client_instance.subscribe("esp/rfids")
mqtt_client_instance.loop_start()

# Set up theme toggle button and theme store
theme_toggle_button = dbc.Button(
    "Change Theme", id="theme-toggle", color="danger")
theme_store = dcc.Store(id="theme-store", storage_type="local", data="default")

# Set up the navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(theme_toggle_button),
    ],
    brand="Fiacre DashBoard",
    color="blue",
    dark=True,
    sticky="top"
)


def get_from_database(rfid):
    # conn = sqlite3.connect('example.db')

    conn = sqlite3.connect('example_1.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE rfid = ?', (rfid,))
    user_info = cursor.fetchone()
    conn.close()

    if user_info:
        global user_id
        user_id = user_info[0]
        global temp_threshold
        temp_threshold = user_info[1]
        global light_threshold
        light_threshold = user_info[2]
        global picture
        picture = user_info[3]

        # Print the retrieved user information to the console
        print('Retrieved user information:')
        print('User ID:', user_id)
        print('Temperature threshold:', temp_threshold)
        print('Light threshold:', light_threshold)
        print('Path to picture:', picture)

        return {
            'username': user_id,
            'humidity': temp_threshold,
            'temperature': light_threshold,
            'light_intensity': humidity,  # Replace this with the correct value from the database
            'profile_image': picture
        }

    # If no user was found, print a message to the console
    else:
        print('No user found with RFID tag ID:', rfid)

    print(str(user_id) + " " + str(temp_threshold) +
          " " + str(light_threshold) + " " + picture)


def checkLight():
    global light_value_received
    return light_value_received


#checks if a user replied with a yes
def user_answer():
    global received
    imap_url = "imap.gmail.com"
    email_address = "fiacreiot23@gmail.com"
    password = "rukeavdzcxviypic"
    imap = imaplib.IMAP4_SSL(imap_url)
    imap.login(email_address, password)
    imap.select("Inbox")
    result, data = imap.search(None, 'UNSEEN')
    mail_ids = data[0]
    id_list = mail_ids.split()
    fan_on2 = False

    if id_list:
        latest_email_id = id_list[-1]
        result, data = imap.fetch(latest_email_id, "(RFC822)")
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True)
                    body = body.decode(part.get_content_charset())
                    if "YES" in body.upper() and not received:
                        received = True
                        fan_on2 = True
                        return fan_on2
    imap.close()
    return fan_on2

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
    value=20,
    size=50)

html_Div_Fan_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url,
                            id='lottie-gif', isStopped=True, isClickToPauseDisabled=True)], id='fan_display')
html_Fan_Status_Message = html.H5(
    id='fan_status_message', style={'text-align': 'center'})
html_Fan_Label = html.H6("Electric Fan", style={'text-align': 'center'})

html_Light_Intensity_Label = html.H6(
    'Light Intensity', style={'text-align': 'center'})
html_Led_Status_Message = html.H1(
    id='light_h1', style={'text-align': 'center'})

html_Celcius_Label = html.H6('Celcius', style={'text-align': 'center'})
html_Fahrenheit_Label = html.H6('Fahrenheit', style={'text-align': 'center'})

fan_Status_Message_Interval = dcc.Interval(
    id='fan_status_message_update',
    disabled=False,
    interval=1 * 3000,
    n_intervals=0)

fan_Interval = dcc.Interval(
    id='fan-update',
    disabled=False,
    interval=1 * 8000,
    n_intervals=0)

humidity_Interval = dcc.Interval(
    id='humid-update',
    disabled=False,
    interval=1 * 3000,
    n_intervals=0)

temperature_Interval = dcc.Interval(
    id='temp-update',
    disabled=False,
    interval=1*20000,
    n_intervals=0)

light_Intensity_Interval = dcc.Interval(
    id='light-intensity-update',
    disabled=False,
    interval=1*5000,
    n_intervals=0)

led_On_Email_Interval = dcc.Interval(
    id='led-email-status-update',
    disabled=False,
    interval=1*5000,
    n_intervals=0)

user_data_interval = dcc.Interval(
    id='user_data_interval',
    interval=2000,  # 5 seconds interval
    n_intervals=0
)

user_info = dcc.Interval(
    id='user_info',
    disabled=False,
    interval=1*2000,
    n_intervals=0)

fahrenheit_Interval = dcc.Interval(
    id='fahrenheit-update',
    disabled=False,
    interval=1*2000,
    n_intervals=0)

sidebar = html.Div([
    html.H3('User Profile', style={'text-align': 'center'}),
    dbc.CardBody([
        html.Img(src='https://legendary-digital-network-assets.s3.amazonaws.com/wp-content/uploads/2021/12/12191403/Spider-Man-No-Way-Home-Miles-Morales.jpg', id="picture", style={'border-radius': '80px', 'width': '140px', 'height': '140px',
                                                                                                                                                                                    'object-fit': 'cover', 'display': 'block', 'margin-left': 'auto',
                                                                                                                                                                                    'margin-right': 'auto'}),
        html.H6("Username:" + str(id),
                style={'margin-top': '30px'}, id="username_data"),
        html.H4("Favorites ", style={'margin-top': '40px'}),
        html.H6("Humidity: " + str(humidity),
                style={'margin-left': '15px'}, id="humidity_data"),
        html.H6("Temperature: " + str(temp_threshold),
                style={'margin-left': '15px'}, id="temperature_data"),
        html.H6("Light Intensity: " + str(light_threshold),
                style={'margin-left': '15px'}, id="lightintensity_data")
    ])
])

card_content1 = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    html.H1(
                        html.B("Dash Components"),
                        className="text-center mt-4 mb-2",
                    )
                )
            ]
        ),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.Col(daq_Gauge), color="white", inverse=True, style={
                    "width": "30rem", 'height': "22rem"}), width="auto"),
            dbc.Col(dbc.Card(dbc.Col(html.Div([daq_Thermometer,
                                               dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="white", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
            dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="white", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")],
            justify="center",
        ),
        dbc.Row([
            dbc.Col(dbc.Card(
                html.Div([
                         html_Light_Intensity_Label,
                         html.Img(id="light-bulb", src=bulb_off,
                                  style={'width': '80px', 'height': '110px',
                                         'display': 'block', 'margin-left': 'auto', 'margin-right': 'auto', 'margin-top': '10px'}),
                         daq_Led_Light_Intensity_LEDDisplay,
                         html.H5(id='email_heading', style={"text-align": "center"})]),
                color="white", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
        ],
            justify="center",
            className="mt-5"),
    ],
    fluid=True,)

content = html.Div([
    dbc.Row([
        card_content1,
        humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval,
        user_data_interval, fahrenheit_Interval, fan_Status_Message_Interval, fan_Interval
    ]),
])

app.layout = html.Div(style={'backgroundColor': 'palegreen'}, children=[
    dbc.Container([
        dbc.Row(navbar),
        dbc.Row([
            dbc.Col(sidebar, width=2),
            dbc.Col(content, width=10, className="bg-secondary")
        ], style={"height": "100vh"}),
    ], fluid=True)
])



@app.callback(Output('my-gauge-1', 'value'), Input('humid-update', 'n_intervals'))
def update_output(value):
    dht = DHT.DHT(DHTPin)
    while (True):
        for i in range(0, 15):
            chk = dht.readDHT11()
            if (chk is dht.DHTLIB_OK):
                break
            time.sleep(0.1)
        time.sleep(2)
        print("Humidity : %.2f \t \n" % (dht.humidity))
        return dht.humidity


@app.callback(
    [Output('my-thermometer-1', 'value'),
     Output('my-thermometer-1', 'min'),
     Output('my-thermometer-1', 'max'),
     Output('my-thermometer-1', 'scale'),
     Output('my-thermometer-1', 'units')],
    [Input('fahrenheit-switch', 'value'),
     Input('my-thermometer-1', 'value'),
     Input('temp-update', 'n_intervals')])
def update_output(switch_state, temp_value, interval_value):
    dht = DHT.DHT(DHTPin)
    while (True):
        for i in range(0, 15):
            chk = dht.readDHT11()
            if (chk is dht.DHTLIB_OK):
                break
            time.sleep(0.1)
        time.sleep(2)
        print("Temperature : %.2f \n" % (dht.temperature))
        temperature = dht.temperature
        global temp_email_sent
        if dht.temperature >= temp_threshold and temp_email_sent == False:
            sendEmail()
            temp_email_sent = True

        if switch_state:
            return (temperature * 1.8) + 32, 40, 120, {'start': 40, 'interval': 10}, 'F'
        else:
            return temperature, -40, 60, {'start': -40, 'interval': 10}, 'C'


# Callback for the Fan Lottie gif and status message
@app.callback([Output('fan_status_message', 'children'), Output('lottie-gif', 'isStopped')],
              Input('fan_status_message_update', 'n_intervals'))
def update_h1(n):
    user_replied_yes = user_answer()
    print("fan test", user_replied_yes)
    if user_replied_yes:
        GPIO.output(Motor1, GPIO.HIGH)
        return "Status: On", False

    else:
        return "Status: On", True


def update_fan(value):
    global received
    fan_on = user_answer()

    if fan_on:
        received = False
        GPIO.output(Motor1, GPIO.HIGH)

        return "Status: On", False
    else:
        GPIO.output(Motor1, GPIO.LOW)
        return "Status: On", True


@app.callback([Output('username_data', 'children'),
               Output('humidity_data', 'children'),
               Output('temperature_data', 'children'),
               Output('lightintensity_data', 'children'),
               Output('picture', 'src')],
              Input('user_data_interval', 'n_intervals'))
def update_user_info(n_intervals):
    print("rfid callback")
    # Check if RFID is detected
    if rfid_message:
        user_data = get_from_database(rfid_message)
        if user_data:
            return ("Username: " + str(user_data['username']),
                    "Humidity: " + str(user_data['humidity']),
                    "Temperature: " + str(user_data['temperature']),
                    "Light Intensity: " + str(user_data['light_intensity']),
                    user_data['profile_image'])
    # If no RFID detected or no user found, return the default values
    return "Username: " + str(id), "Humidity: 30", "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), profile

# Callback for light intensity


@app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))
def update_light_intensity(value):
    light_intensity = checkLight()
    print(light_intensity)
    return light_intensity

# Email methods


def sendEmail():
 # Set the subject and body of the email
    email_sender = 'fiacreiot23@gmail.com'
    email_password = 'rukeavdzcxviypic'
    email_receiver = 'fiacreiot23@gmail.com'
    subject = 'Subject: Turn on FAN'
    body = "The current temperature is over the limit would you like to turn on the fan?"

    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, em.as_string())


def sendLedStatusEmail():  # for LED
    email_sender = 'fiacreiot23@gmail.com'
    email_password = 'rukeavdzcxviypic'
    email_receiver = 'fiacreiot23@gmail.com'

    subject = "Subject: Light On"
    current_time = datetime.now()
    time = current_time.strftime("%H:%M")
    body = "The Light was on " + time
    message = subject + '\n\n' + body
    em = EmailMessage()
    em['From'] = email_sender
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(body)

    # Add SSL (layer of security)
    context = ssl.create_default_context()

    # Log in and send the email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, message)



def send_led_email_check(lightvalue):
    global email_counter
    if lightvalue < light_threshold and email_counter == 0:
        sendLedStatusEmail()
        email_counter += 1



@app.callback([Output('email_heading', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))
def update_email_status(value):
    lightvalue = esp_message
    send_led_email_check(lightvalue)

    if email_counter > 0 and lightvalue < light_threshold:
        GPIO.output(LedPin, GPIO.HIGH)
        return "Email has been sent. Lightbulb is ON", bulb_on
    elif email_counter > 0 and lightvalue > light_threshold:
        GPIO.output(LedPin, GPIO.LOW)
        return "Email has been sent. Lightbulb is OFF", bulb_off
    else:
        GPIO.output(LedPin, GPIO.LOW)
        return "No email has been sent. Lightbulb is OFF", bulb_off


if __name__ == '__main__':
    app.run_server(debug=True)
