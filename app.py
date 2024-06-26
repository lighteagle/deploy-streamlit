import streamlit as st
import geopandas as gpd
import folium
import zipfile
import tempfile
import os

st.title("Geospatial File Viewer with Polygon Validation")

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

# Function to check for invalid polygons and add a cause column
def check_invalid_polygons(gdf):
    def get_invalid_reason(geometry):
        try:
            if geometry.geom_type == 'Polygon' and not geometry.is_valid:
                return "Invalid Polygon: Self-intersection detected"
            elif geometry.geom_type == 'Polygon' and geometry.is_empty:
                return "Invalid Polygon: Empty geometry"
            elif geometry.geom_type == 'Polygon':
                return "Invalid Polygon: Unknown reason"
            elif geometry.geom_type == 'MultiPolygon' and not geometry.is_valid:
                return "Invalid MultiPolygon: Invalid components detected"
            elif geometry.geom_type == 'MultiPolygon' and geometry.is_empty:
                return "Invalid MultiPolygon: Empty geometry"
            elif geometry.geom_type == 'MultiPolygon':
                return "Invalid MultiPolygon: Unknown reason"
            else:
                return "Unknown geometry type"
        except Exception as e:
            return f"Error: {str(e)}"
    
    invalid_polygons = gdf[~gdf.is_valid]
    invalid_polygons['invalid_cause'] = invalid_polygons['geometry'].apply(get_invalid_reason)
    return invalid_polygons

# Function to style the DataFrame
def style_dataframe(df):
    styled_df = df.style.set_table_styles([
        {'selector': 'thead th', 'props': [('background-color', '#4CAF50'), ('color', 'white'), ('text-align', 'center')]},
        {'selector': 'td', 'props': [('text-align', 'left')]},
        {'selector': 'tbody tr:nth-child(even)', 'props': [('background-color', '#f2f2f2')]},
        {'selector': 'tbody tr:hover', 'props': [('background-color', '#ddd')]}
    ]).set_properties(**{
        'border': '1px solid black',
        'font-size': '14px',
        'text-align': 'left'
    })
    return styled_df

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
        # Display selected columns excluding 'geometry'
        non_geom_columns = [col for col in gdf.columns if col != 'geometry']
        st.write("### Selected Columns of GeoDataFrame")
        st.dataframe(gdf[non_geom_columns].head(), height=300)

        # Check for invalid polygons
        invalid_polygons = check_invalid_polygons(gdf)
        if not invalid_polygons.empty:
            st.warning(f"Found {len(invalid_polygons)} invalid polygon(s):")
            # Display invalid polygons with cause of invalidity
            invalid_polygons_display = invalid_polygons[non_geom_columns + ['invalid_cause']]
            st.dataframe(style_dataframe(invalid_polygons_display), height=300)
        else:
            st.success("All polygons are valid!")

        # Calculate the center of the map
        centroid = gdf.geometry.centroid
        mean_lat = centroid.y.mean()
        mean_lon = centroid.x.mean()

        # Display map
        m = folium.Map(location=[mean_lat, mean_lon], zoom_start=10)
        folium.GeoJson(gdf).add_to(m)

        # Render map using Streamlit's HTML renderer
        st.components.v1.html(m._repr_html_(), height=500)
