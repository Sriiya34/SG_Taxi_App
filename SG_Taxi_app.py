import streamlit as st
import requests
import folium
from datetime import datetime, timezone, timedelta
from streamlit_folium import st_folium
from folium.plugins import HeatMap
from folium import LayerControl

# Title of the app
st.title("Real-time Taxi Availability in Singapore")
st.markdown("""
This app retrieves and displays real-time taxi availability data from Data.gov.sg. 
Taxis are plotted on an interactive map using GeoJSON data. Areas with more taxis are shown with warmer colors.
""")

# Function to get taxi availability data from the real-time API
@st.cache_data(ttl=60)  # Cache data for 60 seconds
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

    # Creates the map centered on Singapore
    map_center = [1.3521, 103.8198]
    m = folium.Map(location=map_center, zoom_start=12)

    # Add HeatMap layer
    HeatMap(taxi_locations, radius=10, blur=20, min_opacity=0.5).add_to(m)
    LayerControl().add_to(m)

    for location in taxi_locations:
         folium.CircleMarker(location=location, radius=2, color='blue', fill=True).add_to(m)

    # Display the map in Streamlit
    st_folium(m, width=800, height=500)
else:
    st.warning("No taxi data available at the moment.")

# Footer information
st.markdown("""
* Data source: [Singapore Government Taxi Availability API](https://api.data.gov.sg/v1/transport/taxi-availability)
* Data updates every minute.
""")
