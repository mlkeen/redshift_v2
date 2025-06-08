
from datetime import datetime, timedelta

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.mutable import MutableDict, MutableList
from sqlalchemy.types import JSON

from . import db


# === Utility Classes ===

class NestedMutableDict(MutableDict):
    """Allows nested mutable dicts with mutable lists for JSON voting."""
    @classmethod
    def coerce(cls, key, value):
        if not isinstance(value, NestedMutableDict):
            if isinstance(value, dict):
                return NestedMutableDict({
                    k: MutableList(v) if isinstance(v, list) else v
                    for k, v in value.items()
                })
            return MutableDict.coerce(key, value)
        return value


# === User and Auth Models ===

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


# === Core Game Models ===

class Panel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)
    system = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    primary_display = db.Column(db.String(100), nullable=False)
    menu_items = db.Column(JSON)
    current_player = db.Column(db.String)
    player_last_interaction = db.Column(db.DateTime)
    current_interactable = db.Column(db.String)
    interactable_last_interaction = db.Column(db.DateTime)


class QRObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    object_type = db.Column(db.String(20))  # 'player', 'item', 'tool'
    object_id = db.Column(db.String(12))
    qr_code_path = db.Column(db.String(100))


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_code = db.Column(db.String(12), unique=True, nullable=False)

    honorific = db.Column(db.String(20))
    first_name = db.Column(db.String(50))
    surname = db.Column(db.String(100))
    role = db.Column(db.String(100))
    assignment = db.Column(db.String(100))
    faction = db.Column(db.String(100))

    system_access = db.Column(JSON)
    player_menu = db.Column(JSON)
    permissions = db.Column(JSON, default=list)

    resolve = db.Column(db.Integer)
    skill = db.Column(db.Integer)
    knowledge = db.Column(db.Integer)
    luck = db.Column(db.Integer)

    specialization = db.Column(db.String(100))
    mini_access = db.Column(JSON)
    hidden_objective = db.Column(db.String(500))
    description = db.Column(db.Text)
    conditions = db.Column(JSON)

    def has_permission(self, key):
        return key in (self.permissions or [])


class Condition(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    label = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    effect = db.Column(db.String(200), nullable=False)


class Interactable(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(12), unique=True, nullable=False)
    label = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    data = db.Column(db.Text)
    requires_player = db.Column(db.Boolean, default=False)
    is_biological = db.Column(db.Boolean, default=False)
    bioscan_result = db.Column(db.String)
    last_scanned = db.Column(db.DateTime)


class ScannedBioSample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('panel.id'), nullable=False)
    interactable_id = db.Column(db.Integer, db.ForeignKey('interactable.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    interactable = db.relationship('Interactable')


# === Space Object Tracking ===

class SpaceObject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    mass = db.Column(db.Float)
    radius = db.Column(db.Float)
    x = db.Column(db.Float, nullable=False)
    y = db.Column(db.Float, nullable=False)
    z = db.Column(db.Float, nullable=False)
    vx = db.Column(db.Float)
    vy = db.Column(db.Float)
    vz = db.Column(db.Float)
    ax = db.Column(db.Float)
    ay = db.Column(db.Float)
    az = db.Column(db.Float)
    transponder_signal = db.Column(db.String(100))

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


# === Game State ===

class GameState(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, default="default")
    phase_name = db.Column(db.String(64), default="briefing")
    phase_start_time = db.Column(db.DateTime)
    phase_duration_minutes = db.Column(db.Integer, default=40)
    thermal_fail_time = db.Column(db.DateTime)
    magnetic_fail_time = db.Column(db.DateTime)

    def time_remaining(self):
        if not self.phase_start_time or not self.phase_duration_minutes:
            return None
        end_time = self.phase_start_time + timedelta(minutes=self.phase_duration_minutes)
        return max(end_time - datetime.utcnow(), timedelta(0))


# === Messaging ===

class MessageTarget(db.Model):
    __tablename__ = "message_target"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    distance_in_light_minutes = db.Column(db.Float)


class LaserMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    panel_id = db.Column(db.Integer, db.ForeignKey('panel.id'))
    panel = db.relationship('Panel', backref='laser_messages')
    sender_player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player = db.relationship('Player', backref='laser_messages')
    message_target_id = db.Column(db.Integer, db.ForeignKey('message_target.id'))
    audio_filename = db.Column(db.String(256))
    sent_time = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_time = db.Column(db.DateTime)
    response_text = db.Column(db.Text)
    response_time = db.Column(db.DateTime)
    target = db.relationship("MessageTarget", backref="laser_messages")


# === Polls ===

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
        if not self.votes:
            self.votes = {}
        if option not in self.votes:
            self.votes[option] = []
        if voter_id not in self.all_voters():
            self.votes[option].append(voter_id)

    def all_voters(self):
        return [voter for voters in self.votes.values() for voter in voters]

    @property
    def is_active(self):
        return datetime.utcnow() - self.created_at < timedelta(minutes=5)


# === Power System ===

class PowerSource(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    status = db.Column(db.String, default='Offline')
    current_output = db.Column(db.Float, default=0.0)
    max_output = db.Column(db.Float, default=0.0)
    cooldown = db.Column(db.Boolean, default=False)
    source_type = db.Column(db.String, nullable=False)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class PowerConsumer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    priority = db.Column(db.String, default='Medium')
    power_draw = db.Column(db.Float, default=0.0)
    is_disabled = db.Column(db.Boolean, default=False)
    consumer_type = db.Column(db.String)

    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
