import streamlit as st
import requests
import folium
from datetime import datetime, timezone, timedelta
from streamlit_folium import st_folium
from folium import LayerControl

# Title of the app
st.title("Real-time Taxi Availability in Singapore")
st.markdown("""
This app retrieves and displays real-time taxi availability data from Data.gov.sg.

Grid-based counting identifies high-density areas, visualized with colored rectangles and markers.
""")

# Function to get taxi availability data from the real-time API
@st.cache_data(ttl=90)  # Cache data for 90 seconds
def fetch_taxi_data():
    base_url = "https://api.data.gov.sg/v1/transport/taxi-availability"
    try:
        # Make the API request
        response = requests.get(base_url)
        response.raise_for_status()  # Raise an error for HTTP error codes
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data from the API: {e}")
        return None

# Function to assign a taxi location to a grid cell
def get_grid_cell(lat, lon, grid_size):
    lat_idx = int((lat - min_lat) / grid_size)
    lon_idx = int((lon - min_lon) / grid_size)
    return (lat_idx, lon_idx)
    
# Fetch the taxi data
data = fetch_taxi_data()

# Process the GeoJSON response
if data and "features" in data:
    features = data["features"]
    timestamp = features[0]["properties"]["timestamp"] if features else "N/A"
    taxi_count = features[0]["properties"]["taxi_count"] if features else 0

    st.write(f"**Data Timestamp**: {timestamp}")
    st.write(f"**Total Available Taxis**: {taxi_count}")

    # Extract taxi coordinates
    coordinates = features[0]["geometry"]["coordinates"]
    taxi_locations = [[lat, lon] for lon, lat in coordinates]

    # Define grid parameters
    grid_size = 0.01  
    min_lat, max_lat = 1.2, 1.5  # Approx. latitude bounds of Singapore
    min_lon, max_lon = 103.6, 104.0  # Approx. longitude bounds of Singapore

    grid_counts = {}

    # Count taxis in each grid cell
    for lat, lon in taxi_locations:
        cell = get_grid_cell(lat, lon, grid_size)
        if cell not in grid_counts:
            grid_counts[cell] = 0
        grid_counts[cell] += 1

    # Creates the map centered on Singapore
    map_center = [1.3521, 103.8198]
    m = folium.Map(location=map_center, zoom_start=12)
   
    # Grid-based rectangles layer
    rectangle_layer = folium.FeatureGroup(name="Grid Rectangles")
    for (lat_idx, lon_idx), count in grid_counts.items():
        cell_lat = min_lat + lat_idx * grid_size
        cell_lon = min_lon + lon_idx * grid_size

        # Determine color based on density
        if count > 35:
            color = 'red'
        elif count > 20:
            color = 'orange'
        else:
            color = 'green'

        folium.Rectangle(
            bounds=[
                [cell_lat, cell_lon],
                [cell_lat + grid_size, cell_lon + grid_size],
            ],
            color=color,
            fill=True,
            fill_opacity=0.3,
            weight=1,
            popup=f"Taxis: {count}"
        ).add_to(rectangle_layer)

    rectangle_layer.add_to(m)
    
    # Markers layer
    marker_layer = folium.FeatureGroup(name="High-Density Markers")
    for (lat_idx, lon_idx), count in grid_counts.items():
        if count > 25:  # Only for high-density areas
            cell_lat = min_lat + lat_idx * grid_size
            cell_lon = min_lon + lon_idx * grid_size
            folium.Marker(
                location=[cell_lat + grid_size / 2, cell_lon + grid_size / 2],
                icon=folium.Icon(color='red', icon='info-sign'),
                tooltip=f"High Density: {count} taxis"
            ).add_to(marker_layer)
    
    #LayerControl to toggle layers
    LayerControl().add_to(m)

    # Display the map in Streamlit
    st_folium(m, width=900, height=500)

    st.markdown("""
    Explanation of Layers
        
        Grid Rectangles: Colored rectangles show taxi density in each grid cell.
            Green: Low density (< 20 taxis)
            Orange: Medium density (> 20 taxis)
            Red: High density (> 35 taxis)
        
        High-Density Markers: Markers highlight areas with very high taxi density.
    
    Each grid cell represents a 0.01° x 0.01° area of the map.
            """)
else:
    st.warning("No taxi data available at the moment.")

# Footer information
st.markdown("""
* Data source: [Singapore Government Taxi Availability API](https://api.data.gov.sg/v1/transport/taxi-availability)
* Data updates every minute.
""")
