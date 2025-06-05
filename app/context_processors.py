from .models import GameState
from datetime import datetime, timezone
from flask import current_app
from jinja2 import pass_context


@pass_context
def has_permission(context, player, perm):
    return player and perm in (player.permissions or [])

def base_context():
    game_state = GameState.query.first()
    now = datetime.now(timezone.utc)
    fictional_time = now.replace(year=now.year + 250)
    return {
        "game_state": game_state,
        "now": now,
        "fictional_time": fictional_time,
        "has_permission": has_permission
    }

