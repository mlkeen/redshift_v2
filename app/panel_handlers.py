# app/panel_handlers.py

from flask import redirect, request
from app.models import Poll, Player, Panel, Interactable, ScannedBioSample, db
from app.forms import PollForm
from app.extensions import db
from sqlalchemy.orm.attributes import flag_modified 
from datetime import datetime
import random



def resolve_panel(code):
    if not code:
        return None
    return Panel.query.filter_by(code=code.upper()).first()

def resolve_player(code):
    if not code:
        return None
    return Player.query.filter_by(code=code.upper()).first()

def resolve_interactable(code):
    if not code:
        return None
    return Interactable.query.filter_by(code=code.upper()).first()



def handle_polling_display(player, panel, **kwargs):
    form = PollForm()
    polls = Poll.query.order_by(Poll.created_at.desc()).all()

    if request.method == "POST":
        form_type = request.form.get("form_type")

        # --- Handle Poll Creation ---
        if form_type == "create_poll":
            if form.validate_on_submit() and player and "poll.create" in (player.permissions or []):
                options = [opt.strip() for opt in form.options.data.split(',') if opt.strip()]
                new_poll = Poll(
                    question=form.question.data,
                    creator_id=player.id,
                    votes={opt: [] for opt in options}
                )
                db.session.add(new_poll)
                db.session.commit()
                return {"redirect": request.url}

        # --- Handle Voting ---
        elif form_type == "vote" and player:
            poll_id = request.form.get("poll_id")
            selected_option = request.form.get("selected_option")

            if poll_id and selected_option:
                poll = Poll.query.get(int(poll_id))
                if poll and poll.is_open and selected_option in poll.votes:
                    # Prevent duplicate votes
                    already_voted = any(player.id in voters for voters in poll.votes.values())
                    if not already_voted:
                        updated_votes = poll.votes.copy()
                        updated_votes[selected_option] = updated_votes.get(selected_option, []) + [player.id]
                        poll.votes = updated_votes

                        flag_modified(poll, "votes")

                        db.session.add(poll)                        
                        db.session.commit()
                        return {"redirect": request.url}

    return {
        "form": form,
        "polls": polls
    }



def handle_biolab_display(player, panel, **kwargs):
    # POST: Handle a new scan
    if request.method == "POST" and player:
        interactable_id = request.form.get("interactable_id")
        scan_type = request.form.get("scan_type")

        if interactable_id and scan_type:
            target = Interactable.query.get(int(interactable_id))

            if target and target.is_biological:
                if scan_type == "pathogen":
                    # Simulate pathogen scan
                    result = random.choice(["Clean", "Pathogen Detected"])
                    target.bioscan_result = result
                    target.last_scanned = datetime.utcnow()
                    db.session.commit()

                # Add to scanned biosamples if not already logged
                existing = ScannedBioSample.query.filter_by(
                    interactable_id=target.id,
                    panel_id=panel.id
                ).first()

                if not existing:
                    sample = ScannedBioSample(
                        interactable_id=target.id,
                        panel_id=panel.id,
                        timestamp=datetime.utcnow()
                    )
                    db.session.add(sample)
                    db.session.commit()

                return {"redirect": request.url}

    # For display: show recent scanned samples for this panel
    recent_samples = (
        ScannedBioSample.query
        .filter_by(panel_id=panel.id)
        .order_by(ScannedBioSample.timestamp.desc())
        .limit(10)
        .all()
    )

    # Also pull latest biological interactables with bioscan results
    biological = (
        Interactable.query
        .filter(Interactable.is_biological.is_(True))
        .order_by(Interactable.last_scanned.desc())
        .limit(10)
        .all()
    )

    print("Recent scanned bio samples:", recent_samples)
    for sample in recent_samples:
        print("→", sample.interactable_id, 
              sample.interactable.label if sample.interactable else "None")

    return {
        "recent_samples": recent_samples,
        "biological": biological,
    }


def handle_laser_comms_display(panel, player, **kwargs):
    messages = LaserMessage.query.filter_by(panel_id=panel.id).order_by(LaserMessage.sent_time.desc()).all()
    return {"messages": messages}




# More handlers can go here, like:
# def handle_inspect_display(...): ...


