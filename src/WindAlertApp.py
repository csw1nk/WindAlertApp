import configparser
import requests
import time
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
import logging
from email.header import decode_header
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Read configuration
config = configparser.ConfigParser()
config.read('../config.ini')
API_KEY = config['DEFAULT']['API_KEY']
EMAIL = config['EMAIL']['EMAIL']
APP_PASSWORD = config['EMAIL']['APP_PASSWORD']
COREY_PHONE = config['PHONE_NUMBERS']['Corey']
imap_url = 'imap.gmail.com'

# Store the last alert time
last_alert_time = None
LAT = '42.708720'
LON = '-83.214720'
URL = f'https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=imperial'

def get_wind_speed():
    response = requests.get(URL)
    data = response.json()
    wind_speed = data['wind']['speed']
    logging.info(f"API Call: Received wind speed data: {wind_speed} mph")
    return wind_speed

def send_sms_via_email(recipient_number, carrier_gateway, message):
    global last_alert_time
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    msg = MIMEText(message)
    msg['Subject'] = "Wind Alert"
    msg['From'] = EMAIL
    msg['To'] = f"{recipient_number}@{carrier_gateway}"
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(EMAIL, APP_PASSWORD)
        server.sendmail(EMAIL, msg['To'], msg.as_string())
        last_alert_time = datetime.now(timezone.utc)  # Update the time when the alert was sent
    logging.info(f"Sent SMS to {recipient_number} via {carrier_gateway}")

def read_emails():
    global last_alert_time
    if last_alert_time is None:
        return 'continue'  # Skip processing if no alert has been sent yet
    with imaplib.IMAP4_SSL(imap_url) as mail:
        mail.login(EMAIL, APP_PASSWORD)
        mail.select('inbox')
        status, messages = mail.search(None, '(UNSEEN)')
        for mail_id in messages[0].split():
            _, msg = mail.fetch(mail_id, '(RFC822)')
            mail.store(mail_id, '+FLAGS', '\\Seen')  # Mark email as read
            for response_part in msg:
                if isinstance(response_part, tuple):
                    message = email.message_from_bytes(response_part[1])
                    email_date = message['date']
                    email_datetime = parsedate_to_datetime(email_date)
                    if email_datetime > last_alert_time:
                        subject = decode_header(message['subject'])[0][0]
                        if isinstance(subject, bytes):
                            subject = subject.decode().strip().lower()
                        logging.info(f"Processing email with subject: {subject} received at {email_date}")
                        if 'resume' in subject.lower():
                            return 'resume'
    return 'continue'

def main_loop():
    global last_alert_time
    pause_api_calls = False  # Flag to control API calls
    alert_sent = False  # To ensure alert is sent only once per wind condition
    check_email_interval = 300  # Default check interval for wind is every 5 minutes

    while True:
        if not pause_api_calls:
            wind_speed = get_wind_speed()
            if wind_speed > 1 and not alert_sent:
                message = "Honey, the wind's picking up! :-O Let's roll in the awning! ~~~"
                logging.info(f"Alert condition met: Wind speed is {wind_speed} mph. {message}")
                send_sms_via_email(COREY_PHONE, "vtext.com", message)
                alert_sent = True
                pause_api_calls = True  # Pause further API calls until resumed
                check_email_interval = 30  # Start checking emails every 10 seconds after sending an alert

        command = read_emails()
        if command == 'resume':
            pause_api_calls = False  # Resume API calls
            alert_sent = False  # Reset alert_sent to allow future alerts
            check_email_interval = 300  # Resume normal interval for wind speed checks
            logging.info("Received resume command. Resuming API calls and alerts.")

        time.sleep(check_email_interval)

if __name__ == "__main__":
    logging.info("Starting Wind Alert application.")
    main_loop()
