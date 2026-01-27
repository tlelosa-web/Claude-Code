"""
connection_lookup.py

Determines motor connection (STAR or DELTA) based on:
- Voltage
- Pole count
- Motor size (kW)

Rules implemented exactly as provided.
"""

from typing import Tuple, Optional


# -------------------------------
# Connection rules (engineering tables)
# -------------------------------

# Each rule:
# (voltage, pole) -> thresholds in kW
#
# For STAR:
#   motor_kw <= max_kw
#
# For DELTA:
#   motor_kw >= min_kw (for 380V)
#   motor_kw <= max_kw (for 525V / 220V as specified)

STAR_RULES = {
    (380, 2): 3.0,
    (380, 4): 3.0,
    (380, 6): 1.5,
    (380, 8): 1.1,
}

DELTA_RULES_380_MIN = {
    (380, 2): 4.0,
    (380, 4): 4.0,
    (380, 6): 2.2,
    (380, 8): 1.5,
}

DELTA_RULES_MAX = {
    (525, 2): 4.0,
    (525, 4): 4.0,
    (525, 6): 2.2,
    (525, 8): 1.5,

    (220, 2): 3.0,
    (220, 4): 3.0,
    (220, 6): 1.5,
    (220, 8): 1.1,
}


# -------------------------------
# Public API
# -------------------------------
def suggest_connection(
    voltage: float,
    pole: int,
    motor_kw: float,
) -> Tuple[str, Optional[str]]:
    """
    Returns:
        ("STAR" | "DELTA" | "", error_message | None)
    """

    try:
        v = int(round(voltage))
        p = int(pole)
        m = float(motor_kw)
    except Exception:
        return "", "Invalid numeric input for voltage, pole, or motor kW."

    key = (v, p)

    # ---------- STAR (380V only) ----------
    if key in STAR_RULES:
        max_kw = STAR_RULES[key]
        if m <= max_kw:
            return "STAR", None

    # ---------- DELTA (380V minimum size) ----------
    if key in DELTA_RULES_380_MIN:
        min_kw = DELTA_RULES_380_MIN[key]
        if m >= min_kw:
            return "DELTA", None

    # ---------- DELTA (525V / 220V maximum size) ----------
    if key in DELTA_RULES_MAX:
        max_kw = DELTA_RULES_MAX[key]
        if m <= max_kw:
            return "DELTA", None

    return "", "No valid STAR or DELTA configuration for given motor size, pole, and voltage."
