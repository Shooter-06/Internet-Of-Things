import smtplib, ssl, getpass
from datetime import datetime

class Send:
    # code to send the email
    def sendEmail():
        smtp_server = 'smtp.gmail.com'
        port = 587  # For starttls

        sender_email = 'john190curry@gmail.com'
        receiver_email= 'john190curry@gmail.com'
        password = 'CUURY23JOHN45'

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

Send.sendEmail()  # call sendEmail method of the Send class

#put in an infinite loop or something, find a way to feed the temperature data to this method
#if ("THE TEMPERATURE IS ABOVE 24"):
#   sendEmail()

# put in an infinite loop or something, find a way to feed the light data to this method
# if (light_is_on):
#    Send.sendEmail()