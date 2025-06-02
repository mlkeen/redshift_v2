from app.models import GameState
from datetime import datetime

def base_context():
    game_state = GameState.query.first()
    return {
        "game_state": game_state,
        "now": datetime.utcnow
    }
