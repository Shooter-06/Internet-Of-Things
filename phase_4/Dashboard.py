from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_extensions as de
import dash_daq as daq
import RPi.GPIO as GPIO
from PIL import Image
import time
from time import sleep
import Freenove_DHT as DHT
import smtplib, ssl
import random
from paho.mqtt import client as mqtt_client
from datetime import datetime

app = Dash(__name__)
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

#------------PHASE03 VARIABLE CODES--------------
broker = '192.168.1.110' #chilka home
port = 1883
topic1 = "esp/lightintensity"
topic2 = "esp/lightswitch"
client_id = f'python-mqtt-{random.randint(0, 100)}'
esp_message = 0
esp_lightswitch_message = "OFF"
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
LedPin = 35 # Led Pin/Enable Pin
GPIO.setup(LedPin,GPIO.OUT)
email_counter = 0
# -----------------------------------------------
# MQTT settings
broker = 'mqtt.eclipseprojects.io'
port = 1883
topic1 = "lightintensity"
topic2 = "lightswitch"
client_id = "python-mqtt-dashboard"

# Global variables
esp_message = 0
esp_lightswitch_message = ""
email_counter = 0
#------------PHASE02 VARIABLE CODES--------------
EMAIL = 'john190curry@gmail.com'
PASSWORD = 'CUURY23JOHN45'

SERVER= "smtp.gmail.com"

temperature = 0
DHTPin = 40 # equivalent to GPIO21
fan_status_checker=False

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
Motor1 = 35 # Enable Pin
Motor2 = 37 # Input Pin
Motor3 = 33 # Input Pin

GPIO.setup(Motor1,GPIO.IN)
GPIO.setup(Motor2,GPIO.IN)
GPIO.setup(Motor3,GPIO.IN)

bulb_off="photos/BulbOff.jpg"
bulb_on="photos/BulbOn.jpg"
url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json"
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))

# -----------------------------------------------
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
                                        value = 0, size=64)
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
        html.Img(src='photos/Ppic.jpg', style={'border-radius': '80px', 'width': '140px', 'height': '140px',
                                               'object-fit': 'cover', 'display': 'block', 'margin-left': 'auto',
                                               'margin-right': 'auto'}),
        html.H6("Username"),
        html.H4("Favorites: "),
        html.H6("Humidity"),
        html.H6("Temperature"),
        html.H6("Light Intensity")])
])

content = html.Div([
    dbc.Row([
        dbc.Col(dbc.Row([daq_Gauge, daq_Thermometer, html_Div_Fan_Gif, html_Fan_Status_Message]), width=5),
        dbc.Col(dbc.Row([daq_Led_Light_Intensity_LEDDisplay, html.Img(id="light-bulb", src=bulb_off,
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

app.layout = dbc.Container([
    dbc.Row(navbar),
    dbc.Row([
        dbc.Col(sidebar, width=2),
        dbc.Col(content, width=10, className="bg-secondary")
    ], style={"height": "100vh"}),
], fluid=True)

# Callbacks
@app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))
def update_output(value):
    run()
    return esp_message

@app.callback([Output('email_h1', 'children'), Output('light-bulb', 'src')],
              Input('led-email-status-update', 'n_intervals'))
def update_email_status(value):
    send_led_email_check(esp_lightswitch_message)
    if email_counter > 0:
        return "Email has been sent. Lightbulb is ON", bulb_on
    else:
        return "No email has been sent. Lightbulb is OFF", bulb_off

def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker!")
            time.sleep(5)
        else:
            print("Failed to connect, return code %d\n", rc)
    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def on_message(client, userdata, message):
    global esp_message, esp_lightswitch_message
    if message.topic == topic1:
        esp_message = int(float(message.payload.decode()))
    elif message.topic == topic2:
        esp_lightswitch_message = message.payload.decode()

def sendLedStatusEmail():
         print("PASSED BY SENDLEDSTATUSEMAIL method")
         port = 587  # For starttls
         smtp_server = "smtp-mail.outlook.com"
         sender_email = "iotdashboard2022@outlook.com"
         receiver_email = "iotdashboard2022@outlook.com"
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
    global email_counter
    if value == "ON" and email_counter == 0:
        sendLedStatusEmail()
        email_counter += 1

@app.callback([Output('email_h1', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))
def update_email_status(value):
    send_led_email_check(esp_lightswitch_message)
    if email_counter > 0:
        return "Email has been sent. Lightbulb is ON", bulb_on
    else:
        return "No email has been sent. Lightbulb is OFF", bulb_off

if __name__ == '__main__':
    app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)