import sqlite3
from datetime import datetime, timedelta

def get_data_for_city(city):
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM weather WHERE city=?', (city,))
    data = c.fetchall()
    conn.close()
    return data

def average_temperature(city):
    data = get_data_for_city(city)
    if data:
        temps = [row[2] for row in data]  
        return sum(temps) / len(temps)
    return None

def last_week_data(city):
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()
    one_week_ago = datetime.now() - timedelta(days=7)
    c.execute('SELECT * FROM weather WHERE city=? AND date_time > ?', (city, one_week_ago))
    data = c.fetchall()
    conn.close()
    return data


def store_weather_data(city, temperature, humidity, weather_condition, wind_speed):
    conn = sqlite3.connect('weather_data.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO weather (city, temperature, humidity, weather_condition, wind_speed, date_time)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (city, temperature, humidity, weather_condition, wind_speed, datetime.now()))
    conn.commit()
    conn.close()
