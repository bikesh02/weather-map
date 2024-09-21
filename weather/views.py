from django.http import HttpResponse
import os
import requests
import folium
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
    

def predict_next_day_temperature(current_temp):
    return current_temp + 1.5   

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
            elif 'clear' in weather_condition.lower():
                condition_analysis = "The sky is clear. Enjoy the sunshine!"
            else:
                condition_analysis = f"The weather is {weather_condition}."
                
            
            predicted_temp = predict_next_day_temperature(temperature)
            prediction_message = f"Based on current trends, the predicted temperature for tomorrow is {predicted_temp:.2f}°C."
            
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
                    </div>
                    {map_content}
                    
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
                color: white;
                font-family: Arial, sans-serif;
            }

            h1 {
                margin-top: 50px;
                font-size: 2em;
            }

            form {
                background-color: rgba(0, 0, 0, 0.6);  /* Optional: Add a semi-transparent background for better readability */
                padding: 20px;
                border-radius: 10px;
                display: inline-block;
            }

            label, input, button {
                color: white;
                font-size: 1.2em;
            }

            button {
                background-color: #4CAF50;
                border: none;
                padding: 10px 20px;
                color: white;
                cursor: pointer;
            }

            button:hover {
                background-color: #45a049;
            }
        </style>
    </head>
    <body>
        <h1>Welcome to Live Weather</h1>
        <form method="post">
            <label for="city">Enter city name:</label>
            <input type="text" id="city" name="city" required>
            <button type="submit">Get Weather</button>
        </form>
    </body>
</html>
'''

        return HttpResponse(form_html)


