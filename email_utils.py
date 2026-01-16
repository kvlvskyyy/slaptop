from extensions import mail
from flask_mail import Message
from flask import current_app
from threading import Thread

def send_async_email(msg):
    with current_app.app_context():  # ensures Flask context is active
        try:
            mail.send(msg)
        except Exception as e:
            print("Mail sending error:", e)

def send_email(msg):
    Thread(target=send_async_email, args=(msg,)).start()
