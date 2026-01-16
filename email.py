from app import app, mail


from threading import Thread

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print("Mail sending error:", e)

def send_email(msg):
    Thread(target=send_async_email, args=(app, msg)).start()
