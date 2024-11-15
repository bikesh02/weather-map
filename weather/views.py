from django.http import HttpResponse
import os
import requests
import folium
import matplotlib
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
import joblib
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime, timedelta
from django.templatetags.static import static
from .data_analysis import average_temperature, last_week_data, store_weather_data
from .train.model import get_future_data

def fetch_live_weather_data_by_city(api_key, city_name):
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city_name}&units=metric&appid={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return None

data = {
    'day_index': list(range(1, 11)),
    'temperature': [23, 25, 22, 24, 26, 27, 25, 28, 30, 29]
}
df = pd.DataFrame(data)

X = df[['day_index']]
y = df['temperature']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = DecisionTreeRegressor()
model.fit(X_train, y_train)

joblib.dump(model, 'temperature_prediction_model.pkl')

def predict_next_day_temperature(city_name):
    try:
        model = joblib.load('temperature_prediction_model.pkl')
        last_index = len(last_week_data(city_name))
        predicted_temp = model.predict([[last_index + 1]])[0]
        return predicted_temp
    except Exception as e:
        return None

@csrf_exempt
def index(request):
    if request.method == 'POST':
        city_name = request.POST.get('city')
        api_key = '45a9478f21851ae5fbc7ef7a6620e15c'
        weather_data = fetch_live_weather_data_by_city(api_key, city_name)

        if weather_data and 'main' in weather_data and 'coord' in weather_data:
            temperature = weather_data['main']['temp']
            humidity = weather_data['main']['humidity']
            weather_condition = weather_data['weather'][0]['description']
            wind_speed = weather_data['wind']['speed']
            lat = weather_data['coord']['lat']
            lon = weather_data['coord']['lon']
            weather_icon_code = weather_data['weather'][0]['icon']
            weather_icon = f"http://openweathermap.org/img/wn/{weather_icon_code}@2x.png"

            store_weather_data(city_name, temperature, humidity, weather_condition, wind_speed)

            if temperature < 10:
                temp_analysis = "It's quite cold."
            elif 10 <= temperature <= 25:
                temp_analysis = "The weather is mild."
            else:
                temp_analysis = "It's warm or hot."

            if humidity > 70:
                humidity_analysis = "The air is quite humid."
            else:
                humidity_analysis = "Humidity levels are comfortable."

            condition_analysis = "The weather is calm."
            if 'rain' in weather_condition.lower():
                condition_analysis = "It might be raining. Don't forget your umbrella!"
                weather_icon = "/static/icons/rain1.jpeg"
            elif 'broken clouds' in weather_condition.lower():
                condition_analysis = "Broken clouds are present. Enjoy a mix of sun and shade!"
                weather_icon = "/static/icons/bc.jpeg"
            elif 'scattered clouds' in weather_condition.lower():
                condition_analysis = "Scattered clouds in the sky. A mix of sun and shade today!"
                weather_icon = "/static/icons/sc.png"
            elif 'few clouds' in weather_condition.lower():
                condition_analysis = "Few clouds in the sky. Enjoy the clear view!"
                weather_icon = "/static/icons/few.png"
            elif 'haze' in weather_condition.lower():
                condition_analysis = "Haze is expected. Limit outdoor activities if possible."
                weather_icon = "/static/icons/haze.png"
            elif 'overcast' in weather_condition.lower():
                condition_analysis = "Overcast skies ahead. Expect a cloudy day with little sunshine!"
                weather_icon = "/static/icons/overcast.jpeg"
            elif 'mist' in weather_condition.lower():
                condition_analysis = "Misty conditions ahead. Visibility may be reduced!"
                weather_icon = "/static/icons/mist.png"
            elif 'clear' in weather_condition.lower():
                condition_analysis = "The sky is clear. Enjoy the sunshine!"
                weather_icon = "/static/icons/clear.jpeg"
            else:
                condition_analysis = f"The weather is {weather_condition}."
                weather_icon = "/static/icons/default_weather.jpeg"

            predicted_temp = predict_next_day_temperature(city_name)
            if predicted_temp is not None:
                prediction_message = f"Based on current trends, the predicted temperature for tomorrow is {predicted_temp:.2f}°C."
            else:
                prediction_message = "Prediction is not available at the moment."

            average_temp = average_temperature(city_name)
            last_week = last_week_data(city_name)
            historical_analysis = f"The average temperature over the past week was {average_temp:.2f}°C." if average_temp else "No historical data available."

            m = folium.Map(location=[lat, lon], zoom_start=10)

            folium.Marker(
                [lat, lon],
                popup=f"{city_name}: {temperature}°C"
            ).add_to(m)

            map_filename = f'{city_name}_temperature_map.html'
            file_path = os.path.join(os.getcwd(), map_filename)
            m.save(file_path)

            with open(file_path, 'r') as file:
                map_content = file.read()

            response_content = f"""
                <html>
                 <head>
                 <title>Weather Analysis</title>
                 </head>
                <body>
                <div>
                    <h1 style="text-align: center;"><b>Weather Analysis for {city_name}</b></h1>
                    <p><b>Temperature: </b>{temperature}°C - {temp_analysis}</p>
                    <p><b>Humidity: </b>{humidity}% - {humidity_analysis}</p>
                    <p><b>Weather Condition: </b>{weather_condition} - {condition_analysis}</p>
                    <p><b>Wind Speed: </b>{wind_speed} m/s</p>
                    <h2><b>Prediction for Tomorrow</b></h2>
                    <p>{prediction_message}</p>
                    <h2><b>Historical Data</b></h2>
                    <p>{historical_analysis}</p>
                       <div>
                        <h2><b>Current Weather </b></h2>
                        <img src="{weather_icon}" alt="Weather Icon" style="width: 100px; height: 100px;">
                    </div>
                    <div>
                        <h2><b>Map Location </b></h2>
                        {map_content}
                        </div>
                    </div>
                </body>
                </html>
            """

            return HttpResponse(response_content)
        else:
            return HttpResponse("Could not retrieve weather data for the city.")
    else:
        data = get_future_data()

        # Unpack the dictionary
        precip, predicted_temp_max,temp_min = list(data.values())[:3]


        # Create the HTML content with the unpacked values
        form_html = f'''
        <html>
          <head>
            <style>
                body {{
                    background-image: url("/static/background-image/4f98a2c314cd2a207e0772b4e14118e4.JPG");
                    background-size: cover;
                    background-repeat: no-repeat;
                    background-position: center;
                    color: black;
                    font-family: Arial, sans-serif;
                }}
                h1 {{
                    margin-top: 50px;
                    font-size: 2em;
                }}
                form {{
                    background-color: rgba(0, 0, 0, 0.6);
                    padding: 20px;
                    border-radius: 10px;
                    display: inline-block;
                }}
                label {{
                    color: white;
                    font-size: 1.2em;
                    display: block;
                    margin-bottom: 10px;
                }}
                input[type="text"] {{
                    padding: 10px;
                    width: 250px;
                    border-radius: 5px;
                    border: none;
                    font-size: 1em;
                }}
                button {{
                    background-color: #4CAF50;
                    border: none;
                    padding: 10px 20px;
                    color: white;
                    font-size: 1.2em;
                    cursor: pointer;
                    border-radius: 5px;
                    margin-top: 10px;
                }}
                button:hover {{
                    background-color: #45a049;
                }}
                .highlight {{
                    font-weight: bold;
                    color: #FF6347; /* Highlight color */
                }}
            </style>
          </head>
          <body>
            <div style="display: flex; justify-content: center; align-items: center; height: 30vh; text-align: center; flex-direction: column;">
                <h1>Welcome to Live Weather</h1>
                <form method="post">
                    <label for="city">Enter city name:</label>
                    <input type="text" id="city" name="city" required>
                    <button type="submit">Get Weather</button>
                </form>
            </div>
            <div style="text-align: center;">
                <h2><b>Predicted Weather Data For Tomorrow In Kathmandu:</b></h2>
                <p>Precipitation: <span class="">{precip}%</span></p>
                <p>Max Temp: <span class="">{predicted_temp_max}°C</span></p>
                <p>Min Temp: <span class="">{temp_min}°C</span></p>
              
            </div>
        </body>
        </html>
        '''
        return HttpResponse(form_html)
