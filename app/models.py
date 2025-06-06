from app.extensions import db 
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy import Column, Integer, JSON
from sqlalchemy.types import JSON

# Nest Mutable Dict for vote tracking
class NestedMutableDict(MutableDict):
    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, NestedMutableDict):
            if isinstance(value, dict):
                return NestedMutableDict({
                    k: MutableList(v) if isinstance(v, list) else v
                    for k, v in value.items()
                })
            return MutableDict.coerce(key, value)
        else:
            return value




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
    current_player = db.Column(db.String, nullable=True)
    player_last_interaction = db.Column(db.DateTime, nullable=True)
    current_interactable = db.Column(db.String, nullable=True)
    interactable_last_interaction = db.Column(db.DateTime, nullable=True)


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
    permissions = db.Column(db.JSON, default=list)  # list of ability/item/etc keys

    resolve = db.Column(db.Integer)
    skill = db.Column(db.Integer)
    knowledge = db.Column(db.Integer)
    luck = db.Column(db.Integer)

    specialization = db.Column(db.String(100))
    mini_access = db.Column(db.JSON)  # list of restricted view or mini-panels
    hidden_objective = db.Column(db.String(500))  # secret goal
    description = db.Column(db.Text)  # longer text about who they are
    condition = db.Column(db.JSON)    # list of condition codes

    def has_permission(self, key):
        return key in (self.permissions or [])


class Interactable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False)  # e.g., "G12-HG3"
    label = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # e.g., "tool", "item", "tag"
    data = db.Column(db.Text)  # Optional JSON or content payload
    requires_player = db.Column(db.Boolean, default=False)  # Whether it checks who accessed the panel
    is_biological = db.Column(db.Boolean, default=False)
    bioscan_result = db.Column(db.String)  # Or JSON/Text if complex
    last_scanned = db.Column(db.DateTime)

class ScannedBioSample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('panel.id'), nullable=False)
    interactable_id = db.Column(db.Integer, db.ForeignKey('interactable.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    interactable = db.relationship('Interactable')


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
    thermal_fail_time = db.Column(db.DateTime, nullable=True)
    magnetic_fail_time = db.Column(db.DateTime, nullable=True)

    def time_remaining(self):
        if not self.phase_start_time or not self.phase_duration_minutes:
            return None

        end_time = self.phase_start_time + timedelta(minutes=self.phase_duration_minutes)
        remaining = end_time - datetime.utcnow()
        return max(remaining, timedelta(0))  # Avoid negative values

class LaserMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('panel.id'))
    panel = db.relationship('Panel', backref='laser_messages')
    sender_player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player = db.relationship('Player', backref='laser_messages')
    message_target_id = db.Column(db.Integer, db.ForeignKey('message_target.id'))
    audio_filename = db.Column(db.String(256))
    sent_time = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_time = db.Column(db.DateTime)  # sent_time + delay
    response_text = db.Column(db.Text, nullable=True)
    response_time = db.Column(db.DateTime, nullable=True)
    target = db.relationship("MessageTarget", backref="laser_messages")

class MessageTarget(db.Model):
    __tablename__ = "message_target"  # Add this line
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    distance_in_light_minutes = db.Column(db.Float, nullable=True)

class Poll(db.Model):
    __tablename__ = 'polls'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    creator_id = db.Column(db.Integer, db.ForeignKey('player.id'), nullable=False)
    creator = db.relationship("Player", backref="polls_created")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_open = db.Column(db.Boolean, default=True)
    votes = db.Column(NestedMutableDict.as_mutable(JSON), default=dict)

    def vote(self, option, voter_id):
        """Register a vote from a player or NPC ID"""
        if not self.votes:
            self.votes = {}
        if option not in self.votes:
            self.votes[option] = []
        if voter_id not in self.all_voters():
            self.votes[option].append(voter_id)

    def all_voters(self):
        """Return a flat list of all voter IDs"""
        return [voter for voters in self.votes.values() for voter in voters]

    @property
    def is_open(self):
        return datetime.utcnow() - self.created_at < timedelta(minutes=5)


class PowerSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default='Offline')  # Online, Offline, Critical, etc.
    current_output = db.Column(db.Float, default=0.0)
    max_output = db.Column(db.Float, default=0.0)
    cooldown = db.Column(db.Boolean, default=False)
    source_type = db.Column(db.String, nullable=False)  # 'fusion', 'solar', etc.

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "status": self.status,
            "current_output": self.current_output,
            "max_output": self.max_output,
            "cooldown": self.cooldown,
            "source_type": self.source_type,
        }

class PowerConsumer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    priority = db.Column(db.String, default='Medium')  # High, Medium, Low
    power_draw = db.Column(db.Float, default=0.0)
    is_disabled = db.Column(db.Boolean, default=False)
    consumer_type = db.Column(db.String, nullable=True)  # e.g., 'life_support'

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "priority": self.priority,
            "power_draw": self.power_draw,
            "is_disabled": self.is_disabled,
            "consumer_type": self.consumer_type,
        }