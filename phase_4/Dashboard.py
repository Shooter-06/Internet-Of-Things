# Standard library imports
import random
import smtplib
import ssl
import time
from datetime import datetime

# Third-party imports
import dash
import RPi.GPIO as GPIO
from PIL import Image
from dash import Dash, html, Input, Output
import dash_bootstrap_components as dbc
# import dash_core_components as dcc
from dash import dcc
# import dash_html_components as html
from dash import html
from dash.dependencies import Input, Output
import dash_bootstrap_templates as dbt
import dash_extensions as de
import dash_daq as daq
from paho.mqtt import client as mqtt_client
import Freenove_DHT as DHT

# Import additional necessary libraries
import MFRC522
import json
import paho.mqtt.publish as publish
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Set up theme toggle button and theme store
theme_toggle_button = dbc.Button("Change Theme", id="theme-toggle", color="danger")
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
#phase 4 -- RFID Setup
reader = MFRC522.MFRC522()
user_profiles = {} # Store user profiles
user_data = {} # Store user data


#phase 3
broker = '192.168.2.67'
topic1 = "esp/lightIntensity"
topic2 = "esp/lightswitch"
topic3 = "esp/rfid"
client_id = f'python-mqtt-{random.randint(0, 100)}'
light_intensity_value = 0
light_intensity_state = "OFF"
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
LedPin = 35
GPIO.setup(LedPin,GPIO.OUT)
led_email_sent_count = 0

# MQTT settings
port = 1883
topic1 = "lightIntensity"
# client_id = "dashboard"

#phase 2
EMAIL = 'john190curry@gmail.com'
PASSWORD = 'CUURY23JOHN45'
SERVER= "smtp.gmail.com"

temperature = 0
DHTPin = 40
fan_status_checker=False

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
Motor1 = 35
Motor2 = 37
Motor3 = 33

GPIO.setup(Motor1,GPIO.IN)
GPIO.setup(Motor2,GPIO.IN)
GPIO.setup(Motor3,GPIO.IN)

bulb_off='https://cdn-icons-png.flaticon.com/512/32/32299.png'
bulb_on="photos/BulbOn.jpg"

url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json"
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))

#Components
daq_Gauge = daq.Gauge(
                id='my-gauge-1',
                label="Humidity",
                showCurrentValue=True,
                value = 62,
                size=200,
                max=100,
                min=0)

daq_Thermometer = daq.Thermometer(
                        id='my-thermometer-1',
                        min=-40,
                        value = 18,
                        max=160,
                        scale={'start': -40, 'interval': 25},
                        label="Temperature(Celsius)",
                        showCurrentValue=True,
                        units="C",
                        color="red")

daq_Fan = daq.Knob(
                id='my-fan',
                min=0,
                value=0,
                max=100,
                label="Fan Speed (%)",
                color="blue",
                scale={'start': 0, 'interval': 10, 'labelInterval': 2},
                size=200)

html_Button_Celcius_To_Fahrenheit =  html.Button('Fahrenheit', id='fahrenheit-button', n_clicks=0, style={'width':'20%'})

# all fan related html
html_Fan_Label = html.H6('Fan',style={'text-align':'center'})
html_Div_Fan_Gif = html.Div([de.Lottie(options=options, width="25%", height="25%", url=url)], id='my-gif', style={'display':'none'})
html_Fan_Status_Message = html.H1(id='fan_status_message',style={'text-align':'center'})

# all related to light intensity and led
html_Light_Intensity_Label =  html.H1('LightIntensity',style={'text-align':'center'})
daq_Led_Light_Intensity_LEDDisplay = daq.LEDDisplay(
                                        id='light-intensity',
                                        label="Light Intensity",
                                        value = 10, size=64)
html_Led_Status_Message = html.H1(id='light_h1',style={'text-align':'center'})  #not used yet

# intervals
fan_Status_Message_Interval = dcc.Interval(
            id='fan_status_message_update',
            disabled=False,
            interval=5*1000, # 10 seconds
            n_intervals=0)
            # max_intervals=-1, # -1 goes on forever no max
            
fan_Interval = dcc.Interval(
            id = 'fan-update',
            disabled=False,
            interval = 1*8000,  
            n_intervals = 0)
            
humidity_Interval = dcc.Interval(
            id = 'humid-update',
            disabled=False,
            interval = 1*3000,  #lower than 3000 for humidity wouldn't show the humidity on the terminal
            n_intervals = 0)

temperature_Interval =  dcc.Interval(
            id = 'temp-update',
            disabled=False,
            interval = 1*8000,   #lower than 5000 for temperature wouldn't show the temp on the terminal #1800000 equivalent to 30 mins
            n_intervals = 0)

light_Intensity_Interval =  dcc.Interval(
            id = 'light-intensity-update',
            disabled=False,
            interval = 1*1000,   
            n_intervals = 0)

led_On_Email_Interval = dcc.Interval(
            id = 'led-email-status-update',
            disabled=False,
            interval = 1*2000,   
            n_intervals = 0)

# Layout
sidebar = html.Div([
    html.H3('User Profile', style={'text-align': 'center'}),
    dbc.CardBody([
        html.Img(src='https://cdn4.iconfinder.com/data/icons/small-n-flat/24/user-512.png', style={'border-radius': '80px', 'width': '140px', 'height': '140px',
                                               'object-fit': 'cover', 'display': 'block', 'margin-left': 'auto',
                                               'margin-right': 'auto'}),
        html.H6("Username"),
        html.H4("Favorites: "),
        html.H6("Humidity"),
        html.H6("Temperature"),
        html.H6("Light Intensity")])
])

light_intensity_slider = daq.Slider(
    id='my-light-intensity-slider',
    min=200,
    max=600,
    value=light_intensity_value,
    step=1,
    handleLabel={"showCurrentValue": True, "label": "VALUE"},
    marks={
        200: '200',
        400: '400',
        600: '600'
    },
    included=False,
)

content = html.Div([
    dbc.Row([
        dbc.Col(dbc.Row([daq_Gauge, daq_Thermometer, daq_Fan, html_Div_Fan_Gif, html_Fan_Status_Message]), width=5),
        dbc.Col(dbc.Row([daq_Led_Light_Intensity_LEDDisplay, light_intensity_slider, html.Img(id="light-bulb", src=bulb_off,
                                                                      style={'width': '100px', 'height': '100px',
                                                                             'display': 'block', 'margin-left': 'auto',
                                                                             'margin-right': 'auto',
                                                                             'margin-top': '10px'}),
                         html.H1(id='email_h1', style={"text-align": "center"})]), width=4,
                className="border border-secondary"),
        fan_Status_Message_Interval, humidity_Interval, temperature_Interval, light_Intensity_Interval,
        led_On_Email_Interval
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

# Callbacks
# @app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))
# def update_output(value):
#     global light_intensity_value
#     return light_intensity_value

@app.callback([Output('email_h1', 'children'), Output('light-bulb', 'src')],
              Input('led-email-status-update', 'n_intervals'))
def update_email_status(value):
    send_led_email_check(light_intensity_state)
    if led_email_sent_count > 0:
        return "Email has been sent. Lightbulb is ON", bulb_on
    else:
        return "No email has been sent. Lightbulb is OFF", bulb_off


@app.callback(Output('light-intensity', 'value'),
              Output('my-light-intensity-slider', 'value'),
              Input('light-intensity-update', 'n_intervals'))
def update_output(value):
    global light_intensity_value
    if light_intensity_value < 400:
        send_led_email_check(light_intensity_state)
    return light_intensity_value, light_intensity_value


def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            time.sleep(5)
        else:
            print("Failed to connect, return code %d\n", rc)
    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port, keepalive=60) # Added a keep alive paramater to increase timeout duration
    return client

def on_message(client, userdata, message):
    global light_intensity_value, light_intensity_state
    if message.topic == topic1:
        light_intensity_value = int(float(message.payload.decode()))
        print(light_intensity_value)
    elif message.topic == topic2:
        light_intensity_state = message.payload.decode()
        print(light_intensity_state)

# Function to read RFID tags
def read_rfid():
    (status, tag_type) = reader.MFRC522_Request(reader.PICC_REQIDL)
    if status == reader.MI_OK:
        (status, uid) = reader.MFRC522_Anticoll()
        if status == reader.MI_OK:
            card_id = f"{uid[0]}{uid[1]}{uid[2]}{uid[3]}"
            return card_id
    return None

# Function to load user profiles
def load_user_profiles():
    global user_profiles
    try:
        with open("user_profiles.json", "r") as f:
            user_profiles = json.load(f)
    except FileNotFoundError:
        user_profiles = {}

# Function to save user profiles
def save_user_profiles():
    global user_profiles
    with open("user_profiles.json", "w") as f:
        json.dump(user_profiles, f)

# Function to send email notification
def send_email_notification(username, time):
    message = MIMEMultipart("alternative")
    message["Subject"] = f"User {username} entered at {time}"
    message["From"] = EMAIL
    message["To"] = EMAIL

    # Create the plain-text and HTML version of your message
    text = f"User {username} entered at {time}"
    html = f"<html><body><p>User <strong>{username}</strong> entered at {time}</p></body></html>"

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    message.attach(part1)
    message.attach(part2)

    # Send the message
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SERVER, 465, context=context) as server:
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, EMAIL, message.as_string())

# Load user profiles initially
load_user_profiles()

# Add a new interval for RFID
rfid_interval = dcc.Interval(id='rfid-update', disabled=False, interval=1*1000, n_intervals=0)
content.children.append(rfid_interval)

# Add RFID card_id to user_profiles when a new card is read
@app.callback(Output('rfid-update', 'n_intervals'),
              Input('rfid-update', 'n_intervals'))
def rfid_update(value):
    card_id = read_rfid()
    if card_id and card_id not in user_profiles:
        # Add a new user to the user_profiles dictionary
        user_profiles[card_id] = {
            "username": f"User{len(user_profiles)}",
            "favorites": {
                "humidity": 50,
                "temperature": 25,
                "light_intensity": 300
            }
        }
        save_user_profiles()

    return value 

@app.callback(
    [Output('sidebar-username', 'children'),
     Output('sidebar-humidity', 'children'),
     Output('sidebar-temperature', 'children'),
     Output('sidebar-light_intensity', 'children')],
    Input('rfid-tag', 'data')
)
def update_user_profile(rfid_tag):
    if rfid_tag in user_data:
        user = user_data[rfid_tag]
        return user['username'], user['humidity'], user['temperature'], user['light_intensity']
    else:
        return "Unknown", "", "", ""
 
def sendLedStatusEmail():
         print("PASSED BY SENDLEDSTATUSEMAIL method")
         port = 587  # For starttls
         smtp_server = "smtp.gmail.com"
         sender_email = "john190curry@gmail.com"
         receiver_email = "john190curry@gmail.com"
         password = 'iotpassword123'
         subject = "Subject: LIGHT NOTIFICATION" 
         current_time = datetime.now()
         time = current_time.strftime("%H:%M")
         body = "The Light is ON at " + time
         message = subject + '\n\n' + body
         context = ssl.create_default_context()
         with smtplib.SMTP(smtp_server, port) as server:
             server.ehlo()  # Can be omitted
             server.starttls(context=context)
             server.ehlo()  # Can be omitted
             server.login(sender_email, password)
             server.sendmail(sender_email, receiver_email, message)
        
def run():
    client = connect_mqtt()
    client.subscribe(topic1, qos=1)
    client.subscribe(topic2, qos=1)
    client.on_message = on_message
    client.loop_start()

def send_led_email_check(value):
    global led_email_sent_count
    if value == "ON" and led_email_sent_count == 0:
        sendLedStatusEmail()
        led_email_sent_count += 1


def update_stylesheet(modified_timestamp, theme):
    return dbt.themes[theme]

if __name__ == '__main__':
    run()
    app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)





# from dash import Dash, html, dcc, Input, Output
# import dash_bootstrap_components as dbc
# # import dash_core_components as dcc
# # from dash import dcc
# import dash
# # import dash_html_components as html
# from dash.dependencies import Input, Output
# import dash_bootstrap_templates as dbt
# import dash_extensions as de
# import dash_daq as daq
# import RPi.GPIO as GPIO
# from PIL import Image
# import time
# from time import sleep
# import Freenove_DHT as DHT
# import smtplib, ssl
# import random
# from paho.mqtt import client as mqtt_client
# from datetime import datetime

# app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# # Set up theme toggle button and theme store
# theme_toggle_button = dbc.Button("Change Theme", id="theme-toggle", color="danger")
# theme_store = dcc.Store(id="theme-store", storage_type="local", data="default")

# # Set up the navbar
# navbar = dbc.NavbarSimple(
#     children=[
#         dbc.NavItem(theme_toggle_button),
#     ],
#     brand="Fiacre DashBoard",
#     color="blue",
#     dark=True,
#     sticky="top"
# )

# #------------PHASE03 VARIABLE CODES--------------
# broker = '192.168.2.67' 
# port = 1883
# topic1 = "esp/lightIntensity"
# topic2 = "esp/lightswitch"
# client_id = f'python-mqtt-{random.randint(0, 100)}'
# light_intensity_value = 0
# light_intensity_state = "OFF"
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# LedPin = 35 # Led Pin/Enable Pin
# GPIO.setup(LedPin,GPIO.OUT)
# led_email_sent_count = 0
# # -----------------------------------------------
# # MQTT settings
# port = 1883
# topic1 = "lightIntensity"
# client_id = "dashboard"

# # Global variables
# light_intensity_value = 0
# light_intensity_state = ""
# led_email_sent_count = 0
# #------------PHASE02 VARIABLE CODES--------------
# EMAIL = 'john190curry@gmail.com'
# PASSWORD = 'CUURY23JOHN45'

# SERVER= "smtp.gmail.com"

# temperature = 0
# DHTPin = 40 # equivalent to GPIO21
# fan_status_checker=False

# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# Motor1 = 35 # Enable Pin
# Motor2 = 37 # Input Pin
# Motor3 = 33 # Input Pin

# GPIO.setup(Motor1,GPIO.IN)
# GPIO.setup(Motor2,GPIO.IN)
# GPIO.setup(Motor3,GPIO.IN)

# bulb_off='https://cdn-icons-png.flaticon.com/512/32/32299.png'
# bulb_on="photos/BulbOn.jpg"

# # bulb_off = 'ph/Ppic.jpg'        
# # bulb_on = 'assets/Ppic.jpg' 

# url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json"
# options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))

# # -----------------------------------------------
# #Components

# daq_Gauge = daq.Gauge(
#                 id='my-gauge-1',
#                 label="Humidity",
#                 showCurrentValue=True,
#                 value = 62,
#                 size=200,
#                 max=100,
#                 min=0)

# daq_Thermometer = daq.Thermometer(
#                         id='my-thermometer-1',
#                         min=-40,
#                         value = 18,
#                         max=160,
#                         scale={'start': -40, 'interval': 25},
#                         label="Temperature(Celsius)",
#                         showCurrentValue=True,
#                         units="C",
#                         color="red")

# daq_Fan = daq.Knob(
#                 id='my-fan',
#                 min=0,
#                 value=0,
#                 max=100,
#                 label="Fan Speed (%)",
#                 color="blue",
#                 scale={'start': 0, 'interval': 10, 'labelInterval': 2},
#                 size=200)
                        
# html_Button_Celcius_To_Fahrenheit =  html.Button('Fahrenheit', id='fahrenheit-button', n_clicks=0, style={'width':'20%'})

# # all fan related html
# html_Fan_Label = html.H6('Fan',style={'text-align':'center'})
# html_Div_Fan_Gif = html.Div([de.Lottie(options=options, width="25%", height="25%", url=url)], id='my-gif', style={'display':'none'})
# html_Fan_Status_Message = html.H1(id='fan_status_message',style={'text-align':'center'})

# # all related to light intensity and led
# html_Light_Intensity_Label =  html.H1('LightIntensity',style={'text-align':'center'})
# daq_Led_Light_Intensity_LEDDisplay = daq.LEDDisplay(
#                                         id='light-intensity',
#                                         label="Light Intensity",
#                                         value = 10, size=64)
# html_Led_Status_Message = html.H1(id='light_h1',style={'text-align':'center'})  #not used yet

# # intervals
# fan_Status_Message_Interval = dcc.Interval(
#             id='fan_status_message_update',
#             disabled=False,
#             interval=5*1000, # 10 seconds
#             n_intervals=0)
#             # max_intervals=-1, # -1 goes on forever no max
            
# fan_Interval = dcc.Interval(
#             id = 'fan-update',
#             disabled=False,
#             interval = 1*8000,  
#             n_intervals = 0)
            
# humidity_Interval = dcc.Interval(
#             id = 'humid-update',
#             disabled=False,
#             interval = 1*3000,  #lower than 3000 for humidity wouldn't show the humidity on the terminal
#             n_intervals = 0)

# temperature_Interval =  dcc.Interval(
#             id = 'temp-update',
#             disabled=False,
#             interval = 1*8000,   #lower than 5000 for temperature wouldn't show the temp on the terminal #1800000 equivalent to 30 mins
#             n_intervals = 0)

# light_Intensity_Interval =  dcc.Interval(
#             id = 'light-intensity-update',
#             disabled=False,
#             interval = 1*1000,   
#             n_intervals = 0)

# led_On_Email_Interval = dcc.Interval(
#             id = 'led-email-status-update',
#             disabled=False,
#             interval = 1*2000,   
#             n_intervals = 0)


# # Layout
# sidebar = html.Div([
#     html.H3('User Profile', style={'text-align': 'center'}),
#     dbc.CardBody([
#         html.Img(src='https://cdn4.iconfinder.com/data/icons/small-n-flat/24/user-512.png', style={'border-radius': '80px', 'width': '140px', 'height': '140px',
#                                                'object-fit': 'cover', 'display': 'block', 'margin-left': 'auto',
#                                                'margin-right': 'auto'}),
#         html.H6("Username"),
#         html.H4("Favorites: "),
#         html.H6("Humidity"),
#         html.H6("Temperature"),
#         html.H6("Light Intensity")])
# ])

# light_intensity_slider = daq.Slider(
#     id='my-light-intensity-slider',
#     min=200,
#     max=600,
#     value=light_intensity_value,
#     step=1,
#     handleLabel={"showCurrentValue": True, "label": "VALUE"},
#     marks={
#         200: '200',
#         400: '400',
#         600: '600'
#     },
#     included=False,
# )

# content = html.Div([
#     dbc.Row([
#         dbc.Col(dbc.Row([daq_Gauge, daq_Thermometer, daq_Fan, html_Div_Fan_Gif, html_Fan_Status_Message]), width=5),
#         dbc.Col(dbc.Row([daq_Led_Light_Intensity_LEDDisplay, light_intensity_slider, html.Img(id="light-bulb", src=bulb_off,
#                                                                       style={'width': '100px', 'height': '100px',
#                                                                              'display': 'block', 'margin-left': 'auto',
#                                                                              'margin-right': 'auto',
#                                                                              'margin-top': '10px'}),
#                          html.H1(id='email_h1', style={"text-align": "center"})]), width=4,
#                 className="border border-secondary"),
#         fan_Status_Message_Interval, humidity_Interval, temperature_Interval, light_Intensity_Interval,
#         led_On_Email_Interval
#     ]),
# ])

# # content = html.Div([
# #     dbc.Row([
# #         dbc.Col(dbc.Row([daq_Gauge, daq_Thermometer,daq_Fan, html_Div_Fan_Gif, html_Fan_Status_Message]), width=5),
# #         # dbc.Col(dbc.Row([daq_Fan, daq.Knob, html_Div_Fan_Gif, html_Fan_Status_Message]), width=5),
# #         dbc.Col(dbc.Row([daq_Led_Light_Intensity_LEDDisplay, html.Img(id="light-bulb", src=bulb_off,
# #                                                                       style={'width': '100px', 'height': '100px',
# #                                                                              'display': 'block', 'margin-left': 'auto',
# #                                                                              'margin-right': 'auto',
# #                                                                              'margin-top': '10px'}),
# #                          html.H1(id='email_h1', style={"text-align": "center"})]), width=4,
# #                 className="border border-secondary"),
# #         fan_Status_Message_Interval, humidity_Interval, temperature_Interval, light_Intensity_Interval,
# #         led_On_Email_Interval
# #     ]),
# # ])

# app.layout = html.Div(style={'backgroundColor': 'palegreen'}, children=[

#     dbc.Container([
#     dbc.Row(navbar),
#     dbc.Row([
#             dbc.Col(sidebar, width=2),
#             dbc.Col(content, width=10, className="bg-secondary")
#         ], style={"height": "100vh"}),
#     ], fluid=True)
# ])

# # app.layout = dbc.Container([
# #     dbc.Row(navbar),
# #     dbc.Row([
# #         dbc.Col(sidebar, width=2),
# #         dbc.Col(content, width=10, className="bg-secondary")
# #     ], style={"height": "100vh"}),
# # ], fluid=True)

# # Callbacks
# # @app.callback(Output('light-intensity', 'value'),
# #               Output('my-light-intensity-slider', 'value'),
# #               Input('light-intensity-update', 'n_intervals'))

# @app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))
# def update_output(value):
#     global light_intensity_value
#     return light_intensity_value

# @app.callback([Output('email_h1', 'children'), Output('light-bulb', 'src')],
#               Input('led-email-status-update', 'n_intervals'))
# def update_email_status(value):
#     send_led_email_check(light_intensity_state)
#     if led_email_sent_count > 0:
#         return "Email has been sent. Lightbulb is ON", bulb_on
#     else:
#         return "No email has been sent. Lightbulb is OFF", bulb_off


# @app.callback(Output('light-intensity', 'value'),
#               Output('my-light-intensity-slider', 'value'),
#               Input('light-intensity-update', 'n_intervals'))
# def update_output(value):
#     global light_intensity_value
#     if light_intensity_value < 400:
#         send_led_email_check(light_intensity_state)
#     return light_intensity_value, light_intensity_value

# def connect_mqtt() -> mqtt_client:
#     def on_connect(client, userdata, flags, rc):
#         if rc == 0:
#             print("Connected to MQTT Broker!")
#             time.sleep(5)
#         else:
#             print("Failed to connect, return code %d\n", rc)
#     client = mqtt_client.Client(client_id)
#     client.on_connect = on_connect
#     client.connect(broker, port, keepalive=60) # Added a keep alive paramater to increase timeout duration
#     return client

# def on_message(client, userdata, message):
#     global light_intensity_value, light_intensity_state
#     if message.topic == topic1:
#         light_intensity_value = int(float(message.payload.decode()))
#         print(light_intensity_value)

# def sendLedStatusEmail():
#          print("PASSED BY SENDLEDSTATUSEMAIL method")
#          port = 587  # For starttls
#          smtp_server = "smtp-mail.outlook.com"
#          sender_email = "iotdashboard2022@outlook.com"
#          receiver_email = "iotdashboard2022@outlook.com"
#          password = 'iotpassword123'
#          subject = "Subject: LIGHT NOTIFICATION" 
#          current_time = datetime.now()
#          time = current_time.strftime("%H:%M")
#          body = "The Light is ON at " + time
#          message = subject + '\n\n' + body
#          context = ssl.create_default_context()
#          with smtplib.SMTP(smtp_server, port) as server:
#              server.ehlo()  # Can be omitted
#              server.starttls(context=context)
#              server.ehlo()  # Can be omitted
#              server.login(sender_email, password)
#              server.sendmail(sender_email, receiver_email, message)
        
# def run():
#     client = connect_mqtt()
#     client.subscribe(topic1, qos=1)
#     client.subscribe(topic2, qos=1)
#     client.on_message = on_message
#     client.loop_start()

# def send_led_email_check(value):
#     global led_email_sent_count
#     if value == "ON" and led_email_sent_count == 0:
#         sendLedStatusEmail()
#         led_email_sent_count += 1


# def update_stylesheet(modified_timestamp, theme):
#     return dbt.themes[theme]

# if __name__ == '__main__':
#     run()
#     app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)  # Move the app.run_server() inside the run() function
