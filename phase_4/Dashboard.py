from dash import Dash, html, dcc, Input, Output, State
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
import dash_bootstrap_components as dbc
import dash_extensions as de
import dash_daq as daq
import RPi.GPIO as GPIO
import base64
from PIL import Image       # use and download PILLOW for it to work  https://pillow.readthedocs.io/en/stable/installation.html
import time
from time import sleep
import Freenove_DHT as DHT
import smtplib, ssl, getpass, imaplib, email
import random
import dash_draggable
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
# broker = '192.168.0.158' #ip in Lab class
# broker = '192.168.76.10'
broker = '192.168.1.110' #chilka home
port = 1883
topic1 = "esp/lightintensity"
topic2 = "esp/lightswitch"
# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'
# username = 'emqx'
# password = 'public'
esp_message = 0
esp_lightswitch_message = "OFF"
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
LedPin = 35 # Led Pin/Enable Pin
GPIO.setup(LedPin,GPIO.OUT)
email_counter = 0    # just checks if email has been sent at some stage
# -----------------------------------------------

#------------PHASE02 VARIABLE CODES--------------
EMAIL = 'iotdashboard2022@outlook.com'
PASSWORD = 'iotpassword123'

SERVER = 'outlook.office365.com'
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

light_bulb_off="https://media.geeksforgeeks.org/wp-content/uploads/OFFbulb.jpg"
light_bulb_on="https://media.geeksforgeeks.org/wp-content/uploads/ONbulb.jpg"
url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json"
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))

# -----------------------------------------------
#Components

# related to gauge
daq_Gauge = daq.Gauge(
                id='my-gauge-1',
                label="Humidity",
                showCurrentValue=True,
                value = 62,
                size=200,
                max=100,
                min=0)

# related to temperature
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


sidebar = html.Div([
    html.H3('User Profile', style={'text-align': 'center'}),
    dbc.CardBody([
            html.Img(src='assets/Ppic.jpg', style={'border-radius': '80px', 'width':'140px', 'height':'140px', 'object-fit': 'cover', 'display': 'block','margin-left':'auto','margin-right': 'auto'}),
            html.H6("Username"),
            html.H4("Favorites: "),
            html.H6("Humidity"),
            html.H6("Temperature"),
            html.H6("Light Intensity")])
    ])

content = html.Div([
           dbc.Row([
#               dbc.Col(dbc.Row([daq_Gauge, daq_Thermometer, html_Button_Celcius_To_Fahrenheit,html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message]), width=7),
                dbc.Col(dbc.Row([daq_Gauge, daq_Thermometer,html_Div_Fan_Gif, html_Fan_Status_Message]), width=5),
        #                             dbc.Col(dbc.Row([html_Light_Intensity_Label, html_Led_Status_Message])),
                dbc.Col(dbc.Row([daq_Led_Light_Intensity_LEDDisplay, html.Img(id="light-bulb", src=light_bulb_off,
                    style={'width':'100px', 'height':'100px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}),
                    html.H1(id='email_h1',style ={"text-align":"center"})]), width=4, className="border border-secondary"),
                fan_Status_Message_Interval, humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval
             ]), #inner Row
        ])

app.layout = dbc.Container([
                dbc.Row(navbar),
                dbc.Row([
                    dbc.Col(sidebar, width=2), 
                    dbc.Col(content, width=10, className="bg-secondary") # content col
                ], style={"height": "100vh"}), # outer
            ], fluid=True) #container

# @app.callback(Output('my-gauge-1', 'value'), Input('humid-update', 'n_intervals'))
# def update_output(value):
#     dht = DHT.DHT(DHTPin)   #create a DHT class object
#     while(True):
#         for i in range(0,15):            
#             chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
#             if (chk is dht.DHTLIB_OK):      #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         print("Humidity : %.2f \t \n"%(dht.humidity))  # for testing on the terminal
#         return dht.humidity
#     
# @app.callback([Output('my-thermometer-1', 'value')], Input('temp-update', 'n_intervals'))
# def update_output(value):
#     dht = DHT.DHT(DHTPin)   #create a DHT class object
#     while(True):
#         for i in range(0,15):            
#             chk = dht.readDHT11()     #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
#             if (chk is dht.DHTLIB_OK):      #read DHT11 and get a return value. Then determine whether data read is normal according to the return value.
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         temperature = dht.temperature
#         print("Temperature : %.2f \n"%(dht.temperature))
#         if (dht.temperature >= 24):
#             sendEmail()
#           
#         return dht.temperature

def sendEmail():
        port = 587  # For starttls
        smtp_server = "smtp-mail.outlook.com"
        sender_email = "iotdashboard2022@outlook.com"
        receiver_email = "iotdashboard2022@outlook.com"
        password = 'iotpassword123'
        subject = "Subject: FAN CONTROL" 
        body = "Your home temperature is greater than 24. Do you wish to turn on the fan. Reply YES if so."
        message = subject + '\n\n' + body
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message) 
# 
# def is_fan_on():  
#     if GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3):
#         return True
#     else:
#         return False
# 
# @app.callback(Output('my-fan-1', 'value'), Input('fan-update', 'n_intervals'))
# def update_output(value):
#     fan_status_checker = is_fan_on()
# #     print(fan_status_checker)
#     return True if fan_status_checker else False
#         # return True if GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3) else False
# 

# @app.callback([Output('fan_status_message', 'children'), Output('my-gif', 'style')],Input('fan_status_message_update', 'n_intervals'))
# def update_h1(n):
#     fan_status_checker = is_fan_on()
#     
#     if fan_status_checker:
#         return "Status: On", {'display':'block'}
#     
#     else:
#         return "Status: Off",{'display':'none'}
#     
#CONVERSION NOT YET DONE
@app.callback([Output('my-thermometer-1', 'value')] ,
              [Input('temp-update', 'n_intervals'),
              Input('fahrenheit-button', 'n_clicks')])
def changeToFahrenheit(n_intervals, n_clicks): 
    return (temperature * 1.8) + 32

# PHASE 03 CODE FOR SUBSCRIBE 
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
        
            
@app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))  
def update_output(value):
    run()
    # print("Here: ", esp_message) UNCOMMENT TO SEE THE VALUE PASSED FROM THE PUBLISHER 
    value = esp_message
    return value

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

def on_message_from_lightintensity(client, userdata, message):
   global esp_message
   esp_message = int(float(message.payload.decode()))
   print("Message Received from LightSwtch: ")
   print(esp_message)

def on_message_from_lightswitch(client, userdata, message):
   global esp_lightswitch_message
   esp_lightswitch_message = message.payload.decode()
   print("Message Received from lightswitch: ")
   print(esp_lightswitch_message)

def on_message(client, userdata, message):
   print("Message Received from Others: "+message.payload.decode())

def run():
    client = connect_mqtt()
    client.subscribe(topic1, qos=1)
    client.subscribe(topic2, qos=1)
    client.message_callback_add(topic1, on_message_from_lightintensity)
    client.message_callback_add(topic2, on_message_from_lightswitch)
    client.loop_start()

def send_led_email_check(value):         # send email and increase the email counter to know there is an email sent
      global email_counter
      if value.__eq__("ON") and email_counter == 0:
         sendLedStatusEmail()
         email_counter += 1

#printing
@app.callback([Output('email_h1', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))       # update email sent message
def update_email_status(value):
    send_led_email_check(esp_lightswitch_message)
    print(email_counter + str(email_counter))
    if email_counter > 0:
        return "Email has been sent. Lightbulb is ON", light_bulb_on
    else:
        return "No email has been sent. Lightbulb is OFF", light_bulb_off

if __name__ == '__main__':
#     app.run_server(debug=True)
    app.run_server(debug=False,dev_tools_ui=False,dev_tools_props_check=False)


        


"""
from dash import Dash, html, dcc, Input, Output
from dash_bootstrap_templates import ThemeChangerAIO
import dash_bootstrap_components as dbc
import dash_extensions as de
import dash_daq as daq
import RPi.GPIO as GPIO
import time
from time import sleep
import Freenove_DHT as DHT
import random
from paho.mqtt import client as mqtt_client
import sqlite3
import ssl
import smtplib

# Images and GIFs
light_bulb_off = 'assets/lightbulbOFF.png'
light_bulb_on = 'assets/lightbulbON.png'
url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json" # fan lottie gif
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))
url2 = "https://assets8.lottiefiles.com/packages/lf20_ylvmhzmx.json" # bluetooth lottie gif

dbc_css = (
    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.1/dbc.min.css"
)
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])

theme_change = ThemeChangerAIO(aio_id="theme", radio_props={"persistence": True}, button_props={"color": "danger","children": "Change Theme"})

# User Information Variables
user_id = "Default"
temp_threshold = 25.0
light_threshold = 0
humidity = 40
path_to_picture = 'photos/Ppic.jpg'

# MQTT connection variables
broker = '192.168.0.158' #ip in Lab class
port = 1883
topic1 = "esp/lightintensity"
topic2 = "esp/rfid"
client_id = f'python-mqtt-{random.randint(0, 100)}'
esp_message = 0
esp_rfid_message = "000000"

# Counters and checkers
temp_email_sent = False
fan_status_checker = False
emails = 0    # just checks if email has been sent at some stage

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



#interval
fan_Status_Message_Interval = dcc.Interval(
    id='fan_status_message_update',
    disabled=False,
    interval=1 * 1000, # update every second for frequently changing data
    n_intervals=0
)

fan_Interval = dcc.Interval(
id = 'fan-update',
disabled=False,
interval = 1 * 5000, # update every 5 seconds for frequently changing data
n_intervals = 0)

humidity_Interval = dcc.Interval(
id = 'humid-update',
disabled=False,
interval = 1 * 2000, # update every 2 seconds for frequently changing data
n_intervals = 0)

temperature_Interval = dcc.Interval(
id = 'temp-update',
disabled=False,
interval = 1* 60000, # update every minute for less frequently changing data
n_intervals = 0)

light_Intensity_Interval = dcc.Interval(
id = 'light-intensity-update',
disabled=False,
interval = 1*3000, # update every 3 seconds for frequently changing data
n_intervals = 0)

led_On_Email_Interval = dcc.Interval(
id = 'led-email-status-update',
disabled=False,
interval = 1*5000,
n_intervals = 0)

userinfo_Interval = dcc.Interval(
id = 'userinfo-update',
disabled=False,
interval = 1*5000, # update every 5 seconds for less frequently changing data
n_intervals = 0)

bluetooth_Interval = dcc.Interval(
id = 'bluetooth-update',
disabled=False,
interval = 1*5000, # update every 5 seconds for less frequently changing data
n_intervals = 0)

fahrenheit_Interval = dcc.Interval(
id = 'fahrenheit-update',
disabled=False,
interval = 1*60000, # update every minute for less frequently changing data
n_intervals = 0)

#all fan related html
html_Div_Fan_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url, id='lottie-gif', isStopped=True, isClickToPauseDisabled=True)], id='fan_display')
html_Fan_Status_Message = html.H5(id='fan_status_message',style={'text-align':'center'})
html_Fan_Label = html.H6("Electric Fan", style={'text-align': 'center'});

#all related to light intensity and led html
html_Light_Intensity_Label = html.H6('Light Intensity',style={'text-align':'center'})
html_Led_Status_Message = html.H1(id='light_h1',style={'text-align':'center'})

#all temperature related html
html_Celcius_Label = html.H6('Celcius',style={'text-align':'center'})
html_Fahrenheit_Label = html.H6('Fahrenheit',style={'text-align':'center'})

#all bluetooth related html
html_Bluetooth_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url2, isClickToPauseDisabled=True)])
html_bluetooth_Label =  html.H6('Bluetooth Devices',style={'text-align':'center'})


sidebar  =html.Div({
    html.H3('User Profile', style={'text-align': 'center', 'margin-top': '20px'}),
    dbc.CardBody([
        html.Img(src=path_to_picture, id="picture_path", style={'border-radius': '80px', 'width':'140px', 'height':'140px', 'object-fit': 'cover', 'display': 'block','margin-left':'auto','margin-right': 'auto'}),
        html.H6("Username:" + str(user_id), style={'margin-top':'30px'}, id="username_user_data"),
        html.H4("Favorites ", style={'margin-top':'40px'}),
        html.H6("Humidity: " + str(humidity), style={'margin-left':'15px'}, id="humidity_user_data"),
        html.H6("Temperature: " + str(temp_threshold), style={'margin-left':'15px'}, id="temperature_user_data"),
        html.H6("Light Intensity: " + str(light_threshold), style={'margin-left':'15px'}, id="lightintensity_user_data")
    ])
}) 

daq_Fahrenheit_ToggleSwitch = daq.ToggleSwitch(
    id='fahrenheit-switch',
    value=False
)

daq_led = daq.LEDDisplay(
    id='light-intensity',

    labelPosition='bottom',
    value = 0,
    size = 50
)

# create fan gauge
fan_gauge = daq.Gauge(
    id='fan-gauge',
    label='Fan Speed',
    min=0,
    max=100,
    value=50,
    color={"gradient":True,"ranges":{"green":[0,50],"yellow":[50,75],"red":[75,100]}}
)
"""
app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(theme_change),
        ],
        brand="Fiacre Dashboard",
        color="Blue",
        dark=True,
        sticky="top"
    ),
    html.Div([
        sidebar,
        dbc.Container([
            dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.Col(daq.Gauge(
                    id='my-gauge-1',
                    label="Humidity",
                    showCurrentValue=True,
                    size=250,
                    max=100,
                    min=0
                )), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
                dbc.Col(dbc.Card(dbc.Col(html.Div([
                    daq.Thermometer(
                        id='my-thermometer-1',
                        min=-40,
                        max=60,
                        scale={'start': -40, 'interval': 10},
                        label="Temperature",
                        showCurrentValue=True,
                        height=150,
                        units="C",
                        color="red"
                    ),
                    dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch, id='fahrenheit-switch'), dbc.Col(html_Fahrenheit_Label)])
                ])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
                dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message, fan_gauge])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
            ], justify="center"),
            dbc.Row([
                dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
                dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
            ], justify="center", className="mt-5"),
        ], fluid=True),
        humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval
    ])
])
"""

app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavItem(theme_change),
        ],
        brand="Fiacre Dashboard",
        color="Blue",
        dark=True,
        sticky="top"
    ),
    html.Div([
        sidebar,
        dbc.Container([
            dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.Col(daq.Gauge(
                    id='my-gauge-1',
                    label="Humidity",
                    showCurrentValue=True,
                    size=250,
                    max=100,
                    min=0
                )), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
                dbc.Col(dbc.Card(dbc.Col(html.Div([
                    daq.Thermometer(
                        id='my-thermometer-1',
                        min=-40,
                        max=60,
                        scale={'start': -40, 'interval': 10},
                        label="Temperature",
                        showCurrentValue=True,
                        height=150,
                        units="C",
                        color="red"
                    ),
                    dbc.Row([dbc.Col(html.H6('Celcius',style={'text-align':'center'})), dbc.Col(daq.ToggleSwitch(id='fahrenheit-switch', value=False)), dbc.Col(html.H6('Fahrenheit',style={'text-align':'center'}))])
                ])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
                dbc.Col(dbc.Card(dbc.Col(html.Div([html.H6("Electric Fan", style={'text-align': 'center'}), html.Div([de.Lottie(options=options, width="40%", height="25%", url=url, id='lottie-gif', isStopped=True, isClickToPauseDisabled=True)], id='fan_display'), html.H5(id='fan_status_message',style={'text-align':'center'}), daq.Gauge(
                    id='fan-gauge',
                    label='Fan Speed',
                    min=0,
                    max=100,
                    value=50,
                    color={"gradient":True,"ranges":{"green":[0,50],"yellow":[50,75],"red":[75,100]}}
                )])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
            ], justify="center"),
            dbc.Row([
                dbc.Col(dbc.Card(html.Div([html.H6('Light Intensity',style={'text-align':'center'}), html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq.LEDDisplay(
                    id='light-intensity',
                    labelPosition='bottom',
                    value = 0,
                    size = 50
                ), html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
                dbc.Col(dbc.Card(html.Div([html.H6('Bluetooth Devices',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
            ], justify="center", className="mt-5"),
        ], fluid=True),
        humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval
    ])
])


card_content1 = dbc.Container([
    dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
    dbc.Row([
        dbc.Col(dbc.Card(dbc.Col(id='my-gauge-1'), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
        dbc.Col(dbc.Card(dbc.Col(html.Div([daq.Thermometer, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
        dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
    ], justify="center"),
    dbc.Row([
        dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
        dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
    ], justify="center", className="mt-5"),
], fluid=True)

content = html.Div([dbc.Row([card_content1, humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval, fan_Interval])])

app.layout = dbc.Col(dbc.Card(dbc.Col(html.Div([daq.Gauge, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),

@app.callback(Output('my-gauge-1', 'value'), Input('humid-update', 'n_intervals'))
def update_output(value):
    dht = DHT.DHT(DHTPin)
    while(True):
        for i in range(0,15):
            chk = dht.readDHT11()
            if (chk is dht.DHTLIB_OK):
                break
            time.sleep(0.1)
        time.sleep(2)
        print("Humidity : %.2f \t \n"%(dht.humidity))
        return dht.humidity

@app.callback(
    [Output('my-thermometer-1', 'value'), Output('my-thermometer-1', 'min'), Output('my-thermometer-1', 'max'), Output('my-thermometer-1', 'scale'), Output('my-thermometer-1', 'units')],
    [Input('fahrenheit-switch', 'value'), Input('temp-update', 'n_intervals')])

   
def update_output(switch_state, temp_value, interval_value):
    dht = DHT.DHT(DHTPin)   
    while(True):
        for i in range(0,15):            
            chk = dht.readDHT11()     
            if (chk is dht.DHTLIB_OK):      
                break
            time.sleep(0.1)
        time.sleep(2)
        temperature = dht.temperature
        print("Temperature : %.2f \n"%(dht.temperature))
        temp_email_sent
        if dht.temperature >= temp_threshold and temp_email_sent == False:
            sendEmail()
            temp_email_sent = True
             
        if switch_state:
           return (temperature * 1.8) + 32, 40, 120, {'start': 40, 'interval': 10}, 'F'
        else:
            return temperature, -40, 60, {'start': -40, 'interval': 10}, 'C'

# Checks if the Motor is active or not
def is_fan_on():  
    if GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3):
        return True
    else:
        return False
        
from dash import Output, Input

def is_fan_on():  
    return GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3)

# Callback for the Fan Lottie gif and status message
@app.callback([Output('fan_status_message', 'children'), Output('lottie-gif', 'isStopped')], Input('fan_status_message_update', 'n_intervals'))
def update_h1(n):
    return ("Status: On", False) if is_fan_on() else ("Status: Off", True)

@app.callback([Output('username_user_data', 'children'), Output('humidity_user_data', 'children'), Output('temperature_user_data', 'children'), Output('lightintensity_user_data', 'children'), Output('picture_path', 'src')], Input('userinfo-update', 'n_intervals'))
def update_user_information():
    #return "Username: " + str(user_id), "Humidity: 40", "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture
    return "Username: " + str(user_id), "Humidity: " + str(humidity), "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture

@app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))  
def update_output(value):
    print("Here is light intensity: ", esp_message) 
    return esp_message
def send_email(subject, body):
    smtp_server = 'smtp.gmail.com'
    port = 587
    sender_email = 'john190curry@gmail.com'
    receiver_email = 'john190curry@gmail.com'
    password = 'CUURY23JOHN45'
    message = f"{subject}\n\n{body}"
    context = ssl.create_default_context()

    with smtplib.SMTP(smtp_server, port) as server:
        server.starttls(context=context)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, message)
def sendEmail():
    send_email("Subject: Home Temperatue NOTIFICATION", "The temperature is at high")

def sendEmailLed():
    time = datetime.now().strftime("%H:%M")
    send_email("Subject: LIGHT NOTIFICATION", f"The Light is ON at {time}")

def send_Email_Led(lightValue):
    global emails
    if lightValue < light_threshold and emails == 0:
        sendEmailLed()
        emails += 1
@app.callback([Output('email_heading', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))      
def update_email_status(value):
    lightvalue = esp_message
    send_Email_Led(lightvalue)
    
    if emails > 0 and lightvalue < light_threshold:
        GPIO.output(LedPin, GPIO.HIGH)
        return "Email has been sent. Lightbulb is ON", light_bulb_on
    else:
        GPIO.output(LedPin, GPIO.LOW)
        return ("Email has been sent. Lightbulb is OFF", light_bulb_off) if emails > 0 else ("No email has been sent. Lightbulb is OFF", light_bulb_off)
if __name__ == '__main__':
    app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)

# def sendUserEnteredEmail(user_name): #for user(rfid)
"""

# from dash import Dash, html, dcc, Input, Output
# from dash_bootstrap_templates import ThemeChangerAIO
# import dash_bootstrap_components as dbc
# import dash_extensions as de
# import dash_daq as daq
# import RPi.GPIO as GPIO
# import time
# from time import sleep
# import Freenove_DHT as DHT
# import random
# from paho.mqtt import client as mqtt_client
# import sqlite3
# import ssl
# import smtplib

# # Images and GIFs
# light_bulb_off = 'assets/lightbulbOFF.png'
# light_bulb_on = 'assets/lightbulbON.png'
# url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json" # fan lottie gif
# options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))
# url2 = "https://assets8.lottiefiles.com/packages/lf20_ylvmhzmx.json" # bluetooth lottie gif

# dbc_css = (
#     "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.1/dbc.min.css"
# )
# app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])

# theme_change = ThemeChangerAIO(aio_id="theme", radio_props={"persistence": True}, button_props={"color": "danger","children": "Change Theme"})

# # User Information Variables
# user_id = "Default"
# temp_threshold = 25.0
# light_threshold = 0
# humidity = 40
# path_to_picture = 'photos/Ppic.jpg'

# # MQTT connection variables
# broker = '192.168.0.158' #ip in Lab class
# port = 1883
# topic1 = "esp/lightintensity"
# topic2 = "esp/rfid"
# client_id = f'python-mqtt-{random.randint(0, 100)}'
# esp_message = 0
# esp_rfid_message = "000000"

# # Counters and checkers
# temp_email_sent = False
# fan_status_checker = False
# emails = 0    # just checks if email has been sent at some stage

# # For Phase02 temperature (used in temperature callback)
# temperature = 0

# # RPI GPIO
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# DHTPin = 40 # equivalent to GPIO21
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# Motor1 = 35 # Enable Pin
# Motor2 = 37 # Input Pin
# Motor3 = 33 # Input Pin
# LedPin = 38
# GPIO.setup(Motor1, GPIO.IN)
# GPIO.setup(Motor2, GPIO.IN)
# GPIO.setup(Motor3, GPIO.IN)
# GPIO.setup(LedPin, GPIO.OUT)



# #interval
# fan_Status_Message_Interval = dcc.Interval(
#     id='fan_status_message_update',
#     disabled=False,
#     interval=1 * 1000, # update every second for frequently changing data
#     n_intervals=0
# )

# fan_Interval = dcc.Interval(
# id = 'fan-update',
# disabled=False,
# interval = 1 * 5000, # update every 5 seconds for frequently changing data
# n_intervals = 0)

# humidity_Interval = dcc.Interval(
# id = 'humid-update',
# disabled=False,
# interval = 1 * 2000, # update every 2 seconds for frequently changing data
# n_intervals = 0)

# temperature_Interval = dcc.Interval(
# id = 'temp-update',
# disabled=False,
# interval = 1* 60000, # update every minute for less frequently changing data
# n_intervals = 0)

# light_Intensity_Interval = dcc.Interval(
# id = 'light-intensity-update',
# disabled=False,
# interval = 1*3000, # update every 3 seconds for frequently changing data
# n_intervals = 0)

# led_On_Email_Interval = dcc.Interval(
# id = 'led-email-status-update',
# disabled=False,
# interval = 1*5000,
# n_intervals = 0)

# userinfo_Interval = dcc.Interval(
# id = 'userinfo-update',
# disabled=False,
# interval = 1*5000, # update every 5 seconds for less frequently changing data
# n_intervals = 0)

# bluetooth_Interval = dcc.Interval(
# id = 'bluetooth-update',
# disabled=False,
# interval = 1*5000, # update every 5 seconds for less frequently changing data
# n_intervals = 0)

# fahrenheit_Interval = dcc.Interval(
# id = 'fahrenheit-update',
# disabled=False,
# interval = 1*60000, # update every minute for less frequently changing data
# n_intervals = 0)

# #all fan related html
# html_Div_Fan_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url, id='lottie-gif', isStopped=True, isClickToPauseDisabled=True)], id='fan_display')
# html_Fan_Status_Message = html.H5(id='fan_status_message',style={'text-align':'center'})
# html_Fan_Label = html.H6("Electric Fan", style={'text-align': 'center'});

# #all related to light intensity and led html
# html_Light_Intensity_Label = html.H6('Light Intensity',style={'text-align':'center'})
# html_Led_Status_Message = html.H1(id='light_h1',style={'text-align':'center'})

# #all temperature related html
# html_Celcius_Label = html.H6('Celcius',style={'text-align':'center'})
# html_Fahrenheit_Label = html.H6('Fahrenheit',style={'text-align':'center'})

# #all bluetooth related html
# html_Bluetooth_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url2, isClickToPauseDisabled=True)])
# html_bluetooth_Label =  html.H6('Bluetooth Devices',style={'text-align':'center'})


# sidebar  =html.Div({
#     html.H3('User Profile', style={'text-align': 'center', 'margin-top': '20px'}),
#     dbc.CardBody([
#         html.Img(src=path_to_picture, id="picture_path", style={'border-radius': '80px', 'width':'140px', 'height':'140px', 'object-fit': 'cover', 'display': 'block','margin-left':'auto','margin-right': 'auto'}),
#         html.H6("Username:" + str(user_id), style={'margin-top':'30px'}, id="username_user_data"),
#         html.H4("Favorites ", style={'margin-top':'40px'}),
#         html.H6("Humidity: " + str(humidity), style={'margin-left':'15px'}, id="humidity_user_data"),
#         html.H6("Temperature: " + str(temp_threshold), style={'margin-left':'15px'}, id="temperature_user_data"),
#         html.H6("Light Intensity: " + str(light_threshold), style={'margin-left':'15px'}, id="lightintensity_user_data")
#     ])
# }) 

# daq_Fahrenheit_ToggleSwitch = daq.ToggleSwitch(
#     id='fahrenheit-switch',
#     value=False
# )

# daq_led = daq.LEDDisplay(
#     id='light-intensity',

#     labelPosition='bottom',
#     value = 0,
#     size = 50
# )

# # create fan gauge
# fan_gauge = daq.Gauge(
#     id='fan-gauge',
#     label='Fan Speed',
#     min=0,
#     max=100,
#     value=50,
#     color={"gradient":True,"ranges":{"green":[0,50],"yellow":[50,75],"red":[75,100]}}
# )

# app.layout = html.Div([
#     dbc.NavbarSimple(
#         children=[
#             dbc.NavItem(theme_change),
#         ],
#         brand="Fiacre Dashboard",
#         color="Blue",
#         dark=True,
#         sticky="top"
#     ),
#     html.Div([
#         sidebar,
#         dbc.Container([
#             dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
#             dbc.Row([
#                 dbc.Col(dbc.Card(dbc.Col(daq.Gauge(
#                     id='my-gauge-1',
#                     label="Humidity",
#                     showCurrentValue=True,
#                     size=250,
#                     max=100,
#                     min=0
#                 )), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(dbc.Col(html.Div([
#                     daq.Thermometer(
#                         id='my-thermometer-1',
#                         min=-40,
#                         max=60,
#                         scale={'start': -40, 'interval': 10},
#                         label="Temperature",
#                         showCurrentValue=True,
#                         height=150,
#                         units="C",
#                         color="red"
#                     ),
#                     dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch, id='fahrenheit-switch'), dbc.Col(html_Fahrenheit_Label)])
#                 ])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message, fan_gauge])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#             ], justify="center"),
#             dbc.Row([
#                 dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#             ], justify="center", className="mt-5"),
#         ], fluid=True),
#         humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval
#     ])
# ])

# card_content1 = dbc.Container([
#     dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
#     dbc.Row([
#         dbc.Col(dbc.Card(dbc.Col(id='my-gauge-1'), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(dbc.Col(html.Div([daq.Thermometer, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#     ], justify="center"),
#     dbc.Row([
#         dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#     ], justify="center", className="mt-5"),
# ], fluid=True)

# content = html.Div([dbc.Row([card_content1, humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval, fan_Interval])])


# #app.layout = dbc.Container([dbc.Row(navbar), dbc.Row([dbc.Col(sidebar, width=2), dbc.Col(content, width=10, className="bg-secondary")], style={"height": "100vh"})], fluid=True)
# #app.layout = dbc.Container([dbc.Row(navbar), dbc.Row([dbc.Col(sidebar, width=2), dbc.Col(content, width=10, className="bg-secondary")], style={"height": "100vh"})], fluid=True)
# app.layout = dbc.Col(dbc.Card(dbc.Col(html.Div([daq.Gauge, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),

# @app.callback(Output('my-gauge-1', 'value'), Input('humid-update', 'n_intervals'))
# def update_output(value):
#     dht = DHT.DHT(DHTPin)
#     while(True):
#         for i in range(0,15):
#             chk = dht.readDHT11()
#             if (chk is dht.DHTLIB_OK):
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         print("Humidity : %.2f \t \n"%(dht.humidity))
#         return dht.humidity

# """@app.callback(
#     [Output('my-thermometer-1', 'value'), Output('my-thermometer-1', 'min'), Output('my-thermometer-1', 'max'), Output('my-thermometer-1', 'scale'), Output('my-thermometer-1', 'units')],
#     [Input('fahrenheit-switch', 'value'), Input('temp-update', 'n_intervals')])
# """
# @app.callback(
#     [Output('my-thermometer-1', 'value'), Output('my-thermometer-1', 'min'), Output('my-thermometer-1', 'max'), Output('my-thermometer-1', 'scale'), Output('my-thermometer-1', 'units')],
#     [Input('fahrenheit-switch', 'value'), Input('temp-update', 'n_intervals')])

   
# def update_output(switch_state, temp_value, interval_value):
#     dht = DHT.DHT(DHTPin)   
#     while(True):
#         for i in range(0,15):            
#             chk = dht.readDHT11()     
#             if (chk is dht.DHTLIB_OK):      
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         temperature = dht.temperature
#         print("Temperature : %.2f \n"%(dht.temperature))
#         temp_email_sent
#         if dht.temperature >= temp_threshold and temp_email_sent == False:
#             sendEmail()
#             temp_email_sent = True
             
#         if switch_state:
#            return (temperature * 1.8) + 32, 40, 120, {'start': 40, 'interval': 10}, 'F'
#         else:
#             return temperature, -40, 60, {'start': -40, 'interval': 10}, 'C'

# # Checks if the Motor is active or not
# def is_fan_on():  
#     if GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3):
#         return True
#     else:
#         return False
        
# from dash import Output, Input

# def is_fan_on():  
#     return GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3)

# # Callback for the Fan Lottie gif and status message
# @app.callback([Output('fan_status_message', 'children'), Output('lottie-gif', 'isStopped')], Input('fan_status_message_update', 'n_intervals'))
# def update_h1(n):
#     return ("Status: On", False) if is_fan_on() else ("Status: Off", True)

# @app.callback([Output('username_user_data', 'children'), Output('humidity_user_data', 'children'), Output('temperature_user_data', 'children'), Output('lightintensity_user_data', 'children'), Output('picture_path', 'src')], Input('userinfo-update', 'n_intervals'))
# def update_user_information():
#     #return "Username: " + str(user_id), "Humidity: 40", "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture
#     return "Username: " + str(user_id), "Humidity: " + str(humidity), "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture

# @app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))  
# def update_output(value):
#     print("Here is light intensity: ", esp_message) 
#     return esp_message

# def send_email(subject, body):
#     smtp_server = 'smtp.gmail.com'
#     port = 587
#     sender_email = 'john190curry@gmail.com'
#     receiver_email = 'john190curry@gmail.com'
#     password = 'CUURY23JOHN45'
#     message = f"{subject}\n\n{body}"
#     context = ssl.create_default_context()

#     with smtplib.SMTP(smtp_server, port) as server:
#         server.starttls(context=context)
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, message)

# def sendEmail():
#     send_email("Subject: Home Temperatue NOTIFICATION", "The temperature is at high")

# def sendEmailLed():
#     time = datetime.now().strftime("%H:%M")
#     send_email("Subject: LIGHT NOTIFICATION", f"The Light is ON at {time}")

# def send_Email_Led(lightValue):
#     global emails
#     if lightValue < light_threshold and emails == 0:
#         sendEmailLed()
#         emails += 1

# @app.callback([Output('email_heading', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))      
# def update_email_status(value):
#     lightvalue = esp_message
#     send_Email_Led(lightvalue)
    
#     if emails > 0 and lightvalue < light_threshold:
#         GPIO.output(LedPin, GPIO.HIGH)
#         return "Email has been sent. Lightbulb is ON", light_bulb_on
#     else:
#         GPIO.output(LedPin, GPIO.LOW)
#         return ("Email has been sent. Lightbulb is OFF", light_bulb_off) if emails > 0 else ("No email has been sent. Lightbulb is OFF", light_bulb_off)

# if __name__ == '__main__':
#     app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)

# # def sendUserEnteredEmail(user_name): #for user(rfid)












# from dash import Dash, html, dcc, Input, Output
# from dash_bootstrap_templates import ThemeChangerAIO
# import dash_bootstrap_components as dbc
# import dash_extensions as de
# import dash_daq as daq
# import RPi.GPIO as GPIO
# import time
# from time import sleep
# import Freenove_DHT as DHT
# import random
# from paho.mqtt import client as mqtt_client
# import sqlite3
# import ssl

# # Images and GIFs
# light_bulb_off = 'assets/lightbulbOFF.png'
# light_bulb_on = 'assets/lightbulbON.png'
# url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json" # fan lottie gif
# options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))
# url2 = "https://assets8.lottiefiles.com/packages/lf20_ylvmhzmx.json" # bluetooth lottie gif

# dbc_css = (
#     "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.1/dbc.min.css"
# )
# app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])

# theme_change = ThemeChangerAIO(aio_id="theme", radio_props={"persistence": True}, button_props={"color": "danger","children": "Change Theme"})

# # User Information Variables
# user_id = "Default"
# temp_threshold = 25.0
# light_threshold = 0
# humidity = 40
# path_to_picture = 'photos/Ppic.jpg'

# # MQTT connection variables
# broker = '192.168.0.158' #ip in Lab class
# port = 1883
# topic1 = "esp/lightintensity"
# topic2 = "esp/rfid"
# client_id = f'python-mqtt-{random.randint(0, 100)}'
# esp_message = 0
# esp_rfid_message = "000000"

# # Counters and checkers
# temp_email_sent = False
# fan_status_checker = False
# emails = 0    # just checks if email has been sent at some stage

# # For Phase02 temperature (used in temperature callback)
# temperature = 0

# # RPI GPIO
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# DHTPin = 40 # equivalent to GPIO21
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# Motor1 = 35 # Enable Pin
# Motor2 = 37 # Input Pin
# Motor3 = 33 # Input Pin
# LedPin = 38
# GPIO.setup(Motor1, GPIO.IN)
# GPIO.setup(Motor2, GPIO.IN)
# GPIO.setup(Motor3, GPIO.IN)
# GPIO.setup(LedPin, GPIO.OUT)



# #interval
# fan_Status_Message_Interval = dcc.Interval(
#     id='fan_status_message_update',
#     disabled=False,
#     interval=1 * 1000, # update every second for frequently changing data
#     n_intervals=0
# )

# fan_Interval = dcc.Interval(
# id = 'fan-update',
# disabled=False,
# interval = 1 * 5000, # update every 5 seconds for frequently changing data
# n_intervals = 0)

# humidity_Interval = dcc.Interval(
# id = 'humid-update',
# disabled=False,
# interval = 1 * 2000, # update every 2 seconds for frequently changing data
# n_intervals = 0)

# temperature_Interval = dcc.Interval(
# id = 'temp-update',
# disabled=False,
# interval = 1* 60000, # update every minute for less frequently changing data
# n_intervals = 0)

# light_Intensity_Interval = dcc.Interval(
# id = 'light-intensity-update',
# disabled=False,
# interval = 1*3000, # update every 3 seconds for frequently changing data
# n_intervals = 0)

# led_On_Email_Interval = dcc.Interval(
# id = 'led-email-status-update',
# disabled=False,
# interval = 1*5000,
# n_intervals = 0)

# userinfo_Interval = dcc.Interval(
# id = 'userinfo-update',
# disabled=False,
# interval = 1*5000, # update every 5 seconds for less frequently changing data
# n_intervals = 0)

# bluetooth_Interval = dcc.Interval(
# id = 'bluetooth-update',
# disabled=False,
# interval = 1*5000, # update every 5 seconds for less frequently changing data
# n_intervals = 0)

# fahrenheit_Interval = dcc.Interval(
# id = 'fahrenheit-update',
# disabled=False,
# interval = 1*60000, # update every minute for less frequently changing data
# n_intervals = 0)

# #all fan related html
# html_Div_Fan_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url, id='lottie-gif', isStopped=True, isClickToPauseDisabled=True)], id='fan_display')
# html_Fan_Status_Message = html.H5(id='fan_status_message',style={'text-align':'center'})
# html_Fan_Label = html.H6("Electric Fan", style={'text-align': 'center'});

# #all related to light intensity and led html
# html_Light_Intensity_Label = html.H6('Light Intensity',style={'text-align':'center'})
# html_Led_Status_Message = html.H1(id='light_h1',style={'text-align':'center'})

# #all temperature related html
# html_Celcius_Label = html.H6('Celcius',style={'text-align':'center'})
# html_Fahrenheit_Label = html.H6('Fahrenheit',style={'text-align':'center'})

# #all bluetooth related html
# html_Bluetooth_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url2, isClickToPauseDisabled=True)])
# html_bluetooth_Label =  html.H6('Bluetooth Devices',style={'text-align':'center'})


# sidebar  =html.Div({
#     html.H3('User Profile', style={'text-align': 'center', 'margin-top': '20px'}),
#     dbc.CardBody([
#         html.Img(src=path_to_picture, id="picture_path", style={'border-radius': '80px', 'width':'140px', 'height':'140px', 'object-fit': 'cover', 'display': 'block','margin-left':'auto','margin-right': 'auto'}),
#         html.H6("Username:" + str(user_id), style={'margin-top':'30px'}, id="username_user_data"),
#         html.H4("Favorites ", style={'margin-top':'40px'}),
#         html.H6("Humidity: " + str(humidity), style={'margin-left':'15px'}, id="humidity_user_data"),
#         html.H6("Temperature: " + str(temp_threshold), style={'margin-left':'15px'}, id="temperature_user_data"),
#         html.H6("Light Intensity: " + str(light_threshold), style={'margin-left':'15px'}, id="lightintensity_user_data")
#     ])
# }) 



# """
# app.layout = html.Div([
#     dbc.NavbarSimple(
#         children=[
#             dbc.NavItem(theme_change),
#         ],
#         brand="Fiacre Dashboard",
#         color="Blue",
#         dark=True,
#         sticky="top"
#     ),
#     html.Div([
#         sidebar,
#         dbc.Container([
#             dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
#             dbc.Row([
#                 dbc.Col(dbc.Card(dbc.Col(daq.Gauge(
#                     id='my-gauge-1',
#                     label="Humidity",
#                     showCurrentValue=True,
#                     size=250,
#                     max=100,
#                     min=0
#                 )), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(dbc.Col(html.Div([
#                     daq.Thermometer(
#                         id='my-thermometer-1',
#                         min=-40,
#                         max=60,
#                         scale={'start': -40, 'interval': 10},
#                         label="Temperature",
#                         showCurrentValue=True,
#                         height=150,
#                         units="C",
#                         color="red"
#                     ),
#                     dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])
#                 ])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#             ], justify="center"),
#             dbc.Row([
#                 dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#             ], justify="center", className="mt-5"),
#         ], fluid=True),
#         humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval
#     ])
# ])    
# """
# daq_Fahrenheit_ToggleSwitch = daq.ToggleSwitch(
#     id='fahrenheit-switch',
#     value=False
# )

# daq_led = daq.LEDDisplay(
#     id='light-intensity',

#     labelPosition='bottom',
#     value = 0,
#     size = 50
# )

# # create fan gauge
# fan_gauge = daq.Gauge(
#     id='fan-gauge',
#     label='Fan Speed',
#     min=0,
#     max=100,
#     value=50,
#     color={"gradient":True,"ranges":{"green":[0,50],"yellow":[50,75],"red":[75,100]}}
# )
# app.layout = html.Div([
#     dbc.NavbarSimple(
#         children=[
#             dbc.NavItem(theme_change),
#         ],
#         brand="Fiacre Dashboard",
#         color="Blue",
#         dark=True,
#         sticky="top"
#     ),
#     html.Div([
#         sidebar,
#         dbc.Container([
#             dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
#             dbc.Row([
#                 dbc.Col(dbc.Card(dbc.Col(daq.Gauge(
#                     id='my-gauge-1',
#                     label="Humidity",
#                     showCurrentValue=True,
#                     size=250,
#                     max=100,
#                     min=0
#                 )), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(dbc.Col(html.Div([
#                     daq.Thermometer(
#                         id='my-thermometer-1',
#                         min=-40,
#                         max=60,
#                         scale={'start': -40, 'interval': 10},
#                         label="Temperature",
#                         showCurrentValue=True,
#                         height=150,
#                         units="C",
#                         color="red"
#                     ),
#                     dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])
#                 ])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#             ], justify="center"),
#             dbc.Row([
#                 dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#             ], justify="center", className="mt-5"),
#         ], fluid=True),
#         humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval
#     ])
# ])

# card_content1 = dbc.Container([
#     dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
#     dbc.Row([
#         dbc.Col(dbc.Card(dbc.Col(id='my-gauge-1'), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(dbc.Col(html.Div([Thermometer, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#     ], justify="center"),
#     dbc.Row([
#         dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#     ], justify="center", className="mt-5"),
# ], fluid=True)

# content = html.Div([dbc.Row([card_content1, humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval, fan_Interval])])


# #app.layout = dbc.Container([dbc.Row(navbar), dbc.Row([dbc.Col(sidebar, width=2), dbc.Col(content, width=10, className="bg-secondary")], style={"height": "100vh"})], fluid=True)
# #app.layout = dbc.Container([dbc.Row(navbar), dbc.Row([dbc.Col(sidebar, width=2), dbc.Col(content, width=10, className="bg-secondary")], style={"height": "100vh"})], fluid=True)
# app.layout = dbc.Col(dbc.Card(dbc.Col(html.Div([daq_Humidity, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),

# @app.callback(Output('my-gauge-1', 'value'), Input('humid-update', 'n_intervals'))
# def update_output(value):
#     dht = DHT.DHT(DHTPin)
#     while(True):
#         for i in range(0,15):
#             chk = dht.readDHT11()
#             if (chk is dht.DHTLIB_OK):
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         print("Humidity : %.2f \t \n"%(dht.humidity))
#         return dht.humidity

# """@app.callback(
#     [Output('my-thermometer-1', 'value'), Output('my-thermometer-1', 'min'), Output('my-thermometer-1', 'max'), Output('my-thermometer-1', 'scale'), Output('my-thermometer-1', 'units')],
#     [Input('fahrenheit-switch', 'value'), Input('temp-update', 'n_intervals')])
# """
# @app.callback(
#     [Output('my-thermometer-1', 'value'), Output('my-thermometer-1', 'min'), Output('my-thermometer-1', 'max'), Output('my-thermometer-1', 'scale'), Output('my-thermometer-1', 'units')],
#     [Input('fahrenheit-switch', 'value'), Input('temp-update', 'n_intervals')])

   
# def update_output(switch_state, temp_value, interval_value):
#     dht = DHT.DHT(DHTPin)   
#     while(True):
#         for i in range(0,15):            
#             chk = dht.readDHT11()     
#             if (chk is dht.DHTLIB_OK):      
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         temperature = dht.temperature
#         print("Temperature : %.2f \n"%(dht.temperature))
#         temp_email_sent
#         if dht.temperature >= temp_threshold and temp_email_sent == False:
#             sendEmail()
#             temp_email_sent = True
             
#         if switch_state:
#            return (temperature * 1.8) + 32, 40, 120, {'start': 40, 'interval': 10}, 'F'
#         else:
#             return temperature, -40, 60, {'start': -40, 'interval': 10}, 'C'

# # Checks if the Motor is active or not
# def is_fan_on():  
#     if GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3):
#         return True
#     else:
#         return False
        
# from dash import Output, Input

# def is_fan_on():  
#     return GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3)

# # Callback for the Fan Lottie gif and status message
# @app.callback([Output('fan_status_message', 'children'), Output('lottie-gif', 'isStopped')], Input('fan_status_message_update', 'n_intervals'))
# def update_h1(n):
#     return ("Status: On", False) if is_fan_on() else ("Status: Off", True)

# @app.callback([Output('username_user_data', 'children'), Output('humidity_user_data', 'children'), Output('temperature_user_data', 'children'), Output('lightintensity_user_data', 'children'), Output('picture_path', 'src')], Input('userinfo-update', 'n_intervals'))
# def update_user_information():
#     #return "Username: " + str(user_id), "Humidity: 40", "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture
#     return "Username: " + str(user_id), "Humidity: " + str(humidity), "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture

# @app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))  
# def update_output(value):
#     print("Here is light intensity: ", esp_message) 
#     return esp_message

# def send_email(subject, body):
#     smtp_server = 'smtp.gmail.com'
#     port = 587
#     sender_email = 'john190curry@gmail.com'
#     receiver_email = 'john190curry@gmail.com'
#     password = 'CUURY23JOHN45'
#     message = f"{subject}\n\n{body}"
#     context = ssl.create_default_context()

#     with smtplib.SMTP(smtp_server, port) as server:
#         server.starttls(context=context)
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, message)

# def sendEmail():
#     send_email("Subject: Home Temperatue NOTIFICATION", "The temperature is at high")

# def sendEmailLed():
#     time = datetime.now().strftime("%H:%M")
#     send_email("Subject: LIGHT NOTIFICATION", f"The Light is ON at {time}")

# def send_Email_Led(lightValue):
#     global emails
#     if lightValue < light_threshold and emails == 0:
#         sendEmailLed()
#         emails += 1

# @app.callback([Output('email_heading', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))      
# def update_email_status(value):
#     lightvalue = esp_message
#     send_Email_Led(lightvalue)
    
#     if emails > 0 and lightvalue < light_threshold:
#         GPIO.output(LedPin, GPIO.HIGH)
#         return "Email has been sent. Lightbulb is ON", light_bulb_on
#     else:
#         GPIO.output(LedPin, GPIO.LOW)
#         return ("Email has been sent. Lightbulb is OFF", light_bulb_off) if emails > 0 else ("No email has been sent. Lightbulb is OFF", light_bulb_off)

# if __name__ == '__main__':
#     app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)

# # def sendUserEnteredEmail(user_name): #for user(rfid)





# from dash import Dash, html, dcc, Input, Output
# from dash_bootstrap_templates import ThemeChangerAIO
# import dash_bootstrap_components as dbc
# import dash_extensions as de
# import dash_daq as daq
# import RPi.GPIO as GPIO
# import time
# from time import sleep
# import Freenove_DHT as DHT
# import random
# from paho.mqtt import client as mqtt_client
# import sqlite3
# import ssl

# # Images and GIFs
# light_bulb_off = 'assets/lightbulbOFF.png'
# light_bulb_on = 'assets/lightbulbON.png'
# url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json" # fan lottie gif
# options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))
# url2 = "https://assets8.lottiefiles.com/packages/lf20_ylvmhzmx.json" # bluetooth lottie gif

# dbc_css = (
#     "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.1/dbc.min.css"
# )
# app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])

# theme_change = ThemeChangerAIO(aio_id="theme", radio_props={"persistence": True}, button_props={"color": "danger","children": "Change Theme"})

# # User Information Variables
# user_id = "Default"
# temp_threshold = 25.0
# light_threshold = 0
# humidity = 40
# path_to_picture = 'photos/Ppic.jpg'

# # MQTT connection variables
# broker = '192.168.0.158' #ip in Lab class
# port = 1883
# topic1 = "esp/lightintensity"
# topic2 = "esp/rfid"
# client_id = f'python-mqtt-{random.randint(0, 100)}'
# esp_message = 0
# esp_rfid_message = "000000"

# # Counters and checkers
# temp_email_sent = False
# fan_status_checker = False
# emails = 0    # just checks if email has been sent at some stage

# # For Phase02 temperature (used in temperature callback)
# temperature = 0

# # RPI GPIO
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# DHTPin = 40 # equivalent to GPIO21
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# Motor1 = 35 # Enable Pin
# Motor2 = 37 # Input Pin
# Motor3 = 33 # Input Pin
# LedPin = 38
# GPIO.setup(Motor1, GPIO.IN)
# GPIO.setup(Motor2, GPIO.IN)
# GPIO.setup(Motor3, GPIO.IN)
# GPIO.setup(LedPin, GPIO.OUT)



# #interval
# fan_Status_Message_Interval = dcc.Interval(
#     id='fan_status_message_update',
#     disabled=False,
#     interval=1 * 1000, # update every second for frequently changing data
#     n_intervals=0
# )

# fan_Interval = dcc.Interval(
# id = 'fan-update',
# disabled=False,
# interval = 1 * 5000, # update every 5 seconds for frequently changing data
# n_intervals = 0)

# humidity_Interval = dcc.Interval(
# id = 'humid-update',
# disabled=False,
# interval = 1 * 2000, # update every 2 seconds for frequently changing data
# n_intervals = 0)

# temperature_Interval = dcc.Interval(
# id = 'temp-update',
# disabled=False,
# interval = 1* 60000, # update every minute for less frequently changing data
# n_intervals = 0)

# light_Intensity_Interval = dcc.Interval(
# id = 'light-intensity-update',
# disabled=False,
# interval = 1*3000, # update every 3 seconds for frequently changing data
# n_intervals = 0)

# led_On_Email_Interval = dcc.Interval(
# id = 'led-email-status-update',
# disabled=False,
# interval = 1*5000,
# n_intervals = 0)

# userinfo_Interval = dcc.Interval(
# id = 'userinfo-update',
# disabled=False,
# interval = 1*5000, # update every 5 seconds for less frequently changing data
# n_intervals = 0)

# bluetooth_Interval = dcc.Interval(
# id = 'bluetooth-update',
# disabled=False,
# interval = 1*5000, # update every 5 seconds for less frequently changing data
# n_intervals = 0)

# fahrenheit_Interval = dcc.Interval(
# id = 'fahrenheit-update',
# disabled=False,
# interval = 1*60000, # update every minute for less frequently changing data
# n_intervals = 0)

# #all fan related html
# html_Div_Fan_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url, id='lottie-gif', isStopped=True, isClickToPauseDisabled=True)], id='fan_display')
# html_Fan_Status_Message = html.H5(id='fan_status_message',style={'text-align':'center'})
# html_Fan_Label = html.H6("Electric Fan", style={'text-align': 'center'});

# #all related to light intensity and led html
# html_Light_Intensity_Label = html.H6('Light Intensity',style={'text-align':'center'})
# html_Led_Status_Message = html.H1(id='light_h1',style={'text-align':'center'})

# #all temperature related html
# html_Celcius_Label = html.H6('Celcius',style={'text-align':'center'})
# html_Fahrenheit_Label = html.H6('Fahrenheit',style={'text-align':'center'})

# #all bluetooth related html
# html_Bluetooth_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url2, isClickToPauseDisabled=True)])
# html_bluetooth_Label =  html.H6('Bluetooth Devices',style={'text-align':'center'})


# sidebar  =html.Div({
#     html.H3('User Profile', style={'text-align': 'center', 'margin-top': '20px'}),
#     dbc.CardBody([
#         html.Img(src=path_to_picture, id="picture_path", style={'border-radius': '80px', 'width':'140px', 'height':'140px', 'object-fit': 'cover', 'display': 'block','margin-left':'auto','margin-right': 'auto'}),
#         html.H6("Username:" + str(user_id), style={'margin-top':'30px'}, id="username_user_data"),
#         html.H4("Favorites ", style={'margin-top':'40px'}),
#         html.H6("Humidity: " + str(humidity), style={'margin-left':'15px'}, id="humidity_user_data"),
#         html.H6("Temperature: " + str(temp_threshold), style={'margin-left':'15px'}, id="temperature_user_data"),
#         html.H6("Light Intensity: " + str(light_threshold), style={'margin-left':'15px'}, id="lightintensity_user_data")
#     ])
# }) 

# card_content1 = dbc.Container([
#     dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
#     dbc.Row([
#         dbc.Col(dbc.Card(dbc.Col(daq_Humudity), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(dbc.Col(html.Div([daq_Thermometer, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#     ], justify="center"),
#     dbc.Row([
#         dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#     ], justify="center", className="mt-5"),
# ], fluid=True)

# app.layout = html.Div([
#     dbc.NavbarSimple(
#         children=[
#             dbc.NavItem(theme_change),
#         ],
#         brand="Fiacre Dashboard",
#         color="Blue",
#         dark=True,
#         sticky="top"
#     ),
#     html.Div([
#         sidebar,
#         dbc.Container([
#             dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
#             dbc.Row([
#                 dbc.Col(dbc.Card(dbc.Col(daq.Gauge(
#                     id='my-gauge-1',
#                     label="Humidity",
#                     showCurrentValue=True,
#                     size=250,
#                     max=100,
#                     min=0
#                 )), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(dbc.Col(html.Div([
#                     daq.Thermometer(
#                         id='my-thermometer-1',
#                         min=-40,
#                         max=60,
#                         scale={'start': -40, 'interval': 10},
#                         label="Temperature",
#                         showCurrentValue=True,
#                         height=150,
#                         units="C",
#                         color="red"
#                     ),
#                     dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])
#                 ])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#             ], justify="center"),
#             dbc.Row([
#                 dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#                 dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#             ], justify="center", className="mt-5"),
#         ], fluid=True),
#         humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval
#     ])
# ])    


# content = html.Div([dbc.Row([card_content1, humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval, fan_Interval])])


# #app.layout = dbc.Container([dbc.Row(navbar), dbc.Row([dbc.Col(sidebar, width=2), dbc.Col(content, width=10, className="bg-secondary")], style={"height": "100vh"})], fluid=True)
# #app.layout = dbc.Container([dbc.Row(navbar), dbc.Row([dbc.Col(sidebar, width=2), dbc.Col(content, width=10, className="bg-secondary")], style={"height": "100vh"})], fluid=True)
# app.layout = dbc.Col(dbc.Card(dbc.Col(html.Div([daq_Humidity, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),

# @app.callback(Output('my-gauge-1', 'value'), Input('humid-update', 'n_intervals'))
# def update_output(value):
#     dht = DHT.DHT(DHTPin)
#     while(True):
#         for i in range(0,15):
#             chk = dht.readDHT11()
#             if (chk is dht.DHTLIB_OK):
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         print("Humidity : %.2f \t \n"%(dht.humidity))
#         return dht.humidity

# """@app.callback(
#     [Output('my-thermometer-1', 'value'), Output('my-thermometer-1', 'min'), Output('my-thermometer-1', 'max'), Output('my-thermometer-1', 'scale'), Output('my-thermometer-1', 'units')],
#     [Input('fahrenheit-switch', 'value'), Input('temp-update', 'n_intervals')])
# """
# @app.callback(
#     [Output('my-thermometer-1', 'value'), Output('my-thermometer-1', 'min'), Output('my-thermometer-1', 'max'), Output('my-thermometer-1', 'scale'), Output('my-thermometer-1', 'units')],
#     [Input('fahrenheit-switch', 'value'), Input('temp-update', 'n_intervals')])

   
# def update_output(switch_state, temp_value, interval_value):
#     dht = DHT.DHT(DHTPin)   
#     while(True):
#         for i in range(0,15):            
#             chk = dht.readDHT11()     
#             if (chk is dht.DHTLIB_OK):      
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         temperature = dht.temperature
#         print("Temperature : %.2f \n"%(dht.temperature))
#         temp_email_sent
#         if dht.temperature >= temp_threshold and temp_email_sent == False:
#             sendEmail()
#             temp_email_sent = True
             
#         if switch_state:
#            return (temperature * 1.8) + 32, 40, 120, {'start': 40, 'interval': 10}, 'F'
#         else:
#             return temperature, -40, 60, {'start': -40, 'interval': 10}, 'C'

# # Checks if the Motor is active or not
# def is_fan_on():  
#     if GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3):
#         return True
#     else:
#         return False
        
# from dash import Output, Input

# def is_fan_on():  
#     return GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3)

# # Callback for the Fan Lottie gif and status message
# @app.callback([Output('fan_status_message', 'children'), Output('lottie-gif', 'isStopped')], Input('fan_status_message_update', 'n_intervals'))
# def update_h1(n):
#     return ("Status: On", False) if is_fan_on() else ("Status: Off", True)

# @app.callback([Output('username_user_data', 'children'), Output('humidity_user_data', 'children'), Output('temperature_user_data', 'children'), Output('lightintensity_user_data', 'children'), Output('picture_path', 'src')], Input('userinfo-update', 'n_intervals'))
# def update_user_information():
#     #return "Username: " + str(user_id), "Humidity: 40", "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture
#     return "Username: " + str(user_id), "Humidity: " + str(humidity), "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture

# @app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))  
# def update_output(value):
#     print("Here is light intensity: ", esp_message) 
#     return esp_message

# def send_email(subject, body):
#     smtp_server = 'smtp.gmail.com'
#     port = 587
#     sender_email = 'john190curry@gmail.com'
#     receiver_email = 'john190curry@gmail.com'
#     password = 'CUURY23JOHN45'
#     message = f"{subject}\n\n{body}"
#     context = ssl.create_default_context()

#     with smtplib.SMTP(smtp_server, port) as server:
#         server.starttls(context=context)
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, message)

# def sendEmail():
#     send_email("Subject: Home Temperatue NOTIFICATION", "The temperature is at high")

# def sendEmailLed():
#     time = datetime.now().strftime("%H:%M")
#     send_email("Subject: LIGHT NOTIFICATION", f"The Light is ON at {time}")

# def send_Email_Led(lightValue):
#     global emails
#     if lightValue < light_threshold and emails == 0:
#         sendEmailLed()
#         emails += 1

# @app.callback([Output('email_heading', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))      
# def update_email_status(value):
#     lightvalue = esp_message
#     send_Email_Led(lightvalue)
    
#     if emails > 0 and lightvalue < light_threshold:
#         GPIO.output(LedPin, GPIO.HIGH)
#         return "Email has been sent. Lightbulb is ON", light_bulb_on
#     else:
#         GPIO.output(LedPin, GPIO.LOW)
#         return ("Email has been sent. Lightbulb is OFF", light_bulb_off) if emails > 0 else ("No email has been sent. Lightbulb is OFF", light_bulb_off)

# if __name__ == '__main__':
#     app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)

# # def sendUserEnteredEmail(user_name): #for user(rfid)








# from dash import Dash, html, dcc, Input, Output
# from dash_bootstrap_templates import ThemeChangerAIO
# import dash_bootstrap_components as dbc
# import dash_extensions as de
# import dash_daq as daq
# import RPi.GPIO as GPIO
# import time
# from time import sleep
# import Freenove_DHT as DHT
# import random
# from paho.mqtt import client as mqtt_client
# import sqlite3
# import ssl


# # Images and GIFs
# light_bulb_off = 'assets/lightbulbOFF.png'
# light_bulb_on = 'assets/lightbulbON.png'
# url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json" # fan lottie gif
# options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))
# url2 = "https://assets8.lottiefiles.com/packages/lf20_ylvmhzmx.json" # bluetooth lottie gif

# dbc_css = (
#     "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.1/dbc.min.css"
# )
# app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])

# theme_change = ThemeChangerAIO(aio_id="theme", radio_props={"persistence": True}, button_props={"color": "danger","children": "Change Theme"})

# # Side bar functions
# navbar = dbc.NavbarSimple(
#     children=[
#         dbc.NavItem(theme_change),
#     ],
#     brand="Fiacre Dashboard",
#     color="Blue",
#     dark=True,
#     sticky="top"
# )

# # User Information Variables
# user_id = "Default"
# temp_threshold = 25.0
# light_threshold = 0
# humidity = 40
# path_to_picture = 'photos/Ppic.jpg'

# # MQTT connection variables
# broker = '192.168.0.158' #ip in Lab class
# port = 1883
# topic1 = "esp/lightintensity"
# topic2 = "esp/rfid"
# client_id = f'python-mqtt-{random.randint(0, 100)}'
# esp_message = 0
# esp_rfid_message = "000000"

# # Counters and checkers
# temp_email_sent = False
# fan_status_checker = False
# emails = 0    # just checks if email has been sent at some stage

# # For Phase02 temperature (used in temperature callback)
# temperature = 0

# # RPI GPIO
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# DHTPin = 40 # equivalent to GPIO21
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# Motor1 = 35 # Enable Pin
# Motor2 = 37 # Input Pin
# Motor3 = 33 # Input Pin
# LedPin = 38
# GPIO.setup(Motor1, GPIO.IN)
# GPIO.setup(Motor2, GPIO.IN)
# GPIO.setup(Motor3, GPIO.IN)
# GPIO.setup(LedPin, GPIO.OUT)

# # create thermometer
# daq_Thermometer = daq.Thermometer(
#     id='my-thermometer-1',
#     min=-40,
#     max=60,
#     scale={'start': -40, 'interval': 10},
#     label="Temperature",
#     showCurrentValue=True,
#     height=150,
#     units="C",
#     color="red"
# )

# # create humudity
# daq_Humudity = daq.Gauge(
#     id='my-gauge-1',
#     label="Humidity",
#     showCurrentValue=True,
#     size=250,
#     max=100,
#     min=0    
# )
# daq_Fahrenheit_ToggleSwitch = daq.ToggleSwitch(
#     id='fahrenheit-switch',
#     value=False
# )

# daq_led = daq.LEDDisplay(
#     id='light-intensity',
#     label="Light Intensity Value",
#     labelPosition='bottom',
#     value = 0,
#     size = 50
# )

# # create fan gauge
# fan_gauge = daq.Gauge(
#     id='fan-gauge',
#     label='Fan Speed',
#     min=0,
#     max=100,
#     value=50,
#     color={"gradient":True,"ranges":{"green":[0,50],"yellow":[50,75],"red":[75,100]}}
# )

# #interval
# fan_Status_Message_Interval = dcc.Interval(
#     id='fan_status_message_update',
#     disabled=False,
#     interval=1 * 1000, # update every second for frequently changing data
#     n_intervals=0
# )

# fan_Interval = dcc.Interval(
# id = 'fan-update',
# disabled=False,
# interval = 1 * 5000, # update every 5 seconds for frequently changing data
# n_intervals = 0)

# humidity_Interval = dcc.Interval(
# id = 'humid-update',
# disabled=False,
# interval = 1 * 2000, # update every 2 seconds for frequently changing data
# n_intervals = 0)

# temperature_Interval = dcc.Interval(
# id = 'temp-update',
# disabled=False,
# interval = 1* 60000, # update every minute for less frequently changing data
# n_intervals = 0)

# light_Intensity_Interval = dcc.Interval(
# id = 'light-intensity-update',
# disabled=False,
# interval = 1*3000, # update every 3 seconds for frequently changing data
# n_intervals = 0)

# led_On_Email_Interval = dcc.Interval(
# id = 'led-email-status-update',
# disabled=False,
# interval = 1*5000,
# n_intervals = 0)

# userinfo_Interval = dcc.Interval(
# id = 'userinfo-update',
# disabled=False,
# interval = 1*5000, # update every 5 seconds for less frequently changing data
# n_intervals = 0)

# bluetooth_Interval = dcc.Interval(
# id = 'bluetooth-update',
# disabled=False,
# interval = 1*5000, # update every 5 seconds for less frequently changing data
# n_intervals = 0)

# fahrenheit_Interval = dcc.Interval(
# id = 'fahrenheit-update',
# disabled=False,
# interval = 1*60000, # update every minute for less frequently changing data
# n_intervals = 0)

# #all fan related html
# html_Div_Fan_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url, id='lottie-gif', isStopped=True, isClickToPauseDisabled=True)], id='fan_display')
# html_Fan_Status_Message = html.H5(id='fan_status_message',style={'text-align':'center'})
# html_Fan_Label = html.H6("Electric Fan", style={'text-align': 'center'});

# #all related to light intensity and led html
# html_Light_Intensity_Label = html.H6('Light Intensity',style={'text-align':'center'})
# html_Led_Status_Message = html.H1(id='light_h1',style={'text-align':'center'})

# #all temperature related html
# html_Celcius_Label = html.H6('Celcius',style={'text-align':'center'})
# html_Fahrenheit_Label = html.H6('Fahrenheit',style={'text-align':'center'})

# #all bluetooth related html
# html_Bluetooth_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url2, isClickToPauseDisabled=True)])
# html_bluetooth_Label =  html.H6('Bluetooth Devices',style={'text-align':'center'})


# sidebar  =html.Div({
#     html.H3('User Profile', style={'text-align': 'center', 'margin-top': '20px'}),
#     dbc.CardBody([
#         html.Img(src=path_to_picture, id="picture_path", style={'border-radius': '80px', 'width':'140px', 'height':'140px', 'object-fit': 'cover', 'display': 'block','margin-left':'auto','margin-right': 'auto'}),
#         html.H6("Username:" + str(user_id), style={'margin-top':'30px'}, id="username_user_data"),
#         html.H4("Favorites ", style={'margin-top':'40px'}),
#         html.H6("Humidity: " + str(humidity), style={'margin-left':'15px'}, id="humidity_user_data"),
#         html.H6("Temperature: " + str(temp_threshold), style={'margin-left':'15px'}, id="temperature_user_data"),
#         html.H6("Light Intensity: " + str(light_threshold), style={'margin-left':'15px'}, id="lightintensity_user_data")
#     ])
# }) 

# card_content1 = dbc.Container([
#     dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
#     dbc.Row([
#         dbc.Col(dbc.Card(dbc.Col(daq_Humudity), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(dbc.Col(html.Div([daq_Thermometer, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#     ], justify="center"),
#     dbc.Row([
#         dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#     ], justify="center", className="mt-5"),
# ], fluid=True)

# content = html.Div([dbc.Row([card_content1, humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval, fan_Interval])])

# #app.layout = dbc.Container([dbc.Row(navbar), dbc.Row([dbc.Col(sidebar, width=2), dbc.Col(content, width=10, className="bg-secondary")], style={"height": "100vh"})], fluid=True)
# #app.layout = dbc.Container([dbc.Row(navbar), dbc.Row([dbc.Col(sidebar, width=2), dbc.Col(content, width=10, className="bg-secondary")], style={"height": "100vh"})], fluid=True)
# app.layout = dbc.Col(dbc.Card(dbc.Col(html.Div([daq_Humidity, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),

# @app.callback(Output('my-gauge-1', 'value'), Input('humid-update', 'n_intervals'))
# def update_output(value):
#     dht = DHT.DHT(DHTPin)
#     while(True):
#         for i in range(0,15):
#             chk = dht.readDHT11()
#             if (chk is dht.DHTLIB_OK):
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         print("Humidity : %.2f \t \n"%(dht.humidity))
#         return dht.humidity

# """@app.callback(
#     [Output('my-thermometer-1', 'value'), Output('my-thermometer-1', 'min'), Output('my-thermometer-1', 'max'), Output('my-thermometer-1', 'scale'), Output('my-thermometer-1', 'units')],
#     [Input('fahrenheit-switch', 'value'), Input('temp-update', 'n_intervals')])
# """
# @app.callback(
#     [Output('my-thermometer-1', 'value'), Output('my-thermometer-1', 'min'), Output('my-thermometer-1', 'max'), Output('my-thermometer-1', 'scale'), Output('my-thermometer-1', 'units')],
#     [Input('fahrenheit-switch', 'value'), Input('temp-update', 'n_intervals')])

   
# def update_output(switch_state, temp_value, interval_value):
#     dht = DHT.DHT(DHTPin)   
#     while(True):
#         for i in range(0,15):            
#             chk = dht.readDHT11()     
#             if (chk is dht.DHTLIB_OK):      
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         temperature = dht.temperature
#         print("Temperature : %.2f \n"%(dht.temperature))
#         temp_email_sent
#         if dht.temperature >= temp_threshold and temp_email_sent == False:
#             sendEmail()
#             temp_email_sent = True
             
#         if switch_state:
#            return (temperature * 1.8) + 32, 40, 120, {'start': 40, 'interval': 10}, 'F'
#         else:
#             return temperature, -40, 60, {'start': -40, 'interval': 10}, 'C'

# # Checks if the Motor is active or not
# def is_fan_on():  
#     if GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3):
#         return True
#     else:
#         return False
        
# from dash import Output, Input

# def is_fan_on():  
#     return GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3)

# # Callback for the Fan Lottie gif and status message
# @app.callback([Output('fan_status_message', 'children'), Output('lottie-gif', 'isStopped')], Input('fan_status_message_update', 'n_intervals'))
# def update_h1(n):
#     return ("Status: On", False) if is_fan_on() else ("Status: Off", True)

# @app.callback([Output('username_user_data', 'children'), Output('humidity_user_data', 'children'), Output('temperature_user_data', 'children'), Output('lightintensity_user_data', 'children'), Output('picture_path', 'src')], Input('userinfo-update', 'n_intervals'))
# def update_user_information():
#     #return "Username: " + str(user_id), "Humidity: 40", "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture
#     return "Username: " + str(user_id), "Humidity: " + str(humidity), "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture

# @app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))  
# def update_output(value):
#     print("Here is light intensity: ", esp_message) 
#     return esp_message

# def send_email(subject, body):
#     smtp_server = 'smtp.gmail.com'
#     port = 587
#     sender_email = 'john190curry@gmail.com'
#     receiver_email = 'john190curry@gmail.com'
#     password = 'CUURY23JOHN45'
#     message = f"{subject}\n\n{body}"
#     context = ssl.create_default_context()

#     with smtplib.SMTP(smtp_server, port) as server:
#         server.starttls(context=context)
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, message)

# def sendEmail():
#     send_email("Subject: Home Temperatue NOTIFICATION", "The temperature is at high")

# def sendEmailLed():
#     time = datetime.now().strftime("%H:%M")
#     send_email("Subject: LIGHT NOTIFICATION", f"The Light is ON at {time}")

# def send_Email_Led(lightValue):
#     global emails
#     if lightValue < light_threshold and emails == 0:
#         sendEmailLed()
#         emails += 1

# @app.callback([Output('email_heading', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))      
# def update_email_status(value):
#     lightvalue = esp_message
#     send_Email_Led(lightvalue)
    
#     if emails > 0 and lightvalue < light_threshold:
#         GPIO.output(LedPin, GPIO.HIGH)
#         return "Email has been sent. Lightbulb is ON", light_bulb_on
#     else:
#         GPIO.output(LedPin, GPIO.LOW)
#         return ("Email has been sent. Lightbulb is OFF", light_bulb_off) if emails > 0 else ("No email has been sent. Lightbulb is OFF", light_bulb_off)

# if __name__ == '__main__':
#     app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)

# # def sendUserEnteredEmail(user_name): #for user(rfid)



# from dash import Dash, html, dcc, Input, Output
# from dash_bootstrap_templates import ThemeChangerAIO
# import dash_bootstrap_components as dbc
# import dash_extensions as de
# import dash_daq as daq
# import RPi.GPIO as GPIO
# import time
# from time import sleep
# import Freenove_DHT as DHT
# import random
# from paho.mqtt import client as mqtt_client
# import sqlite3

# # Images and GIFs
# light_bulb_off = 'assets/lightbulbOFF.png'
# light_bulb_on = 'assets/lightbulbON.png'
# url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json" # fan lottie gif
# options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))
# url2 = "https://assets8.lottiefiles.com/packages/lf20_ylvmhzmx.json" # bluetooth lottie gif

# dbc_css = (
#     "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.1/dbc.min.css"
# )
# app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])

# theme_change = ThemeChangerAIO(aio_id="theme", radio_props={"persistence": True}, button_props={"color": "danger","children": "Change Theme"})

# # Side bar functions
# navbar = dbc.NavbarSimple(
#     children=[
#         dbc.NavItem(theme_change),
#     ],
#     brand="Fiacre Dashboard",
#     color="Blue",
#     dark=True,
#     sticky="top"
# )

# # User Information Variables
# user_id = "Default"
# temp_threshold = 25.0
# light_threshold = 0
# humidity = 40
# path_to_picture = 'photos/Ppic.jpg'

# # MQTT connection variables
# broker = '192.168.0.158' #ip in Lab class
# port = 1883
# topic1 = "esp/lightintensity"
# topic2 = "esp/rfid"
# client_id = f'python-mqtt-{random.randint(0, 100)}'
# esp_message = 0
# esp_rfid_message = "000000"

# # Counters and checkers
# temp_email_sent = False
# fan_status_checker = False
# emails = 0    # just checks if email has been sent at some stage

# # For Phase02 temperature (used in temperature callback)
# temperature = 0

# # RPI GPIO
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# DHTPin = 40 # equivalent to GPIO21
# GPIO.setmode(GPIO.BOARD)
# GPIO.setwarnings(False)
# Motor1 = 35 # Enable Pin
# Motor2 = 37 # Input Pin
# Motor3 = 33 # Input Pin
# LedPin = 38
# GPIO.setup(Motor1, GPIO.IN)
# GPIO.setup(Motor2, GPIO.IN)
# GPIO.setup(Motor3, GPIO.IN)
# GPIO.setup(LedPin, GPIO.OUT)

# # create thermometer
# daq_Thermometer = daq.Thermometer(
#     id='my-thermometer-1',
#     min=-40,
#     max=60,
#     scale={'start': -40, 'interval': 10},
#     label="Temperature",
#     showCurrentValue=True,
#     height=150,
#     units="C",
#     color="red"
# )

# # create humudity
# daq_Humudity = daq.Gauge(
#     id='my-gauge-1',
#     label="Humidity",
#     showCurrentValue=True,
#     size=250,
#     max=100,
#     min=0    
# )
# daq_Fahrenheit_ToggleSwitch = daq.ToggleSwitch(
#     id='fahrenheit-switch',
#     value=False
# )

# daq_led = daq.LEDDisplay(
#     id='light-intensity',
#     label="Light Intensity Value",
#     labelPosition='bottom',
#     value = 0,
#     size = 50
# )

# # create fan gauge
# fan_gauge = daq.Gauge(
#     id='fan-gauge',
#     label='Fan Speed',
#     min=0,
#     max=100,
#     value=50,
#     color={"gradient":True,"ranges":{"green":[0,50],"yellow":[50,75],"red":[75,100]}}
# )

# #interval
# fan_Status_Message_Interval = dcc.Interval(
#     id='fan_status_message_update',
#     disabled=False,
#     interval=1 * 1000, # update every second for frequently changing data
#     n_intervals=0
# )

# fan_Interval = dcc.Interval(
# id = 'fan-update',
# disabled=False,
# interval = 1 * 5000, # update every 5 seconds for frequently changing data
# n_intervals = 0)

# humidity_Interval = dcc.Interval(
# id = 'humid-update',
# disabled=False,
# interval = 1 * 2000, # update every 2 seconds for frequently changing data
# n_intervals = 0)

# temperature_Interval = dcc.Interval(
# id = 'temp-update',
# disabled=False,
# interval = 1* 60000, # update every minute for less frequently changing data
# n_intervals = 0)

# light_Intensity_Interval = dcc.Interval(
# id = 'light-intensity-update',
# disabled=False,
# interval = 1*3000, # update every 3 seconds for frequently changing data
# n_intervals = 0)

# led_On_Email_Interval = dcc.Interval(
# id = 'led-email-status-update',
# disabled=False,
# interval = 1*5000,
# n_intervals = 0)

# userinfo_Interval = dcc.Interval(
# id = 'userinfo-update',
# disabled=False,
# interval = 1*5000, # update every 5 seconds for less frequently changing data
# n_intervals = 0)

# bluetooth_Interval = dcc.Interval(
# id = 'bluetooth-update',
# disabled=False,
# interval = 1*5000, # update every 5 seconds for less frequently changing data
# n_intervals = 0)

# fahrenheit_Interval = dcc.Interval(
# id = 'fahrenheit-update',
# disabled=False,
# interval = 1*60000, # update every minute for less frequently changing data
# n_intervals = 0)

# #all fan related html
# html_Div_Fan_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url, id='lottie-gif', isStopped=True, isClickToPauseDisabled=True)], id='fan_display')
# html_Fan_Status_Message = html.H5(id='fan_status_message',style={'text-align':'center'})
# html_Fan_Label = html.H6("Electric Fan", style={'text-align': 'center'});

# #all related to light intensity and led html
# html_Light_Intensity_Label = html.H6('Light Intensity',style={'text-align':'center'})
# html_Led_Status_Message = html.H1(id='light_h1',style={'text-align':'center'})

# #all temperature related html
# html_Celcius_Label = html.H6('Celcius',style={'text-align':'center'})
# html_Fahrenheit_Label = html.H6('Fahrenheit',style={'text-align':'center'})

# #all bluetooth related html
# html_Bluetooth_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url2, isClickToPauseDisabled=True)])
# html_bluetooth_Label =  html.H6('Bluetooth Devices',style={'text-align':'center'})


# sidebar  =html.Div({
#     html.H3('User Profile', style={'text-align': 'center', 'margin-top': '20px'}),
#     dbc.CardBody([
#         html.Img(src=path_to_picture, id="picture_path", style={'border-radius': '80px', 'width':'140px', 'height':'140px', 'object-fit': 'cover', 'display': 'block','margin-left':'auto','margin-right': 'auto'}),
#         html.H6("Username:" + str(user_id), style={'margin-top':'30px'}, id="username_user_data"),
#         html.H4("Favorites ", style={'margin-top':'40px'}),
#         html.H6("Humidity: " + str(humidity), style={'margin-left':'15px'}, id="humidity_user_data"),
#         html.H6("Temperature: " + str(temp_threshold), style={'margin-left':'15px'}, id="temperature_user_data"),
#         html.H6("Light Intensity: " + str(light_threshold), style={'margin-left':'15px'}, id="lightintensity_user_data")
#     ])
# }) 

# card_content1 = dbc.Container([
#     dbc.Row(dbc.Col(html.H1(html.B("SMART HOME COMPONENTS"), className="text-center mt-4 mb-2"))),
#     dbc.Row([
#         dbc.Col(dbc.Card(dbc.Col(daq_Humudity), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(dbc.Col(html.Div([daq_Thermometer, dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)])])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#     ], justify="center"),
#     dbc.Row([
#         dbc.Col(dbc.Card(html.Div([html_Light_Intensity_Label, html.Img(id="light-bulb", src=light_bulb_off, style={'width':'80px', 'height': '110px', 'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}), daq_led, html.H5(id='email_heading',style ={"text-align":"center"})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
#         dbc.Col(dbc.Card(html.Div([html_bluetooth_Label, html_Bluetooth_Gif, html.H5("Number of Bluetooth Devices: ", id='bluetooth_heading',style ={"text-align":"center", 'margin-top':'10px'})]), color="secondary", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")
#     ], justify="center", className="mt-5"),
# ], fluid=True)

# content = html.Div([dbc.Row([card_content1, humidity_Interval, temperature_Interval, light_Intensity_Interval, led_On_Email_Interval, userinfo_Interval, bluetooth_Interval, fahrenheit_Interval, fan_Status_Message_Interval, fan_Interval])])

# app.layout = dbc.Container([dbc.Row(navbar), dbc.Row([dbc.Col(sidebar, width=2), dbc.Col(content, width=10, className="bg-secondary")], style={"height": "100vh"})], fluid=True)

# @app.callback(Output('my-gauge-1', 'value'), Input('humid-update', 'n_intervals'))
# def update_output(value):
#     dht = DHT.DHT(DHTPin)
#     while(True):
#         for i in range(0,15):
#             chk = dht.readDHT11()
#             if (chk is dht.DHTLIB_OK):
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         print("Humidity : %.2f \t \n"%(dht.humidity))
#         return dht.humidity

# @app.callback(
#     [Output('my-thermometer-1', 'value'), Output('my-thermometer-1', 'min'), Output('my-thermometer-1', 'max'), Output('my-thermometer-1', 'scale'), Output('my-thermometer-1', 'units')],
#     [Input('fahrenheit-switch', 'value'), Input('temp-update', 'n_intervals')])
    
# def update_output(switch_state, temp_value, interval_value):
#     dht = DHT.DHT(DHTPin)   
#     while(True):
#         for i in range(0,15):            
#             chk = dht.readDHT11()     
#             if (chk is dht.DHTLIB_OK):      
#                 break
#             time.sleep(0.1)
#         time.sleep(2)
#         temperature = dht.temperature
#         print("Temperature : %.2f \n"%(dht.temperature))
#         global temp_email_sent
#         if dht.temperature >= temp_threshold and temp_email_sent == False:
#             sendEmail()
#             temp_email_sent = True
             
#         if switch_state:
#            return (temperature * 1.8) + 32, 40, 120, {'start': 40, 'interval': 10}, 'F'
#         else:
#             return temperature, -40, 60, {'start': -40, 'interval': 10}, 'C'

# # Checks if the Motor is active or not
# def is_fan_on():  
#     if GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3):
#         return True
#     else:
#         return False
        
# from dash import Output, Input

# def is_fan_on():  
#     return GPIO.input(Motor1) and not GPIO.input(Motor2) and GPIO.input(Motor3)

# # Callback for the Fan Lottie gif and status message
# @app.callback([Output('fan_status_message', 'children'), Output('lottie-gif', 'isStopped')], Input('fan_status_message_update', 'n_intervals'))
# def update_h1(n):
#     return ("Status: On", False) if is_fan_on() else ("Status: Off", True)

# @app.callback([Output('username_user_data', 'children'), Output('humidity_user_data', 'children'), Output('temperature_user_data', 'children'), Output('lightintensity_user_data', 'children'), Output('picture_path', 'src')], Input('userinfo-update', 'n_intervals'))
# def update_user_information(n):
#     return "Username: " + str(user_id), "Humidity: 40", "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), path_to_picture

# @app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))  
# def update_output(value):
#     print("Here is light intensity: ", esp_message) 
#     return esp_message

# def send_email(subject, body):
#     smtp_server = 'smtp.gmail.com'
#     port = 587
#     sender_email = 'john190curry@gmail.com'
#     receiver_email = 'john190curry@gmail.com'
#     password = 'CUURY23JOHN45'
#     message = f"{subject}\n\n{body}"
#     context = ssl.create_default_context()

#     with smtplib.SMTP(smtp_server, port) as server:
#         server.starttls(context=context)
#         server.login(sender_email, password)
#         server.sendmail(sender_email, receiver_email, message)

# def sendEmail():
#     send_email("Subject: Home Temperatue NOTIFICATION", "The temperature is at high")

# def sendEmailLed():
#     time = datetime.now().strftime("%H:%M")
#     send_email("Subject: LIGHT NOTIFICATION", f"The Light is ON at {time}")

# def send_Email_Led(lightValue):
#     global emails
#     if lightValue < light_threshold and emails == 0:
#         sendEmailLed()
#         emails += 1

# @app.callback([Output('email_heading', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))      
# def update_email_status(value):
#     lightvalue = esp_message
#     send_Email_Led(lightvalue)
    
#     if emails > 0 and lightvalue < light_threshold:
#         GPIO.output(LedPin, GPIO.HIGH)
#         return "Email has been sent. Lightbulb is ON", light_bulb_on
#     else:
#         GPIO.output(LedPin, GPIO.LOW)
#         return ("Email has been sent. Lightbulb is OFF", light_bulb_off) if emails > 0 else ("No email has been sent. Lightbulb is OFF", light_bulb_off)

# if __name__ == '__main__':
#     app.run_server(debug=False, dev_tools_ui=False, dev_tools_props_check=False)

# # def sendUserEnteredEmail(user_name): #for user(rfid)