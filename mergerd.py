



# Import necessary libraries
from dash import Dash, html, dcc, dash_table
from dash.dash_table.Format import Format, Scheme  # Updated import path for formatters\
import dash
from dash.dependencies import Input, Output, State
from dash import html
import pandas as pd
import plotly.express as px
from dash import dcc
from dash.dependencies import Output, Input
import plotly.graph_objects as go
import sqlite3 
import gspread
import re
import os
import boto3
from google.oauth2.service_account import Credentials


import dash
import pandas as pd
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash.exceptions
from dash.dcc import send_data_frame
import numpy as np
import calendar
import plotly.express as px
import itertools
import matplotlib.pyplot as plt

from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from geopy.geocoders import Nominatim

import ast
import json
import re
import os
from shapely.geometry import Point, Polygon
import random  # For selecting a random marker
import dash_player
from babel import Locale


from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.client import GoogleCredentials
from google.oauth2 import service_account




import os
"""current_dir = os.path.dirname(__file__)
python_files = [f for f in os.listdir(current_dir) if f.endswith(".py") and f != "app.py" and f != "extraction.py" and f != "extraction_poi.py"]

for script in python_files:
    script_path = os.path.join(current_dir, script)
    print(f"Running {script}...")

    try:
        with open(script_path, "r", encoding="utf-8") as file:
            code = file.read()
        
        exec(code)  # Execute the entire code in the script

    except UnicodeDecodeError as e:
        print(f"Error reading {script}: {e}")
        print("Try converting the file to UTF-8 encoding.")"""



import pandas as pd
import gspread
from google.oauth2.service_account import Credentials


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions= True)
server = app.server  # if you need the Flask server reference


# ✅ Service account and scopes
SERVICE_ACCOUNT_FILE = r"C:\Users\roy\OneDrive\Desktop\ASR JSONS\Geo_Analysis\arabic-transcription-435113-c8120df00a35.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ✅ Authenticate
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)


# ✅ Spreadsheet & sheet names
sheets_to_load = {
    "df": ("1JQ960HoB0VVTskzma3zd3Il7khFTWVbPWTlLT8v6NUU", "Obj_ann_with_total"),
    "df3": ("1ZPcwPcIrGU-brYoGrNLLcjRJbRCNaLfaP3s0shS7ZeI", "output_transcriptions"),
    "coordinates_df": ("1epNqVVLwcG0a5YI0_kgKQa5G6_q6v3F4eWzX4PD4CUg", "Coordinates"),
    "Overall_frames_ann_per_vid": ("1pSjFV6o0PHzuTc2pCqL6uJH1VAJ2DPSbOBMZQPDZoIs", "Overall_ann_od"),
    "ann_per_ob": ("1pSjFV6o0PHzuTc2pCqL6uJH1VAJ2DPSbOBMZQPDZoIs", "Overall_ann_od_per_obj"),
    "otb": ("1SD9vtPyeUwUj366zhRNxlLyegYaLlLca4A7DmT6b020", "OTB2"),
    "attributes": ("15NRg3T2B9jPWEn3HzzNXxOgIYe8U0x8a_Ael28d23vk", "OTB3"),
    "df2": ("1-XZPzpql4o0Flq5WHZf8GjuPoXTY_vVFqkYq9QKOuMU", "POI"),
    "df_voice": ("1LoUYrB_gFCqaMiZ-D31hc4mENCWF42iPvldxi7e2NGU", "800 OG copy"),
    "df_encord_Work_od" : ("1MnK95qghsLCjQDFGboB0r79S0NJwHnQ09cN8LT_t4OM" , "OD Q1"),
    "df_encord_Work_poi" : ("1MnK95qghsLCjQDFGboB0r79S0NJwHnQ09cN8LT_t4OM" , "POI Q1")
}

import time 
import random

def load_sheets(sheet_map, client, max_retries=8, max_backoff=64):
    sheet_dfs = {}
    for key, (spreadsheet_id, sheet_name) in sheet_map.items():
        n = 0  # Retry counter
        while n <= max_retries:
            try:
                worksheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
                data = worksheet.get_all_values()
                if not data or len(data) < 2:
                    print(f"⚠️ Skipping empty sheet: {sheet_name}")
                    sheet_dfs[key] = pd.DataFrame()
                    break

                headers, rows = data[0], data[1:]
                df = pd.DataFrame(rows, columns=headers)
                sheet_dfs[key] = df.apply(pd.to_numeric, errors='ignore')
                print(f"✅ Loaded: {sheet_name}")
                break  # success, exit retry loop

            except Exception as e:
                if '429' in str(e):  # Rate limit error
                    wait_time = min((2 ** n) + random.randint(0, 1000) / 1000.0, max_backoff)
                    print(f"🔁 Rate limit hit. Retrying in {wait_time:.2f}s (attempt {n + 1})...")
                    time.sleep(wait_time)
                    n += 1
                else:
                    print(f"❌ Error loading {sheet_name}: {e}")
                    sheet_dfs[key] = pd.DataFrame()
                    break  # other errors: don't retry

        if n > max_retries:
            print(f"❌ Max retries reached for {sheet_name}. Giving up.")
            sheet_dfs[key] = pd.DataFrame()

    return sheet_dfs

dfs = load_sheets(sheets_to_load, client)

# ✅ Access your DataFrames by name
df = dfs["df"]
df3 = dfs["df3"]
coordinates_df = dfs["coordinates_df"]
Overall_frames_ann_per_vid = dfs["Overall_frames_ann_per_vid"]
ann_per_ob = dfs["ann_per_ob"]
otb = dfs["otb"]
attributes = dfs["attributes"]
df2 = dfs["df2"]
df_voice = dfs["df_voice"]
df_work_od = dfs["df_encord_Work_od"]
df_work_poi = dfs["df_encord_Work_poi"]

# ✅ Total column & merge
df["Total_per_video"] = df.select_dtypes(include="number").sum(axis=1)

joined_df3 = pd.merge(otb, attributes, left_on='Object_Hash', right_on='object_hash', how='left')
columns_to_drop = ["video_name", "object_hash", "Blurring", "Truncation", "Occlusion"]
joined_df3 = joined_df3.drop(columns=[c for c in columns_to_drop if c in joined_df3.columns])
joined_df3 = joined_df3.drop_duplicates()


# ✅ Upload to Google Sheets
def upload_to_google_sheets(df, spreadsheet_id, sheet_name):
    try:
        df = df.replace([float('inf'), float('-inf')], 0).fillna("")
        sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
        sheet.clear()
        sheet.update([df.columns.tolist()] + df.values.tolist())
        print(f"✅ Uploaded to {sheet_name}")
    except Exception as e:
        print(f"❌ Upload failed: {e}")

upload_to_google_sheets(joined_df3, sheets_to_load["df"][0], "Merged_Data")

# ✅ Sort & done
df = df.sort_values(by='Total_per_video', ascending=False)

df_top = df
df_filt = df.iloc[:1 , : ].reset_index()
df_gauge_sum = df_filt["Total_per_video"]
df_filtered = df.iloc[1: , : ].reset_index()
transposed_df = df.set_index('Video Name').T
transposed_df_obj_ann = ann_per_ob.set_index('Object Name').T
att_sum = pd.read_csv("instances_for_attributes.csv")
att_sum = att_sum.sort_values(by='Count', ascending=False)
black = attributes["Black"].dropna().ne("").sum()
blue = attributes["Blue"].dropna().ne("").sum()
white = attributes["White"].dropna().ne("").sum()
red = attributes["Red"].dropna().ne("").sum()
gray = attributes["Gray"].dropna().ne("").sum()
yellow = attributes["Yellow"].dropna().ne("").sum()
green = attributes["Green"].dropna().ne("").sum()
brown = attributes["Brown"].dropna().ne("").sum()
purple = attributes["Purple"].dropna().ne("").sum()
pink = attributes["Pink"].dropna().ne("").sum()
columns_to_drop = ['occlusion_count', 'truncation_count', 'blur_count', 'Yes', 'Not Visible', 'Not visible', 'Not Sure' , 'Occlusion ' , 'None']
OD_ATT = joined_df3.drop(columns=columns_to_drop)
OD_ATT = OD_ATT.fillna("")
OD_ATT = OD_ATT.replace("none" , "")
OD_ATT_FILT_cols = ["Video Name" , "object_name" , "Object_Hash", "No" , "Partial"]
OD_ATT_FILT = OD_ATT.drop (columns = OD_ATT_FILT_cols)
snips_df = pd.read_csv("snippets_metadata.csv")
# ✅ Store results in a dictionary
colors_data = {
    "Black": black, 
    "Blue": blue,
    "White": white,
    "Red": red,
    "Gray": gray,
    "Yellow": yellow,
    "Green": green,
    "Brown": brown,
    "Purple": purple,
    "Pink": pink,
}

styles = {
    "content": {
        "width": "100%",
        "background": "#F7F7F7"
    },
    "right_content": {
        "width": "85%",
        "position": "absolute",
        "top": "0",
        "right": "0"
    },
    "top_metrics": {
        "background": "#EAEAEA",
        "height": "200px",
        "width": "85%",
        "position": "absolute",
        "top": "0",
        "right": "0"
    },
    "left_menu": {
        "width": "15%",
        "position": "absolute",
        "top": "0",
        "left": "0",
        "height": "100vh",
        "z-index": "999",
        "background": "#2A3F54"
    }
}

colors_df = pd.DataFrame(list(colors_data.items()), columns=["Color Name", "Count"])

df2 = df2.sort_values(by='Overall Frames Annotated', ascending=False)
objects = transposed_df.columns[0]
df2 = df2.head(16)
sum_of_nlp_audio = pd.to_numeric(df3["video_length_secs"], errors='coerce').sum() / 3600
sum_of_nlp_audio_hour = int(sum_of_nlp_audio)
sum_of_nlp_audio_min = int((sum_of_nlp_audio - sum_of_nlp_audio_hour) * 1000)
sum_of_size = df3["size_in_mb"].sum()

sum_of_blurry = df2["Blurry"].sum()
sum_of_acceptable = df2["Blur (Acceptable)"].sum()
sum_of_occluded = df2["Partially Occluded"].sum()
partially_occluded = df2["Not Occluded"].sum()
total_ann = df2["Overall Frames Annotated"].sum()
occluded = joined_df3["occlusion_count"].sum()
truncated = joined_df3["truncation_count"].sum()
blurry = joined_df3["blur_count"].sum()

Overall_ann = Overall_frames_ann_per_vid["bounding_boxes_count"].sum()
Not_oc = int(Overall_ann) - int(occluded)
Not_trun = int(Overall_ann) - int(truncated)
Not_bl = int(Overall_ann) - int(blurry)
Trunc_df_od = { 
    "truncation_count": truncated,
    "Not_truncated" : Not_trun
}

Blur_df_od = {
    "blurry": blurry,
    "acceptable": Not_bl
}

Oc_df_od = {
    "partially_occluded": occluded,
    "not_occluded": Not_oc
    
} 

blur_df = {
    "blurry": sum_of_blurry,
    "acceptable": sum_of_acceptable
}

occluded_df = {
    "occluded": sum_of_occluded,
    "partially_occluded": partially_occluded
}


colors = {
    'background': '#e8f5f1',
    'text': '#1f1f1f'
}


update_log_button ={
    "width": "100%",
    "height": "60px",
    "margin": "30px",
    "background-color": '#F0FFF0',
    "border": "2px solid white",
    "display": "block",
    "font-weight": "bold",
    "color": "#ff1493",
    "borderRadius": "50px",   
}

# Dropdown Style
dropdown_style = {
    'width': '50%',
    'margin': '0 auto',
    'backgroundColor': colors['background'],
    'color': colors['text'],
    'border': '1px solid #333',
    'borderRadius': '8px',
    'padding': '5px',
}

# Tabs Style
tabs_styles = {
    'backgroundColor': colors['background'],
    'color': colors['text'],
    'padding': '10px',
    'fontFamily': 'Arial, sans-serif'
}
colors_tab = {
    'background': '#111111',
    'text': '#7FDBFF',
    'tab': '#222222',
    'tab_selected': '#444444',
    'card_bg': '#222831',
    'card_shadow': '2px 2px 10px rgba(0,0,0,0.2)',
}

tab_style = {
    'backgroundColor': tabs_styles['backgroundColor'],
    'color': '809C94',
    'padding': '10px',
    'borderRadius': '5px',
    'margin': '2px'
}

selected_tab_style = {
    'backgroundColor': tabs_styles['backgroundColor'],
    'color': '375048',
    'padding': '10px',
    'borderRadius': '5px',
    'margin': '2px',
    'fontWeight': 'bold'
}
text_style = {
    'color': colors['text'],
    'fontWeight': 'bold',
    'fontSize': '18px'
}

vid_count = joined_df3["Video Name"].nunique() + 1
total_frames_ann = Overall_frames_ann_per_vid["bounding_boxes_count"].sum()


query = """
SELECT *
FROM nlp_data
WHERE override_translation LIKE  ''
"""



geolocator = Nominatim(user_agent="myGeocoder")



# Path to your service account key file
SERVICE_ACCOUNT_FILE = r"C:\Users\roy\OneDrive\Desktop\ASR JSONS\Geo_Analysis\arabic-transcription-435113-c8120df00a35.json"

# Authenticate and connect to the Sheets API
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


#SERVICE_ACCOUNT_FILE = r"C:\Users\roy\OneDrive\Desktop\ASR JSONS\Geo_Analysis\arabic-transcription-435113-c5acf93c0185.json"

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate using Service Account
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Drive API service
drive_service = build('drive', 'v3', credentials=creds)


# Define color maps
color_map_city = {
    'Youtube': 'rgb(255,0,0)',
    'TikTok': 'rgb(255,182,193)',
    'Tik Tok': 'rgb(255,182,193)',
    'facebook': 'rgb(30,144,255)',
    'Facebook': 'rgb(30,144,255)',
    'other': 'rgb(112,128,144)',
    'Instegram': 'rgb(112,128,144)',
    'Instagram': 'green',
    
}
color_map2_city = {
    'Night Time': 'rgb(1, 1, 1)',      # Black
    ' Day Time': '#FFD700'
}
color_map3_city = {
    'Clear': 'rgb(135,206,235)',
    'Snow': 'rgb(255,250,250)',
    'Rain': 'rgb(123,104,238)',
    'Fog or Smoke': 'rgb(128,128,128)'
}

color_map4_city = {
    'Prominent' : 'rgb(236, 255, 0)',
    'None': 'rgb(255,250,250)',
    'slight': 'rgb(135,206,235)'
}


# Define background style
background_style_city = {
    "background-size": "cover",
    "background-position": "center",
    "height": "350vh",
    "padding": "10px",
    "background-color": 'black',
}
# Common styles
container_style = {
    "background-color": "black",
    "border-radius": "50px",
    "padding": "15px",
    "box-shadow": "0px 8px 20px rgba(0, 0, 0, 0.3)",
    "width": "150%",
    "max-width": "2000px",
    "margin": "0 auto",
}
background_style = {
    "background-size": "cover",
    "background-color": 'black',
    "background-position": "center",
    "height": "250vh",
    "padding": "10px",
}

button_style_city = {
    "width": "50%",
    "height": "60px",
    "margin": "30px",
    "background-color": '#F5F5DC',
    "border": "2px solid black",
    "display": "block",
    "font-weight": "bold",
    "color": "#ff1493",
    "borderRadius": "50px",
}

insert_button = {
    "width": "50%",
    "height": "60px",
    "margin": "30px",
    "background-color": '#F5F5DC',
    "border": "2px solid black",
    "display": "flex",  # changed from block to flex
    "justify-content": "center",  # centers horizontally
    "align-items": "center",      # centers vertically
    "font-weight": "bold",
    "font-size": '38px',
    "color": "#ff1493",
    "borderRadius": "50px",
}


button_search = {
    "width": "100%",
    "height": "60px",
    "margin": "30px",
    "background-color": '#faf0e6',
    "border": "2px solid black",
    "display": "block",
    "font-weight": "bold",
    "color": "#ff1493",
    "borderRadius": "50px",
}

export_button ={
    "width": "90%",
    "height": "60px",
    "margin": "30px",
    "background-color": '#F5DEB3',
    "border": "2px solid black",
    "display": "block",
    "font-weight": "bold",
    "color": "#ff1493",
    "borderRadius": "50px",   
}

update_log_button ={
    "width": "100%",
    "height": "60px",
    "margin": "30px",
    "background-color": '#F0FFF0',
    "border": "2px solid black",
    "display": "block",
    "font-weight": "bold",
    "color": "#ff1493",
    "borderRadius": "50px",   
}

button_check = {
    "width": "30%",
    "height": "60px",
    "margin": "-60px 0px 0px 1550px",
    "background-color": '#fff6d2',
    "border": "2px solid black",
    "display": "block",
    "font-weight": "bold",
    "color": "#ff1493",
    "borderRadius": "50px",
}

button_dropouts = {
    "width": "30%",
    "height": "60px",
    "margin": "-50px 0px 0px 1300px",
    "background-color": '#c4b69e',
    "border": "2px solid black",
    "display": "block",
    "font-weight": "bold",
    "color": "#ff1493",
    "borderRadius": "50px",    
}

button_clear = {
    "width": "100%",
    "height": "60px",
    "margin": "30px",
    "background-color": 'white',
    "border": "2px solid black",
    "display": "block",
    "font-weight": "bold",
    "color": "red",
    "borderRadius": "50px",    
}

button_style15 = {
    "width": "150%",
    "height": "60px",
    "margin": "30px -5px",
    "background-color": '#dbd2c3',
    "border": "2px solid black",
    "display": "block",
    "font-weight": "bold",
    "color": "rgb(255,51,153)",
    "borderRadius": "50px",   
}

font_style = {
    "color": "white",
    "size": "25px",
    'font-weight': 'bold'
}

gen_sum_font_style = {
    "color": "white",
    "font-size": "26px",
    'font-weight': 'bold'
}

modal_style = {
    "color": "black",
    "size": "36px",
    'font-weight': 'bold'
}

# Function to load a city's data from Google Sheets
def load_city(sheet_id, sheet_range):
    result = sheet.values().get(spreadsheetId=sheet_id, range=sheet_range).execute()
    values = result.get('values', [])
    if values:
        headers = values[0]
        data = values[1:]
        df_city = pd.DataFrame(data, columns=headers)
    else:
        df_city = pd.DataFrame()
    return df_city

def get_country_name_in_english(local_name):
    # First, check if it's already the English name
    for code, english_name in Locale('en').territories.items():
        if english_name.lower() == local_name.lower():
            return english_name  # Already English, return as-is

    # Try to translate from other known locales
    for country_code in Locale('en').territories:
        for lang in ['es', 'hu', 'fr', 'de', 'it', 'pt']:  # Add more locales if needed
            loc = Locale(lang)
            translated = loc.territories.get(country_code)
            if translated and translated.lower() == local_name.lower():
                return Locale('en').territories.get(country_code)
    
    return None

def extract_last_word_if_single(text):
    last_part = text.split('-')[-1].strip()
    if ',' not in last_part and len(last_part.split()) == 1:
        return last_part
    return None

def convert_to_minutes(duration):
    try:
        parts = list(map(int, duration.split(':')))
        if len(parts) == 2:  # mm:ss format
            minutes, seconds = parts
            total_minutes = round(minutes + seconds / 60,2)
        elif len(parts) == 3:  # h:mm:ss format
            hours, minutes, seconds = parts
            total_minutes = round(hours * 60 + minutes + seconds / 60,2)
        else:
            return None  # Invalid format
        return total_minutes  # Convert total seconds to minutes
    except (ValueError, AttributeError):
        return None  # Handle invalid inputs

def is_valid_coordinate(value):
    if isinstance(value, tuple) and len(value) == 2:
        try:
            lat, lon = float(value[0]), float(value[1])
            return -90 <= lat <= 90 and -180 <= lon <= 180
        except ValueError:
            return False
    
    elif isinstance(value, str):
        pattern = r"""
            ^\s*([-+]?(?:\d*\.\d+|\d+))\s*,\s*([-+]?(?:\d*\.\d+|\d+))\s*$
        """
        matches = re.match(pattern, value.strip(), re.VERBOSE)
        
        if not matches:
            return False
        
        lat, lon = float(matches.group(1)), float(matches.group(2))
        return -90 <= lat <= 90 and -180 <= lon <= 180
    
    return False

def float_to_mm_ss(time_float):
    total_seconds = int(time_float * 60)  # Convert fraction of a minute to total seconds
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes:02d}:{seconds:02d}"

def is_valid_coord(coord_str):
    numbers = re.findall(r'[-+]?\d*\.\d+|[-+]?\d+', str(coord_str))
    return len(numbers) >= 2

def clean_coordinate(coord_str: str) -> str:
    # Extract numbers (handles both integers and floats, including optional + or -)
    numbers = re.findall(r'[-+]?\d*\.\d+|[-+]?\d+', coord_str)
    if len(numbers) < 2:
        raise ValueError("Not enough coordinate numbers found in the input.")
    # Return the first two numbers separated by a comma
    return f"{numbers[0]},{numbers[1]}"

def apply_all_filters2(
    df,
    duration_range,
    selected_terrain,
    selected_occluded,
    selected_VQ,
    selected_tilt,
    selected_distance,
    selected_distortions,
    bar_weather_clickData,
    pie_clickData,
    pie_2_clickData,
    bar_2_clickData,
    polygon_active
):
    # Ensure the Duration column exists
    if 'Duration' not in df.columns and 'Finish Time' in df.columns and 'Start Time' in df.columns:
        df['Duration'] = df['Finish Time'].apply(convert_to_minutes) - df['Start Time'].apply(convert_to_minutes)
    
    # Apply the range filter on Duration
    if duration_range:
        df = df[(df['Duration'] >= duration_range[0]) & (df['Duration'] <= duration_range[1])]
    
    # Then apply each dropdown filter (skip if value is 'All')
    if selected_terrain != 'All':
        df = df[df['Terrain'].notna() & (df['Terrain'] == selected_terrain)]
    if selected_occluded != 'All':
        df = df[df['Occluded'].notna() & (df['Occluded'] == selected_occluded)]
    if selected_VQ != 'All':
        df = df[df['Video quality'].notna() & (df['Video quality'] == selected_VQ)]
    if selected_tilt != 'All':
        df = df[df['Camera tilt'].notna() & (df['Camera tilt'] == selected_tilt)]
    if selected_distance != 'All':
        df = df[df['Distance from building'].notna() & (df['Distance from building'] == selected_distance)]
    if selected_distortions != 'All':
        df = df[df['Distortions'].notna() & (df['Distortions'] == selected_distortions)]

    # Now apply bar_clickData / pie_clickData filters
    if bar_weather_clickData:
        clicked_weather = bar_weather_clickData['points'][0]['y']
        df = df[df['Weather'] == clicked_weather]
    if pie_clickData:
        clicked_time_of_day = pie_clickData['points'][0]['label']
        df = df[df['Time of the day'] == clicked_time_of_day]
    if pie_2_clickData:
        clicked_source = pie_2_clickData['points'][0]['label']
        df = df[df['Source'] == clicked_source]
    if bar_2_clickData:
        clicked_logos = bar_2_clickData['points'][0]['x']
        df = df[df['Logos and text'] == clicked_logos]
    return df


def create_map_markers(df):
    """Generate a list of Dash Leaflet Markers from the DataFrame's lat/lon."""
    markers = []
    for i, row in df.iterrows():
        coord = row['Coordinates']
        if isinstance(coord, str) and ',' in coord.lower() and 'not found' not in coord.lower():
            try:
                lat, lon = coord.split(',')
                lat, lon = float(lat), float(lon)
                markers.append(
                    dl.Marker(
                        position=(lat, lon),
                        children=[dl.Popup(coord)],
                        id=f"city-mark-{i}"
                    )
                )
            except ValueError:
                pass  # skip invalid coords
    return markers

def generate_interactive_countries_compaered_bar_plot(df): 
    # Group by the combined city-country and sum the records.
    city_country_records = df.groupby('City')['Records'].sum().reset_index()
    
    # Select the top 5 cities by the Records sum.
    city_country_records = city_country_records.nlargest(5, 'Records')
    
    # Calculate the percentage contribution of each city's records.
    city_country_records['Percentage'] = (city_country_records['Records'] / city_country_records['Records'].sum()) * 100

    # Create an interactive bar plot using Plotly Express.
    fig = px.bar(
        city_country_records,
        x='City',
        y='Records',
        color='City',  # This uses the available column for coloring.
        color_discrete_map=color_map4_city,
        title='Top 5 Cities by Records',
        text=city_country_records['Records']
    )

    # Customize the plot's appearance.
    fig.update_traces(
        marker_line_width=1.5,
        hovertemplate="Records: %{y}<br>Percentage: %{text}",
        textposition='outside',
        textfont=dict(size=20)
    )

    fig.update_layout(
        xaxis_title="City",
        yaxis_title="Records",
        showlegend=False,
        hovermode="x unified",
        font=dict(size=20, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white'),
        xaxis=dict(
            color='white',
            gridcolor='gray',
            showgrid=False,
            zeroline=False,
            title_font=dict(color='white',size=28),
            tickfont=dict(color='white')
        ),
        yaxis=dict(
            color='yellow',
            gridcolor='gray',
            showgrid=False,
            zeroline=False,
            title_font=dict(color='white'),
            tickfont=dict(color='white'),
            range=[0, 1.25 * city_country_records['Records'].max()]
        ),
        hoverlabel=dict(font=dict(size=24, color='white'))
    )

    return fig


def generate_interactive_bar_plot_2_city(df):
    source_counts = df['Logos and text'].value_counts().reset_index()
    source_counts.columns = ['Logos and text', 'Count']
    source_counts['Percentage'] = (source_counts['Count'] / source_counts['Count'].sum()) * 100
    
    fig = px.bar(
        source_counts, 
        x='Logos and text', 
        y='Count', 
        color='Logos and text', 
        color_discrete_map=color_map4_city,
        title='Logos & Text',
        text=source_counts['Count'].apply(lambda x: f'{x}'),  
        custom_data=['Percentage']   
        
    )
    
    fig.update_traces(
        marker_line_width=1.5,
        hovertemplate=(
            "Count: %{y}<br>"
            "Percentage: %{customdata[0]:.2f}%"
        ),
        textposition='outside',
        textfont=dict(size=24),
    )
    
    fig.update_layout(
        xaxis_title="Logos and text", 
        yaxis_title="Count", 
        showlegend=False,
        hovermode="x unified",
        font=dict(size=20, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white'),
        xaxis=dict(
            color='white',
            gridcolor='gray',
            showgrid=False,  # Hide x-axis grid lines
            zeroline=False,  # Hide zero line
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white')
        ),
        yaxis=dict(
            color='yellow',
            gridcolor='gray',
            showgrid=False,  # Hide x-axis grid lines
            zeroline=False,  # Hide zero line
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white'),
            range=[0, 1.25*(source_counts['Count'].max())]
        ),
        hoverlabel=dict(font=dict(size=24, color='white'))
    )
    
    return fig


def generate_interactive_pie_chart_city(df):
    tod_counts = df['Time of the day'].value_counts().reset_index()
    tod_counts.columns = ['Time of the day', 'Count']
    fig = px.pie(
        tod_counts,
        names='Time of the day',
        values='Count',
        color='Time of the day',
        color_discrete_map=color_map2_city,
        title='Time'
    )
    fig.update_traces(
        marker=dict(line=dict(color='white', width=2)),
        textinfo='label+percent',
        textfont=dict(color='white', size=22)
    )
    fig.update_layout(
        showlegend=False,
        hovermode="x unified",
        margin=dict(t=40, b=20, l=0, r=0),
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white', size=24, ),
        hoverlabel=dict(font=dict(size=24, color='white'))
    )
    return fig

def generate_interactive_bar_chart_weather_city(df):
    weather_counts = df['Weather'].value_counts().reset_index()
    weather_counts.columns = ['Weather', 'Count']
    weather_counts['Percentage'] = (weather_counts['Count'] / weather_counts['Count'].sum()) * 100
    
    fig = px.bar(
        weather_counts,
        y='Weather',
        x='Count',
        orientation='h',
        color='Weather',
        color_discrete_map=color_map3_city,
        title='Weather',
        text=weather_counts['Count'].apply(lambda x: f'{x}'),
        custom_data=['Percentage']  
    )
    
    fig.update_traces(
        marker_line_width=1.5,
        hovertemplate="Count: %{x}<br>Percentage: %{customdata[0]:.2f}%",
        textposition='outside',
        textfont=dict(size=22)
    )
    
    fig.update_layout(
        xaxis_title="Count",
        yaxis_title="Weather",
        showlegend=False,
        hovermode="y unified",
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white', size=24),
        xaxis=dict(
            color='yellow',
            gridcolor='gray',
            showgrid=False,  # Hide x-axis grid lines
            zeroline=False,  # Hide zero line
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white'),
            range=[0, 1.25*(weather_counts['Count'].max())]  # Adjusted range calculation
        ),
        yaxis=dict(
            color='white',
            gridcolor='gray',
            zerolinecolor='gray',
            showgrid=False,  # Hide x-axis grid lines
            zeroline=False,  # Hide zero line
            title_font=dict(color='white'),
            tickfont=dict(color='white')
        ),
        margin=dict(t=40, b=20, l=0, r=0),
        hoverlabel=dict(font=dict(size=24, color='white'))
    )
    
    return fig


import plotly.express as px

def generate_interactive_pie_chart_source(df):
    color_map = {
        'Youtube': '#FF0000',
        'Tiktok': '#FFB6C1',
        'Telegram': '#87CEEB',
        'facebook': '#0000CD',
        'Instegram': '#c13584',
        'other':'#F5DEB3'
    }
    
    source_counts = df['Source'].value_counts().reset_index()
    source_counts.columns = ['Source', 'Count']
    
    fig = px.pie(
        source_counts,
        names='Source',
        values='Count',
        color='Source',
        color_discrete_map=color_map,
        title='Source'
    )
    
    fig.update_traces(
        marker=dict(line=dict(color='white', width=2)),
        textinfo='label+percent',  # Added percent here
        textfont=dict(color='white', size=22)
    )
    
    fig.update_layout(
        showlegend=False,
        hovermode="x unified",
        margin=dict(t=40, b=20, l=0, r=0),
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white', size=24),
        hoverlabel=dict(font=dict(size=24, color='white'))
    )
    
    return fig


def city_load_data():
    SHEET_ID = '1Svc-2iK5wvHFicmBZHoOxqf5iajdg57ntilgR_cM3ZE'
    RANGE = 'Cities!A1:E300'
    result = sheet.values().get(spreadsheetId=SHEET_ID, range=RANGE).execute()
    values = result.get('values', [])
    if values:
        headers_n = values[0]
        data_n = values[1:]
        df_Cities = pd.DataFrame(data_n, columns=headers_n)
    else:
        print("No data found for Naples.")
        df_Cities = pd.DataFrame()
    return df_Cities

global cities
cities = city_load_data()
states = cities['Country'].unique()
states= ['All Countries'] + list(states)

@app.callback([
    Output('city_filter', 'options'),
    Output('city_filter', 'value'),],
[
    Input('state_filter', 'value'),
]
)
def update_city_data(selected_country, current_city_options=None):

    # For other selections, initialize the current list if not provided.
    if current_city_options is None:
        current_city_options = []

    # Get cities based on the selected country or list of countries.
    if (isinstance(selected_country, str) and selected_country == "All Countries") or \
       (isinstance(selected_country, list) and "All Countries" in selected_country):
        new_cities = list(cities['City Name'].unique())
    else:
        # If multiple countries are selected (and not "All Countries"), filter using isin().
        if isinstance(selected_country, list):
            new_cities = list(cities[cities['Country'].isin(selected_country)]['City Name'].unique())
        else:
            # For a single country selection, filter directly.
            new_cities = list(cities[cities['Country'] == selected_country]['City Name'].unique())

    # Remove "All Cities" from the current list if present.
    if current_city_options and current_city_options[0] == "All Cities":
        current_cities = current_city_options[1:]
    else:
        current_cities = current_city_options

    # Merge new cities with the current list, avoiding duplicates.
    updated_cities = current_cities.copy()
    for city in new_cities:
        if city not in updated_cities:
            updated_cities.append(city)

    # Add "All Cities" as the first option.
    updated_options = ["All Cities"] + updated_cities

    # Set a default value.
    city_value = 'All Cities' if len(updated_options) > 1 else None

    return updated_options, city_value




def tab_layout():
    return html.Div(
        style=background_style,
        children=[  
            html.Img(
                src="/assets/airis.png", 
                alt="Airis Logo", 
                style={
                    "width": "200px", 
                    "position": "absolute",  
                    "top": "80px",          
                    "left": "10px",         
                    "zIndex": "1000"        
                }
            ), 
            dcc.Store(id='data', data=None),
            dcc.Store(id='current-city-data', data=None),
            dcc.Store('polygon_drop_active', data=False),
            dcc.Store(id='polygon-coords-store', data=None),
            dcc.Store(id='reset_button_clicked', data=False),
            dcc.Store(id='load_button_clicked', data=False),
            dcc.Store(id='filter_comp_store', data=None),
            dcc.Store(id='original_total',data=None),
            dcc.Store(id='last-clicked-labels', data=None),
            dcc.Store(id='city_records_df', data=None),

            dbc.Container(
                style=container_style,
                children=[
                    html.H1(
                        children=f"Airis-Labs: Geo-Location Analysis",
                        className='mb-4',
                        style={'textAlign': 'center', 'color': 'rgb(255,51,153)'},
                        id='city_name'
                    ),
                    dbc.Row([
                        dbc.Col([
                            dl.Map(
                                id='map',
                                children=[
                                    dl.TileLayer(),
                                    dl.LayerGroup(id="map-layer", children=[]),
                                    dl.LayerGroup(id="polygon-layer", children=[]),
                                ],
                                center=(41.9028, 12.4964),  
                                zoom=10,
                                style={"width": "100%", "height": "500px", "margin": "6px","border": "2px solid black"}
                            ),
                            dbc.Row([
                                dbc.Col(
                                    html.Div([
                                        dbc.Label("Select A Country:", style=font_style),
                                        dcc.Dropdown(
                                            id='state_filter',
                                            options=[{'label': r, 'value': r} for r in states],
                                            value='All Countries',
                                            className="form-control mb-2",
                                            multi=True,
                                        )
                                    ]), width=4
                                ),
                                dbc.Col(
                                    html.Div([
                                        dbc.Label("Select Cities:", style=font_style),
                                        dcc.Dropdown(
                                            id='city_filter',
                                            options=[],
                                            value=[], 
                                            multi=True,
                                            searchable=True,
                                            className="form-control mb-2",
                                        )
                                    ]), width=4
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "Load",
                                        id='city-filter-btn',
                                        color='primary',
                                        n_clicks=0,
                                        style=button_style_city
                                    ),
                                    width=4
                                )  
                            ])
                        ], width=6),                 
                        
                        dbc.Col([
                            dbc.Row([
                                dbc.Col([
                                    html.Div([
                                        html.H4("Filters", className='mb-3', style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}),
                                        dbc.Label("Terrain Filtering:", style=font_style),
                                        dcc.Dropdown(id='Terrain', options=[], value=None, className="form-control mb-2"),
                                        dbc.Label("Camera Tilt Filtering:", style=font_style),
                                        dcc.Dropdown(id='Camera_Tilt', options=[], value=None, className="form-control mb-2"),
                                        dbc.Label("Occlusion Filtering:", style=font_style),
                                        dcc.Dropdown(id='Occlusion', options=[], value=None, className="form-control mb-2"),
                                        dbc.Label("Video Quality Filtering:", style=font_style),
                                        dcc.Dropdown(id='VQ', options=[], value=None, className="form-control mb-2"),
                                        dbc.Label("Distance Filtering:", style=font_style),
                                        dcc.Dropdown(id='Distance_Building', options=[], value=None, className="form-control mb-2"),
                                        dbc.Label("Distortion Filtering:", style=font_style),
                                        dcc.Dropdown(id='Distortions', options=[], value=None, className="form-control mb-2"),                                        
                                        dbc.Row([
                                            dbc.Col(dbc.Button("Update DB & Reset Filters", id='update', color='primary', n_clicks=0, style=button_style15), width="auto"),
                                        ]),
                                    ], style={"marginBottom": "30px"}),
                                ], width=4),
                                dbc.Col([
                                    html.Div([
                                        html.H4("Filter/City Comparison:", className='mb-4', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}),
                                        html.Br(),
                                        dash_table.DataTable(
                                            id='filter_comp',
                                            columns=[
                                                {"name": "Filters", "id": "Filters"},
                                                {"name": "Values", "id": "fvalue"},
                                                {"name": "City", "id": "City"},
                                                {"name": "%", "id": "Percentage"},
                                                {"name": "Total", "id": "total"},
                                                
                                            ],
                                            data=[],
                                            sort_action="native",
                                            filter_action="native",
                                            fixed_rows={'headers': True},
                                            style_table={'maxHeight': '500px', 'overflowX': 'auto', 'overflowY': 'auto'},
                                            style_cell={
                                                'textAlign': 'center',
                                                'width': '30px',
                                                'maxWidth': '30px',
                                                'whiteSpace': 'wrap',
                                                'overflow': 'hidden',
                                                'textOverflow': 'ellipsis',
                                            },
                                            style_header={
                                                'backgroundColor': 'rgb(30, 30, 30)',
                                                'color': 'white',
                                                'fontWeight': 'bold',
                                            },
                                            style_data_conditional=[]
                                        ),
                                html.Div([
                                        dbc.Row([
                                            dbc.Col(
                                                dbc.Button(
                                                    "Clear Filters Table",
                                                    id='clear_table',
                                                    color='primary',
                                                    n_clicks=0,
                                                    style=button_clear
                                                ),
                                                width=4
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    "Update&Reset Log",
                                                    id='update_log',
                                                    color='primary',
                                                    n_clicks=0,
                                                    style=update_log_button
                                                ),
                                                width=4
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    "Export Filters Log",
                                                    id='export_log',
                                                    color='primary',
                                                    n_clicks=0,
                                                    style=export_button
                                                ),
                                                width=4
                                            ),

                                            ])
                                ],style={"textAlign": "center", "marginTop": "10px"}
                                    ),
                                dcc.Download(id="download-component")
                                    ]),  
                                ], width=8),
                            ]),
                        ], width=6),
                    ]),
                    dbc.Col(
                        [
                            dbc.Label("Search for a coordinate:", style={'font-size': '36px', 'font-weight': 'bold'}),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.Dropdown(id='search_input', options=[],placeholder="Insert a coordinate",
                                                     multi=True, value=None, className="form-control mb-2"),
                                        width=6,  # Adjust width as needed
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "Search",
                                            id='search_coord',
                                            color='primary',
                                            n_clicks=0,
                                            style=button_search
                                        ),
                                        width="auto"  # Makes button width auto-adjust
                                    ),

                                ],
                                align="center",
                            ),
                        ],
                        width=6
                    ),
                    html.H1(
                        id='record-count',
                        children="Total Records: 0",
                        style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    html.Br(),
                    html.H1(
                        id='total_cities',
                        children=f"Total Cities : 0",
                        style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    html.Br(),
                    html.H2(
                        id='drop-pre',
                        children=f"0% out of Poylgon",
                        style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    dbc.Col([
                        dbc.Button(
                            "Show Dropouts",
                            id='dropouts',
                            color='primary',
                            n_clicks=0,
                            style=button_dropouts
                        ),
                        dbc.Button(
                            "Is it in Polygon?",
                            id='check',
                            color='primary',
                            n_clicks=0,
                            style=button_check
                        )],
                        width=4
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader("Enter a Coordinate"),
                            dbc.ModalBody(
                                dbc.Input(
                                    id="coord_modal",
                                    type="text",
                                    placeholder="Enter a value...",
                                )
                            ),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Check",
                                    id="modal-check",
                                    color="primary",
                                    className="ml-auto"
                                ),
                            ),
                        ],
                        id="input-modal",
                        is_open=False,  # Initially closed
                    ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader("Confirmation"),
                            dbc.ModalBody(
                                html.Div(id="confirmation-message",style=modal_style)  # Displays user input
                            ),
                        ],
                        id="confirmation-modal",
                        is_open=False,  # Initially closed
                    ),
                     
                    html.Br(),
                    html.H3("Filter by Video Duration (minutes):", className='mb-1', style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}),
                    dbc.Row([
                        dbc.Col(
                            dcc.RangeSlider(
                                id='duration-slider',
                                min=0,
                                max=100,
                                step=0.05,
                                value=[0, 100],
                                updatemode='mouseup',
                                marks={},
                                tooltip={"always_visible": True, "placement": "bottom"}
                            ), width=5
                        )
                    ], justify="left"),
                    
                    html.Div([
                        html.H1("Graphical Analysis", className='mb-3', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}), 
                        html.Br(),
                        html.Br(),    
                        html.Br(),         
                        html.Div(
                            id="graphs-container",
                            style={"display": "none"},  
                            children=[
                                dbc.Row([
                                    dbc.Col(dcc.Graph(id='pie-chart', figure={}), width=6),
                                    dbc.Col(dcc.Graph(id='bar-chart-weather', figure={}), width=6),
                                    html.Div(style={'marginTop': '150px'}),
                                    dbc.Col(dcc.Graph(id='bar-plot-logos', figure={}), width=6),
                                    dbc.Col(dcc.Graph(id='source-pie', figure={}), width=6),
                                    dbc.Col(dcc.Graph(id='compare-bar', figure={}), width=12,style={}),
                                    html.Hr(),
                                    html.Br(),
                                ]),
                            ],
                        ),
                    ], style={'marginTop': '20px'}),
                    html.Div([
                        html.H1("Quick Summary:", className='mb-4', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}),
                        html.Hr(),
                            html.Div(id='summary'),
                            html.Br(),                               
                        html.H1("Full Details:", className='mb-4', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}),
                        html.Hr(),
                        
                        dash_table.DataTable(
                            id='table',
                            columns=[{'name': 'No Data', 'id': 'no_data'}],  # Dummy column to avoid errors
                            data=[], 
                            row_selectable='single',  # or 'multi' if needed
                            sort_action="native",
                            filter_action="native",
                            fixed_rows={'headers': True},
                            style_table={'maxHeight': '500px', 'overflowX': 'auto', 'overflowY': 'auto'},
                            style_cell={
                                'textAlign': 'center',
                                'width': '100px',
                                'maxWidth': '100px',
                                'whiteSpace': 'nowrap',
                                'overflow': 'hidden',
                                'textOverflow': 'ellipsis',
                            },
                            style_header={
                                'backgroundColor': 'rgb(30, 30, 30)',
                                'color': 'white',
                                'fontWeight': 'bold',
                            },
                        ),
                                html.Br(),
                                html.Div(
                                    dash_player.DashPlayer(
                                        id='picked_video',
                                        url="",
                                        controls=True,
                                        width="1200px",
                                        height="600px",
                                        style={"border": "2px solid black"}
                                    ),
                                    style={"display": "flex", "justifyContent": "center"}
                                )                       
                    ]),
                ]
            )
        ]
    )




    
# Helper to build a single-row (or no rows) for the filter-comparison table
def compute_filter_comp(
    filtered_df,
    original_total,
    city_name,
    selected_terrain,
    selected_occluded,
    selected_VQ,
    selected_tilt,
    selected_distance,
    selected_distortions,
    pie_clickData,
    bar_weather_clickData,
    bar_clickData,
    pie2_clickData,
):
    def normalize(v):
        if isinstance(v, (list, tuple)):
            # Remove None and flatten
            v = [item for item in v if item is not None]
            if len(v) == 1:
                return v[0]
            elif len(v) == 0:
                return None
            return ", ".join(str(item) for item in v)
        return v

    # Normalize all filters
    filters_dict = {
        'Terrain': normalize(selected_terrain),
        'Occluded': normalize(selected_occluded),
        'Video quality': normalize(selected_VQ),
        'Camera tilt': normalize(selected_tilt),
        'Distance from building': normalize(selected_distance),
        'Distortions': normalize(selected_distortions),
        'Time': normalize(pie_clickData),
        'Weather': normalize(bar_weather_clickData),
        'Logos': normalize(bar_clickData),
        'Source': normalize(pie2_clickData)
    }

    # Build active filters
    active_filters = {
        k: v for k, v in filters_dict.items()
        if v is not None and v != 'All'
    }

    # Calculate percentage
    filtered_count = len(filtered_df)
    percentage = (filtered_count / original_total * 100) if original_total else 0

    row = {
        "City": city_name,
        "Filters": ", ".join(active_filters.keys()) if active_filters else '',
        "fvalue": ", ".join(str(v) for v in active_filters.values()) if active_filters else '',
        "Percentage": f"{filtered_count} - {percentage:.2f}%",
        "total": f"{original_total}"
    }

    return [row]




@app.callback(
    [
        Output('map', 'center'),
        Output('map-layer', 'children'),
        Output('polygon-layer', 'children'),
        Output('Terrain', 'options'),
        Output('Terrain', 'value'),
        Output('Occlusion', 'options'),
        Output('Occlusion', 'value'),
        Output('VQ', 'options'),
        Output('VQ', 'value'),
        Output('Camera_Tilt', 'options'),
        Output('Camera_Tilt', 'value'),
        Output('Distance_Building', 'options'),
        Output('Distance_Building', 'value'),
        Output('Distortions', 'options'),
        Output('Distortions', 'value'),
        Output('record-count', 'children'),
        Output('drop-pre', 'children'),
        Output('duration-slider', 'min'),
        Output('duration-slider', 'max'),
        Output('duration-slider', 'value'),
        Output('duration-slider', 'step'),
        Output('pie-chart', 'figure'),
        Output('bar-chart-weather', 'figure'),
        Output('bar-plot-logos', 'figure'),
        Output('source-pie', 'figure'),
        Output('pie-chart', 'clickData'),
        Output('bar-chart-weather', 'clickData'),
        Output('bar-plot-logos', 'clickData'),
        Output('source-pie', 'clickData'),
        Output('city_name','children'),
        Output('table', 'data'),
        Output('table', 'columns'),
        Output('current-city-data','data'),
        Output('reset_button_clicked','data'),
        Output('graphs-container', 'style'),
        Output('polygon_drop_active','data'),
        Output('polygon-coords-store', 'data'),
        Output('filter_comp', 'data'),            # <-- The table showing filter comparisons
        Output('filter_comp_store','data'),       # <-- Store for filter comparison
        Output('load_button_clicked','data'),
        Output('picked_video','url'),
        Output('search_input', 'options'),
        Output("input-modal", "is_open"),
        Output('confirmation-modal','is_open'),
        Output('confirmation-message','children'),
        Output('summary','children'),
        Output('original_total','data'),
        Output('last-clicked-labels', 'data'),
        Output('total_cities','children'),
        Output('compare-bar','figure'),
        Output('compare-bar', 'style'),
        Output('compare-bar','clickData'),
        Output('city_records_df','data'),
        Output("download-component", "data")
  


    ],
    [
        Input('city-filter-btn', 'n_clicks'),
        Input('city_filter', "value"),
        Input('city_filter', "options"),
        Input('update','n_clicks'),
        Input('pie-chart', 'clickData'),
        Input('bar-chart-weather', 'clickData'),
        Input('bar-plot-logos', 'clickData'),
        Input('source-pie','clickData'),
        Input('compare-bar','clickData'),
        Input('duration-slider', 'value'),
        Input('Terrain', 'value'),
        Input('Occlusion', 'value'),
        Input('VQ', 'value'),
        Input('Camera_Tilt', 'value'),
        Input('Distance_Building', 'value'),
        Input('Distortions','value'),
        Input('dropouts','n_clicks'),
        Input('clear_table','n_clicks'),
        Input('table', 'selected_rows'),
        Input('search_coord','n_clicks'),
        Input('check','n_clicks'),
        Input('modal-check','n_clicks'),
        Input('export_log','n_clicks'),
        Input('update_log','n_clicks')


    ],
    [
        State('current-city-data','data'),
        State('reset_button_clicked','data'),
        State('polygon_drop_active','data'),
        State('polygon-coords-store', 'data'),
        State('filter_comp_store','data'),
        State('load_button_clicked','data'),
        State('search_input', 'value'),
        State("coord_modal", "value"),  # Captures input value from modal
        State("input-modal", "is_open"),
        State('original_total','data'),
        State('last-clicked-labels', 'data'),
        State('city_records_df','data')


    ]
)
def load_dashboards(load_btn, selected_city, city_options, update, pie_clickData, bar_weather_clickData,  
bar_clickData, pie2_clickData,city_rec_clickdata, duration_range, selected_terrain,  
selected_occluded, selected_VQ, selected_tilt, selected_distance,selected_distortions,  
dropouts_n_clicks,clear_button, selected_row,search_button,checkif,check_modal,export_button,update_log_btn,
current_data, reset_clicked, polygon_active,  
polygon_coords_store, filter_comp_store, load_clicked,search_value,coord_modal_input,modal_window,original_total,last_labels,city_rec_data
):

    global title
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    
    # If city dropdown changes without a button click, do nothing
    if triggered_id and triggered_id.startswith('city_filter'):
            return (dash.no_update,dash.no_update,dash.no_update, dash.no_update,
                dash.no_update, dash.no_update,dash.no_update, dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update,dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update,reset_clicked,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update,  # Single row or empty
                dash.no_update,load_clicked, "", dash.no_update,False,False,"",dash.no_update,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update)

    # Reset chart clickData if they weren’t the trigger
    if triggered_id != 'pie-chart.clickData':
        pie_clickData = None
    if triggered_id != 'bar-chart-weather.clickData':
        bar_weather_clickData = None
    if triggered_id != 'bar-plot-logos.clickData':
        bar_clickData = None
    if triggered_id != 'source-pie.clickData':
        pie2_clickData = None
    if triggered_id != 'compare-bar.clickData':
        city_rec_clickdata = None        
    if triggered_id != 'table.selected_rows':
        selected_row = None


    def extract_label(clickData, key='label', figure_id=None, last_labels=None):
        if clickData and 'points' in clickData and clickData['points']:
            label = clickData['points'][0].get(key, "All")
            if figure_id and last_labels is not None:
                last_labels[figure_id] = label
            return label, last_labels
        else:
            if figure_id and last_labels is not None and figure_id in last_labels:
                return last_labels[figure_id], last_labels
            return "All", last_labels
    
    # Helper: Build dropdown options for a given column
    def build_options(df, col_name):
        if col_name in df.columns:
            unique_vals = sorted([v for v in df[col_name].unique() if pd.notnull(v)])
            return [{'label': 'All', 'value': 'All'}] + [{'label': str(val), 'value': str(val)} for val in unique_vals]
        return []
    
    def general_summary(df):
        avg_dur = df['Duration'].mean()
        min_dur = df['Duration'].min()
        max_dur = df['Duration'].max() 
        avg_dur = float_to_mm_ss(avg_dur)
        min_dur = float_to_mm_ss(min_dur)
        max_dur = float_to_mm_ss(max_dur)
        mcvq = df['Video quality'].mode()[0]
        mct = df['Camera tilt'].mode()[0]
        mctr = df['Terrain'].mode()[0]
        mcoc = df['Occluded'].mode()[0]
        mcdistance = df['Distance from building'].mode()[0]
        mcdistortion = df['Distortions'].mode()[0]

        return (html.Div([
                    html.Ul([
                        html.Li(f"The average video duration is {avg_dur} minutes, with {max_dur} the longest and {min_dur} the shortest"),
                        html.Li(f"Most of the videos were shot in {mcvq} quality, in {mct} tilt, and with {mcdistortion} distortion"),
                        html.Li(f"The anchored building were mostly {mcoc} occluded, shot from {mcdistance} distance and in {mctr} terrain")                        
                    ],style=gen_sum_font_style)
                    
        ]))
    # Helper: Load city Sheets & polygons
    def load_selected_cities(selected_cities):
        if not selected_cities:
            return [], [], []
        if isinstance(selected_cities, str):
            selected_cities = [selected_cities]
        filtered_cities = cities[cities['City Name'].isin(selected_cities)]
        sheet_ids = filtered_cities['Sheet ID'].tolist()
        sheet_ranges = filtered_cities['Sheet Range'].tolist()
        polygon_ids = filtered_cities['PolygonID'].tolist()
        return sheet_ids, sheet_ranges, polygon_ids
    
    # Check inside polygon
    def is_inside_any(lat, lon, polygons):
        pt = Point(lat, lon)
        for poly in polygons:
            if poly and Polygon(poly).contains(pt):
                return True
        return False

    # -------------- Branch 1: Load Button --------------
    if triggered_id == 'city-filter-btn.n_clicks':
        reset_clicked = False
        load_clicked = True
        last_labels = {"pie-chart": "All", "bar-chart-weather": "All", "bar-plot-logos": "All", "source-pie": "All",'compare-bar': "All"}
        records_ct_df = pd.DataFrame()
        # Clear filter-comp data on new city load
        if filter_comp_store:
            filter_comp_data = filter_comp_store
        else:
            filter_comp_data =[]
            
        cities_dict = {}
                
        if not 'All Cities' in selected_city:
            sheet_ids, sheet_ranges, polygon_ids = load_selected_cities(selected_city)
            total_cities = f"Total Cities: {len(selected_city)}"            
        else:
            sheet_ids, sheet_ranges, polygon_ids = load_selected_cities(city_options)
            
            total_cities = f"Total Cities: {len(city_options) -1}"
     
        combined_dfs = []
        polygons_list = []
        
        for sid, srange, pid in zip(sheet_ids, sheet_ranges, polygon_ids):
            # Load polygon data
            request = drive_service.files().get_media(fileId=pid)
            polygon_bytes = request.execute()
            try:
                if isinstance(polygon_bytes, bytes):
                    polygon_data = json.loads(polygon_bytes.decode('utf-8'))
                else:
                    polygon_data = json.loads(polygon_bytes)
            except Exception:
                polygon_data = []
            poly_coords = [tuple(coord) for coord in polygon_data]
            polygons_list.append(poly_coords)

            # Load city data from Sheets
            df_city = load_city(sid, srange)

            city_name = srange.split('!')[0]

            df_records = len(df_city[df_city['Coordinates'].apply(is_valid_coord)])
            # Keep only rows with valid coordinates
            df_city = df_city[df_city['Coordinates'].apply(is_valid_coord)]
            df_city['Coordinates'] = df_city['Coordinates'].apply(clean_coordinate)


            duration_range=None,
            selected_terrain=None,
            selected_occluded=None,
            selected_VQ=None,
            selected_tilt=None,
            selected_distance=None,
            selected_distortions=None,
            bar_weather_clickData=None,
            pie_clickData=None,
            pie2_clickData=None,
            bar_weather_clickData=None,
            polygon_active=None
            
        
            time_pie = extract_label(pie_clickData, key='label', figure_id="pie-chart")
            weather_bar = extract_label(bar_weather_clickData, key='y', figure_id="bar-chart-weather")
            logos_bar = extract_label(bar_clickData, key='x', figure_id="bar-plot-logos")
            source_pie = extract_label(pie2_clickData, key='label', figure_id="source-pie")
            
            if filter_comp_store is not None:
                city_entry = next((entry for entry in filter_comp_store if entry.get('City') == city_name), None)

                if city_entry is None:
                    print('not exists')
                    # City does not exist, add new computed filter data
                    new_data = compute_filter_comp(
                        filtered_df=df_city,
                        original_total=df_records,
                        city_name=city_name,
                        selected_terrain=selected_terrain,
                        selected_occluded=selected_occluded,
                        selected_VQ=selected_VQ,
                        selected_tilt=selected_tilt,
                        selected_distance=selected_distance,
                        selected_distortions=selected_distortions,
                        pie_clickData=time_pie,
                        bar_weather_clickData=weather_bar,
                        bar_clickData=logos_bar,
                        pie2_clickData=source_pie
                    )
                    filter_comp_data.extend(new_data)

                else:
                    print('exists')
                    new_filter_data = compute_filter_comp(
                        filtered_df=df_city,
                        original_total=df_records,
                        city_name=city_name,
                        selected_terrain=selected_terrain,
                        selected_occluded=selected_occluded,
                        selected_VQ=selected_VQ,
                        selected_tilt=selected_tilt,
                        selected_distance=selected_distance,
                        selected_distortions=selected_distortions,
                        pie_clickData=time_pie,
                        bar_weather_clickData=weather_bar,
                        bar_clickData=logos_bar,
                        pie2_clickData=source_pie
                    )[0]  # Grab the first item from the list

                    filters_match = all(
                        city_entry.get(key) == new_filter_data.get(key)
                        for key in ["Filters", "fvalue", "Percentage",'total']
                    )

                    if not filters_match:
                        # Update the existing city's filters and values
                        city_entry.update(new_filter_data)
                        filter_comp_data = filter_comp_store  # Updated list with modified entry
                    else:
                        
                        # If filters and values are the same, do nothing
                        filter_comp_data = filter_comp_store

            else:
                print(city_name)
                new_data = compute_filter_comp(
                    filtered_df=df_city,
                    original_total=df_records,
                    city_name=city_name,
                    selected_terrain=selected_terrain,
                    selected_occluded=selected_occluded,
                    selected_VQ=selected_VQ,
                    selected_tilt=selected_tilt,
                    selected_distance=selected_distance,
                    selected_distortions=selected_distortions,
                    pie_clickData=time_pie,
                    bar_weather_clickData=weather_bar,
                    bar_clickData=logos_bar,
                    pie2_clickData=source_pie
                )
                filter_comp_data.extend(new_data)

        
      
            cities_dict[city_name] = (city_name, df_records)
            records_ct_df = pd.DataFrame(
                list(cities_dict.values()), columns=["City", "Records"]
            )            
                
            combined_dfs.append(df_city)
            
        
        if combined_dfs:
            df_combined = pd.concat(combined_dfs, ignore_index=True)
        else:
            df_combined = pd.DataFrame() 
                                  
        colors = [
            "cyan", "red", "green", "purple", "orange", "brown", "pink", "gray", "teal", "olive",
            "blue", "magenta", "lime", "maroon", "navy", "aqua", "gold", "coral", "indigo", "turquoise",
            "violet", "chocolate", "crimson", "salmon", "plum", "orchid", "darkgreen", "darkblue", "darkred", "darkcyan",
            "khaki", "lightblue", "lightgreen", "lightcoral", "lightpink", "mediumblue", "mediumseagreen", "mediumvioletred",
            "peru", "rosybrown", "sandybrown", "seagreen", "sienna", "skyblue", "slateblue", "springgreen",
            "steelblue", "tomato", "wheat", "yellowgreen"
        ]

        # Use itertools.cycle to cycle through the colors if there are more polygons than colors
        color_cycle = itertools.cycle(colors)

        
        # Build polygon layer
        polygon_layers = []
        for poly_coords in polygons_list:
            if poly_coords:
                city_poly = Polygon(poly_coords)
                color = next(color_cycle)
                polygon_layers.append(
                    dl.Polygon(
                        positions=list(city_poly.exterior.coords),
                        color="blue",
                        fillColor=color,
                        fillOpacity=0.6,
                    )
                )
        polygon_layer = dl.LayerGroup(children=polygon_layers)

        # Create markers
        if 'Coordinates' in df_combined.columns:
            df_combined = df_combined[df_combined['Coordinates'].str.contains(',', na=False)]
            df_combined[['Latitude', 'Longitude']] = df_combined['Coordinates'].str.split(',', expand=True)
            df_combined['Latitude'] = pd.to_numeric(df_combined['Latitude'].str.strip(), errors='coerce')
            df_combined['Longitude'] = pd.to_numeric(df_combined['Longitude'].str.strip(), errors='coerce')
            df_combined['Latitude'] = pd.to_numeric(df_combined['Latitude'], errors='coerce')
            df_combined['Longitude'] = pd.to_numeric(df_combined['Longitude'], errors='coerce')
            city_markers = create_map_markers(df_combined)
        else:
            city_markers = []


        count_within = sum(
            is_inside_any(row['Latitude'], row['Longitude'], polygons_list)
            for _, row in df_combined.iterrows()
            if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude'])
        )
        pre_out_city = round(((len(df_combined) - count_within) / len(df_combined) * 100), 2) if len(df_combined) > 0 else 0

        # Duration
        if 'Duration' not in df_combined.columns:
            df_combined['Duration'] = df_combined['Finish Time'].apply(convert_to_minutes) - df_combined['Start Time'].apply(convert_to_minutes)
        df_combined.dropna(subset=['Latitude', 'Longitude'], inplace=True)
        min_dur = round(df_combined['Duration'].min(),2) if not df_combined['Duration'].empty else 0
        max_dur = round(df_combined['Duration'].max(),2) if not df_combined['Duration'].empty else 100

        record_count = f"Total Records: {len(df_combined)}"
        drop_count = f"{pre_out_city} % out of Polygon"
        if city_markers:
            random_marker = random.choice(city_markers)
            map_center = random_marker.position
        else:
            map_center = (41.9028, 12.4964)

        # Generate charts
        city_logos_bar = generate_interactive_bar_plot_2_city(df_combined)
        city_time_of_day_pie = generate_interactive_pie_chart_city(df_combined)
        city_weather_bar = generate_interactive_bar_chart_weather_city(df_combined)
        city_source_pie = generate_interactive_pie_chart_source(df_combined)
         
        if len(records_ct_df) >= 5 and records_ct_df['Records'].sum() > 0:            
            print(records_ct_df)
            city_country_bar = generate_interactive_countries_compaered_bar_plot(records_ct_df)
            visibiliy= {"display": "block"}
            print('successful') 
        else:
            city_country_bar = px.bar()
            visibiliy= {"display": "none"}  
        
        gen_summary = general_summary(df_combined)
        
        coords_list = [coord.strip() for coord in df_combined['Coordinates'].unique()]
        if len(selected_city) == len(city_options) and len(city_options) >=4:
            title = f"Airis-Labs: Geo-Location Analysis - Full State Scope"
        else:
            title = f"Airis-Labs: Geo-Location Analysis - {', '.join(selected_city) if isinstance(selected_city, list) else selected_city}"
        # Store original total for subsequent filter-comparison
        original_total = len(df_combined[df_combined['Coordinates'].apply(is_valid_coord)])

        # Return everything
        return (
            map_center,                                # map center
            city_markers,                              # map-layer children
            polygon_layer,                             # polygon-layer children
            build_options(df_combined, 'Terrain'),     # Terrain dropdown options
            'All',                                     # Terrain value
            build_options(df_combined, 'Occluded'),    # Occlusion dropdown options
            'All',                                     # Occlusion value
            build_options(df_combined, 'Video quality'),
            'All',
            build_options(df_combined, 'Camera tilt'),
            'All',
            build_options(df_combined, 'Distance from building'),
            'All',
            build_options(df_combined, 'Distortions'),
            'All',
            record_count,
            drop_count,
            min_dur,
            max_dur,
            [min_dur, max_dur],
            round((max_dur/6),2),
            city_time_of_day_pie,
            city_weather_bar,
            city_logos_bar,
            city_source_pie,
            dash.no_update,  # pie-chart clickData
            dash.no_update,  # bar-chart-weather clickData
            dash.no_update,  # bar-plot-logos clickData
            dash.no_update,  # source-pie clickData
            title,
            df_combined.to_dict('records'),
            [{'name': col, 'id': col} for col in df_combined.columns],
            df_combined.to_dict('records'),
            reset_clicked,
            {"display": "block"},
            polygons_list,
            polygons_list,
            filter_comp_data,   # filter_comp => empty on load
            filter_comp_data,   # filter_comp_store => empty on load
            load_clicked,
            "",
            coords_list,False,False,"",gen_summary,original_total,
            last_labels,total_cities,city_country_bar,visibiliy,dash.no_update,
            records_ct_df.to_dict('records'),dash.no_update

        )

    elif triggered_id == 'table.selected_rows':
        row_idx = selected_row[0]
        df_table = pd.DataFrame(current_data)
        if row_idx < len(df_table):
            selected_trip_link = df_table.iloc[row_idx][df_table.columns[0]]
            
            
        return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, load_clicked, selected_trip_link,dash.no_update,False,False,
                "",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update)
           
    elif triggered_id == 'search_coord.n_clicks':
        # If no input provided, do nothing.
        if not search_value:
            return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update,dash.no_update, dash.no_update, dash.no_update,
                reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, load_clicked,
                "",dash.no_update,False,False,"",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
            ,dash.no_update,dash.no_update,dash.no_update)
        
        # Check if the input is a valid coordinate
        if isinstance(search_value, list):
            search_value = ",".join(search_value)
            search_value = search_value.replace(" ", "")
        # Now split the joined string
        search_values = [s.strip() for s in search_value.split(",")]
        # Ensure that the input consists of valid coordinate pairs
        coord_pairs = []
        for i in range(0, len(search_values), 2):  # Process in pairs
            if i + 1 < len(search_values):  # Ensure there is a latitude & longitude
                coord_pair = f"{search_values[i]},{search_values[i+1]}"
                if is_valid_coordinate(coord_pair):  # Validate
                    coord_pairs.append(coord_pair)
        if coord_pairs:

            # Convert current data to DataFrame
            df_search = pd.DataFrame(current_data)
            df_search = df_search[df_search['Coordinates'].apply(is_valid_coord)]
            df_search['Coordinates'] = df_search['Coordinates'].apply(clean_coordinate)
            
            # Filter rows where the 'Coordinates' column matches any of the coordinate pairs
            df_search = df_search[df_search['Coordinates'].str.strip().isin(coord_pairs)]
            selected_trip_link = df_search[df_search.columns[0]]
            
           
            # Apply any additional filters if needed.
            search_filtered = apply_all_filters2(
                df=df_search,
                duration_range=duration_range,
                selected_terrain=selected_terrain,
                selected_occluded=selected_occluded,
                selected_VQ=selected_VQ,
                selected_tilt=selected_tilt,
                selected_distance=selected_distance,
                selected_distortions=selected_distortions,
                bar_weather_clickData=bar_weather_clickData,
                pie_clickData=pie_clickData,
                pie_2_clickData=pie2_clickData,
                bar_2_clickData=bar_clickData,
                polygon_active=polygon_active
            )
            
            # Update dropdown options based on the filtered data.
            terrain_options = build_options(search_filtered, 'Terrain')
            occlusion_options = build_options(search_filtered, 'Occluded')
            vq_options = build_options(search_filtered, 'Video quality')
            camera_tilt_options = build_options(search_filtered, 'Camera tilt')
            distance_options = build_options(search_filtered, 'Distance from building')
            distortions_options = build_options(search_filtered, 'Distortions')
            
            # Ensure 'Coordinates' is a string and remove spaces
            search_filtered['Coordinates'] = search_filtered['Coordinates'].str.replace('', '', regex=False)

            # Keep only rows that contain a comma
            search_filtered = search_filtered[search_filtered['Coordinates'].str.contains(',', na=False)]

            # Split the Coordinates column into two new columns
            temp = search_filtered['Coordinates'].str.split(',', n=1, expand=True)

            # Ensure temp has at least two columns
            if temp.shape[1] == 2:
                search_filtered['Latitude'] = pd.to_numeric(temp.iloc[:, 0], errors='coerce')
                search_filtered['Longitude'] = pd.to_numeric(temp.iloc[:, 1], errors='coerce')
            else:
                print("Warning: Some rows still do not contain a valid coordinate pair.")
            city_markers = create_map_markers(search_filtered)
            
            # Determine map center based on available markers.
            if city_markers:
                random_marker = random.choice(city_markers)
                map_center = random_marker.position
            else:
                map_center = (41.9028, 12.4964)
            
            # Compute how many records lie within the polygon.
            polygons_list = polygon_coords_store if polygon_coords_store else []
            if polygons_list and len(polygons_list) > 0:
                city_polygon = Polygon(polygons_list[0])
            else:
                city_polygon = None
            count_within = 0
            if city_polygon:
                count_within = sum(
                    city_polygon.contains(Point(row['Latitude'], row['Longitude']))
                    for _, row in search_filtered.iterrows()
                    if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude'])
                )
            pre_out_city = round(((len(search_filtered) - count_within) / len(search_filtered) * 100), 2) if len(search_filtered) > 0 else 0
            
            # Compute duration values if needed.
            if 'Duration' not in search_filtered.columns:
                search_filtered['Duration'] = search_filtered['Finish Time'].apply(convert_to_minutes) - search_filtered['Start Time'].apply(convert_to_minutes)
            search_filtered.dropna(subset=['Latitude', 'Longitude'], inplace=True)
            min_dur = search_filtered['Duration'].min() if not search_filtered['Duration'].empty else 0
            max_dur = search_filtered['Duration'].max() if not search_filtered['Duration'].empty else 100
            record_count = f"Total Records: {len(search_filtered)}"
            drop_count = f"{pre_out_city} % out of Polygon"

            coords_list = search_filtered['Coordinates'].unique()             
            # Generate charts based on the filtered data.
            pie_fig = generate_interactive_pie_chart_city(search_filtered)
            weather_bar_fig = generate_interactive_bar_chart_weather_city(search_filtered)
            logos_bar_fig = generate_interactive_bar_plot_2_city(search_filtered)
            source_pie_fig = generate_interactive_pie_chart_source(search_filtered)
            
            gen_summary = general_summary(search_filtered)
            
            return (
                map_center,               # 1. map center
                city_markers,             # 2. map-layer children
                dash.no_update,           # 3. polygon-layer children (no update)
                terrain_options,          # 4. Terrain options
                selected_terrain,         # 5. Terrain value
                occlusion_options,        # 6. Occlusion options
                selected_occluded,        # 7. Occlusion value
                vq_options,               # 8. VQ options
                selected_VQ,              # 9. VQ value
                camera_tilt_options,      # 10. Camera_Tilt options
                selected_tilt,            # 11. Camera_Tilt value
                distance_options,         # 12. Distance_Building options
                selected_distance,        # 13. Distance_Building value
                distortions_options,      # 14. Distortions options
                selected_distortions,     # 15. Distortions value
                record_count,             # 16. record-count children
                drop_count,               # 17. drop-pre children
                min_dur,                  # 18. duration-slider min
                max_dur,                  # 19. duration-slider max
                [min_dur, max_dur],       # 20. duration-slider value
                round((max_dur/6),2),
                pie_fig,                  # 21. pie-chart figure
                weather_bar_fig,          # 22. bar-chart-weather figure
                logos_bar_fig,            # 23. bar-plot-logos figure
                source_pie_fig,           # 24. source-pie figure
                dash.no_update,           # 25. pie-chart clickData
                dash.no_update,           # 26. bar-chart-weather clickData
                dash.no_update,           # 27. bar-plot-logos clickData
                dash.no_update,           # 28. source-pie clickData
                dash.no_update,           # 29. city_name children (unchanged)
                search_filtered.to_dict('records'),  # 30. table data
                dash.no_update,           # 31. table columns (unchanged)
                search_filtered.to_dict('records'),  # 32. current-city-data
                reset_clicked,            # 33. reset_button_clicked
                {"display": "block"},     # 34. graphs-container style
                polygon_active,           # 35. polygon_drop_active
                dash.no_update,           # 36. polygon-coords-store
                dash.no_update,           # 37. filter_comp data
                dash.no_update,           # 38. filter_comp_store data
                load_clicked,             # 39. load_button_clicked
                selected_trip_link,     
                coords_list,False,False,"",gen_summary,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
            ,dash.no_update,dash.no_update)
        else:
            # If the coordinate is not valid, do nothing.
            return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, load_clicked, "",dash.no_update,False,False,
                "",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
            ,dash.no_update,dash.no_update)
            
    elif triggered_id =='check.n_clicks':
        if current_data:
            return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, load_clicked, "",dash.no_update,True,False,
                "",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
            ,dash.no_update)
        else:
            return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, load_clicked,
                "",dash.no_update,False,False,"",dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
            ,dash.no_update)
        
    elif triggered_id == 'modal-check.n_clicks':
        if is_valid_coordinate(coord_modal_input):
                       
            sheet_ids, sheet_ranges, polygon_ids = load_selected_cities(selected_city)
            polygons_list = []

            for sid, srange, pid in zip(sheet_ids, sheet_ranges, polygon_ids):
                request = drive_service.files().get_media(fileId=pid)
                polygon_bytes = request.execute()
                try:
                    if isinstance(polygon_bytes, bytes):
                        polygon_data = json.loads(polygon_bytes.decode('utf-8'))
                    else:
                        polygon_data = json.loads(polygon_bytes)
                except Exception:
                    polygon_data = []
                poly_coords = [tuple(coord) for coord in polygon_data]
                polygons_list.append(poly_coords)
            
            lat, lon = map(float, coord_modal_input.split(","))    
            if is_inside_any(lat,lon,polygons_list):
                result_window = html.Div(
                    f"{coord_modal_input} is in the Polygon",
                    style={"color": "green", "font-weight": "bold"})
                return (
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, load_clicked, "",
                    dash.no_update,False,True,result_window,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
                ,dash.no_update)
            else:
                result_window = html.Div(
                    f"{coord_modal_input} is out of the Polygon",
                    style={"color": "red", "font-weight": "bold"})
                return (
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                    reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                    dash.no_update, dash.no_update, load_clicked, "",dash.no_update,
                    False,True,result_window,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
                ,dash.no_update,dash.no_update)
        else:
            result_window = html.Div(
            f"Invalid Coordinate",
            style={"color": "red", "font-weight": "bold"})
            return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, load_clicked, "",dash.no_update,
                False,True,result_window,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
            ,dash.no_update,dash.no_update)
    
    elif triggered_id == 'export_log.n_clicks':
        filters_comp_data = pd.DataFrame(filter_comp_store)
        if filter_comp_store:
            filters_comp_data.columns = ['City', 'Filters', 'Values', 'Precentage', 'Total']
            filters_comp_data['Total'] = pd.to_numeric(filters_comp_data['Total'], errors='coerce')
            max_rec = filters_comp_data['Total'].max()
            min_rec = filters_comp_data['Total'].min()
            sum_rec = filters_comp_data['Total'].sum()
            count_rec = filters_comp_data['Total'].count()
            mean_rec = filters_comp_data['Total'].mean()
            
            Agg_data = pd.DataFrame([
                        ['Max', max_rec],
                        ['Min', min_rec],
                        ['Sum', sum_rec],
                        ['Count', count_rec],
                        ['Average', mean_rec]], columns = ['AggFunction','Value'])
            # Create 4 empty columns as a spacer
            spacer = pd.DataFrame('', index=range(max(len(filters_comp_data), len(Agg_data))), columns=['']*4)

            # Reset indexes to align properly
            filters_comp_data = filters_comp_data.reset_index(drop=True)
            Agg_data = Agg_data.reset_index(drop=True)

            # Pad the shorter DataFrame to match the length
            if len(filters_comp_data) < len(Agg_data):
                pad_len = len(Agg_data) - len(filters_comp_data)
                pad_df = pd.DataFrame('', index=range(pad_len), columns=filters_comp_data.columns)
                filters_comp_data = pd.concat([filters_comp_data, pad_df], ignore_index=True)
            elif len(Agg_data) < len(filters_comp_data):
                pad_len = len(filters_comp_data) - len(Agg_data)
                pad_df = pd.DataFrame('', index=range(pad_len), columns=Agg_data.columns)
                Agg_data = pd.concat([Agg_data, pad_df], ignore_index=True)
            
            filters_log= pd.concat([filters_comp_data,spacer, Agg_data], axis=1)
            
            return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, load_clicked, "",dash.no_update,
                False,False,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
            ,dash.no_update,dcc.send_data_frame(filters_log.to_csv, filename="export_log.csv"))
        
        else:
            return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, load_clicked, "",dash.no_update,
                False,False,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
            ,dash.no_update,dash.no_update)
                                            
    elif triggered_id == 'update_log.n_clicks':
        if filter_comp_store is not None:
            filter_data = filter_comp_store
            all_data =[]
            cities_list = [city.strip() for entry in filter_data if 'City' in entry for city in entry['City'].split(',')]

            print(cities_list)
            for city in cities_list:
                sid,srange,pid= load_selected_cities(city)
                df_city_log = load_city(sid[0], srange[0])
                df_city_log = df_city_log[df_city_log['Coordinates'].apply(is_valid_coord)]
                df_city_log['Coordinates'] = df_city_log['Coordinates'].apply(clean_coordinate)           
                df_records=len(df_city_log)
                
                duration_range=None,
                selected_terrain=None,
                selected_occluded=None,
                selected_VQ=None,
                selected_tilt=None,
                selected_distance=None,
                selected_distortions=None,
                bar_weather_clickData=None,
                pie_clickData=None,
                pie2_clickData=None,
                bar_weather_clickData=None,
                polygon_active=None
                
                time_pie = extract_label(pie_clickData, key='label', figure_id="pie-chart")
                weather_bar = extract_label(bar_weather_clickData, key='y', figure_id="bar-chart-weather")
                logos_bar = extract_label(bar_clickData, key='x', figure_id="bar-plot-logos")
                source_pie = extract_label(pie2_clickData, key='label', figure_id="source-pie")
    
                new_data = compute_filter_comp(
                    filtered_df=df_city_log,
                    original_total=df_records,
                    city_name=city,
                    selected_terrain=selected_terrain,
                    selected_occluded=selected_occluded,
                    selected_VQ=selected_VQ,
                    selected_tilt=selected_tilt,
                    selected_distance=selected_distance,
                    selected_distortions=selected_distortions,
                    pie_clickData=time_pie,
                    bar_weather_clickData=weather_bar,
                    bar_clickData=logos_bar,
                    pie2_clickData=source_pie
                )
                all_data.extend(new_data) 
            filter_data = [dict(t) for t in {tuple(d.items()) for d in all_data}]               
            result_window = f"Filter Log Updated!"            
            return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update,dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                reset_clicked, dash.no_update, dash.no_update, dash.no_update,
                filter_data, filter_data, load_clicked, "",dash.no_update,
                False,True,result_window,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
            ,dash.no_update,dash.no_update)
            
    elif triggered_id == 'update.n_clicks':
        reset_clicked = True
        load_clicked = False
        last_labels = {"pie-chart": "All", "bar-chart-weather": "All", "bar-plot-logos": "All", "source-pie": "All"}
        
        if filter_comp_store:
            filter_comp_data = filter_comp_store
        else:
            filter_comp_data =[]
                    
        cities_dict = {}
        # Reload city data
        if not 'All Cities' in selected_city:
            sheet_ids, sheet_ranges, polygon_ids = load_selected_cities(selected_city)
            total_cities = f"Total Cities: {len(selected_city)}"            
        else:
            sheet_ids, sheet_ranges, polygon_ids = load_selected_cities(city_options)
            total_cities = f"Total Cities: {len(city_options) -1}"
     
        combined_dfs = []
        polygons_list = []
        for sid, srange, pid in zip(sheet_ids, sheet_ranges, polygon_ids):
            # Load polygon data
            request = drive_service.files().get_media(fileId=pid)
            polygon_bytes = request.execute()
            try:
                if isinstance(polygon_bytes, bytes):
                    polygon_data = json.loads(polygon_bytes.decode('utf-8'))
                else:
                    polygon_data = json.loads(polygon_bytes)
            except Exception:
                polygon_data = []
            poly_coords = [tuple(coord) for coord in polygon_data]
            polygons_list.append(poly_coords)

            # Load city data from Sheets
            df_city = load_city(sid, srange)
            
            city_name = srange.split('!')[0]


            
            # Keep only rows with valid coordinates
            df_city = df_city[df_city['Coordinates'].apply(is_valid_coord)]
            df_city['Coordinates'] = df_city['Coordinates'].apply(clean_coordinate)

            
            df_records = len(df_city)
            
            duration_range=None,
            selected_terrain=None,
            selected_occluded=None,
            selected_VQ=None,
            selected_tilt=None,
            selected_distance=None,
            selected_distortions=None,
            bar_weather_clickData=None,
            pie_clickData=None,
            pie2_clickData=None,
            bar_weather_clickData=None,
            polygon_active=None
            
        
            time_pie = extract_label(pie_clickData, key='label', figure_id="pie-chart")
            weather_bar = extract_label(bar_weather_clickData, key='y', figure_id="bar-chart-weather")
            logos_bar = extract_label(bar_clickData, key='x', figure_id="bar-plot-logos")
            source_pie = extract_label(pie2_clickData, key='label', figure_id="source-pie")
            
            if filter_comp_store is not None:
                city_entry = next((entry for entry in filter_comp_store if entry.get('City') == city_name), None)

                if city_entry is None:
                    print('not exists')
                    # City does not exist, add new computed filter data
                    new_data = compute_filter_comp(
                        filtered_df=df_city,
                        original_total=df_records,
                        city_name=city_name,
                        selected_terrain=selected_terrain,
                        selected_occluded=selected_occluded,
                        selected_VQ=selected_VQ,
                        selected_tilt=selected_tilt,
                        selected_distance=selected_distance,
                        selected_distortions=selected_distortions,
                        pie_clickData=time_pie,
                        bar_weather_clickData=weather_bar,
                        bar_clickData=logos_bar,
                        pie2_clickData=source_pie
                    )
                    filter_comp_data.extend(new_data)

                else:
                    print('exists')
                    fvalue_str = city_entry.get('fvalue', '')                    
                    values_list = [item.strip() for item in fvalue_str.split(',') if item.strip()]
                    filter_str = city_entry.get('Filters','')
                    filter_list = [item.strip() for item in filter_str.split(',') if item.strip()]
                    print(values_list,filter_list)

                    from collections import Counter

                    def row_contains_all_substrings(row, substrings):
                        # Convert the entire row to a single string.
                        row_str = ' '.join(map(str, row.tolist()))
                        # Count the occurrences of each substring required.
                        required_counts = Counter(substrings)
                        # Check that each substring appears at least the required number of times.
                        for substring, count in required_counts.items():
                            if row_str.count(substring) < count:
                                return False
                        return True


                    # Example: Filter columns that have any of the filter strings in their header
                    filtered_columns = [col for col in df_city.columns if any(flt in col for flt in filter_list)]
                    df_filtered_city = df_city[filtered_columns]
                    
                    
                    df_filtered = df_filtered_city[
                        df_filtered_city.apply(lambda r: row_contains_all_substrings(r, values_list), axis=1)                        
                    ]

                    percentage = (len(df_filtered) / df_records * 100) if original_total else 0                  
                    city_entry['Percentage'] = f"{len(df_filtered)} - {percentage:.2f}%"
                    city_entry['total'] = df_records



            else:
                print(city_name)
                new_data = compute_filter_comp(
                    filtered_df=df_city,
                    original_total=df_records,
                    city_name=city_name,
                    selected_terrain=selected_terrain,
                    selected_occluded=selected_occluded,
                    selected_VQ=selected_VQ,
                    selected_tilt=selected_tilt,
                    selected_distance=selected_distance,
                    selected_distortions=selected_distortions,
                    pie_clickData=time_pie,
                    bar_weather_clickData=weather_bar,
                    bar_clickData=logos_bar,
                    pie2_clickData=source_pie
                )
                filter_comp_data.extend(new_data)            
            
            
            cities_dict[city_name] = (city_name, df_records)
            records_ct_df = pd.DataFrame(
                list(cities_dict.values()), columns=["City", "Records"]
            )
            combined_dfs.append(df_city)

        if combined_dfs:
            df_updated = pd.concat(combined_dfs, ignore_index=True)
        else:
            df_updated = pd.DataFrame()

        if 'Coordinates' in df_updated.columns:
            df_updated = df_updated[df_updated['Coordinates'].str.contains(',', na=False)]
            df_updated[['Latitude', 'Longitude']] = df_updated['Coordinates'].str.split(',', expand=True)
            df_updated['Latitude'] = pd.to_numeric(df_updated['Latitude'], errors='coerce')
            df_updated['Longitude'] = pd.to_numeric(df_updated['Longitude'], errors='coerce')
            city_markers = create_map_markers(df_updated)
            coords_list= df_updated['Coordinates'].unique()
        else:
            city_markers = []
            

            return False
        count_within = sum(
            is_inside_any(row['Latitude'], row['Longitude'], polygons_list)
            for _, row in df_updated.iterrows()
            if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude'])
        )
        pre_out_city = round(((len(df_updated) - count_within) / len(df_updated) * 100), 2) if len(df_updated)>0 else 0

        if 'Duration' not in df_updated.columns:
            df_updated['Duration'] = df_updated['Finish Time'].apply(convert_to_minutes) - df_updated['Start Time'].apply(convert_to_minutes)
        df_updated.dropna(subset=['Latitude', 'Longitude'], inplace=True)
        min_dur = df_updated['Duration'].min() if not df_updated['Duration'].empty else 0
        max_dur = df_updated['Duration'].max() if not df_updated['Duration'].empty else 100
        record_count = f"Total Records: {len(df_updated)}"
        drop_count = f"{pre_out_city} % out of Polygon"
        if city_markers:
            random_marker = random.choice(city_markers)
            map_center = random_marker.position
        else:
            map_center = (41.9028, 12.4964)

        city_logos_bar = generate_interactive_bar_plot_2_city(df_updated)
        city_time_of_day_pie = generate_interactive_pie_chart_city(df_updated)
        city_weather_bar = generate_interactive_bar_chart_weather_city(df_updated)
        city_source_pie = generate_interactive_pie_chart_source(df_updated)
        
        gen_summary = general_summary(df_updated)
        
        if len(records_ct_df) >= 5 and records_ct_df['Records'].sum() > 0:            
            print(records_ct_df)
            city_country_bar = generate_interactive_countries_compaered_bar_plot(records_ct_df)
            visibiliy= {"display": "block"}
        else:
            city_country_bar = px.bar()
            visibiliy= {"display": "none"}  
            
        original_total =len(df_updated[df_updated['Coordinates'].apply(is_valid_coord)])
        
        if len(selected_city) == len(city_options) and len(city_options) >=4:
            title = f"Airis-Labs: Geo-Location Analysis - Full State Scope"
        else:
            title = f"Airis-Labs: Geo-Location Analysis - {', '.join(selected_city) if isinstance(selected_city, list) else selected_city}"

        total_cities = f"Total Cities: {len(selected_city)}"

        # Now produce a single row for filter-comp if user changed any filters
        # (But since "update" was clicked, presumably we want to reset everything.)
        # We'll keep it empty or you can do the compute_filter_comp if you want.
        # For a strict "reset," we do not compute filters. We'll keep it empty:

        return (
            map_center,
            city_markers,
            dash.no_update,  # keep existing polygons
            build_options(df_updated, 'Terrain'),
            'All',
            build_options(df_updated, 'Occluded'),
            'All',
            build_options(df_updated, 'Video quality'),
            'All',
            build_options(df_updated, 'Camera tilt'),
            'All',
            build_options(df_updated, 'Distance from building'),
            'All',
            build_options(df_updated, 'Distortions'),
            'All',
            record_count,
            drop_count,
            min_dur,
            max_dur,
            [min_dur, max_dur],
            round((max_dur/6),2),
            city_time_of_day_pie,
            city_weather_bar,
            city_logos_bar,
            city_source_pie,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            title,
            df_updated.to_dict('records'),
            [{'name': col, 'id': col} for col in df_updated.columns],
            df_updated.to_dict('records'),
            reset_clicked,
            {"display": "block"},
            polygons_list,
            polygons_list,
            filter_comp_data,  
            filter_comp_data,
            load_clicked,
            "",coords_list,False,False,"",gen_summary,
            original_total,last_labels,total_cities,city_country_bar,visibiliy,dash.no_update,records_ct_df.to_dict('records'),dash.no_update
        )          

    # -------------- Branch 3: Dropouts Filtering --------------
    elif triggered_id == 'dropouts.n_clicks' and dropouts_n_clicks > 0:
        polygon_active = True
        df_filtered = pd.DataFrame(current_data)
        

        # Apply all filters
        filtered_df = apply_all_filters2(
            df=df_filtered,
            duration_range=duration_range,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            selected_distortions=selected_distortions,
            bar_weather_clickData=bar_weather_clickData,
            pie_clickData=pie_clickData,
            pie_2_clickData=pie2_clickData,
            bar_2_clickData=bar_clickData,
            polygon_active=polygon_active
        )

        if 'Coordinates' in filtered_df.columns:
            filtered_df = filtered_df[filtered_df['Coordinates'].str.contains(',', na=False)]
            temp = filtered_df['Coordinates'].str.split(',', n=1, expand=True)
            filtered_df['Latitude'] = pd.to_numeric(temp[0], errors='coerce')
            filtered_df['Longitude'] = pd.to_numeric(temp[1], errors='coerce')
            coords_list= filtered_df['Coordinates'].unique()

        polygons_list = polygon_coords_store if polygon_coords_store is not None else []

        def is_inside_any_poly(row):
            pt = Point(row['Latitude'], row['Longitude'])
            return any(Polygon(poly).contains(pt) for poly in polygons_list if poly)

        total_count = len(filtered_df)
        count_inside = filtered_df.apply(is_inside_any_poly, axis=1).sum()
        dropout_percentage = round(((total_count - count_inside) / total_count * 100), 2) if total_count > 0 else 0

        # Keep only the dropouts (outside polygons)
        filtered_df = filtered_df[~filtered_df.apply(is_inside_any_poly, axis=1)]
        city_markers = create_map_markers(filtered_df)

        if 'Duration' not in filtered_df.columns:
            filtered_df['Duration'] = filtered_df['Finish Time'].apply(convert_to_minutes) - filtered_df['Start Time'].apply(convert_to_minutes)
        filtered_df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
        min_dur = filtered_df['Duration'].min() if not filtered_df['Duration'].empty else 0
        max_dur = filtered_df['Duration'].max() if not filtered_df['Duration'].empty else 100
        record_count = f"Total Records: {len(filtered_df)}"
        if city_markers:
            random_marker = random.choice(city_markers)
            map_center = random_marker.position
        else:
            map_center = (41.9028, 12.4964)

        city_logos_bar = generate_interactive_bar_plot_2_city(filtered_df)
        city_time_of_day_pie = generate_interactive_pie_chart_city(filtered_df)
        city_weather_bar = generate_interactive_bar_chart_weather_city(filtered_df)
        city_source_pie = generate_interactive_pie_chart_source(filtered_df)

        gen_summary = general_summary(filtered_df)

        drop_count = f"100 % out of Polygon" if total_count > 0 else "Nothing to show"

        # Now produce filter_comp row
        city_label = selected_city if isinstance(selected_city, str) else ", ".join(selected_city)
        time_pie = extract_label(pie_clickData, key='label', figure_id="pie-chart")
        weather_bar = extract_label(bar_weather_clickData, key='y', figure_id="bar-chart-weather")
        logos_bar = extract_label(bar_clickData, key='x', figure_id="bar-plot-logos")
        source_pie = extract_label(pie2_clickData, key='label', figure_id="source-pie")
        
        filter_comp_data = compute_filter_comp(
            filtered_df=filtered_df,
            original_total=original_total,
            city_name=city_label,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            selected_distortions=selected_distortions,
            pie_clickData = time_pie,
            bar_weather_clickData=weather_bar,
            bar_clickData= logos_bar,
            pie2_clickData= source_pie
        )

        return (
            map_center,
            city_markers,
            dash.no_update,
            build_options(filtered_df, 'Terrain'),
            'All',
            build_options(filtered_df, 'Occluded'),
            'All',
            build_options(filtered_df, 'Video quality'),
            'All',
            build_options(filtered_df, 'Camera tilt'),
            'All',
            build_options(filtered_df, 'Distance from building'),
            'All',
            build_options(filtered_df, 'Distortions'),
            'All',
            record_count,
            drop_count,
            min_dur,
            max_dur,
            [min_dur, max_dur],
            round((max_dur/6),2),
            city_time_of_day_pie,
            city_weather_bar,
            city_logos_bar,
            city_source_pie,
            pie_clickData,
            bar_clickData,
            bar_weather_clickData,
            pie2_clickData,
            dash.no_update,
            filtered_df.to_dict('records'),
            dash.no_update,
            filtered_df.to_dict('records'),
            reset_clicked,
            {"display": "block"},
            polygon_active,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            load_clicked,
            "",coords_list,False,False,"",gen_summary
            ,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
        ,dash.no_update,dash.no_update,dash.no_update)


    elif triggered_id == 'clear_table.n_clicks':
        filter_comp_store =[]
        filter_comp_data = filter_comp_store
        return (
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            reset_clicked,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            filter_comp_data,  # Single row or empty
            filter_comp_data,
            load_clicked,
            "" ,dash.no_update,False,False,"",
            dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update         
        ,dash.no_update)


    # -------------- Branch 5: Default Filtering (No explicit button) --------------
    else:
        df_current = pd.DataFrame(current_data)
        if df_current.empty:
            # If we have no data in current_data, attempt to reload
            sheet_ids, sheet_ranges, polygon_ids = load_selected_cities(selected_city)
            combined_dfs = []
            polygons_list = []

            for sid, srange, pid in zip(sheet_ids, sheet_ranges, polygon_ids):
                request = drive_service.files().get_media(fileId=pid)
                polygon_bytes = request.execute()
                try:
                    if isinstance(polygon_bytes, bytes):
                        polygon_data = json.loads(polygon_bytes.decode('utf-8'))
                    else:
                        polygon_data = json.loads(polygon_bytes)
                except Exception:
                    polygon_data = []
                poly_coords = [tuple(coord) for coord in polygon_data]
                polygons_list.append(poly_coords)
                df_city = load_city(sid, srange)
                combined_dfs.append(df_city)

            if combined_dfs:
                df_current = pd.concat(combined_dfs, ignore_index=True)
            else:
                df_current = pd.DataFrame()

            polygon_layer = dl.LayerGroup(
                children=[
                    dl.Polygon(
                        positions=list(Polygon(polygons_list[0]).exterior.coords) if polygons_list and len(polygons_list[0])>0 else [],
                        color="blue",
                        fillColor="cyan",
                        fillOpacity=0.6,
                    )
                ]
            ) if polygons_list else dl.LayerGroup()

            table_columns = [{'name': col, 'id': col} for col in df_current.columns]
            terrain_options = build_options(df_current, 'Terrain')
            occlusion_options = build_options(df_current, 'Occluded')
            vq_options = build_options(df_current, 'Video quality')
            camera_tilt_options = build_options(df_current, 'Camera tilt')
            distance_options = build_options(df_current, 'Distance from building')
            distortions_options = build_options(df_current, 'Distortions')
            
            df_current = df_current[df_current['Coordinates'].str.contains(',', na=False)]
            temp = df_current['Coordinates'].str.split(',', n=1, expand=True)
            df_current['Latitude'] = pd.to_numeric(temp[0], errors='coerce')
            df_current['Longitude'] = pd.to_numeric(temp[1], errors='coerce')
            city_markers = create_map_markers(df_current)
            coords_list = df_current['Coordinates'].unique()

            if polygons_list and len(polygons_list) > 0:
                city_polygon = Polygon(polygons_list[0])
            else:
                city_polygon = None

            count_within = sum(
                city_polygon.contains(Point(row['Latitude'], row['Longitude']))
                for _, row in df_current.iterrows()
                if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude'])
            ) if city_polygon else 0

            pre_out_city = round(((len(df_current) - count_within) / len(df_current) * 100), 2) if len(df_current)>0 else 0

            if 'Duration' not in df_current.columns:
                df_current['Duration'] = df_current['Finish Time'].apply(convert_to_minutes) - df_current['Start Time'].apply(convert_to_minutes)
            df_current.dropna(subset=['Latitude', 'Longitude'], inplace=True)
            min_dur = df_current['Duration'].min() if not df_current['Duration'].empty else 0
            max_dur = df_current['Duration'].max() if not df_current['Duration'].empty else 100
            record_count = f"Total Records: {len(df_current)}"
            drop_count = f"{pre_out_city} % out of Polygon"
            if city_markers:
                random_marker = random.choice(city_markers)
                map_center = random_marker.position
            else:
                map_center = (41.9028, 12.4964)

            title = f"Airis-Labs: Geo-Location Analysis - {', '.join(selected_city) if isinstance(selected_city, list) else selected_city}"

            city_logos_bar = generate_interactive_bar_plot_2_city(df_current)
            city_time_of_day_pie = generate_interactive_pie_chart_city(df_current)
            city_weather_bar = generate_interactive_bar_chart_weather_city(df_current)
            city_source_pie = generate_interactive_pie_chart_source(df_current)
            
            gen_summary = general_summary(df_current)

            city_label = selected_city if isinstance(selected_city, str) else ", ".join(selected_city)
            time_pie, last_labels = extract_label(pie_clickData, key='label', figure_id="pie-chart", last_labels=last_labels)
            weather_bar, last_labels = extract_label(bar_weather_clickData, key='y', figure_id="bar-chart-weather", last_labels=last_labels)
            logos_bar, last_labels = extract_label(bar_clickData, key='x', figure_id="bar-plot-logos", last_labels=last_labels)
            source_pie, last_labels = extract_label(pie2_clickData, key='label', figure_id="source-pie", last_labels=last_labels)

            # No filters applied => filter_comp_data = []
            filter_comp_data = compute_filter_comp(
                filtered_df=df_current,
                original_total=original_total,
                city_name=city_label,
                selected_terrain=selected_terrain,
                selected_occluded=selected_occluded,
                selected_VQ=selected_VQ,
                selected_tilt=selected_tilt,
                selected_distance=selected_distance,
                selected_distortions=selected_distortions,
                pie_clickData = time_pie,
                bar_weather_clickData=weather_bar,
                bar_clickData= logos_bar,
                pie2_clickData= source_pie)

            return (
                map_center,
                city_markers,
                polygon_layer,
                terrain_options,
                'All',
                occlusion_options,
                'All',
                vq_options,
                'All',
                camera_tilt_options,
                'All',
                distance_options,
                'All',
                distortions_options,
                'All',
                record_count,
                drop_count,
                min_dur,
                max_dur,
                [min_dur, max_dur],
                round((max_dur/6),2),
                city_time_of_day_pie,
                city_weather_bar,
                city_logos_bar,
                city_source_pie,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                dash.no_update,
                title,
                df_current.to_dict('records'),
                table_columns,
                df_current.to_dict('records'),
                reset_clicked,
                {"display": "block"},
                polygon_active,
                dash.no_update,
                filter_comp_data,
                filter_comp_data,
                load_clicked,
                "",coords_list,False,False,"",gen_summary,original_total,last_labels
                ,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update
            )
        else:
            # We do have data in current_data => user changed a filter

            rec_df= pd.DataFrame(city_rec_data)

            if city_rec_clickdata:
                bar3_click = city_rec_clickdata['points'][0]['x']
                rec_df = rec_df[rec_df['City'] == bar3_click] 
                
                city_rec_bar, last_labels = extract_label(city_rec_clickdata, key='x', figure_id="compare-bar", last_labels=last_labels)
                sheet_ids, sheet_ranges, polygon_ids = load_selected_cities(city_rec_bar)
                sheet_ids=sheet_ids[0]
                sheet_ranges=sheet_ranges[0]
                polygons_list = []
                for sid, srange, pid in zip(sheet_ids, sheet_ranges, polygon_ids):
                    # Load polygon data
                    request = drive_service.files().get_media(fileId=pid)
                    polygon_bytes = request.execute()
                    try:
                        if isinstance(polygon_bytes, bytes):
                            polygon_data = json.loads(polygon_bytes.decode('utf-8'))
                        else:
                            polygon_data = json.loads(polygon_bytes)
                    except Exception:
                        polygon_data = []
                    poly_coords = [tuple(coord) for coord in polygon_data]
                    polygons_list.append(poly_coords)
                    
                df_selected_city = load_city(sheet_ids, sheet_ranges)             
                original_total = len(df_selected_city[df_selected_city['Coordinates'].apply(is_valid_coord)])
                
                # Keep only rows with valid coordinates
                df_selected_city = df_selected_city[df_selected_city['Coordinates'].apply(is_valid_coord)]
                df_selected_city['Coordinates'] = df_selected_city['Coordinates'].apply(clean_coordinate)
                
                terrain_options = build_options(df_selected_city, 'Terrain')
                occlusion_options = build_options(df_selected_city, 'Occluded')
                vq_options = build_options(df_selected_city, 'Video quality')
                camera_tilt_options = build_options(df_selected_city, 'Camera tilt')
                distance_options = build_options(df_selected_city, 'Distance from building')
                distortions_options = build_options(df_selected_city, 'Distortions')

                df_selected_city = df_selected_city[df_selected_city['Coordinates'].str.contains(',', na=False)]
                temp = df_selected_city['Coordinates'].str.split(',', n=1, expand=True)
                df_selected_city['Latitude'] = pd.to_numeric(temp[0], errors='coerce')
                df_selected_city['Longitude'] = pd.to_numeric(temp[1], errors='coerce')
                city_markers = create_map_markers(df_selected_city)
                coords_list= df_selected_city['Coordinates'].unique()

                if polygons_list and len(polygons_list) > 0:
                    city_polygon = Polygon(polygons_list[0])
                else:
                    city_polygon = None

                count_within = sum(
                    city_polygon.contains(Point(row['Latitude'], row['Longitude']))
                    for _, row in df_selected_city.iterrows()
                    if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude'])
                ) if city_polygon else 0

                pre_out_city = round(((len(df_selected_city) - count_within) / len(df_selected_city) * 100), 2) if len(df_selected_city)>0 else 0

                if 'Duration' not in df_selected_city.columns:
                    df_selected_city['Duration'] = df_selected_city['Finish Time'].apply(convert_to_minutes) - df_selected_city['Start Time'].apply(convert_to_minutes)
                df_selected_city.dropna(subset=['Latitude', 'Longitude'], inplace=True)
                min_dur = df_selected_city['Duration'].min() if not df_selected_city['Duration'].empty else 0
                max_dur = df_selected_city['Duration'].max() if not df_selected_city['Duration'].empty else 100

                record_count = f"Total Records: {len(df_selected_city)}"
                drop_count = f"{pre_out_city} % out of Polygon"

                if city_markers:
                    random_marker = random.choice(city_markers)
                    map_center = random_marker.position
                else:
                    map_center = (41.9028, 12.4964)

                title = f"Airis-Labs: Geo-Location Analysis - {city_rec_bar}"

                # Build final charts
                city_country_bar = generate_interactive_countries_compaered_bar_plot(rec_df) 

                pie_fig = generate_interactive_pie_chart_city(df_selected_city)
                weather_bar_fig = generate_interactive_bar_chart_weather_city(df_selected_city)
                logos_bar_fig = generate_interactive_bar_plot_2_city(df_selected_city)
                source_pie_fig = generate_interactive_pie_chart_source(df_selected_city)
                
                gen_summary = general_summary(df_selected_city)        
                city_label =   city_rec_bar            
    
                pie_fig = generate_interactive_pie_chart_city(df_selected_city)
                weather_bar_fig = generate_interactive_bar_chart_weather_city(df_selected_city)
                logos_bar_fig = generate_interactive_bar_plot_2_city(df_selected_city)
                source_pie_fig = generate_interactive_pie_chart_source(df_selected_city)
                total_cities = f"Total Cities: 1"
                
            else:
                
                df_filtered = apply_all_filters2(
                    df=df_current,
                    duration_range=duration_range,
                    selected_terrain=selected_terrain,
                    selected_occluded=selected_occluded,
                    selected_VQ=selected_VQ,
                    selected_tilt=selected_tilt,
                    selected_distance=selected_distance,
                    selected_distortions=selected_distortions,
                    bar_weather_clickData=bar_weather_clickData,
                    pie_clickData=pie_clickData,
                    pie_2_clickData=pie2_clickData,
                    bar_2_clickData=bar_clickData,
                    polygon_active=polygon_active
                )                   
                terrain_options = build_options(df_filtered, 'Terrain')
                occlusion_options = build_options(df_filtered, 'Occluded')
                vq_options = build_options(df_filtered, 'Video quality')
                camera_tilt_options = build_options(df_filtered, 'Camera tilt')
                distance_options = build_options(df_filtered, 'Distance from building')
                distortions_options = build_options(df_filtered, 'Distortions')

                # Build final charts
                city_country_bar = generate_interactive_countries_compaered_bar_plot(rec_df) 

                pie_fig = generate_interactive_pie_chart_city(df_filtered)
                weather_bar_fig = generate_interactive_bar_chart_weather_city(df_filtered)
                logos_bar_fig = generate_interactive_bar_plot_2_city(df_filtered)
                source_pie_fig = generate_interactive_pie_chart_source(df_filtered)
                
                
                gen_summary = general_summary(df_filtered)
                city_rec_bar, last_labels = extract_label(city_rec_clickdata, key='x', figure_id="compare-bar", last_labels=last_labels)
                if city_rec_bar !='All':
                    city_label=city_rec_bar
                else:
                    city_label = selected_city if isinstance(selected_city, str) else ", ".join(selected_city)
                # Convert selected_city to a string if it is a list
                time_pie, last_labels = extract_label(pie_clickData, key='label', figure_id="pie-chart", last_labels=last_labels)
                weather_bar, last_labels = extract_label(bar_weather_clickData, key='y', figure_id="bar-chart-weather", last_labels=last_labels)
                logos_bar, last_labels = extract_label(bar_clickData, key='x', figure_id="bar-plot-logos", last_labels=last_labels)
                source_pie, last_labels = extract_label(pie2_clickData, key='label', figure_id="source-pie", last_labels=last_labels)
                
                df_filtered = df_filtered[df_filtered['Coordinates'].str.contains(',', na=False)]
                temp = df_filtered['Coordinates'].str.split(',', n=1, expand=True)
                df_filtered['Latitude'] = pd.to_numeric(temp[0], errors='coerce')
                df_filtered['Longitude'] = pd.to_numeric(temp[1], errors='coerce')
                city_markers = create_map_markers(df_filtered)
                coords_list= df_filtered['Coordinates'].unique()


                polygons_list = polygon_coords_store if polygon_coords_store else []
                if polygons_list and len(polygons_list) > 0:
                    city_polygon = Polygon(polygons_list[0])

                else:
                    city_polygon = None

                count_within = sum(
                    is_inside_any(row['Latitude'], row['Longitude'], polygons_list)
                    for _, row in df_filtered.iterrows()
                    if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude'])
                )

                pre_out_city = round(((len(df_filtered) - count_within) / len(df_filtered) * 100), 2) if len(df_filtered)>0 else 0

                if 'Duration' not in df_filtered.columns:
                    df_filtered['Duration'] = df_filtered['Finish Time'].apply(convert_to_minutes) - df_filtered['Start Time'].apply(convert_to_minutes)
                df_filtered.dropna(subset=['Latitude', 'Longitude'], inplace=True)
                min_dur = df_filtered['Duration'].min() if not df_filtered['Duration'].empty else 0
                max_dur = df_filtered['Duration'].max() if not df_filtered['Duration'].empty else 100

                record_count = f"Total Records: {len(df_filtered)}"
                drop_count = f"{pre_out_city} % out of Polygon"

                if city_markers:
                    random_marker = random.choice(city_markers)
                    map_center = random_marker.position
                else:
                    map_center = (41.9028, 12.4964)


                
                if filter_comp_store is not None:
                    # Check if city_label already exists in filter_comp_store

                    city_entry = next((entry for entry in filter_comp_store if entry.get('City') == city_label), None)

                    if city_entry is None:
                        # City does not exist, add new computed filter data
                        filter_comp_data = filter_comp_store + compute_filter_comp(
                            filtered_df=df_filtered,
                            original_total=original_total,
                            city_name=city_label,
                            selected_terrain=selected_terrain,
                            selected_occluded=selected_occluded,
                            selected_VQ=selected_VQ,
                            selected_tilt=selected_tilt,
                            selected_distance=selected_distance,
                            selected_distortions=selected_distortions,
                            pie_clickData = time_pie,
                            bar_weather_clickData=weather_bar,
                            bar_clickData= logos_bar,
                            pie2_clickData= source_pie
                        )
                    else:
                        # City exists, check if filters and values match
                        
                        new_filter_data = compute_filter_comp(
                            filtered_df=df_filtered,
                            original_total=original_total,
                            city_name=city_label,
                            selected_terrain=selected_terrain,
                            selected_occluded=selected_occluded,
                            selected_VQ=selected_VQ,
                            selected_tilt=selected_tilt,
                            selected_distance=selected_distance,
                            selected_distortions=selected_distortions,
                            pie_clickData = time_pie,
                            bar_weather_clickData=weather_bar,
                            bar_clickData= logos_bar,
                            pie2_clickData= source_pie
                        )[0]  # Assuming compute_filter_comp returns a list

                        # Check if filters and values match
                        filters_match = all(
                            city_entry.get(key) == new_filter_data.get(key)
                            for key in ["Filters", "fvalue","Percentage",'total']
                        )

                        if not filters_match:
                            # Update the existing city's filters and values
                            city_entry.update(new_filter_data)
                            filter_comp_data = filter_comp_store  # Updated list with modified entry
                        else:
                            # If filters and values are the same, do nothing
                            filter_comp_data = filter_comp_store
                else:
                    # If filter_comp_store is None, compute fresh data
                    filter_comp_data = compute_filter_comp(
                        filtered_df=df_filtered,
                        original_total=original_total,
                        city_name=city_label,
                        selected_terrain=selected_terrain,
                        selected_occluded=selected_occluded,
                        selected_VQ=selected_VQ,
                        selected_tilt=selected_tilt,
                        selected_distance=selected_distance,
                        selected_distortions=selected_distortions,
                        pie_clickData = time_pie,
                        bar_weather_clickData=weather_bar,
                        bar_clickData= logos_bar,
                        pie2_clickData= source_pie
                    )
                return (
                    map_center,
                    city_markers,
                    dash.no_update,
                    terrain_options,
                    selected_terrain,
                    occlusion_options,
                    selected_occluded,
                    vq_options,
                    selected_VQ,
                    camera_tilt_options,
                    selected_tilt,
                    distance_options,
                    selected_distance,
                    distortions_options,
                    selected_distortions,
                    record_count,
                    drop_count,
                    min_dur,
                    max_dur,
                    [min_dur, max_dur],
                    round((max_dur/6),2),
                    pie_fig,
                    weather_bar_fig,
                    logos_bar_fig,
                    source_pie_fig,
                    pie_clickData,
                    bar_clickData,
                    bar_weather_clickData,
                    pie2_clickData,
                    dash.no_update,
                    df_filtered.to_dict('records'),
                    dash.no_update,
                    df_filtered.to_dict('records'),
                    reset_clicked,
                    {"display": "block"},
                    polygon_active,
                    dash.no_update,
                    filter_comp_data,  # Single row or empty
                    filter_comp_data,
                    load_clicked,
                    "",coords_list,False,False,"",gen_summary,
                    dash.no_update,last_labels,dash.no_update,city_country_bar,dash.no_update,city_rec_clickdata,rec_df.to_dict('records'),dash.no_update)       

            return (
                map_center,
                city_markers,
                dash.no_update,
                terrain_options,
                selected_terrain,
                occlusion_options,
                selected_occluded,
                vq_options,
                selected_VQ,
                camera_tilt_options,
                selected_tilt,
                distance_options,
                selected_distance,
                distortions_options,
                selected_distortions,
                record_count,
                drop_count,
                min_dur,
                max_dur,
                [min_dur, max_dur],
                round((max_dur/6),2),
                pie_fig,
                weather_bar_fig,
                logos_bar_fig,
                source_pie_fig,
                pie_clickData,
                bar_clickData,
                bar_weather_clickData,
                pie2_clickData,
                title,
                df_selected_city.to_dict('records'),
                dash.no_update,
                df_selected_city.to_dict('records'),
                reset_clicked,
                {"display": "block"},
                polygon_active,
                polygons_list,
                dash.no_update,  # Single row or empty
                dash.no_update,
                load_clicked,
                "",coords_list,False,False,"",gen_summary,
                original_total,last_labels,total_cities,city_country_bar,dash.no_update,city_rec_clickdata,rec_df.to_dict('records')
                ,dash.no_update
            )

app.layout = html.Div(
    [
        dcc.Tabs(
            [
                dcc.Tab(label='Geo-Location', children=tab_layout(), style=tab_style, selected_style=selected_tab_style),
            ]
        )
    ]
)


def add_image_to_tab(content):
    """Add a small logo to the top-left corner of each tab."""
    return html.Div([
        # Add the logo at the top-left corner
        html.Img(
            src="/assets/airis-logo.png",  # Dash automatically serves files from `assets`
            style={
                'position': 'absolute',
                'top': '10px',
                'center': '10px',
                'height': '70px',
                'width': '70px',
            }
        ),
        # Content of the tab
        html.Div(content, style={'margin-top': '60px'})  # Adjust margin to avoid overlapping
    ], style={'position': 'relative', 'backgroundColor': colors['background'], 'padding': '20px'})

predefined_audio_events = [
    "Barking", "Shouting", "Gunshots", "Explosion", "Music", "Jackhammer",
    "Crowd", "Crying", "Traffic", "People talking", "Alarm", "Engine",
    "Buzzing", "Shofar", "Whistle", "Siren", "Street"
]

# Compile a case-insensitive regex pattern for these words
audio_event_pattern = re.compile(r"\b(" + "|".join(predefined_audio_events) + r")\b", re.IGNORECASE)

# Function to extract matching audio events
def extract_audio_events_from_predefined_list(webvtt_text):
    if not isinstance(webvtt_text, str):
        return []  # Skip non-string values
    matches = audio_event_pattern.findall(webvtt_text)
    return [match.capitalize() for match in matches]  

# Step 1: Iterate over the column and collect all valid audio events
all_audio_events = []
for content in df3["override_translation"]:
    audio_events = extract_audio_events_from_predefined_list(content)
    all_audio_events.extend(audio_events)

# Create a DataFrame of all valid audio events
df_audio_events = pd.DataFrame(all_audio_events, columns=['Audio Event'])

# Step 2: Save audio events into an SQLite database
conn = sqlite3.connect("audio_events.db")  # Creates or connects to `audio_events.db`

# Append audio events to a table
df_audio_events.to_sql('audio_events', conn, if_exists='replace', index=False)

# Step 3: Query the database to group and count each audio event
query = """
SELECT `Audio Event`, COUNT(*) as Count
FROM audio_events
GROUP BY `Audio Event`
ORDER BY Count DESC
"""

# Execute the query and save the result into a new DataFrame
df_audio_event_counts = pd.read_sql_query(query, conn)

# Close the database connection Total_ann_hours_per_user
conn.close()

def create_objects_tab():
    """Create the 'Objects' tab layout."""
    return dcc.Tab(
        label='Objects',
        children=[

            # Row: Number chart and Dynamic Color Pie chart
            html.Div([
                create_attributes_axis_dropdown('att_selection'),
                create_objects_axis_dropdown('obj_selection'),
                html.Div([
                    dcc.Graph(
                        id='number-chart-videos',
                        style={
                            'border': '1px solid #ddd',
                            'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                            'borderRadius': '8px'
                        }
                    )
                ], style={'flex': '1', 'marginRight': '10px'}),

                html.Div([
                    dcc.Graph(
                        id='OD-color-pie',  # 🔄 now dynamic via callback
                        style={
                            'border': '1px solid #ddd',
                            'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                            'borderRadius': '8px'
                        }
                    )
                ], style={'flex': '1'})
            ], style={
                'display': 'flex',
                'flexDirection': 'row',
                'gap': '20px',
                'marginBottom': '30px',
                'padding': '20px',
                'backgroundColor': colors['background'],
                'borderRadius': '8px'
            }),

            # Bar Plot Section
            html.Div([
                html.H3("Bar Plot", style={
                    'textAlign': 'center', 'fontSize': '24px',
                    'color': colors['text'], 'fontWeight': 'bold'
                }),
                dcc.Graph(
                    id='scatter-plot',
                    style={
                        'border': '5px solid #ddd',
                        'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                        'borderRadius': '20px'
                    }
                )
            ], style={
                'marginBottom': '40px',
                'padding': '60px',
                'backgroundColor': colors['background'],
                'borderRadius': '20px',
                'width': '100%',
                'margin': 'auto'
            }),     
            # Treemap Section
            html.Div([
                html.H3("Objects Treemap", style={
                    'textAlign': 'center',
                    'fontSize': '24px',
                    'color': colors['text'],
                    'fontWeight': 'bold'
                }),
                html.P([
                    "You can click on the object that you want to and it will filter the bar chart above to videos that contain the picked object.",
                    html.Br(),
                    "Also you can interact with the slider below to filter object annotation count in a given range."
                ], style={
                    'color': colors['text'],
                    'textAlign': 'center',
                    'marginBottom': '10px',
                    'fontWeight': 'bold',
                    'fontSize': '20px'
                }),
                create_slider_treemap('my-slider'),
                html.Button(
                    'Reset Filters',
                    id='reset-button',
                    n_clicks=0,
                    style={
                        'display': 'block',
                        'margin': '0 auto',
                        'padding': '10px',
                        'backgroundColor': '#2ECC40',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '8px'
                    }
                ),
                dcc.Graph(
                    id='objects-treemap',
                    style={
                        'border': '1px solid #ddd',
                        'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                        'borderRadius': '8px'
                    }
                )
            ], style={
                'marginBottom': '30px',
                'padding': '20px',
                'backgroundColor': colors['background'],
                'borderRadius': '8px'
            }),

            # Attribute Bar Chart
            html.Div([
                html.H3(
                    "This bar chart shows the instances of attributes in the annotations",
                    style={
                        'textAlign': 'center',
                        'fontSize': '24px',
                        'color': colors['text'],
                        'fontWeight': 'bold'
                    }
                ),
                dcc.Graph(
                    figure=bar_attributes(),
                    style={
                        'border': '1px solid #ddd',
                        'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                        'borderRadius': '8px'
                    }
                )
            ], style={
                'marginBottom': '30px',
                'padding': '20px',
                'backgroundColor': colors['background'],
                'borderRadius': '8px'
            }),

            # Dropdown Pie Chart
            html.Div([
                html.H3("Pick an attribute to see distribution", style={
                    'textAlign': 'center',
                    'fontSize': '24px',
                    'color': colors['text'],
                    'fontWeight': 'bold'
                }),
                dcc.Dropdown(
                    id='df-dropdown_OD',
                    options=[
                        {'label': 'Blur', 'value': 'blurry'},
                        {'label': 'Occlusion', 'value': 'occluded'},
                        {'label': 'Truncation', 'value': 'truncated'}
                    ],
                    value='blurry',
                    clearable=False,
                    style={'width': '50%', 'margin': '0 auto', 'display': 'block'}
                ),
                dcc.Graph(
                    id='OD-pie',
                    style={
                        'border': '1px solid #ddd',
                        'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                        'borderRadius': '8px'
                    }
                )
            ], style={
                'marginBottom': '30px',
                'padding': '20px',
                'backgroundColor': colors['background'],
                'borderRadius': '8px'
            }),

            # Gauge Chart for Objects
            html.Div([
                html.H3(
                    "Select an object to view the number of annotations associated with it",
                    style={
                        'textAlign': 'center',
                        'fontSize': '24px',
                        'color': colors['text'],
                        'fontWeight': 'bold'
                    }
                ),
                create_y_axis_dropdown('y-axis-dropdown-overall', 'total', include_video_name=False),
                dcc.Graph(
                    id='gauge-indicator-total',
                    style={
                        'border': '1px solid #ddd',
                        'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                        'borderRadius': '8px'
                    }
                )
            ], style={
                'marginBottom': '30px',
                'padding': '20px',
                'backgroundColor': colors['background'],
                'borderRadius': '8px'
            }),

            # Data Table Section
            html.H3("Select a row to see data for each video.", style={
                'textAlign': 'center',
                'fontSize': '24px',
                'color': colors['text'],
                'fontWeight': 'bold'
            }),
            html.P([
                "You can also search for a criterion in the search bar above each column in the table and press Enter or you can click the check box to see the video details below."
            ], style={
                'color': colors['text'],
                'textAlign': 'center',
                'marginBottom': '10px',
                'fontWeight': 'bold',
                'fontSize': '20px'
            }),
            create_OD_attributes(),
            html.Div(id='datatable-interactivity-container-od', style={'marginTop': '20px'}),
            html.Ul([
                html.Li("Info on the whole database:"),
                html.Li(f"This table shows the data of '{vid_count}' videos"),
                html.Li(f"There are a total of '{total_frames_ann}' frames annotated")
            ], style={
                'marginTop': '20px',
                'color': colors['text'],
                'fontSize': '16px'
            }),

            # Average Gauge Section
            html.Div([
                create_average_annotations_gauge()
            ])
        ]
    )





def create_attributes_axis_dropdown(id):
    """Create a dropdown for selecting the y-axis value."""
    options = [{'label': col, 'value': col} for col in OD_ATT_FILT.columns]
    return dcc.Dropdown(id=id, options=options, multi= True, clearable=True, style={'width': '50%', 'margin': '0 auto', 'display': 'block'})

def create_objects_axis_dropdown(id):
    """Create a dropdown for selecting object names from the 'object_name' column."""
    if 'object_name' not in OD_ATT.columns:
        return html.Div("⚠️ 'object_name' column not found in data.")

    object_names = OD_ATT['object_name'].dropna().unique()
    options = [{'label': name, 'value': name} for name in sorted(object_names)]

    return dcc.Dropdown(
        id=id,
        options=options,
        multi=True,
        clearable=True,
        placeholder="Select object(s)...",
        style={'width': '50%', 'margin': '0 auto', 'display': 'block'}
    )


def create_y_axis_dropdown(id, default_value, include_video_name=True):
    """Create a dropdown for selecting the y-axis value."""
    options = [{'label': col, 'value': col} for col in transposed_df_obj_ann.columns if include_video_name or col != 'Video Name']
    return dcc.Dropdown(id=id, options=options, value=default_value, clearable=False, style={'width': '50%', 'margin': '0 auto', 'display': 'block'})

num_columns = len(df.columns) - 1
num_columns = float(num_columns)
total_annotations = df.iloc[1:, 1:-1].sum().sum()
total_annotations = float(total_annotations)
average_ann_per_object = total_annotations / num_columns if num_columns > 0 else 0


# Create the gauge figure
average_gauge_fig = go.Figure(go.Indicator(
    mode="gauge+number",
    value=average_ann_per_object,
    title={'text': "Average Annotations per Object"},
    gauge={
        'axis': {'range': [0, max(10, average_ann_per_object + 5)]},  # Adjust range as needed
        'bar': {'color': "#7FDBFF"},
        'steps': [
            {'range': [0, 5], 'color': "#FF4136"},
            {'range': [5, 10], 'color': "#2ECC40"}
        ],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': average_ann_per_object
        }
    }
))

average_gauge_fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

def create_average_annotations_gauge():
    """Create the gauge for average annotations per object."""
    return html.Div([
        html.H2("Average Annotations per Object", style={'textAlign': 'center', 'color': colors['text']}),
        dcc.Graph(
            figure=average_gauge_fig,
            style={
                'width': '70%',
                'height': '400px',
                'border': '1px solid #ddd',
                'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                'borderRadius': '8px'
            }
        )
    ], style={
        'display': 'flex',
        'flexDirection': 'column',
        'justify-content': 'center',
        'align-items': 'center',
        'height': '500px',
        'padding': '20px',
        'backgroundColor': colors['background'],
        'borderRadius': '8px'
    })

def create_slider_treemap(id):
    """Create a range slider for the treemap."""
    reset_df = transposed_df.iloc[:-1 , :].reset_index()
    min_val = reset_df['Total'].min()
    min_val = int(min_val)
    max_val = reset_df['Total'].max()
    max_val = int (max_val)
    return dcc.RangeSlider(
        id=id,
        min=min_val,
        max=max_val,
        step=1,
        value=[min_val, max_val],  # Initial selected range
        marks={
            int(min_val): str(int(min_val)),
            int(max_val): str(int(max_val))
        },
        
    )


statuus = []

for x in df3["status"] : 
    if x == "Done" :
         statuus.append(x)
    elif x == "ongoing" : 
        statuus.append(x)
    elif x == "Not started" : 
        statuus.append(x)
        
statuus2 = pd.DataFrame(statuus)
def pie_NLP():
    
    # Count the occurrences of each unique status
    statuus_counts = statuus2[0].value_counts()  # Access the first column of the DataFrame
    labels1 = statuus_counts.index.tolist()  # Get unique values as labels
    values1 = statuus_counts.tolist()  # Get counts as values

    # Create the pie chart
    fig = px.pie(values=values1, names=labels1, title="Status" ,color_discrete_sequence=["#00FFFF", "#1E90FF", "#00BFFF", "#5F9EA0", "#4682B4"])
    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Annotations: %{value}<extra></extra>'
    )

    return fig
def pie_audio_events():
    """
    Create a pie chart for audio events counts.

    Returns:
        fig (plotly.graph_objects.Figure): Pie chart figure for audio events.
    """
    # Ensure df_audio_event_counts is properly formatted
    values = df_audio_event_counts['Count']  # Access the Count column
    labels = df_audio_event_counts['Audio Event']  # Access the Audio Event column

    # Create the pie chart
    fig = px.pie(
        values=values,
        names=labels,
        title="Audio Events Distribution"
    )
    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Occurrences: %{value}<extra></extra>'
    )

    return fig


def create_NLP_table():
    """
    Create the layout for the NLP table and associated statistics.

    Returns:
        html.Div: Dash layout containing the table, statistics, and pie charts.
    
    # Data table for NLP data
    table_nlp = dash_table.DataTable(
    id="nlp-table",
    columns=[{"name": i, "id": i} for i in df3.columns],  # Set columns from DataFrame
    data=df3.to_dict('records'),  # Convert DataFrame to list of records
    editable=True,
    filter_action="native",
    sort_action="native",
    sort_mode="multi",
    column_selectable="single",
    row_selectable="multi",
    row_deletable=True,
    page_action="native",
    page_current=0,
    page_size=40,
    style_table={
        'overflowX': 'auto',  # Enable horizontal scrolling
        'maxWidth': '100%'  # Optional: Limit max width of the table
    },
    style_cell={
        'backgroundColor': colors['background'],  # Background color for table cells
        'color': colors['text'],  # Text color
        'textAlign': 'left',  # Text alignment
        'padding': '5px',  # Padding inside cells
        'fontSize': '14px',  # Font size for cell content
        'border': '1px solid #444'  # Optional: Border color and style
    },
    style_header={
        'backgroundColor': '#444',  # Background color for header
        'color': colors['text'],  # Text color for header
        'fontWeight': 'bold',  # Bold text for header
        'border': '1px solid #333'  # Optional: Border color for header
    },
    style_data={
        'backgroundColor': colors['background'],  # Row background color
        'color': colors['text'],  # Text color for rows
        'border': '1px solid #444'  # Optional: Border color for rows
    },
    style_data_conditional=[
        # Example: Highlight selected rows
        {
            'if': {'state': 'selected'},  # Apply styles when a row is selected
            'backgroundColor': '#2ECC40',  # Highlight color
            'color': 'white'  # Text color for selected row
        }
    ]
)"""


    # Pie chart for audio events
    pie_chart2 = dcc.Graph(
        figure=pie_audio_events(),
        style={'border': '1px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'}
    )

    return html.Div([
        html.Div([
            html.H3("NLP Table Overview", style={
                'color': colors['text'],
                'textAlign': 'center',
                'margin-bottom': '20px'
            }),
            html.P(
            "You can search for a criterion in the search bar above each column in the table and press Enter or you can click the check box to see the video details below.",
            style={
                'color': colors['text'],
                'textAlign': 'center',
                'margin-bottom': '10px', 
                'fontWeight': 'bold',
                'fontSize' : '20px'
            }
        ),
            html.H3("Pie Chart for NLP Status", style={
                'color': colors['text'],
                'textAlign': 'center',
                'margin-top': '40px',
                'margin-bottom': '20px'
            }),
            pie_chart2  # Add the second pie chart
        ], style={'padding': '20px', 'backgroundColor': colors['background']})
    ])

       
@app.callback(
    Output('datatable-interactivity', 'style_data_conditional'),
    Input('datatable-interactivity', 'selected_columns')
)
def update_styles(selected_columns):
    return [{
        'if': { 'column_id': i },
        'background_color': '#D2F3FF'
    } for i in selected_columns]

@app.callback(
    Output('datatable-interactivity-container', 'children'),
    [Input('nlp-table', 'selected_rows')],
    [Input('nlp-table', 'data')]
)
def display_row_explanation(selected_rows, data):
    """Display explanations based on the selected row in the DataTable."""
    if not selected_rows:
        return html.P("Click on a row to see its details.", style={'color': colors['text']})

    # Extract the data for the selected rows
    selected_data = [data[i] for i in selected_rows]
    explanations = []
    
    for row in selected_data:
        # Example explanation logic based on selected row data
        video_name = row.get('file_name', 'Unknown')
        video_length = row.get('video_length_secs', 'Unknown')
        video_length_fixed = round(video_length,2)
        file_size = row.get('size_in_mb', 'Unknown')
        upload_date = row.get('upload_date', 'Unknown')
        explanation = f"""
        The video '{video_name}' has a length of {video_length_fixed} seconds and its size is {file_size} Mbs and it was uploaded at {upload_date}.
        """
        explanations.append(html.P(explanation, style={'color': colors['text']}))

    return html.Div(explanations)

def create_table_tab():
    return dcc.Tab(
        children=[
        html.Div([
      
    html.H4("Select Dataset"),
    dcc.Dropdown(
        id='dataset-selector',
        options=[
            {'label': 'OD Dataset', 'value': 'od'},
            {'label': 'POI Dataset', 'value': 'poi'}
        ],
        value='od',
        clearable=False,
        style={'width': '300px', 'margin': '10px auto'}
    ),
    html.H3("This bar chart shows the total working hours per user in correlation to the tasks submitted", style={
                    'textAlign': 'center',
                    'fontSize': '24px',
                    'color': colors['text'],
                    'fontWeight': 'bold'
                }),
    dcc.Graph(id='bar-hours-tasks', style={
                    'border': '5px solid #ddd',
                    'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                    'borderRadius': '20px'
                })
], style={
                'margin-bottom': '40px',
                'padding': '30px',
                'backgroundColor': colors['background'],
                'borderRadius': '20px',
                'width': '70%',
                'margin': 'auto'
            }
) ,
html.Div([
    dcc.Graph(id='rejection-rate-bar', style={
                    'border': '5px solid #ddd',
                    'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                    'borderRadius': '20px'
                })
], style={
                'margin-bottom': '40px',
                'padding': '30px',
                'backgroundColor': colors['background'],
                'borderRadius': '20px',
                'width': '70%',
                'margin': 'auto'
            }
),
html.Div([
    dcc.Graph(id='avg-work-time-bar', style={
                    'border': '5px solid #ddd',
                    'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                    'borderRadius': '20px'
                })
], style={
                'margin-bottom': '40px',
                'padding': '30px',
                'backgroundColor': colors['background'],
                'borderRadius': '20px',
                'width': '70%',
                'margin': 'auto'
            }
) , 
html.Div([
    dcc.Graph(id='rejection-rate-pie', style={
                    'border': '5px solid #ddd',
                    'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                    'borderRadius': '20px'
                })
], style={
                'margin-bottom': '40px',
                'padding': '30px',
                'backgroundColor': colors['background'],
                'borderRadius': '20px',
                'width': '70%',
                'margin': 'auto'
            }
),



html.Div([
    dcc.Graph(id='generate_avg_time_per_user', style={
                    'border': '5px solid #ddd',
                    'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)',
                    'borderRadius': '20px'
                })
], style={
                'margin-bottom': '40px',
                'padding': '30px',
                'backgroundColor': colors['background'],
                'borderRadius': '20px',
                'width': '70%',
                'margin': 'auto'
            }
)


])
    



# Heatmap Chart Tab
def voice_rec():

    return dcc.Tab(label='Voice Recognition Analysis', children=[
      html.Div(style={'display': 'flex', 'justifyContent': 'space-around', 'padding': '20px', 'background': '#F7F7F7'}, children=[
        
        html.Div(children=[
            html.H4("Voice Gender", style={'textAlign': 'center', 'color': '#333'}),
            dcc.Graph(figure=Male_female_voice(), style={'width': '100%', 'height': '250px'})
        ], style={'width': '30%', 'background': 'white', 'padding': '10px', 'border-radius': '10px', 'box-shadow': '2px 2px 10px lightgray'}),
        
        html.Div(children=[
            html.H4("Dominant Analysis", style={'textAlign': 'center', 'color': '#333'}),
            dcc.Graph(figure=Dominant(), style={'width': '100%', 'height': '250px'})
        ], style={'width': '30%', 'background': 'white', 'padding': '10px', 'border-radius': '10px', 'box-shadow': '2px 2px 10px lightgray'}),
        
        html.Div(children=[
            html.H4("Face Show", style={'textAlign': 'center', 'color': '#333'}),
            dcc.Graph(figure=Face_show(), style={'width': '100%', 'height': '250px'})
        ], style={'width': '30%', 'background': 'white', 'padding': '10px', 'border-radius': '10px', 'box-shadow': '2px 2px 10px lightgray'})
    ]),

    # Graph Title Section
    html.Div([
        dcc.Graph(figure=language_bar(df_voice), style={'color': 'gray', 'margin-left': '10px'})
    ], style={'padding': '10px'})

])

def snips_table() : 
    snips_df['file_path'] = snips_df['file_path'].astype(str)
    snips_table = dash_table.DataTable(
    id="snips-table",
    columns=[{"name": i, "id": i} for i in snips_df.columns],  # Set columns from DataFrame
    data=snips_df.to_dict('records'),  # Convert DataFrame to list of records
    editable=True,
    filter_action="native",
    sort_action="native",
    sort_mode="multi",
    column_selectable="single",
    row_selectable="multi",
    row_deletable=True,
    page_action="native",
    page_current=0,
    page_size=40,
    style_table={
        'overflowX': 'auto',  # Enable horizontal scrolling
        'maxWidth': '100%'  # Optional: Limit max width of the table
    },
    style_cell={
        'backgroundColor': colors['background'],  # Background color for table cells
        'color': colors['text'],  # Text color
        'textAlign': 'left',  # Text alignment
        'padding': '5px',  # Padding inside cells
        'fontSize': '14px',  # Font size for cell content
        'border': '1px solid #444'  # Optional: Border color and style
    },
    style_header={
        'backgroundColor': '#444',  # Background color for header
        'color': colors['text'],  # Text color for header
        'fontWeight': 'bold',  # Bold text for header
        'border': '1px solid #333'  # Optional: Border color for header
    },
    style_data={
        'backgroundColor': colors['background'],  # Row background color
        'color': colors['text'],  # Text color for rows
        'border': '1px solid #444'  # Optional: Border color for rows
    }
    )
    return snips_table
        

def create_empty_tab(label, content=[]):
    """Create an empty tab with the given label and content."""
    return dcc.Tab(label=label, children=[
        html.Div(
            content, style={'padding': '50px', 'backgroundColor': colors['background'], 'borderRadius': '8px', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)'})])

maxx = df2["Overall Frames Annotated"].max()
bar_lim = maxx + 3000
sheet1_content = [
    # Overview Section
    html.Div(
        [
           
            html.H3("Face frames Overview", style={'color': colors['text'], 'textAlign': 'center'}),
            dcc.Graph(
                
                figure=px.bar(
                    df2,
                    x="Video Title",
                    y="Overall Frames Annotated",
                    title="Overall Annotated per Video",
                    text = "Overall Frames Annotated"
                ).update_layout(
                    plot_bgcolor=colors['background'],
                    paper_bgcolor=colors['background'],
                    font_color=colors['text'],
                    yaxis = dict(range = [0 , bar_lim])
                ).update_traces(
            textposition='outside',
            texttemplate='%{text}',
            marker_color='LightSkyBlue'
            ),   
                style={
                    'border': '1px solid #333',
                    'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.5)',
                    'borderRadius': '8px',
                    'padding': '20px',
                    'backgroundColor': colors['background']
                }
            )
        ],
        style={
            'margin-bottom': '30px',
            'padding': '20px',
            'backgroundColor': colors['background'],
            'borderRadius': '8px'
        }
    ),
            
 html.Div([
    html.H2("Select an attribute for the Pie Chart", style={'textAlign': 'center', 'color': colors['text']}),

    # Dropdown with ARIA attribute and accessible role
    html.Div(
        dcc.Dropdown(
            id='df-dropdown',
            options=[
                {'label': 'Blur', 'value': 'blur'},
                {'label': 'Occlusion', 'value': 'occluded'}
            ],
            value='blur', 
            clearable=False,
            style={'width': '50%', 'margin': '0 auto', 'display': 'block'}
        ),
        role="combobox",  # Accessible role for dropdown
        **{'aria-label': 'Select DataFrame for Pie Chart'}  # ARIA attribute
    ),

    # Pie chart visualization
    dcc.Graph(
        id='pie-chart', 
        style={
            'border': '1px solid #ddd', 
            'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 
            'borderRadius': '8px'
        }
    )
], style={'padding': '20px', 'backgroundColor': colors['background'], 'borderRadius': '8px'}),
html.Div([
    html.H2("Faces snips table per video", style={'textAlign': 'center', 'color': colors['text']}),

    snips_table()  # Call the function from Part 1
], style={'padding': '20px', 'backgroundColor': colors['background'], 'borderRadius': '8px'})

]
# Define the Faces Tab
sheet1_tab = create_empty_tab("Faces", sheet1_content)

# App layout
app.layout = html.Div([
    html.Div("Airis-labs annotations overview", style={
        'textAlign': 'center',
        'color': colors['text'],
        'fontSize': '24px',
        'backgroundColor': colors['background'], 
        'borderRadius' : '9px'
    }),
    dcc.Tabs(id='tabs', value='tab-1', children=[
        dcc.Tab(
            label='Faces',
            value='tab-1',
            style=tab_style,
            selected_style=selected_tab_style
        ),
        dcc.Tab(
            label='Objects',
            value='tab-2',
            style=tab_style,
            selected_style=selected_tab_style
        ),
        dcc.Tab(
            label='NLP Transcript data',
            value='tab-3',
            style=tab_style,
            selected_style=selected_tab_style
        ),
        dcc.Tab(
            label='Voice recognition',
            value='tab-4',
            style=tab_style,
            selected_style=selected_tab_style
        ),
        dcc.Tab(
            label='Encord work progress',
            value='tab-5',
            style=tab_style,
            selected_style=selected_tab_style
        ),
        dcc.Tab(
            label='Geo',
            value='tab-6',
            style=tab_style,
            selected_style=selected_tab_style
        ),
    ]),
    html.Div(id='main-content', style={
        'padding': '22px',
        'backgroundColor': colors['background']
    })
])

# Callback to update main content based on selected tab
@app.callback(
    Output('main-content', 'children'),
    [Input('tabs', 'value')]
)
def update_main_content(tab):
    if tab == 'tab-1':
        return add_image_to_tab(sheet1_content)  # Add image to Faces tab
    elif tab == 'tab-2':
        return add_image_to_tab(create_objects_tab())  # Add image to Objects tab
    elif tab == 'tab-3':
        return add_image_to_tab(create_NLP_table())  # Add image to NLP tab
    elif tab == 'tab-4':
        return add_image_to_tab(voice_rec())  # Add image to Heatmap tab
    elif tab == 'tab-5':
        return add_image_to_tab(create_table_tab())  # Add image to DataFrames tab
    elif tab == 'tab-6':
        return add_image_to_tab(tab_layout())  # Add image to DataFrames tab
    else:
        return html.Div("Tab not found.", style={
            'textAlign': 'center',
            'fontSize': '24px',
            'color': 'gray'
        })


from dash import callback_context

@app.callback(
    [Output('objects-treemap', 'figure'),
     Output('scatter-plot', 'figure'),
     Output('number-chart-videos', 'figure')],
    [Input('my-slider', 'value'),
     Input('att_selection', 'value'),
     Input('obj_selection', 'value'),
     Input('reset-button', 'n_clicks')]
)
def update_treemap_and_scatter(selected_range, selected_attributes, selected_objects, n_clicks):
    fixed_y_axis = 'Total_per_video'
    filtered_treemap_df = transposed_df.iloc[:-1, :].reset_index()

    # Filter range for treemap
    if not selected_range or len(selected_range) != 2:
        min_val = filtered_treemap_df['Total'].min()
        max_val = filtered_treemap_df['Total'].max()
    else:
        min_val, max_val = selected_range
        filtered_treemap_df = filtered_treemap_df[
            (filtered_treemap_df['Total'] >= min_val) & 
            (filtered_treemap_df['Total'] <= max_val)
        ]

    # Reset logic
    triggered = callback_context.triggered[0]['prop_id'].split('.')[0]
    if triggered == 'reset-button':
        selected_attributes = None
        selected_objects = None

    # Treemap figure
    treemap_fig = px.treemap(
        filtered_treemap_df,
        path=['index'],
        values='Total',
        title=f"Treemap: Annotations per Object ({min_val} ≤ x ≤ {max_val})",
        labels={'index': 'Object', 'Total': 'Annotations'}
    )
    treemap_fig.update_traces(hovertemplate='<b>%{label}</b><br>Annotations: %{value}<extra></extra>')
    treemap_fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

    df_top_filtered = df_top.drop(index=df.index[0])
    filtered_df = df_top_filtered

    # Filter by attributes and object_name
    if selected_attributes or selected_objects:
        video_mask = pd.Series(True, index=OD_ATT.index)

        if selected_attributes:
            att_mask = OD_ATT[selected_attributes].apply(lambda x: x != "", axis=1).all(axis=1)
            video_mask &= att_mask

        if selected_objects:
            obj_video_map = OD_ATT[OD_ATT['object_name'].isin(selected_objects)]
            video_counts = obj_video_map.groupby("Video Name")['object_name'].nunique()
            matching_video_names = video_counts[video_counts == len(selected_objects)].index
            obj_mask = OD_ATT["Video Name"].isin(matching_video_names)
            video_mask &= obj_mask

        matching_videos = OD_ATT.loc[video_mask, "Video Name"].unique()
        filtered_df = filtered_df[filtered_df["Video Name"].isin(matching_videos)]

    # Scatter plot
    if not filtered_df.empty:
        scatter_fig = px.bar(
            filtered_df,
            x='Video Name',
            y=fixed_y_axis,
            title="Videos Matching Filters",
            text=fixed_y_axis
        )
        scatter_fig.update_traces(
            textposition='outside',
            texttemplate='%{text}',
            marker_color='LightSkyBlue'
        )
    else:
        scatter_fig = px.bar(title="No Videos Match the Selected Filters")

    scatter_fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        yaxis=dict(range=[0, 70])
    )

    # Number chart
    video_count = filtered_df["Video Name"].nunique() if not filtered_df.empty else 0
    number_chart_fig = go.Figure(go.Indicator(
        mode="number",
        value=video_count,
        title={"text": "Videos Matching Filters"}
    ))
    number_chart_fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

    return treemap_fig, scatter_fig, number_chart_fig




# Callback to update the gauge for total annotations
@app.callback(
    Output('gauge-indicator-total', 'figure'),
    [Input('y-axis-dropdown-overall', 'value')]
)
def update_gauge_total(selected_column):
    """Update the gauge indicator with the total overall objects."""
    
    if selected_column in transposed_df_obj_ann.columns:
        total_value = transposed_df_obj_ann[selected_column].sum()
    else:
        total_value = 0  # Default value if column not found

    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=total_value,
        title={'text': f"Total Annotations for {selected_column}"},
        gauge={
            'axis': {'range': [0, max(10, total_value + 5)]},  # Adjust range as needed
            'bar': {'color': "#7FDBFF"},
            'steps': [
                {'range': [0, total_value * 0.5], 'color': "#FF4136"},
                {'range': [total_value * 0.5, total_value], 'color': "#2ECC40"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': total_value
            }
        }
    ))
    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )
    

    return fig

# Callback to update the pie chart based on dropdown selection
@app.callback(
    Output('pie-chart', 'figure'),
    [Input('df-dropdown', 'value')]
)
def update_pie_chart(selected_df):
    """Update the pie chart based on the selected DataFrame."""
    # Choose the DataFrame
    if selected_df == 'blur':
        data = blur_df
        title = "Blur Distribution"
    elif selected_df == 'occluded':
        data = occluded_df
        title = "Occlusion Distribution"
    else:
        data = {}
        title = "No Data Selected"

    # Convert the data into a pie chart
    if data:
        labels = list(data.keys())
        values = list(data.values())
        fig = px.pie(values=values, names=labels, title=title)
        
        fig.update_layout(
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font_color=colors['text']
        )
        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>Frames: %{value}<extra></extra>'
        )
    else:
        # Empty figure if no data is selected
        fig = go.Figure()
        fig.update_layout(
            title=title,
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font_color=colors['text']
        )
    
    return fig



@app.callback(
    Output('OD-pie', 'figure'),
    [Input('df-dropdown_OD', 'value'),
     Input('att_selection', 'value'),
     Input('obj_selection', 'value')]
)
def update_attribute_pie(selected, att_selection, obj_selection):
    df = OD_ATT.copy()

    # Apply filters
    if att_selection:
        att_mask = df[att_selection].apply(lambda x: x != "", axis=1).all(axis=1)
        df = df[att_mask]

    if obj_selection:
        obj_video_map = df[df['object_name'].isin(obj_selection)]
        video_counts = obj_video_map.groupby("Video Name")['object_name'].nunique()
        matching_videos = video_counts[video_counts == len(obj_selection)].index
        df = df[df['Video Name'].isin(matching_videos)]

    # Choose the column
    col_map = {
        'blurry': 'Blurry',
        'occluded': 'Occluded',
        'truncated': 'Truncated'
    }

    column = col_map.get(selected)
    if not column or column not in df.columns:
        return px.pie(title="No Data Selected")

    counts = df[column].value_counts().to_dict()

    fig = px.pie(values=list(counts.values()), names=list(counts.keys()), title=f"{column} Distribution")
    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )
    return fig


   

     
def create_OD_attributes():
  

  table_OD = dash_table.DataTable(
    id="OD-table",
    columns=[{"name": i, "id": i} for i in OD_ATT.columns],  # Set columns from DataFrame
    data=OD_ATT.to_dict('records'),  # Convert DataFrame to list of records
    editable=True,
    filter_action="native",
    sort_action="native",
    sort_mode="multi",
    column_selectable="single",
    row_selectable="multi",
    row_deletable=True,
    page_action="native",
    page_current=0,
    page_size=40,
    style_table={
        'overflowX': 'auto',  # Enable horizontal scrolling
        'maxWidth': '100%'  # Optional: Limit max width of the table
    },
    style_cell={
        'backgroundColor': colors['background'],  # Background color for table cells
        'color': colors['text'],  # Text color
        'textAlign': 'left',  # Text alignment
        'padding': '5px',  # Padding inside cells
        'fontSize': '14px',  # Font size for cell content
        'border': '1px solid #444'  # Optional: Border color and style
    },
    style_header={
        'backgroundColor': '#444',  # Background color for header
        'color': colors['text'],  # Text color for header
        'fontWeight': 'bold',  # Bold text for header
        'border': '1px solid #333'  # Optional: Border color for header
    },
    style_data={
        'backgroundColor': colors['background'],  # Row background color
        'color': colors['text'],  # Text color for rows
        'border': '1px solid #444'  # Optional: Border color for rows
    },
    style_data_conditional=[
        # Example: Highlight selected rows
        {
            'if': {'state': 'selected'},  # Apply styles when a row is selected
            'backgroundColor': '#2ECC40',  # Highlight color
            'color': 'white'  # Text color for selected row
        }
    ]
)
  return table_OD


@app.callback(
    Output('datatable-interactivity-container-od', 'children'),
    [Input('OD-table', 'selected_rows')],
    [Input('OD-table', 'data')]
)
def display_row_explanation(selected_rows, data):
    """Display explanations based on the selected row in the DataTable."""
    if not selected_rows:
        return html.P("Click on a row to see its details.", style={'color': colors['text']})

    # Extract the data for the selected rows
    selected_data = [data[i] for i in selected_rows]
    explanations = []

    for row in selected_data:
        explanation = [html.P("This row contains the following details:", style={'color': colors['text']})]
        
        # Add non-empty key-value pairs with line breaks and styled text
        for key, value in row.items():
            if value and str(value).strip():  # Check if value is not empty
                value = True
                explanation.append(
                    html.Span(f"{key}: {value}", style={'color': colors['text']})
                )
                explanation.append(html.Br())  # Line break between entries
        
        explanations.append(html.Div(explanation))

    return html.Div(explanations)




@app.callback(
    Output('OD-color-pie', 'figure'),
    [Input('att_selection', 'value'),
     Input('obj_selection', 'value')]
)
def update_color_pie(att_selection, obj_selection):
    color_name_to_hex = {
        "Black": "#323232",
        "Blue": "#0000FF",
        "White": "#FFFFFF",
        "Red": "#FF0000",
        "Gray": "#808080",
        "Yellow": "#FFFF00",
        "Green": "#008000",
        "Brown": "#A52A2A",
        "Purple": "#800080",
        "Pink": "#FFC0CB"
    }

    df = OD_ATT.copy()

    # Filter by attributes (AND across selected attributes)
    if att_selection:
        att_mask = df[att_selection].apply(lambda x: x != "", axis=1).all(axis=1)
        df = df[att_mask]

    # Filter by object_name (AND logic)
    if obj_selection:
        obj_video_map = df[df['object_name'].isin(obj_selection)]
        video_counts = obj_video_map.groupby("Video Name")['object_name'].nunique()
        matching_videos = video_counts[video_counts == len(obj_selection)].index
        df = df[df['Video Name'].isin(matching_videos)]

    # Count non-empty occurrences for known color columns
    color_counts = {}
    for color in color_name_to_hex:
        if color in df.columns:
            count = df[color].astype(bool).sum()
            if count > 0:
                color_counts[color] = count

    if not color_counts:
        return px.pie(title="No Valid Colors Found")

    fig = px.pie(
        values=list(color_counts.values()),
        names=list(color_counts.keys()),
        title="Color Distribution",
        color=list(color_counts.keys()),
        color_discrete_map=color_name_to_hex,
        hole=0.4
    )
    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

    return fig





def bar_attributes():

    fig = px.bar(
                    att_sum,
                    x="Attribute",
                    y="Count",
                    title="Overall instances of attributes",
                    text = "Count"
                )

    # Update layout for colors and styling
    fig.update_layout(
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font_color=colors['text']
        )

    # Update hover template for better interactivity
    fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Annotations: %{value}<extra></extra>'
    )

    return fig


def language_bar(df):
    """Creates a bar chart showing language counts from a DataFrame."""
    
    # Ensure column exists
    if "Language" not in df.columns:
        print("❌ Error: 'Language' column is missing from DataFrame")
        return px.bar(title="No Language Data Available")  # Return a blank figure

    # Normalize column names (strip spaces)
    df.columns = df.columns.str.strip()

    # Clean and capitalize Language values
    df["Language"] = df["Language"].astype(str).str.strip().str.capitalize()

    # Count occurrences
    lans = df["Language"].value_counts()
    maxxx = lans.max()
    lim = maxxx + 50

    # Create the bar chart
    fig = px.bar(
        x=lans.index,  # Language names
        y=lans.values,  # Count
        title="Language Count",
        labels={"x": "Language", "y": "Count"},
        text=lans.values  # Show count as text on bars
    )

    # Improve styling
    fig.update_traces(
        textposition="outside",
        marker=dict(color="lightblue")
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
        yaxis = dict(range = [0 , lim]),
        title_x=0.5  # Center the title
    )

    return fig  # ✅ Return only the figure!
  

def Male_female_voice() : 
    
    df_voice["Gender"] = df_voice["Gender"].astype(str).str.strip().str.capitalize()

    male_count = (df_voice["Gender"] == "Male").sum()
    female_count = (df_voice["Gender"] == "Female").sum()

    fig = px.pie(
        values=[male_count, female_count], 
        names=["Male", "Female"], 
        title="Gender Distribution"
    )

    fig.update_traces(textinfo='percent', marker=dict(colors=["#B6E880", "#FF97FF"]))
    return fig

    
def Face_show() : 
    

    Not_show = (df_voice["Face Showing"] == "No").sum()
    Partly = (df_voice["Face Showing"] == "Partly").sum()
    Showing = (df_voice["Face Showing"] == "Most-All video").sum()

    Face = {"No": Not_show, "Partly": Partly, "Showing_mostly" : Showing}

    fig = px.pie (values=list(Face.values()) ,names=list(Face.keys()) ,title = "Face show distibution")
    fig.update_traces(textinfo='percent', marker=dict(colors=["#B6E880", "#FF97FF"]))
    return fig

    
def Dominant():
    df_voice["Super Dominant"] = df_voice["Super Dominant"].astype(str).str.strip().str.capitalize()

    YES = (df_voice["Super Dominant"] == "Yes").sum()
    NO = (df_voice["Super Dominant"] == "No").sum()

    fig = px.pie(
        values=[YES, NO], 
        names=["Super Dominant", "Not Dominant"], 
        title="Dominant Analysis"
    )

    fig.update_traces(textinfo='percent', marker=dict(colors=["#B6E880", "#FF97FF"]))
    return fig

dcc.Dropdown(
    id='dataset-selector',
    options=[
        {'label': 'OD Dataset', 'value': 'od'},
        {'label': 'POI Dataset', 'value': 'poi'}
    ],
    value='od',  # default selection
    style={'width': '300px', 'margin': '0 auto'}
),


@app.callback(
    Output('bar-hours-tasks', 'figure'),
    Input('dataset-selector', 'value')
)
def Total_ann_hours_per_user(selected_dataset):
    df_en = df_work_od if selected_dataset == 'od' else df_work_poi
    df_en = df_en.iloc[:-1]  # Exclude last row

    df_en = df_en.sort_values(by='Total annotation time hours', ascending=False)
    max_val = df_en["Total annotation time hours"].max()
    bar_limm = max_val + 100

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=df_en["User"],
        y=df_en["Total annotation time hours"],
        name='Annotation Hours',
        text=df_en["Total annotation time hours"]
    ))

    fig.add_trace(go.Bar(
        x=df_en["User"],
        y=df_en["Submitted tasks"],
        name='Submitted Tasks',
        text=df_en["Submitted tasks"]
    ))

    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        yaxis=dict(range=[0, bar_limm]),
        barmode='group',
        title='Annotation Hours vs Submitted Tasks per User'
    )

    fig.update_traces(
        texttemplate='%{text:.2f}',
        textposition='outside',
        hovertemplate='<b>User: %{x}</b><br>Value: %{y}<extra></extra>'
    )

    return fig

@app.callback(
    Output('avg-work-time-bar', 'figure'),
    Input('dataset-selector', 'value')
)
def update_avg_work_time(source):
    df = df_work_od if source == 'od' else df_work_poi
    df = df.iloc[:-1].copy()
    df['AVG annotation time per video (hours)'] = pd.to_numeric(df['AVG annotation time per video (hours)'], errors='coerce')

    max_val = df['AVG annotation time per video (hours)'].max()
    bins = [0, 0.2 * max_val, 0.4 * max_val, 0.6 * max_val, 0.8 * max_val, max_val]
    labels = [f"{round(bins[i], 2)}–{round(bins[i+1], 2)}" for i in range(len(bins) - 1)]

    df['Time Bin'] = pd.cut(df['AVG annotation time per video (hours)'], bins=bins, labels=labels, right=False)
    bar_data = df['Time Bin'].value_counts().sort_index().reset_index()
    bar_data.columns = ['Time Bin', 'Count']

    fig = px.bar(
        bar_data,
        x='Time Bin',
        y='Count',
        color='Time Bin',
        title='Average Work Time Per Video Histogram',
        text='Count'
    )

    fig.update_traces(
        textposition='outside',
        marker_line_width=1.5,
        hovertemplate="Count: %{y}",
        textfont=dict(size=24)
    )

    fig.update_layout(
        xaxis_title="AVG annotation time per video (hours)",
        yaxis_title="Count",
        showlegend=False,
        font=dict(size=20, color='white'),
        yaxis=dict(range=[0, 1.25 * bar_data['Count'].max()])
    )

    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

    return fig



@app.callback(
    Output('rejection-rate-pie', 'figure'),
    Input('dataset-selector', 'value')
)
def update_rejection_pie(source):
    # Select appropriate dataset
    df = df_work_od if source == 'od' else df_work_poi
    df = df.iloc[:-1].copy()

    # Convert 'Submitted tasks' to numeric
    df['Submitted tasks'] = pd.to_numeric(df['Submitted tasks'], errors='coerce')

    # Clean and convert 'Tasks rejection rate' to float
    df['Tasks rejection rate'] = (
        df['Tasks rejection rate'].astype(str)
        .str.replace('%', '', regex=False)
        .astype(float)
    )

    # Filter rows with valid data
    df = df[(df['Tasks rejection rate'] >= 0) & (df['Submitted tasks'] > 0)]

    # Total task count for annotation
    total_sum = int(df['Submitted tasks'].sum())

    # Define bins and labels
    bins = [0, 10, 25, 100]
    labels = ['Good (0%-10%)', 'Mediocre (10%-25%)', 'Bad (>25%)']

    df['Rejection Category'] = pd.cut(
        df['Tasks rejection rate'],
        bins=bins,
        labels=labels,
        right=True,
        include_lowest=True
    )

    # Count each category
    pie_rejection = df['Rejection Category'].value_counts().reset_index()
    pie_rejection.columns = ['Tasks rejection rate', 'Count']

    # Custom color map
    color_map = {
        'Good (0%-10%)': 'green',
        'Mediocre (10%-25%)': 'orange',
        'Bad (>25%)': 'red'
    }

    # Build pie chart
    fig = px.pie(
        pie_rejection,
        names='Tasks rejection rate',
        values='Count',
        color='Tasks rejection rate',
        color_discrete_map=color_map,
        title='Rejection Rate'
    )

    fig.update_traces(
        marker=dict(line=dict(color='black', width=2)),
        textinfo='label+percent',
        textfont=dict(color='black', size=12)
    )

    # Styling
    fig.update_layout(
        hovermode="x unified",
        margin=dict(t=40, b=20, l=0, r=0),
        font=dict(size=12, color='black'),
        title_font=dict(color='black', size=24),
        hoverlabel=dict(font=dict(size=24, color='black'))
    )
    fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

    # Add total task count as annotation
    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=1.0,
        y=1.00,
        text=f"Out of {total_sum:,} Tasks",
        showarrow=False,
        font=dict(size=16, color='white'),
        borderwidth=2,
        borderpad=4
    )

    return fig

@app.callback(
    Output('rejection-rate-bar', 'figure'),
    Input('dataset-selector', 'value'))

def generate_rejection_rate(source):
    df = df_work_od if source == 'od' else df_work_poi

    # Clean before slicing for summary metrics
    df['AVG annotation time per video (hours)'] = pd.to_numeric(df['AVG annotation time per video (hours)'], errors='coerce')
    df['Total annotation time hours'] = pd.to_numeric(df['Total annotation time hours'], errors='coerce')
    df['Submitted tasks'] = pd.to_numeric(df['Submitted tasks'], errors='coerce')

    avg_total_wt = df['AVG annotation time per video (hours)'].iloc[-1]
    total_hr = df['Total annotation time hours'].iloc[-1]

    df = df.iloc[:-1].copy()  # Exclude the summary row

    df['User'] = df['User'].str.split('@').str[0]
    df['Tasks rejection rate'] = df['Tasks rejection rate'].astype(str).str.replace('%', '', regex=False)
    df['Tasks rejection rate'] = pd.to_numeric(df['Tasks rejection rate'], errors='coerce')
    df = df[df['Submitted tasks'] != 0].copy()

    df = df.sort_values("Tasks rejection rate", ascending=True)

    fig = px.bar(
        df,
        x='Tasks rejection rate',
        y='User',
        orientation='h',
        color='Tasks rejection rate',
        title='Rejection Rate by User (%)',
        text='Tasks rejection rate'
    )

    fig.update_traces(
        marker_line_width=1.5,
        textposition='outside',
        textfont=dict(size=12),
        hovertemplate="User: %{y}<br>Rejection Rate: %{x:.2f}%"
    )

    fig.update_coloraxes(showscale=False)

    fig.update_layout(
        height=1000,
        width=1000,
        font=dict(size=12, color='black'),
        title_font=dict(color='black'),
        xaxis=dict(
            color='black',
            gridcolor='gray',
            showgrid=False,
            zeroline=False,
            title_font=dict(color='black'),
            tickfont=dict(color='black'),
            range=[0, 1.25 * df['Tasks rejection rate'].max()]
        ),
        yaxis=dict(
            color='yellow',
            gridcolor='gray',
            showgrid=False,
            zeroline=False,
            title_font=dict(color='black'),
            tickfont=dict(color='black')
        ),
        hoverlabel=dict(font=dict(size=24, color='black')),
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background']
    )

    fig.add_annotation(
        xref="paper",
        yref="paper",
        x=1.5,
        y=0.97,
        text=f"Overall Average Work Time: {avg_total_wt:.2f} hrs<br>Total Annotation Time: {total_hr:.2f} hrs",
        showarrow=False,
        font=dict(size=16, color='white'),
        align="right",
        bgcolor='black',
        bordercolor='white',
        borderwidth=2,
        borderpad=4
    )

    return fig



@app.callback(
    Output('generate_avg_time_per_user', 'figure'),
    Input('dataset-selector', 'value'))

def generate_avg_time_per_user(source):
    df = df_work_od if source == 'od' else df_work_poi
    df0 = df[df['Submitted tasks'] > 0].copy()
    df1 = df0.iloc[:-1].copy()
    df1['User'] = df1['User'].str.split('@').str[0]
    # Convert to numeric
    df1['Total annotation time hours'] = pd.to_numeric(
        df1['Total annotation time hours'], errors='coerce'
    )
    df2 = df1.sort_values("Total annotation time hours", ascending=True)
    fig = px.bar(
        df2,
        x='Total annotation time hours',
        y='User',
        orientation='h',
        labels={'Total annotation time hours': 'Total annotation time (hours)'},
        title='Annotation Time by User',
        category_orders={'User': df2['User'].tolist()[::-1]}  # top user on top
    )
    fig.update_traces(
        marker_line_width=1.5,
        textposition='outside',
        textfont=dict(size=16),
        hovertemplate="User: %{y}<br>Annotation Time: %{x}"
    )
    fig.update_layout(
    width=1000,
    height=1000,
    xaxis_title='Total annotation time hours',
    yaxis_title="User",
    showlegend=False,
    hovermode="y unified",
    font=dict(size=20, color='black'),
    title_font=dict(color='white'),
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    
    xaxis=dict(
        color='black',
        gridcolor='gray',
        showgrid=False,
        zeroline=False,
        title_font=dict(color='black'),
        tickfont=dict(color='black'),
        range=[0, 1.25 * df2['Total annotation time hours'].max()]
    ),

    yaxis=dict(
        color='yellow',
        gridcolor='gray',
        showgrid=False,
        zeroline=False,
        title_font=dict(color='black'),
        tickfont=dict(color='black')
    ),

    hoverlabel=dict(
        font=dict(size=16, color='black')
    )
)

    return fig


    

if __name__ == '__main__':
    app.run_server(host='100.118.47.56', port=8051, debug=True)
