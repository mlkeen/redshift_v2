
# app/panel_handlers.py

from flask import redirect, request
from datetime import datetime
import random

from app.models import (
    Poll, Player, Panel, Interactable, ScannedBioSample,
    LaserMessage, db
)
from app.forms import PollForm
from sqlalchemy.orm.attributes import flag_modified


# === DISPLAY HANDLERS ===

def handle_polling_display(player, panel, **kwargs):
    """
    Handle creation and voting on polls.
    Returns form and poll context or redirects on submit.
    """
    form = PollForm()
    polls = Poll.query.order_by(Poll.created_at.desc()).all()

    if request.method == "POST":
        form_type = request.form.get("form_type")

        # Create new poll
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

        # Submit a vote
        elif form_type == "vote" and player:
            poll_id = request.form.get("poll_id")
            selected_option = request.form.get("selected_option")

            if poll_id and selected_option:
                poll = Poll.query.get(int(poll_id))
                if poll and poll.is_open and selected_option in poll.votes:
                    if not any(player.id in voters for voters in poll.votes.values()):
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
    """
    Handle pathogen scans and display recent biosamples.
    """
    if request.method == "POST" and player:
        interactable_id = request.form.get("interactable_id")
        scan_type = request.form.get("scan_type")

        if interactable_id and scan_type:
            target = Interactable.query.get(int(interactable_id))

            if target and target.is_biological:
                if scan_type == "pathogen":
                    result = random.choice(["Clean", "Pathogen Detected"])
                    target.bioscan_result = result
                    target.last_scanned = datetime.utcnow()
                    db.session.commit()

                existing = ScannedBioSample.query.filter_by(
                    interactable_id=target.id,
                    panel_id=panel.id
                ).first()

                if not existing:
                    db.session.add(ScannedBioSample(
                        interactable_id=target.id,
                        panel_id=panel.id,
                        timestamp=datetime.utcnow()
                    ))
                    db.session.commit()

                return {"redirect": request.url}

    recent_samples = (
        ScannedBioSample.query
        .filter_by(panel_id=panel.id)
        .order_by(ScannedBioSample.timestamp.desc())
        .limit(10)
        .all()
    )

    biological = (
        Interactable.query
        .filter(Interactable.is_biological.is_(True))
        .order_by(Interactable.last_scanned.desc())
        .limit(10)
        .all()
    )

    return {
        "recent_samples": recent_samples,
        "biological": biological
    }


def handle_laser_comms_display(panel, player, **kwargs):
    """
    Return recent laser messages for this panel.
    """
    messages = LaserMessage.query.filter_by(panel_id=panel.id).order_by(
        LaserMessage.sent_time.desc()
    ).all()
    return {"messages": messages}

# More display handlers (e.g., inspect, engineering) can be added below
