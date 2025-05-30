from flask import Blueprint, render_template, abort, session, redirect, url_for, request, flash, current_app
from flask_login import login_required
from app.models import Panel, Player, Interactable, SpaceObject, TightbeamMessage, CommTarget
from datetime import datetime, timedelta
from .forms import PlayerForm, PanelForm, InteractableForm, SpaceObjectForm
from . import db
import base64
import uuid
from werkzeug.utils import secure_filename
import os


# app/routes.py





main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/scan')
def scan():
    return render_template('scan.html')


### CONTROL INTERFACE

@main.route('/control')
@login_required
def control_dashboard():
    from app.models import GameState, TightbeamMessage, CommTarget
    messages = TightbeamMessage.query.order_by(TightbeamMessage.sent_time.desc()).all()
    game_state = GameState.query.first()
    return render_template("control_dashboard.html", messages=messages, game_state=game_state)


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




### PANELS

@main.route('/panel/<code>')
def show_panel(code):
    panel = Panel.query.filter_by(code=code.upper()).first()
    if not panel:
        abort(404)

    session_key = f"access_{code.upper()}"
    timestamp_key = f"access_time_{code.upper()}"
    access_name = session.get(session_key)
    access_time_str = session.get(timestamp_key)

    if access_name and access_time_str:
        access_time = datetime.fromisoformat(access_time_str)
        if datetime.utcnow() - access_time > timedelta(seconds=60):
            # Expired — clear session
            session.pop(session_key, None)
            session.pop(timestamp_key, None)
            access_name = None

    return render_template('panel.html', panel=panel, access_name=access_name)


@main.route('/access/<player_code>/<panel_code>', methods=["POST"])
def grant_access(player_code, panel_code):
    player = Player.query.filter_by(code=player_code.upper()).first()
    panel = Panel.query.filter_by(code=panel_code.upper()).first()

    if not player or not panel:
        abort(404)

    session[f"access_{panel_code.upper()}"] = player.name
    session[f"access_time_{panel_code.upper()}"] = datetime.utcnow().isoformat()
    return ('', 204)

from app.models import Interactable

@main.route('/use/<interact_code>/<panel_code>', methods=["POST"])
def use_object(interact_code, panel_code):
    interact = Interactable.query.filter_by(code=interact_code.upper()).first()
    panel = Panel.query.filter_by(code=panel_code.upper()).first()

    if not interact or not panel:
        abort(404)

    access_name = session.get(f"access_{panel_code.upper()}") if interact.requires_player else None

    # Sample effect: update panel content
    effect = f"Used {interact.label}"
    if access_name:
        effect += f" (by {access_name})"
    
    panel.content = f"<p>{effect}</p>\n" + panel.content
    panel.last_updated = datetime.utcnow()
    db.session.commit()

    return ('', 204)


@main.route('/overlay/<panel_code>')
def overlay(panel_code):
    from app.models import SpaceObject, Panel
    panel = Panel.query.filter_by(code=panel_code.upper()).first_or_404()
    objects = SpaceObject.query.all()
    obj_data = [obj.to_dict() for obj in objects]  # ✅ convert to dicts
    return render_template('overlay.html', panel=panel, objects=obj_data)


@main.route('/send_message/<player_code>', methods=['GET', 'POST'])
def send_message(player_code):
    import base64, os
    from datetime import datetime
    from app.models import Player, CommTarget, TightbeamMessage

    player = Player.query.filter_by(code=player_code.upper()).first_or_404()
    targets = CommTarget.query.all()

    if request.method == 'POST':
        target_id = request.form.get('target_id')
        audio_data_base64 = request.form.get('audio_data')

        if not target_id or not audio_data_base64:
            flash('Missing target or audio data.', 'danger')
            return redirect(request.url)

        # Decode and save audio file
        audio_bytes = base64.b64decode(audio_data_base64)
        filename = f"{player.code}_{datetime.utcnow().isoformat().replace(':', '-')}.webm"
        save_dir = os.path.join(current_app.root_path, 'static', 'audio_messages')
        os.makedirs(save_dir, exist_ok=True)
        filepath = os.path.join(save_dir, filename)

        # Decode and save the file
        try:
            audio_bytes = base64.b64decode(audio_data_base64)
            with open(filepath, 'wb') as f:
                f.write(audio_bytes)
        except Exception as e:
            flash(f"Error saving file: {str(e)}", "danger")
            return redirect(request.url)

        # Create DB record
        message = TightbeamMessage(
            player_code=player.code,
            target_id=target_id,
            file_path=filename,
            sent_time=datetime.utcnow()
        )
        db.session.add(message)
        db.session.commit()

        flash("Message sent successfully!", "success")
        return redirect(url_for('main.send_message', player_code=player_code))

    return render_template('send_message.html', player=player, targets=targets)

