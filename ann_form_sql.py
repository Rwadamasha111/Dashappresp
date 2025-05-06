import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
from dash import html, Input, Output
from dash import dcc
from dash import dash_table
from dash.dash_table import DataTable
import dash.exceptions as dash_exceptions
import random

import os
import re
import math
import ast
import numpy as np
import pandas as pd
import json

import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
from dash import dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import yt_dlp
from TikTokApi import TikTokApi
import requests
from bs4 import BeautifulSoup
import time
import dash_player
from dash import callback_context
from shapely.geometry import Point, Polygon
import datetime    
from datetime import timedelta
from datetime import date

# Google API imports
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from oauth2client.client import GoogleCredentials
from google.oauth2 import service_account



#ydl_opts = {
#    'quiet': False,
#    'outtmpl': 'C:/videos_download/%(title)s.%(ext)s',
#    'ffmpeg_location': r"C:\Users\roy\OneDrive\Desktop\ASR JSONS\Geo_Analysis\ffmpeg-2025-04-14-git-3b2a9410ef-full_build\bin"
#}
# Then, download (with proper options)
#with yt_dlp.YoutubeDL(ydl_opts) as ydl:
 #   ydl.download([valid_url])             
# Get current time
#now = time.time()
# Apply timestamp to the merged output file
# If you know the title in advance, do this directly. Otherwise use glob
#import glob
#for file in glob.glob("C:/videos_download/*.mp4"):
#    filename_only = os.path.splitext(os.path.basename(file))[0]  # strip directory and .mp4
#    if filename_only == video_name:
#        os.utime(file, (now, now))  # update access and modified times
#    else:
#        continue
SERVICE_ACCOUNT_FILE = r"C:\Users\rwad\Downloads\arabic-transcription-435113-c8120df00a35 (1).json"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('sheets', 'v4', credentials=credentials)
# Define scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly', 
          'https://www.googleapis.com/auth/drive']

# Authenticate
creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build Sheets API service
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()


# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate using Service Account
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Drive API service
drive_service = build('drive', 'v3', credentials=creds)
import psycopg2
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Annotation Form"
# --- DB CONNECTION FUNCTION ---
def get_db_connection():
    return psycopg2.connect(
        host="127.0.0.1",
        port="5432",
        user="postgres",
        password="postgres",
        dbname="postgres"
    )


button_style1 = {
    "borderRadius": "24px",
    "width": "250px",
    "padding": "15px 25px",
    "position": "absolute",
    "bottom": "30px",
    "right": "30px",
    "background": "linear-gradient(to right, #4facfe, #00f2fe)",
    "border": "2px solid black",
    "fontWeight": "600",
    "fontSize": "40px",
    "font-weight": 'bold',
    "color": "white",
    "textAlign": "center",
    "boxShadow": "0 8px 16px rgba(0, 0, 0, 0.2)",
    "transition": "all 0.3s ease-in-out"
}

button_style2 = {
    "borderRadius": "24px",
    "width": "250px",
    "padding": "15px 25px",
    "background": "linear-gradient(to right, #006400, #98FB98)",
    "border": "2px solid black",
    "fontWeight": "bold",
    "fontSize": "24px",
    "color": "white",
    "textAlign": "center",
    "boxShadow": "0 8px 16px rgba(0, 0, 0, 0.2)",
    "transition": "all 0.3s ease-in-out"
}

button_style3 = {
    "borderRadius": "24px",
    "width": "250px",
    "padding": "15px 25px",
    "background": "linear-gradient(to right, #B22222, #F08080)",
    "border": "2px solid black",
    "fontWeight": "bold",
    "fontSize": "24px",
    "color": "white",
    "textAlign": "center",
    "boxShadow": "0 8px 16px rgba(0, 0, 0, 0.2)",
    "transition": "all 0.3s ease-in-out",

}

button_style4 = {
    "padding": "5px 10px",
    "border": "2px solid black",
    "fontWeight": "bold",
    "fontSize": "24px",
    "textAlign": "center",
    "boxShadow": "0 8px 16px rgba(0, 0, 0, 0.2)",
    "position": "relative",
    "top": "350px"
}

rec_num = {
    "fontWeight": "bold",
    "fontSize": "18px",
    "textAlign": "center",
    "position": "relative",
    "top": "285px"       
}

save_link_btn = {
    "padding": "5px 10px",
    "border": "2px solid black",
    "fontWeight": "bold",
    "background-color":'orange',
    "fontSize": "16px",
    "textAlign": "center",
    "boxShadow": "0 8px 16px rgba(0, 0, 0, 0.2)",
    "position": "relative",
    "top": "385px",
    "borderRadius": "50px",
}

place_map_btn = {
    "padding": "5px 10px",
    "border": "2px solid black",
    "fontWeight": "bold",
    "background-color":'blue',
    "fontSize": "16px",
    "textAlign": "center",
    "boxShadow": "0 8px 16px rgba(0, 0, 0, 0.2)",
    "position": "relative",
    "top": "535px",
    "borderRadius": "50px",
}

check_btn_ed = {
    "padding": "5px 10px",
    "border": "2px solid black",
    "fontWeight": "bold",
    "background-color":'blue',
    "fontSize": "16px",
    "textAlign": "center",
    "boxShadow": "0 8px 16px rgba(0, 0, 0, 0.2)",
    "position": "relative",
    "top": "600px",
    "left": "-50px",
    "borderRadius": "50px",
}


check_div ={
   "top": "985px", 
}
background_style = {
    "background": "linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)",
    "minHeight": "auto",
    "padding": "20px"
}

container_style = {
    "backgroundColor": "white",
    "borderRadius": "30px",
    "padding": "30px",
    "boxShadow": "0 10px 40px rgba(0, 0, 0, 0.1)",
    "width": "100%",
    "maxWidth": "2400px",
    "margin": "auto",
    "position": "relative"
}

container_style_2 = {
    "backgroundColor": "white",
    "borderRadius": "30px",
    "padding": "30px",
    "boxShadow": "0 10px 40px rgba(0, 0, 0, 0.1)",
    "width": "100%",
    "maxWidth": "2400px",
    "margin": "auto",
    "position": "relative"
}

heading_style = {
    "textAlign": "center",
    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen",
    "color": "#333",
    "fontSize": "48px",
    "marginBottom": "30px"
}

heading_style2 = {
    "textAlign": "center",
    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen",
    "color": "#333",
    "fontSize": "28px",
    "marginBottom": "30px"
}

tab_style = {
    "backgroundColor": "#E0FFFF",
    "borderRadius": "12px 12px 0 0",
    "padding": "10px 20px",
    "fontSize": "32px",
    "color": "#555",
    "border": "none",
    "fontWeight": "500"
}

selected_tab_style = {
    "backgroundColor": "#00f2fe",
    "borderBottom": "2px solid #00f2fe",
    "fontWeight": "bold",
    "color": "white",
    "fontSize": "32px"
}

modal_style = {
    "color": "#333",
    "fontSize": "20px",
    "padding": "10px",
    "fontWeight": "500"
}

update_modal_style = {"textAlign": "center"}



def append_row_to_sql(row_data, table_name):
    """
    Inserts a row into the SQL table (city_table).
    row_data: list of values in exact order matching columns.
    """
    conn = get_db_connection()
    cur = conn.cursor()
    cut_table_columns = [
    'Index',
    'Cut_ID',
    'Country',
    'City',
    'Links',
    'Title',
    'Annotated File Name',
    'Cut_Start',
    'Cut_Fnish',
    'Cut_Duration',
    'Cut_Size',
    'GCP_Bucket_URL',
    'Ignored',
    'Validated_By',
    'Upload_Time',
    'Video_Size_OG',
    'Video Duration_OG'
]
    if table_name == 'geo' : 

     sql = """
        INSERT INTO geo (
    "Index", "Cut_ID", "record_id", "Country", "City", "Links", "Title", "Coordinates",
    "Analyst", "Source", "Original Duration", "Start Time", "Finish Time",
    "Duration", "Time of the day", "Terrain", "Weather", "Video quality",
    "Camera tilt", "Distance from building", "Occluded", "Distortions",
    "Logos and text", "Comments", "TimeStamp"
)
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s,%s,%s
        )
    
    """
    elif table_name == "geo_cut":
        sql =f"""
INSERT INTO geo_cut ({', '.join([f'"{col}"' for col in cut_table_columns])})
VALUES ({', '.join(['%s'] * len(cut_table_columns))})
"""
    try:
        cur.execute(sql, row_data)
        conn.commit()
        print("✅ Row inserted into database.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error inserting row: {e}")
    finally:
        cur.close()
        conn.close()

def update_row_in_sql(cut_id, values):
    """
    Updates a row in geo table identified by Cut_ID.
    values: list of values in the exact order of columns (EXCEPT Cut_ID and Index).
    """
    conn = get_db_connection()
    cur = conn.cursor()

    update_columns = [
        'record_id', 'Country', 'City', 'Links', 'Title', 'Coordinates',
        'Analyst', 'Source', 'Original Duration', 'Start Time', 'Finish Time',
        'Duration', 'Time of the day', 'Terrain', 'Weather', 'Video quality',
        'Camera tilt', 'Distance from building', 'Occluded', 'Distortions',
        'Logos and text', 'Comments', 'TimeStamp'
    ]

    # Dynamically build the SET part
    set_clause = ", ".join([f'"{col}" = %s' for col in update_columns])

    sql = f"""
    UPDATE geo
    SET {set_clause}
    WHERE "Cut_ID" = %s
    """

    try:
        # values: list of 23 items (excluding Index, Cut_ID)
        cur.execute(sql, values + [cut_id])
        conn.commit()
        print(f"✅ Row with Cut_ID {cut_id} updated in database.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error updating row: {e}")
    finally:
        cur.close()
        conn.close()



def remove_record_sql(cut_id):
    """
    Deletes a row from the SQL table by Cut_ID.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    sql = "DELETE FROM geo WHERE cut_id = %s"
    try:
        cur.execute(sql, (cut_id,))
        conn.commit()
        print(f"✅ Row with Cut_ID {cut_id} deleted from database.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error deleting row: {e}")
    finally:
        cur.close()
        conn.close()
  
   
     
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

def parse_input_time(time_str):
    # Assume format is M:S
    parts = [p.strip() for p in time_str.split(':')]
    if any(p == '' for p in parts):
        raise ValueError(f"Invalid time string: {time_str}")
    if len(parts) != 2:
        raise ValueError("Expected format MM:SS")
    return timedelta(minutes=int(parts[0]), seconds=int(parts[1]))

def parse_duration(duration_str):
    # Assume format is H:M:S
    hours, minutes, seconds = map(int, duration_str.split(':'))
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)


def is_valid_social_url(url: str) -> bool:
    patterns = {
        "youtube": re.compile(
            r'^(https?://)?(www\.)?'
            r'(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)'
            r'[\w-]{11}($|&)', re.IGNORECASE
        ),
        "instagram": re.compile(
            r'^(https?://)?(www\.)?instagram\.com/(p|reel|tv)/[A-Za-z0-9_-]+/?$', re.IGNORECASE
        ),
        "telegram": re.compile(
            r'^(https?://)?(t\.me|telegram\.me)/[A-Za-z0-9_]{5,32}/?$', re.IGNORECASE
        ),
        "facebook": re.compile(
            r'^(https?://)?(www\.)?facebook\.com/(?:[^/?#&]+/)*[^/?#&]+/?$', re.IGNORECASE
        ),
        "tiktok": re.compile(
            r'^(https?://)?(www\.)?tiktok\.com/@[A-Za-z0-9_.]+/video/\d+/?$', re.IGNORECASE
        )
    }

    return any(pattern.match(url) for pattern in patterns.values())

def general_validations (analyst,city_name,distancebuild,occlusion,terrain,
                         logo,distortions, tod,weather,vq,tilt):
    if not analyst:
        raise ValueError("Please select an Analyst!")
    if not city_name:
        raise ValueError("Please select a City!")            
    if not distancebuild:
        raise ValueError("Please Insert Distance from building!")
    if not occlusion:
        raise ValueError("Please Insert Occlusion!")
    if not terrain:
        raise ValueError("Please Insert Terrain!")  
    if not logo:
        raise ValueError("Please Insert Logos & Text!")    
    if not distortions:
        raise ValueError("Please Insert Distortions!") 
    if not tod:
        raise ValueError("Please Insert Time of Day!")  
    if not weather:
        raise ValueError("Please Insert Weather!")  
    if not vq:
        raise ValueError("Please Insert Video Quality!")                     
    if not tilt:
        raise ValueError("Please Insert Camera Tilt!")  
    
def is_valid_url (url):
    if not url:
        raise ValueError("Please insert a url!")
    else:
        valid_url = is_valid_social_url(url)
        if not valid_url:
            raise ValueError("Please insert a valid social url!")
        return url  

def valid_coords(coords):
    if not coords:
        raise ValueError("Please insert coordinates!")
    if not is_valid_coord(coords):
        raise ValueError("Invalid Coordinates!")
    cleaned_coordinates =  clean_coordinate(coords)
    return cleaned_coordinates

def valid_dur(duration):
    if not duration:
        raise ValueError("Please insert duration!")
    if duration == "Invalid duration!":
        raise ValueError("Invalid Duration!")
    return duration
               
def parse_time_string(time_str):
    parts = list(map(int, time_str.strip().split(':')))
    if len(parts) == 3:
        hh, mm, ss = parts
    elif len(parts) == 2:
        hh = 0
        mm, ss = parts
    elif len(parts) == 1:
        hh = mm = 0
        ss = parts[0]
    else:
        raise ValueError(f"Invalid time format: {time_str}")
    return hh, mm, ss

# Check inside polygon
def is_inside_any(lat, lon, polygons):
    pt = Point(lat, lon)
    if polygons and Polygon(polygons).contains(pt):
            return True
    return False
    


def city_load_data(query):
    """
    Runs a SQL query and returns results as a pandas DataFrame.
    """
    conn = get_db_connection()
    try:
        df = pd.read_sql_query(query, conn)
    except Exception as e:
        print(f"❌ Error loading data from SQL: {e}")
        df = pd.DataFrame()
    finally:
        conn.close()
    return df

global df_city_edit
df_city_edit = city_load_data("SELECT * FROM geo")

global cities
cities = city_load_data("SELECT * FROM geo")
cities_list = cities['City'].unique()
country_list = cities['Country'].unique()



source_list = df_city_edit['Source'].unique()
time_list = df_city_edit['Time of the day'].unique()
terrain_list = df_city_edit['Terrain'].unique()
weather_list = df_city_edit['Weather'].unique()
video_vq = df_city_edit['Video quality'].unique()
camera_tilt = df_city_edit['Camera tilt'].unique()
distance = df_city_edit['Distance from building'].unique()
occlusion = df_city_edit['Occluded'].unique()
distortions = df_city_edit['Distortions'].unique()
logos = df_city_edit['Logos and text'].unique()
analysts =df_city_edit['Analyst'].unique()


def parse_time(t):
    parts = list(map(int, t.split(':')))
    if len(parts) == 3:            # HH:MM:SS
        h, m, s = parts
    elif len(parts) == 2:          # MM:SS
        h, m, s = 0, *parts
    else:
        raise ValueError('Bad time format')
    return datetime.timedelta(hours=h, minutes=m, seconds=s)

           
import random

import random

def generate_unique_random_id(city, df, url):
    df_filtered = df[df['City'] == city].copy()

    # Create a set of existing record_id prefixes for efficient lookup
    existing_prefixes = set(rec_id.split('_', 2)[0] + '_' + rec_id.split('_', 2)[1] + '_' for rec_id in df['Cut_ID'].values)

    def create_random_initials():
        country_name = cities[cities['City Name'] == city]['Country'].values[0].lower()
        city_name = city.lower()

        # Ensure the names are long enough for sampling
        if len(country_name) < 2 or len(city_name) < 3:
            raise ValueError("Country or city name too short for random sampling.")

        init_1 = ''.join(random.sample(country_name, 2))
        init_2 = ''.join(random.sample(city_name, 3))
        return f"{init_1}_{init_2}_"

    if df_filtered.empty:
        # Default deterministic initials
        country_name = cities[cities['City Name'] == city]['Country'].values[0]
        init_1 = f"{country_name[:2].lower()}_"
        init_2 = f"{city[:3].lower()}_"
        initials = init_1 + init_2

        # If deterministic initials are already used, generate random ones
        if initials in existing_prefixes:
            max_tries = 1000
            for _ in range(max_tries):
                initials = create_random_initials()
                if initials not in existing_prefixes:
                    break
            else:
                raise RuntimeError("Failed to find unique initials after many attempts.")

        # Generate unique numeric part and return
        xyz = f"{random.randint(9, 99)}{random.randint(9, 99)}{random.randint(99, 999)}"
        joined = initials + xyz
        new_rec_id = f"{joined}_cut1_v1"
        return new_rec_id

    else:
        df_filt2 = df[df['Links'] == url].copy()
        if not df_filt2.empty:
            df_filt2['base'] = df_filt2['Cut_ID'].str.extract(r'^(.*)_v\d+$')[0]
            df_filt2['version'] = df_filt2['Cut_ID'].str.extract(r'_v(\d+)$')[0].astype(int)
            
            latest_versions = df_filt2.sort_values('version').groupby('base', as_index=False).last()

            url_times = latest_versions['base'].nunique()  # <-- Count different cuts (bases)

            extra_cut = url_times + 1
            new_cut_id = f"cut{extra_cut}"

            id_video = df_filt2['record_id'].values[0]  # Assuming record_id is same for all versions
            new_rec_id = f"{id_video}_{new_cut_id}_v1"

        else:
            # Generate from last record_id for existing city
            rec_id = df_filtered['Cut_ID'].iloc[-1]
            rec_id_start = '_'.join(rec_id.split('_')[:2]) + '_'

            while True:
                xyz = f"{random.randint(9, 99)}{random.randint(9, 99)}{random.randint(99, 999)}"
                new_rec = rec_id_start + xyz
                if new_rec not in df_filtered['record_id'].values:
                    new_rec_id = f"{new_rec}_cut1_v1"
                    return new_rec_id
        return new_rec_id

cleaned_source = [v for v in source_list if v not in ("", None)]  
cleaned_distance = [v for v in distance if v not in ("","Street level", None)]   
cleaned_occlusion = [v for v in occlusion if v not in ("", None)] 
cleaned_logos = [v for v in logos if v not in ("","slight ", "Prominent ", None)] 
cleaned_distortions = [v for v in distortions if v not in ("","Motion DIstortions","No", None)] 
cleaned_vq = [v for v in video_vq if v not in ("", None)] 
cleaned_tilt = [v for v in camera_tilt if v not in ("", None)] 


def insert_tab_layout():
    return html.Div(
        style=background_style,
        children=[
            dbc.Container(
                style=container_style,
                children=[
                dcc.Store(id='default-values', data={
                    'link_url': "",
                    "coordinates_input": "",
                    'sources': "Select a source",
                    'input-hours': 0,
                    'input-minutes': 0,
                    'input-seconds': 0,
                    'input-hours_end': 0,
                    'input-minutes_end': 0,
                    'input-seconds_end': 0,
                    'tod': 'Select time of day',
                    'weather': "Select weather ",
                    'vq': "Select video quality",
                    'tilt': 'Select camera tilt ',
                    'distance': 'Select a distance ',
                    'occlusion_list': 'Select an occlusion',
                    'terrain': "Select a terrain",
                    'logos_list': 'Select Logos & Text',
                    'distortions_list': 'Select a Distortion ',
                    'analysts': 'Select Analyst',
                    'comments':""
                }),
                dcc.Store('links_table_store',data=None),


                    html.H1("Geo Annotation Form", style=heading_style),
                    html.Hr(),
                    dbc.Row([
                        # First Column
                        dbc.Col([
                            html.H4("Link & Coordinates"),
                            dbc.Label("Choose a city:"),
                            dcc.Dropdown(
                                id='cities',
                                options=[{'label': k, 'value': k} for k in cities_list],
                                value="Rome",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Country:"),
                            dcc.Dropdown(
                                id='country',
                                options=[{'label': k, 'value': k} for k in country_list],
                                value="Italy",
                                placeholder='country selection',
                                className="form-control",
                                disabled=True,
                            ),
                            html.Br(),
                            dbc.Label("Pick a source:"),
                            dcc.Dropdown(
                                id='sources',
                                options=[{'label': d, 'value': d} for d in cleaned_source],
                                value="",
                                placeholder = "Select a source",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Video Link:"),
                            dcc.Input(id='link_url', type='text', value="", className="form-control"),
                            html.Div(id="link_url_error", style={"color": "red"}),
                            html.Br(),
                            dbc.Label("Video Title:"),
                            dcc.Input(id='link_title', type='text',disabled=True, value="", className="form-control"),  
                            html.Br(),                     
                            dbc.Label("Coordinates:"),
                            dcc.Input(id='coordinates_input', type='text', value="", className="form-control"),
                            html.Div(id="coords_error", style={"color": "red"}),
                            html.Br(),
                            html.Br(),
                            html.Br(),
                            html.H4("Timing"),
                            dbc.Label("Start Time:"),
                            html.Br(),
                            html.Div([
                                html.Div([
                                    html.Label("Hours"),
                                    dcc.Input(id='input-hours', type='number', min=0, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label("Minutes"),
                                    dcc.Input(id='input-minutes', type='number', min=0, max=59, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label("Seconds"),
                                    dcc.Input(id='input-seconds', type='number', min=0, max=59, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block'}),
                            ]),
                            html.Br(),
                            dbc.Label("End Time:"),
                            html.Br(),
                            html.Div([
                                html.Div([
                                    html.Label("Hours"),
                                    dcc.Input(id='input-hours_end', type='number', min=0, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label("Minutes"),
                                    dcc.Input(id='input-minutes_end', type='number', min=0, max=59, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label("Seconds"),
                                    dcc.Input(id='input-seconds_end', type='number', min=0, max=59, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block'}),
                            ]),
                            html.Br(),
                        html.Div([
                            html.Label("Cut Duration:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                            dcc.Input(id='output-duration', disabled=True, style={'width': '100px', 'fontWeight': 'bold'}),
                            dcc.Checklist(
                                options=[{'label': '  Full', 'value': 'on'}],
                                value=[], 
                                id='checkbox',
                                style={'marginLeft': '20px', 'marginTop': '-10px'}) 
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),

                        html.Div([
                            html.Label("Full Video Duration:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                            dcc.Input(id='og_duration', disabled=False, style={'width': '100px', 'fontWeight': 'bold'}),
                            
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
                            html.Div(id="dur_error", style={"color": "red"}),
                        html.Div([
                            html.Label("Full Video Size:", style={'fontWeight': 'bold', 'marginRight': '10px'}),
                            dcc.Input(id='og_size', disabled=True, style={'width': '100px', 'fontWeight': 'bold'}),
                            
                        ], style={'display': 'flex', 'alignItems': 'center', 'marginBottom': '10px'}),
                        ], width=2),
                        dbc.Col([dbc.Button("Save for later", id="save_later", color="success", n_clicks=0,style=save_link_btn),
                        dbc.Button("Check", id="place_map", color="success", n_clicks=0,style=place_map_btn),
 # Increase value to push it further down
                    ],width=1),
                        dbc.Col([
                            html.H4("Anchoring Features"),
                            dbc.Label("Distance from a building:"),
                            dcc.Dropdown(
                                id='distance',
                                options=[{'label': d, 'value': d} for d in cleaned_distance],
                                value='',
                                placeholder = "Select a distance",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Occlusion:"),
                            dcc.Dropdown(
                                id='occlusion_list',
                                options=[{'label': d, 'value': d} for d in cleaned_occlusion],
                                value='',
                                placeholder = "Select an occlusion",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Terrain type:"),
                            dcc.Dropdown(
                                id='terrain',
                                options=[{'label': d, 'value': d} for d in terrain_list],
                                value="",
                                placeholder = "Select a terrain",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Logos and text:"),
                            dcc.Dropdown(
                                id='logos_list',
                                options=[{'label': d, 'value': d} for d in cleaned_logos],
                                value='',
                                placeholder = "Select Logos & Text",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Distortions:"),
                            dcc.Dropdown(
                                id='distortions_list',
                                options=[{'label': d, 'value': d} for d in cleaned_distortions],
                                value='',
                                placeholder = "Select a Distortion",
                                className="form-control"
                            ),
                            html.Br(),
                            html.Br(),
                            html.Br(),
                            html.Br(),                            
                            html.H4(children=f"Map",style=heading_style2),
                            dl.Map(
                                id='map',
                                children=[
                                    dl.TileLayer(),
                                    dl.LayerGroup(id="map-layer", children=[]),
                                ],
                                center=(41.9028, 12.4964),  
                                zoom=10,
                                style={"width": "100%", "height": "400px", "margin": "6px","border": "2px solid black"}
                            ),
                        ], width=2),
                        dbc.Col(width=1),
                        dbc.Col([
                            html.H4("General Features"),
                            dbc.Label("Time of the day:"),
                            dcc.Dropdown(
                                id='tod',
                                options=[{'label': d, 'value': d} for d in time_list],
                                value='',
                                placeholder = "Select time of day",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Weather:"),
                            dcc.Dropdown(
                                id='weather',
                                options=[{'label': d, 'value': d} for d in weather_list],
                                value="",
                                placeholder = "Select weather",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Video Quality:"),
                            dcc.Dropdown(
                                id='vq',
                                options=[{'label': d, 'value': d} for d in cleaned_vq],
                                value="",
                                placeholder = "Select video quality",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Camera Tilt:"),
                            dcc.Dropdown(
                                id='tilt',
                                options=[{'label': d, 'value': d} for d in cleaned_tilt],
                                value='',
                                placeholder = "Select camera tilt",
                                className="form-control"
                            ),
                            html.Br(),
                            html.Br(),
                            html.Br(),
                            html.H4("Analyst Data"),
                            dbc.Label("Anlyst:"),
                            dcc.Dropdown(
                                id='analysts',
                                options=[{'label': k, 'value': k} for k in analysts],
                                placeholder="Select Analyst",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Comments:"),
                            dcc.Input(id='comments', type='text', value="", className="form-control"),
                            ],width=2),
                            dbc.Col(width=1),
                        dbc.Col([
                            html.H4("Links Collection",style=heading_style2),
                            dash_table.DataTable(
                                id='links_table',
                                columns=[
                                    {'name': 'Links', 'id': 'links'}, 
                                ],
                                data=[], 
                                row_selectable='single',
                                sort_action="native",
                                filter_action="native",
                                fixed_rows={'headers': True},
                                style_table={
                                    'maxHeight': '250px',
                                    'overflowX': 'auto',
                                    'overflowY': 'auto'
                                },
                                style_cell={
                                    'textAlign': 'center',
                                    'whiteSpace': 'normal',
                                    'overflow': 'hidden',
                                    'textOverflow': 'clip',
                                    'height': 'auto',
                                    'width': '100px',
                                    'maxWidth': '150px',
                                },

                                style_header={
                                    'backgroundColor': 'rgb(30, 30, 30)',
                                    'color': 'white',
                                    'fontWeight': 'bold',
                                },
                            ),
                    html.Br(),
                    html.Br(),    
                    html.Br(),    
                        html.H4("Watch It Here:",style=heading_style2),
                    html.Br(),                 
                html.Div(
                    dash_player.DashPlayer(
                        id='picked_video_insert',
                        url="",
                        controls=True,
                        width="800px",
                        height="400px",
                        style={"border": "2px solid black"}
                    ),
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "marginBottom": "-50px",
                    })

                    ],width=3),
                        
                        # Third Column (Button + Modal)
                        dbc.Col([
                            dbc.Button(
                                "Insert",
                                id='insert',
                                color='success',
                                n_clicks=0,
                                style=button_style1
                            ),
                            dbc.Modal(
                                [
                                    dbc.ModalHeader("Video Details"),
                                    dbc.ModalBody(
                                        html.Div(id="confirmation-message", style=modal_style)
                                    ),
                                ],
                                id="confirmation-modal",
                                is_open=False,
                            ),
                        ], width=2),
                    ])
                ]
            ),
        ]
    )

        



@app.callback(
    Output('output-duration', 'value'),
    [
        Input('input-hours', 'value'),
        Input('input-minutes', 'value'),
        Input('input-seconds', 'value'),
        Input('input-hours_end', 'value'),
        Input('input-minutes_end', 'value'),
        Input('input-seconds_end', 'value'),
        Input('checkbox','value')
    ]
)
def calculate_duration(start_hours, start_minutes, start_seconds,
                       end_hours, end_minutes, end_seconds, checked):
    
    if not checked:
        # Ensure all start and end inputs are valid (not None)
        if start_hours is None or start_minutes is None or start_seconds is None:
            return "Invalid duration!"
        if end_hours is None or end_minutes is None or end_seconds is None:
            return "Invalid duration!"

        # Convert to total seconds
        start_total = start_hours * 3600 + start_minutes * 60 + start_seconds
        end_total = end_hours * 3600 + end_minutes * 60 + end_seconds

        duration_diff = end_total - start_total

        # Handle negative or zero duration
        if duration_diff <= 0:
            return "Invalid duration!"

        hours = duration_diff // 3600
        minutes = (duration_diff % 3600) // 60
        seconds = duration_diff % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    else:
        return "Full Video"


@app.callback(
    [
    Output('og_duration', 'value'),
    Output('dur_error','children'),
    Output("link_title","value"),
    Output("link_title","disabled"),
    Output("og_size","value"),

    ],
    [
        Input('link_url','value')
    ]
)


def check_dur(link):
    try:
        if not link:
            return "", "", "", True,""

        valid_url = is_valid_url(link)
        if not valid_url:
            return 'NA', "Invalid Link", "", True,""

        # Now try extracting
        ydl_opts = {}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(valid_url, download=False)
                og_dur = info_dict.get('duration', 0)
                video_og_dur = str(datetime.timedelta(seconds=og_dur))
                video_name = info_dict.get('title', 'No title found')
                video_size = info_dict.get('filesize') or info_dict.get('filesize_approx')
                if video_size:
                    vid_size = f"{video_size / (1024 * 1024):.2f} MB"
                    print(f"Video size: {video_size / (1024 * 1024):.2f} MB")
                else:
                    print("Video size not available")

                return (video_og_dur, "", video_name, True,vid_size)
            except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError, Exception) as e:
                # Handle yt-dlp specific errors
                return ("", "Failed to extract video info. Please insert manually.", "Title Not Found! Please insert manually!", False,
                "")

    except Exception as e:
        # Handle any other unexpected errors
        return ("", "Unexpected error occurred. Please try again.", "Title Not Found!", False,"")
    
@app.callback (
    [
        Output('confirmation-modal','is_open'),
        Output('confirmation-message','children'),
        Output("country","value"),
        Output('link_url','value'),
        Output('coordinates_input','value'),
        Output('sources','value'),
        Output('input-hours','value'),
        Output('input-minutes','value'),
        Output('input-seconds','value'),
        Output('input-hours_end','value'),
        Output('input-minutes_end','value'),
        Output('input-seconds_end','value'), 
        Output('tod','value'),
        Output('weather','value'),       
        Output('vq','value'),    
        Output('tilt','value'),     
        Output('distance','value'),     
        Output('occlusion_list','value'), 
        Output('terrain','value'),   
        Output('logos_list','value'),
        Output('distortions_list','value'),
        Output('analysts','value'),
        Output('comments','value'), 
        Output('links_table','data'),
        Output('links_table_store','data'),
        Output('map', 'viewport'),
        Output('map-layer', 'children'),
        Output('checkbox','value'),
        Output('picked_video_insert','url'),
        Output('link_url_error', 'children'),
        Output('coords_error', 'children'),
          

],
    
    [
    Input('insert','n_clicks'),
    Input("cities","value"),
    Input('cities', 'options'),
    Input("country","value"),
    Input('link_url','value'),
    Input('coordinates_input','value'),
    Input('sources','value'),
    Input('input-hours','value'),
    Input('input-minutes','value'),
    Input('input-seconds','value'),
    Input('input-hours_end','value'),
    Input('input-minutes_end','value'),
    Input('input-seconds_end','value'), 
    Input('tod','value'),
    Input('weather','value'),       
    Input('vq','value'),    
    Input('tilt','value'),     
    Input('distance','value'),     
    Input('occlusion_list','value'), 
    Input('terrain','value'),   
    Input('logos_list','value'),
    Input('distortions_list','value'),  
    Input('analysts','value'),
    Input('comments','value'), 
    Input('save_later','n_clicks'),
    Input('links_table','selected_rows'),
    Input('place_map','n_clicks'),
  
         
             
],
[

    State('default-values','data'),
    State('output-duration','value'),
    State('links_table_store','data'),
    State('checkbox','value'),
    State('og_duration', 'value'),
    State("link_title","value"),
    State("og_size","value"),

 
]

)

def validations(insertbtn, city_name,city_options,country_name, linkurl, coords_input,sources,hourst,minst,secst,
                hourend,minend,secend,tod,weather,vq,tilt,distancebuild,occlusion,terrain,logos,distortions,
                analyst,comments,save_later_btn,selected_link,place_on_map,
                defaults,dur_input,links_table,checkbox,og_dur,title_vid,og_size_val):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    


    if links_table is not None and (
            (isinstance(links_table, pd.DataFrame) and not links_table.empty)  # DataFrame
            or (not isinstance(links_table, pd.DataFrame) and len(links_table))  # list / dict-list
    ):
        links_data = links_table
    else:
        links_data = []
        
        
    if triggered_id == 'link_url.value':
        if linkurl:
            try:                      
                valid_url_watch = is_valid_url(linkurl)
                if valid_url_watch:
                    picked_video = valid_url_watch
                    return (
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update,dash.no_update,picked_video,"",dash.no_update
                    )
            except ValueError as e:
                # If any validation fails, catch and show the error message
                error_input = html.Div(f"Incorrect Link Format", style={"color": "red"})

                return(dash.no_update, dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update, dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update, dash.no_update,dash.no_update,dash.no_update, dash.no_update , dash.no_update,    
                dash.no_update , dash.no_update,dash.no_update,dash.no_update,error_input,dash.no_update)
        else:
            return (
            dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
            dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
            dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
            dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
            dash.no_update, dash.no_update, dash.no_update,dash.no_update,"","",dash.no_update
        )   
    if triggered_id == 'coordinates_input.value':
        if coords_input:
            try: 
                valid_coordintes_place = is_valid_coord(coords_input)
                if valid_coordintes_place or coords_input:
                    lat, lon = map(float, coords_input.split(","))
                    marker = dl.Marker(
                        position=[lat, lon],
                        children=[dl.Popup(coords_input)],
                        id='city-mark'
                    )

                    viewport = {'center': [lat, lon], 'zoom': 14}                 
                    return (
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                        dash.no_update, viewport, [marker],dash.no_update,dash.no_update,dash.no_update,""
                    )
            except ValueError as e:
                # If any validation fails, catch and show the error message
                error_input = html.Div(f"Incorrect Coordinates Format", style={"color": "red"})
                
                return(dash.no_update, dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update,dash.no_update, dash.no_update,dash.no_update,dash.no_update,
                dash.no_update,dash.no_update, dash.no_update,dash.no_update,dash.no_update, dash.no_update , dash.no_update,    
                dash.no_update , dash.no_update,dash.no_update,dash.no_update,dash.no_update,error_input)
        else:
            if city_name:
                center= cities[cities['City Name'] == city_name]['CityCenter'].iloc[0]
                lat, lon =map(float, center.split(",")) 
                map_center_city = {'center': [lat, lon], 'zoom': 10}
            else:
                map_center_city = {'center': [41.9028, 12.4964], 'zoom': 10}    
            return (
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, map_center_city,[],dash.no_update,dash.no_update,dash.no_update,""
            ) 


                    
    elif triggered_id == 'insert.n_clicks':
        try:
            general_validation = general_validations (analyst,city_name,distancebuild,occlusion,terrain,logos,
                         distortions, tod,weather,vq,tilt)
               
            valid_url = is_valid_url(linkurl)                
            valid_coordinates = valid_coords(coords_input)


            df_all = city_load_data("SELECT * FROM geo")
            cut_db = city_load_data("SELECT * FROM geo_cut")
            
            matched_rows = df_all[df_all['Links'] == valid_url]
            
            if checkbox is None or len(checkbox) == 0:    
                start_time = f"{minst}:{secst:02}"
                end_time = f"{minend}:{secend:02}"

                dur_time =  re.sub(r"^00:0?(\d):", r"\1:", dur_input)
            else:
                start_time=f"0:00"
                end_time = f"0:00" 
                dur_time = dur_input  
                
            # Step 2: If there are any such rows, check for coordinate match
            if not matched_rows.empty:
                match_copy = matched_rows.copy()
                match_copy['base'] = match_copy['Cut_ID'].str.extract(r'^(.*)_v\d+$')[0] 
                match_copy['version'] = match_copy['Cut_ID'].str.extract(r'_v(\d+)$')[0].astype(int)
                
                # Step 3: Keep only the latest version for each base
                latest_versions = match_copy.sort_values('version').groupby('base', as_index=False).last()                
                if valid_coordinates in latest_versions['Coordinates'].values:
                    raise ValueError("Video link and Coordinates already exist!")  

                video_name = match_copy['Title'].values[0]
                video_og_dur = match_copy['Original Duration'].values[0]


                match_rows = latest_versions.copy()  # Safely modify

                time_to_check = parse_time(start_time)
                match_rows['Start Time Parsed'] = match_rows['Start Time'].apply(parse_time)
                match_rows['Finish Time Parsed'] = match_rows['Finish Time'].apply(parse_time)

                dur_dup = match_rows.apply(
                    lambda row: row['Start Time Parsed'] <= time_to_check <= row['Finish Time Parsed'],
                    axis=1
                )

                full_video_cross = match_rows.apply(
                    lambda row: row['Duration'] == "Full Video" ,
                    axis=1
                )

                if dur_dup.any() or full_video_cross.any():
                    raise ValueError("There's already this video with another crossing timing, please select another duration!")


            else:   
                if 'youtube' in valid_url and 'Youtube' in sources:
                    with yt_dlp.YoutubeDL() as ydl:
                        video_name = title_vid
                       

                elif 'tiktok' in valid_url and 'Tiktok' in sources:
                    with yt_dlp.YoutubeDL() as ydl:

                        video_name = title_vid

                elif 'facebook' in valid_url and 'facebook' in sources:
                    with yt_dlp.YoutubeDL() as ydl:
                        video_name = title_vid
                        
                else:
                    raise ValueError("Video title not found - maybe not a matching source?")
                

            end_time_check = parse_input_time(end_time)
            og_dur_check = parse_duration(og_dur)
            
            if end_time_check > og_dur_check:
                raise ValueError ("Annotation time exceeding original video duration!")

            time_d=(datetime.datetime.now())
            formatted_datetime = time_d.strftime("%Y-%m-%d %H:%M:%S")    
           
            cut_id = generate_unique_random_id(city_name,df_all,valid_url)
            video_id = '_'.join(cut_id.split('_')[:3])
            
            if og_dur:
                parts = og_dur.split(":")
                if parts[0] == "0":
                    formatted_duration = ":".join(parts[1:])
                    minutes, seconds = map(int, formatted_duration.split(":"))
                    formatted_dur = f"{minutes}:{seconds:02d}"
                else:
                    formatted_dur = og_dur     
            else:
                raise ValueError("Please insert original video duration")    
                       
            latest_index = int(df_all['Index'].iloc[-1]) + 1

            
            row_data =[latest_index,cut_id,video_id,country_name,city_name,linkurl,video_name,valid_coordinates,analyst,sources,formatted_dur,start_time,end_time,dur_time,
                       tod,terrain,weather,vq,tilt,distancebuild,occlusion,distortions,
                       logos,comments,formatted_datetime]

            append_row_to_sql(row_data,table_name="geo")
            
            cut_sheet = '1R-qzDHwVB6f27sGYQvpQTZIoDQbzla59j5jM0rfIm3M'
            cut_ranges = 'Cuts_DB!A1:Q500000'
            
            latest_cut_index = int(cut_db['Index'].iloc[-1]) + 1
            cuts_row_data =[latest_cut_index,cut_id,country_name,city_name,linkurl,video_name,'TBD',start_time,end_time,dur_time,'TBD',
                            'TBD','FALSE','og_user','TBD',og_size_val,formatted_dur]
            append_row_to_sql(cuts_row_data, table_name="geo_cut")
            
            
            lat, lon = map(float, valid_coordinates.split(","))   
            marker = dl.Marker(
                position=[lat, lon],
                children=[dl.Popup(valid_coordinates)],
                id='city-mark'
            )

            viewport = {'center': [lat, lon], 'zoom': 14}
            
            links_dframe = pd.DataFrame(links_table or [])

            links_dframe = pd.DataFrame(links_table or [])
            if 'links' in links_dframe.columns:
                links_dframe = links_dframe[links_dframe['links'] != valid_url]
            else:
                links_dframe = pd.DataFrame(columns=['links'])
            links_data_clean = links_dframe.to_dict('records')

                                                       
            # If all validations pass
            result_window = html.Div([
                html.H1('Video Added Successfully!'),
                html.Br(),
                html.H3("Video Details: "),
                html.Ul([
                    html.Li(f"City: {city_name}"),
                    html.Li(f"City: {country_name}"),
                    html.Li(f"Cut_id: {cut_id}"),
                    html.Li(f"Video Link: {valid_url}"),
                    html.Li(f"Video Name: {video_name}"),
                    html.Li(f"Video Source: {sources}"),                    
                    html.Li(f"Coordinates: {valid_coordinates}"),
                    html.Li(f"Start Time: {start_time}"),
                    html.Li(f"Start Time: {end_time}"),                    
                    html.Li(f"Video Duration: {dur_time}"),
                    html.Li(f"Analyst: {analyst}"),
                    html.Li(f"Time of the day: {tod}"),
                    html.Li(f"Weather: {weather}"), 
                    html.Li(f"Video Quality: {vq}"), 
                    html.Li(f"Camera Tilt: {tilt}"),
                    html.Li(f"Distance from a building: {distancebuild}"),
                    html.Li(f"Occlusion: {occlusion}"),                                         
                    html.Li(f"Terrain: {terrain}"),
                    html.Li(f"Logos and Text: {logos}"),
                    html.Li(f"Distortions: {distortions}"),
                    html.Li(f"Comments: {comments}")                                                                    
                ])
            ])
            
            
            return (True, result_window,
            dash.no_update,
            defaults['link_url'],
            defaults['coordinates_input'],
            defaults['sources'],
            defaults['input-hours'],
            defaults['input-minutes'],
            defaults['input-seconds'],
            defaults['input-hours_end'],
            defaults['input-minutes_end'],
            defaults['input-seconds_end'],
            defaults['tod'],
            defaults['weather'],
            defaults['vq'],  
            defaults['tilt'],
            defaults['distance'],
            defaults['occlusion_list'],     
            defaults['terrain'],
            defaults['logos_list'],
            defaults['distortions_list'],
            defaults['analysts'],  
            defaults['comments'], links_data_clean , links_data_clean, viewport, [marker],[],"",dash.no_update,dash.no_update                     
            )


        except ValueError as e:
            # If any validation fails, catch and show the error message
            error_message = html.Div(
                [
                    html.H5("⚠️ Validation Error", style={"color": "red"}),
                    html.P(str(e), style={"color": "black"})
                ]
            )
            return( True, error_message,dash.no_update,
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
            dash.no_update, dash.no_update , dash.no_update, dash.no_update ,
            dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update)
    
    elif triggered_id == 'save_later.n_clicks':
        try:
            valid_url = is_valid_url(linkurl)
            if valid_url:
                if links_table is not None:

                    links_entry = next((entry for entry in links_table if entry.get('links') == valid_url), None) 
                    if links_entry is None:
                        row_links_table = {
                        "links": f"{valid_url}"}
                        links_data.append(row_links_table)
                    else:
                        links_data = links_table
                else:
                    row_links_table = {
                    "links": f"{valid_url}"}
                    links_data.append(row_links_table)
            
            return (False,dash.no_update,dash.no_update,"",dash.no_update,dash.no_update,dash.no_update,dash.no_update,
            dash.no_update, dash.no_update,dash.no_update, dash.no_update,dash.no_update,dash.no_update,dash.no_update,
            dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
            dash.no_update, links_data ,links_data, dash.no_update , dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update )
            
        except ValueError as e:
            # If any validation fails, catch and show the error message
            error_message = html.Div(
                [
                    html.H5("⚠️ Validation Error", style={"color": "red"}),
                    html.P(str(e), style={"color": "black"})
                ]
            )
        return( True, error_message,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
        dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
        dash.no_update,dash.no_update,dash.no_update, dash.no_update,dash.no_update,dash.no_update,
        dash.no_update,dash.no_update, dash.no_update,dash.no_update,dash.no_update, dash.no_update , dash.no_update,    
         dash.no_update , dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update )
        
    elif triggered_id == 'links_table.selected_rows':
        row_idx = selected_link[0]
        links_df = pd.DataFrame(links_table)
        if row_idx < len(links_df):
            selected_url = links_df.iloc[row_idx][links_df.columns[0]]
            picked_url = selected_url
        return (False,dash.no_update,dash.no_update,selected_url,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
        dash.no_update, dash.no_update,dash.no_update, dash.no_update,dash.no_update,dash.no_update,dash.no_update,
        dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update,
        dash.no_update, dash.no_update ,dash.no_update, dash.no_update , dash.no_update,dash.no_update,picked_url,dash.no_update,dash.no_update )
    
    
    elif triggered_id == 'place_map.n_clicks':
        try:
            validated_coor = valid_coords(coords_input)
            if not validated_coor or not city_name:
                raise ValueError('Please insert both coordinates & city name!')
            
            polygodid = cities[cities['City Name'] == city_name]['PolygonID'].values[0]
            request = drive_service.files().get_media(fileId=polygodid)
            polygon_bytes = request.execute()

            try:
                if isinstance(polygon_bytes, bytes):
                    polygon_data = json.loads(polygon_bytes.decode('utf-8'))
                else:
                    polygon_data = json.loads(polygon_bytes)
            except Exception:
                polygon_data = []
            poly_coords = [tuple(coord) for coord in polygon_data]

            lat, lon = map(float, validated_coor.split(","))    

            if is_inside_any(lat, lon, poly_coords):
                validation_msg = html.Div(
                    [
                        html.H5("✅ Success", style={"color": "green"}),
                        html.P(f"{validated_coor} is in the Polygon", style={"color": "green", "font-weight": "bold"})
                    ]
                )
            else:
                validation_msg = html.Div(
                    [
                        html.H5("❌ Warning", style={"color": "red"}),
                        html.P(f"{validated_coor} is out of the Polygon", style={"color": "red", "font-weight": "bold"})
                    ]
                )

            marker = dl.Marker(
                position=[lat, lon],
                children=[dl.Popup(validated_coor)],
                id='city-mark'
            )

            viewport = {'center': [lat, lon], 'zoom': 14}



            return (
                True, validation_msg, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,dash.no_update,
                viewport, [marker],dash.no_update,dash.no_update,dash.no_update,dash.no_update )

        except ValueError as e:
            error_message = html.Div(
                [
                    html.H5("⚠️ Validation Error", style={"color": "red"}),
                    html.P(str(e), style={"color": "black"})
                ]
            )

            return (
                True, error_message, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update, dash.no_update,
                dash.no_update, dash.no_update, dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update 
            )


        
                                                     
    else:
        # Update Country based on City selected
        if triggered_id == 'cities.value':
            if city_name:
                country_match = cities[cities['City Name'] == city_name]['Country']
                country_val = country_match.iloc[0] if not country_match.empty else ''
                center= cities[cities['City Name'] == city_name]['CityCenter'].iloc[0]
                lat, lon =map(float, center.split(",")) 
                map_center_city = {'center': [lat, lon], 'zoom': 10}         
            else:
                country_val = ''
                map_center_city= {'center': [41.9028, 12.4964], 'zoom': 10} 
            return (False,dash.no_update,country_val,
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
                dash.no_update, dash.no_update, dash.no_update, map_center_city,
                [],dash.no_update,dash.no_update,dash.no_update,dash.no_update )  # Rest of outputs unchanged
        else:

            return (False, dash.no_update,
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
                    dash.no_update, dash.no_update, dash.no_update, dash.no_update ,
                    dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update )

filters_list= ['City','Record ID','Analyst']        

# Find the first timestamp
df_city_edit['TimeStamp'] = pd.to_datetime(df_city_edit['TimeStamp'], errors='coerce')

# 2. Drop rows with bad timestamps if needed
df_city_edit = df_city_edit.dropna(subset=['TimeStamp'])

# 3. Get the earliest timestamp
first_timestamp = df_city_edit['TimeStamp'].min()

# Create a function to assign relative quarters
def assign_relative_quarter(ts):
    diff = ts - first_timestamp
    months = diff.days // 30  # Approximate months
    quarter = (months // 3) + 1
    return quarter
df_city_edit['Quarter'] = df_city_edit['TimeStamp'].apply(assign_relative_quarter)

# Example: sum by quarter
quarters = df_city_edit['Quarter'].nunique()
timeframes = ["", "Year", "1/2 Year", "3 Months", "Month", "Week", "Day", ""]

def edit_tab_layout():
     return html.Div(
        style=background_style,
        children=[
            dbc.Container(
                style=container_style_2,
                children=[
                dcc.Store(id='default-values_edit', data={
                    'link_url_edit': "",
                    "coordinates_input_edit": "",
                    'sources_edit': "",
                    'input-hours_edit': 0,
                    'input-minutes_edit': 0,
                    'input-seconds_edit': 0,
                    'input-hours_end_edit': 0,
                    'input-minutes_end_edit': 0,
                    'input-seconds_end_edit': 0,
                    'tod_edit': '',
                    'weather_edit': "",
                    'vq_edit': "",
                    'tilt_edit': '',
                    'distance_edit': '',
                    'occlusion_list_edit': '',
                    'terrain_edit': "",
                    'logos_list_edit': '',
                    'distortions_list_edit': '',
                    'analysts_edit': 'Select Analyst',
                    'comments_edit':""
                }),
                dcc.Store(id="stored-videoid", data=None),
                dcc.Store(id='latest_df',data=None),
                dcc.Store(id="refresh_flag"),

                    html.H1("Edit Mode", style=heading_style),
                    html.Hr(),

                    dbc.Row([
                        # First Column
                        dbc.Col([
                            html.H4("Pick a City & Video"),
                            dbc.Label("Choose a Filter:"),
                            dcc.Dropdown(
                                id='filters_list',
                                options=[{'label': k, 'value': k} for k in filters_list],
                                value="",
                                className="form-control",
                                placeholder = "Select a filter"
                            ),   
                            html.Br(),
                            dbc.Label("Filter Annotation Time by Last (All Time - Hour):"),
                            html.Div(
                                dcc.RangeSlider(
                                    id='timeframe_slider',
                                    min=0,
                                    max=len(timeframes) - 1,
                                    step=1,
                                    value=[0, len(timeframes) - 1],
                                    marks={i: label for i, label in enumerate(timeframes)},
                                    tooltip={"always_visible": True, "placement": "bottom"}
                                ),
                                style={"width": "550px", "margin-bottom": "20px"}  # Increase width as needed
                            ),
                            html.Br(),  
                            html.Br(),                       
                            dbc.Label("Choose a sub filter:"),
                            dcc.Dropdown(
                                id='cities_edit',
                                options=[{'label': k, 'value': k} for k in cities_list],
                                value="",
                                className="form-control"
                            ),
                            html.Br(),
                        html.Div([
                            dbc.Row([
                                dbc.Col([
                                    dbc.Label("Pick a Cut ID:"),
                                    dcc.Dropdown(
                                        id='videoid_edit',
                                        options=[],
                                        value="",
                                        className="form-control",
                                        placeholder="Select a cut id"
                                    )
                                ], width=7),  # Half width
                                dbc.Col([
                                    dbc.Label("Pick a Version:"),
                                    dcc.Dropdown(
                                        id='cut_version',
                                        options=[],
                                        value="",
                                        className="form-control",
                                        placeholder="Select a version"
                                    )
                                ], width=5)  # Half width
                            ]),
                            html.Br()
                        ]),
                            dbc.Label("Pick a source:"),
                            dcc.Dropdown(
                                id='sources_edit',
                                options=[{'label': d, 'value': d} for d in source_list],
                                value="",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Video Link:"),
                            dcc.Input(id='link_url_edit', type='text', value="", className="form-control"),
                            html.Div(id="link_error_edit", style={"color": "red"}),
                            html.Br(),
                            dbc.Label("Coordinates:"),
                            dcc.Input(id='coordinates_input_edit', type='text', value="", className="form-control"),
                            html.Div(id="coords_error_ed", style={"color": "red"}),
                            html.Br(),
                            html.Br(),
                            html.Br(),
                            html.H4("Timing"),
                            dbc.Label("Start Time:"),
                            html.Br(),
                            html.Div([
                                html.Div([
                                    html.Label("Hours"),
                                    dcc.Input(id='input-hours_edit', type='number', min=0, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label("Minutes"),
                                    dcc.Input(id='input-minutes_edit', type='number', min=0, max=59, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label("Seconds"),
                                    dcc.Input(id='input-seconds_edit', type='number', min=0, max=59, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block'}),
                            ]),
                            html.Br(),
                            dbc.Label("End Time:"),
                            html.Br(),
                            html.Div([
                                html.Div([
                                    html.Label("Hours"),
                                    dcc.Input(id='input-hours_end_edit', type='number', min=0, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label("Minutes"),
                                    dcc.Input(id='input-minutes_end_edit', type='number', min=0, max=59, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block', 'margin-right': '10px'}),
                                html.Div([
                                    html.Label("Seconds"),
                                    dcc.Input(id='input-seconds_end_edit', type='number', min=0, max=59, step=1, value=0, className="form-control"),
                                ], style={'display': 'inline-block'}),
                            ]),
                            html.Br(),
                            dbc.Label("Duration:  "),
                            dcc.Input(id='output-duration_edit', disabled=True, style={'margin-top': '30px', 'margin-left': '30px','font-weight': 'bold'}),
                        ], width=2),
                        dbc.Col([
                            html.Div([dbc.Label("Records Number:"),
                            html.Br(),
                            dcc.Input(id='rec_num', type='number', disabled=True, value=0, className="form-control")]
                            ,style=rec_num),
                            dbc.Button("↻", id='update_ids', color='success', n_clicks=0, style=button_style4),
                            dbc.Button("Check", id="place_map_ed", color="success", n_clicks=0,style=check_btn_ed),
                            dcc.Checklist(
                                    options=[{'label': '  Full', 'value': 'on'}],
                                    value=[], 
                                    id='checkbox_edit',
                                    style={'marginLeft': '-50px', 'marginTop': '965px'})                             
                            ],width=1),
                        dbc.Col([
                            html.H4("Anchoring Features"),
                            dbc.Label("Distance from a building:"),
                            dcc.Dropdown(
                                id='distance_edit',
                                options=[{'label': d, 'value': d} for d in distance],
                                value='',
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Occlusion:"),
                            dcc.Dropdown(
                                id='occlusion_list_edit',
                                options=[{'label': d, 'value': d} for d in occlusion],
                                value='',
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Terrain type:"),
                            dcc.Dropdown(
                                id='terrain_edit',
                                options=[{'label': d, 'value': d} for d in terrain_list],
                                value="",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Logos and text:"),
                            dcc.Dropdown(
                                id='logos_list_edit',
                                options=[{'label': d, 'value': d} for d in logos],
                                value='',
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Distortions:"),
                            dcc.Dropdown(
                                id='distortions_list_edit',
                                options=[{'label': d, 'value': d} for d in distortions],
                                value='',
                                className="form-control"
                            ),
                            html.Br(),
                            html.Br(),
                            html.Br(),
                            html.Br(),      
                            html.H4("Map",id="map_title",style=heading_style2),
                            dl.Map(
                                id='map_edit',
                                children=[
                                    dl.TileLayer(),
                                    dl.LayerGroup(id="map-layer_ed", children=[]),
                                ],
                                center=(41.9028, 12.4964),  
                                zoom=10,
                                style={"width": "100%", "height": "400px", "margin": "6px","border": "2px solid black"}
                            ),
                        ], width=2),
                        dbc.Col(width=1),
                        dbc.Col([
                            html.H4("General Features"),
                            dbc.Label("Time of the day:"),
                            dcc.Dropdown(
                                id='tod_edit',
                                options=[{'label': d, 'value': d} for d in time_list],
                                value='',
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Weather:"),
                            dcc.Dropdown(
                                id='weather_edit',
                                options=[{'label': d, 'value': d} for d in weather_list],
                                value="",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Video Quality:"),
                            dcc.Dropdown(
                                id='vq_edit',
                                options=[{'label': d, 'value': d} for d in video_vq],
                                value="",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Camera Tilt:"),
                            dcc.Dropdown(
                                id='tilt_edit',
                                options=[{'label': d, 'value': d} for d in camera_tilt],
                                value='',
                                className="form-control"
                            ),
                            html.Br(),
                            html.Br(),
                            html.Br(),
                            html.H4("Analyst Data"),
                            dbc.Label("Anlyst:"),
                            dcc.Dropdown(
                                id='analysts_edit',
                                options=[{'label': k, 'value': k} for k in analysts],
                                placeholder="Select Analyst",
                                className="form-control"
                            ),
                            html.Br(),
                            dbc.Label("Comments:"),
                            dcc.Input(id='comments_edit', type='text', value="", className="form-control"),                           
                            ],width=2),
                        dbc.Col([html.H2("Watch It Here:"),
                    html.Br(),
                    html.Br(),    
                    html.Br(),                 
                html.Div(
                    dash_player.DashPlayer(
                        id='picked_video_edit',
                        url="",
                        controls=True,
                        width="800px",
                        height="400px",
                        style={"border": "2px solid black"}
                    ),
                    style={
                        "display": "flex",
                        "justifyContent": "center",
                        "marginBottom": "-50px",
                    }
                ),       
                    ],width=4), 
                    html.Br(),
                    html.Div(
                        [
                            dbc.Button("Update", id='update', color='success', n_clicks=0, style=button_style2),
                            dbc.Button("Delete", id='delete', color='danger', n_clicks=0, style=button_style3)
                        ],
                        style={"display": "flex", "justifyContent": "right", "gap": "40px", "marginBottom": "30px"}
                    ),
                        # Third Column (Button + Modal)

                            dbc.Modal(
                                [
                                    dbc.ModalHeader("Edit Mode:"),
                                    dbc.ModalBody(
                                        html.Div(id="confirmation-message_edit", style=modal_style)
                                    ),
                                ],
                                id="confirmation-modal_edit",
                                is_open=False,
                            ),
                            dbc.Modal(
                                [
                                    dbc.ModalHeader("Confirmation"),
                                    dbc.ModalBody(
                                        html.Div("Are you sure you want to proceed?", style=modal_style)
                                    ),
                                    dbc.ModalFooter(
                                        dbc.ButtonGroup(
                                            [
                                                dbc.Button("Yes", id="confirm-yes", color="success", n_clicks=0),
                                                dbc.Button("No", id="confirm-no", color="danger", n_clicks=0),
                                            ],
                                            className="w-100",  # full width button group
                                        )
                                    ),
                                ],
                                id="confirmation-update",
                                is_open=False,
                            ),
                    dbc.Modal(
                        [
                            dbc.ModalHeader("Removal Confirmation"),
                            dbc.ModalBody([
                                dbc.Label("Since it's a irreversable action, please insert the removal key: "),
                                dbc.Input(
                                    id="delete_password",
                                    type="password",
                                    placeholder="Enter your password...",
                                )
                        ]),
                            dbc.ModalFooter(
                                dbc.Button(
                                    "Delete",
                                    id="delete_btn",
                                    color="primary",
                                    className="ml-auto"
                                ),
                            ),
                        ],
                        id="delete-modal",
                        is_open=False,  # Initially closed
                    ),
                    ])
                ]
            ),
        ]
    )

def video_options_per_time (df,timing):
    today = pd.Timestamp.today().normalize()
    df['TimeStamp'] = pd.to_datetime(df['TimeStamp'], errors='coerce')
    time_delta = today - pd.Timedelta(days=timing)
    mask = df['TimeStamp'].between(time_delta, today)
    filtered_df = df.loc[mask].copy()
    filtered_df['base'] = filtered_df['Cut_ID'].str.extract(r'^(.*)_v\d+$')[0]
    voptions = filtered_df['base'].unique()
    
    return voptions
global time_constants
time_constants = ['Up to a week ago', 'Up to 2 weeks ago','Up to a month ago','Up to 3 months ago','Up to half a year ago', 'Up to a year ago', 'All Time'] 


@app.callback(
    Output('output-duration_edit', 'value'),
    [
        Input('input-hours_edit','value'),
        Input('input-minutes_edit','value'),
        Input('input-seconds_edit','value'),
        Input('input-hours_end_edit','value'),
        Input('input-minutes_end_edit','value'),
        Input('input-seconds_end_edit','value'),
        Input('checkbox_edit','value') 
    ]
)

def calculate_duration_edit(start_hours, start_minutes, start_seconds,
                       end_hours, end_minutes, end_seconds,checkbox_edit):
    # Calculate start and end times in total seconds
    if not checkbox_edit:
        # Ensure all start and end inputs are valid (not None)
        if start_hours is None or start_minutes is None or start_seconds is None:
            return "Invalid duration!"
        if end_hours is None or end_minutes is None or end_seconds is None:
            return "Invalid duration!"

        # Convert to total seconds
        start_total = start_hours * 3600 + start_minutes * 60 + start_seconds
        end_total = end_hours * 3600 + end_minutes * 60 + end_seconds

        duration_diff = end_total - start_total

        # Handle negative or zero duration
        if duration_diff <= 0:
            return "Invalid duration!"

        hours = duration_diff // 3600
        minutes = (duration_diff % 3600) // 60
        seconds = duration_diff % 60

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    else:
        return "Full Video"


    
@app.callback(
    Output("cities_edit", "options"),
    Input("filters_list", "value"),
    Input("timeframe_slider", "value")
)
def load_sub_filter(selected_filter, slider_val):

    # ── 1.  make TimeStamp tz-aware & in UTC ───────────────────────
    ts = pd.to_datetime(df_city_edit["TimeStamp"], errors="coerce")

    if ts.dt.tz is None:                                             # tz-naïve
        ts = (
            ts.dt.tz_localize(
                "Asia/Jerusalem",
                ambiguous="NaT",          # DST fall-back ambiguities → NaT
                nonexistent="shift_forward",  # spring-forward gaps → next valid
            )
            .dt.tz_convert("UTC")
        )
    else:                                                            # tz-aware
        ts = ts.dt.tz_convert("UTC")                                 # → UTC

    df_city_edit["TimeStamp"] = ts

    # ── 2.  map slider indices → look-back windows ─────────────────
    lookback = {
        7: pd.Timedelta(hours=1),        # last hour
        6: pd.Timedelta(days=1),         # last day
        5: pd.Timedelta(days=7),         # last week
        4: pd.Timedelta(days=30),        # ~ last month
        3: pd.Timedelta(days=90),        # ~ last 3 months
        2: pd.Timedelta(days=183),       # ~ last 6 months
        1: pd.Timedelta(days=365),       # last year
        0: None,                         # “all time”
    }

    low_idx, high_idx = slider_val

    # ── 3a.  if the slider is untouched (full range 0→7), don't filter at all
    if (low_idx, high_idx) == (0, 7):
        window_df = df_city_edit
    else:
        # ── 3b.  otherwise compute cutoffs and slice as before ──────
        now = pd.Timestamp.now(tz="Asia/Jerusalem")

        # newer bound (right-hand knob)
        start_cutoff = (
            now - lookback[high_idx]
            if lookback[high_idx] is not None
            else pd.Timestamp.min.tz_localize(tz="Asia/Jerusalem")
        )
        print(start_cutoff)

        # older bound (left-hand knob)
        end_cutoff = (
            now - lookback[low_idx]
            if lookback[low_idx] is not None
            else now
        )

        print(end_cutoff)
        # swap if crossed
        if start_cutoff > end_cutoff:
            start_cutoff, end_cutoff = end_cutoff, start_cutoff

        window_df = df_city_edit.loc[
            df_city_edit["TimeStamp"].between(start_cutoff, end_cutoff)
        ]


    # ── 4.  return the unique values for the chosen sub-filter ─────
    if selected_filter == "City":
        opts = sorted(window_df["City"].dropna().unique())
    elif selected_filter == "Record ID":
        opts = sorted(window_df["record_id"].dropna().unique())
    elif selected_filter == "Analyst":
        opts = sorted(window_df["Analyst"].dropna().unique())
    else:
        opts = []       # invalid selector → empty list

    return opts

@app.callback(
    Output("videoid_edit","options"),
    Output("videoid_edit","value"),
    Output("latest_df",   "data"),
    Output("rec_num","value"),

    Input("cities_edit",  "value"),
    Input("update_ids",   "n_clicks"),

         # <-- NEW
    prevent_initial_call=True
)            

def loading_videoid_options(selected_input,update_ids):
    sheetid_edit = '1aIEe5GLAY-MVfGPj8BVjaiZoJ1z1lWwfXUTBswT576U'
    sheetrange_edit = 'All_Cities!A1:Y500000'
    df_city_edit = city_load_data(sheetid_edit, sheetrange_edit)
    
    rec_num=""
    
    df_city_edit['TimeStamp'] = pd.to_datetime(df_city_edit['TimeStamp'])  # Convert to datetime
    

    q2_df = df_city_edit.copy()
    q2_df['base'] = q2_df['Cut_ID'].str.extract(r'^(.*)_v\d+$')[0]

    
    if selected_input in df_city_edit['City'].values:

        video_id_options =  q2_df[q2_df['City']==selected_input]['base'].unique()
        rec_num = q2_df[q2_df['City']==selected_input]['base'].shape[0]
    elif selected_input in q2_df['record_id'].values:
        video_id_options =  q2_df[q2_df['record_id']==selected_input]['base'].unique()
        rec_num = q2_df[q2_df['record_id']==selected_input]['base'].shape[0]
    elif selected_input in q2_df['Analyst'].values:
        video_id_options =  q2_df[q2_df['Analyst']==selected_input]['base'].unique() 
        rec_num = q2_df[q2_df['Analyst']==selected_input]['base'].shape[0] 
    else:
        video_id_options = []

    return (video_id_options,"Select a cut id",q2_df.to_dict('records'),rec_num)

@app.callback(
    Output("cut_version","options"),
    Output("cut_version","value"),

    Input("videoid_edit","value"),
    State("latest_df",   "data"),
)


def load_versions(cut,df):

    v_df=pd.DataFrame(df)
    if cut:
        cuts_df = v_df[v_df['Cut_ID'].str.contains(cut)].copy()
        cuts_df['version'] = cuts_df['Cut_ID'].str.extract(r'_(v\d+)$')[0]
        version_options = cuts_df['version'].unique()

        ver_val = ""
    else:
        version_options =[]
        ver_val = ""

    return version_options,ver_val


@app.callback ([
        Output('confirmation-modal_edit','is_open'),
        Output('confirmation-message_edit','children'),
        Output("stored-videoid", "data"), 
        Output('sources_edit','value'),    
        Output('link_url_edit','value'),
        Output('coordinates_input_edit','value'),
        Output('input-hours_edit','value'),
        Output('input-minutes_edit','value'),
        Output('input-seconds_edit','value'),
        Output('input-hours_end_edit','value'),
        Output('input-minutes_end_edit','value'),
        Output('input-seconds_end_edit','value'), 
        Output('tod_edit','value'),
        Output('weather_edit','value'),       
        Output('vq_edit','value'),    
        Output('tilt_edit','value'),     
        Output('distance_edit','value'),     
        Output('occlusion_list_edit','value'), 
        Output('terrain_edit','value'),   
        Output('logos_list_edit','value'),
        Output('distortions_list_edit','value'),
        Output('analysts_edit','value'),
        Output('comments_edit','value'), 
        Output('picked_video_edit','url'),
        Output("confirmation-update", "is_open"),
        Output('delete-modal',"is_open"),
        Output('checkbox_edit','value'),
        Output('link_error_edit', 'children'),
        Output('coords_error_ed', 'children'),
        Output('map_edit', 'viewport'),
        Output('map-layer_ed', 'children'),
        
        
   ],
    [ 
    Input("cities_edit",  "value"),
    Input("videoid_edit","value"),
    Input("cut_version","value"),
    Input('sources_edit','value'),    
    Input('link_url_edit','value'),
    Input('coordinates_input_edit','value'),
    Input('tod_edit','value'),
    Input('weather_edit','value'),       
    Input('vq_edit','value'),    
    Input('tilt_edit','value'),     
    Input('distance_edit','value'),     
    Input('occlusion_list_edit','value'), 
    Input('terrain_edit','value'),   
    Input('logos_list_edit','value'),
    Input('distortions_list_edit','value'),
    Input('analysts_edit','value'),
    Input('comments_edit','value'),
    Input('update','n_clicks'),
    Input("confirm-yes", "n_clicks"),
    Input("confirm-no", "n_clicks"),
    Input('delete','n_clicks'),
    Input('delete_btn','n_clicks'),
    Input('place_map_ed','n_clicks'),
    

           
    ],
[    
 State('output-duration_edit','value'), 
 State('default-values_edit','data'),
 State("stored-videoid", "data"),
 State('latest_df','data'),
 State("confirmation-update", "is_open"),
 State('delete_password','value'),
 State('checkbox_edit','value'),
State('input-hours_edit','value'),
State('input-minutes_edit','value'),
State('input-seconds_edit','value'),
State('input-hours_end_edit','value'),
State('input-minutes_end_edit','value'),
State('input-seconds_end_edit','value'),    
],
               
)
def edit_mode(city_name_edit, video_cut, video_version, sourceedit, linkedit, coord_edit, tod_edit, weather_edit, vq_edit, tilt_edit, distance_edit,
              occlusion_edit, terrain_edit, logos_edit, distortions_edit, analyst_edit, comments_edit, update,confirm_yes,confirm_no,
              delete,delete_btn, check_btn,duration_edit, defaults_edit,stored_videoid,latest_df,update_confirmation,delete_password,checkbox_ed,
              hours_st_edit, minute_st_edit, sec_st_edit,hours_end_edit, min_end_edit, sec_end_edit,):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    df_city_edit = pd.DataFrame(latest_df)
    # Define fallback/default output with the right length (25 in your case)
    
    if video_version:
        video_ver = f"{video_cut}_{video_version}"
        city_val = df_city_edit[df_city_edit['Cut_ID'] == video_ver]['City'].values[0]
    else:
        video_ver = ""
        city_val = ""
    print(video_ver)
    
    if not video_version :
        # Reset all fields to defaults
        return (
            False, dash.no_update, dash.no_update,"","","",0,0,0,0,0,0,"","","","","","","","","","","","",False,False,dash.no_update,dash.no_update,dash.no_update
        ,dash.no_update,[])


                        
    elif triggered_id == 'link_url_edit.value':
        if linkedit:
            try: 
                valid_url_watch = is_valid_url(linkedit)
                if valid_url_watch:
                    picked_video = valid_url_watch
                    return (False, dash.no_update,stored_videoid) + (dash.no_update,) * 20 + (picked_video,False,False,dash.no_update,"",dash.no_update,dash.no_update,dash.no_update)
            except ValueError as e:
                # If any validation fails, catch and show the error message
                error_input = html.Div(f"Incorrect Link Format", style={"color": "red"})   
                return (False, dash.no_update,stored_videoid) + (dash.no_update,) * 20 + (dash.no_update,False,False,dash.no_update,error_input,dash.no_update,dash.no_update,dash.no_update)
        else:
            return (False, dash.no_update,stored_videoid) + (dash.no_update,) * 20 + ("",False,False,dash.no_update,"",dash.no_update,dash.no_update,dash.no_update)

    elif triggered_id == 'coordinates_input_edit.value':
        if coord_edit:
            try: 
                lat_str, lon_str = coord_edit.split(",")
                # 2) … and 2) both must convert to float
                lat, lon = float(lat_str), float(lon_str)
                marker = dl.Marker(position=[lat, lon],
                                children=[dl.Popup(coord_edit)],
                                id='city-mark')
                viewport = {'center': [lat, lon], 'zoom': 14}
                return (False, dash.no_update,stored_videoid) + (dash.no_update,) * 20 + (dash.no_update,False,False,dash.no_update,dash.no_update,"",viewport,[marker])
            except ValueError as e:
                # If any validation fails, catch and show the error message
                error_input_cor = html.Div(f"Incorrect Coordinates Format", style={"color": "red"})
                return (False, dash.no_update,stored_videoid) + (dash.no_update,) * 20 + (dash.no_update,False,False,dash.no_update,dash.no_update,error_input_cor,dash.no_update,dash.no_update)
        else:
            center= cities[cities['City Name'] == city_name_edit]['CityCenter'].iloc[0]
            lat, lon =map(float, center.split(",")) 
            map_center_city = {'center': [lat, lon], 'zoom': 10}      
            return (False, dash.no_update,stored_videoid) + (dash.no_update,) * 20 + (dash.no_update,False,False,dash.no_update,dash.no_update,"",map_center_city,[])



    elif triggered_id == 'place_map_ed.n_clicks':
        try:
            lat_str, lon_str = coord_edit.split(",")
            # 2) … and 2) both must convert to float
            lat, lon = float(lat_str), float(lon_str)
            if not coord_edit or not city_name_edit:
                raise ValueError('Please insert both coordinates & city name!')
            
            polygodid = cities[cities['City Name'] == city_name_edit]['PolygonID'].values[0]
            request = drive_service.files().get_media(fileId=polygodid)
            polygon_bytes = request.execute()

            try:
                if isinstance(polygon_bytes, bytes):
                    polygon_data = json.loads(polygon_bytes.decode('utf-8'))
                else:
                    polygon_data = json.loads(polygon_bytes)
            except Exception:
                polygon_data = []
            poly_coords = [tuple(coord) for coord in polygon_data]
   

            if is_inside_any(lat, lon, poly_coords):
                validation_msg = html.Div(
                    [
                        html.H5("✅ Success", style={"color": "green"}),
                        html.P(f"{coord_edit} is in the Polygon", style={"color": "green", "font-weight": "bold"})
                    ]
                )
            else:
                validation_msg = html.Div(
                    [
                        html.H5("❌ Warning", style={"color": "red"}),
                        html.P(f"{coord_edit} is out of the Polygon", style={"color": "red", "font-weight": "bold"})
                    ]
                )

            marker = dl.Marker(
                position=[lat, lon],
                children=[dl.Popup(coord_edit)],
                id='city-mark'
            )

            viewport = {'center': [lat, lon], 'zoom': 14}
            return (True, validation_msg,stored_videoid) + (dash.no_update,) * 20 + (dash.no_update,False,False,dash.no_update,dash.no_update,"",viewport,[marker])


        except ValueError as e:
            error_message = html.Div(
                [
                    html.H5("⚠️ Validation Error", style={"color": "red"}),
                    html.P(str(e), style={"color": "black"})
                ]
            )
            return (True, validation_msg,stored_videoid) + (dash.no_update,) * 20 + (dash.no_update,False,False,dash.no_update,dash.no_update,"",viewport,[marker])


    
    elif  triggered_id == 'cut_version.value':
        row = df_city_edit[df_city_edit['Cut_ID'] == video_ver]
        if not row.empty:
            time_st = row['Start Time'].values[0]
            hh_st, mm_st, ss_st = parse_time_string(time_st)

            time_end = row['Finish Time'].values[0]
            hh_end, mm_end, ss_end = parse_time_string(time_end)

            value_check=['on'] if row['Duration'].iloc[0] == 'Full Video' else []
            
            coord_outputs = row['Coordinates'].values[0]
            lat_str_l, lon_str_l = coord_outputs.split(",")
            lat, lon = float(lat_str_l), float(lon_str_l)
            marker = dl.Marker(position=[lat, lon],
                            children=[dl.Popup(coord_outputs)],
                            id='city-mark')
            viewport = {'center': [lat, lon], 'zoom': 14}
            
            return (
                False, dash.no_update, video_ver,
                row['Source'].values[0],
                row['Links'].values[0],
                row['Coordinates'].values[0],
                hh_st, mm_st, ss_st,
                hh_end, mm_end, ss_end,
                row['Time of the day'].values[0],
                row['Weather'].values[0],
                row['Video quality'].values[0],
                row['Camera tilt'].values[0],
                row['Distance from building'].values[0],
                row['Occluded'].values[0],
                row['Terrain'].values[0],
                row['Logos and text'].values[0],
                row['Distortions'].values[0],
                row['Analyst'].values[0],
                row['Comments'].values[0] if row['Comments'].values[0] else "",
                row['Links'].values[0],False,False,value_check,dash.no_update,dash.no_update,viewport,[marker]
            )
      
        return (False, dash.no_update,"Select a video id", "","","",0,0,0,0,0,0,"","","","","","","","","","","","",
                False,False,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update)
    
    elif triggered_id == 'update.n_clicks':   
        return (False, dash.no_update,stored_videoid) + (dash.no_update,) * 21 + (True,False,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update)

    elif triggered_id =='confirm-yes.n_clicks' :
        try:
            general_validations_update = general_validations (analyst_edit,city_name_edit,distance_edit,occlusion_edit,
            terrain_edit,logos_edit,duration_edit, tod_edit,weather_edit,vq_edit,tilt_edit)
            
            valid_url_update = is_valid_url(linkedit)                
            valid_coordinates_update = valid_coords(coord_edit)
            valid_duration_update = valid_dur(duration_edit)

            if not checkbox_ed:     
                start_time_edit = f"{minute_st_edit}:{sec_st_edit:02}"
                end_time_edit = f"{min_end_edit}:{sec_end_edit:02}" 
                dur_time =  re.sub(r"^00:0?(\d):", r"\1:", duration_edit)
            else:
                start_time_edit =f"0:00"
                end_time_edit=f"0:00"
                dur_time= duration_edit

            df_city_edit['base'] = df_city_edit['Cut_ID'].str.extract(r'^(.*)_v\d+$')[0]
            other_rows = df_city_edit[df_city_edit['base'] != video_cut]

            # Check if the new URL and Coordinates pair exists elsewhere
            duplicate_match = other_rows[
                (other_rows['Links'] == valid_url_update)]

            if not duplicate_match.empty:
                if valid_coordinates_update in duplicate_match['Coordinates'].values:
                    raise ValueError("Video link and Coordinates already exist in another entry!")
                
                video_name_edit = df_city_edit[
                    df_city_edit['Links'] == valid_url_update
                ]['Title'].values[0]
                duplicate_match = duplicate_match.copy()  # Safely modify

                time_to_check_ed = parse_time(start_time_edit)
                duplicate_match['Start Time Parsed'] = duplicate_match['Start Time'].apply(parse_time)
                duplicate_match['Finish Time Parsed'] = duplicate_match['Finish Time'].apply(parse_time)

                dur_dup = duplicate_match.apply(
                    lambda row: row['Start Time Parsed'] <= time_to_check_ed <= row['Finish Time Parsed'],
                    axis=1
                )

                full_video_cross = duplicate_match.apply(
                    lambda row: row['Duration'] == "Full Video" ,
                    axis=1
                )
                if dur_dup.any() or full_video_cross.any():
                    raise ValueError("There's already this video with another crossing timing, please select another duration!")
                
            else:                
                if valid_url_update not in df_city_edit['Links'].values:  
                    if 'youtube' in valid_url_update and 'Youtube' in sourceedit:
                        with yt_dlp.YoutubeDL() as ydl:
                            info_dict = ydl.extract_info(valid_url_update, download=False)
                            video_name_edit = info_dict.get('title', 'No title found')
                    elif 'tiktok' in valid_url_update and 'Tiktok' in sourceedit:
                        with yt_dlp.YoutubeDL() as ydl:
                            info_dict = ydl.extract_info(valid_url_update, download=False)
                            video_name_edit = info_dict.get('title', 'No title found')
                            
                    elif 'facebook' in valid_url_update and 'facebook' in sourceedit:
                        with yt_dlp.YoutubeDL() as ydl:
                            info_dict = ydl.extract_info(valid_url_update, download=False)
                            video_name_edit = info_dict.get('title', 'No title found')
                    else:
                        raise ValueError("Video title not found - maybe not a matching source?")  
                    
                video_name_edit = df_city_edit[
                    df_city_edit['Links'] == valid_url_update]['OG File Name'].values[0]
   
            video_og_dur = df_city_edit[
                    df_city_edit['Links'] == valid_url_update
                ]['Original Duration'].values[0]
            
            updated_rec_id = df_city_edit[
                    df_city_edit['Links'] == valid_url_update
                ]['record_id'].values[0]
            
            updated_country = df_city_edit[
                    df_city_edit['Links'] == valid_url_update
                ]['Country'].values[0] 
            
            time_d=(datetime.datetime.now())
            formatted_datetime = time_d.strftime("%Y-%m-%d %H:%M:%S")                 
            
            match = re.match(r'^(.*)_v\d+$', video_ver)

            if match:
                cleaned_cut = match.group(1)
            else:
                cleaned_cut = video_ver  # fallback if no match
                 
            df_city_edit['base'] = df_city_edit['Cut_ID'].str.extract(r'^(.*)_v\d+$')[0]
            filt_clean = df_city_edit[df_city_edit['base'] == cleaned_cut]
            new_v = filt_clean.shape[0] + 1
            new_cut_v = f"{cleaned_cut}_v{new_v}"

            
            selected_inputs =[video_ver,updated_rec_id,updated_country,city_val, valid_url_update,video_name_edit,
            video_og_dur,sourceedit,valid_coordinates_update,start_time_edit,end_time_edit,
            dur_time,analyst_edit,tod_edit,terrain_edit,weather_edit,vq_edit,tilt_edit,distance_edit,
            occlusion_edit,distortions_edit,logos_edit,comments_edit]
            
            cut_ver_df = df_city_edit[df_city_edit['Cut_ID'] == video_ver].copy()
            
            mask = cut_ver_df.apply(lambda row: all(val in row.values for val in selected_inputs), axis=1)
            if mask.iloc[0]:
                raise ValueError ("Please change values to proceed!")
            latest_index = int(df_city_edit['Index'].iloc[-1]) + 1
            values_update= [latest_index,new_cut_v,updated_rec_id,updated_country,city_val, valid_url_update,video_name_edit,
            valid_coordinates_update,analyst_edit,sourceedit,video_og_dur,start_time_edit,end_time_edit,
            dur_time,tod_edit,terrain_edit,weather_edit,vq_edit,tilt_edit,distance_edit,
            occlusion_edit,distortions_edit,logos_edit,comments_edit,formatted_datetime]  

            
            try:
                append_row_to_sql(values_update)

            except Exception as e:
                error_window_update = html.Div([
                html.H5("⚠️ Update Failed", style={"color": "red"}),
                html.P(f"Could not update the database: {e}", style={"color": "black"})
             ])
                
            
                # Return the error window and leave everything else unchanged
                return (
                    True,                      # keep the update dialog open
                    error_window_update,       # show our new error
                    stored_videoid,            # keep current selection
                    *([dash.no_update] * 21),  # no other fields change
                    False,False,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update                     # disable Confirm button
                )
            
            center= cities[cities['City Name'] == city_val]['CityCenter'].iloc[0]
            lat, lon =map(float, center.split(",")) 
            map_center_city = {'center': [lat, lon], 'zoom': 10} 
                            
            result_window_update = html.Div([
                html.H1('Video Updated Successfully!'),
                html.Br(),
                html.H3("Video Details: "),
                html.Ul([
                    html.Li(f"City: {city_name_edit}"),
                    html.Li(f"Cut ID: {new_cut_v}"),
                    html.Li(f"Video Link: {valid_url_update}"),
                    html.Li(f"Video Name: {video_name_edit}"),
                    html.Li(f"Video Source: {sourceedit}"),                    
                    html.Li(f"Coordinates: {valid_coordinates_update}"),
                    html.Li(f"Start Time: {start_time_edit}"),
                    html.Li(f"Start Time: {end_time_edit}"),                    
                    html.Li(f"Video Duration: {valid_duration_update}"),
                    html.Li(f"Analyst: {analyst_edit}"),
                    html.Li(f"Time of the day: {tod_edit}"),
                    html.Li(f"Weather: {weather_edit}"), 
                    html.Li(f"Video Quality: {vq_edit}"), 
                    html.Li(f"Camera Tilt: {tilt_edit}"),
                    html.Li(f"Distance from a building: {distance_edit}"),
                    html.Li(f"Occlusion: {occlusion_edit}"),                                         
                    html.Li(f"Terrain: {terrain_edit}"),
                    html.Li(f"Logos and Text: {logos_edit}"),
                    html.Li(f"Distortions: {distortions_edit}"),
                    html.Li(f"Comments: {comments_edit}")                                                                    
                ])
            ])
            
            checkbox_ed =[]  
            return (True,result_window_update,"Select a video id", "","","",0,0,0,0,0,0,"","","",
                    "","","","","","","","","",False,False,checkbox_ed,dash.no_update,dash.no_update,map_center_city,[])      
        except ValueError as e:
            # If any validation fails, catch and show the error message
            error_message = html.Div(
                [
                    html.H5("⚠️ Validation Error", style={"color": "red"}),
                    html.P(str(e), style={"color": "black"})
                ]
            )
            return(True, error_message,stored_videoid) + (dash.no_update,) * 21 + (False,False,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update)
    
    elif triggered_id == 'delete.n_clicks':
        if stored_videoid:
            return (False, dash.no_update,stored_videoid) + (dash.no_update,) * 21 + (False,True,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update)
        else:
            raise ValueError("No  selected to remove!")
        
    elif triggered_id == 'delete_btn.n_clicks':
        if delete_password == "delete":
            try:
                center= cities[cities['City Name'] == city_val]['CityCenter'].iloc[0]
                lat, lon =map(float, center.split(",")) 
                map_center_city = {'center': [lat, lon], 'zoom': 10} 
                remove_record_sql(video_ver)
            except Exception as e:
                # Build a Dash error window if the Sheets update fails
                error_window_update = html.Div([
                    html.H5("⚠️ Deletion Failed", style={"color": "red"}),
                    html.P(f"Could not update the sheet: {e}", style={"color": "black"})
                ])
                # Return the error window and leave everything else unchanged
                return (
                    True,                      # keep the update dialog open
                    error_window_update,       # show our new error
                    stored_videoid,            # keep current selection
                    *([dash.no_update] * 21),  # no other fields change
                    False,False,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update                     # disable Confirm button
                )
            
            result_removal = f"{video_ver} has successfully removed !"
            return (True,result_removal,"Select a video id", "","","",0,0,0,0,0,0,"","","","","","","","","","","","",
        False,False,dash.no_update,dash.no_update,dash.no_update,map_center_city,[])        
        else:
            result_removal = "Incorrect Password, please try again!"
            return (True,result_removal,stored_videoid) + (dash.no_update,) * 21 + (False,False,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update)        

    # No videoid selected, just update options
    return (False, dash.no_update,stored_videoid) + (dash.no_update,) * 21 + (False,False,dash.no_update,dash.no_update,dash.no_update,dash.no_update,dash.no_update)








 # Define the main layout with tabs
app.layout = html.Div(
    [
        dcc.Tabs(id='tabs', value='tab1', children=[
                dcc.Tab(
                    label='Geo-Tag Form',
                    children=insert_tab_layout(),
                    style=tab_style,
                    selected_style=selected_tab_style,
                    value='tab1'),
                dcc.Tab(
                    label='Geo-Tag Edit Mode',
                    children=edit_tab_layout(),
                    style=tab_style,
                    selected_style=selected_tab_style,
                    value='tab2'),
                

            ],
        ),
    ]
)                 
             
if __name__ == "__main__":
    app.run(host='100.84.182.85', port=8050, debug=True)
