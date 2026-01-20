"""Constants for the Xiaomi miHeater integration."""

DOMAIN = "miheater"

CONF_MODEL = "model"
DEFAULT_NAME = "Xiaomi Heater"

DEFAULT_MIN_TEMP = 18
DEFAULT_MAX_TEMP = 28

MODEL_PROPERTIES = {
    "zhimi.heater.mc2": {
        "power": (2, 1),
        "target_temperature": (2, 5),
        "current_temperature": (4, 7),
        "humidity": None,
        "child_lock": (5, 1),
        "buzzer": (6, 1),
        "led_brightness": (7, 3),
        "countdown_time": (3, 1),
    },
    "zhimi.heater.mc2a": {
        "power": (2, 1),
        "target_temperature": (2, 5),
        "current_temperature": (4, 7),
        "humidity": None,
        "child_lock": (5, 1),
        "buzzer": (6, 1),
        "led_brightness": (7, 3),
        "countdown_time": (3, 1),
    },
    "zhimi.heater.zb1": {
        "power": (2, 2),
        "target_temperature": (2, 6),
        "current_temperature": (5, 8),
        "humidity": (5, 7),
        "child_lock": None,
        "buzzer": None,
        "led_brightness": None,
        "countdown_time": None,
    },
    "zhimi.heater.za2": {
        "power": (2, 2),
        "target_temperature": (2, 6),
        "current_temperature": (5, 8),
        "humidity": (5, 7),
        "child_lock": (7, 1),
        "buzzer": (3, 1),
        "led_brightness": (6, 1),
        "countdown_time": (4, 1),
    },
    "leshow.heater.bs1s": {
        "power": (2, 1),
        "target_temperature": (2, 3),
        "current_temperature": (4, 7),
        "humidity": None,
        "child_lock": (5, 1),
        "buzzer": (6, 1),
        "led_brightness": (7, 1),
        "countdown_time": (3, 1),
    },
}

MODEL_LIMITS = {
    "zhimi.heater.mc2": {"temperature_range": (18, 28), "delay_off_range": (0, 12)},
    "zhimi.heater.mc2a": {"temperature_range": (18, 28), "delay_off_range": (0, 12)},
    "zhimi.heater.za2": {"temperature_range": (16, 28), "delay_off_range": (0, 8)},
    "leshow.heater.bs1s": {
        "temperature_range": (18, 28),
        "delay_off_range": (0, 12),
    },
    "zhimi.heater.zb1": {"temperature_range": (16, 28), "delay_off_range": (0, 8)},
}
