import configparser
import requests
import time
import smtplib
from email.mime.text import MIMEText

# Setup to read config file
config = configparser.ConfigParser()
config.read('../config.ini')
API_KEY = config['DEFAULT']['API_KEY']
EMAIL = config['EMAIL']['EMAIL']
APP_PASSWORD = config['EMAIL']['APP_PASSWORD']

LAT = '42.708720'
LON = '-83.214720'
URL = f'https://api.openweathermap.org/data/2.5/weather?lat={LAT}&lon={LON}&appid={API_KEY}&units=imperial'

def get_wind_speed():
    response = requests.get(URL)
    data = response.json()
    wind_speed = data['wind']['speed']  # Wind speed in miles per hour
    return wind_speed

def send_sms_via_email(recipient_number, carrier_gateway, message):
    smtp_server = "smtp.gmail.com"
    smtp_port = 587  # Use TLS
    msg = MIMEText(message)
    msg['Subject'] = "Wind Alert"
    msg['From'] = EMAIL
    msg['To'] = f"{recipient_number}@{carrier_gateway}"
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(EMAIL, APP_PASSWORD)
    server.sendmail(EMAIL, msg['To'], msg.as_string())
    server.quit()

def check_wind_and_send_alerts():
    while True:
        wind_speed = get_wind_speed()
        print(f"Checked at {time.strftime('%Y-%m-%d %H:%M:%S')} - Current wind speed: {wind_speed} mph")
        if wind_speed > 20:  # Threshold for sending an alert
            message = "💕Honey, the wind's picking up 😨 Let's roll in the awning! 🌬️"
            print(f"Sending alert: {message}")
            # Send SMS to Corey
            send_sms_via_email("2485055521", "vtext.com", message)
            # Send SMS to Ericka
            send_sms_via_email("5866126796", "vtext.com", message)
        time.sleep(300)  # Sleep for 5 minutes (300 seconds)

if __name__ == "__main__":
    check_wind_and_send_alerts()
