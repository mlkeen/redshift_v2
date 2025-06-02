from app.extensions import db 
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class Control(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100))
    pronouns = db.Column(db.String(50))
    email_address = db.Column(db.String(120))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class ControlInvite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)




class Panel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    system = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    primary_display = db.Column(db.String(100), nullable=False)  # e.g., 'panels/example_display.html'
    menu_items = db.Column(db.JSON)

class QRObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.String(20))  # 'player', 'item', 'tool'
    object_id = db.Column(db.String(12))    # ID code
    qr_code_path = db.Column(db.String(100))

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False)

    honorific = db.Column(db.String(20))
    first_name = db.Column(db.String(50))
    name = db.Column(db.String(100))  # surname
    role = db.Column(db.String(100))
    assignment = db.Column(db.String(100))
    faction = db.Column(db.String(100))

    system_access = db.Column(db.JSON)  # list of system codes they can use
    player_menu = db.Column(db.JSON)    # list of menu keys
    special_options = db.Column(db.JSON)  # list of ability/item/etc keys

    resolve = db.Column(db.Integer)
    skill = db.Column(db.Integer)
    knowledge = db.Column(db.Integer)
    luck = db.Column(db.Integer)

    specialization = db.Column(db.String(100))
    mini_access = db.Column(db.JSON)  # list of restricted view or mini-panels
    hidden_objective = db.Column(db.String(500))  # secret goal
    description = db.Column(db.Text)  # longer text about who they are
    condition = db.Column(db.JSON)    # list of condition codes


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
    name = db.Column(db.String(64), unique=True, default="default")
    phase_name = db.Column(db.String(64), default="briefing")
    phase_start_time = db.Column(db.DateTime, nullable=True)
    phase_duration_minutes = db.Column(db.Integer, default=40)

    def time_remaining(self):
        if not self.phase_start_time or not self.phase_duration_minutes:
            return None

        end_time = self.phase_start_time + timedelta(minutes=self.phase_duration_minutes)
        remaining = end_time - datetime.utcnow()
        return max(remaining, timedelta(0))  # Avoid negative values

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

