import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///redshift.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🔧 Email settings for Fastmail
    MAIL_SERVER = 'smtp.fastmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')  # e.g., yourname@fastmail.com
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')  # your Fastmail app password
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER', 'redshift_game@fastmail.com')

    AUDIO_UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "audio")

