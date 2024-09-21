from django.db import models
import sqlite3
from datetime import datetime

def create_weather_table():
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS weather (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            temperature REAL,
            humidity REAL,
            weather_condition TEXT,
            wind_speed REAL,
            date_time TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()


create_weather_table()

