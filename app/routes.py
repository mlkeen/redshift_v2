from flask import Blueprint, render_template, abort, session, redirect, url_for, request, flash, current_app
from flask_login import login_required
from app.models import Panel, Player, Interactable, SpaceObject, LaserMessage, MessageTarget, Control, ControlInvite, GameState, ScannedBioSample
from datetime import datetime, timedelta
from .forms import PlayerForm, PanelForm, InteractableForm, SpaceObjectForm, ControlInviteForm, ControlRegistrationForm
from app.email_utils import send_email
from . import db
import base64
import uuid
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
import os
from app.extensions import db
from datetime import datetime, timedelta
import secrets
import json
from app.panel_handlers import handle_polling_display, handle_biolab_display
from app.helpers import resolve_player, resolve_panel, resolve_interactable, build_menu_items, get_fictional_time, get_delay_to_target

# Move this to helper? 
def prune_inactive(panel):
    cutoff = datetime.utcnow() - timedelta(minutes=1)

    if panel.player_last_interaction and panel.player_last_interaction < cutoff:
        panel.current_player = None
        panel.player_last_interaction = None

    if panel.interactable_last_interaction and panel.interactable_last_interaction < cutoff:
        panel.current_interactable = None
        panel.interactable_last_interaction = None

    db.session.commit()




main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/scan')
def scan():
    return render_template('scan.html')

### CONTROL REGISTRATION
@main.route('/invite_control', methods=['GET', 'POST'])
@login_required
def invite_control():
    form = ControlInviteForm()
    if form.validate_on_submit():
        recipient_email = form.email.data
        token = secrets.token_urlsafe(16)  # or use a timed serializer for added security
        invite_link = url_for('main.register_control', token=token, _external=True)

        # Store token and email in DB or temporary store
        invite = ControlInvite(email=recipient_email, token=token)
        db.session.add(invite)
        db.session.commit()

        # Send email
        subject = "Redshift Control Registration Invitation"
        body = f"""
        Hello,

        You've been invited to register as a Control user for the upcoming Redshift megagame scheduled for 8/12/25.

        Click the link below to complete your registration:
        {invite_link}

        If you weren't expecting this email, you can ignore it.

        Regards,  
        Redshift Admin Team
        """
        send_email(recipient_email, subject, body)

        flash("Invitation email sent.", "success")
        return redirect(url_for('main.control_dashboard'))  # Or wherever makes sense
    return render_template('invite_control.html', form=form)


@main.route('/register_control/<token>', methods=['GET', 'POST'])
def register_control(token):
    invite = ControlInvite.query.filter_by(token=token).first()

    if not invite:
        flash("Invalid or expired invitation link.", "danger")
        return redirect(url_for('main.index'))

    form = ControlRegistrationForm()

    if request.method == 'GET':
        form.email_address.data = invite.email  # Pre-fill from invite

    if form.validate_on_submit():
        # Ensure unique username
        if Control.query.filter_by(username=form.username.data).first():
            flash("Username already taken.", "danger")
            return render_template('register_control.html', form=form)

        # Create Control user
        new_control = Control(
            username=form.username.data,
            password_hash=generate_password_hash(form.password.data),
            name=form.name.data,
            pronouns=form.pronouns.data,
            email_address=form.email_address.data
        )
        db.session.add(new_control)
        db.session.delete(invite)  # Invalidate the invite
        db.session.commit()

        # After successful Control registration
        send_email(
            recipient=form.email_address.data,
            subject="Redshift Control Account Confirmed",
            body=f"""Hello {form.name.data},

        Your Control account for the Redshift megagame (scheduled 8/12/25) has been successfully registered.

        You can now log in and begin preparing for your role.

        Welcome aboard!

        — Redshift Admin Team"""
        )

        flash("Control account created successfully. A confirmation email has been sent.", "success")
        return redirect(url_for('auth.login'))

    return render_template('register_control.html', form=form)



### CONTROL INTERFACE
@main.route('/control_dashboard')
@login_required
def control_dashboard():
    game_state = GameState.query.first()
    messages = TightbeamMessage.query.order_by(TightbeamMessage.sent_time.desc()).all()
    time_remaining = game_state.time_remaining() if game_state else None
    return render_template('control/dashboard.html', messages=messages, game_state=game_state, time_remaining=time_remaining)


@main.route('/control/start_phase', methods=['GET', 'POST'])
def start_phase():
    if request.method == 'POST':
        phase_name = request.form.get('phase_name', 'Unnamed Phase')
        duration = int(request.form.get('duration', 0))
        in_game_time = request.form.get('in_game_time', '')

        state = GameState.query.first()
        if not state:
            state = GameState()

        state.phase_name = phase_name
        state.phase_duration_minutes = duration
        state.phase_start_time = datetime.utcnow()

        db.session.add(state)
        db.session.commit()
        flash(f"Phase '{phase_name}' started for {duration} minutes.", 'success')
        return redirect(url_for('main.control_dashboard'))

    return render_template('control/start_phase.html')




@main.route('/control/messages')
@login_required
def view_messages():
    from app.models import TightbeamMessage
    messages = TightbeamMessage.query.order_by(TightbeamMessage.sent_time.desc()).all()
    return render_template('control_messages.html', messages=messages)

@main.route('/control/respond/<int:message_id>', methods=["POST"])
@login_required
def respond_to_message(message_id):
    from app.models import TightbeamMessage
    message = TightbeamMessage.query.get_or_404(message_id)
    file = request.files.get("reply_file")

    if not file:
        flash("No file uploaded.")
        return redirect(url_for("main.control_dashboard"))

    filename = f"response_{message.id}_{int(datetime.utcnow().timestamp())}.webm"
    save_path = os.path.join("app", "static", "messages", filename)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    file.save(save_path)

    message.response_path = os.path.join("messages", filename)
    message.response_time = datetime.utcnow()
    db.session.commit()

    flash("Reply sent.")
    return redirect(url_for("main.control_dashboard"))


######
@main.route('/control/edit/<string:object_type>')
@login_required
def control_edit_list(object_type):
    obj_map = {
        'players': Player,
        'panels': Panel,
        'interactables': Interactable,
        'spaceobjects': SpaceObject
    }
    model = obj_map.get(object_type)
    if not model:
        flash('Invalid object type.')
        return redirect(url_for('main.control_dashboard'))

    items = model.query.all()
    return render_template('control_edit_list.html', object_type=object_type, items=items)


@main.route('/control/edit/<string:object_type>/new', methods=['GET', 'POST'])
@login_required
def control_add_object(object_type):
    form_map = {
        'players': PlayerForm,
        'panels': PanelForm,
        'interactables': InteractableForm,
        'spaceobjects': SpaceObjectForm
    }
    FormClass = form_map.get(object_type)
    if not FormClass:
        flash('Invalid form type.')
        return redirect(url_for('main.control_dashboard'))

    form = FormClass()
    if form.validate_on_submit():
        new_obj = FormClass.model_class()  # set on form class
        form.populate_obj(new_obj)
        db.session.add(new_obj)
        db.session.commit()
        flash(f"{object_type.capitalize()} added.")
        return redirect(url_for('main.control_edit_list', object_type=object_type))

    return render_template('control_edit_form.html', form=form, object_type=object_type)


@main.route('/control/edit/<string:object_type>/<int:object_id>', methods=['GET', 'POST'])
@login_required
def control_edit_object(object_type, object_id):
    model_map = {
        'players': Player,
        'panels': Panel,
        'interactables': Interactable,
        'spaceobjects': SpaceObject
    }
    form_map = {
        'players': PlayerForm,
        'panels': PanelForm,
        'interactables': InteractableForm,
        'spaceobjects': SpaceObjectForm
    }

    model = model_map.get(object_type)
    FormClass = form_map.get(object_type)
    if not model or not FormClass:
        flash('Invalid object type.')
        return redirect(url_for('main.control_dashboard'))

    obj = model.query.get_or_404(object_id)
    form = FormClass(obj=obj)
    if form.validate_on_submit():
        form.populate_obj(obj)
        db.session.commit()
        flash(f"{object_type.capitalize()} updated.")
        return redirect(url_for('main.control_edit_list', object_type=object_type))

    return render_template('control_edit_form.html', form=form, object_type=object_type)


from app.forms import PollForm
from app.models import Poll

### PANELS
@main.route('/panel/<string:panel_code>/', methods=['GET', 'POST'], defaults={'display': None, 'player_code': None, 'interactable_code': None})
@main.route('/panel/<string:panel_code>/display/<string:display>/', methods=['GET', 'POST'], defaults={'player_code': None, 'interactable_code': None})
@main.route('/panel/<string:panel_code>/display/<string:display>/player/<string:player_code>/', methods=['GET', 'POST'], defaults={'interactable_code': None})
@main.route('/panel/<string:panel_code>/display/<string:display>/player/<string:player_code>/interact/<string:interactable_code>/', methods=['GET', 'POST'])
def panel_view(panel_code, display, player_code, interactable_code):
    panel = resolve_panel(panel_code)
    if not panel:
        abort(404)
    prune_inactive(panel)


    display = display or panel.primary_display
    player = resolve_player(player_code or request.args.get("player_code"))
    interactable = resolve_interactable(interactable_code)

    if player:
        panel.current_player = player.id
        panel.player_last_interaction = datetime.utcnow()

    if interactable:
        panel.current_interactable = interactable.id
        panel.interactable_last_interaction = datetime.utcnow()

    DISPLAY_HANDLERS = {
        "polling": handle_polling_display,
        "biolab": handle_biolab_display,
        # Add more display handlers here as needed
    }

    handler = DISPLAY_HANDLERS.get(display.lower())
    extra_context = {}

    ### Debug
    print("Display:", display)
    print("Handler:", handler)
    ### End debug
    if handler:
        handler_result = handler(player=player, panel=panel, display=display, interactable=interactable)
        if isinstance(handler_result, dict):
            if 'redirect' in handler_result:
                return redirect(handler_result['redirect'])
            extra_context.update(handler_result)

    if display.lower() == "laser_comms":
        extra_context["message_targets"] = MessageTarget.query.all()

    #Debugging 
    print("Request method:", request.method)
    #End debugging

    #Bioscan, but should this be a helper function?
    if interactable and interactable.is_biological:
        print(f"Biological interactable scanned: {interactable.label} (ID: {interactable.id})")
        print(f"Panel display: {display}")
        
        if display == "Biolab":
            existing = ScannedBioSample.query.filter_by(
                panel_id=panel.id,
                interactable_id=interactable.id
            ).first()
            
            if not existing:
                print("No existing scan found — creating new.")
                db.session.add(ScannedBioSample(panel_id=panel.id, interactable_id=interactable.id))
                db.session.commit()
            else:
                print("Sample already scanned.")

    if request.args.get("logout") == "1":
        panel.current_player = None
        panel.player_last_interaction = None
        panel.current_interactable = None
        panel.interactable_last_interaction = None
        db.session.commit()
        return redirect(url_for("main.panel_view", panel_code=panel.code))


#############3
    elif request.method == "POST" and request.form.get("form_type") == "send_laser":
        target_name = request.form.get("target_name")
        target = MessageTarget.query.filter_by(name=target_name).first()

        if not target:
            flash("Invalid target selected.", "error")
            return redirect(request.path)

        delay_seconds = get_delay_to_target(target)

        audio_base64 = request.form.get("audio_data")
        audio_blob = base64.b64decode(audio_base64)

        # Save audio file
        filename = f"{uuid.uuid4().hex}.webm"
        from flask import current_app
        filepath = os.path.join(current_app.config['AUDIO_UPLOAD_FOLDER'], filename)
        with open(filepath, "wb") as f:
            f.write(audio_blob)

        new_message = LaserMessage(
            panel_id=panel.id,
            sender_player_id=player.id if player else None,
            message_target_id=target.id,
            audio_filename=filename,
            delivery_time=datetime.utcnow() + timedelta(seconds=delay_seconds)
        )

        db.session.add(new_message)
        db.session.commit()
        flash(f"Message sent to {target.name}. ETA: {round(delay_seconds / 60, 2)} minutes. ERT: {round(2*delay_seconds / 60, 2)} minutes.", "success")
        return redirect(request.path)
    

###################

    return render_template(
        "panel_base.html",
        panel=panel,
        player=player,
        interactable=interactable,
        fictional_time=get_fictional_time(),
        display=display,
        menu_items=build_menu_items(panel, player),
        timedelta=timedelta,
        now=datetime.utcnow(),
        **extra_context
    )

            


