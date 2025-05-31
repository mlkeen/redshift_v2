from app.extensions import db 
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db

class Control(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Panel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    system = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    primary_display = db.Column(db.String(100), nullable=False)  # e.g., 'panels/example_display.html'
    menu_items = db.Column(db.JSON, nullable=False, default=[])

    def set_default_menu(self):
        self.menu_items = [
            {"key": "1", "label": "Status"},
            {"key": "2", "label": "Polling"},
            {"key": "3", "label": "Medical Logs"},
            {"key": "4", "label": "Med Bay"},
            {"key": "5", "label": "Engineering"},
            {"key": "6", "label": "Hydroponics"},
            {"key": "7", "label": "Biolab"},
            {"key": "8", "label": "Ghesa Array"},
            {"key": "9", "label": "Redacted Lab"},
            {"key": "A", "label": "Laser Comms"},
            {"key": "B", "label": "Crew Roster"},
            {"key": "C", "label": "Overlay"}

        ]

class QRObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.String(20))  # 'player', 'item', 'tool'
    object_id = db.Column(db.String(12))    # ID code
    qr_code_path = db.Column(db.String(100))

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False)
    name = db.Column(db.String(80), nullable=False)

class Interactable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False)  # e.g., "G12-HG3"
    label = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., "tool", "item", "tag"
    data = db.Column(db.Text)  # Optional JSON or content payload
    requires_player = db.Column(db.Boolean, default=False)  # Whether it checks who accessed the panel

class SpaceObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # e.g., "asteroid", "ship", "probe", "unknown"
    name = db.Column(db.String(100), nullable=False)
    mass = db.Column(db.Float, nullable=True)  # in kg, log base 10
    radius = db.Column(db.Float, nullable=True)  # in km

    # 3D position in km
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    z = db.Column(db.Float, nullable=False)

    # Velocity in km/s
    vx = db.Column(db.Float, nullable=True)
    vy = db.Column(db.Float, nullable=True)
    vz = db.Column(db.Float, nullable=True)

    # Acceleration in m/s^2
    ax = db.Column(db.Float, nullable=True)
    ay = db.Column(db.Float, nullable=True)
    az = db.Column(db.Float, nullable=True)

    transponder_signal = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        return {
            "type": self.type,
            "name": self.name,
            "mass": self.mass,
            "radius": self.radius,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "vx": self.vx,
            "vy": self.vy,
            "vz": self.vz,
            "ax": self.ax,
            "ay": self.ay,
            "az": self.az,
            "transponder_signal": self.transponder_signal
        }

class GameState(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    game_name = db.Column(db.String(100), nullable=False)
    control_code = db.Column(db.String(50), nullable=False)

    # UTC time the game actually started
    start_time = db.Column(db.DateTime, nullable=False)

    # Duration of each phase in seconds (e.g., 300 for 5 minutes)
    phase_duration = db.Column(db.Integer, nullable=False)

    # Current in-universe time (ISO or custom format)
    universe_time = db.Column(db.String(100), nullable=True)

    # Optional: track current phase number
    current_phase = db.Column(db.Integer, default=0)

class CommTarget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)  # e.g., "Earth Relay"
    delay_seconds = db.Column(db.Integer, nullable=False)  # Total round-trip delay (sec)


class TightbeamMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_code = db.Column(db.String(12), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('comm_target.id'), nullable=False)
    target = db.relationship("CommTarget")

    file_path = db.Column(db.String(200), nullable=False)
    sent_time = db.Column(db.DateTime, nullable=False)

    # Optional response
    response_path = db.Column(db.String(200), nullable=True)
    response_time = db.Column(db.DateTime, nullable=True)

