import random
import smtplib
import time
from time import sleep
import Freenove_DHT as DHT
import smtplib, ssl, getpass, imaplib, email
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
import pymysql
import pymysql.cursors
import os
import sqlite3


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

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
light_intensity_value = 0
light_intensity_state = "OFF"
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
LedPin = 35
GPIO.setup(LedPin,GPIO.OUT)
led_email_sent_count = 0

# MQTT settings
port = 1883
client_id = f'python-mqtt-{random.randint(0, 100)}'
topic3 = "esp/rfid"
# client_id = "dashboard"

#phase 2
EMAIL = 'john190curry@gmail.com'
PASSWORD = 'CUURY23JOHN45'
SERVER= "smtp.gmail.com"

message = 0
DHTPin = 40
fan_status_checker=False

# info
id="Default"
temp_threshold = 25.0
light_threshold = 0
humidity = 30
profile='assets/profile.png'

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

# Set up the GPIO pins
m1 = 17
m2 = 27
m3 = 22

GPIO.setup(m1,GPIO.IN)
GPIO.setup(m2,GPIO.IN)
GPIO.setup(m3,GPIO.IN)

# bulb_off='https://cdn-icons-png.flaticon.com/512/32/32299.png'
# bulb_on="photos/BulbOn.jpg"
bulb_off= 'assets/lightbulbOff.png'
bulb_on= 'assets/lightbulbOn.png'

fan_off='assets/fanOff.png'
fan_on='assets/fanON.png'
url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json"
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))

#Components
daq_Gauge = daq.Gauge(
                id='my-gauge',
                label="Humidity",
                showCurrentValue=True,
                value = 62,
                size=200,
                max=100,
                min=0)

daq_Thermometer = daq.Thermometer(
                        id='my-thermometer',
                        min=-40,
                        value = 18,
                        max=160,
                        scale={'start': -40, 'interval': 25},
                        label="Temperature(Celsius)",
                        showCurrentValue=True,
                        units="C",
                        color="red")

daq_Fahrenheit_ToggleSwitch = daq.ToggleSwitch(
                    id='fahrenheit-switch',
                    value=False)

daq_light_display = daq.Knob(
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
html_Fan_Status_Message = html.H1(id='fan_message',style={'text-align':'center'})
html_Celcius_Label =  html.H6('Celcius',style={'text-align':'center'})
html_Fahrenheit_Label =  html.H6('Fahrenheit',style={'text-align':'center'})

# all related to light intensity and led
html_Light_Intensity_Label =  html.H1('LightIntensity',style={'text-align':'center'})
daq_light_display = daq.Knob(
                        id='light-intensity',
                        label="Light Intensity",
                        value = 10, size=64)
html_Led_Status_Message = html.H1(id='light_h1',style={'text-align':'center'})  #not used yet
# intervals
# # the fan status interval for each Messag
fan_Interval_Status = dcc.Interval(
            id='fan_status_message',
            disabled=False,
            interval=5*1000, # 10 seconds
            fanStatus_intervals=0)
            # max_intervals=-1, # -1 goes on forever no max          
fan_Interval = dcc.Interval(
            id = 'fan_Update',
            disabled=False,
            interval = 1*8000,  
            fan_intervals = 0)
            
humidity_Interval = dcc.Interval(
            id = 'humidity',
            disabled=False,
            interval = 1*3000,  #lower than 3000 for humidity wouldn't show the humidity on the terminal
            humidity_interv = 0)
temperature_Interval =  dcc.Interval(
            id = 'temperature',
            disabled=False,
            interval = 1*8000,   #lower than 5000 for temperature wouldn't show the temp on the terminal #1800000 equivalent to 30 mins
            temp_intervals = 0)
light_Intensity_Interval =  dcc.Interval(
            id = 'light_Intensity',
            disabled=False,
            interval = 1*1000,   
            Light_intervals = 0)
# led email sender intrevals 
led_Email_Interval = dcc.Interval(
            id = 'led_Email',
            disabled=False,
            interval = 1*2000,   
            led_intervals = 0)
# user intervals 
user_info = dcc.Interval(
            id = 'user_info',
            disabled=False,
            interval = 1*2000,   
            user_intervals = 0)
# Layout
sidebar = html.Div([
    html.H3('User Profile', style={'text-align': 'center'}),
    dbc.CardBody([
        html.Img(src='profile',id="picture", style={'border-radius': '80px', 'width': '140px', 'height': '140px',
                                               'object-fit': 'cover', 'display': 'block', 'margin-left': 'auto',
                                               'margin-right': 'auto'}),
        html.H6("Username:" + str(id), style={'margin-top':'30px'}, id="username_data"),
            html.H4("Favorites ", style={'margin-top':'40px'}),
            html.H6("Humidity: " + str(humidity), style={'margin-left':'15px'}, id="humidity_data"),
            html.H6("Temperature: " + str(temp_threshold), style={'margin-left':'15px'}, id="temperature_data"),
            html.H6("Light Intensity: " + str(light_threshold), style={'margin-left':'15px'}, id="lightintensity_data")
            ])
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

card_container_content = dbc.Container(
    [
        dbc.Col(
            html.H2(
                "Product Features",
                className="text-center mt-3 mb-2",
            )
        ),
        dbc.Col(
            html.Ul(
                [
                    html.Li("Easy to install"),
                    html.Li("Smartphone compatible"),
                    html.Li("Energy-efficient"),
                    html.Li("Customizable settings"),
                ]
            ),
            width=6,
            className="mt-3",
        ),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.Col(daq_Gauge), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
            dbc.Col(dbc.Card(dbc.Col(html.Div([daq_Thermometer,
                                               dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)]) ])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
            dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")],
            justify="center",
        ),
        dbc.Row([
            dbc.Col(dbc.Card(
                     html.Div([
                        html_Light_Intensity_Label,
                        html.Img(id="light-bulb", src=bulb_off,
                                  style={'width':'80px', 'height': '110px',
                                  'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}),
                        
                        daq_light_display,
                        html.H5(id='email_heading',style ={"text-align":"center"}) ]),
                        
                        color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")],
            justify="center",
        className="mt-5"),
    ],
    fluid=True,)

content = html.Div([
           dbc.Row([
                card_container_content,html_Div_Fan_Gif, html_Fan_Status_Message,
                fan_Interval_Status,humidity_Interval, temperature_Interval, light_Intensity_Interval, 
                led_Email_Interval,fan_Interval,
            ]),
        ])

# ''' the Dashboard Layout '''
app.layout = html.Div(style={'backgroundColor': 'palegreen'}, children=[
    dbc.Container([
        dbc.Row(navbar),
        dbc.Row([
            dbc.Col(sidebar, width=2),
            dbc.Col(content, width=10, className="bg-secondary")
        ], style={"height": "100vh"}),
    ], fluid=True)
])
# Callback for the temperature
@app.callback(Output('my-gauge', 'value'), Input('humidity', 'humidity_interv'))
def update_temperature(value):
    dht = DHT.DHT(DHTPin)
    while(True):
        for i in range(0,15):
            chk = dht.readDHT11()
            if (chk is dht.DHTLIB_OK):
                break
            time.sleep(0.1)
        time.sleep(2)
        print("Temperature : %.2f \t \n"%(dht.temperature))
        return dht.temperature

# Callback for thermometers and Celsius to Fahrenheit conversion
@app.callback(
    [Output('thermometer', 'value'),
     Output('thermometer', 'min'),
     Output('thermometer', 'max'),
     Output('thermometer', 'scale'),
     Output('thermometer', 'units')],
    [Input('fahrenheit-switch', 'value'),
     Input('thermometer', 'value'),
     Input('temperature', 'temp_intervals')])

def update_output(switch_state, temp_value, interval_value):
    dht = DHT.DHT(DHTPin)
    while(True):
        for i in range(0, 15):
            chk = dht.readDHT11()
            if chk is dht.DHTLIB_OK:
                break
            time.sleep(0.1)
        time.sleep(2)
        temperature = dht.temperature
        humidity = dht.humidity
        print("Temperature : %.2f\nHumidity : %.2f\n" % (dht.temperature, dht.humidity))
        global temp_email_sent
        if dht.temperature >= temp_threshold and temp_email_sent == False:
            sendEmail()
            temp_email_sent = True
        if switch_state:
            return (temperature * 1.8) + 32, 40, 120, {'start': 40, 'interval': 10}, 'F', humidity, 0, 100, {'start': 0, 'interval': 10}, '%'
        else:
            return temperature, -40, 60, {'start': -40, 'interval': 10}, 'C', humidity, 0, 100, {'start': 0, 'interval': 10}, '%'

#Email methods
def sendEmail(): #for temperature
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "john190curry@gmail.com"
        receiver_email = "john190curry@gmail.com"
        password = 'JOHN23CUURY45'
        subject = "Subject: FAN CONTROL" 
        body = "temperature greater than the desired threshold. Turn on the fan? Reply YES if so."
        message = subject + '\n\n' + body
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
    
# Checks if the motor set on is active or not
def set_on():
    if not GPIO.input(m1) and GPIO.input(m2) and not GPIO.input(m3):
        return True
    else:
        return False

# Callback for the Fan Lottie gif and status message
@app.callback([Output('fan_message', 'children'), Output('lottie-gif', 'isStopped')],
              Input('fan_status_message', 'fanStatus_intervals'))
def update_h1(n):
    checker_on = set_on()
    
    if checker_on:
        print("The pump is on.")
    else:
        print("The pump is off.")

# update the dashboard 
@app.callback([Output('username_data', 'children'),
               Output('humidity_data', 'children'),
               Output('temperature_data', 'children'),
               Output('lightintensity_data', 'children'),
               Output('picture', 'src')],
               Input('user_info', 'user_intervals'))

def user_Info_Update(n):
    return "Username: " + str(id) ,"Humidity: 30" ,"Temperature: " +  str(temp_threshold), "Light Intensity: " + str(light_threshold), profile

@app.callback(Output('my-light-intensity-slider', 'value'),
              Input('light_Intensity', 'Light_intervals'))
def update_output(value):
    global light_intensity_value
    if light_intensity_value < 400:
        send_led_email_check(light_intensity_state)
    return light_intensity_value, light_intensity_value

# for LED
def sendEmailLed():
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "john190curry@gmail.com"
        receiver_email = "john190curry@gmail.com"
        password = 'JOHN23CUURY45'
        subject = "Subject: light Notification" 
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

# MQTT
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

# MQTT for light intensity
def on_message(client, userdata, message):
    global light_intensity_value, light_intensity_state
    if message.topic == topic1:
        light_intensity_value = int(float(message.payload.decode()))
        print(light_intensity_value)
    elif message.topic == topic2:
        light_intensity_state = message.payload.decode()
        print(light_intensity_state)

# Database code caller
def get_from_database(rfid):
    conn = sqlite3.connect('example.db')
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
       global  picture
       picture = user_info[3]
       
       # Print the retrieved user information to the console
       print('Retrieved user information:')
       print('User ID:', user_id)
       print('Temperature threshold:', temp_threshold)
       print('Light threshold:', light_threshold)
       print('Path to picture:', picture)
    
    # If no user was found, print a message to the console
    else:
        print('No user found with RFID tag ID:', rfid)
        
    print(str(user_id) + " " + str(temp_threshold) + " " + str(light_threshold) + " " + path_to_picture)

def sendEmailRfid(name):
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        sender_email = "john190curry@gmail.com"
        receiver_email = "john190curry@gmail.com"
        password = 'JOHN23CUURY45'
        subject = "Subject: light Notification" 
        current_time = datetime.now()
        time = current_time.strftime("%H:%M")
        body = name + " has entered at: " + time
        message = subject + '\n\n' + body
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

# Function to read RFID tags
def on_message_from_rfid(client, userdata, message):
   global esp_rfid_message
   esp_rfid_message = message.payload.decode()
   print("Message Received from rfid: ")
   print(esp_rfid_message)
   get_from_database(esp_rfid_message)
   sendEmailRfid(esp_rfid_message)

def run():
    client = connect_mqtt()
    client.subscribe(topic1, qos=1)
    client.subscribe(topic2, qos=1)
    client.message_callback_add(topic1, on_message)
    client.message_callback_add(topic2, on_message_from_rfid)
    client.loop_start()
    
# Checks if the light intensity value is lower than the user's desired threshold and send email and increase the email counter to know there is an email sent
def send_led_email_check(lightvalue):
    global email_counter
    if lightvalue < light_threshold and email_counter == 0:
        print("passed here in send_led_email_check")
        sendEmailLed()
        email_counter += 1

#Callback to change the lightbulb image & lightbulb status and update email sent message
@app.callback([Output('email_heading', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))      
def update_email_status(value):
    lightvalue = message
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

def update_stylesheet(modified_timestamp, theme):
    return dbt.themes[theme]

if __name__ == '__main__':
    run()
    app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)