import email
import imaplib
import getpass
import smtplib
from email.mime.text import MIMEText
from dash import Dash, html, dcc, Input, Output
import dash_bootstrap_components as dbc
import dash_daq as daq
import RPi.GPIO as GPIO
import time
from time import sleep

GPIO.setmode(GPIO.BOARD)
GPIO.setwarnings(False)

#DC motor pins(USING BOARD/Physical addressing)
Motor1 = 35 # Enable Pin
Motor2 = 37 # Input Pin
Motor3 = 33 # Input Pin

GPIO.setup(Motor1,GPIO.OUT)
GPIO.output(Motor1,GPIO.LOW)

# Set up the IMAP server details
# Set up the IMAP server details
EMAIL = 'john190curry@gmail.com'
PASSWORD = 'CUURY23JOHN45'


SERVER = 'imap.gmail.com'
imap_port = 993


# function to send an email
def sendEmail(subject, body):
    try:
        smtp_server = smtplib.SMTP('smtp.gmail.com', 587)
        smtp_server.ehlo()
        smtp_server.starttls()
        smtp_server.login(EMAIL, PASSWORD)

        message = MIMEText(body)
        message['Subject'] = subject
        message['From'] = EMAIL
        message['To'] = EMAIL

        smtp_server.sendmail(EMAIL, EMAIL, message.as_string())
        smtp_server.quit()

        print("Email sent successfully")

    except Exception as ex:
        print("Unable to send email")
        print(ex)


# physical fan(DC motor)
def activateFan():
    print("pass here")
    GPIO.setup(Motor1,GPIO.OUT)
    GPIO.setup(Motor2,GPIO.OUT)
    GPIO.setup(Motor3,GPIO.OUT)
    
    GPIO.output(Motor1,GPIO.HIGH)
    GPIO.output(Motor2,GPIO.LOW)
    GPIO.output(Motor3,GPIO.HIGH)

    # send an email when the fan is turned on
    sendEmail("Fan turned on", "The fan has been turned on in the dashboard")

    
message = ''
mail_content = ''
replybody = ''
replylist = []

#SETUP PERMANENT EMAIL AND HARD CODED PASSWORD
while True:

    mail = imaplib.IMAP4_SSL(SERVER)
    time.sleep(5)
    mail.login(EMAIL, PASSWORD)
    mail.select('inbox')
    #SUBJECT is set to fan control so it detects that its a reply probably
    status, data = mail.search(None,'(FROM:{EMAIL}UBJECT "FAN CONTROL" UNSEEN)')
    #status, data = mail.search(None,'(SUBJECT "FAN CONTROL" UNSEEN)')

    #most of this is useless stuff, check the comments 
    mail_ids = []
    for block in data:
        mail_ids += block.split()
    
    for i in mail_ids:
        status, data = mail.fetch(i, '(RFC822)')
        for response_part in data:
            if isinstance(response_part, tuple):
                message = email.message_from_bytes(response_part[1])
                mail_from = message['from']
                mail_subject = message['subject']
                if message.is_multipart():
                    mail_content = ''

                    for part in message.get_payload():
                        #this is where the code activates when we reply YES or anything else
                        if part.get_content_type() == 'text/plain':
                            mail_content += part.get_payload()
                           
                            #print(f'MAIL CONTENT: {mail_content}')
                            replybody = str(mail_content.split('\n', 1)[0])
                            print(f'IF THIS IS NOT YES WHEN YOU REPLY TO THE ORIGINAL EMAIL ITS BAD: {replybody}')
                            replybody = (replybody.upper()).strip()
                            replylist.append(replybody)
                            print(replylist)
                            
                            
                            # Makes sure only "YES" would activate the fan
                            if replybody.__eq__("YES") and len(str(replybody)) == 3 and replylist[0] == "YES":
                                activateFan()
                            if replylist[0] == "NO":
                                #status, data = mail.fetch(i, '(RFC822)')
                                status, data = mail.search(None,'(FROM "iotdashboardother2022@outlook.com" SUBJECT "FAN CONTROL" UNSEEN)')
                                for num in data[0].split():
                                    mail.store(num, '+FLAGS', '\\Deleted')
                                mail.expunge()
                                
                                
                            
                            replylist.clear()
                            
                else:
                    #This part gets called when the email is not a reply (left for testing)
                    mail_content = message.get_payload()
                    print(f'From: {mail_from}')
                    print(f'Subject: {mail_subject}')
                    print(f'Content: {mail_content}')
      