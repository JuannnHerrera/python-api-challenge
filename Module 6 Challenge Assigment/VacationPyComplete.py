import hvplot.pandas
import pandas as pd
import requests
import folium

# Define Geoapify API key
geoapify_key = "1afffafb81674eb5b82e4126d6073fd4"

# Load the CSV file created in Part 1 into a Pandas DataFrame
city_data_df = pd.read_csv("output_data/cities.csv")

# Step 1: Create a map that displays a point for every city in the `city_data_df` DataFrame.
# The size of the point should be the humidity in each city.

# Configure the map plot
# Adjust the column names for longitude and latitude
city_data_df.rename(columns={'Lng': 'Longitude', 'Lat': 'Latitude'}, inplace=True)

# Configure the map plot
city_map = city_data_df.hvplot.scatter(
    x='Longitude',
    y='Latitude',
    size='Humidity',
    hover_cols=['City', 'Country'],
    title='City Map with Humidity',
    xlabel='Longitude',
    ylabel='Latitude',
    frame_height=400
)

# Step 2: Narrow down the `city_data_df` DataFrame to find your ideal weather condition
# Narrow down cities that fit criteria and drop any results with null values
ideal_weather_df = city_data_df[(city_data_df['Max Temp'] > 70) & 
                                (city_data_df['Max Temp'] < 80) & 
                                (city_data_df['Wind Speed'] < 10) & 
                                (city_data_df['Cloudiness'] == 0)].dropna()

# Step 3: Create a new DataFrame called `hotel_df`.
# Use the Pandas copy function to create DataFrame called hotel_df to store the city, country, coordinates, and humidity
hotel_df = ideal_weather_df[['City', 'Country', 'Latitude', 'Longitude', 'Humidity']].copy()

# Add empty columns for additional data
hotel_df['Hotel Name'] = ""
hotel_df['LNG'] = ""
hotel_df['LAT'] = ""
hotel_df['Hotel Color'] = ""

# Step 5: For each city, use the Geoapify Places API to find the nearest hotel located within the specified coordinates.
# Set base URL for the Places API
base_url = "https://api.geoapify.com/v2/places"

# Print a message to follow up the hotel search
print("Starting hotel search")

# Iterate through the hotel_df DataFrame
for index, row in hotel_df.iterrows():
    # Get latitude and longitude from the DataFrame
    lat = row['Latitude']
    lon = row['Longitude']
    
    # Set parameters for the Places API request
    params = {
        'categories': 'accommodation.hotel',
        'lat': lat,
        'lon': lon,
        'limit': 1,
        'apiKey': geoapify_key
    }
    
    # Make an API request using the params dictionary
    response = requests.get(base_url, params=params)
    
    # Convert the API response to JSON format
    data = response.json()
    
    # Check if hotels are found in the response
    if data.get('features'):
        # Extract hotel name and coordinates from the response if they exist
        if data['features'][0]['properties'].get('name'):
            hotel_name = data['features'][0]['properties']['name']
            hotel_df.loc[index, "Hotel Name"] = hotel_name
        if data['features'][0]['properties'].get('lon'):
            lng = data['features'][0]['properties']['lon']
            hotel_df.loc[index, "LNG"] = lng
        if data['features'][0]['properties'].get('lat'):
            lat = data['features'][0]['properties']['lat']
            hotel_df.loc[index, "LAT"] = lat
    else:
        # If no hotel is found, set the hotel name as "No Hotel Name Found".
        hotel_df.loc[index, "Hotel Name"] = "No Hotel Name Found"
        hotel_df.loc[index, "LNG"] = "N/A"
        hotel_df.loc[index, "LAT"] = "N/A"
        
    # Log the search results
    print(f"{hotel_df.loc[index, 'City']} - nearest hotel: {hotel_df.loc[index, 'Hotel Name']}")

# Create a list of unique hotel names for the legend
unique_hotel_names = hotel_df['Hotel Name'].unique()

# Assign colors to hotel markers
colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'beige', 'darkblue', 'darkgreen', 'cadetblue', 'darkpurple', 'white', 'pink', 'lightblue', 'lightgreen', 'gray', 'black', 'lightgray']

for index, row in hotel_df.iterrows():
    hotel_df.loc[index, 'Hotel Color'] = colors[list(unique_hotel_names).index(row['Hotel Name']) % len(colors)]

# Create a Folium map and add markers for each hotel
m = folium.Map(location=[hotel_df['Latitude'].mean(), hotel_df['Longitude'].mean()], zoom_start=3, tiles='CartoDB dark_matter')

# Add hotel markers to the map
for _, row in hotel_df.iterrows():
    popup_text = f"""
    <div style="width: 200px; height: auto; overflow-y: auto;">
    <strong>City:</strong> {row['City']}<br>
    <strong>Country:</strong> {row['Country']}<br>
    <strong>LNG:</strong> {row['LNG']}<br>
    <strong>LAT:</strong> {row['LAT']}<br>
    <strong>Humidity:</strong> {row['Humidity']}<br>
    <strong>Hotel:</strong> {row['Hotel Name']}<br>
    </div>
    """
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_text, max_width=300),
        icon=folium.Icon(color=row['Hotel Color'], icon='info-sign')
    ).add_to(m)

# Add legend for hotel names with corresponding colors
legend_html = """
     <div style="position: fixed; 
                 bottom: 50px; left: 50px; width: 200px; 
                 border:2px solid grey; z-index:9999; font-size:14px;
                 background-color: white;
                 opacity: 0.7;
                 overflow-y: auto; /* Adding scroll */
                 max-height: 250px; /* Setting maximum height */
                 ">
      &nbsp; <strong>Hotel Legend</strong> <br>
      """
for name, color in zip(unique_hotel_names, colors):
    legend_html += f"&nbsp; <i class='fa fa-square' style='color:{color}'></i> &nbsp; {name if name != 'No Hotel Name Found' else 'No Hotel Name'} <br>"
legend_html += """
     </div>
    """
m.get_root().html.add_child(folium.Element(legend_html))

# Save the Folium map as an HTML file
m.save("output_data/hotel_map.html")

# Print confirmation message
print("Folium map with hotel information saved as 'output_data/hotel_map.html'")
