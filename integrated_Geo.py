import dash
import pandas as pd
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash.exceptions
import numpy as np

import plotly.express as px
import plotly.graph_objects as go
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import ast
import json
import re
from shapely.geometry import Point, Polygon


# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Geo-Location Hub"


# Path to your service account key file
SERVICE_ACCOUNT_FILE = r"C:\Users\roy\OneDrive\Desktop\ASR JSONS\Geo_Anlysis_Data\arabic-transcription-435113-c8120df00a35.json"

# Authenticate and connect to the Sheets API
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
)
service = build('sheets', 'v4', credentials=creds)
sheet = service.spreadsheets()

# Convert 'Duration' column from mm:ss to float (minutes)
def convert_to_minutes(duration):
    try:
        minutes, seconds = map(int, duration.split(':'))
        total_seconds = minutes * 60 + seconds
        return total_seconds  # Convert total seconds to minutes
    except (ValueError, AttributeError):
        return None  # handle rows where duration is NaN or invalid format
    
def calculate_duration(row):
    try:
        def parse_time(time_str):
            # Check if the time includes hours
            time_parts = list(map(int, time_str.split(':')))
            if len(time_parts) == 3:  # h:mm:ss
                h, m, s = time_parts
            elif len(time_parts) == 2:  # mm:ss
                h, m, s = 0, time_parts[0], time_parts[1]
            else:
                raise ValueError("Invalid time format")
            return h * 3600 + m * 60 + s
        
        # Parse Start Time
        start_seconds = parse_time(row['Start Time'])

        # Parse Finish Time
        finish_seconds = parse_time(row['Finish Time'])

        # Calculate Duration
        return finish_seconds - start_seconds
    except Exception as e:
        print(f"Error parsing row: {e}")
        return None

def build_general_insights_div(filtered_df):
    """Create the HTML div for the general insights, e.g., mode or average."""
    if len(filtered_df) == 0:
        return html.Div("No data available", style={'color': 'white'})

    most_common_source = (filtered_df['Source'].mode().iloc[0]
                          if 'Source' in filtered_df.columns 
                          and not filtered_df['Source'].dropna().mode().empty else None)
    most_common_tod = (filtered_df['Time of the day'].mode().iloc[0]
                       if 'Time of the day' in filtered_df.columns
                       and not filtered_df['Time of the day'].dropna().mode().empty else None)
    most_common_terrain = (filtered_df['Terrain'].mode().iloc[0]
                           if 'Terrain' in filtered_df.columns
                           and not filtered_df['Terrain'].dropna().mode().empty else None)
    most_common_tilt = (filtered_df['Camera tilt'].mode().iloc[0]
                        if 'Camera tilt' in filtered_df.columns 
                        and not filtered_df['Camera tilt'].dropna().mode().empty else None)
    avg_dur = round(filtered_df['Duration'].mean(), 2) if 'Duration' in filtered_df.columns else None
    
def apply_all_filters(
    df,
    duration_range,
    selected_terrain,
    selected_occluded,
    selected_VQ,
    selected_tilt,
    selected_distance,
    bar_clickData,
    pie_clickData,
    pie_weather_clickData,
    bar_2_clickData,
    polygon_filter_active
):
    # Apply the range filter
    if duration_range:
        df = df[
            (df['Duration'] >= duration_range[0]) &
            (df['Duration'] <= duration_range[1])
        ]
    # Then each dropdown
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

    # Now apply bar_clickData / pie_clickData filters
    if bar_clickData:
        clicked_source = bar_clickData['points'][0]['x']
        df = df[df['Source'] == clicked_source]

    if pie_clickData:
        clicked_time_of_day = pie_clickData['points'][0]['label']
        df = df[df['Time of the day'] == clicked_time_of_day]

    if pie_weather_clickData:
        clicked_weather = pie_weather_clickData['points'][0]['label']
        df = df[df['Weather'] == clicked_weather]

    if bar_2_clickData:
        clicked_logos = bar_2_clickData['points'][0]['x']
        df = df[df['Logos and text'] == clicked_logos]

    return df

def apply_all_filters2(
    df,
    duration_range,
    selected_terrain,
    selected_occluded,
    selected_VQ,
    selected_tilt,
    selected_distance,
    bar_weather_clickData,
    pie_clickData,
    pie_2_clickData,
    bar_2_clickData,
    milan_polygon_active

):
    # Apply the range filter
    if duration_range:
        df = df[
            (df['Duration'] >= duration_range[0]) &
            (df['Duration'] <= duration_range[1])
        ]
    # Then each dropdown
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

def apply_all_filters3(
    df,
    duration_range,
    selected_terrain,
    selected_occluded,
    selected_VQ,
    selected_tilt,
    selected_distance,
    bar_weather_clickData,
    pie_clickData,
    pie_2_clickData,
    bar_2_clickData,
    budapest_polygon_active

):
    # Apply the range filter
    if duration_range:
        df = df[
            (df['Duration'] >= duration_range[0]) &
            (df['Duration'] <= duration_range[1])
        ]
    # Then each dropdown
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
                        id=f"madrid-mark-{i}"
                    )
                )
            except ValueError:
                pass  # skip invalid coords
    return markers

    
# Common styles
container_style = {
    "background-color": "black",
    "border-radius": "50px",
    "padding": "15px",
    "box-shadow": "0px 8px 20px rgba(0, 0, 0, 0.3)",
    "width": "100%",
    "max-width": "1600px",
    "margin": "0 auto",
}

background_style = {
    "background-size": "cover",
    "background-color": 'black',
    "background-position": "center",
    "height": "200vh",
    "padding": "10px",
}

button_style = {
    "width": "70%",
    "height": "60px",
    "margin": "30px",
    "background-color": 'red',
    "border": "2px solid white",
    "display": "block",
    "font-weight": "bold",
    "color": "black",
}

button_style1 = {
    "width": "20%",
    "height": "60px",
    "margin": "30px",
    "background-color": 'orange',
    "border": "2px solid white",
    "display": "block",
    "font-weight": "bold",
    "color": "black",
}

button_style15 = {
    "width": "80%",
    "height": "60px",
    "margin": "30px",
    "background-color": 'green',
    "border": "2px solid white",
    "display": "block",
    "font-weight": "bold",
    "color": "white",   
}

button_polygon = {
    "width": "15%",
    "height": "60px",
    "margin": "-50px 0px 0px 850px",
    "background-color": 'blue',
    "border": "2px solid white",
    "display": "block",
    "font-weight": "bold",
    "color": "white",       
}

font_style = {
    "color": "white",
    "size": "25px",
    'font-weight': 'bold'
}

tab_style = {
'background-color': 'black',
'color':'rgb(255,51,153)',
'font-size': '24px',


    
}

selected_tab_style = {
    'background-color': 'gray',  # Change this to your desired background color
    'color': 'rgb(255,51,153)',            # Change this to your desired text color
    'font-size': '24px',
    'padding': '10px',
    'font-weight': 'bold'
}

def generate_general_insights(
    most_common_tilt,most_common_tod,most_common_terrain,avg_dur):
    return html.Div(
        [
            html.H2(
                "General Insights",
                className='mb-3',
                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
            ),
            html.Ul(
                [
                    html.Li(
                        f"They were mostly shot in {most_common_tilt} tilt, "
                        f"in {most_common_tod} and in {most_common_terrain} terrain.",
                        style={
                            'fontSize': '18px',
                            'marginBottom': '10px',
                            'fontWeight': 'bold',
                            'textAlign': 'justify',
                            'color': 'white'
                        }
                    ),
                    html.Li(
                        f"The average video duration is {avg_dur} seconds.",
                        style={
                            'fontSize': '18px',
                            'marginBottom': '10px',
                            'fontWeight': 'bold',
                            'textAlign': 'justify',
                            'color': 'white'
                        }
                    ),
                ],
                style={'padding': '10px', 'marginLeft': '10px'}
            ),
        ],
        style={'padding': '10px'}
    )

# ---------------------------- London Tab Data and Layout ----------------------------



def load_london_data():
    # Google Sheet ID and Range for London
    SHEET_ID_LONDON = '14hSdXXSL_ehJO3tdogLQcVahqIuDy6UREUEv7LusVU8'
    RANGE_LONDON = 'London!A1:W860'

    # Access the Google Sheet for London
    result = sheet.values().get(spreadsheetId=SHEET_ID_LONDON, range=RANGE_LONDON).execute()
    values = result.get('values', [])

    # Convert the data to a pandas DataFrame
    if values:
        headers = values[0]  # Assuming the first row is the header
        data = values[1:]    # Rest is the data
        df_london = pd.DataFrame(data, columns=headers)
    else:
        print("No data found for London.")
        df_london = pd.DataFrame()

    return df_london
global df_london
df_london = load_london_data()

# Process London Data
first_column_name_london = df_london.columns[0]
df_london[first_column_name_london] = df_london[first_column_name_london].apply(
    lambda x: f"[{x}]({x})" if pd.notnull(x) else x
)

# Define unique values for dropdowns
unique_sources_london = df_london['Source'].dropna().unique()
unique_tod_london = df_london['Time of the day'].dropna().unique()
unique_occluded_london = df_london['Occluded'].dropna().unique()
unique_category_london = df_london['Category'].dropna().unique()
unique_terrain_london = df_london['Terrain'].dropna().unique()
unique_tilt_london = df_london['Camera tilt'].dropna().unique()
unique_distance_london = df_london['Distance from building'].dropna().unique()

most_common_source_london = df_london['Source'].mode().iloc[0] if not df_london['Source'].dropna().mode().empty else None
most_common_tod_london = df_london['Time of the day'].mode().iloc[0] if not df_london['Time of the day'].dropna().mode().empty else None
most_common_occluded_london = df_london['Occluded'].mode().iloc[0] if not df_london['Occluded'].dropna().mode().empty else None
most_common_category_london = df_london['Category'].mode().iloc[0] if not df_london['Category'].dropna().mode().empty else None
most_common_terrain_london = df_london['Terrain'].mode().iloc[0] if not df_london['Terrain'].dropna().mode().empty else None
most_common_tilt_london = df_london['Camera tilt'].mode().iloc[0] if not df_london['Camera tilt'].dropna().mode().empty else None
most_common_distance_london = df_london['Distance from building'].mode().iloc[0] if not df_london['Distance from building'].dropna().mode().empty else None

# Convert 'Duration' column
df_london['Duration'] = df_london['Finish Time'].apply(convert_to_minutes) - df_london['Start Time'].apply(convert_to_minutes)
df_london['Duration'] = df_london['Duration']


avg_dur_london = round(df_london['Duration'].mean(), 2)
min_dur_london = df_london['Duration'].min()
max_dur_london = df_london['Duration'].max()

# Color maps for London
color_map_london = {
    'Youtube': 'rgb(255, 0, 0)',       # Red
    'Telegram': 'rgb(36, 161, 222)',   # Blue
    'Tik Tok': 'rgb(1, 1, 1)',         # Black
}

color_map2_london = {
    'Night Time': 'rgb(1, 1, 1)',      # Black
    'Day Time': 'rgb(236, 255, 0)',
    '???': 'rgb(255,250,250)',
    "Unidentified": 'rgb(169,169,169)'
}

def generate_interactive_bar_plot_london(df_london):
    source_counts = df_london['Source'].value_counts().reset_index()
    source_counts.columns = ['Source', 'Count']

    fig = px.bar(
        source_counts, 
        x='Source', 
        y='Count', 
        color='Source', 
        color_discrete_map=color_map_london,
        title='Source Type'
    )
    fig.update_traces(marker_line_width=1.5, hovertemplate="Count: %{y}")
    fig.update_layout(
        xaxis_title="Source",
        yaxis_title="Count",
        showlegend=False,
        paper_bgcolor='black',  # Set the background outside the plot area to black
        plot_bgcolor='black',   # Set the background inside the plot area to black
        font=dict(size=16, color='white')  # Update font color for better visibility
    )
    fig.update_layout(hovermode="x unified")

    return fig


def generate_interactive_pie_chart_london(df_london):
    tod_counts = df_london['Time of the day'].value_counts().reset_index()
    tod_counts.columns = ['Time of the day', 'Count']
    
    fig = px.pie(
        tod_counts,
        names='Time of the day',
        values='Count',
        color='Time of the day',
        color_discrete_map=color_map2_london,
        title='Time of the day'
    )
    
    depth_values = [0.05 + i * 0.01 for i in range(len(tod_counts))]
    fig.update_traces(
        marker=dict(line=dict(color='white', width=1.5)),
        pull=depth_values,
        textinfo='label'
    )
    fig.update_layout(
        showlegend=False,
        hovermode="x unified",
        margin=dict(t=40, b=20, l=0, r=0),
        font=dict(size=16, color='white'),  # Update font color for better visibility
        paper_bgcolor='black',  # Set the background outside the plot area to black
        plot_bgcolor='black'    # Set the background inside the plot area to black
    )

    return fig


# Update dropdown options to include an "All" option
unique_occluded_london_1 = ['All'] + list(unique_occluded_london)
unique_category_london_1 = ['All'] + list(unique_category_london)
unique_terrain_london_1 = ['All'] + list(unique_terrain_london)
unique_tilt_london_1 = ['All'] + list(unique_tilt_london)
unique_distance_london_1 = ['All'] + list(unique_distance_london)

df_london = df_london[df_london['Coordinates'].str.contains(',', na=False)]
df_london[['Latitude', 'Longitude']] = df_london['Coordinates'].str.split(',', expand=True)
df_london['Latitude'] = df_london['Latitude'].astype(float)
df_london['Longitude'] = df_london['Longitude'].astype(float)

# Create Map Markers
markers_london = []
for i, (coord, coord) in enumerate(zip(df_london['Coordinates'], df_london['Coordinates'])):
    try:
        # Remove extra whitespace and split the coordinate string
        lat, lon = map(float, coord.strip().split(','))
        # Add valid markers
        markers_london.append(dl.Marker(position=(lat, lon), children=[dl.Popup(coord)], id="london-mark" + str(i)))
    except (ValueError, AttributeError):
        # Skip invalid coordinates such as "not found" or malformed entries
        continue
global london_polygon
global polygon_london
     
file_path = "london_coordinates.txt"

# Read and extract coordinates
london_polygon = []
with open(file_path, "r") as file:
    for line in file:
        match = re.findall(r"[-+]?\d*\.\d+", line)  # Extract floating point numbers
        if match:
            london_polygon.append([float(match[0]), float(match[1])]) 

polygon_london = Polygon(london_polygon)
count_within_london = sum(
    polygon_london.contains(Point(row['Latitude'], row['Longitude']))
    for _, row in df_london.iterrows()
    if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
)

pre_out_london = round(((len(df_london)-count_within_london)/len(df_london) *100),2)

def general_insights_london (df_london_r):
    # General Insights Section
    
    df_in = df_london_r
    most_common_source_l =  df_in['Source'].mode().iloc[0] if not  df_in['Source'].dropna().mode().empty else None
    avg_dur_l = round( df_in['Duration'].mean(), 2)   
    most_common_terrain_l =  df_in['Terrain'].mode().iloc[0] if not  df_in['Terrain'].dropna().mode().empty else None
    most_common_tilt_l =  df_in['Camera tilt'].mode().iloc[0] if not  df_in['Camera tilt'].dropna().mode().empty else None
    general_insights_london =    html.Div(
        [
            html.H2(
                "General Insights",
                className='mb-3',
                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
            ),
            html.Ul(
                [
                    html.Li(
                        f"The majority of the videos are from {most_common_source_l}.",
                        style={
                            'fontSize': '18px',
                            'marginBottom': '10px',
                            'fontWeight': 'bold',
                            'textAlign': 'justify',
                            'color': 'white'
                        }
                    ),
                    html.Li(
                        f"They were mostly shot in {most_common_tilt_l} tilt, in "
                        f"{most_common_tod_london} and in {most_common_terrain_l} terrain.",
                        style={
                            'fontSize': '18px',
                            'marginBottom': '10px',
                            'fontWeight': 'bold',
                            'textAlign': 'justify',
                            'color': 'white'
                        }
                    ),
                    html.Li(
                        f"The average video duration is {avg_dur_l} seconds.",
                        style={
                            'fontSize': '18px',
                            'marginBottom': '10px',
                            'fontWeight': 'bold',
                            'textAlign': 'justify',
                            'color': 'white'
                        }
                    )
                ],
                style={
                    'padding': '10px',
                    'marginLeft': '10px'
                }
            ),
        ],
        style={'padding': '10px'}
    ),
    return general_insights_london

def tab1_layout():
    return html.Div(
        style=background_style,
        children=[
            dcc.Store (id="London_data",data=df_london.to_dict('records')),
            dcc.ConfirmDialog(
                id='london-confirm-dialog',
                message="The data has refreshed successfully!"
            ),
                html.Img(
                    src="/assets/airis.png", 
                    alt="Example Image", 
                    style={
                        "width": "200px", 
                        "position": "absolute",  # Absolute positioning
                        "top": "80px",          # Distance from the top of the page
                        "left": "10px",         # Distance from the left of the page
                        "zIndex": "1000"        # Ensures it stays above other elements
                    }
                ), 
            dbc.Container(
                style=container_style,
                children=[
                html.H1(
                        "Airis-Labs: Geo-Location Analysis - London",
                        className='mb-4',
                        style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}
                    ),
                    html.Div(id='london-countdown', style={'color':'white','fontSize':'18px','marginBottom':'20px'}),
                    # Map and Filters Section
                    dbc.Row([
                        # Map on the left
                        dbc.Col(
                            dl.Map(
                                [
                                    dl.TileLayer(),
                                    dl.LayerGroup(id="london-map-layer", children=markers_london),
                                    dl.LayerGroup(
                                        id="polygon-layer_london",
                                        children=[
                                            dl.Polygon(
                                                positions=london_polygon,
                                                color="blue",
                                                fillColor="cyan",
                                                fillOpacity=0.6,
                                            )
                                        ]
                                    ),
                                ],
                                center=(51.5074, -0.1278),
                                zoom=10,
                                style={"width": "100%", "height": "500px", "margin": "6px"}
                            ),
                            width=8
                        ),
                        # Filters on the right
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H4(
                                            "Filters",
                                            className='mb-3',
                                            style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                                        ),
                                        dbc.Label("Terrain Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='london-Terrain',
                                            options=[{'label': k, 'value': k} for k in unique_terrain_london_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Camera Tilt Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='london-Camera_Tilt',
                                            options=[{'label': k, 'value': k} for k in unique_tilt_london_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Occlusion Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='london-Occlusion',
                                            options=[{'label': k, 'value': k} for k in unique_occluded_london_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Category Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='london-Category',
                                            options=[{'label': k, 'value': k} for k in unique_category_london_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Distance Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='london-Distance_Building',
                                            options=[{'label': k, 'value': k} for k in unique_distance_london_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Reset Filters",
                                                        id='london-reset-btn',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style
                                                    ),
                                                    width="auto"
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Update DB",
                                                        id='london-update',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style15
                                                    ),
                                                    width="auto"
                                                )
                                            ],
                                        ),
                                    ],
                                    style={"marginBottom": "30px"}
                                ),
                            ],
                            width=4
                        ),
                    ]),
                    # Duration Slider Section (below the map)
                    html.Br(),
                    html.H4(
                        "Filter by Video Duration (seconds):",
                        className='mb-1',
                        style={'textAlign': 'left', 'color': 'rgb(255,51,153)', 'marginBottom': '0'}
                    ),
                    dbc.Row(
                        dbc.Col(
                            dcc.RangeSlider(
                                id='london-duration-slider',
                                min=min_dur_london,
                                max=max_dur_london,
                                step=0.1,
                                value=[min_dur_london, max_dur_london],
                                marks={int(min_dur_london): str(int(min_dur_london)), int(max_dur_london): str(int(max_dur_london))},
                                tooltip={"always_visible": True, "placement": "bottom"}
                            ),
                            width=8
                        ),
                        justify="left"
                    ),
                    html.H1(
                        id='london-record-count',
                        style={'textAlign': 'left', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    dbc.Button("Show Which Ones",id='polygon_dropouts_london', color='primary',n_clicks=0,style=button_polygon),
                    html.Br(),
                    # Graphs Section
                    html.Div(
                        [
                            html.H4(
                                "Graphical Analysis",
                                className='mb-3',
                                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                            ),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Graph(id='london-bar-plot', figure=generate_interactive_bar_plot_london(df_london)),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Graph(id='london-pie-chart', figure=generate_interactive_pie_chart_london(df_london)),
                                    width=6
                                ),
                            ]),
                        ],
                        style={'marginTop': '20px'}
                    ),
                    # General Insights Section
                    html.Div(
                        id='london-general-insights',
                        children=[
                            html.H2(
                                "General Insights",
                                className='mb-3',
                                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        f"The majority of the videos are from {most_common_source_london}.",
                                        style={
                                            'fontSize': '18px',
                                            'marginBottom': '10px',
                                            'fontWeight': 'bold',
                                            'textAlign': 'justify',
                                            'color': 'white'
                                        }
                                    ),
                                    html.Li(
                                        f"They were mostly shot in {most_common_tilt_london} tilt, in "
                                        f"{most_common_tod_london} and in {most_common_terrain_london} terrain.",
                                        style={
                                            'fontSize': '18px',
                                            'marginBottom': '10px',
                                            'fontWeight': 'bold',
                                            'textAlign': 'justify',
                                            'color': 'white'
                                        }
                                    ),
                                    html.Li(
                                        f"The average video duration is {avg_dur_london} seconds.",
                                        style={
                                            'fontSize': '18px',
                                            'marginBottom': '10px',
                                            'fontWeight': 'bold',
                                            'textAlign': 'justify',
                                            'color': 'white'
                                        }
                                    )
                                ],
                                style={
                                    'padding': '10px',
                                    'marginLeft': '10px'
                                }
                            ),
                        ],
                        style={'padding': '10px'}
                    ),
                    # Full Details Section
                    html.Div(
                        [
                            html.H1("Full Details:", className='mb-4', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}),
                            html.Hr(),
                            dash_table.DataTable(
                                id='london-table',
                                columns=[
                                    {"name": first_column_name_london, "id": first_column_name_london, "presentation": "markdown"}
                                ] + [{"name": i, "id": i} for i in df_london.columns[1:]],
                                data=df_london.to_dict('records'),
                                row_selectable="single",  # Use "multi" for multiple row selection
                                selected_rows=[],                                       
                                sort_action="native",
                                filter_action="native",
                                fixed_rows={'headers': True}, 
                                style_table={'maxHeight': '500px',
                                            'overflowX': 'auto',
                                             'overflowY': 'auto'},
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
                                style_data_conditional=[
                                    {
                                        'if': {'column_id': 'Status'},
                                        'backgroundColor': 'rgb(220, 220, 220)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Active"'},
                                        'backgroundColor': 'rgb(85, 255, 85)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Inactive"'},
                                        'backgroundColor': 'rgb(255, 85, 85)',
                                        'color': 'white'
                                    },
                                ],
                            ),
                        ]
                    ),
                ]
            )
        ]
    )

# ---------------------------- London Callback ----------------------------

import dash
from dash.dependencies import Input, Output
import dash_leaflet as dl
import plotly.graph_objects as go  # for empty figures if needed

@app.callback(
    [
        Output('london-table', 'data'),
        Output('london-map-layer', 'children'),
        Output('london-Terrain', 'value'),
        Output('london-Occlusion', 'value'),
        Output('london-Category', 'value'),
        Output('london-Camera_Tilt', 'value'),
        Output('london-Distance_Building', 'value'),
        Output('london-record-count', 'children'),
        Output('london-duration-slider', 'min'),
        Output('london-duration-slider', 'max'),
        Output('london-duration-slider', 'value'),
        Output('london-confirm-dialog', 'displayed'),
        Output('london-general-insights', 'children'),
        Output('london-bar-plot', 'figure'),
        Output('london-pie-chart', 'figure'),
        Output('london-bar-plot', 'clickData'),    
        Output('london-pie-chart', 'clickData') 
    ],
    [
        Input('london-bar-plot', 'clickData'),
        Input('london-pie-chart', 'clickData'),
        Input('london-reset-btn', 'n_clicks'),
        Input('london-update', 'n_clicks'),
        Input('london-duration-slider', 'value'),
        Input('london-Terrain', 'value'),
        Input('london-Occlusion', 'value'),
        Input('london-Category', 'value'),
        Input('london-Camera_Tilt', 'value'),
        Input('london-Distance_Building', 'value'),
        Input('polygon_dropouts_london','n_clicks')
    ],
    State("London_data","data")
)
def handle_table_and_refresh_london(
    bar_clickData, pie_clickData, reset_clicks, update_clicks, duration_range,
    selected_terrain, selected_occluded, selected_category, selected_tilt,
    selected_distance,polygon_filter_london, current_data
):

    ctx = dash.callback_context
    triggered = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    try: 
        global df_london    
        # On interval update, reload the data (if needed)  
        if triggered == 'london-update' and update_clicks > 0:
            df_london = load_london_data()
            df_london['Duration'] = df_london['Finish Time'].apply(convert_to_minutes) - df_london['Start Time'].apply(convert_to_minutes)
            min_dur_london = df_london['Duration'].min()
            max_dur_london = df_london['Duration'].max()
            gen_in = general_insights_london(df_london)
            updated_bar_plotl = generate_interactive_bar_plot_london(df_london)
            updated_pie_chartl = generate_interactive_pie_chart_london(df_london)
                    # Recreate markers
            markers_london = []
            for i, (coord, coord) in enumerate(zip(df_london['Coordinates'], df_london['Coordinates'])):
                try:
                    # Remove extra whitespace and split the coordinate string
                    lat, lon = map(float, coord.strip().split(','))
                    # Add valid markers
                    markers_london.append(dl.Marker(position=(lat, lon), children=[dl.Popup(coord)], id="london-mark" + str(i)))
                except (ValueError, AttributeError):
                    # Skip invalid coordinates such as "not found" or malformed entries
                    continue
                
                count_within_london = sum(
                    polygon_london.contains(Point(row['Latitude'], row['Longitude']))
                    for _, row in df_london.iterrows()
                    if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
                )

                pre_out_london = round(((len(df_london)-count_within_london)/len(df_london) *100),2)  
                              
            return (
                df_london.to_dict('records'),    # data
                markers_london,                  # children
                'All',                           # Terrain.value
                'All',                           # Occlusion.value
                'All',                           # Category.value
                'All',                           # Camera_Tilt.value
                'All',                           # Distance_Building.value
                f"Total Records: {len(df_london)}, {pre_out_london} % out of Polygon", # record-count.children
                min_dur_london,                  # duration-slider.min
                max_dur_london,                  # duration-slider.max
                [min_dur_london, max_dur_london],# duration-slider.value
                False,                            # confirm-dialog.displayed (boolean)
                gen_in,
                updated_bar_plotl,               # bar-plot.figure
                updated_pie_chartl,               
                None,
                None
            )
            
        elif triggered == 'polygon_dropouts_london.n_clicks':
            filtered_polygon = df_london.copy()
            filtered_polygon['Duration'] = filtered_polygon['Finish Time'].apply(convert_to_minutes) - filtered_polygon['Start Time'].apply(convert_to_minutes)
            min_dur_london = filtered_polygon['Duration'].min()
            max_dur_london = filtered_polygon['Duration'].max()
            filtered_polygon = filtered_polygon[
                (filtered_polygon['Duration'] >= duration_range[0]) &
                (filtered_polygon['Duration'] <= duration_range[1])
            ]            
            filtered_polygon = filtered_polygon[filtered_polygon['Coordinates'].str.contains(',', na=False)]
            filtered_polygon[['Latitude', 'Longitude']] = filtered_polygon['Coordinates'].str.split(',', expand=True)
            filtered_polygon['Latitude'] = filtered_polygon['Latitude'].astype(float)
            filtered_polygon['Longitude'] = filtered_polygon['Longitude'].astype(float)
            
            filtered_polygon = filtered_polygon[
                ~filtered_polygon.apply(lambda row: polygon_london.contains(Point(row['Latitude'], row['Longitude'])), axis=1)
            ]

            gen_in = general_insights_london(filtered_polygon)
            updated_bar_plotl = generate_interactive_bar_plot_london(filtered_polygon)
            updated_pie_chartl = generate_interactive_pie_chart_london(filtered_polygon)
            
            markers_london = []
            for i, (coord, coord) in enumerate(zip(filtered_polygon['Coordinates'], filtered_polygon['Coordinates'])):
                try:
                    # Remove extra whitespace and split the coordinate string
                    lat, lon = map(float, coord.strip().split(','))
                    # Add valid markers
                    markers_london.append(dl.Marker(position=(lat, lon), children=[dl.Popup(coord)], id="london-mark" + str(i)))
                except (ValueError, AttributeError):
                    # Skip invalid coordinates such as "not found" or malformed entries
                    continue
                
            count_within_london = sum(
                polygon_london.contains(Point(row['Latitude'], row['Longitude']))
                for _, row in filtered_polygon.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            )

            pre_out_london = round(((len(filtered_polygon)-count_within_london)/len(filtered_polygon) *100),2)               
            record_count_text = f"Total Records: {len(filtered_polygon)}, 100% out of Polygon" 
       
            return (
                filtered_polygon.to_dict('records'),
                markers_london,
                selected_terrain,
                selected_occluded,
                selected_category,
                selected_tilt,
                selected_distance,
                record_count_text,
                min_dur_london,
                max_dur_london,
                duration_range,
                False,              # confirm-dialog.displayed
                gen_in,
                updated_bar_plotl,  # bar figure
                updated_pie_chartl,
                bar_clickData,
                pie_clickData
        )       
        # Handle Reset button
        elif triggered == 'london-reset-btn.n_clicks':
            # Reset filters
            filtered_df = df_london.copy()  # filtered_df reset as well
            filtered_df['Duration'] = filtered_df['Finish Time'].apply(convert_to_minutes) - filtered_df['Start Time'].apply(convert_to_minutes)
            filtered_df = filtered_df[
                (filtered_df['Duration'] >= duration_range[0]) &
                (filtered_df['Duration'] <= duration_range[1])
            ]
            min_dur_london = filtered_df['Duration'].min()
            max_dur_london = filtered_df['Duration'].max()
            gen_in = general_insights_london(filtered_df)
            updated_bar_plotl = generate_interactive_bar_plot_london(filtered_df)
            updated_pie_chartl = generate_interactive_pie_chart_london(filtered_df)

            markers_london = []
            for i, (coord, coord) in enumerate(zip(df_london['Coordinates'], df_london['Coordinates'])):
                try:
                    # Remove extra whitespace and split the coordinate string
                    lat, lon = map(float, coord.strip().split(','))
                    # Add valid markers
                    markers_london.append(dl.Marker(position=(lat, lon), children=[dl.Popup(coord)], id="london-mark" + str(i)))
                except (ValueError, AttributeError):
                    # Skip invalid coordinates such as "not found" or malformed entries
                    continue
                
            count_within_london = sum(
                polygon_london.contains(Point(row['Latitude'], row['Longitude']))
                for _, row in df_london.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            )

            pre_out_london = round(((len(df_london)-count_within_london)/len(df_london) *100),2)  
   
            return (
                filtered_df.to_dict('records'),
                markers_london,
                'All', 'All', 'All', 'All', 'All',
                f"Total Records: {len(df_london)}, {pre_out_london} % out of Polygon",
                min_dur_london,
                max_dur_london,
                [min_dur_london, max_dur_london],
                False,               # confirm-dialog.displayed (boolean)
                gen_in,
                updated_bar_plotl,   # bar figure
                updated_pie_chartl,
                None,
                None
            )

        else:
            df_london['Duration'] = df_london['Finish Time'].apply(convert_to_minutes) - df_london['Start Time'].apply(convert_to_minutes)
            df_london['Duration'] = df_london['Duration']
            min_dur_london = df_london['Duration'].min()
            max_dur_london = df_london['Duration'].max()
            
        
            gen_in = general_insights_london(df_london)

            filtered_df = pd.DataFrame(current_data)

            # Apply Duration Filter
            filtered_df = filtered_df[
                (filtered_df['Duration'] >= duration_range[0]) &
                (filtered_df['Duration'] <= duration_range[1])
            ]

            # Apply Source Filter from Bar Plot
            if bar_clickData:
                clicked_source = bar_clickData['points'][0]['x']
                filtered_df = filtered_df[filtered_df['Source'] == clicked_source]

            # Apply Time of Day Filter from Pie Chart
            if pie_clickData:
                clicked_time_of_day = pie_clickData['points'][0]['label']
                filtered_df = filtered_df[filtered_df['Time of the day'] == clicked_time_of_day]

            # Apply Dropdown Filters
            if selected_terrain != 'All':
                filtered_df = filtered_df[filtered_df['Terrain'] == selected_terrain]
            if selected_occluded != 'All':
                filtered_df = filtered_df[filtered_df['Occluded'] == selected_occluded]
            if selected_category != 'All':
                filtered_df = filtered_df[filtered_df['Category'] == selected_category]
            if selected_tilt != 'All':
                filtered_df = filtered_df[filtered_df['Camera tilt'] == selected_tilt]
            if selected_distance != 'All':
                filtered_df = filtered_df[filtered_df['Distance from building'] == selected_distance]

            # Convert Coordinates to string for Dash DataTable
            filtered_df['Coordinates'] = filtered_df['Coordinates'].apply(lambda x: str(x))

            # Count the records after filtering
            

            # Create Map Markers
        
            gen_in = general_insights_london(filtered_df)
            # Generate updated figures after filtering
            updated_bar_plotl = generate_interactive_bar_plot_london(filtered_df)
            updated_pie_chartl = generate_interactive_pie_chart_london(filtered_df)
            
            markers_london = []
            for i, (coord, coord) in enumerate(zip(filtered_df['Coordinates'], filtered_df['Coordinates'])):
                try:
                    # Remove extra whitespace and split the coordinate string
                    lat, lon = map(float, coord.strip().split(','))
                    # Add valid markers
                    markers_london.append(dl.Marker(position=(lat, lon), children=[dl.Popup(coord)], id="london-mark" + str(i)))
                except (ValueError, AttributeError):
                    # Skip invalid coordinates such as "not found" or malformed entries
                    continue
                     
            count_within_london = sum(
                polygon_london.contains(Point(row['Latitude'], row['Longitude']))
                for _, row in filtered_df.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            )

            pre_out_london = round(((len(filtered_df)-count_within_london)/len(filtered_df) *100),2)  
            
            record_count_text = f"Total Records: {len(filtered_df)}, {pre_out_london} % out of Polygon"

            return (
                filtered_df.to_dict('records'),
                markers_london,
                selected_terrain,
                selected_occluded,
                selected_category,
                selected_tilt,
                selected_distance,
                record_count_text,
                min_dur_london,
                max_dur_london,
                duration_range,
                False,              # confirm-dialog.displayed
                gen_in,
                updated_bar_plotl,  # bar figure
                updated_pie_chartl,
                bar_clickData,
                pie_clickData
        )

    except Exception as e:
        print(f"Error: {e}")
        raise dash.exceptions.PreventUpdate
    


# ---------------------------- Rome Tab Data and Layout ----------------------------

def load_rome_data():
    # Google Sheet ID and Range for Rome
    SHEET_ID_ROME = '14hSdXXSL_ehJO3tdogLQcVahqIuDy6UREUEv7LusVU8'
    RANGE_ROME = 'Rome!A1:W400'

    # Access the Google Sheet for Rome
    result = sheet.values().get(spreadsheetId=SHEET_ID_ROME, range=RANGE_ROME).execute()
    values = result.get('values', [])

    # Convert the data to a pandas DataFrame
    if values:
        headers = values[0]  # Assuming the first row is the header
        data = values[1:]    # Rest is the data
        df_rome = pd.DataFrame(data, columns=headers)
    else:
        print("No data found for Rome.")
        df_rome = pd.DataFrame()

    return df_rome
global df_rome
df_rome = load_rome_data()

# Process Rome Data
first_column_name_rome = df_rome.columns[0]
df_rome[first_column_name_rome] = df_rome[first_column_name_rome].apply(
    lambda x: f"[{x}]({x})" if pd.notnull(x) else x
)

# Define unique values for dropdowns
unique_sources_rome = df_rome['Source'].dropna().unique()
unique_tod_rome = df_rome['Time of the day'].dropna().unique()
unique_occluded_rome = df_rome['Occluded'].dropna().unique()
unique_weather_rome = df_rome['Weather'].dropna().unique()
unique_terrain_rome = df_rome['Terrain'].dropna().unique()
unique_tilt_rome = df_rome['Camera tilt'].dropna().unique()
unique_distance_rome = df_rome['Distance from building'].dropna().unique()
unique_vq_rome = df_rome['Video quality'].dropna().unique()

most_common_source_rome = df_rome['Source'].mode().iloc[0] if not df_rome['Source'].dropna().mode().empty else None
most_common_tod_rome = df_rome['Time of the day'].mode().iloc[0] if not df_rome['Time of the day'].dropna().mode().empty else None
most_common_terrain_rome = df_rome['Terrain'].mode().iloc[0] if not df_rome['Terrain'].dropna().mode().empty else None
most_common_tilt_rome = df_rome['Camera tilt'].mode().iloc[0] if not df_rome['Camera tilt'].dropna().mode().empty else None

df_rome['Duration'] = df_rome['Finish Time'].apply(convert_to_minutes) - df_rome['Start Time'].apply(convert_to_minutes)
# Convert 'Duration' column
df_rome['Duration'] = df_rome['Duration']
avg_dur_rome = round(df_rome['Duration'].mean(), 2)
min_dur_rome = df_rome['Duration'].min()
max_dur_rome = df_rome['Duration'].max()

# Color maps for Rome
color_map_rome = {
    'Youtube': 'rgb(255, 0, 0)',       # Red
    'Facebook': 'rgb(36, 161, 222)',   # Blue
    'Tik Tok': 'rgb(1, 1, 1)',         # Black
    'Instegram': 'rgb(131, 58, 180)'
}

color_map2_rome = {
    'Night Time': 'rgb(1, 1, 1)',      # Black
    'Day Time': 'rgb(236, 255, 0)',
    '???': 'rgb(255,250,250)',
    "Unidentified": 'rgb(169,169,169)'
}

color_map3_rome = {
    'Clear': 'rgb(224,255,255)',
    'Snow': 'rgb(255,250,250)',
    'Rain': 'rgb(123,104,238)',
    'Fog or Smoke': 'rgb(128,128,128)'
}

background_style_rome = {
     "background-size": "cover",
    "background-position": "center",
    "height": "250vh",
    "padding": "10px",
    "background-color": 'black',
}

def generate_interactive_bar_plot_rome(df_rome):
    source_counts = df_rome['Source'].value_counts().reset_index()
    source_counts.columns = ['Source', 'Count']

    fig = px.bar(
        source_counts, 
        x='Source', 
        y='Count', 
        color='Source', 
        color_discrete_map=color_map_rome,
        title='Source Type'
    )
    fig.update_traces(marker_line_width=1.5, hovertemplate="Count: %{y}")
    fig.update_layout(
        xaxis_title="Source", 
        yaxis_title="Count", 
        showlegend=False,
        hovermode="x unified",
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white'),
        xaxis=dict(
            color='white',
            gridcolor='gray',
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white')
        ),
        yaxis=dict(
            color='white',
            gridcolor='gray',
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white')
        )
    )

    return fig

def generate_interactive_bar_plot_2_rome(df_rome):
    source_counts = df_rome['Logos and text'].value_counts().reset_index()
    source_counts.columns = ['Logos and text', 'Count']

    fig = px.bar(
        source_counts, 
        x='Logos and text', 
        y='Count', 
        color='Logos and text', 
        color_discrete_map=color_map_rome,
        title='Logos and text Distribution'
    )
    fig.update_traces(marker_line_width=1.5, hovertemplate="Count: %{y}")
    fig.update_layout(
        xaxis_title="Logos and text", 
        yaxis_title="Count", 
        showlegend=False,
        hovermode="x unified",
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white'),
        xaxis=dict(
            color='white',
            gridcolor='gray',
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white')
        ),
        yaxis=dict(
            color='white',
            gridcolor='gray',
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white')
        )
    )

    return fig

def generate_interactive_pie_chart_rome(df_rome):
    tod_counts = df_rome['Time of the day'].value_counts().reset_index()
    tod_counts.columns = ['Time of the day', 'Count']
    
    fig = px.pie(
        tod_counts,
        names='Time of the day',
        values='Count',
        color='Time of the day',
        color_discrete_map=color_map2_rome,
        title='Time of the day'
    )
    
    depth_values = [0.05 + i * 0.01 for i in range(len(tod_counts))]
    fig.update_traces(
        marker=dict(line=dict(color='#000000', width=2)),
        pull=depth_values,
        textinfo='label',
        textfont_color='white'
    )
    fig.update_layout(
        showlegend=False,
        hovermode="x unified",
        margin=dict(t=40, b=20, l=0, r=0),
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white')
    )

    return fig

def generate_interactive_pie_chart_2_rome(df_rome):
    weather_counts = df_rome['Weather'].value_counts().reset_index()
    weather_counts.columns = ['Weather', 'Count']
    
    fig = px.pie(
        weather_counts,
        names='Weather',
        values='Count',
        color='Weather',
        color_discrete_map=color_map3_rome,
        title='Weather'
    )
    
    depth_values = [0.05 + i * 0.01 for i in range(len(weather_counts))]
    fig.update_traces(
        marker=dict(line=dict(color='#000000', width=2)),
        pull=depth_values,
        textinfo='label',
        textfont_color='orange'
    )
    fig.update_layout(
        showlegend=False,
        hovermode="x unified",
        margin=dict(t=40, b=20, l=0, r=0),
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white')
    )

    return fig


# Update dropdown options to include an "All" option
unique_occluded_rome_1 = ['All'] + list(unique_occluded_rome)
unique_terrain_rome_1 = ['All'] + list(unique_terrain_rome)
unique_tilt_rome_1 = ['All'] + list(unique_tilt_rome)
unique_distance_rome_1 = ['All'] + list(unique_distance_rome)
unique_vq_rome_1 = ['All'] + list(unique_vq_rome)

df_rome = df_rome[df_rome['Coordinates'].str.contains(',', na=False)]
df_rome[['Latitude', 'Longitude']] = df_rome['Coordinates'].str.split(',', expand=True)
df_rome['Latitude'] = df_rome['Latitude'].astype(float)
df_rome['Longitude'] = df_rome['Longitude'].astype(float)
# Filter valid coordinates and handle invalid entries
markers_rome = []
for i, (coord, coord) in enumerate(zip(df_rome['Coordinates'], df_rome['Coordinates'])):
    try:
        # Remove extra whitespace and split the coordinate string
        lat, lon = map(float, coord.strip().split(','))
        # Add valid markers
        markers_rome.append(dl.Marker(position=(lat, lon), children=[dl.Popup(coord)], id="rome-mark" + str(i)))
    except (ValueError, AttributeError):
        # Skip invalid coordinates such as "not found" or malformed entries
        continue

global polygon_rome
global rome_polygon

rome_polygon =[ [ 42.058116945280013, 12.368100298177971 ], [ 42.072743816113771, 12.438249576666429 ], [ 42.049161718238928, 12.460339136701092 ], [ 42.039012460925704, 12.562428724969401 ],  
[ 41.976027364070113, 12.650786965108052 ], [ 41.925281077503996, 12.715264599803826 ], [ 41.852146723335181, 12.715861614939898 ], [ 41.785579535663153, 12.646010844019477 ],  
[ 41.757221316699734, 12.625115314256957 ], [ 41.755430271291516, 12.600637693678006 ], [ 41.762892960492415, 12.597055602861575 ], [ 41.786773565935299, 12.551085437384032 ],  
[ 41.763489975628488, 12.528100354645261 ], [ 41.764684005900634, 12.499145120545771 ], [ 41.754236241019377, 12.47466749996682 ], [ 41.757221316699734, 12.464518242653597 ],  
[ 41.767072066444925, 12.448398833979653 ], [ 41.771251172397427, 12.429592857193386 ], [ 41.81572880003479, 12.388995827940491 ], [ 41.865579563896794, 12.371085373858332 ],  
[ 41.879907927162527, 12.37795104792316 ], [ 41.921400479119526, 12.325413715948827 ], [ 42.045878134990538, 12.345115215439201 ], [ 42.058116945280013, 12.368100298177971 ]  ]

polygon_rome = Polygon(rome_polygon)
count_within_rome = sum(
    polygon_rome.contains(Point(row['Latitude'], row['Longitude']))
    for _, row in df_rome.iterrows()
    if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
)

pre_out_rome = round(((len(df_rome)-count_within_rome)/len(df_rome) *100),2)

def tab2_layout():
    return html.Div(
        style=background_style_rome,
        children=[
            dcc.Store(id='Rome_data',data=df_rome.to_dict('records')),           
            dcc.ConfirmDialog(
                id='rome-confirm-dialog',
                message="The data has refreshed successfully!"
            ),
                html.Img(
                    src="/assets/airis.png", 
                    alt="Example Image", 
                    style={
                        "width": "200px", 
                        "position": "absolute",  # Absolute positioning
                        "top": "80px",          # Distance from the top of the page
                        "left": "10px",         # Distance from the left of the page
                        "zIndex": "1000"        # Ensures it stays above other elements
                    }
                ), 
            dbc.Container(
                style=container_style,
                children=[
                    # Title
                    html.H1(
                        "Airis-Labs: Geo-Location Analysis - Rome",
                        className='mb-4',
                        style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}
                    ),
                    # Map and Filters Section
                    dbc.Row([
                        # Map on the left
                        dbc.Col(
                            dl.Map(
                                [
                                    dl.TileLayer(),
                                    dl.LayerGroup(id="rome-map-layer", children=markers_rome),
                                    dl.LayerGroup(
                                        id="polygon-layer_rome",
                                        children=[
                                            dl.Polygon(
                                                positions=rome_polygon,
                                                color="blue",
                                                fillColor="cyan",
                                                fillOpacity=0.6,
                                            )
                                        ]
                                    ),
                                ],
                                center=(41.9028, 12.4964),
                                zoom=10,
                                style={"width": "100%", "height": "500px", "margin": "6px"}
                            ),
                            width=8
                        ),
                        # Filters on the right
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H4(
                                            "Filters",
                                            className='mb-3',
                                            style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                                        ),
                                        dbc.Label("Terrain Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='rome-Terrain',
                                            options=[{'label': k, 'value': k} for k in unique_terrain_rome_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Camera Tilt Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='rome-Camera_Tilt',
                                            options=[{'label': k, 'value': k} for k in unique_tilt_rome_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Occlusion Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='rome-Occlusion',
                                            options=[{'label': k, 'value': k} for k in unique_occluded_rome_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Video Quality Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='rome-VQ',
                                            options=[{'label': k, 'value': k} for k in unique_vq_rome_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Distance Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='rome-Distance_Building',
                                            options=[{'label': k, 'value': k} for k in unique_distance_rome_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Reset Filters",
                                                        id='rome-reset-btn',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style
                                                    ),
                                                    width="auto"
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Update DB",
                                                        id='rome-update',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style15
                                                    ),
                                                    width="auto"
                                                )
                                            ],
                                        ),
                                    ],
                                    style={"marginBottom": "30px"}
                                ),
                            ],
                            width=4
                        ),
                    ]),
                    html.H1(
                        id='rome-record-count',
                        style={'textAlign': 'left', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    dbc.Button("Show Which Ones",id='polygon_dropouts_rome', color='primary',n_clicks=0,style=button_polygon),

                    # Duration Slider Section (below the map)
                    html.Br(),
                    html.H4(
                        "Filter by Video Duration (seconds):",
                        className='mb-1',
                        style={'textAlign': 'left', 'color': 'rgb(255,51,153)', 'marginBottom': '0'}
                    ),
                    dbc.Row(
                        dbc.Col(
                            dcc.RangeSlider(
                                id='rome-duration-slider',
                                min=min_dur_rome,
                                max=max_dur_rome,
                                step=0.1,
                                value=[min_dur_rome, max_dur_rome],
                                updatemode='mouseup',
                                marks={int(min_dur_rome): str(int(min_dur_rome)), int(max_dur_rome): str(int(max_dur_rome))},
                                tooltip={"always_visible": True, "placement": "bottom"}
                            ),
                            width=8
                        ),
                        justify="left"
                    ),
                    # Graphs Section
                    html.Div(
                        [
                            html.H4(
                                "Graphical Analysis",
                                className='mb-3',
                                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                            ),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Graph(id='rome-bar-plot', figure=generate_interactive_bar_plot_rome(df_rome)),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Graph(id='rome-pie-chart', figure=generate_interactive_pie_chart_rome(df_rome)),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Graph(id='rome-pie-chart-weather', figure=generate_interactive_pie_chart_2_rome(df_rome)),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                                dbc.Col(
                                    dcc.Graph(id='rome-bar-plot-logos', figure=generate_interactive_bar_plot_2_rome(df_rome)),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                            ]),
                        ],
                        style={'marginTop': '20px'}
                    ),
                    # General Insights Section
                    html.Div(
                        id='rome-general-insights',
                        children=[
                            html.H2(
                                "General Insights",
                                className='mb-3',
                                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        f"The majority of the videos are from {most_common_source_rome}.",
                                        style={
                                            'fontSize': '18px',
                                            'marginBottom': '10px',
                                            'fontWeight': 'bold',
                                            'textAlign': 'justify',
                                            'color': 'white'
                                        }
                                    ),
                                    html.Li(
                                        f"They were mostly shot in {most_common_tilt_rome} tilt, in "
                                        f"{most_common_tod_rome} and in {most_common_terrain_rome} terrain.",
                                        style={
                                            'fontSize': '18px',
                                            'marginBottom': '10px',
                                            'fontWeight': 'bold',
                                            'textAlign': 'justify',
                                            'color': 'white'
                                        }
                                    ),
                                    html.Li(
                                        f"The average video duration is {avg_dur_rome} seconds.",
                                        style={
                                            'fontSize': '18px',
                                            'marginBottom': '10px',
                                            'fontWeight': 'bold',
                                            'textAlign': 'justify',
                                            'color': 'white'
                                        }
                                    )
                                ],
                                style={
                                    'padding': '10px',
                                    'marginLeft': '10px'
                                }
                            ),
                        ],
                        style={'padding': '10px'}
                    ),
                    # Full Details Section
                    html.Div(
                        [
                            html.H1("Full Details:", className='mb-4', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}),
                            html.Hr(),
                            dash_table.DataTable(
                                id='rome-table',
                                columns=[
                                    {"name": first_column_name_rome, "id": first_column_name_rome, "presentation": "markdown"}
                                ] + [{"name": i, "id": i} for i in df_rome.columns[1:]],
                                data=df_rome.to_dict('records'),
                                sort_action="native",
                                filter_action="native",
                                fixed_rows={'headers': True},
                                style_table={'maxHeight': '500px',
                                            'overflowX': 'auto',
                                             'overflowY': 'auto'},
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
                                style_data_conditional=[
                                    {
                                        'if': {'column_id': 'Status'},
                                        'backgroundColor': 'rgb(220, 220, 220)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Active"'},
                                        'backgroundColor': 'rgb(85, 255, 85)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Inactive"'},
                                        'backgroundColor': 'rgb(255, 85, 85)',
                                        'color': 'white'
                                    },
                                ],
                            ),
                        ]
                    ),
                ]
            )
        ]
    )

# ---------------------------- Rome Callback ----------------------------

@app.callback(
    [
        Output('rome-table', 'data'),
        Output('rome-map-layer', 'children'),
        Output('rome-Terrain', 'value'),
        Output('rome-Occlusion', 'value'),
        Output('rome-VQ', 'value'),
        Output('rome-Camera_Tilt', 'value'),
        Output('rome-Distance_Building', 'value'),
        Output('rome-record-count', 'children'),
        Output('rome-duration-slider', 'min'),
        Output('rome-duration-slider', 'max'),
        Output('rome-duration-slider', 'value'),
        Output('rome-bar-plot', 'figure'),
        Output('rome-pie-chart', 'figure'),
        Output('rome-pie-chart-weather', 'figure'),
        Output('rome-bar-plot-logos','figure'),
        Output('rome-confirm-dialog', 'displayed'),
        Output('rome-general-insights', 'children'),
        Output('rome-bar-plot', 'clickData'),
        Output('rome-pie-chart', 'clickData'),
        Output('rome-pie-chart-weather', 'clickData'),
        Output('rome-bar-plot-logos','clickData'),
    ],
    [
        Input('rome-bar-plot', 'clickData'),
        Input('rome-pie-chart', 'clickData'),
        Input('rome-pie-chart-weather', 'clickData'),
        Input('rome-bar-plot-logos','clickData'),
        Input('rome-reset-btn', 'n_clicks'),
        Input('rome-update', 'n_clicks'),
        Input('rome-duration-slider', 'value'),
        Input('rome-Terrain', 'value'),
        Input('rome-Occlusion', 'value'),
        Input('rome-VQ', 'value'),
        Input('rome-Camera_Tilt', 'value'),
        Input('rome-Distance_Building', 'value'),
        Input('polygon_dropouts_rome','n_clicks')
    ],
    State("Rome_data","data")
)
def handle_table_and_refresh_rome(
    bar_clickData, pie_clickData, pie_weather_clickData, bar_2_clickData, reset_clicks,update_clicks, duration_range,
    selected_terrain, selected_occluded, selected_VQ, selected_tilt, selected_distance,filter_polygon_rome,current_data
):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    
    try:
        global df_rome, min_dur_rome, max_dur_rome
        df_handle = df_rome.copy()
        # If the interval triggered the callback, reload the data
        if triggered_id == 'rome-update.n_clicks' and update_clicks > 0:
            df_updated = load_rome_data()
            df_updated['Duration'] = df_updated['Finish Time'].apply(convert_to_minutes) - df_updated['Start Time'].apply(convert_to_minutes)
            min_dur_rome = df_updated['Duration'].min()
            max_dur_rome = df_updated['Duration'].max()

            # Recalculate general insights
            most_common_source_rome = df_updated['Source'].mode().iloc[0] if not df_updated['Source'].dropna().mode().empty else None
            most_common_tod_rome = df_updated['Time of the day'].mode().iloc[0] if not df_updated['Time of the day'].dropna().mode().empty else None
            most_common_terrain_rome = df_updated['Terrain'].mode().iloc[0] if not df_updated['Terrain'].dropna().mode().empty else None
            most_common_tilt_rome = df_updated['Camera tilt'].mode().iloc[0] if not df_updated['Camera tilt'].dropna().mode().empty else None
            avg_dur_rome = round(df_updated['Duration'].mean(), 2)

            # Create updated general insights
            general_insights = html.Div(
                children=[
                    html.H2(
                        "General Insights",
                        className='mb-3',
                        style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                    ),
                    html.Ul(
                        [
                            html.Li(
                                f"The majority of the videos are from {most_common_source_rome}.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"They were mostly shot in {most_common_tilt_rome} tilt, in "
                                f"{most_common_tod_rome} and in {most_common_terrain_rome} terrain.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"The average video duration is {avg_dur_rome} seconds.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            )
                        ],
                        style={'padding': '10px', 'marginLeft': '10px'}
                    ),
                ],
                style={'padding': '10px'}
            )

            df_updated = df_updated[df_updated['Coordinates'].str.contains(',', na=False)]
            df_updated[['Latitude', 'Longitude']] = df_updated['Coordinates'].str.split(',', expand=True)
            df_updated['Latitude'] = df_updated['Latitude'].astype(float)
            df_updated['Longitude'] = df_updated['Longitude'].astype(float)
            if 'Coordinates' in df_updated.columns and 'Coordinates' in df_updated.columns:
                markers_rome = []
                for i, (coord, coord) in enumerate(zip(df_updated['Coordinates'], df_updated['Coordinates'])):
                    try:
                        # Remove extra whitespace and split the coordinate string
                        lat, lon = map(float, coord.strip().split(','))
                        # Add valid markers
                        markers_rome.append(dl.Marker(position=(lat, lon), children=[dl.Popup(coord)], id="rome-mark" + str(i)))
                    except (ValueError, AttributeError):
                        # Skip invalid coordinates such as "not found" or malformed entries
                        continue
            else:
                markers_rome = []
            count_within_rome = sum(
                polygon_rome.contains(Point(row['Latitude'], row['Longitude']))
                for _, row in df_updated.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            )

            pre_out_rome = round(((len(df_updated)-count_within_rome)/len(df_updated) *100),2)
                        # Count the records after filtering
            record_count_text = f"Total Records: {len(df_updated)}, {pre_out_rome} % out of Polygon"

                
            # Refresh the graphs
            updated_bar_plot = generate_interactive_bar_plot_rome(df_updated)
            updated_pie_chart = generate_interactive_pie_chart_rome(df_updated)
            updated_pie_chart_weather = generate_interactive_pie_chart_2_rome(df_updated)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_rome(df_updated)

            # Return the refreshed data
            return (
                df_updated.to_dict('records'),
                markers_rome,
                'All', 'All', 'All', 'All', 'All',
                record_count_text,
                min_dur_rome,
                max_dur_rome,
                [min_dur_rome, max_dur_rome],
                updated_bar_plot,
                updated_pie_chart,
                updated_pie_chart_weather,
                updated_bar_plot_logos,
                True,  # Show confirmation dialog
                general_insights,
                None,
                None,
                None,
                None
            )
        elif triggered_id == 'polygon_dropouts_rome.n_clicks':
            filtered_polygon = df_handle.copy()
            filtered_polygon['Duration'] = filtered_polygon['Finish Time'].apply(convert_to_minutes) - filtered_polygon['Start Time'].apply(convert_to_minutes)
            min_dur_rome = filtered_polygon['Duration'].min()
            max_dur_rome = filtered_polygon['Duration'].max() 
            filtered_polygon = filtered_polygon[
                (filtered_polygon['Duration'] >= duration_range[0]) &
                (filtered_polygon['Duration'] <= duration_range[1])
            ]            
            filtered_polygon = filtered_polygon[filtered_polygon['Coordinates'].str.contains(',', na=False)]
            filtered_polygon[['Latitude', 'Longitude']] = filtered_polygon['Coordinates'].str.split(',', expand=True)
            filtered_polygon['Latitude'] = filtered_polygon['Latitude'].astype(float)
            filtered_polygon['Longitude'] = filtered_polygon['Longitude'].astype(float)
            
            filtered_polygon = filtered_polygon[
                ~filtered_polygon.apply(lambda row: polygon_rome.contains(Point(row['Latitude'], row['Longitude'])), axis=1)
            ]

            if 'Coordinates' in filtered_polygon.columns and 'Coordinates' in filtered_polygon.columns:
                markers_rome = []
                for i, (coord, coord) in enumerate(zip(filtered_polygon['Coordinates'], filtered_polygon['Coordinates'])):
                    try:
                        # Remove extra whitespace and split the coordinate string
                        lat, lon = map(float, coord.strip().split(','))
                        # Add valid markers
                        markers_rome.append(dl.Marker(position=(lat, lon), children=[dl.Popup(coord)], id="rome-mark" + str(i)))
                    except (ValueError, AttributeError):
                        # Skip invalid coordinates such as "not found" or malformed entries
                        continue
            else:
                markers_rome = []
                
            count_within_rome = sum(
                polygon_rome.contains(Point(row['Latitude'], row['Longitude']))
                for _, row in df_rome.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            )
            
            record_count_text = f"Total Records: {len(filtered_polygon)}, 100% out of Polygon"
            updated_bar_plot = generate_interactive_bar_plot_rome(filtered_polygon)
            updated_pie_chart = generate_interactive_pie_chart_rome(filtered_polygon)
            updated_pie_chart_weather = generate_interactive_pie_chart_2_rome(filtered_polygon)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_rome(filtered_polygon)

            # Recalculate general insights
            most_common_source_rome = filtered_polygon['Source'].mode().iloc[0] if not filtered_polygon['Source'].dropna().mode().empty else None
            most_common_tod_rome = filtered_polygon['Time of the day'].mode().iloc[0] if not filtered_polygon['Time of the day'].dropna().mode().empty else None
            most_common_terrain_rome = filtered_polygon['Terrain'].mode().iloc[0] if not filtered_polygon['Terrain'].dropna().mode().empty else None
            most_common_tilt_rome = filtered_polygon['Camera tilt'].mode().iloc[0] if not filtered_polygon['Camera tilt'].dropna().mode().empty else None
            avg_dur_rome = round(filtered_polygon['Duration'].mean(), 2)

            # Create updated general insights
            general_insights = html.Div(
                children=[
                    html.H2(
                        "General Insights",
                        className='mb-3',
                        style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                    ),
                    html.Ul(
                        [
                            html.Li(
                                f"The majority of the videos are from {most_common_source_rome}.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"They were mostly shot in {most_common_tilt_rome} tilt, in "
                                f"{most_common_tod_rome} and in {most_common_terrain_rome} terrain.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"The average video duration is {avg_dur_rome} seconds.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            )
                        ],
                        style={'padding': '10px', 'marginLeft': '10px'}
                    ),
                ],
                style={'padding': '10px'}
            )

            return (filtered_polygon.to_dict('records'),
                markers_rome,
                selected_terrain,
                selected_occluded,
                selected_VQ,
                selected_tilt,
                selected_distance,
                record_count_text,
                min_dur_rome,
                max_dur_rome,
                duration_range,
                updated_bar_plot,
                updated_pie_chart,
                updated_pie_chart_weather,
                updated_bar_plot_logos,
                False,  # Don't show confirmation dialog
                general_insights,
                bar_clickData,
                pie_clickData,
                pie_weather_clickData,
                bar_2_clickData)        
                                               
        elif triggered_id == 'rome-reset-btn.n_clicks':
            df_handle = df_handle[df_handle['Coordinates'].str.contains(',', na=False)]
            df_handle[['Latitude', 'Longitude']] = df_handle['Coordinates'].str.split(',', expand=True)
            df_handle['Latitude'] = df_handle['Latitude'].astype(float)
            df_handle['Longitude'] = df_handle['Longitude'].astype(float)
            if 'Coordinates' in df_handle.columns and 'Coordinates' in df_handle.columns:
                markers_rome = []
                for i, (coord, coord) in enumerate(zip(df_handle['Coordinates'], df_handle['Coordinates'])):
                    try:
                        # Remove extra whitespace and split the coordinate string
                        lat, lon = map(float, coord.strip().split(','))
                        # Add valid markers
                        markers_rome.append(dl.Marker(position=(lat, lon), children=[dl.Popup(coord)], id="rome-mark" + str(i)))
                    except (ValueError, AttributeError):
                        # Skip invalid coordinates such as "not found" or malformed entries
                        continue
            else:
                markers_rome = []
            count_within_rome = sum(
                polygon_rome.contains(Point(row['Latitude'], row['Longitude']))
                for _, row in df_handle.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            )

            pre_out_rome = round(((len(df_handle)-count_within_rome)/len(df_handle) *100),2)
                        # Count the records after filtering
            record_count_text = f"Total Records: {len(df_handle)}, {pre_out_rome} % out of Polygon"
            df_handle['Duration'] = df_handle['Finish Time'].apply(convert_to_minutes) - df_handle['Start Time'].apply(convert_to_minutes)    
            df_handle = df_handle[
                (df_handle['Duration'] >= duration_range[0]) &
                (df_handle['Duration'] <= duration_range[1])
            ]
            # Reset graphs to their initial state
            updated_bar_plot = generate_interactive_bar_plot_rome(df_handle)
            updated_pie_chart = generate_interactive_pie_chart_rome(df_handle)
            updated_pie_chart_weather = generate_interactive_pie_chart_2_rome(df_handle)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_rome(df_handle)

            # Recalculate general insights
            most_common_source_rome = df_handle['Source'].mode().iloc[0] if not df_handle['Source'].dropna().mode().empty else None
            most_common_tod_rome = df_handle['Time of the day'].mode().iloc[0] if not df_handle['Time of the day'].dropna().mode().empty else None
            most_common_terrain_rome = df_handle['Terrain'].mode().iloc[0] if not df_handle['Terrain'].dropna().mode().empty else None
            most_common_tilt_rome = df_handle['Camera tilt'].mode().iloc[0] if not df_handle['Camera tilt'].dropna().mode().empty else None
            avg_dur_rome = round(df_handle['Duration'].mean(), 2)

            # Create updated general insights
            general_insights = html.Div(
                children=[
                    html.H2(
                        "General Insights",
                        className='mb-3',
                        style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                    ),
                    html.Ul(
                        [
                            html.Li(
                                f"The majority of the videos are from {most_common_source_rome}.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"They were mostly shot in {most_common_tilt_rome} tilt, in "
                                f"{most_common_tod_rome} and in {most_common_terrain_rome} terrain.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"The average video duration is {avg_dur_rome} seconds.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            )
                        ],
                        style={'padding': '10px', 'marginLeft': '10px'}
                    ),
                ],
                style={'padding': '10px'}
            )

            return (
                df_handle.to_dict('records'),
                markers_rome,
                'All', 'All', 'All', 'All', 'All',
                record_count_text,
                min_dur_rome,
                max_dur_rome,
                [min_dur_rome, max_dur_rome],
                updated_bar_plot,
                updated_pie_chart,
                updated_pie_chart_weather,
                updated_bar_plot_logos,
                False,  # Don't show confirmation dialog
                general_insights,
                None,
                None,
                None,
                None
            )
        else:
            # Default filtering logic (apply dropdowns, charts, etc.)
            filtered_df = pd.DataFrame(current_data)
            filtered_df['Duration'] = filtered_df['Finish Time'].apply(convert_to_minutes) - filtered_df['Start Time'].apply(convert_to_minutes)
            # Apply filters from duration range and dropdowns
            filtered_df = filtered_df[
                (filtered_df['Duration'] >= duration_range[0]) &
                (filtered_df['Duration'] <= duration_range[1])
            ]
            if selected_terrain != 'All':
                filtered_df = filtered_df[filtered_df['Terrain'] == selected_terrain]
            if selected_occluded != 'All':
                filtered_df = filtered_df[filtered_df['Occluded'] == selected_occluded]
            if selected_VQ != 'All':
                filtered_df = filtered_df[filtered_df['Video quality'] == selected_VQ]
            if selected_tilt != 'All':
                filtered_df = filtered_df[filtered_df['Camera tilt'] == selected_tilt]
            if selected_distance != 'All':
                filtered_df = filtered_df[filtered_df['Distance from building'] == selected_distance]

            # Apply click data filters
            if bar_clickData:
                clicked_source = bar_clickData['points'][0]['x']
                filtered_df = filtered_df[filtered_df['Source'] == clicked_source]
            if pie_clickData:
                clicked_time_of_day = pie_clickData['points'][0]['label']
                filtered_df = filtered_df[filtered_df['Time of the day'] == clicked_time_of_day]
            if pie_weather_clickData:
                clicked_weather = pie_weather_clickData['points'][0]['label']
                filtered_df = filtered_df[filtered_df['Weather'] == clicked_weather]
            if bar_2_clickData:
                clicked_source_2 = bar_2_clickData['points'][0]['x']
                filtered_df = filtered_df[filtered_df['Logos and text'] == clicked_source_2]
                
            # Create filtered map markers
            
            filtered_df = filtered_df[filtered_df['Coordinates'].str.contains(',', na=False)]
            filtered_df[['Latitude', 'Longitude']] = filtered_df['Coordinates'].str.split(',', expand=True)
            filtered_df['Latitude'] = filtered_df['Latitude'].astype(float)
            filtered_df['Longitude'] = filtered_df['Longitude'].astype(float)



            if 'Coordinates' in filtered_df.columns and 'Coordinates' in filtered_df.columns:
                markers_rome = []
                for i, (coord, coord) in enumerate(zip(filtered_df['Coordinates'], filtered_df['Coordinates'])):
                    try:
                        # Remove extra whitespace and split the coordinate string
                        lat, lon = map(float, coord.strip().split(','))
                        markers_rome.append(dl.Marker(position=(lat, lon), children=[dl.Popup(coord)], id="rome-mark" + str(i)))
                    except (ValueError, AttributeError):
                        # Skip invalid coordinates such as "not found" or malformed entries
                        continue
            else:
                markers_rome = []
                
            count_within_rome = sum(
                polygon_rome.contains(Point(row['Latitude'], row['Longitude']))
                for _, row in filtered_df.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            )

            pre_out_rome = round(((len(filtered_df)-count_within_rome)/len(filtered_df) *100),2)
                        # Count the records after filtering
            record_count_text = f"Total Records: {len(filtered_df)}, {pre_out_rome} % out of Polygon"

            # Refresh graphs for filtered data
            updated_bar_plot = generate_interactive_bar_plot_rome(filtered_df)
            updated_pie_chart = generate_interactive_pie_chart_rome(filtered_df)
            updated_pie_chart_weather = generate_interactive_pie_chart_2_rome(filtered_df)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_rome(filtered_df)

            # Recalculate general insights
            most_common_source_rome = filtered_df['Source'].mode().iloc[0] if not filtered_df['Source'].dropna().mode().empty else None
            most_common_tod_rome = filtered_df['Time of the day'].mode().iloc[0] if not filtered_df['Time of the day'].dropna().mode().empty else None
            most_common_terrain_rome = filtered_df['Terrain'].mode().iloc[0] if not filtered_df['Terrain'].dropna().mode().empty else None
            most_common_tilt_rome = filtered_df['Camera tilt'].mode().iloc[0] if not filtered_df['Camera tilt'].dropna().mode().empty else None
            avg_dur_rome = round(filtered_df['Duration'].mean(), 2)

            # Create updated general insights
            general_insights = html.Div(
                children=[
                    html.H2(
                        "General Insights",
                        className='mb-3',
                        style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                    ),
                    html.Ul(
                        [
                            html.Li(
                                f"The majority of the videos are from {most_common_source_rome}.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"They were mostly shot in {most_common_tilt_rome} tilt, in "
                                f"{most_common_tod_rome} and in {most_common_terrain_rome} terrain.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"The average video duration is {avg_dur_rome} seconds.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            )
                        ],
                        style={'padding': '10px', 'marginLeft': '10px'}
                    ),
                ],
                style={'padding': '10px'}
            )

            return (
                filtered_df.to_dict('records'),
                markers_rome,
                selected_terrain,
                selected_occluded,
                selected_VQ,
                selected_tilt,
                selected_distance,
                record_count_text,
                min_dur_rome,
                max_dur_rome,
                duration_range,
                updated_bar_plot,
                updated_pie_chart,
                updated_pie_chart_weather,
                updated_bar_plot_logos,
                False,  # Don't show confirmation dialog
                general_insights,
                bar_clickData,
                pie_clickData,
                pie_weather_clickData,
                bar_2_clickData
            )

    except Exception as e:
        print(f"Error: {e}")
        raise dash.exceptions.PreventUpdate

# ---------------------------- App Layout ----------------------------

# Define the main layout with tabs

# ------------------------------- Tab 3 - Madrid----------------------------------
# Make sure to define these styles/variables if they are used

def load_madrid_data():
    # Google Sheet ID and Range for Madrid
    SHEET_ID_MADRID = '14hSdXXSL_ehJO3tdogLQcVahqIuDy6UREUEv7LusVU8'
    RANGE_MADRID = 'Madrid!A1:Y660'

    # Access the Google Sheet for Madrid
    result = sheet.values().get(spreadsheetId=SHEET_ID_MADRID, range=RANGE_MADRID).execute()
    values = result.get('values', [])

    # Convert the data to a pandas DataFrame
    if values:
        headers = values[0]  # Assuming the first row is the header
        data = values[1:]    # Rest is the data
        df_madrid = pd.DataFrame(data, columns=headers)
    else:
        print("No data found for Madrid.")
        df_madrid = pd.DataFrame()

    return df_madrid

df_madrid = load_madrid_data()

# Process Madrid Data
first_column_name_madrid = df_madrid.columns[0]
df_madrid[first_column_name_madrid] = df_madrid[first_column_name_madrid].apply(
    lambda x: f"[{x}]({x})" if pd.notnull(x) else x
)

    
unique_sources_madrid = df_madrid['Source'].dropna().unique()
unique_tod_madrid = df_madrid['Time of the day'].dropna().unique()
unique_weather_madrid = df_madrid['Weather'].dropna().unique()
unique_terrain_madrid = df_madrid['Terrain'].dropna().unique()
unique_occluded_madrid = df_madrid['Occluded'].dropna().unique()
unique_tilt_madrid = df_madrid['Camera tilt'].dropna().unique()
unique_distance_madrid = df_madrid['Distance from building'].dropna().unique()
unique_vq_madrid = df_madrid['Video quality'].dropna().unique()

most_common_source_madrid = df_madrid['Source'].mode().iloc[0] if not df_madrid['Source'].dropna().mode().empty else None
most_common_tod_madrid = df_madrid['Time of the day'].mode().iloc[0] if not df_madrid['Time of the day'].dropna().mode().empty else None
most_common_terrain_madrid = df_madrid['Terrain'].mode().iloc[0] if not df_madrid['Terrain'].dropna().mode().empty else None
most_common_tilt_madrid = df_madrid['Camera tilt'].mode().iloc[0] if not df_madrid['Camera tilt'].dropna().mode().empty else None
df_madrid['Duration'] = df_madrid['Finish Time'].apply(convert_to_minutes) - df_madrid['Start Time'].apply(convert_to_minutes)

avg_dur_madrid = round(df_madrid['Duration'].mean(), 2)
min_dur_madrid = df_madrid['Duration'].min()
max_dur_madrid = df_madrid['Duration'].max()

# Color maps for Madrid
color_map_madrid = {
    'Youtube': 'rgb(255, 0, 0)',       # Red
    'Facebook': 'rgb(36, 161, 222)',   # Blue
    'Tik Tok': 'rgb(1, 1, 1)',         # Black
    'Instegram': 'rgb(131, 58, 180)'
}

color_map2_madrid = {
    'Night Time': 'rgb(1, 1, 1)',      # Black
    'Day Time': 'rgb(236, 255, 0)',
    '???': 'rgb(255,250,250)',
    "Unidentified": 'rgb(169,169,169)'
}

color_map3_madrid = {
    'Clear': 'rgb(224,255,255)',
    'Snow': 'rgb(255,250,250)',
    'Rain': 'rgb(123,104,238)',
    'Fog or Smoke': 'rgb(128,128,128)'
}

background_style_madrid = {
     "background-size": "cover",
    "background-position": "center",
    "height": "250vh",
    "padding": "10px",
    "background-color": 'black',
}

def generate_interactive_bar_plot_madrid(df_madrid):
    source_counts = df_madrid['Source'].value_counts().reset_index()
    source_counts.columns = ['Source', 'Count']

    fig = px.bar(
        source_counts, 
        x='Source', 
        y='Count', 
        color='Source', 
        color_discrete_map=color_map_madrid,
        title='Source Type'
    )
    fig.update_traces(marker_line_width=1.5, hovertemplate="Count: %{y}")
    fig.update_layout(
        xaxis_title="Source", 
        yaxis_title="Count", 
        showlegend=False,
        hovermode="x unified",
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white'),
        xaxis=dict(
            color='white',
            gridcolor='gray',
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white')
        ),
        yaxis=dict(
            color='white',
            gridcolor='gray',
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white')
        )
    )

    return fig

def generate_interactive_bar_plot_2_madrid(df_madrid):
    source_counts = df_madrid['Logos and text'].value_counts().reset_index()
    source_counts.columns = ['Logos and text', 'Count']

    fig = px.bar(
        source_counts, 
        x='Logos and text', 
        y='Count', 
        color='Logos and text', 
        color_discrete_map=color_map_madrid,
        title='Logos and text Distribution'
    )
    fig.update_traces(marker_line_width=1.5, hovertemplate="Count: %{y}")
    fig.update_layout(
        xaxis_title="Logos and text", 
        yaxis_title="Count", 
        showlegend=False,
        hovermode="x unified",
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white'),
        xaxis=dict(
            color='white',
            gridcolor='gray',
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white')
        ),
        yaxis=dict(
            color='white',
            gridcolor='gray',
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white')
        )
    )

    return fig

def generate_interactive_pie_chart_madrid(df_madrid):
    tod_counts = df_madrid['Time of the day'].value_counts().reset_index()
    tod_counts.columns = ['Time of the day', 'Count']
    
    fig = px.pie(
        tod_counts,
        names='Time of the day',
        values='Count',
        color='Time of the day',
        color_discrete_map=color_map2_madrid,
        title='Time of the day'
    )
    
    depth_values = [0.05 + i * 0.01 for i in range(len(tod_counts))]
    fig.update_traces(
        marker=dict(line=dict(color='#000000', width=2)),
        pull=depth_values,
        textinfo='label',
        textfont_color='white'
    )
    fig.update_layout(
        showlegend=False,
        hovermode="x unified",
        margin=dict(t=40, b=20, l=0, r=0),
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white')
    )

    return fig

def generate_interactive_pie_chart_2_madrid(df_madrid):
    weather_counts = df_madrid['Weather'].value_counts().reset_index()
    weather_counts.columns = ['Weather', 'Count']
    
    fig = px.pie(
        weather_counts,
        names='Weather',
        values='Count',
        color='Weather',
        color_discrete_map=color_map3_madrid,
        title='Weather'
    )
    
    depth_values = [0.05 + i * 0.01 for i in range(len(weather_counts))]
    fig.update_traces(
        marker=dict(line=dict(color='#000000', width=2)),
        pull=depth_values,
        textinfo='label',
        textfont_color='orange'
    )
    fig.update_layout(
        showlegend=False,
        hovermode="x unified",
        margin=dict(t=40, b=20, l=0, r=0),
        font=dict(size=16, color='white'),
        plot_bgcolor='black',
        paper_bgcolor='black',
        title_font=dict(color='white')
    )

    return fig


# Update dropdown options to include an "All" option
unique_occluded_madrid_1 = ['All'] + list(unique_occluded_madrid)
unique_terrain_madrid_1 = ['All'] + list(unique_terrain_madrid)
unique_tilt_madrid_1 = ['All'] + list(unique_tilt_madrid)
unique_distance_madrid_1 = ['All'] + list(unique_distance_madrid)
unique_vq_madrid_1 = ['All'] + list(unique_vq_madrid)

# Create Map Markers
markers_madrid = [
    dl.Marker(
        position=(float(lat), float(lon)), 
        children=[dl.Popup(coord)], 
        id="madrid-mark" + str(i)
    )
    for i, coord in enumerate(df_madrid['Coordinates'])
    if ',' in coord and 'not found' not in coord.lower()  # Ensure coord is valid and not 'not found'
    for lat, lon in [coord.split(',')]  # Safely split latitude and longitude
]


df_madrid = df_madrid[df_madrid['Coordinates'].str.contains(',', na=False)]
df_madrid[['Latitude', 'Longitude']] = df_madrid['Coordinates'].str.split(',', expand=True)
df_madrid['Latitude'] = df_madrid['Latitude'].astype(float)
df_madrid['Longitude'] = df_madrid['Longitude'].astype(float)

global madrid_polygon
global polygon_madrid

madrid_polygon = [  [40.57087558603525, -3.713015305051728], [40.571094724761224, -3.706441143272527], [40.572409557117062, -3.60826699403645], 
  [40.536251667331456, -3.578025849852123], [40.536251667331456, -3.55260575763921], [40.500312916271817, -3.552386618913237], 
  [40.470071772087493, -3.520392364921123], [40.445747373504446, -3.512941648238027], [40.426463165618785, -3.49628710506405], 
  [40.413753119512329, -3.500231602131571], [40.406740680281182, -3.52083064237307], [40.390743553285127, -3.529596191412005],
  [40.361817241456635, -3.559399058144385], [40.355681357129384, -3.551071786557397], [40.308347392319128, -3.583285179275485],
  [40.317989496261958, -3.668530143679132], [40.323687103137267, -3.692635403536204], [40.325440212945054, -3.722876547720531], [40.334205761983988, -3.733395206567254], 
  [40.358091883115101, -3.763417212025607], [40.359625854196914, -3.791247830224227], [40.381320588068277, -3.815353090081299], [40.383511975328013, -3.828720552365676], 
  [40.396660298886417, -3.836390407774744], [40.404987570473402, -3.831350217077357], [40.410246899896769, -3.824995194024128], 
  [40.424929194536986, -3.837705240130584], [40.43457129847981, -3.838581795034478], [40.445089957326537, -3.830473662173463], 
  [40.461087084322592, -3.812942564095592], [40.475111962784887, -3.783797113541132], [40.475331101510861, -3.763417212025607], 
  [40.474673685332938, -3.760130131136006],[40.480371292208247, -3.751802859549017], [40.484315789275769, -3.746324391399683], 
  [40.4939578932186, -3.738873674716588], [40.501846887353636, -3.736682287456854], [40.506229661873107, -3.745009559043842],
  [40.52595214721071, -3.730984680581546],[40.532964586441857, -3.715206692311462],[40.53888133204314, -3.70731769817642],
  [40.563205730626187, -3.717178940845223], [40.57087558603525, -3.713015305051728]
]
polygon_madrid = Polygon(madrid_polygon)
count_within = sum(
    polygon_madrid.contains(Point(row['Latitude'], row['Longitude']))
    for _, row in df_madrid.iterrows()
    if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
)

pre_out_madrid = round(((len(df_madrid)-count_within)/len(df_madrid) *100),2)
    
def tab3_layout():
    return html.Div(
        style=background_style_madrid,
        children=[
            dcc.Store(id='Madrid_data',data=df_madrid.to_dict('records')),
            dcc.Store(id='madrid-polygon-filter-active', data=False),
            dcc.Store(id='madrid-filtered-data', data=None),
            dcc.ConfirmDialog(
                id='madrid-confirm-dialog',
                message="The data has refreshed successfully!"
            ),
                html.Img(
                    src="/assets/airis.png", 
                    alt="Example Image", 
                    style={
                        "width": "200px", 
                        "position": "absolute",  # Absolute positioning
                        "top": "80px",          # Distance from the top of the page
                        "left": "10px",         # Distance from the left of the page
                        "zIndex": "1000"        # Ensures it stays above other elements
                    }
                ), 
            dbc.Container(
                style=container_style,
                children=[
                    # Title
                    html.H1(
                        "Airis-Labs: Geo-Location Analysis - Madrid",
                        className='mb-4',
                        style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}
                    ),
                    # Map and Filters Section
                    dbc.Row([
                        # Map on the left
                        dbc.Col(
                            dl.Map(
                                [
                                    dl.TileLayer(),
                                    dl.LayerGroup(id="madrid-map-layer", children=markers_madrid),    
                                    dl.LayerGroup(
                                        id="polygon-layer_madrid",
                                        children=[
                                            dl.Polygon(
                                                positions=madrid_polygon,
                                                color="blue",
                                                fillColor="cyan",
                                                fillOpacity=0.6,
                                            )
                                        ]
                                    ),

                                ],
                                center=(40.4168, -3.7038),  # Updated to Madrid coordinates
                                zoom=10,
                                style={"width": "100%", "height": "500px", "margin": "6px"}
                            ),
                            width=8
                        ),
                        # Filters on the right
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H4(
                                            "Filters",
                                            className='mb-3',
                                            style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                                        ),
                                        dbc.Label("Terrain Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='madrid-Terrain',
                                            options=[{'label': k, 'value': k} for k in unique_terrain_madrid_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Camera Tilt Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='madrid-Camera_Tilt',
                                            options=[{'label': k, 'value': k} for k in unique_tilt_madrid_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Occlusion Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='madrid-Occlusion',
                                            options=[{'label': k, 'value': k} for k in unique_occluded_madrid_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Video Quality Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='madrid-VQ',
                                            options=[{'label': k, 'value': k} for k in unique_vq_madrid_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Distance Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='madrid-Distance_Building',
                                            options=[{'label': k, 'value': k} for k in unique_distance_madrid_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Reset Filters",
                                                        id='madrid-reset-btn',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style
                                                    ),
                                                    width="auto"
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Update DB",
                                                        id='madrid-update',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style15
                                                    ),
                                                    width="auto"
                                                )
                                            ],
                                        ),
                                    ],
                                    style={"marginBottom": "30px"}
                                ),
                            ],
                            width=4
                        ),
                    ]),
                    html.H1(
                        id='madrid-record-count',
                        style={'textAlign': 'left', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    dbc.Button("Show Which Ones",id='polygon_dropouts_madrid', color='primary',n_clicks=0,style=button_polygon),
                    # Duration Slider Section (below the map)
                    html.Br(),
                    html.H4(
                        "Filter by Video Duration (seconds):",
                        className='mb-1',
                        style={'textAlign': 'left', 'color': 'rgb(255,51,153)', 'marginBottom': '0'}
                    ),
                    dbc.Row(
                        dbc.Col(
                            dcc.RangeSlider(
                                id='madrid-duration-slider',
                                min=min_dur_madrid,
                                max=max_dur_madrid,
                                step=0.1,
                                value=[min_dur_madrid, max_dur_madrid],
                                updatemode='mouseup',
                                marks={int(min_dur_madrid): str(int(min_dur_madrid)), int(max_dur_madrid): str(int(max_dur_madrid))},
                                tooltip={"always_visible": True, "placement": "bottom"}
                            ),
                            width=8
                        ),
                        justify="left"
                    ),
                    # Graphs Section
                    html.Div(
                        [
                            html.H4(
                                "Graphical Analysis",
                                className='mb-3',
                                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                            ),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Graph(id='madrid-bar-plot', figure=generate_interactive_bar_plot_madrid(df_madrid)),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Graph(id='madrid-pie-chart', figure=generate_interactive_pie_chart_madrid(df_madrid)),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Graph(id='madrid-pie-chart-weather', figure=generate_interactive_pie_chart_2_madrid(df_madrid)),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                                dbc.Col(
                                    dcc.Graph(id='madrid-bar-plot-logos', figure=generate_interactive_bar_plot_2_madrid(df_madrid)),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                            ]),
                        ],
                        style={'marginTop': '20px'}
                    ),
                    # General Insights Section
                    html.Div(
                        id='madrid-general-insights',
                        children=[
                            html.H2(
                                "General Insights",
                                className='mb-3',
                                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                            ),
                            html.Ul(
                                [
                                    html.Li(
                                        f"The majority of the videos are from {most_common_source_madrid}.",
                                        style={
                                            'fontSize': '18px',
                                            'marginBottom': '10px',
                                            'fontWeight': 'bold',
                                            'textAlign': 'justify',
                                            'color': 'white'
                                        }
                                    ),
                                    html.Li(
                                        f"They were mostly shot in {most_common_tilt_madrid} tilt, in "
                                        f"{most_common_tod_madrid} and in {most_common_terrain_madrid} terrain.",
                                        style={
                                            'fontSize': '18px',
                                            'marginBottom': '10px',
                                            'fontWeight': 'bold',
                                            'textAlign': 'justify',
                                            'color': 'white'
                                        }
                                    ),
                                    html.Li(
                                        f"The average video duration is {avg_dur_madrid} seconds.",
                                        style={
                                            'fontSize': '18px',
                                            'marginBottom': '10px',
                                            'fontWeight': 'bold',
                                            'textAlign': 'justify',
                                            'color': 'white'
                                        }
                                    )
                                ],
                                style={
                                    'padding': '10px',
                                    'marginLeft': '10px'
                                }
                            ),
                        ],
                        style={'padding': '10px'}
                    ),
                    # Full Details Section
                    html.Div(
                        [
                            html.H1("Full Details:", className='mb-4', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}),
                            html.Hr(),
                            dash_table.DataTable(
                                id='madrid-table',
                                columns=[
                                    {"name": first_column_name_madrid, "id": first_column_name_madrid, "presentation": "markdown"}
                                ] + [{"name": i, "id": i} for i in df_madrid.columns[1:]],
                                data=df_madrid.to_dict('records'),
                                sort_action="native",
                                filter_action="native",
                                fixed_rows={'headers': True},
                                style_table={'maxHeight': '500px',
                                            'overflowX': 'auto',
                                             'overflowY': 'auto'},
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
                                style_data_conditional=[
                                    {
                                        'if': {'column_id': 'Status'},
                                        'backgroundColor': 'rgb(220, 220, 220)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Active"'},
                                        'backgroundColor': 'rgb(85, 255, 85)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Inactive"'},
                                        'backgroundColor': 'rgb(255, 85, 85)',
                                        'color': 'white'
                                    },
                                ],
                            ),
                        ]
                    ),
                ]
            )
        ]
    )

# ---------------------------- Madrid Callback ----------------------------

@app.callback(
    [
        Output('madrid-table', 'data'),
        Output('madrid-map-layer', 'children'),
        Output('madrid-Terrain', 'value'),
        Output('madrid-Occlusion', 'value'),
        Output('madrid-VQ', 'value'),
        Output('madrid-Camera_Tilt', 'value'),
        Output('madrid-Distance_Building', 'value'),
        Output('madrid-record-count', 'children'),
        Output('madrid-duration-slider', 'min'),
        Output('madrid-duration-slider', 'max'),
        Output('madrid-duration-slider', 'value'),
        Output('madrid-bar-plot', 'figure'),
        Output('madrid-pie-chart', 'figure'),
        Output('madrid-pie-chart-weather', 'figure'),
        Output('madrid-bar-plot-logos','figure'),
        Output('madrid-general-insights', 'children'),
        Output('madrid-bar-plot', 'clickData'),
        Output('madrid-pie-chart', 'clickData'),
        Output('madrid-pie-chart-weather', 'clickData'),
        Output('madrid-bar-plot-logos','clickData'),
        Output('madrid-polygon-filter-active', 'data'),
        Output('madrid-filtered-data','data'),   # <--- NEW OUTPUT to store the filtered df
    ],
    [
        Input('madrid-bar-plot', 'clickData'),
        Input('madrid-pie-chart', 'clickData'),
        Input('madrid-pie-chart-weather', 'clickData'),
        Input('madrid-bar-plot-logos','clickData'),
        Input('madrid-reset-btn', 'n_clicks'),
        Input('madrid-update', 'n_clicks'),
        Input('madrid-duration-slider', 'value'),
        Input('madrid-Terrain', 'value'),
        Input('madrid-Occlusion', 'value'),
        Input('madrid-VQ', 'value'),
        Input('madrid-Camera_Tilt', 'value'),
        Input('madrid-Distance_Building', 'value'),
        Input('polygon_dropouts_madrid', "n_clicks"),
    ],
    [
        State('Madrid_data','data'),
        State('madrid-polygon-filter-active', 'data'),
        State('madrid-filtered-data', 'data'),  # <--- NEW STATE for the previously filtered df
    ]
)
def handle_table_and_refresh_madrid(
    bar_clickData, pie_clickData, pie_weather_clickData, bar_2_clickData, 
    reset_clicks, update_clicks, duration_range,
    selected_terrain, selected_occluded, selected_VQ, selected_tilt, selected_distance,
    polygon_filter_madrid,
    # States
    original_data, polygon_filter_active, stored_filtered_data
):

    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None

    # ------------------------------------------------------------------------
    # STEP 1: Decide which starting DataFrame we will use this round
    # ------------------------------------------------------------------------
    # - If this is the very first callback or we've just reset, 
    #   we start from `original_data`.
    # - Otherwise, we start from `stored_filtered_data` if available.

    if stored_filtered_data is not None and triggered_id != 'madrid-reset-btn.n_clicks':
        # Start from the previously filtered subset
        df_current = pd.DataFrame(stored_filtered_data)
    else:
        # Use the original data from the store if there's no existing filtered subset 
        # or if the user clicked reset
        df_current = pd.DataFrame(original_data)

    # Ensure Coordinates are split into lat/long if not already
    if 'Coordinates' in df_current.columns:
        df_current = df_current[df_current['Coordinates'].str.contains(',', na=False)]
        df_current[['Latitude', 'Longitude']] = df_current['Coordinates'].str.split(',', expand=True)
        df_current['Latitude'] = pd.to_numeric(df_current['Latitude'], errors='coerce')
        df_current['Longitude'] = pd.to_numeric(df_current['Longitude'], errors='coerce')

    # Compute or recompute Duration if needed
    if 'Duration' not in df_current.columns:
        df_current['Duration'] = df_current['Finish Time'].apply(convert_to_minutes) - \
                                 df_current['Start Time'].apply(convert_to_minutes)

    # Drop any rows with invalid coords
    df_current.dropna(subset=['Latitude', 'Longitude'], inplace=True)

    global df_madrid, min_dur_madrid, max_dur_madrid  # If you rely on these globally
    df_madrid = load_madrid_data()  # optional if you still need the original outside
    min_dur_madrid = df_current['Duration'].min()
    max_dur_madrid = df_current['Duration'].max()

    # polygon_madrid should be globally defined or imported from somewhere
    # for checking .contains(Point(row['Latitude'], row['Longitude']))

    # ------------------------------------------------------------------------
    # STEP 2: Handle each triggered event
    # ------------------------------------------------------------------------

    # 2.1 "UPDATE" button - re-load from original source, but keep current filters
    if triggered_id == 'madrid-update.n_clicks' and update_clicks > 0:
        # Re-load data from your source
        df_updated = load_madrid_data()
        # Same prep steps (split coords, compute Duration, drop invalid coords, etc.)
        df_updated['Duration'] = df_updated['Finish Time'].apply(convert_to_minutes) - \
                                 df_updated['Start Time'].apply(convert_to_minutes)
        df_updated = df_updated[df_updated['Coordinates'].str.contains(',', na=False)]
        df_updated[['Latitude', 'Longitude']] = df_updated['Coordinates'].str.split(',', expand=True)
        df_updated['Latitude'] = pd.to_numeric(df_updated['Latitude'], errors='coerce')
        df_updated['Longitude'] = pd.to_numeric(df_updated['Longitude'], errors='coerce')
        df_updated.dropna(subset=['Latitude', 'Longitude'], inplace=True)

        # Now apply the current user filters to the newly updated data
        filtered_df = apply_all_filters(
            df=df_updated,
            duration_range=duration_range,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            bar_clickData=bar_clickData,
            pie_clickData=pie_clickData,
            pie_weather_clickData=pie_weather_clickData,
            bar_2_clickData=bar_2_clickData,
            polygon_filter_active=polygon_filter_active,
        )

        # Create map markers
        markers_madrid = create_map_markers(filtered_df)

        # Count inside polygon
        count_within = sum(
            polygon_madrid.contains(Point(row['Latitude'], row['Longitude']))
            for _, row in filtered_df.iterrows()
        )
        pre_out_madrid = round(((len(filtered_df)-count_within)/len(filtered_df) * 100), 2)
        record_count_text = f"Total Records: {len(filtered_df)}, {pre_out_madrid} % out of polygon"

        # Build / refresh graphs
        updated_bar_plot = generate_interactive_bar_plot_madrid(filtered_df)
        updated_pie_chart = generate_interactive_pie_chart_madrid(filtered_df)
        updated_pie_chart_weather = generate_interactive_pie_chart_2_madrid(filtered_df)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_madrid(filtered_df)

        # Build general insights
        general_insights = build_general_insights_div(filtered_df)

        # Return and also store filtered data in 'madrid-filtered-data'
        return (
            filtered_df.to_dict('records'),
            dash.no_update,  # map-layer - if you want the new markers, see below
            dash.no_update,  # Terrain
            dash.no_update,  # Occlusion
            dash.no_update,  # VQ
            dash.no_update,  # Tilt
            dash.no_update,  # Distance building
            record_count_text,
            filtered_df['Duration'].min(),
            filtered_df['Duration'].max(),
            duration_range,  # keep slider the same
            updated_bar_plot,
            updated_pie_chart,
            updated_pie_chart_weather,
            updated_bar_plot_logos,
            general_insights,
            None, None, None, None,
            polygon_filter_active,
            filtered_df.to_dict('records'),  # <--- store updated data
        )

    # 2.2 "POLYGON FILTER" button
    elif triggered_id == 'polygon_dropouts_madrid.n_clicks' and polygon_filter_madrid > 0:
        # Indicate that polygon filter is now active
        polygon_filter_active = True

        # Start from df_current and remove in-polygon points
        filtered_polygon = df_current.copy()

        # Re-apply standard filters (duration, etc.) if needed
        # (You can do it before or after removing in-polygon points, 
        #  but typically you want them all together.)
        filtered_polygon = apply_all_filters(
            df=filtered_polygon,
            duration_range=duration_range,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            bar_clickData=bar_clickData,
            pie_clickData=pie_clickData,
            pie_weather_clickData=pie_weather_clickData,
            bar_2_clickData=bar_2_clickData,
            polygon_filter_active=False, # Because we'll remove them below
        )

        # Now remove points *inside* the polygon
        filtered_polygon = filtered_polygon[
            ~filtered_polygon.apply(
                lambda row: polygon_madrid.contains(Point(row['Latitude'], row['Longitude'])), 
                axis=1
            )
        ]

        # Build map markers
        markers_madrid = create_map_markers(filtered_polygon)

        # Build Figures
        updated_bar_plot = generate_interactive_bar_plot_madrid(filtered_polygon)
        updated_pie_chart = generate_interactive_pie_chart_madrid(filtered_polygon)
        updated_pie_chart_weather = generate_interactive_pie_chart_2_madrid(filtered_polygon)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_madrid(filtered_polygon)

        # Build general insights
        general_insights = build_general_insights_div(filtered_polygon)

        record_count_text = f"Total Records: {len(filtered_polygon)}, 100% out of Polygon"

        return (
            filtered_polygon.to_dict('records'),
            markers_madrid,
            selected_terrain,
            selected_occluded,
            selected_VQ,
            selected_tilt,
            selected_distance,
            record_count_text,
            filtered_polygon['Duration'].min(),
            filtered_polygon['Duration'].max(),
            duration_range,
            updated_bar_plot,
            updated_pie_chart,
            updated_pie_chart_weather,
            updated_bar_plot_logos,
            general_insights,
            bar_clickData,
            pie_clickData,
            pie_weather_clickData,
            bar_2_clickData,
            polygon_filter_active,
            filtered_polygon.to_dict('records'),  # <--- store the polygon-filtered df
        )

    # 2.3 "RESET" button
    elif triggered_id == 'madrid-reset-btn.n_clicks':
        # Reset everything to the original data
        df_reset = pd.DataFrame(original_data).copy()
        df_reset = df_reset[df_reset['Coordinates'].str.contains(',', na=False)]
        df_reset[['Latitude', 'Longitude']] = df_reset['Coordinates'].str.split(',', expand=True)
        df_reset['Latitude'] = pd.to_numeric(df_reset['Latitude'], errors='coerce')
        df_reset['Longitude'] = pd.to_numeric(df_reset['Longitude'], errors='coerce')
        df_reset.dropna(subset=['Latitude', 'Longitude'], inplace=True)

                               

        polygon_filter_active = False  # turn off polygon filter

        # Create map markers
        markers_madrid = create_map_markers(df_reset)

        # Count in polygon vs out
        count_within = sum(
            polygon_madrid.contains(Point(row['Latitude'], row['Longitude']))
            for _, row in df_reset.iterrows()
        )
        pre_out_madrid = round(((len(df_reset) - count_within) / len(df_reset) * 100), 2)

        # Build graphs
        updated_bar_plot = generate_interactive_bar_plot_madrid(df_reset)
        updated_pie_chart = generate_interactive_pie_chart_madrid(df_reset)
        updated_pie_chart_weather = generate_interactive_pie_chart_2_madrid(df_reset)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_madrid(df_reset)

        # General insights
        general_insights = build_general_insights_div(df_reset)

        return (
            df_reset.to_dict('records'),
            markers_madrid,
            'All',       # reset Terrain
            'All',       # reset Occlusion
            'All',       # reset VQ
            'All',       # reset Camera Tilt
            'All',       # reset Distance from building
            f"Total Records: {len(df_reset)}, {pre_out_madrid}% out of polygon",
            df_reset['Duration'].min(),
            df_reset['Duration'].max(),
            [df_reset['Duration'].min(), df_reset['Duration'].max()],
            updated_bar_plot,
            updated_pie_chart,
            updated_pie_chart_weather,
            updated_bar_plot_logos,
            general_insights,
            None, None, None, None,
            polygon_filter_active,
            df_reset.to_dict('records')  ,  # <--- store data as None or the full df again, your choice
        )

    # 2.4 DEFAULT branch: user changed dropdowns, slider, or clicked bar/pie but not polygon filter
    #     We just apply all filters on df_current
    else:
        filtered_df = apply_all_filters(
            df=df_current,
            duration_range=duration_range,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            bar_clickData=bar_clickData,
            pie_clickData=pie_clickData,
            pie_weather_clickData=pie_weather_clickData,
            bar_2_clickData=bar_2_clickData,
            polygon_filter_active=polygon_filter_active,
        )

        # If polygon filter is active, remove inside-polygon points
        if polygon_filter_active:
            filtered_df = filtered_df[
                ~filtered_df.apply(
                    lambda row: polygon_madrid.contains(Point(row['Latitude'], row['Longitude'])), 
                    axis=1
                )
            ]

        # Create map markers
        markers_madrid = create_map_markers(filtered_df)

        # Count in polygon vs out
        count_within = sum(
            polygon_madrid.contains(Point(row['Latitude'], row['Longitude']))
            for _, row in filtered_df.iterrows()
        )
        pre_out_madrid = round(((len(filtered_df) - count_within) / len(filtered_df) * 100), 2)

        record_count_text = f"Total Records: {len(filtered_df)}, {pre_out_madrid} % out of polygon"

        # Refresh graphs
        updated_bar_plot = generate_interactive_bar_plot_madrid(filtered_df)
        updated_pie_chart = generate_interactive_pie_chart_madrid(filtered_df)
        updated_pie_chart_weather = generate_interactive_pie_chart_2_madrid(filtered_df)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_madrid(filtered_df)

        # Insights
        general_insights = build_general_insights_div(filtered_df)

        return (
            filtered_df.to_dict('records'),
            markers_madrid,
            selected_terrain,
            selected_occluded,
            selected_VQ,
            selected_tilt,
            selected_distance,
            record_count_text,
            filtered_df['Duration'].min(),
            filtered_df['Duration'].max(),
            duration_range,
            updated_bar_plot,
            updated_pie_chart,
            updated_pie_chart_weather,
            updated_bar_plot_logos,
            general_insights,
            bar_clickData,
            pie_clickData,
            pie_weather_clickData,
            bar_2_clickData,
            polygon_filter_active,
            filtered_df.to_dict('records'),  # <--- store final filtered df
        )



def load_barcelona_data():
    # Google Sheet ID and Range for Barcelona
    SHEET_ID_barcelona = '14hSdXXSL_ehJO3tdogLQcVahqIuDy6UREUEv7LusVU8'
    RANGE_barcelona = 'Barcelona!A1:R400'

    try:
        # Access the Google Sheet for Barcelona
        result = sheet.values().get(spreadsheetId=SHEET_ID_barcelona, range=RANGE_barcelona).execute()
        values = result.get('values', [])

        # Convert the data to a pandas DataFrame
        if values:
            headers = values[0]  # Assuming the first row is the header
            data = values[1:]    # Rest is the data
            df_bar = pd.DataFrame(data, columns=headers)
        else:
            print("No data found for Barcelona.")
            df_bar = pd.DataFrame()

        return df_bar

    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

# ---------------------------- Initial Data Loading ----------------------------
# Load the full DataFrame
df_barcelona_full = load_barcelona_data()

# Create a copy for initial display and filtering
df_barcelona = df_barcelona_full.copy()

# ---------------------------- Initial Data Processing ----------------------------
# Process Barcelona Data
if not df_barcelona.empty:
    first_column_name_barcelona = df_barcelona.columns[0]
    df_barcelona[first_column_name_barcelona] = df_barcelona[first_column_name_barcelona].apply(
        lambda x: f"[{x}]({x})" if pd.notnull(x) else x
    )
    replacements = {
        'NaN': np.nan,
        'NULL': np.nan,
        '': np.nan,
    }

    # Replace values in specified columns
    for col in df_barcelona.columns[8:-1]:
        df_barcelona[col] = df_barcelona[col].replace(replacements)

    # Convert 'Duration' column
    df_barcelona['Duration'] = df_barcelona.apply(calculate_duration, axis=1)

    # Extract unique values for filters
    unique_tod_barcelona = df_barcelona['Time of the day'].dropna().unique()
    unique_weather_barcelona = df_barcelona['Weather'].dropna().unique()
    unique_terrain_barcelona = df_barcelona['Terrain'].dropna().unique()
    unique_occluded_barcelona = df_barcelona['Occluded'].dropna().unique()
    unique_tilt_barcelona = df_barcelona['Camera tilt'].dropna().unique()
    unique_distance_barcelona = df_barcelona['Distance from building'].dropna().unique()
    unique_vq_barcelona = df_barcelona['Video quality'].dropna().unique()

    # Determine most common values
    most_common_tod_barcelona = df_barcelona['Time of the day'].mode().iloc[0] if not df_barcelona['Time of the day'].dropna().mode().empty else None
    most_common_terrain_barcelona = df_barcelona['Terrain'].mode().iloc[0] if not df_barcelona['Terrain'].dropna().mode().empty else None
    most_common_tilt_barcelona = df_barcelona['Camera tilt'].mode().iloc[0] if not df_barcelona['Camera tilt'].dropna().mode().empty else None

    # Calculate duration statistics
    avg_dur_barcelona = round(df_barcelona['Duration'].mean(), 2)
    min_dur_barcelona = df_barcelona['Duration'].min()
    max_dur_barcelona = df_barcelona['Duration'].max()

    # Define color maps
    color_map2_barcelona = {
        'Night Time': 'rgb(1, 1, 1)',      # Black
        'Day Time': 'rgb(236, 255, 0)'
    }

    color_map3_barcelona = {
        'Clear': 'rgb(224,255,255)',
        'Snow': 'rgb(255,250,250)',
        'Rain': 'rgb(123,104,238)',
        'Fog or Smoke': 'rgb(128,128,128)'
    }

    # Define background style
    background_style_barcelona = {
        "background-size": "cover",
        "background-position": "center",
        "height": "250vh",
        "padding": "10px",
        "background-color": 'black',
    }

    # Define filter options with 'All'
    unique_occluded_barcelona_1 = ['All'] + list(unique_occluded_barcelona)
    unique_terrain_barcelona_1 = ['All'] + list(unique_terrain_barcelona)
    unique_tilt_barcelona_1 = ['All'] + list(unique_tilt_barcelona)
    unique_distance_barcelona_1 = ['All'] + list(unique_distance_barcelona)
    unique_vq_barcelona_1 = ['All'] + list(unique_vq_barcelona)
    
    df_barcelona = df_barcelona[df_barcelona['Coordinates'].notna() & df_barcelona['Coordinates'].str.contains(',')]
    df_barcelona = df_barcelona[
        df_barcelona['Coordinates'].notna() &  
        df_barcelona['Coordinates'].str.contains(
            r'^\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*$',  # Non-capturing groups
            na=False
        )
    ]

    # Split 'Coordinates' into 'Latitude' and 'Longitude'
    df_barcelona[['Latitude', 'Longitude']] = df_barcelona['Coordinates'].str.split(',', expand=True)
    df_barcelona['Latitude'] = pd.to_numeric(df_barcelona['Latitude'], errors='coerce')
    df_barcelona['Longitude'] = pd.to_numeric(df_barcelona['Longitude'], errors='coerce')
    df_barcelona = df_barcelona.dropna(subset=['Latitude', 'Longitude'])



    # Get the integer index of the "Raw File Name" column

    # Create Map Markers
    markers_barcelona = [
        dl.Marker(
            position=(row['Latitude'], row['Longitude']),
            children=[dl.Popup(row['Coordinates'])],  # Directly use the string instead of the hyperlink format
            id=f"barcelona-mark-{i}"
        )
        for i, row in df_barcelona.iterrows()
        if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
    ]

    global polygon_coordinates_ellipse
    global polygon
    
    polygon_coordinates_ellipse = [ 
  [ 41.418995032424789, 2.238026462497374 ], 
  [ 41.293540319613996, 2.160395613168439 ], 
  [ 41.272503001920555, 2.058057828138868 ], 
  [ 41.262439553143395, 1.995505251289152 ], 
  [ 41.262439553143395, 1.936796946558631 ], 
  [ 41.34001838439444, 1.985021625444416 ], 
  [ 41.373216532902774, 1.994107434509854 ], 
  [ 41.437076185126571, 2.002067883652669 ], 
  [ 41.445239102669078, 2.004533194319869 ], 
  [ 41.449841015914515, 2.009189892246804 ], 
  [ 41.449128815055104, 2.019653766412033 ], 
  [ 41.431104654843786, 2.05301763744148 ], 
  [ 41.439103218341813, 2.090764282990396 ], 
  [ 41.427762789272705, 2.12226547484907 ], 
  [ 41.447868767380761, 2.132838918377287 ], 
  [ 41.448663145262429, 2.152342264988918 ], 
  [ 41.450087546981258, 2.153520135641025 ], 
  [ 41.450142331662754, 2.155547168856279 ], 
  [ 41.450744963159181, 2.157902910160493 ], 
  [ 41.451731087426062, 2.167791545170042 ], 
  [ 41.458990057723931, 2.166832813243909 ], 
  [ 41.466166850999556, 2.166202789406735 ], 
  [ 41.467344721651664, 2.164915349391641 ], 
  [ 41.469152616140946, 2.167572406444068 ], 
  [ 41.468906085074224, 2.168558530710949 ], 
  [ 41.465619004184624, 2.17365350608983 ], 
  [ 41.467043405903446, 2.178529342742738 ], 
  [ 41.467919960807343, 2.178501950401991 ], 
  [ 41.470385271474541, 2.179323720624391 ], 
  [ 41.471398788082169, 2.179981136802311 ], 
  [ 41.472357520008302, 2.18691139901122 ], 
  [ 41.466221635681052, 2.187514030507646 ], 
  [ 41.466870257115744, 2.225096657288868 ], 
  [ 41.483644058467327, 2.251655176095531 ], 
  [ 41.506358581130918, 2.281009328460792 ], 
  [ 41.539556729639251, 2.372915781699643 ], 
  [ 41.53990618383407, 2.387942312077098 ], 
  [ 41.563669069082145, 2.465259052682024 ], 
  [ 41.547069994827986, 2.475131133685817 ], 
  [ 41.517191661170486, 2.436865899352531 ], 
  [ 41.484692421051804, 2.365926697803152 ], 
  [ 41.418995032424789, 2.238026462497374 ] 
]
    polygon = Polygon(polygon_coordinates_ellipse)

    # Iterate through the markers and count those within the polygon
    count_within = sum(
        polygon.contains(Point(row['Latitude'], row['Longitude']))
        for _, row in df_barcelona.iterrows()
        if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
    )
    
    pre_within = round(((len(df_barcelona)-count_within)/len(df_barcelona) *100),2)


    # Generate Initial Figures
    def generate_interactive_bar_plot_2_barcelona(df):
        source_counts = df['Logos and text'].value_counts().reset_index()
        source_counts.columns = ['Logos and text', 'Count']

        fig = px.bar(
            source_counts, 
            x='Logos and text', 
            y='Count', 
            color='Logos and text', 
            color_discrete_map=color_map2_barcelona,
            title='Logos and text Distribution'
        )
        fig.update_traces(
            marker_line_width=1.5, 
            hovertemplate="Count: %{y}", 
            textfont=dict(size=22)
        )
        fig.update_layout(
            xaxis_title="Logos and text", 
            yaxis_title="Count", 
            showlegend=False,
            hovermode="x unified",
            font=dict(size=16, color='white'),
            plot_bgcolor='black',
            paper_bgcolor='black',
            title_font=dict(color='white'),
            xaxis=dict(
                color='white',
                gridcolor='gray',
                zerolinecolor='gray',
                title_font=dict(color='white'),
                tickfont=dict(color='white')
            ),
            yaxis=dict(
                color='white',
                gridcolor='gray',
                zerolinecolor='gray',
                title_font=dict(color='white'),
                tickfont=dict(color='white')
            ),
            hoverlabel=dict(font=dict(size=24, color='white'))
        )

        return fig

    def generate_interactive_pie_chart_barcelona(df):
        tod_counts = df['Time of the day'].value_counts().reset_index()
        tod_counts.columns = ['Time of the day', 'Count']

        fig = px.pie(
            tod_counts,
            names='Time of the day',
            values='Count',
            color='Time of the day',
            color_discrete_map=color_map2_barcelona,
            title='Time of the day'
        )

        depth_values = [0.05 + i * 0.01 for i in range(len(tod_counts))]
        fig.update_traces(
            marker=dict(line=dict(color='white', width=2)),
            pull=depth_values,
            textinfo='label',
            textfont=dict(color='yellow', size=22)  
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

    def generate_interactive_bar_chart_weather_barcelona(df):
        # Calculate the counts for each Weather category
        weather_counts = df['Weather'].value_counts().reset_index()
        weather_counts.columns = ['Weather', 'Count']

        # Create a bar chart
        fig = px.bar(
            weather_counts,
            x='Weather',
            y='Count',
            color='Weather',
            color_discrete_map=color_map3_barcelona,
            title='Weather'
        )

        # Customize the bar traces
        fig.update_traces(
            marker_line_width=1.5,
            hovertemplate="Count: %{y}",
            textfont=dict(size=22)  
        )

        # Update layout for black background, fonts, etc.
        fig.update_layout(
            xaxis_title="Weather",
            yaxis_title="Count",
            showlegend=False,
            hovermode="x unified",
            font=dict(size=16, color='white'),
            plot_bgcolor='black',
            paper_bgcolor='black',
            title_font=dict(color='white', size=24),
            xaxis=dict(
                color='white',
                gridcolor='gray',
                zerolinecolor='gray',
                title_font=dict(color='white'),
                tickfont=dict(color='white')
            ),
            yaxis=dict(
                color='white',
                gridcolor='gray',
                zerolinecolor='gray',
                title_font=dict(color='white'),
                tickfont=dict(color='white')
            ),
            margin=dict(t=40, b=20, l=0, r=0),
            hoverlabel=dict(font=dict(size=24, color='white'))
        )

        return fig

    def generate_interactive_pie_chart_status(df):
        color_map = {
            'done': '#006400',
            'not started': '#FF0000',
            'not found': '#DC143C',
            'irrelevant': '#00FFFF'
        }

        # Ensure that only the Status column is used for value_counts
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']

        # Map a color to each status
        fig = px.pie(
            status_counts,
            names='Status',
            values='Count',
            color='Status',
            color_discrete_map=color_map,
            title='Status Distribution'
        )

        # Add depth to the slices
        depth_values = [0.05 + i * 0.01 for i in range(len(status_counts))]
        fig.update_traces(
            marker=dict(line=dict(color='white', width=2)),
            pull=depth_values,
            textinfo='label',
            textfont=dict(color='yellow', size=22)  
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

    # Generate Initial Figures
    pie_chart_initial = generate_interactive_pie_chart_barcelona(df_barcelona)
    pie_chart_weather_initial = generate_interactive_bar_chart_weather_barcelona(df_barcelona)
    bar_plot_logos_initial = generate_interactive_bar_plot_2_barcelona(df_barcelona)
    status_pie_initial = generate_interactive_pie_chart_status(df_barcelona)

    # General Insights
    general_insights_initial = html.Div(
        [
            html.H2(
                "General Insights",
                className='mb-3',
                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
            ),
            html.Ul(
                [
                    html.Li(
                        f"They were mostly shot in {most_common_tilt_barcelona} tilt, in "
                        f"{most_common_tod_barcelona} and in {most_common_terrain_barcelona} terrain.",
                        style={
                            'fontSize': '18px',
                            'marginBottom': '10px',
                            'fontWeight': 'bold',
                            'textAlign': 'justify',
                            'color': 'white'
                        }
                    ),
                    html.Li(
                        f"The average video duration is {avg_dur_barcelona} seconds.",
                        style={
                            'fontSize': '18px',
                            'marginBottom': '10px',
                            'fontWeight': 'bold',
                            'textAlign': 'justify',
                            'color': 'white'
                        }
                    )
                ],
                style={
                    'padding': '10px',
                    'marginLeft': '10px'
                }
            ),
        ],
        style={'padding': '10px'}
    )
else:
    # Handle empty DataFrame
    first_column_name_barcelona = "ID"
    avg_dur_barcelona = 0
    min_dur_barcelona = 0
    max_dur_barcelona = 0
    most_common_tod_barcelona = None
    most_common_terrain_barcelona = None
    most_common_tilt_barcelona = None
    markers_barcelona = []
    pie_chart_initial = {}
    pie_chart_weather_initial = {}
    bar_plot_logos_initial = {}
    status_pie_initial = {}
    general_insights_initial = html.Div()

# ---------------------------- Layout Definition ----------------------------
def tab4_layout():
    return html.Div(
        style=background_style_barcelona,
        children=[  
            dcc.ConfirmDialog(
                id='barcelona-confirm-dialog',
                message="The data has refreshed successfully!"
            ),
            html.Img(
                src="/assets/airis.png", 
                alt="Airis Logo", 
                style={
                    "width": "200px", 
                    "position": "absolute",  # Absolute positioning
                    "top": "80px",          # Distance from the top of the page
                    "left": "10px",         # Distance from the left of the page
                    "zIndex": "1000"        # Ensures it stays above other elements
                }
            ), 
            dcc.Store(id='barcelone-data', data=df_barcelona.to_dict('records')),
            dbc.Container(
                style=container_style,
                children=[
                    # Title
                    html.H1(
                        "Airis-Labs: Geo-Location Analysis - Barcelona",
                        className='mb-4',
                        style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}
                    ),
                    # Map and Filters Section
                    dbc.Row([
                        # Map on the left
                            dbc.Col(
                                dl.Map(
                                    [
                                        dl.TileLayer(),
                                        # Layer group for markers
                                        dl.LayerGroup(id="barcelona-map-layer", children=markers_barcelona),
                                        # Separate layer group for polygon
                                        dl.LayerGroup(
                                            id="polygon-layer",
                                            children=[
                                                dl.Polygon(
                                                    positions=polygon_coordinates_ellipse,
                                                    color="blue",
                                                    fillColor="cyan",
                                                    fillOpacity=0.6,
                                                )
                                            ]
                                        ),
                                    ],
                                    center=(41.4035011, 2.1743682),  # Barcelona coordinates
                                    zoom=10,
                                    style={"width": "100%", "height": "500px", "margin": "6px"}
                                ),
                                width=8
                            ),
                        # Filters on the right
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H4(
                                            "Filters",
                                            className='mb-3',
                                            style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                                        ),
                                        dbc.Label("Terrain Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='barcelona-Terrain',
                                            options=[{'label': k, 'value': k} for k in unique_terrain_barcelona_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Camera Tilt Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='barcelona-Camera_Tilt',
                                            options=[{'label': k, 'value': k} for k in unique_tilt_barcelona_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Occlusion Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='barcelona-Occlusion',
                                            options=[{'label': k, 'value': k} for k in unique_occluded_barcelona_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Video Quality Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='barcelona-VQ',
                                            options=[{'label': k, 'value': k} for k in unique_vq_barcelona_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Distance Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='barcelona-Distance_Building',
                                            options=[{'label': k, 'value': k} for k in unique_distance_barcelona_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Reset Filters",
                                                        id='barcelona-reset-btn',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style
                                                    ),
                                                    width="auto"
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Update DB",
                                                        id='barcelona-update',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style15
                                                    ),
                                                    width="auto"
                                                ),
                                            ],
                                        ),
                                    ],
                                    style={"marginBottom": "30px"}
                                ),
                            ],
                            width=4
                        ),
                    ]),
                    # Record Count
                    html.H1(
                        id='barcelona-record-count',
                        children=f"Total Records: {len(df_barcelona)}, {pre_within} % out of Polygon ",
                        style={'textAlign': 'left', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    dbc.Button("Show Which Ones",id='polygon_dropouts', color='primary',n_clicks=0,style=button_polygon),
                    # Duration Slider Section (below the map)
                    html.Br(),
                    html.H4(
                        "Filter by Video Duration (seconds):",
                        className='mb-1',
                        style={'textAlign': 'left', 'color': 'rgb(255,51,153)', 'marginBottom': '0'}
                    ),
                    dbc.Row(
                        dbc.Col(
                            dcc.RangeSlider(
                                id='barcelona-duration-slider',
                                min=min_dur_barcelona if not df_barcelona.empty else 0,
                                max=max_dur_barcelona if not df_barcelona.empty else 100,
                                step=0.1,
                                value=[min_dur_barcelona, max_dur_barcelona] if not df_barcelona.empty else [0, 100],
                                updatemode='mouseup',
                                marks={
                                    int(min_dur_barcelona): str(int(min_dur_barcelona)),
                                    int(max_dur_barcelona): str(int(max_dur_barcelona))
                                } if not df_barcelona.empty else {},
                                tooltip={"always_visible": True, "placement": "bottom"}
                            ),
                            width=8
                        ),
                        justify="left"
                    ),
                    # Graphs Section
                    html.Div(
                        [
                            html.H4(
                                "Graphical Analysis",
                                className='mb-3',
                                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                            ),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Graph(id='barcelona-pie-chart', figure=pie_chart_initial),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Graph(id='barcelona-pie-chart-weather', figure=pie_chart_weather_initial),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                                dbc.Col(
                                    dcc.Graph(id='barcelona-bar-plot-logos', figure=bar_plot_logos_initial),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                                dbc.Col(
                                    dcc.Graph(id='barcelona-status-pie', figure=status_pie_initial),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),                                
                                
                            ]),
                        ],
                        style={'marginTop': '20px'}
                    ),
                    # General Insights Section
                    html.Div(
                        id='barcelona-general-insights',
                        children=general_insights_initial,
                        style={'padding': '10px'}
                    ),
                    # Full Details Section
                    html.Div(
                        [
                            html.H1("Full Details:", className='mb-4', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}),
                            html.Hr(),
                            dash_table.DataTable(
                                id='barcelona-table',
                                columns=[
                                    {"name": first_column_name_barcelona, "id": first_column_name_barcelona, "presentation": "markdown"}
                                ] + [{"name": i, "id": i} for i in df_barcelona.columns[1:]] if not df_barcelona.empty else [],
                                data=df_barcelona.to_dict('records') if not df_barcelona.empty else [],
                                sort_action="native",
                                filter_action="native",
                                fixed_rows={'headers': True},
                                style_table={'maxHeight': '500px',
                                            'overflowX': 'auto',
                                             'overflowY': 'auto'},
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
                                style_data_conditional=[
                                    {
                                        'if': {'column_id': 'Status'},
                                        'backgroundColor': 'rgb(220, 220, 220)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Active"'},
                                        'backgroundColor': 'rgb(85, 255, 85)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Inactive"'},
                                        'backgroundColor': 'rgb(255, 85, 85)',
                                        'color': 'white'
                                    },
                                ],
                            ),
                        ]
                    ),
                ]
            )
        ]
    )

# ---------------------------- Callback Definition ----------------------------

@app.callback(
    [
        Output('barcelona-table', 'data'),
        Output('barcelona-map-layer', 'children'),
        Output('barcelona-Terrain', 'value'),
        Output('barcelona-Occlusion', 'value'),
        Output('barcelona-VQ', 'value'),
        Output('barcelona-Camera_Tilt', 'value'),
        Output('barcelona-Distance_Building', 'value'),
        Output('barcelona-record-count', 'children'),
        Output('barcelona-duration-slider', 'min'),
        Output('barcelona-duration-slider', 'max'),
        Output('barcelona-duration-slider', 'value'),
        Output('barcelona-pie-chart', 'figure'),
        Output('barcelona-pie-chart-weather', 'figure'),
        Output('barcelona-bar-plot-logos', 'figure'),
        Output('barcelona-status-pie', 'figure'),
        Output('barcelona-general-insights', 'children'),
        Output('barcelona-pie-chart', 'clickData'),
        Output('barcelona-pie-chart-weather', 'clickData'),
        Output('barcelona-bar-plot-logos', 'clickData'),
        Output('barcelona-status-pie', 'clickData'),
        Output('barcelona-duration-slider', 'marks'),  # 21) Slider marks

    ],
    [
        Input('barcelona-pie-chart', 'clickData'),
        Input('barcelona-pie-chart-weather', 'clickData'),
        Input('barcelona-bar-plot-logos', 'clickData'),
        Input('barcelona-status-pie', 'clickData'),
        Input('barcelona-reset-btn', 'n_clicks'),
        Input('barcelona-duration-slider', 'value'),
        Input('barcelona-Terrain', 'value'),
        Input('barcelona-Occlusion', 'value'),
        Input('barcelona-VQ', 'value'),
        Input('barcelona-Camera_Tilt', 'value'),
        Input('barcelona-Distance_Building', 'value'),
        Input('barcelona-update', 'n_clicks'),
        Input('polygon_dropouts','n_clicks')
    ],
    State("barcelone-data","data")
)
def handle_table_and_refresh_barcelona(
    pie_clickData, pie_weather_clickData, bar_2_clickData, status_pie_clickData,
    reset_clicks, duration_range,
    selected_terrain, selected_occluded, selected_VQ,
    selected_tilt, selected_distance,
    update_clicks,polygon_filter,current_data
):
    ctx = dash.callback_context
    # Split off ".n_clicks" or ".value" from prop_id to get the component ID alone
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else None

    try:
        global df_barcelona_full, df_barcelona, min_dur_barcelona, max_dur_barcelona

        # ---------------------------------------------------------------------
        # 1) If the "Update" button was clicked
        # ---------------------------------------------------------------------
        if triggered_id == 'barcelona-update' and update_clicks > 0:
            # 1) Load the fresh data into df_barcelona_full
            df_barcelona_full = load_barcelona_data()

            # 2) Create a fresh copy for df_barcelona
            df_barcelona = df_barcelona_full.copy()

            if not df_barcelona.empty:
                # Re-apply initial data processing on the full DataFrame
                first_column_name_barcelona = df_barcelona.columns[0]
                df_barcelona[first_column_name_barcelona] = df_barcelona[first_column_name_barcelona].apply(
                    lambda x: f"[{x}]({x})" if pd.notnull(x) else x
                )
                replacements = {
                    'NaN': np.nan,
                    'NULL': np.nan,
                    '': np.nan,
                }
                # Perform the same replacements you do at initial load
                for col in df_barcelona.columns[8:-1]:
                    df_barcelona[col] = df_barcelona[col].replace(replacements)

                # Recalculate Duration
                df_barcelona['Duration'] = df_barcelona.apply(calculate_duration, axis=1)

                # Update duration statistics
                avg_dur_barcelona = round(df_barcelona['Duration'].mean(), 2)
                min_dur_barcelona = df_barcelona['Duration'].min()
                max_dur_barcelona = df_barcelona['Duration'].max()
                
                slider_marks = {
                int(min_dur_barcelona): f"{int(min_dur_barcelona)}",
                int((min_dur_barcelona + max_dur_barcelona) / 2): f"{int((min_dur_barcelona + max_dur_barcelona) / 2)}",
                int(max_dur_barcelona): f"{int(max_dur_barcelona)}"
            }

                # Update unique filter options
                unique_occluded_barcelona_1 = ['All'] + list(df_barcelona_full['Occluded'].dropna().unique())
                unique_terrain_barcelona_1 = ['All'] + list(df_barcelona_full['Terrain'].dropna().unique())
                unique_tilt_barcelona_1 = ['All'] + list(df_barcelona_full['Camera tilt'].dropna().unique())
                unique_distance_barcelona_1 = ['All'] + list(df_barcelona_full['Distance from building'].dropna().unique())
                unique_vq_barcelona_1 = ['All'] + list(df_barcelona_full['Video quality'].dropna().unique())

                df_barcelona = df_barcelona[df_barcelona['Coordinates'].notna() & df_barcelona['Coordinates'].str.contains(',')]
                df_barcelona = df_barcelona[
                    df_barcelona['Coordinates'].notna() &  
                    df_barcelona['Coordinates'].str.contains(
                        r'^\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*$',  # Non-capturing groups
                        na=False
                    )
                ]
                # Split 'Coordinates' into 'Latitude' and 'Longitude'
                df_barcelona[['Latitude', 'Longitude']] = df_barcelona['Coordinates'].str.split(',', expand=True)
                df_barcelona['Latitude'] = pd.to_numeric(df_barcelona['Latitude'], errors='coerce')
                df_barcelona['Longitude'] = pd.to_numeric(df_barcelona['Longitude'], errors='coerce')
                df_barcelona = df_barcelona.dropna(subset=['Latitude', 'Longitude'])


                # Create markers
                markers_barcelona = [
                    dl.Marker(
                        position=(row['Latitude'], row['Longitude']),
                        children=[dl.Popup(row['Coordinates'])],  # Directly use the string instead of the hyperlink format
                        id=f"barcelona-mark2-{i}"
                    )
                    for i, row in df_barcelona.iterrows()
                    if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
                    ]
                count_within = sum(
                    polygon.contains(Point(row['Latitude'], row['Longitude']))
                    for _, row in df_barcelona.iterrows()
                    if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
                )
                
                pre_within = round(((len(df_barcelona)-count_within)/len(df_barcelona) *100),2)

                # Generate updated figures
                updated_pie_chart = generate_interactive_pie_chart_barcelona(df_barcelona)
                updated_pie_chart_weather = generate_interactive_bar_chart_weather_barcelona(df_barcelona)
                updated_bar_plot_logos = generate_interactive_bar_plot_2_barcelona(df_barcelona)
                updated_status_pie = generate_interactive_pie_chart_status(df_barcelona)

                # Update general insights
                most_common_tod_barcelona = (
                    df_barcelona['Time of the day'].mode().iloc[0]
                    if not df_barcelona['Time of the day'].dropna().mode().empty else None
                )
                most_common_terrain_barcelona = (
                    df_barcelona['Terrain'].mode().iloc[0]
                    if not df_barcelona['Terrain'].dropna().mode().empty else None
                )
                most_common_tilt_barcelona = (
                    df_barcelona['Camera tilt'].mode().iloc[0]
                    if not df_barcelona['Camera tilt'].dropna().mode().empty else None
                )

                bar_general_insights = generate_general_insights(most_common_tilt_barcelona,most_common_tod_barcelona,most_common_terrain_barcelona,avg_dur_barcelona)


                record_count_text = f"Total Records: {len(df_barcelona)}, {pre_within} % out of Polygon "



                # Return all outputs, resetting filter values to 'All' and slider to full range
                return (
                    df_barcelona.to_dict('records'),        # 1) table data
                    markers_barcelona,                      # 2) map-layer children
                    'All',                                   # 3) Terrain
                    'All',                                   # 4) Occlusion
                    'All',                                   # 5) VQ
                    'All',                                   # 6) Camera tilt
                    'All',                                   # 7) Distance building
                    record_count_text,                      # 8) record-count text
                    min_dur_barcelona,                      # 9) slider min
                    max_dur_barcelona,                      # 10) slider max
                    [min_dur_barcelona, max_dur_barcelona], # 11) slider value reset
                    updated_pie_chart,                      # 12) pie chart
                    updated_pie_chart_weather,              # 13) weather chart
                    updated_bar_plot_logos,                 # 14) logos chart
                    updated_status_pie,                     # 15) status chart
                    bar_general_insights,                       # 16) insights
                    None,                                   # 17) reset pie-chart clickData
                    None,                                   # 18) reset weather clickData
                    None,                                   # 19) reset bar-logos clickData
                    None,
                    slider_marks                            
                )

        # ---------------------------------------------------------------------
        # 2) If the Reset button was clicked
        # ---------------------------------------------------------------------
        elif triggered_id == 'barcelona-reset-btn' and reset_clicks > 0:
            # Reset df_barcelona to the full DataFrame
            df_barcelona = df_barcelona_full.copy()

            if not df_barcelona.empty:
                # Re-apply initial data processing on the full DataFrame
                first_column_name_barcelona = df_barcelona.columns[0]
                df_barcelona[first_column_name_barcelona] = df_barcelona[first_column_name_barcelona].apply(
                    lambda x: f"[{x}]({x})" if pd.notnull(x) else x
                )
                replacements = {
                    'NaN': np.nan,
                    'NULL': np.nan,
                    '': np.nan,
                }
                # Perform the same replacements you do at initial load
                for col in df_barcelona.columns[8:-1]:
                    df_barcelona[col] = df_barcelona[col].replace(replacements)
                    
                unique_occluded_barcelona_1 = ['All'] + list(df_barcelona_full['Occluded'].dropna().unique())
                unique_terrain_barcelona_1 = ['All'] + list(df_barcelona_full['Terrain'].dropna().unique())
                unique_tilt_barcelona_1 = ['All'] + list(df_barcelona_full['Camera tilt'].dropna().unique())
                unique_distance_barcelona_1 = ['All'] + list(df_barcelona_full['Distance from building'].dropna().unique())
                unique_vq_barcelona_1 = ['All'] + list(df_barcelona_full['Video quality'].dropna().unique())

                # Recalculate Duration
                df_barcelona['Duration'] = df_barcelona.apply(calculate_duration, axis=1)
                slider_marks = {
                    int(min_dur_barcelona): f"{int(min_dur_barcelona)}",
                    int((min_dur_barcelona + max_dur_barcelona) / 2): f"{int((min_dur_barcelona + max_dur_barcelona) / 2)}",
                    int(max_dur_barcelona): f"{int(max_dur_barcelona)}"
                }
                # Update general insights
                avg_dur_barcelona = round(df_barcelona['Duration'].mean(), 2)
                most_common_tod_barcelona = (
                    df_barcelona['Time of the day'].mode().iloc[0]
                    if not df_barcelona['Time of the day'].dropna().mode().empty else None
                )
                most_common_terrain_barcelona = (
                    df_barcelona['Terrain'].mode().iloc[0]
                    if not df_barcelona['Terrain'].dropna().mode().empty else None
                )
                most_common_tilt_barcelona = (
                    df_barcelona['Camera tilt'].mode().iloc[0]
                    if not df_barcelona['Camera tilt'].dropna().mode().empty else None
                )

                bar_general_insights = generate_general_insights(most_common_tilt_barcelona,most_common_tod_barcelona,most_common_terrain_barcelona,avg_dur_barcelona)

                

                df_barcelona = df_barcelona[df_barcelona['Coordinates'].notna() & df_barcelona['Coordinates'].str.contains(',')]
                df_barcelona = df_barcelona[
                    df_barcelona['Coordinates'].notna() &  
                    df_barcelona['Coordinates'].str.contains(
                        r'^\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*$',  # Non-capturing groups
                        na=False
                    )
                ]
                # Split 'Coordinates' into 'Latitude' and 'Longitude'
                df_barcelona[['Latitude', 'Longitude']] = df_barcelona['Coordinates'].str.split(',', expand=True)
                df_barcelona['Latitude'] = pd.to_numeric(df_barcelona['Latitude'], errors='coerce')
                df_barcelona['Longitude'] = pd.to_numeric(df_barcelona['Longitude'], errors='coerce')
                df_barcelona = df_barcelona.dropna(subset=['Latitude', 'Longitude'])


                markers_barcelona = [
                    dl.Marker(
                        position=(row['Latitude'], row['Longitude']),
                        children=[dl.Popup(row['Coordinates'])],  # Directly use the string instead of the hyperlink format
                        id=f"barcelona-mark3-{i}"
                    )
                    for i, row in df_barcelona.iterrows()
                    if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
                ]

                count_within = sum(
                    polygon.contains(Point(row['Latitude'], row['Longitude']))
                    for _, row in df_barcelona.iterrows()
                    if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
                )
                
                pre_within = round(((len(df_barcelona)-count_within)/len(df_barcelona) *100),2)
                # Generate updated figures
                updated_pie_chart = generate_interactive_pie_chart_barcelona(df_barcelona)
                updated_pie_chart_weather = generate_interactive_bar_chart_weather_barcelona(df_barcelona)
                updated_bar_plot_logos = generate_interactive_bar_plot_2_barcelona(df_barcelona)
                updated_status_pie = generate_interactive_pie_chart_status(df_barcelona)
                
                record_count_text = f"Total Records: {len(df_barcelona)}, {pre_within} % out of Polygon "              

                # Return all outputs, resetting filter values to 'All' and slider to full range
                return (
                    df_barcelona.to_dict('records'),        # 1) table data
                    markers_barcelona,                      # 2) map-layer children
                    'All',                                   # 3) Terrain
                    'All',                                   # 4) Occlusion
                    'All',                                   # 5) VQ
                    'All',                                   # 6) Camera tilt
                    'All',                                   # 7) Distance building
                    record_count_text,                      # 8) record-count text
                    min_dur_barcelona,                      # 9) slider min
                    max_dur_barcelona,                      # 10) slider max
                    [min_dur_barcelona, max_dur_barcelona], # 11) slider value reset
                    updated_pie_chart,                      # 12) pie chart
                    updated_pie_chart_weather,              # 13) weather chart
                    updated_bar_plot_logos,                 # 14) logos chart
                    updated_status_pie,                     # 15) status chart
                    bar_general_insights,                       # 16) insights
                    None,                                   # 17) reset pie-chart clickData
                    None,                                   # 18) reset weather clickData
                    None,                                   # 19) reset bar-logos clickData
                    None,
                    slider_marks
                )
        elif triggered_id == 'polygon_dropouts' and polygon_filter> 0:
            filtered_polygon = df_barcelona.copy()

            filtered_polygon['Duration'] = filtered_polygon.apply(calculate_duration, axis=1)

            filtered_polygon[['Latitude', 'Longitude']] = filtered_polygon['Coordinates'].str.split(',', expand=True)
            filtered_polygon['Latitude'] = pd.to_numeric(filtered_polygon['Latitude'], errors='coerce')
            filtered_polygon['Longitude'] = pd.to_numeric(filtered_polygon['Longitude'], errors='coerce')
            filtered_polygon = filtered_polygon.dropna(subset=['Latitude', 'Longitude'])

            # Filter only markers that are outside the polygon
            filtered_polygon = filtered_polygon[
                ~filtered_polygon.apply(lambda row: polygon.contains(Point(row['Latitude'], row['Longitude'])), axis=1)
            ]
            
            # Generate Markers
            markers_barcelona = [
                dl.Marker(
                    position=(row['Latitude'], row['Longitude']),
                    children=[dl.Popup(row['Coordinates'])],  # Directly use the string instead of the hyperlink format
                    id=f"barcelona-mark4-{i}"
                )
                for i, row in filtered_polygon.iterrows()
            ]
            print(markers_barcelona)
            # Update record count
            record_count_text = f"Total Records: {len(filtered_polygon)}, 100% out of Polygon"

            # Generate Updated Figures
            updated_pie_chart = generate_interactive_pie_chart_barcelona(filtered_polygon)
            updated_pie_chart_weather = generate_interactive_bar_chart_weather_barcelona(filtered_polygon)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_barcelona(filtered_polygon)
            updated_status_pie = generate_interactive_pie_chart_status(filtered_polygon)

            # Generate General Insights
            most_common_tod_barcelona = (
                filtered_polygon['Time of the day'].mode().iloc[0]
                if not filtered_polygon['Time of the day'].dropna().mode().empty else None
            )
            most_common_terrain_barcelona = (
                filtered_polygon['Terrain'].mode().iloc[0]
                if not filtered_polygon['Terrain'].dropna().mode().empty else None
            )
            most_common_tilt_barcelona = (
                filtered_polygon['Camera tilt'].mode().iloc[0]
                if not filtered_polygon['Camera tilt'].dropna().mode().empty else None
            )
            avg_dur_barcelona = (
                round(filtered_polygon['Duration'].mean(), 2)
                if 'Duration' in filtered_polygon.columns and len(filtered_polygon) > 0 else None
            )

            bar_general_insights = generate_general_insights(
                most_common_tilt_barcelona, most_common_tod_barcelona, most_common_terrain_barcelona, avg_dur_barcelona
            )
            
            slider_marks = {
                    int(min_dur_barcelona): f"{int(min_dur_barcelona)}",
                    int((min_dur_barcelona + max_dur_barcelona) / 2): f"{int((min_dur_barcelona + max_dur_barcelona) / 2)}",
                    int(max_dur_barcelona): f"{int(max_dur_barcelona)}"
                }

            return (
                filtered_polygon.to_dict('records'),   # 1) table data
                markers_barcelona,                     # 2) map-layer children
                selected_terrain,                      # 3) Terrain value
                selected_occluded,                     # 4) Occlusion value
                selected_VQ,                           # 5) VQ value
                selected_tilt,                         # 6) Camera Tilt value
                selected_distance,                     # 7) Distance Bldg value
                record_count_text,                     # 8) record-count text
                None,                                  # 9) slider min (optional)
                None,                                  # 10) slider max (optional)
                None,                                  # 11) slider value (optional)
                updated_pie_chart,                     # 12) pie chart figure
                updated_pie_chart_weather,             # 13) weather chart figure
                updated_bar_plot_logos,                # 14) bar plot figure
                updated_status_pie,                    # 15) status pie figure
                bar_general_insights,                  # 16) general insights
                pie_clickData,
                pie_weather_clickData,
                bar_2_clickData,
                status_pie_clickData,
                slider_marks  
            )

        # ---------------------------------------------------------------------
        # 3) Else: If ANY other trigger occurred (slider, dropdowns, chart clicks, etc.)
        # ---------------------------------------------------------------------
        else:
            if df_barcelona_full.empty:
                # If the full DataFrame is empty, prevent update
                raise dash.exceptions.PreventUpdate

            # Start filtering from the full DataFrame
            filtered_df = pd.DataFrame(current_data)

            # Re-apply initial data processing
            first_column_name_barcelona = filtered_df.columns[0]
            filtered_df[first_column_name_barcelona] = filtered_df[first_column_name_barcelona].apply(
                lambda x: f"[{x}]({x})" if pd.notnull(x) else x
            )
            replacements = {
                'NaN': np.nan,
                'NULL': np.nan,
                '': np.nan,
            }
            # Perform the same replacements
            for col in filtered_df.columns[8:-1]:
                filtered_df[col] = filtered_df[col].replace(replacements)

            # Recalculate Duration
            filtered_df['Duration'] = filtered_df.apply(calculate_duration, axis=1)

            filtered_df = df_barcelona[df_barcelona['Coordinates'].notna() & df_barcelona['Coordinates'].str.contains(',')]
            filtered_df = filtered_df[
                filtered_df['Coordinates'].notna() &  
                filtered_df['Coordinates'].str.contains(
                    r'^\s*-?\d+(?:\.\d+)?\s*,\s*-?\d+(?:\.\d+)?\s*$',  # Non-capturing groups
                    na=False
                )
            ]
                # Split 'Coordinates' into 'Latitude' and 'Longitude'
            filtered_df[['Latitude', 'Longitude']] = df_barcelona['Coordinates'].str.split(',', expand=True)
            filtered_df['Latitude'] = pd.to_numeric(df_barcelona['Latitude'], errors='coerce')
            filtered_df['Longitude'] = pd.to_numeric(df_barcelona['Longitude'], errors='coerce')
            filtered_df = df_barcelona.dropna(subset=['Latitude', 'Longitude'])


            # Apply Duration Slider Filter
            min_duration = duration_range[0]
            max_duration = duration_range[1]
            filtered_df = filtered_df[
                (filtered_df['Duration'] >= min_duration) &
                (filtered_df['Duration'] <= max_duration)
            ]
            
            if not filtered_df.empty:
                new_min_duration = filtered_df['Duration'].min()
                new_max_duration = filtered_df['Duration'].max()
            else:
                new_min_duration = 0
                new_max_duration = 0

            # Update slider marks based on new min and max
            if new_min_duration == new_max_duration:
                # Avoid duplicate keys in marks
                slider_marks = {
                    int(new_min_duration): f"{int(new_min_duration)}"
                }
            else:
                slider_marks = {
                    int(new_min_duration): f"{int(new_min_duration)}",
                    int((new_min_duration + new_max_duration) / 2): f"{int((new_min_duration + new_max_duration) / 2)}",
                    int(new_max_duration): f"{int(new_max_duration)}"
                }

            # Apply Dropdown Filters
            if selected_terrain != 'All':
                filtered_df = filtered_df[filtered_df['Terrain'] == selected_terrain]
            if selected_occluded != 'All':
                filtered_df = filtered_df[filtered_df['Occluded'] == selected_occluded]
            if selected_VQ != 'All':
                filtered_df = filtered_df[filtered_df['Video quality'] == selected_VQ]
            if selected_tilt != 'All':
                filtered_df = filtered_df[filtered_df['Camera tilt'] == selected_tilt]
            if selected_distance != 'All':
                filtered_df = filtered_df[filtered_df['Distance from building'] == selected_distance]

            # Apply Chart Click Filters
            if pie_clickData:
                clicked_tod = pie_clickData['points'][0]['label']
                filtered_df = filtered_df[filtered_df['Time of the day'] == clicked_tod]
            if pie_weather_clickData:
                clicked_weather = pie_weather_clickData['points'][0]['label']
                filtered_df = filtered_df[filtered_df['Weather'] == clicked_weather]
            if bar_2_clickData:
                clicked_logo = bar_2_clickData['points'][0]['x']
                filtered_df = filtered_df[filtered_df['Logos and text'] == clicked_logo]
            if status_pie_clickData:
                clicked_status = status_pie_clickData['points'][0]['label']
                filtered_df = filtered_df[filtered_df['Status'] == clicked_status]

            # Create Markers based on Filtered Data
            markers_barcelona = [
                dl.Marker(
                    position=(row['Latitude'], row['Longitude']),
                    children=[dl.Popup(row['Coordinates'])],  # Directly use the string instead of the hyperlink format
                    id=f"barcelona-mark5-{i}"
                )
                for i, row in filtered_df.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            ]

            count_within = sum(
                polygon.contains(Point(row['Latitude'], row['Longitude']))
                for _, row in filtered_df.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            )
            
            pre_within = round(((len(filtered_df)-count_within)/len(filtered_df) *100),2)
            # Update record count
            record_count_text = f"Total Records: {len(filtered_df)}, {pre_within} % out of Polygon "

            # Generate Updated Figures
            updated_pie_chart = generate_interactive_pie_chart_barcelona(filtered_df)
            updated_pie_chart_weather = generate_interactive_bar_chart_weather_barcelona(filtered_df)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_barcelona(filtered_df)
            updated_status_pie = generate_interactive_pie_chart_status(filtered_df)

            # Update General Insights
            most_common_tod_barcelona = (
                filtered_df['Time of the day'].mode().iloc[0]
                if not filtered_df['Time of the day'].dropna().mode().empty else None
            )
            most_common_terrain_barcelona = (
                filtered_df['Terrain'].mode().iloc[0]
                if not filtered_df['Terrain'].dropna().mode().empty else None
            )
            most_common_tilt_barcelona = (
                filtered_df['Camera tilt'].mode().iloc[0]
                if not filtered_df['Camera tilt'].dropna().mode().empty else None
            )
            avg_dur_barcelona = (
                round(filtered_df['Duration'].mean(), 2)
                if 'Duration' in filtered_df.columns and len(filtered_df) > 0 else None
            )

            bar_general_insights = generate_general_insights(most_common_tilt_barcelona,most_common_tod_barcelona,most_common_terrain_barcelona,avg_dur_barcelona)

            # Update slider marks dynamically if needed
            slider_marks = {
                int(min_dur_barcelona): str(int(min_dur_barcelona)),
                int(max_dur_barcelona): str(int(max_dur_barcelona))
            }

            # Return all outputs with current filter selections
            return (
                filtered_df.to_dict('records'),   # 1) table data
                markers_barcelona,                # 2) map-layer children
                selected_terrain,                 # 3) Terrain value
                selected_occluded,                # 4) Occlusion value
                selected_VQ,                      # 5) VQ value
                selected_tilt,                    # 6) Camera Tilt value
                selected_distance,                # 7) Distance Bldg value
                record_count_text,                # 8) record-count text
                min_dur_barcelona,                # 9) slider min
                max_dur_barcelona,                # 10) slider max
                duration_range,                   # 11) slider value
                updated_pie_chart,                # 12) pie chart figure
                updated_pie_chart_weather,        # 13) weather chart figure
                updated_bar_plot_logos,           # 14) bar plot figure
                updated_status_pie,               # 15) status pie figure
                bar_general_insights,                 # 16) general insights
                pie_clickData,
                pie_weather_clickData,
                bar_2_clickData,
                status_pie_clickData,
                slider_marks  
            )

    except Exception as e:
        print(f"Error: {e}")
        raise dash.exceptions.PreventUpdate

#Milan load data

def load_milan_data():
    # Google Sheet ID and Range for Madrid
    SHEET_ID_Milan = '1NdmXJluL5VrDj28d6iHV58LvkK5Gvly3_MYH1eBJeIQ'
    RANGE_Milan = 'Milan!A1:S150'

    # Access the Google Sheet for Madrid
    result = sheet.values().get(spreadsheetId=SHEET_ID_Milan, range=RANGE_Milan).execute()
    values = result.get('values', [])

    # Convert the data to a pandas DataFrame
    if values:
        headers = values[0]  # Assuming the first row is the header
        data = values[1:]    # Rest is the data
        df_milan = pd.DataFrame(data, columns=headers)
    else:
        print("No data found for Milan.")
        df_milan = pd.DataFrame()

    return df_milan

# Load the full DataFrame
df_milan_full = load_milan_data()

# Create a copy for initial display and filtering
df_milan = df_milan_full.copy()

# ---------------------------- Initial Data Processing ----------------------------
# Process Barcelona Data
if not df_milan.empty:
    first_column_name_milan = df_milan.columns[0]
    df_milan[first_column_name_milan] = df_milan[first_column_name_milan].apply(
        lambda x: f"[{x}]({x})" if pd.notnull(x) else x
    )



    # Convert 'Duration' column
    df_milan['Duration'] = df_milan.apply(calculate_duration, axis=1)

    # Extract unique values for filters
    unique_tod_milan = df_milan['Time of the day'].dropna().unique()
    unique_weather_milan = df_milan['Weather'].dropna().unique()
    unique_terrain_milan = df_milan['Terrain'].dropna().unique()
    unique_occluded_milan = df_milan['Occluded'].dropna().unique()
    unique_tilt_milan = df_milan['Camera tilt'].dropna().unique()
    unique_distance_milan = df_milan['Distance from building'].dropna().unique()
    unique_vq_milan = df_milan['Video quality'].dropna().unique()

    # Determine most common values
    most_common_tod_milan = df_milan['Time of the day'].mode().iloc[0] if not df_milan['Time of the day'].dropna().mode().empty else None
    most_common_terrain_milan = df_milan['Terrain'].mode().iloc[0] if not df_milan['Terrain'].dropna().mode().empty else None
    most_common_tilt_milan = df_milan['Camera tilt'].mode().iloc[0] if not df_milan['Camera tilt'].dropna().mode().empty else None

    # Calculate duration statistics
    avg_dur_milan = round(df_milan['Duration'].mean(), 2)
    min_dur_milan = df_milan['Duration'].min()
    max_dur_milan = df_milan['Duration'].max()
    

    # Define color maps
    color_map_milan = {
        'Youtube': 'rgb(255,0,0)',
        'tiktok': 'rgb(255,182,193)',
        'facebook': 'rgb(30,144,255)',
        'other': 'rgb(112,128,144)'
    }
    color_map2_milan = {
        'Night Time': 'rgb(1, 1, 1)',      # Black
        'Day Time': 'rgb(236, 255, 0)'
    }

    color_map3_milan = {
        'Clear': 'rgb(135,206,235)',
        'Snow': 'rgb(255,250,250)',
        'Rain': 'rgb(123,104,238)',
        'Fog or Smoke': 'rgb(128,128,128)'
    }

    # Define background style
    background_style_milan = {
        "background-size": "cover",
        "background-position": "center",
        "height": "250vh",
        "padding": "10px",
        "background-color": 'black',
    }

    # Define filter options with 'All'
    unique_occluded_milan_1 = ['All'] + list(unique_occluded_milan)
    unique_terrain_milan_1 = ['All'] + list(unique_terrain_milan)
    unique_tilt_milan_1 = ['All'] + list(unique_tilt_milan)
    unique_distance_milan_1 = ['All'] + list(unique_distance_milan)
    unique_vq_milan_1 = ['All'] + list(unique_vq_milan)
    

    if not df_milan['Coordinates'].empty:
        # Split 'Coordinates' into 'Latitude' and 'Longitude'
        df_milan[['Latitude', 'Longitude']] = df_milan['Coordinates'].str.split(',', expand=True)
        df_milan['Latitude'] = pd.to_numeric(df_milan['Latitude'], errors='coerce')
        df_milan['Longitude'] = pd.to_numeric(df_milan['Longitude'], errors='coerce')
        df_milan = df_milan.dropna(subset=['Latitude', 'Longitude'])



    # Get the integer index of the "Raw File Name" column

    # Create Map Markers
    markers_milan = [
        dl.Marker(
            position=(row['Latitude'], row['Longitude']),
            children=[dl.Popup(row['Coordinates'])],  # Directly use the string instead of the hyperlink format
            id=f"milan-mark-{i}"
        )
        for i, row in df_milan.iterrows()
        if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
    ]

    global milan_polygon
    global polygon_milan
    
    file_path_pm= 'milan_coord.txt'
    
    milan_polygon =[]
    with open (file_path_pm, "r") as file:
        for line in file:
            match = re.findall(r"[-+]?\d*\.\d+", line)  # Extract floating point numbers
            if match:
                milan_polygon.append([float(match[0]), float(match[1])]) 
    polygon_milan = Polygon(milan_polygon)
    count_within_milan = sum(
        polygon_milan.contains(Point(row['Latitude'], row['Longitude']))
        for _, row in df_milan.iterrows()
        if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
    )

    pre_out_milan = round(((len(df_milan)-count_within_milan)/len(df_milan) *100),2)   
     
    def generate_interactive_bar_plot_2_milan(df):
            source_counts = df['Logos and text'].value_counts().reset_index()
            source_counts.columns = ['Logos and text', 'Count']

            fig = px.bar(
                source_counts, 
                x='Logos and text', 
                y='Count', 
                color='Logos and text', 
                color_discrete_map=color_map2_milan,
                title='Logos and text Distribution'
            )
            fig.update_traces(
                marker_line_width=1.5, 
                hovertemplate="Count: %{y}", 
                textfont=dict(size=22)
            )
            fig.update_layout(
                xaxis_title="Logos and text", 
                yaxis_title="Count", 
                showlegend=False,
                hovermode="x unified",
                font=dict(size=16, color='white'),
                plot_bgcolor='black',
                paper_bgcolor='black',
                title_font=dict(color='white'),
                xaxis=dict(
                    color='white',
                    gridcolor='gray',
                    zerolinecolor='gray',
                    title_font=dict(color='white'),
                    tickfont=dict(color='white')
                ),
                yaxis=dict(
                    color='white',
                    gridcolor='gray',
                    zerolinecolor='gray',
                    title_font=dict(color='white'),
                    tickfont=dict(color='white')
                ),
                hoverlabel=dict(font=dict(size=24, color='white'))
            )

            return fig

    def generate_interactive_pie_chart_milan(df):
        tod_counts = df['Time of the day'].value_counts().reset_index()
        tod_counts.columns = ['Time of the day', 'Count']

        fig = px.pie(
            tod_counts,
            names='Time of the day',
            values='Count',
            color='Time of the day',
            color_discrete_map=color_map2_milan,
            title='Time of the day'
        )

        depth_values = [0.05 + i * 0.01 for i in range(len(tod_counts))]
        fig.update_traces(
            marker=dict(line=dict(color='white', width=2)),
            pull=depth_values,
            textinfo='label',
            textfont=dict(color='yellow', size=22)  
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

    def generate_interactive_bar_chart_weather_milan(df):
        # Calculate the counts for each Weather category
        weather_counts = df['Weather'].value_counts().reset_index()
        weather_counts.columns = ['Weather', 'Count']

        # Create a horizontal bar chart
        fig = px.bar(
            weather_counts,
            y='Weather',
            x='Count',
            orientation='h',  # Horizontal bars
            color='Weather',
            color_discrete_map=color_map3_milan,
            title='Weather'
        )

        # Customize the bar traces
        fig.update_traces(
            marker_line_width=1.5,
            hovertemplate="Count: %{x}",
            textfont=dict(size=22)
        )

        # Update layout for black background, fonts, etc.
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
                color='white',
                gridcolor='gray',
                zerolinecolor='gray',
                title_font=dict(color='white'),
                tickfont=dict(color='white')
            ),
            yaxis=dict(
                color='white',
                gridcolor='gray',
                zerolinecolor='gray',
                title_font=dict(color='white'),
                tickfont=dict(color='white')
            ),
            margin=dict(t=40, b=20, l=0, r=0),
            hoverlabel=dict(font=dict(size=24, color='white'))
        )

        return fig

    def generate_interactive_pie_chart_source(df):
        color_map = {
            'done': '#006400',
            'not started': '#FF0000',
            'not found': '#DC143C',
            'irrelevant': '#00FFFF'
        }

        # Ensure that only the Status column is used for value_counts
        source_counts = df['Source'].value_counts().reset_index()
        source_counts.columns = ['Source', 'Count']

        # Map a color to each status
        fig = px.pie(
            source_counts,
            names='Source',
            values='Count',
            color='Source',
            color_discrete_map=color_map_milan,
            title='Source Distribution'
        )

        # Add depth to the slices
        depth_values = [0.05 + i * 0.01 for i in range(len(source_counts))]
        fig.update_traces(
            marker=dict(line=dict(color='white', width=2)),
            pull=depth_values,
            textinfo='label',
            textfont=dict(color='yellow', size=22)  
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

    # Generate Initial Figures
    pie_chart_initial = generate_interactive_pie_chart_milan(df_milan)
    bar_chart_weather_initial = generate_interactive_bar_chart_weather_milan(df_milan)
    bar_plot_logos_initial = generate_interactive_bar_plot_2_milan(df_milan)
    source_pie_initial = generate_interactive_pie_chart_source(df_milan)    
    
def tab5_layout():
    return html.Div(
        style=background_style_milan,
        children=[  
            dcc.ConfirmDialog(
                id='milan-confirm-dialog',
                message="The data has refreshed successfully!"
            ),
            html.Img(
                src="/assets/airis.png", 
                alt="Airis Logo", 
                style={
                    "width": "200px", 
                    "position": "absolute",  # Absolute positioning
                    "top": "80px",          # Distance from the top of the page
                    "left": "10px",         # Distance from the left of the page
                    "zIndex": "1000"        # Ensures it stays above other elements
                }
            ), 
            dcc.Store(id='milan-data', data=df_milan.to_dict('records')),
            dcc.Store(id='milan-polygon-filter-active', data=False),
            dcc.Store(id='milan-filtered-data',data=None),
            dbc.Container(
                style=container_style,
                children=[
                    # Title
                    html.H1(
                        "Airis-Labs: Geo-Location Analysis - Milan",
                        className='mb-4',
                        style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}
                    ),
                    # Map and Filters Section
                    dbc.Row([
                        # Map on the left
                            dbc.Col(
                                dl.Map(
                                    [
                                        dl.TileLayer(),
                                        # Layer group for markers
                                        dl.LayerGroup(id="milan-map-layer", children=markers_milan),
                                        # Separate layer group for polygon
                                        dl.LayerGroup(
                                            id="polygon-layer_milan",
                                            children=[
                                                dl.Polygon(
                                                    positions=milan_polygon,
                                                    color="blue",
                                                    fillColor="cyan",
                                                    fillOpacity=0.6,
                                                )
                                            ]
                                        ),
                                    ],
                                    center=(45.463832, 9.185091),  # milan coordinates
                                    zoom=10,
                                    style={"width": "100%", "height": "500px", "margin": "6px"}
                                ),
                                width=8
                            ),
                        # Filters on the right
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H4(
                                            "Filters",
                                            className='mb-3',
                                            style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                                        ),
                                        dbc.Label("Terrain Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='milan-Terrain',
                                            options=[{'label': k, 'value': k} for k in unique_terrain_milan_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Camera Tilt Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='milan-Camera_Tilt',
                                            options=[{'label': k, 'value': k} for k in unique_tilt_milan_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Occlusion Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='milan-Occlusion',
                                            options=[{'label': k, 'value': k} for k in unique_occluded_milan_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Video Quality Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='milan-VQ',
                                            options=[{'label': k, 'value': k} for k in unique_vq_milan_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Distance Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='milan-Distance_Building',
                                            options=[{'label': k, 'value': k} for k in unique_distance_milan_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Reset Filters",
                                                        id='milan-reset-btn',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style
                                                    ),
                                                    width="auto"
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Update DB",
                                                        id='milan-update',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style15
                                                    ),
                                                    width="auto"
                                                ),
                                            ],
                                        ),
                                    ],
                                    style={"marginBottom": "30px"}
                                ),
                            ],
                            width=4
                        ),
                    ]),
                    # Record Count
                    html.H1(
                        id='milan-record-count',
                        children=f"Total Records: {len(df_milan)}, {pre_out_milan} % out of Polygon ",
                        style={'textAlign': 'left', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    dbc.Button("Show Which Ones",id='polygon_dropouts_milan', color='primary',n_clicks=0,style=button_polygon),
                    # Duration Slider Section (below the map)
                    html.Br(),
                    html.H4(
                        "Filter by Video Duration (seconds):",
                        className='mb-1',
                        style={'textAlign': 'left', 'color': 'rgb(255,51,153)', 'marginBottom': '0'}
                    ),
                    dbc.Row(
                        dbc.Col(
                            dcc.RangeSlider(
                                id='milan-duration-slider',
                                min=min_dur_milan if not df_milan.empty else 0,
                                max=max_dur_milan if not df_milan.empty else 100,
                                step=0.1,
                                value=[min_dur_milan, max_dur_milan] if not df_milan.empty else [0, 100],
                                updatemode='mouseup',
                                marks={
                                    int(min_dur_milan): str(int(min_dur_milan)),
                                    int(max_dur_milan): str(int(max_dur_milan))
                                } if not df_milan.empty else {},
                                tooltip={"always_visible": True, "placement": "bottom"}
                            ),
                            width=8
                        ),
                        justify="left"
                    ),
                    # Graphs Section
                    html.Div(
                        [
                            html.H4(
                                "Graphical Analysis",
                                className='mb-3',
                                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                            ),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Graph(id='milan-pie-chart', figure=pie_chart_initial),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Graph(id='milan-bar-chart-weather', figure=bar_chart_weather_initial),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                                dbc.Col(
                                    dcc.Graph(id='milan-bar-plot-logos', figure=bar_plot_logos_initial),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                                dbc.Col(
                                    dcc.Graph(id='milan-source-pie', figure=source_pie_initial),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),                                
                                
                            ]),
                        ],
                        style={'marginTop': '20px'}
                    ),
                    # General Insights Section
                    html.Div(
                        id='milan-general-insights',
                        children=general_insights_initial,
                        style={'padding': '10px'}
                    ),
                    # Full Details Section
                    html.Div(
                        [
                            html.H1("Full Details:", className='mb-4', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}),
                            html.Hr(),
                            dash_table.DataTable(
                                id='milan-table',
                                columns=[
                                    {"name": first_column_name_milan, "id": first_column_name_milan, "presentation": "markdown"}
                                ] + [{"name": i, "id": i} for i in df_milan.columns[1:]] if not df_milan.empty else [],
                                data=df_milan.to_dict('records') if not df_milan.empty else [],
                                sort_action="native",
                                filter_action="native",
                                fixed_rows={'headers': True},
                                style_table={'maxHeight': '500px',
                                            'overflowX': 'auto',
                                             'overflowY': 'auto'},
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
                                style_data_conditional=[
                                    {
                                        'if': {'column_id': 'Status'},
                                        'backgroundColor': 'rgb(220, 220, 220)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Active"'},
                                        'backgroundColor': 'rgb(85, 255, 85)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Inactive"'},
                                        'backgroundColor': 'rgb(255, 85, 85)',
                                        'color': 'white'
                                    },
                                ],
                            ),
                        ]
                    ),
                ]
            )
        ]
    )
    

@app.callback(
    [
        Output('milan-table', 'data'),
        Output('milan-map-layer', 'children'),
        Output('milan-Terrain', 'value'),
        Output('milan-Occlusion', 'value'),
        Output('milan-VQ', 'value'),
        Output('milan-Camera_Tilt', 'value'),
        Output('milan-Distance_Building', 'value'),
        Output('milan-record-count', 'children'),
        Output('milan-duration-slider', 'min'),
        Output('milan-duration-slider', 'max'),
        Output('milan-duration-slider', 'value'),
        Output('milan-pie-chart', 'figure'),
        Output('milan-bar-chart-weather', 'figure'),
        Output('milan-bar-plot-logos', 'figure'),
        Output('milan-source-pie','figure'),
        Output('milan-general-insights', 'children'),
        Output('milan-pie-chart', 'clickData'),
        Output('milan-bar-chart-weather', 'clickData'),
        Output('milan-bar-plot-logos', 'clickData'),
        Output('milan-source-pie','clickData'),
        Output('milan-polygon-filter-active', 'data'),
        Output('milan-filtered-data','data'),   # <--- NEW OUTPUT to store the filtered df
    ],
    [
        Input('milan-pie-chart', 'clickData'),
        Input('milan-bar-chart-weather', 'clickData'),
        Input('milan-bar-plot-logos', 'clickData'),
        Input('milan-source-pie','clickData'),
        Input('milan-reset-btn', 'n_clicks'),
        Input('milan-update', 'n_clicks'),
        Input('milan-duration-slider', 'value'),
        Input('milan-Terrain', 'value'),
        Input('milan-Occlusion', 'value'),
        Input('milan-VQ', 'value'),
        Input('milan-Camera_Tilt', 'value'),
        Input('milan-Distance_Building', 'value'),
        Input('polygon_dropouts_milan', "n_clicks"),
    ],
    [
        State('milan-data','data'),
        State('milan-polygon-filter-active', 'data'),
        State('milan-filtered-data', 'data'),  # <--- NEW STATE for the previously filtered df

  # <--- NEW STATE for the previously filtered df
    ]
)
def handle_table_and_refresh_milan(
    pie_clickData, bar_weather_clickData,bar_clickData, pie2_clickData, 
    reset_clicks, update_clicks, duration_range,
    selected_terrain, selected_occluded, selected_VQ, selected_tilt, selected_distance,
    milan_polygon_button,
    # States
    original_data,milan_polygon_active,stored_filtered_data
):

    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None

    if stored_filtered_data is not None and triggered_id != 'milan-reset-btn.n_clicks':
        # Start from the previously filtered subset
        df_current = pd.DataFrame(stored_filtered_data)
    else:
        df_current = pd.DataFrame(original_data)

    # Ensure Coordinates are split into lat/long if not already
    if 'Coordinates' in df_current.columns:
        df_current = df_current[df_current['Coordinates'].str.contains(',', na=False)]
        df_current[['Latitude', 'Longitude']] = df_current['Coordinates'].str.split(',', expand=True)
        df_current['Latitude'] = pd.to_numeric(df_current['Latitude'], errors='coerce')
        df_current['Longitude'] = pd.to_numeric(df_current['Longitude'], errors='coerce')

    # Compute or recompute Duration if needed
    if 'Duration' not in df_current.columns:
        df_current['Duration'] = df_current['Finish Time'].apply(convert_to_minutes) - \
                                 df_current['Start Time'].apply(convert_to_minutes)

    markers_milan = create_map_markers(df_current)
    
    # Drop any rows with invalid coords
    df_current.dropna(subset=['Latitude', 'Longitude'], inplace=True)

    global min_dur_milan, max_dur_milan  # If you rely on these globally

    min_dur_milan = df_current['Duration'].min()
    max_dur_milan = df_current['Duration'].max()

    # polygon_milan should be globally defined or imported from somewhere
    # for checking .contains(Point(row['Latitude'], row['Longitude']))

    # ------------------------------------------------------------------------
    # STEP 2: Handle each triggered event
    # ------------------------------------------------------------------------

    # 2.1 "UPDATE" button - re-load from original source, but keep current filters
    if triggered_id == 'milan-update.n_clicks' and update_clicks > 0:
        # Re-load data from your source
        df_updated = load_milan_data()
        # Same prep steps (split coords, compute Duration, drop invalid coords, etc.)
        df_updated['Duration'] = df_updated['Finish Time'].apply(convert_to_minutes) - \
                                 df_updated['Start Time'].apply(convert_to_minutes)
        df_updated = df_updated[df_updated['Coordinates'].str.contains(',', na=False)]
        df_updated[['Latitude', 'Longitude']] = df_updated['Coordinates'].str.split(',', expand=True)
        df_updated['Latitude'] = pd.to_numeric(df_updated['Latitude'], errors='coerce')
        df_updated['Longitude'] = pd.to_numeric(df_updated['Longitude'], errors='coerce')
        df_updated.dropna(subset=['Latitude', 'Longitude'], inplace=True)

        # Now apply the current user filters to the newly updated data
        filtered_df = apply_all_filters2(
            df=df_updated,
            duration_range=duration_range,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            bar_weather_clickData=bar_weather_clickData,
            pie_clickData=pie_clickData,
            pie_2_clickData=pie2_clickData,
            bar_2_clickData=bar_clickData,
            milan_polygon_active = milan_polygon_active
        )

        # Create map markers
        markers_milan = create_map_markers(filtered_df)
        count_within_milan = sum(
            polygon_milan.contains(Point(row['Latitude'], row['Longitude']))
            for _, row in filtered_df.iterrows()
            if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
        )

        pre_out_milan = round(((len(filtered_df)-count_within_milan)/len(filtered_df) *100),2)   

        record_count_text = f"Total Records: {len(filtered_df)},{pre_out_milan} % out of polygon "

        original_data = filtered_df.copy()
    
        # Build / refresh graphs
        updated_pie = generate_interactive_pie_chart_milan(filtered_df)
        updated_bar_weather = generate_interactive_bar_chart_weather_milan(filtered_df)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_milan(filtered_df)
        updated_source_pie = generate_interactive_pie_chart_source(filtered_df)

        # Build general insights
        general_insights = build_general_insights_div(filtered_df)

        # Return and also store filtered data in 'milan-filtered-data'
        return (
            filtered_df.to_dict('records'),
            markers_milan,  # map-layer - if you want the new markers, see below
            dash.no_update,  # Terrain
            dash.no_update,  # Occlusion
            dash.no_update,  # VQ
            dash.no_update,  # Tilt
            dash.no_update,  # Distance building
            record_count_text,
            filtered_df['Duration'].min(),
            filtered_df['Duration'].max(),
            duration_range,  # keep slider the same
            updated_pie,
            updated_bar_weather,
            updated_bar_plot_logos,
            updated_source_pie,
            general_insights,
            None, None, None, None,
            milan_polygon_active,
            filtered_df.to_dict('records'),  # <--- store updated data
        )

    elif triggered_id == 'polygon_dropouts_milan.n_clicks' and milan_polygon_button > 0:
        # Indicate that polygon filter is now active
        milan_polygon_active = True

        # Start from df_current and remove in-polygon points
        filtered_polygon = df_current.copy()

        # Re-apply standard filters (duration, etc.) if needed
        # (You can do it before or after removing in-polygon points, 
        #  but typically you want them all together.)
        filtered_polygon = apply_all_filters2(
            df=filtered_polygon,
            duration_range=duration_range,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            bar_weather_clickData=bar_weather_clickData,
            pie_clickData=pie_clickData,
            pie_2_clickData=pie2_clickData,
            bar_2_clickData=bar_clickData,
            milan_polygon_active = milan_polygon_active # Because we'll remove them below
        )

        # Now remove points *inside* the polygon
        filtered_polygon = filtered_polygon[
            ~filtered_polygon.apply(
                lambda row: polygon_milan.contains(Point(row['Latitude'], row['Longitude'])), 
                axis=1
            )
        ]

        # Build map markers
        markers_milan = create_map_markers(filtered_polygon)

        # Build Figures
        updated_pie = generate_interactive_pie_chart_milan(filtered_polygon)
        updated_bar_weather = generate_interactive_bar_chart_weather_milan(filtered_polygon)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_milan(filtered_polygon)
        updated_source_pie = generate_interactive_pie_chart_source(filtered_polygon)  

        # Build general insights
        general_insights = build_general_insights_div(filtered_polygon)

        record_count_text = f"Total Records: {len(filtered_polygon)}, 100% out of Polygon"

        return (
            filtered_polygon.to_dict('records'),
            markers_milan,
            selected_terrain,
            selected_occluded,
            selected_VQ,
            selected_tilt,
            selected_distance,
            record_count_text,
            filtered_polygon['Duration'].min(),
            filtered_polygon['Duration'].max(),
            duration_range,
            updated_pie,
            updated_bar_weather,
            updated_bar_plot_logos,
            updated_source_pie,
            general_insights,
            pie_clickData,
            bar_clickData,
            bar_weather_clickData,
            pie2_clickData,
            milan_polygon_active,
            filtered_polygon.to_dict('records'),  # <--- store the polygon-filtered df
        )
    # 2.3 "RESET" button
    elif triggered_id == 'milan-reset-btn.n_clicks':
        # Reset everything to the original data
        df_reset = load_milan_data()
        # Same prep steps (split coords, compute Duration, drop invalid coords, etc.)
        df_reset['Duration'] = df_reset['Finish Time'].apply(convert_to_minutes) - \
                                 df_reset['Start Time'].apply(convert_to_minutes)
        df_reset = df_reset[df_reset['Coordinates'].str.contains(',', na=False)]
        df_reset[['Latitude', 'Longitude']] = df_reset['Coordinates'].str.split(',', expand=True)
        df_reset['Latitude'] = pd.to_numeric(df_reset['Latitude'], errors='coerce')
        df_reset['Longitude'] = pd.to_numeric(df_reset['Longitude'], errors='coerce')
        df_reset.dropna(subset=['Latitude', 'Longitude'], inplace=True)
        milan_polygon_active = False

        # Create map markers
        markers_milan = create_map_markers(df_reset)

        count_within_milan = sum(
            polygon_milan.contains(Point(row['Latitude'], row['Longitude']))
            for _, row in df_reset.iterrows()
            if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
        )

        pre_out_milan = round(((len(df_reset)-count_within_milan)/len(df_reset) *100),2)   

        record_count_text = f"Total Records: {len(df_reset)},{pre_out_milan} % out of polygon "


        # Build graphs
        updated_pie = generate_interactive_pie_chart_milan(df_reset)
        updated_bar_chart = generate_interactive_bar_chart_weather_milan(df_reset)
        updated_bar_chart_weather = generate_interactive_bar_plot_2_milan(df_reset)
        updated_pie_2 = generate_interactive_pie_chart_source(df_reset)

        # General insights
        general_insights = build_general_insights_div(df_reset)

        return (
            df_reset.to_dict('records'),
            markers_milan,
            'All',       # reset Terrain
            'All',       # reset Occlusion
            'All',       # reset VQ
            'All',       # reset Camera Tilt
            'All',       # reset Distance from building
            record_count_text,
            df_reset['Duration'].min(),
            df_reset['Duration'].max(),
            [df_reset['Duration'].min(), df_reset['Duration'].max()],
            updated_pie,
            updated_bar_chart,
            updated_bar_chart_weather,
            updated_pie_2,
            general_insights,
            None, None, None, None,
            milan_polygon_active,
            df_reset.to_dict('records')  ,  # <--- store data as None or the full df again, your choice
        )

    # 2.4 DEFAULT branch: user changed dropdowns, slider, or clicked bar/pie but not polygon filter
    #     We just apply all filters on df_current
    else:
        filtered_df = apply_all_filters2(
            df=df_current,
            duration_range=duration_range,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            bar_weather_clickData=bar_weather_clickData,
            pie_clickData=pie_clickData,
            pie_2_clickData=pie2_clickData,
            bar_2_clickData=bar_clickData,
            milan_polygon_active=milan_polygon_active
        )


        if milan_polygon_active:
            filtered_df = filtered_df[
                ~filtered_df.apply(
                    lambda row: polygon_milan.contains(Point(row['Latitude'], row['Longitude'])), 
                    axis=1
                )
            ]

        # Create map markers
        markers_milan = create_map_markers(filtered_df)
        count_within_milan = sum(
            polygon_milan.contains(Point(row['Latitude'], row['Longitude']))
            for _, row in filtered_df.iterrows()
            if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
        )
        if count_within_milan > 0:
            pre_out_milan = round(((len(filtered_df)-count_within_milan)/len(filtered_df) *100),2)           
            record_count_text = f"Total Records: {len(filtered_df)}, {pre_out_milan} % out of polygon"
        else:   
            record_count_text = f"Total Records: {len(filtered_df)}, 0.0 % out of polygon" 
        # Refresh graphs
        updated_pie = generate_interactive_pie_chart_milan(filtered_df)
        updated_bar_weather = generate_interactive_bar_chart_weather_milan(filtered_df)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_milan(filtered_df)
        updated_source_pie = generate_interactive_pie_chart_source(filtered_df)  

        # Insights
        general_insights = build_general_insights_div(filtered_df)

        return (
            filtered_df.to_dict('records'),
            markers_milan,
            selected_terrain,
            selected_occluded,
            selected_VQ,
            selected_tilt,
            selected_distance,
            record_count_text,
            filtered_df['Duration'].min(),
            filtered_df['Duration'].max(),
            duration_range,
            updated_pie,
            updated_bar_weather,
            updated_bar_plot_logos,
            updated_source_pie,
            general_insights,
            pie_clickData,
            bar_clickData,
            bar_weather_clickData,
            pie2_clickData,
            milan_polygon_active,
            filtered_df.to_dict('records'),  # <--- store final filtered df
        )
       
def load_budapest_data():
    # Google Sheet ID and Range for Madrid
    SHEET_ID_budapest = '1_PklSnn0Bkc0Vdpi9B-9JVuDuEe8DZApnesxe3ehxD0'
    RANGE_budapest = 'Budapest!A1:S350'

    # Access the Google Sheet for Madrid
    result = sheet.values().get(spreadsheetId=SHEET_ID_budapest, range=RANGE_budapest).execute()
    values = result.get('values', [])

    # Convert the data to a pandas DataFrame
    if values:
        headers = values[0]  # Assuming the first row is the header
        data = values[1:]    # Rest is the data
        df_budapest = pd.DataFrame(data, columns=headers)
    else:
        print("No data found for budapest.")
        df_budapest = pd.DataFrame()

    return df_budapest

# Load the full DataFrame
df_budapest_full = load_budapest_data()

# Create a copy for initial display and filtering
df_budapest = df_budapest_full.copy()

# ---------------------------- Initial Data Processing ----------------------------
# Process Barcelona Data
if not df_budapest.empty:
    first_column_name_budapest = df_budapest.columns[0]
    df_budapest[first_column_name_budapest] = df_budapest[first_column_name_budapest].apply(
        lambda x: f"[{x}]({x})" if pd.notnull(x) else x
    )

    df_budapest['Comments'] = df_budapest['Comments'].fillna("No Comment")  # Replace NaN with "No Comment"

    # Step 2: Drop NaN values from all other columns
    df_budapest = df_budapest.dropna(subset=[col for col in df_budapest.columns if col != 'Comments'])

    # Convert 'Duration' column
    df_budapest['Duration'] = df_budapest.apply(calculate_duration, axis=1)

    # Extract unique values for filters
    unique_tod_budapest = df_budapest['Time of the day'].dropna().unique()
    unique_weather_budapest = df_budapest['Weather'].dropna().unique()
    unique_terrain_budapest = df_budapest['Terrain'].dropna().unique()
    unique_occluded_budapest = df_budapest['Occluded'].dropna().unique()
    unique_tilt_budapest = df_budapest['Camera tilt'].dropna().unique()
    unique_distance_budapest = df_budapest['Distance from building'].dropna().unique()
    unique_vq_budapest = df_budapest['Video quality'].dropna().unique()

    # Determine most common values
    most_common_tod_budapest = df_budapest['Time of the day'].mode().iloc[0] if not df_budapest['Time of the day'].dropna().mode().empty else None
    most_common_terrain_budapest = df_budapest['Terrain'].mode().iloc[0] if not df_budapest['Terrain'].dropna().mode().empty else None
    most_common_tilt_budapest = df_budapest['Camera tilt'].mode().iloc[0] if not df_budapest['Camera tilt'].dropna().mode().empty else None

    # Calculate duration statistics
    avg_dur_budapest = round(df_budapest['Duration'].mean(), 2)
    min_dur_budapest = df_budapest['Duration'].min()
    max_dur_budapest = df_budapest['Duration'].max()
    

    # Define color maps
    color_map_budapest = {
        'Youtube': 'rgb(255,0,0)',
        'tiktok': 'rgb(255,182,193)',
        'facebook': 'rgb(30,144,255)',
        'other': 'rgb(112,128,144)'
    }
    color_map2_budapest = {
        'Night Time': 'rgb(1, 1, 1)',      # Black
        'Day Time': 'rgb(236, 255, 0)'
    }

    color_map3_budapest = {
        'Clear': 'rgb(135,206,235)',
        'Snow': 'rgb(255,250,250)',
        'Rain': 'rgb(123,104,238)',
        'Fog or Smoke': 'rgb(128,128,128)'
    }

    # Define background style
    background_style_budapest = {
        "background-size": "cover",
        "background-position": "center",
        "height": "250vh",
        "padding": "10px",
        "background-color": 'black',
    }

    # Define filter options with 'All'
    unique_occluded_budapest_1 = ['All'] + list(unique_occluded_budapest)
    unique_terrain_budapest_1 = ['All'] + list(unique_terrain_budapest)
    unique_tilt_budapest_1 = ['All'] + list(unique_tilt_budapest)
    unique_distance_budapest_1 = ['All'] + list(unique_distance_budapest)
    unique_vq_budapest_1 = ['All'] + list(unique_vq_budapest)
    

    if not df_budapest['Coordinates'].empty:
        # Split 'Coordinates' into 'Latitude' and 'Longitude'
        df_budapest[['Latitude', 'Longitude']] = df_budapest['Coordinates'].str.split(',', expand=True)
        df_budapest['Latitude'] = pd.to_numeric(df_budapest['Latitude'], errors='coerce')
        df_budapest['Longitude'] = pd.to_numeric(df_budapest['Longitude'], errors='coerce')
        df_budapest = df_budapest.dropna(subset=['Latitude', 'Longitude'])



    # Get the integer index of the "Raw File Name" column

    # Create Map Markers
    markers_budapest = [
        dl.Marker(
            position=(row['Latitude'], row['Longitude']),
            children=[dl.Popup(row['Coordinates'])],  # Directly use the string instead of the hyperlink format
            id=f"budapest-mark-{i}"
        )
        for i, row in df_budapest.iterrows()
        if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
    ]

    global budapest_polygon
    global polygon_budapest
    
    file_path_pb= 'budapest coord.txt'
    
    budapest_polygon =[]
    with open (file_path_pb, "r") as file_bud:
        for line in file_bud:
            match = re.findall(r"[-+]?\d*\.\d+", line)  # Extract floating point numbers
            if match:
                budapest_polygon.append([float(match[0]), float(match[1])]) 

    polygon_budapest = Polygon(budapest_polygon)
    count_within_budapest = sum(
        polygon_budapest.contains(Point(row['Latitude'], row['Longitude']))
        for _, row in df_budapest.iterrows()
        if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
    )

    pre_out_budapest = round(((len(df_budapest)-count_within_budapest)/len(df_budapest) *100),2)   
     
    def generate_interactive_bar_plot_2_budapest(df):
            source_counts = df['Logos and text'].value_counts().reset_index()
            source_counts.columns = ['Logos and text', 'Count']

            fig = px.bar(
                source_counts, 
                x='Logos and text', 
                y='Count', 
                color='Logos and text', 
                color_discrete_map=color_map2_budapest,
                title='Logos and text Distribution'
            )
            fig.update_traces(
                marker_line_width=1.5, 
                hovertemplate="Count: %{y}", 
                textfont=dict(size=22)
            )
            fig.update_layout(
                xaxis_title="Logos and text", 
                yaxis_title="Count", 
                showlegend=False,
                hovermode="x unified",
                font=dict(size=16, color='white'),
                plot_bgcolor='black',
                paper_bgcolor='black',
                title_font=dict(color='white'),
                xaxis=dict(
                    color='white',
                    gridcolor='gray',
                    zerolinecolor='gray',
                    title_font=dict(color='white'),
                    tickfont=dict(color='white')
                ),
                yaxis=dict(
                    color='white',
                    gridcolor='gray',
                    zerolinecolor='gray',
                    title_font=dict(color='white'),
                    tickfont=dict(color='white')
                ),
                hoverlabel=dict(font=dict(size=24, color='white'))
            )

            return fig

    def generate_interactive_pie_chart_budapest(df):
        tod_counts = df['Time of the day'].value_counts().reset_index()
        tod_counts.columns = ['Time of the day', 'Count']

        fig = px.pie(
            tod_counts,
            names='Time of the day',
            values='Count',
            color='Time of the day',
            color_discrete_map=color_map2_budapest,
            title='Time of the day'
        )

        depth_values = [0.05 + i * 0.01 for i in range(len(tod_counts))]
        fig.update_traces(
            marker=dict(line=dict(color='white', width=2)),
            pull=depth_values,
            textinfo='label',
            textfont=dict(color='yellow', size=22)  
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

    def generate_interactive_bar_chart_weather_budapest(df):
        # Calculate the counts for each Weather category
        weather_counts = df['Weather'].value_counts().reset_index()
        weather_counts.columns = ['Weather', 'Count']

        # Create a horizontal bar chart
        fig = px.bar(
            weather_counts,
            y='Weather',
            x='Count',
            orientation='h',  # Horizontal bars
            color='Weather',
            color_discrete_map=color_map3_budapest,
            title='Weather'
        )

        # Customize the bar traces
        fig.update_traces(
            marker_line_width=1.5,
            hovertemplate="Count: %{x}",
            textfont=dict(size=22)
        )

        # Update layout for black background, fonts, etc.
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
                color='white',
                gridcolor='gray',
                zerolinecolor='gray',
                title_font=dict(color='white'),
                tickfont=dict(color='white')
            ),
            yaxis=dict(
                color='white',
                gridcolor='gray',
                zerolinecolor='gray',
                title_font=dict(color='white'),
                tickfont=dict(color='white')
            ),
            margin=dict(t=40, b=20, l=0, r=0),
            hoverlabel=dict(font=dict(size=24, color='white'))
        )

        return fig

    def generate_interactive_pie_chart_source(df):
        color_map = {
            'done': '#006400',
            'not started': '#FF0000',
            'not found': '#DC143C',
            'irrelevant': '#00FFFF'
        }

        # Ensure that only the Status column is used for value_counts
        source_counts = df['Source'].value_counts().reset_index()
        source_counts.columns = ['Source', 'Count']

        # Map a color to each status
        fig = px.pie(
            source_counts,
            names='Source',
            values='Count',
            color='Source',
            color_discrete_map=color_map_budapest,
            title='Source Distribution'
        )

        # Add depth to the slices
        depth_values = [0.05 + i * 0.01 for i in range(len(source_counts))]
        fig.update_traces(
            marker=dict(line=dict(color='white', width=2)),
            pull=depth_values,
            textinfo='label',
            textfont=dict(color='yellow', size=22)  
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

    # Generate Initial Figures
    pie_chart_initial = generate_interactive_pie_chart_budapest(df_budapest)
    bar_chart_weather_initial = generate_interactive_bar_chart_weather_budapest(df_budapest)
    bar_plot_logos_initial = generate_interactive_bar_plot_2_budapest(df_budapest)
    source_pie_initial = generate_interactive_pie_chart_source(df_budapest)    
    
def tab6_layout():
    return html.Div(
        style=background_style_budapest,
        children=[  
            dcc.ConfirmDialog(
                id='budapest-confirm-dialog',
                message="The data has refreshed successfully!"
            ),
            html.Img(
                src="/assets/airis.png", 
                alt="Airis Logo", 
                style={
                    "width": "200px", 
                    "position": "absolute",  # Absolute positioning
                    "top": "80px",          # Distance from the top of the page
                    "left": "10px",         # Distance from the left of the page
                    "zIndex": "1000"        # Ensures it stays above other elements
                }
            ), 
            dcc.Store(id='budapest-data', data=df_budapest.to_dict('records')),
            dcc.Store(id='budapest-polygon-filter-active', data=False),
            dcc.Store(id='budapest-filtered-data',data=None),
            dbc.Container(
                style=container_style,
                children=[
                    # Title
                    html.H1(
                        "Airis-Labs: Geo-Location Analysis - budapest",
                        className='mb-4',
                        style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}
                    ),
                    # Map and Filters Section
                    dbc.Row([
                        # Map on the left
                            dbc.Col(
                                dl.Map(
                                    [
                                        dl.TileLayer(),
                                        # Layer group for markers
                                        dl.LayerGroup(id="budapest-map-layer", children=markers_budapest),
                                        # Separate layer group for polygon
                                        dl.LayerGroup(
                                            id="polygon-layer_budapest",
                                            children=[
                                                dl.Polygon(
                                                    positions=budapest_polygon,
                                                    color="blue",
                                                    fillColor="cyan",
                                                    fillOpacity=0.6,
                                                )
                                            ]
                                        ),
                                    ],
                                    center=(47.4918275,19.052364),  # budapest coordinates
                                    zoom=10,
                                    style={"width": "100%", "height": "500px", "margin": "6px"}
                                ),
                                width=8
                            ),
                        # Filters on the right
                        dbc.Col(
                            [
                                html.Div(
                                    [
                                        html.H4(
                                            "Filters",
                                            className='mb-3',
                                            style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                                        ),
                                        dbc.Label("Terrain Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='budapest-Terrain',
                                            options=[{'label': k, 'value': k} for k in unique_terrain_budapest_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Camera Tilt Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='budapest-Camera_Tilt',
                                            options=[{'label': k, 'value': k} for k in unique_tilt_budapest_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Occlusion Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='budapest-Occlusion',
                                            options=[{'label': k, 'value': k} for k in unique_occluded_budapest_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Video Quality Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='budapest-VQ',
                                            options=[{'label': k, 'value': k} for k in unique_vq_budapest_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Label("Distance Filtering:", style=font_style),
                                        dcc.Dropdown(
                                            id='budapest-Distance_Building',
                                            options=[{'label': k, 'value': k} for k in unique_distance_budapest_1],
                                            value='All',
                                            className="form-control mb-2"
                                        ),
                                        dbc.Row(
                                            [
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Reset Filters",
                                                        id='budapest-reset-btn',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style
                                                    ),
                                                    width="auto"
                                                ),
                                                dbc.Col(
                                                    dbc.Button(
                                                        "Update DB",
                                                        id='budapest-update',
                                                        color='primary',
                                                        n_clicks=0,
                                                        style=button_style15
                                                    ),
                                                    width="auto"
                                                ),
                                            ],
                                        ),
                                    ],
                                    style={"marginBottom": "30px"}
                                ),
                            ],
                            width=4
                        ),
                    ]),
                    # Record Count
                    html.H1(
                        id='budapest-record-count',
                        children=f"Total Records: {len(df_budapest)}, {pre_out_budapest} % out of Polygon ",
                        style={'textAlign': 'left', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    dbc.Button("Show Which Ones",id='polygon_dropouts_budapest', color='primary',n_clicks=0,style=button_polygon),
                    # Duration Slider Section (below the map)
                    html.Br(),
                    html.H4(
                        "Filter by Video Duration (seconds):",
                        className='mb-1',
                        style={'textAlign': 'left', 'color': 'rgb(255,51,153)', 'marginBottom': '0'}
                    ),
                    dbc.Row(
                        dbc.Col(
                            dcc.RangeSlider(
                                id='budapest-duration-slider',
                                min=min_dur_budapest if not df_budapest.empty else 0,
                                max=max_dur_budapest if not df_budapest.empty else 100,
                                step=0.1,
                                value=[min_dur_budapest, max_dur_budapest] if not df_budapest.empty else [0, 100],
                                updatemode='mouseup',
                                marks={
                                    int(min_dur_budapest): str(int(min_dur_budapest)),
                                    int(max_dur_budapest): str(int(max_dur_budapest))
                                } if not df_budapest.empty else {},
                                tooltip={"always_visible": True, "placement": "bottom"}
                            ),
                            width=8
                        ),
                        justify="left"
                    ),
                    # Graphs Section
                    html.Div(
                        [
                            html.H4(
                                "Graphical Analysis",
                                className='mb-3',
                                style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}
                            ),
                            dbc.Row([
                                dbc.Col(
                                    dcc.Graph(id='budapest-pie-chart', figure=pie_chart_initial),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Graph(id='budapest-bar-chart-weather', figure=bar_chart_weather_initial),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                                dbc.Col(
                                    dcc.Graph(id='budapest-bar-plot-logos', figure=bar_plot_logos_initial),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                                dbc.Col(
                                    dcc.Graph(id='budapest-source-pie', figure=source_pie_initial),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),                                
                                
                            ]),
                        ],
                        style={'marginTop': '20px'}
                    ),
                    # General Insights Section
                    html.Div(
                        id='budapest-general-insights',
                        children=general_insights_initial,
                        style={'padding': '10px'}
                    ),
                    # Full Details Section
                    html.Div(
                        [
                            html.H1("Full Details:", className='mb-4', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}),
                            html.Hr(),
                            dash_table.DataTable(
                                id='budapest-table',
                                columns=[
                                    {"name": first_column_name_budapest, "id": first_column_name_budapest, "presentation": "markdown"}
                                ] + [{"name": i, "id": i} for i in df_budapest.columns[1:]] if not df_budapest.empty else [],
                                data=df_budapest.to_dict('records') if not df_budapest.empty else [],
                                sort_action="native",
                                filter_action="native",
                                fixed_rows={'headers': True},
                                style_table={'maxHeight': '500px',
                                            'overflowX': 'auto',
                                             'overflowY': 'auto'},
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
                                style_data_conditional=[
                                    {
                                        'if': {'column_id': 'Status'},
                                        'backgroundColor': 'rgb(220, 220, 220)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Active"'},
                                        'backgroundColor': 'rgb(85, 255, 85)',
                                        'color': 'black'
                                    },
                                    {
                                        'if': {'filter_query': '{Status} = "Inactive"'},
                                        'backgroundColor': 'rgb(255, 85, 85)',
                                        'color': 'white'
                                    },
                                ],
                            ),
                        ]
                    ),
                ]
            )
        ]
    )
    

@app.callback(
    [
        Output('budapest-table', 'data'),
        Output('budapest-map-layer', 'children'),
        Output('budapest-Terrain', 'value'),
        Output('budapest-Occlusion', 'value'),
        Output('budapest-VQ', 'value'),
        Output('budapest-Camera_Tilt', 'value'),
        Output('budapest-Distance_Building', 'value'),
        Output('budapest-record-count', 'children'),
        Output('budapest-duration-slider', 'min'),
        Output('budapest-duration-slider', 'max'),
        Output('budapest-duration-slider', 'value'),
        Output('budapest-pie-chart', 'figure'),
        Output('budapest-bar-chart-weather', 'figure'),
        Output('budapest-bar-plot-logos', 'figure'),
        Output('budapest-source-pie','figure'),
        Output('budapest-general-insights', 'children'),
        Output('budapest-pie-chart', 'clickData'),
        Output('budapest-bar-chart-weather', 'clickData'),
        Output('budapest-bar-plot-logos', 'clickData'),
        Output('budapest-source-pie','clickData'),
        Output('budapest-polygon-filter-active', 'data'),
        Output('budapest-filtered-data','data'),   # <--- NEW OUTPUT to store the filtered df
    ],
    [
        Input('budapest-pie-chart', 'clickData'),
        Input('budapest-bar-chart-weather', 'clickData'),
        Input('budapest-bar-plot-logos', 'clickData'),
        Input('budapest-source-pie','clickData'),
        Input('budapest-reset-btn', 'n_clicks'),
        Input('budapest-update', 'n_clicks'),
        Input('budapest-duration-slider', 'value'),
        Input('budapest-Terrain', 'value'),
        Input('budapest-Occlusion', 'value'),
        Input('budapest-VQ', 'value'),
        Input('budapest-Camera_Tilt', 'value'),
        Input('budapest-Distance_Building', 'value'),
        Input('polygon_dropouts_budapest', "n_clicks"),
    ],
    [
        State('budapest-data','data'),
        State('budapest-polygon-filter-active', 'data'),
        State('budapest-filtered-data', 'data'),  # <--- NEW STATE for the previously filtered df

  # <--- NEW STATE for the previously filtered df
    ]
)
def handle_table_and_refresh_budapest(
    pie_clickData, bar_weather_clickData,bar_clickData, pie2_clickData, 
    reset_clicks, update_clicks, duration_range,
    selected_terrain, selected_occluded, selected_VQ, selected_tilt, selected_distance,
    budapest_polygon_button,
    # States
    original_data,budapest_polygon_active,stored_filtered_data
):

    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None

    if stored_filtered_data is not None and triggered_id != 'budapest-reset-btn.n_clicks':
        # Start from the previously filtered subset
        df_current = pd.DataFrame(stored_filtered_data)
    else:
        df_current = pd.DataFrame(original_data)

    # Ensure Coordinates are split into lat/long if not already
    if 'Coordinates' in df_current.columns:
        df_current = df_current[df_current['Coordinates'].str.contains(',', na=False)]
        df_current[['Latitude', 'Longitude']] = df_current['Coordinates'].str.split(',', expand=True)
        df_current['Latitude'] = pd.to_numeric(df_current['Latitude'], errors='coerce')
        df_current['Longitude'] = pd.to_numeric(df_current['Longitude'], errors='coerce')

    # Compute or recompute Duration if needed
    if 'Duration' not in df_current.columns:
        df_current['Duration'] = df_current['Finish Time'].apply(convert_to_minutes) - \
                                 df_current['Start Time'].apply(convert_to_minutes)

    markers_budapest = create_map_markers(df_current)
    
    # Drop any rows with invalid coords
    df_current.dropna(subset=['Latitude', 'Longitude'], inplace=True)

    global min_dur_budapest, max_dur_budapest  # If you rely on these globally

    min_dur_budapest = df_current['Duration'].min()
    max_dur_budapest = df_current['Duration'].max()

    # polygon_budapest should be globally defined or imported from somewhere
    # for checking .contains(Point(row['Latitude'], row['Longitude']))

    # ------------------------------------------------------------------------
    # STEP 2: Handle each triggered event
    # ------------------------------------------------------------------------

    # 2.1 "UPDATE" button - re-load from original source, but keep current filters
    if triggered_id == 'budapest-update.n_clicks' and update_clicks > 0:
        # Re-load data from your source
        df_updated = load_budapest_data()
        # Same prep steps (split coords, compute Duration, drop invalid coords, etc.)
        df_updated['Duration'] = df_updated['Finish Time'].apply(convert_to_minutes) - \
                                 df_updated['Start Time'].apply(convert_to_minutes)
        df_updated = df_updated[df_updated['Coordinates'].str.contains(',', na=False)]
        df_updated[['Latitude', 'Longitude']] = df_updated['Coordinates'].str.split(',', expand=True)
        df_updated['Latitude'] = pd.to_numeric(df_updated['Latitude'], errors='coerce')
        df_updated['Longitude'] = pd.to_numeric(df_updated['Longitude'], errors='coerce')
        df_updated.dropna(subset=['Latitude', 'Longitude'], inplace=True)

        # Now apply the current user filters to the newly updated data
        filtered_df = apply_all_filters3(
            df=df_updated,
            duration_range=duration_range,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            bar_weather_clickData=bar_weather_clickData,
            pie_clickData=pie_clickData,
            pie_2_clickData=pie2_clickData,
            bar_2_clickData=bar_clickData,
            budapest_polygon_active = budapest_polygon_active
        )

        # Create map markers
        markers_budapest = create_map_markers(filtered_df)
        count_within_budapest = sum(
            polygon_budapest.contains(Point(row['Latitude'], row['Longitude']))
            for _, row in filtered_df.iterrows()
            if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
        )

        pre_out_budapest = round(((len(filtered_df)-count_within_budapest)/len(filtered_df) *100),2)   

        record_count_text = f"Total Records: {len(filtered_df)},{pre_out_budapest} % out of polygon "

        original_data = filtered_df.copy()
    
        # Build / refresh graphs
        updated_pie = generate_interactive_pie_chart_budapest(filtered_df)
        updated_bar_weather = generate_interactive_bar_chart_weather_budapest(filtered_df)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_budapest(filtered_df)
        updated_source_pie = generate_interactive_pie_chart_source(filtered_df)

        # Build general insights
        general_insights = build_general_insights_div(filtered_df)

        # Return and also store filtered data in 'budapest-filtered-data'
        return (
            filtered_df.to_dict('records'),
            markers_budapest,  # map-layer - if you want the new markers, see below
            dash.no_update,  # Terrain
            dash.no_update,  # Occlusion
            dash.no_update,  # VQ
            dash.no_update,  # Tilt
            dash.no_update,  # Distance building
            record_count_text,
            filtered_df['Duration'].min(),
            filtered_df['Duration'].max(),
            duration_range,  # keep slider the same
            updated_pie,
            updated_bar_weather,
            updated_bar_plot_logos,
            updated_source_pie,
            general_insights,
            None, None, None, None,
            budapest_polygon_active,
            filtered_df.to_dict('records'),  # <--- store updated data
        )

    elif triggered_id == 'polygon_dropouts_budapest.n_clicks' and budapest_polygon_button > 0:
        # Indicate that polygon filter is now active
        budapest_polygon_active = True

        # Start from df_current and remove in-polygon points
        filtered_polygon = df_current.copy()

        # Re-apply standard filters (duration, etc.) if needed
        # (You can do it before or after removing in-polygon points, 
        #  but typically you want them all together.)
        filtered_polygon = apply_all_filters3(
            df=filtered_polygon,
            duration_range=duration_range,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            bar_weather_clickData=bar_weather_clickData,
            pie_clickData=pie_clickData,
            pie_2_clickData=pie2_clickData,
            bar_2_clickData=bar_clickData,
            budapest_polygon_active = budapest_polygon_active # Because we'll remove them below
        )

        # Now remove points *inside* the polygon
        filtered_polygon = filtered_polygon[
            ~filtered_polygon.apply(
                lambda row: polygon_budapest.contains(Point(row['Latitude'], row['Longitude'])), 
                axis=1
            )
        ]

        # Build map markers
        markers_budapest = create_map_markers(filtered_polygon)

        # Build Figures
        updated_pie = generate_interactive_pie_chart_budapest(filtered_polygon)
        updated_bar_weather = generate_interactive_bar_chart_weather_budapest(filtered_polygon)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_budapest(filtered_polygon)
        updated_source_pie = generate_interactive_pie_chart_source(filtered_polygon)  

        # Build general insights
        general_insights = build_general_insights_div(filtered_polygon)

        record_count_text = f"Total Records: {len(filtered_polygon)}, 100% out of Polygon"

        return (
            filtered_polygon.to_dict('records'),
            markers_budapest,
            selected_terrain,
            selected_occluded,
            selected_VQ,
            selected_tilt,
            selected_distance,
            record_count_text,
            filtered_polygon['Duration'].min(),
            filtered_polygon['Duration'].max(),
            duration_range,
            updated_pie,
            updated_bar_weather,
            updated_bar_plot_logos,
            updated_source_pie,
            general_insights,
            pie_clickData,
            bar_clickData,
            bar_weather_clickData,
            pie2_clickData,
            budapest_polygon_active,
            filtered_polygon.to_dict('records'),  # <--- store the polygon-filtered df
        )
    # 2.3 "RESET" button
    elif triggered_id == 'budapest-reset-btn.n_clicks':
        # Reset everything to the original data
        df_reset = load_budapest_data()
        # Same prep steps (split coords, compute Duration, drop invalid coords, etc.)
        df_reset['Duration'] = df_reset['Finish Time'].apply(convert_to_minutes) - \
                                 df_reset['Start Time'].apply(convert_to_minutes)
        df_reset = df_reset[df_reset['Coordinates'].str.contains(',', na=False)]
        df_reset[['Latitude', 'Longitude']] = df_reset['Coordinates'].str.split(',', expand=True)
        df_reset['Latitude'] = pd.to_numeric(df_reset['Latitude'], errors='coerce')
        df_reset['Longitude'] = pd.to_numeric(df_reset['Longitude'], errors='coerce')
        df_reset.dropna(subset=['Latitude', 'Longitude'], inplace=True)
        budapest_polygon_active = False

        # Create map markers
        markers_budapest = create_map_markers(df_reset)

        count_within_budapest = sum(
            polygon_budapest.contains(Point(row['Latitude'], row['Longitude']))
            for _, row in df_reset.iterrows()
            if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
        )

        pre_out_budapest = round(((len(df_reset)-count_within_budapest)/len(df_reset) *100),2)   

        record_count_text = f"Total Records: {len(df_reset)},{pre_out_budapest} % out of polygon "


        # Build graphs
        updated_pie = generate_interactive_pie_chart_budapest(df_reset)
        updated_bar_chart = generate_interactive_bar_chart_weather_budapest(df_reset)
        updated_bar_chart_2 = generate_interactive_bar_plot_2_budapest(df_reset)
        updated_pie_2 = generate_interactive_pie_chart_source(df_reset)

        # General insights
        general_insights = build_general_insights_div(df_reset)

        return (
            df_reset.to_dict('records'),
            markers_budapest,
            'All',       # reset Terrain
            'All',       # reset Occlusion
            'All',       # reset VQ
            'All',       # reset Camera Tilt
            'All',       # reset Distance from building
            record_count_text,
            df_reset['Duration'].min(),
            df_reset['Duration'].max(),
            [df_reset['Duration'].min(), df_reset['Duration'].max()],
            updated_pie,
            updated_bar_chart,
            updated_bar_chart_2,
            updated_pie_2,
            general_insights,
            None, None, None, None,
            budapest_polygon_active,
            df_reset.to_dict('records')  ,  # <--- store data as None or the full df again, your choice
        )

    # 2.4 DEFAULT branch: user changed dropdowns, slider, or clicked bar/pie but not polygon filter
    #     We just apply all filters on df_current
    else:
        filtered_df = apply_all_filters3(
            df=df_current,
            duration_range=duration_range,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
            bar_weather_clickData=bar_weather_clickData,
            pie_clickData=pie_clickData,
            pie_2_clickData=pie2_clickData,
            bar_2_clickData=bar_clickData,
            budapest_polygon_active=budapest_polygon_active
        )


        if budapest_polygon_active:
            filtered_df = filtered_df[
                ~filtered_df.apply(
                    lambda row: polygon_budapest.contains(Point(row['Latitude'], row['Longitude'])), 
                    axis=1
                )
            ]

        # Create map markers
        markers_budapest = create_map_markers(filtered_df)
        count_within_budapest = sum(
            polygon_budapest.contains(Point(row['Latitude'], row['Longitude']))
            for _, row in filtered_df.iterrows()
            if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
        )
        if count_within_budapest > 0:
            pre_out_budapest = round(((len(filtered_df)-count_within_budapest)/len(filtered_df) *100),2)           
            record_count_text = f"Total Records: {len(filtered_df)}, {pre_out_budapest} % out of polygon"
        else:   
            record_count_text = f"Total Records: {len(filtered_df)}, 0.0 % out of polygon" 
        # Refresh graphs
        updated_pie = generate_interactive_pie_chart_budapest(filtered_df)
        updated_bar_weather = generate_interactive_bar_chart_weather_budapest(filtered_df)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_budapest(filtered_df)
        updated_source_pie = generate_interactive_pie_chart_source(filtered_df)  

        # Insights
        general_insights = build_general_insights_div(filtered_df)

        return (
            filtered_df.to_dict('records'),
            markers_budapest,
            selected_terrain,
            selected_occluded,
            selected_VQ,
            selected_tilt,
            selected_distance,
            record_count_text,
            filtered_df['Duration'].min(),
            filtered_df['Duration'].max(),
            duration_range,
            updated_pie,
            updated_bar_weather,
            updated_bar_plot_logos,
            updated_source_pie,
            general_insights,
            pie_clickData,
            bar_clickData,
            bar_weather_clickData,
            pie2_clickData,
            budapest_polygon_active,
            filtered_df.to_dict('records'),  # <--- store final filtered df
        )
           
app.layout = html.Div(
    [
        dcc.Tabs(
            [
                dcc.Tab(label='Geo-Location-London', children=tab1_layout(),style=tab_style, selected_style=selected_tab_style,),
                dcc.Tab(label='Geo-Location-Rome', children=tab2_layout(),style=tab_style,selected_style=selected_tab_style),
                dcc.Tab(label='Geo-Location-Madrid', children=tab3_layout(),style=tab_style,selected_style=selected_tab_style),
                dcc.Tab(label='Geo-Location-Barcelona', children=tab4_layout(),style=tab_style,selected_style=selected_tab_style),
                dcc.Tab(label='Geo-Location-Milan', children=tab5_layout(),style=tab_style,selected_style=selected_tab_style),
                dcc.Tab(label='Geo-Location-Budapest', children=tab6_layout(),style=tab_style,selected_style=selected_tab_style),

            ]
        )
    ]
)

if __name__ == '__main__':
    app.run_server(host='100.118.47.56', port=8050, debug=True)