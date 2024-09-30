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
    

def predict_next_day_temperature():
    try:
        model = joblib.load('temperature_prediction_model.pkl')
        last_index = len(last_week_data()) 
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
                
            try:
                model = joblib.load('temperature_prediction_model.pkl')
                last_index = len(last_week_data(city_name)) - 1  # Get the index of the last day
                predicted_temp = model.predict([[last_index + 1]])[0]
                prediction_message = f"Based on current trends, the predicted temperature for tomorrow is {predicted_temp:.2f}°C."
            except Exception as e:
                prediction_message = "Prediction is not available at the moment."
            
            # predicted_temp = predict_next_day_temperature(temperature)
            # prediction_message = f"Based on current trends, the predicted temperature for tomorrow is {predicted_temp:.2f}°C."
            
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
        form_html = '''
<html>
    <head>
        <style>
            body {
                background-image: url("/static/background-image/4f98a2c314cd2a207e0772b4e14118e4.JPG");
                background-size: cover;
                background-repeat: no-repeat;
                background-position: center;
                color: black;
                font-family: Arial, sans-serif;
            }

            h1 {
                margin-top: 50px;
                font-size: 2em;
            }

            form {
                background-color: rgba(0, 0, 0, 0.6);
                padding: 20px;
                border-radius: 10px;
                display: inline-block;
            }

             label {
                color: white;
                font-size: 1.2em;
                display: block;  
                margin-bottom: 10px; 
            }

            input[type="text"] {
                padding: 10px;  
                width: 250px;  
                border-radius: 5px;  
                border: none;  
                font-size: 1em;  

            button {
                background-color: #4CAF50;
                border: none;
                padding: 10px 20px;
                color: white;
                font-size: 1.2em;
                cursor: pointer;
                border-radius: 5px;
                margin-top: 10px;
            }

            button:hover {
                background-color: #45a049;
            }
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
        
        <div style="text-align: center; margin-top: 20px;">
        <h2>Weather Results</h2>
        <div style="display: flex; justify-content: center;">
            <div style="margin: 0 20px;">
                <h3>Jaleshwor</h3>
                <p>Condition: Sunny</p>
                <p> Temperature: 35°C</p>
                <p> Precipitation: 1%</p>
                <p>Humidity: 64%</p>
                <p> Wind: 14 km/h</p>
                <h4>Weather</h4>
                <p>Saturday 16:00</p>
                <table style="margin: 0 auto; border-collapse: collapse;">
                    <tr>
                        <th>Temperature</th>
                        <th>Precipitation</th>
                        <th>Wind</th>
                    </tr>
                    <tr>
                        <td>35</td>
                        <td>1%</td>
                        <td>14 km/h</td>
                    </tr>
                    <!-- Add hourly data rows as needed -->
                </table>
                <h4>Weekly Forecast</h4>
                <table style="margin: 0 auto; border-collapse: collapse;">
                    <tr>
                        <th>Day</th>
                        <th>Condition</th>
                        <th>High/Low</th>
                    </tr>
                    <tr>
                        <td>Sat</td>
                        <td>Partly cloudy</td>
                        <td>37°/28°</td>
                    </tr>
                    <tr>
                        <td>Sun</td>
                        <td>Mostly sunny</td>
                        <td>37°/28°</td>
                    </tr>
                    <tr>
                        <td>Mon</td>
                        <td>Partly cloudy</td>
                        <td>38°/28°</td>
                    </tr>
                     
                </table>
            </div>
            
            <div style="margin: 0 20px;">
            <h3>Janakpur</h3>
                <p>Condition: Sunny</p>
                <p>Temperature: 35°C</p>
                <p>Precipitation: 1%</p>
                <p>Humidity: 64%</p>
                <p>Wind: 14 km/h</p>
                <h4>Weather</h4>
                <p>Saturday 16:00</p>
                <table style="margin: 0 auto; border-collapse: collapse;">
                    <tr>
                        <th>Temperature</th>
                        <th>Precipitation</th>
                        <th>Wind</th>
                    </tr>
                    <tr>
                        <td>35</td>
                        <td>1%</td>
                        <td>14 km/h</td>
                    </tr>
                     
                </table>
                <h4>Weekly Forecast</h4>
                <table style="margin: 0 auto; border-collapse: collapse;">
                    <tr>
                        <th>Day</th>
                        <th>Condition</th>
                        <th>High/Low</th>
                    </tr>
                    <tr>
                        <td>Sat</td>
                        <td>Partly cloudy</td>
                        <td>37°/28°</td>
                    </tr>
                    <tr>
                        <td>Sun</td>
                        <td>Mostly sunny</td>
                        <td>37°/28°</td>
                    </tr>
                    <tr>
                        <td>Mon</td>
                        <td>Partly cloudy</td>
                        <td>38°/28°</td>
                    </tr>
                     
                </table>
            </div>

            <div style="margin: 0 20px;">
                <h3>Kathmandu</h3>
                <p>Condition: Partly cloudy</p>
                <p>Temperature: 30°C</p>
                <p>Precipitation: 5%</p>
                <p>Humidity: 50%</p>
                <p>Wind: 10 km/h</p>
                <h4>Weather</h4>
                <p>Saturday 16:00</p>
                <table style="margin: 0 auto; border-collapse: collapse;">
                    <tr>
                        <th>Temperature</th>
                        <th>Precipitation</th>
                        <th>Wind</th>
                    </tr>
                    <tr>
                        <td>30</td>
                        <td>5%</td>
                        <td>10 km/h</td>
                    </tr>
                     
                </table>
                <h4>Weekly Forecast</h4>
                <table style="margin: 0 auto; border-collapse: collapse;">
                    <tr>
                        <th>Day</th>
                        <th>Condition</th>
                        <th>High/Low</th>
                    </tr>
                    <tr>
                        <td>Sat</td>
                        <td>Partly cloudy</td>
                        <td>32°/24°</td>
                    </tr>
                    <tr>
                        <td>Sun</td>
                        <td>Sunny</td>
                        <td>34°/26°</td>
                    </tr>
                    <tr>
                        <td>Mon</td>
                        <td>Cloudy</td>
                        <td>30°/25°</td>
                    </tr>
                     
                </table>
            </div>
        </div>
    </div>
    </body>
</html>
'''

        return HttpResponse(form_html)


