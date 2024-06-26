import streamlit as st
import geopandas as gpd
import folium
import zipfile
import tempfile
import os

st.title("Geospatial File Viewer")

# Function to read and display KML file
def read_kml(file):
    gdf = gpd.read_file(file, driver='KML')
    return gdf

# Function to read and display ZIP Shape file
def read_zip_shape(file):
    with tempfile.TemporaryDirectory() as tmpdir:
        with zipfile.ZipFile(file, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
            shp_file = [os.path.join(tmpdir, f) for f in os.listdir(tmpdir) if f.endswith('.shp')][0]
            gdf = gpd.read_file(shp_file)
    return gdf

# Function to read and display GeoJSON file
def read_geojson(file):
    gdf = gpd.read_file(file)
    return gdf

# Upload file
uploaded_file = st.file_uploader("Choose a KML, ZIP shape, or GeoJSON file", type=["kml", "zip", "geojson"])

if uploaded_file is not None:
    filename = uploaded_file.name
    if filename.endswith('.kml'):
        gdf = read_kml(uploaded_file)
    elif filename.endswith('.zip'):
        gdf = read_zip_shape(uploaded_file)
    elif filename.endswith('.geojson') or filename.endswith('.json'):
        gdf = read_geojson(uploaded_file)
    else:
        st.error("Unsupported file format")

    if 'gdf' in locals():
        st.write(gdf.head())

        # Calculate the center of the map
        centroid = gdf.geometry.centroid
        mean_lat = centroid.y.mean()
        mean_lon = centroid.x.mean()

        # Display map
        m = folium.Map(location=[mean_lat, mean_lon], zoom_start=10)
        folium.GeoJson(gdf).add_to(m)

        # Render map using Streamlit's HTML renderer
        st.components.v1.html(m._repr_html_(), height=500)
