# app/helpers.py

from app.models import Player, Panel, Interactable, MessageTarget
import json
from datetime import datetime


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


def build_menu_items(panel, player):
    """Combine static panel menu and any player-specific additions."""
    # Ensure panel.menu_items is a list
    menu_data = []
    if panel.menu_items:
        if isinstance(panel.menu_items, str):
            try:
                menu_data = json.loads(panel.menu_items)
            except json.JSONDecodeError:
                menu_data = []
        elif isinstance(panel.menu_items, list):
            menu_data = panel.menu_items

    # Add player menu if present
    if player and isinstance(player.player_menu, list):
        menu_data += player.player_menu

    return [(item.get('key'), item.get('label')) for item in menu_data if 'key' in item and 'label' in item]



def get_fictional_time():
    # For now, this just returns the current time — update to match your in-universe logic
    return datetime.utcnow()


def get_delay_to_target(target_obj):
    # Expects a MessageTarget object, not a name string
    if not target_obj or not target_obj.distance_in_light_minutes:
        return 0
    return target_obj.distance_in_light_minutes * 60  # convert to seconds
