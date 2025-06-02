from app.models import GameState
from datetime import datetime, timezone

def base_context():
    game_state = GameState.query.first()
    now = datetime.now(timezone.utc)
    fictional_time = now.replace(year=now.year + 250)
    return {
        "game_state": game_state,
        "now": now,
        "fictional_time": fictional_time
    }
