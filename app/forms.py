
# app/forms.py

from flask_wtf import FlaskForm
from wtforms import (
    StringField, FloatField, SubmitField, SelectField,
    PasswordField, TextAreaField
)
from wtforms.validators import (
    DataRequired, Email, EqualTo, Length, Regexp
)

from .models import Player, Panel, Interactable, SpaceObject


# === Control Account Forms ===

class ControlInviteForm(FlaskForm):
    email = StringField('Recipient Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Invitation')


class ControlRegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=30)])
    password = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters."),
        Regexp(r"^(?=.*[a-zA-Z])(?=.*[0-9])", message="Include both letters and numbers.")
    ])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(), EqualTo('password', message="Passwords must match.")
    ])
    email_address = StringField("Email Address", validators=[DataRequired(), Email()])
    name = StringField("Full Name", validators=[DataRequired()])
    pronouns = SelectField("Pronouns", choices=[
        ('they/them', 'They/Them'),
        ('she/her', 'She/Her'),
        ('he/him', 'He/Him'),
        ('custom', 'Custom / Other')
    ], validators=[DataRequired()])
    submit = SubmitField("Register")


# === Admin Edit Forms ===

class PlayerForm(FlaskForm):
    player_code = StringField('Code', validators=[DataRequired()])
    first_name = StringField('First Name')
    surname = StringField('Surname')
    role = StringField('Role')
    assignment = StringField('Assignment')
    faction = StringField('Faction')
    description = TextAreaField('Description')
    submit = SubmitField('Save')
    model_class = Player


class PanelForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])
    system = StringField('System')
    location = StringField('Location')
    primary_display = StringField('Primary Display Template')
    submit = SubmitField('Save')
    model_class = Panel


class InteractableForm(FlaskForm):
    code = StringField('Code', validators=[DataRequired()])
    label = StringField('Label')
    type = StringField('Type')
    is_biological = SelectField('Biological?', choices=[('true', 'Yes'), ('false', 'No')])
    submit = SubmitField('Save')
    model_class = Interactable


class SpaceObjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired()])
    mass = FloatField('Mass')
    radius = FloatField('Radius')
    x = FloatField('X', validators=[DataRequired()])
    y = FloatField('Y', validators=[DataRequired()])
    z = FloatField('Z', validators=[DataRequired()])
    vx = FloatField('VX')
    vy = FloatField('VY')
    vz = FloatField('VZ')
    ax = FloatField('AX')
    ay = FloatField('AY')
    az = FloatField('AZ')
    transponder = StringField('Transponder Signal')
    submit = SubmitField('Save')
    model_class = SpaceObject


# === Game UI Forms ===

class PollForm(FlaskForm):
    question = StringField('Question', validators=[DataRequired()])
    options = StringField('Options (comma-separated)', validators=[DataRequired()])
    submit = SubmitField("Create Poll")
