
# app/helpers.py

import json
from datetime import datetime
from app.models import Player, Panel, Interactable, MessageTarget


def resolve_panel(code):
    """Return a Panel by its code (case-insensitive)."""
    if not code:
        return None
    return Panel.query.filter_by(code=code.upper()).first()


def resolve_player(code):
    """Return a Player by their code (case-insensitive)."""
    if not code:
        return None
    return Player.query.filter_by(player_code=code.upper()).first()


def resolve_interactable(code):
    """Return an Interactable by its code (case-insensitive)."""
    if not code:
        return None
    return Interactable.query.filter_by(code=code.upper()).first()


def build_menu_items(panel, player):
    """
    Merge a panel's static menu items and a player's dynamic menu items.
    Returns a list of (key, label) tuples.
    """
    menu_data = []

    if panel.menu_items:
        if isinstance(panel.menu_items, str):
            try:
                menu_data = json.loads(panel.menu_items)
            except json.JSONDecodeError:
                menu_data = []
        elif isinstance(panel.menu_items, list):
            menu_data = panel.menu_items

    if player and isinstance(player.player_menu, list):
        menu_data += player.player_menu

    return [(item.get('key'), item.get('label')) for item in menu_data if 'key' in item and 'label' in item]


def get_fictional_time():
    """Returns the in-universe time. Placeholder using UTC."""
    return datetime.utcnow()


def get_delay_to_target(target_obj):
    """
    Returns the light-speed delay (in seconds) to a given MessageTarget.
    Assumes distance is stored in light-minutes.
    """
    if not target_obj or not target_obj.distance_in_light_minutes:
        return 0
    return target_obj.distance_in_light_minutes * 60
