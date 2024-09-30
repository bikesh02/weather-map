import matplotlib.pyplot as plt
import os

# Assuming you already have the data for temperature, humidity, and wind speed.
def create_weather_chart(city_name, temperature, humidity, wind_speed):
    # Set up the chart
    plt.figure(figsize=(10, 6))
    parameters = ['Temperature (°C)', 'Humidity (%)', 'Wind Speed (m/s)']
    values = [temperature, humidity, wind_speed]
    
    # Create the bar chart
    plt.bar(parameters, values, color=['skyblue', 'orange', 'lightgreen'])
    plt.title(f'Weather Analysis for {city_name}')
    plt.xlabel('Parameters')
    plt.ylabel('Values')
    plt.grid(axis='y', linestyle='--')
    
    # Save the chart as a static file
    static_dir = os.path.join(os.getcwd(), 'static', 'weather_images')
    os.makedirs(static_dir, exist_ok=True)
    img_filename = f'{city_name}_weather_analysis.png'
    img_path = os.path.join(static_dir, img_filename)
    plt.savefig(img_path)
    plt.close()

    return img_filename
