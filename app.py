
import ee
import geemap.foliumap as geemap
import streamlit as st
import pandas as pd
from google.oauth2 import service_account

# Ambil dari secrets
service_account_info = st.secrets["earthengine"]

# Tambahkan SCOPES untuk Earth Engine
SCOPES = ['https://www.googleapis.com/auth/earthengine.readonly']

# Buat credentials
credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
    scopes=SCOPES
)

# Inisialisasi Earth Engine
ee.Initialize(credentials)


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


layers = process_all_years(roi, years)

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
    Map.to_streamlit(height=600, width=int(0.8 * 3000))

# Luas Area
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


area_df = calculate_area_table(layers)

st.subheader("Luas Daratan dan Perairan (hektar) per Tahun")
st.dataframe(area_df)

st.subheader("Luasan Darat vs Laut")
chart_df = area_df.melt(id_vars="Year", var_name="Kelas", value_name="Luas (ha)")
st.bar_chart(chart_df.pivot(index="Year", columns="Kelas", values="Luas (ha)"))
