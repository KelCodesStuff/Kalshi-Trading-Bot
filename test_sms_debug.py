import asyncio
import logging
from config import ALERT_SMS_EMAIL, SMTP_SERVER, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD
import smtplib
from email.mime.text import MIMEText

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("SMS_DEBUG")

def _send():
    message = "Debugging Kalshi Bot SMS"
    print(f"Attempting to send to {ALERT_SMS_EMAIL} via {SMTP_SERVER}:{SMTP_PORT} as {SMTP_USERNAME}")
    msg = MIMEText(message)
    msg['Subject'] = 'Test'
    msg['From'] = SMTP_USERNAME if SMTP_USERNAME else 'kalshibot@localhost'
    msg['To'] = ALERT_SMS_EMAIL
    
    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.set_debuglevel(1)
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                server.set_debuglevel(1)
                server.starttls()
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.send_message(msg)
        print("SUCCESS! Email accepted by SMTP server.")
    except Exception as e:
        print(f"FAILED! Error: {e}")

if __name__ == "__main__":
    _send()
