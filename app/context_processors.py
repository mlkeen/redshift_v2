
# app/context_processors.py

from datetime import datetime, timezone
from flask import current_app
from jinja2 import pass_context

from .models import GameState


@pass_context
def has_permission(context, player, perm):
    """
    Jinja2 context filter: Check if the player has a specific permission key.
    """
    return player and perm in (player.permissions or [])


def base_context():
    """
    Inject base context variables into all templates:
    - Current game state
    - Current real and fictional time
    - has_permission() helper
    """
    game_state = GameState.query.first()
    now = datetime.now(timezone.utc)
    fictional_time = now.replace(year=now.year + 250)

    return {
        "game_state": game_state,
        "now": now,
        "fictional_time": fictional_time,
        "has_permission": has_permission
    }
