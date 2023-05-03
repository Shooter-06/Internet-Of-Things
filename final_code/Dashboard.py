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

app = Dash(__name__,  meta_tags=[
        {
            "name": "viewport",
            "content": "width=device-width, initial-scale=1.0",
        }
    ])
theme_change = ThemeChangerAIO(aio_id="theme", radio_props={"persistence": True}, button_props={"color": "danger","children": "Change Theme"}) 
# Set up the navbar
navbar = dbc.NavbarSimple(
    children=[
        dbc.NavItem(theme_change),
    ],
    brand="Fiacre DashBoard",
    color="blue",
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
topic2 = "IoTLab/rfid"
client_id = f'python-mqtt-{random.randint(0, 100)}'
esp_message = 0
esp_rfid_message = "000000"

profile='https://images.immediate.co.uk/production/volatile/sites/3/2021/12/miles-morales-Spider-Man-Into-The-Spider-Verse-9e2bb6e.jpg?quality=90&resize=620,414'


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
# url="https://assets5.lottiefiles.com/packages/lf20_UdIDHC.json"
url= "https://assets3.lottiefiles.com/packages/lf20_acmgs9pi.json"
options = dict(loop=True, autoplay=True, rendererSettings=dict(preserveAspectRatio='xMidYMid slice'))


def on_message(client, userdata, msg):
    global light_in, last_rfid_message
    if msg.topic == "lightIntensity":
        light_in = int(msg.payload.decode("utf-8"))
    elif msg.topic == "IoTLab/rfid":
        last_rfid_message = msg.payload.decode("utf-8")

mqtt_client_instance = mqtt_client.Client()
mqtt_client_instance.on_message = on_message
# mqtt_client_instance.connect("192.168.211.248")
mqtt_client_instance.connect("127.0.0.1")
mqtt_client_instance.subscribe("IoTLab/rfid")
mqtt_client_instance.loop_start()

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
        
    print(str(user_id) + " " + str(temp_threshold) + " " + str(light_threshold) + " " + picture)



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
 
# all fan related html
html_Div_Fan_Gif = html.Div([de.Lottie(options=options, width="40%", height="25%", url=url, id='lottie-gif', isStopped=True, isClickToPauseDisabled=True)], id='fan_display')
html_Fan_Status_Message = html.H5(id='fan_status_message',style={'text-align':'center'})
html_Fan_Label = html.H6("Electric Fan", style={'text-align': 'center'});

# all related to light intensity and led html
html_Light_Intensity_Label =  html.H6('Light Intensity',style={'text-align':'center'})
html_Led_Status_Message = html.H1(id='light_h1',style={'text-align':'center'})

#all temperature related html
html_Celcius_Label =  html.H6('Celcius',style={'text-align':'center'})
html_Fahrenheit_Label =  html.H6('Fahrenheit',style={'text-align':'center'})

# Intervals
fan_Status_Message_Interval = dcc.Interval(
            id='fan_status_message_update',
            disabled=False,
            interval=1 * 3000,
            n_intervals=0)
            
fan_Interval = dcc.Interval(
            id = 'fan-update',
            disabled=False,
            interval = 1 * 8000,  
            n_intervals = 0)
            
humidity_Interval = dcc.Interval(
            id = 'humid-update',
            disabled=False,
            interval = 1 * 3000,
            n_intervals = 0)

temperature_Interval =  dcc.Interval(
            id = 'temp-update',
            disabled=False,
            interval = 1*20000,  
            n_intervals = 0)

light_Intensity_Interval =  dcc.Interval(
            id = 'light-intensity-update',
            disabled=False,
            interval = 1*5000,   
            n_intervals = 0)

led_On_Email_Interval = dcc.Interval(
            id = 'led-email-status-update',
            disabled=False,
            interval = 1*5000,   
            n_intervals = 0)

user_data_interval = dcc.Interval(
    id='user_data_interval',
    interval=2000,  # 5 seconds interval
    n_intervals=0
)
  
user_info = dcc.Interval(
            id = 'user_info',
            disabled=False,
            interval = 1*2000,   
            n_intervals = 0)

fahrenheit_Interval = dcc.Interval(
            id = 'fahrenheit-update',
            disabled=False,
            interval = 1*2000,   
            n_intervals = 0)

# sidebar = html.Div([
#     html.H3('User Profile', style={'text-align': 'center', 'margin-top': '20px'}),
#     dbc.CardBody([
#             html.Img(src=path_to_picture, id="picture_path", style={'border-radius': '80px', 'width':'140px', 'height':'140px', 'object-fit': 'cover', 'display': 'block','margin-left':'auto','margin-right': 'auto'}),
#             html.H6("Username:" + str(user_id), style={'margin-top':'30px'}, id="username_user_data"),
#             html.H4("Favorites ", style={'margin-top':'40px'}),
#             html.H6("Humidity: " + str(humidity), style={'margin-left':'15px'}, id="humidity_user_data"),
#             html.H6("Temperature: " + str(temp_threshold), style={'margin-left':'15px'}, id="temperature_user_data"),
#             html.H6("Light Intensity: " + str(light_threshold), style={'margin-left':'15px'}, id="lightintensity_user_data")
#             ])
#     ])

# Layout
sidebar = html.Div([
    html.H3('User Profile', style={'text-align': 'center'}),
    dbc.CardBody([
        html.Img(src='https://legendary-digital-network-assets.s3.amazonaws.com/wp-content/uploads/2021/12/12191403/Spider-Man-No-Way-Home-Miles-Morales.jpg',id="picture", style={'border-radius': '80px', 'width': '140px', 'height': '140px',
                                               'object-fit': 'cover', 'display': 'block', 'margin-left': 'auto',
                                               'margin-right': 'auto'}),
        html.H6("Username:" + str(id), style={'margin-top':'30px'}, id="username_data"),
            html.H4("Favorites ", style={'margin-top':'40px'}),
            html.H6("Humidity: " + str(humidity), style={'margin-left':'15px'}, id="humidity_data"),
            html.H6("Temperature: " + str(temp_threshold), style={'margin-left':'15px'}, id="temperature_data"),
            html.H6("Light Intensity: " + str(light_threshold), style={'margin-left':'15px'}, id="lightintensity_data")
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
            dbc.Col(dbc.Card(dbc.Col(daq_Gauge), color="white", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
            dbc.Col(dbc.Card(dbc.Col(html.Div([daq_Thermometer,
                                               dbc.Row([dbc.Col(html_Celcius_Label), dbc.Col(daq_Fahrenheit_ToggleSwitch), dbc.Col(html_Fahrenheit_Label)]) ])), color="white", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto"),
            dbc.Col(dbc.Card(dbc.Col(html.Div([html_Fan_Label, html_Div_Fan_Gif, html_Fan_Status_Message])), color="white", inverse=True, style={"width": "30rem", 'height': "22rem"}), width="auto")],
            justify="center",
        ),
        dbc.Row([
            dbc.Col(dbc.Card(
                     html.Div([
                         html_Light_Intensity_Label,
                         html.Img(id="light-bulb", src=light_bulb_off,
                                  style={'width':'80px', 'height': '110px',
                                  'display': 'block','margin-left':'auto','margin-right': 'auto', 'margin-top':'10px'}),
                         daq_Led_Light_Intensity_LEDDisplay,
                         html.H5(id='email_heading',style ={"text-align":"center"}) ]),
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

# Dashboard Layout
app.layout = dbc.Container([
                dbc.Row(navbar),
                dbc.Row([
                    dbc.Col(sidebar, width=2), 
                    dbc.Col(content, width=10, className="bg-secondary") # content col
                ], style={"height": "100vh"}), # outer
            ], fluid=True) #container

# Callback for the humidity
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

# Callback for thermometer and Celcius to Fahrenheit conversion
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
    while(True):
        for i in range(0,15):            
            chk = dht.readDHT11()     
            if (chk is dht.DHTLIB_OK):      
                break
            time.sleep(0.1)
        time.sleep(2)
        temperature = dht.temperature
        print("Temperature : %.2f \n"%(dht.temperature))
        global temp_email_sent
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

# Callback for the Fan Lottie gif and status message
@app.callback([Output('fan_status_message', 'children'), Output('lottie-gif', 'isStopped')],
              Input('fan_status_message_update', 'n_intervals'))
def update_h1(n):
    fan_status_checker = is_fan_on()
    
    if fan_status_checker:
        return "Status: On", False
    
    else:
        return "Status: Off", True

@app.callback([Output('username_data', 'children'),
               Output('humidity_data', 'children'),
               Output('temperature_data', 'children'),
               Output('lightintensity_data', 'children'),
               Output('picture', 'src')],
              Input('user_data_interval', 'n_intervals'))

def update_user_info(n_intervals):
    print("rfid callback")
    # Check if RFID is detected
    if last_rfid_message:
        user_data = get_from_database(last_rfid_message)
        if user_data:
            return ("Username: " + str(user_data['username']),
                    "Humidity: " + str(user_data['humidity']),
                    "Temperature: " + str(user_data['temperature']),
                    "Light Intensity: " + str(user_data['light_intensity']),
                    user_data['profile_image'])
    # If no RFID detected or no user found, return the default values
    return "Username: " + str(id), "Humidity: 30", "Temperature: " + str(temp_threshold), "Light Intensity: " + str(light_threshold), profile

#Callback for light intensity
@app.callback(Output('light-intensity', 'value'), Input('light-intensity-update', 'n_intervals'))  
def update_output(value):
#     run()
    print("Here is light intensity: ", esp_message) 
    return esp_message

#Email methods
def sendEmail(): #for temperature
        port = 587  # For starttls
        smtp_server = "smtp-mail.outlook.com"
        sender_email = "fiacreIot@outlook.com"
        receiver_email = "fiacreIot@outlook.com"
        password = '12345pass'
        subject = "Subject: FAN CONTROL" 
        body = "Your home temperature is greater than your desired threshold. Do you wish to turn on the fan. Reply YES if so."
        message = subject + '\n\n' + body
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

def sendLedStatusEmail(): #for LED
        print("PASSED BY SENDLEDSTATUSEMAIL method")
        port = 587  # For starttls
        smtp_server = "smtp-mail.outlook.com"
        sender_email = "fiacreIot@outlook.com"
        receiver_email = "fiacreIot@outlook.com"
        password = '12345pass'
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

def sendUserEnteredEmail(user_name): #for user(rfid)
        port = 587  # For starttls
        smtp_server = "smtp-mail.outlook.com"
        sender_email = "fiacreIot@outlook.com"
        receiver_email = "fiacreIot@outlook.com"
        password = '12345pass'
        subject = "Subject: USER ENTERED" 
        current_time = datetime.now()
        time = current_time.strftime("%H:%M")
        body = user_name + " has entered at: " + time
        message = subject + '\n\n' + body
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message) 
        
# MQTT subscribe codes
def connect_mqtt() -> mqtt_client:
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
#             print("Connected to MQTT Broker!")
            time.sleep(10)
        else:
            print("Failed to connect, return code %d\n", rc)
    client = mqtt_client.Client(client_id)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

# MQTT for light intensity
def on_message_from_lightintensity(client, userdata, message):
   global esp_message
   esp_message = int(float(message.payload.decode()))
#    print("Message Received from Photoresistor: ")
#    print(esp_message)

#MQTT for rfid tag
def on_message_from_rfid(client, userdata, message):
   global esp_rfid_message
   esp_rfid_message = message.payload.decode()
   print("Message Received from rfid: ")
   print(esp_rfid_message)
   get_from_database(esp_rfid_message)
   sendUserEnteredEmail(esp_rfid_message)

# def on_message(client, userdata, message):
#    print("Message Received from Others: "+message.payload.decode())
   
def run():
    client = connect_mqtt()
    client.subscribe(topic1, qos=1)
    client.subscribe(topic2, qos=1)
    client.message_callback_add(topic1, on_message_from_lightintensity)
    client.message_callback_add(topic2, on_message_from_rfid)
    client.loop_start()

# # Database code
# def get_from_database(rfid):
#     #Connect to the database
#     connection = pymysql.connect(host='localhost',
#                              user='root',
#                              password='root',
#                              database='IOT',
#                              charset='utf8mb4',
#                              cursorclass=pymysql.cursors.DictCursor)
#     with connection.cursor(pymysql.cursors.DictCursor) as cursor:
#     # Read a single record
#         sql = "SELECT * FROM USER WHERE id = %s"
#         # To execute the SQL query
#         cursor.execute(sql, (rfid))
#         user_info = cursor.fetchone()
#     print("Result from database select: ")
    
#     print(user_info)
#     if(user_info):
#         global email_counter 
#         global temp_email_sent
#         temp_email_sent = False
#         email_counter = 0
#         global user_id
#         user_id = user_info['id']
#         global temp_threshold
#         temp_threshold = user_info['temp_threshold']
#         global light_threshold
#         light_threshold = user_info['light_threshold']
#         global path_to_picture
#         path_to_picture = user_info['picture']
        
#     print(str(user_id) + " " + str(temp_threshold) + " " + str(light_threshold) + " " + path_to_picture)

# Checks if the light intensity value is lower than the user's desired threshold and send email and increase the email counter to know there is an email sent
def send_led_email_check(lightvalue):        
      global email_counter
      if lightvalue < light_threshold and email_counter == 0:
         print("passed here in send_led_email_check")
         sendLedStatusEmail()
         email_counter += 1
         
#Callback to change the lightbulb image & lightbulb status and update email sent message
@app.callback([Output('email_heading', 'children'), Output('light-bulb', 'src')], Input('led-email-status-update', 'n_intervals'))      
def update_email_status(value):
    lightvalue = esp_message
    send_led_email_check(lightvalue)
    
    if email_counter > 0 and lightvalue < light_threshold:
        GPIO.output(LedPin, GPIO.HIGH)
        return "Email has been sent. Lightbulb is ON", light_bulb_on
    elif email_counter > 0 and lightvalue > light_threshold:
        GPIO.output(LedPin, GPIO.LOW)
        return "Email has been sent. Lightbulb is OFF", light_bulb_off
    else:
        GPIO.output(LedPin, GPIO.LOW)
        return "No email has been sent. Lightbulb is OFF", light_bulb_off

if __name__ == '__main__':
   #app.run_server(debug=True)
    app.run_server(debug=False,dev_tools_ui=False,dev_tools_props_check=False)

  