from flask_mail import Message
from app.extensions import mail

def send_email(recipient, subject, body):
    msg = Message(subject=subject, recipients=[recipient], body=body)
    mail.send(msg)
