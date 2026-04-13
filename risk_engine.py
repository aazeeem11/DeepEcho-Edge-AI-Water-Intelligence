from config import *


def calculate_hypoxia_risk(env):
    w1, w2, w3 = 0.5, 0.3, 0.2

    organic = env["organic_ratio"]
    temp_factor = env["temperature"] / 40
    turbidity_factor = env["turbidity"] / 100

    risk = w1 * organic + w2 * temp_factor + w3 * turbidity_factor

    return min(risk, 1.0)


def generate_alert(risk, ammonia_peak):
    if risk > HYPOXIA_CRITICAL or ammonia_peak > AMMONIA_CRITICAL:
        return "CRITICAL"
    elif risk > HYPOXIA_WARNING or ammonia_peak > AMMONIA_WARNING:
        return "WARNING"
    else:
        return "NORMAL"
