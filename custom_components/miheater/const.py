"""Constants for the Xiaomi miHeater integration."""

DOMAIN = "miheater"

CONF_MODEL = "model"
DEFAULT_NAME = "Xiaomi Heater"

MIN_TEMP = 18
MAX_TEMP = 28

MODEL_PROPERTIES = {
    "zhimi.heater.mc2": {
        "power": (2, 1),
        "target_temperature": (2, 5),
        "current_temperature": (4, 7),
        "humidity": None,
    },
    "zhimi.heater.zb1": {
        "power": (2, 2),
        "target_temperature": (2, 6),
        "current_temperature": (5, 8),
        "humidity": (5, 7),
    },
    "zhimi.heater.za2": {
        "power": (2, 2),
        "target_temperature": (2, 6),
        "current_temperature": (5, 8),
        "humidity": (5, 7),
    },
}
