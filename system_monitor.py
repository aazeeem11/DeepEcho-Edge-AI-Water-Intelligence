import random


def get_system_health():
    return {
        "cpu": random.uniform(20, 80),
        "memory": random.uniform(30, 85),
        "battery": random.uniform(40, 100),
        "signal_quality": random.uniform(60, 100),
    }
