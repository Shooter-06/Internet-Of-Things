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
    brand="IOT PROJECT",
    color="blue",
    dark=True,
    sticky="top"
)

#VARIABLES DELCARATION
broker = '192.168.1.110' #chilka home
port = 1883
topic1 = "esp/lightintensity"
topic2 = "esp/lightswitch"

# generate client ID with pub prefix randomly
client_id = f'python-mqtt-{random.randint(0, 100)}'


esp_message = 0
esp_lightswitch_message = "OFF"
GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)
LedPin = 35 # Led Pin/Enable Pin
GPIO.setup(LedPin,GPIO.OUT)
email_counter = 0    # just checks if email has been sent at some stage

EMAIL = '2073000@gmail.com'
PASSWORD = '123456&H'

SERVER = ''
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

light_bulb_off="photos/OFFbulb.jpg"
light_bulb_on="photos/OnBulb.jpg"
url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json"
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))

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


'''sidebar = html.Div([
    html.H3('User Profile', style={'text-align': 'center'}),
    dbc.CardBody([
            html.Img(src='assets/minion.jpg', style={'border-radius': '80px', 'width':'140px', 'height':'140px', 'object-fit': 'cover', 'display': 'block','margin-left':'auto','margin-right': 'auto'}),
            html.H6("Username"),
            html.H4("Favorites: "),
            html.H6("Humidity"),
            html.H6("Temperature"),
            html.H6("Light Intensity")])
    ])
'''
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

# app.layout = dbc.Container([
#                 dbc.Row(navbar),
#                 dbc.Row([
#                     dbc.Col(sidebar, width=2), 
#                     dbc.Col(content, width=10, className="bg-secondary") # content col
#                 ], style={"height": "100vh"}), # outer
#             ], fluid=True) #container

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