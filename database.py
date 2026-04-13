import sqlite3
from datetime import datetime

import pandas as pd

DB_NAME = "deepecho.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        """
    CREATE TABLE IF NOT EXISTS measurements (
        timestamp TEXT,
        temperature REAL,
        turbidity REAL,
        organic_ratio REAL,
        hypoxia REAL,
        ammonia_peak REAL,
        alert TEXT
    )
    """
    )

    conn.commit()
    conn.close()


def insert_measurement(data):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute(
        """
    INSERT INTO measurements VALUES (?,?,?,?,?,?,?)
    """,
        (
            datetime.now().isoformat(),
            data["temperature"],
            data["turbidity"],
            data["organic_ratio"],
            data["hypoxia"],
            data["ammonia_peak"],
            data["alert"],
        ),
    )

    conn.commit()
    conn.close()


def load_history():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM measurements", conn)
    conn.close()
    return df
