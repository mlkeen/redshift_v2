# app/forms.py

from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SubmitField, SelectField, PasswordField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Regexp
from .models import Player, Panel, Interactable, SpaceObject

class ControlInviteForm(FlaskForm):
    email = StringField('Recipient Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Send Invitation')

class ControlRegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=30)])
    password = PasswordField("Password", validators=[
        DataRequired(),
        Length(min=8, message="Password must be at least 8 characters long."),
        Regexp(
            regex="^(?=.*[a-zA-Z])(?=.*[0-9])",
            message="Password must include both letters and numbers."
        )
    ])
    
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo('password', message="Passwords must match.")
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
