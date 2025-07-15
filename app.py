# import ee
# import geemap.foliumap as geemap
# import streamlit as st
# import pandas as pd

# testing = "testing-460608"

# try:
#     ee.Initialize(project=testing)
# except:
#     ee.Authenticate()
#     ee.Initialize(project=testing)

# st.set_page_config(layout="wide")

# roi = ee.Geometry.Rectangle([113.35, -7.22, 113.38, -7.19])
# years = list(range(2015, 2025))

# @st.cache_data(show_spinner="Memproses semua tahun...")
# def process_all_years(_roi, years):
#     layers = []
#     area_data = []

#     for year in years:
#         collection = ee.ImageCollection("COPERNICUS/S2_HARMONIZED") \
#             .filterDate(f'{year}-01-01', f'{year}-12-31') \
#             .filterBounds(_roi) \
#             .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))

#         image = collection.median().clip(_roi)

#         ndwi = image.normalizedDifference(['B3', 'B11']).rename('NDWI') \
#             .updateMask(image.select('B3'))

#         water_mask = ndwi.gt(0)
#         land_mask = ndwi.lte(0)

#         binary_water = water_mask.updateMask(water_mask).rename('class')
#         binary_land = land_mask.updateMask(land_mask).rename('class')

#         water_vector = binary_water.reduceToVectors(
#             geometry=_roi,
#             scale=10,
#             geometryType='polygon',
#             reducer=ee.Reducer.countEvery()
#         ).map(lambda f: f.set('class', 'water').set('year', year))

#         land_vector = binary_land.reduceToVectors(
#             geometry=_roi,
#             scale=10,
#             geometryType='polygon',
#             reducer=ee.Reducer.countEvery()
#         ).map(lambda f: f.set('class', 'land').set('year', year))

#         # Perhitungan luas daratan dan lautan
#         def calculate_area(vector, class_name):
#             area = vector.map(lambda f: f.set('area', f.geometry().area(1))).aggregate_sum('area').getInfo()
#             return area / 1e6  # Convert to km²

#         land_area_km2 = calculate_area(land_vector, 'land')
#         water_area_km2 = calculate_area(water_vector, 'water')

#         area_data.append({
#             'Year': year,
#             'Land Area (km²)': land_area_km2,
#             'Water Area (km²)': water_area_km2
#         })

#         layers.append({
#             'year': year,
#             'water_vector': water_vector,
#             'land_vector': land_vector
#         })

#     return layers, pd.DataFrame(area_data)


# layers, area_df = process_all_years(roi, years)

# # 🗺️ Map Visualization
# Map = geemap.Map(center=[-7.2061, 113.3695], zoom=14)
# Map.add_basemap("SATELLITE")
# Map.addLayer(roi, {"color": "red"}, "ROI")

# for item in layers:
#     year = item['year']
#     Map.addLayer(item['water_vector'], {"color": "blue"}, f"Water {year}")
#     Map.addLayer(item['land_vector'], {"color": "green"}, f"Land {year}")

# Map.to_streamlit(height=800, width=int(0.8 * 1000))

# # 📊 Tabel dan Grafik Luasan
# st.subheader("📌 Luasan Daratan dan Lautan per Tahun")
# st.dataframe(area_df.style.format({'Land Area (km²)': '{:.2f}', 'Water Area (km²)': '{:.2f}'}), use_container_width=True)

# st.subheader("📈 Visualisasi Luasan (km²) per Tahun")
# st.line_chart(area_df.set_index('Year'))


import ee
import geemap.foliumap as geemap
import streamlit as st
import pandas as pd

# Inisialisasi Earth Engine
testing = "testing-460608"

try:
    ee.Initialize(project=testing)
except:
    ee.Authenticate()
    ee.Initialize(project=testing)

st.set_page_config(layout="wide")
st.title("NDWI Tahun 2015, 2020, dan 2024")

# ROI (Region of Interest)
roi = ee.Geometry.Rectangle([113.35, -7.22, 113.38, -7.19])
years = [2015, 2020, 2024]

@st.cache_data(show_spinner="Memproses semua tahun...")
def process_all_years(_roi, years):
    layers = []
    for year in years:
        collection = ee.ImageCollection("COPERNICUS/S2_HARMONIZED") \
            .filterDate(f'{year}-01-01', f'{year}-12-31') \
            .filterBounds(_roi) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))

        image = collection.median().clip(_roi)

        ndwi = image.normalizedDifference(['B3', 'B11']).rename('NDWI') \
            .updateMask(image.select('B3'))

        water_mask = ndwi.gt(0)
        land_mask = ndwi.lte(0)

        binary_water = water_mask.updateMask(water_mask).rename('class')
        binary_land = land_mask.updateMask(land_mask).rename('class')

        water_vector = binary_water.reduceToVectors(
            geometry=_roi,
            scale=10,
            geometryType='polygon',
            reducer=ee.Reducer.countEvery()
        ).map(lambda f: f.set('class', 'water').set('year', year))

        land_vector = binary_land.reduceToVectors(
            geometry=_roi,
            scale=10,
            geometryType='polygon',
            reducer=ee.Reducer.countEvery()
        ).map(lambda f: f.set('class', 'land').set('year', year))

        layers.append({
            'year': year,
            'water_vector': water_vector,
            'land_vector': land_vector
        })

    return layers

# Proses semua tahun
layers = process_all_years(roi, years)

# Tampilkan Peta
Map = geemap.Map(center=[-7.2061, 113.3695], zoom=14)
Map.add_basemap("SATELLITE")
Map.addLayer(roi, {"color": "red"}, "ROI")

for item in layers:
    year = item['year']
    Map.addLayer(item['water_vector'], {"color": "blue"}, f"Water {year}")
    Map.addLayer(item['land_vector'], {"color": "green"}, f"Land {year}")

st.subheader("Visualisasi NDWI Tahun 2015, 2020, dan 2024")
col1, col2 = st.columns([4, 1])  # 80% - 20%
with col1:
    Map.to_streamlit(height=600)

# Hitung Luas Area
@st.cache_data
def calculate_area_table(_layers):
    data = []
    for item in _layers:
        year = item['year']
        water_vector = item['water_vector']
        land_vector = item['land_vector']

        water_area = water_vector \
            .map(lambda f: f.set({'area': f.geometry().area(10)})) \
            .aggregate_sum('area').getInfo() / 1e4  # m² ke ha

        land_area = land_vector \
            .map(lambda f: f.set({'area': f.geometry().area(10)})) \
            .aggregate_sum('area').getInfo() / 1e4  # m² ke ha

        data.append({
            'Year': year,
            'Water Area (ha)': round(water_area, 2),
            'Land Area (ha)': round(land_area, 2)
        })

    return pd.DataFrame(data)

# Tampilkan Luasan Area dan Chart
area_df = calculate_area_table(layers)

st.subheader("Luas Daratan dan Perairan (hektar) per Tahun")
st.dataframe(area_df)

# Visualisasi bar chart
st.subheader("Bar Chart: Luasan Darat vs Laut")
chart_df = area_df.melt(id_vars="Year", var_name="Kelas", value_name="Luas (ha)")
st.bar_chart(chart_df.pivot(index="Year", columns="Kelas", values="Luas (ha)"))
