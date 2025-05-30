# app/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField
from wtforms.validators import DataRequired
from .models import Player, Panel, Interactable, SpaceObject

class PlayerForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    code = StringField('Code', validators=[DataRequired()])
    submit = SubmitField('Save')
    model_class = Player

class PanelForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])
    label = StringField('Label')
    content = StringField('Content')
    submit = SubmitField('Save')
    model_class = Panel

class InteractableForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])
    name = StringField('Name')
    submit = SubmitField('Save')
    model_class = Interactable

class SpaceObjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired()])
    mass = FloatField('Mass')
    radius = FloatField('Radius')
    x = FloatField('X')
    y = FloatField('Y')
    z = FloatField('Z')
    vx = FloatField('VX')
    vy = FloatField('VY')
    vz = FloatField('VZ')
    transponder = StringField('Transponder')
    submit = SubmitField('Save')
    model_class = SpaceObject
