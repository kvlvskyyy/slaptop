from flask_mail import Message
from extensions import mail
from threading import Thread
from flask import copy_current_request_context

def send_email(msg):
    @copy_current_request_context
    def send():
        try:
            mail.send(msg)
        except Exception as e:
            print("Mail sending error:", e)

    Thread(target=send).start()
