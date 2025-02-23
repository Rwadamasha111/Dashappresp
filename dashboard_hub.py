import dash
import pandas as pd
from dash import dcc, html, dash_table, Input, Output, State
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import dash.exceptions
import numpy as np
import calendar
import plotly.express as px
import plotly.graph_objects as go
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import ast
import json
import re
import os
from shapely.geometry import Point, Polygon
import random  # For selecting a random marker

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from oauth2client.client import GoogleCredentials
from google.oauth2 import service_account

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


SERVICE_ACCOUNT_FILE = r"C:\Users\roy\OneDrive\Desktop\ASR JSONS\Geo_Analysis\arabic-transcription-435113-c5acf93c0185.json"

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/drive']

# Authenticate using Service Account
creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)

# Build the Drive API service
drive_service = build('drive', 'v3', credentials=creds)

# Define color maps
color_map_city = {
    'Youtube': 'rgb(255,0,0)',
    'tiktok': 'rgb(255,182,193)',
    'facebook': 'rgb(30,144,255)',
    'other': 'rgb(112,128,144)'
}
color_map2_city = {
    'Night Time': 'rgb(1, 1, 1)',      # Black
    'Day Time': 'rgb(236, 255, 0)'
}
color_map3_city = {
    'Clear': 'rgb(135,206,235)',
    'Snow': 'rgb(255,250,250)',
    'Rain': 'rgb(123,104,238)',
    'Fog or Smoke': 'rgb(128,128,128)'
}

# Define background style
background_style_city = {
    "background-size": "cover",
    "background-position": "center",
    "height": "350vh",
    "padding": "10px",
    "background-color": 'black',
}

def convert_to_minutes(duration):
    try:
        parts = list(map(int, duration.split(':')))
        if len(parts) == 2:  # mm:ss format
            minutes, seconds = parts
            total_seconds = minutes * 60 + seconds
        elif len(parts) == 3:  # h:mm:ss format
            hours, minutes, seconds = parts
            total_seconds = hours * 3600 + minutes * 60 + seconds
        else:
            return None  # Invalid format
        return total_seconds  # Convert total seconds to minutes
    except (ValueError, AttributeError):
        return None  # Handle invalid inputs

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

def generate_interactive_bar_plot_2_city(df):
    source_counts = df['Logos and text'].value_counts().reset_index()
    source_counts.columns = ['Logos and text', 'Count']
    fig = px.bar(
        source_counts, 
        x='Logos and text', 
        y='Count', 
        color='Logos and text', 
        color_discrete_map=color_map2_city,
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

def generate_interactive_pie_chart_city(df):
    tod_counts = df['Time of the day'].value_counts().reset_index()
    tod_counts.columns = ['Time of the day', 'Count']
    fig = px.pie(
        tod_counts,
        names='Time of the day',
        values='Count',
        color='Time of the day',
        color_discrete_map=color_map2_city,
        title='Time of the day'
    )
    fig.update_traces(
        marker=dict(line=dict(color='white', width=2)),
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

def generate_interactive_bar_chart_weather_city(df):
    weather_counts = df['Weather'].value_counts().reset_index()
    weather_counts.columns = ['Weather', 'Count']
    fig = px.bar(
        weather_counts,
        y='Weather',
        x='Count',
        orientation='h',
        color='Weather',
        color_discrete_map=color_map3_city,
        title='Weather'
    )
    fig.update_traces(
        marker_line_width=1.5,
        hovertemplate="Count: %{x}",
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
    source_counts = df['Source'].value_counts().reset_index()
    source_counts.columns = ['Source', 'Count']
    fig = px.pie(
        source_counts,
        names='Source',
        values='Count',
        color='Source',
        color_discrete_map=color_map_city,
        title='Source Distribution'
    )
    fig.update_traces(
        marker=dict(line=dict(color='white', width=2)),
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

button_style_city = {
    "width": "50%",
    "height": "60px",
    "margin": "30px",
    "background-color": 'yellow',
    "border": "2px solid white",
    "display": "block",
    "font-weight": "bold",
    "color": "black",
    "borderRadius": "50px",
}

button_style15 = {
    "width": "150%",
    "height": "60px",
    "margin": "30px",
    "background-color": 'white',
    "border": "2px solid white",
    "display": "block",
    "font-weight": "bold",
    "color": "rgb(255,51,153)",
    "borderRadius": "50px",   
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
    "borderRadius": "50px",  
}
font_style = {
    "color": "white",
    "size": "25px",
    'font-weight': 'bold'
}
tab_style = {
    'background-color': 'black',
    'color': 'rgb(255,51,153)',
    'font-size': '24px',
}
selected_tab_style = {
    'background-color': 'gray',
    'color': 'rgb(255,51,153)',
    'font-size': '24px',
    'padding': '10px',
    'font-weight': 'bold'
}

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

@app.callback([
    Output('city_filter', 'options'),
    Output('city_filter', 'value'),],
[
    Input('state_filter', 'value'),
]
)
def update_city_data(selected_country):
    city_options = cities[cities['Country'] == selected_country]['City Name'].unique()
    city_value=city_options[0]
    return(
         [{'label': city, 'value': city} for city in city_options],
         city_value
    )

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
            dcc.Store(id='filtered-city-data', data=None),
            dcc.Store(id='reset_button_clicked', data=False),
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
                            # Assign an id "map" so we can update its center dynamically.
                            dl.Map(
                                id='map',
                                children=[
                                    dl.TileLayer(),
                                    dl.LayerGroup(id="map-layer", children=[]),
                                    dl.LayerGroup(id="polygon-layer", children=[]),
                                ],
                                center=(41.9028, 12.4964),  # default center (Rome)
                                zoom=10,
                                style={"width": "100%", "height": "500px", "margin": "6px"}
                            ),
                            dbc.Row([
                                dbc.Col(
                                    html.Div([
                                        dbc.Label("Select A Country:", style=font_style),
                                        dcc.Dropdown(
                                            id='state_filter',
                                            options=[{'label': r, 'value': r} for r in states],
                                            value='Italy',
                                            className="form-control mb-2"
                                        )
                                    ]), width=4
                                ),
                                dbc.Col(
                                    html.Div([
                                        dbc.Label("Select A City:", style=font_style),
                                        dcc.Dropdown(
                                            id='city_filter',
                                            options=[],
                                            value='', 
                                            className="form-control mb-2"
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
                        ], width=8),                 
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
                                dbc.Row([
                                    dbc.Col(dbc.Button("Update DB & Reset Filters", id='update', color='primary', n_clicks=0, style=button_style15), width="auto"),
                                ]),
                            ], style={"marginBottom": "30px"}),
                        ], width=4),
                    ]),
                    html.H1(
                        id='record-count',
                        children="Total Records: 0",
                        style={'textAlign': 'left', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    html.Br(),
                    html.H4("Filter by Video Duration (seconds):", className='mb-1', style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}),
                    dbc.Row([
                        dbc.Col(
                            dcc.RangeSlider(
                                id='duration-slider',
                                min=0,
                                max=100,
                                step=0.1,
                                value=[0, 100],
                                updatemode='mouseup',
                                marks={},
                                tooltip={"always_visible": True, "placement": "bottom"}
                            ), width=8
                        )
                    ], justify="left"),
                    html.Div([
                        html.H4("Graphical Analysis", className='mb-3', style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}),
                        dbc.Row([
                            dbc.Col(dcc.Graph(id='pie-chart', figure={}), width=6),
                            dbc.Col(dcc.Graph(id='bar-chart-weather', figure={}), width=6),
                            dbc.Col(dcc.Graph(id='bar-plot-logos', figure={}), width=6),
                            dbc.Col(dcc.Graph(id='source-pie', figure={}), width=6),
                        ]),
                    ], style={'marginTop': '20px'}),
                    html.Div([
                        html.H1("Full Details:", className='mb-4', style={'textAlign': 'center', 'color': 'rgb(255,51,153)'}),
                        html.Hr(),
                        dash_table.DataTable(
                            id='table',
                            columns=[],
                            data=[],
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
                            style_data_conditional=[]
                        ),
                    ]),
                ]
            )
        ]
    )

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

def load_polygon_df ():
    SHEET_ID_barcelona = '1FZ9i73t915Q3W73QMaQNG7Qn6xa-YahLvV9xMXyLQMw'
    RANGE_barcelona = 'Polygons!A1:B10000'

    try:
        # Access the Google Sheet for Barcelona
        result = sheet.values().get(spreadsheetId=SHEET_ID_barcelona, range=RANGE_barcelona).execute()
        values = result.get('values', [])

        # Convert the data to a pandas DataFrame
        if values:
            headers = values[0]  # Assuming the first row is the header
            data = values[1:]    # Rest is the data
            df_pol = pd.DataFrame(data, columns=headers)
        else:
            print("No data found for Barcelona.")
            df_pol = pd.DataFrame()

        return df_pol
    
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()
    
@app.callback(
    [Output('map', 'center'),
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
     Output('record-count', 'children'),
     Output('duration-slider', 'min'),
     Output('duration-slider', 'max'),
     Output('duration-slider', 'value'),
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
     Output('reset_button_clicked','data')
    ],
    [Input('city-filter-btn', 'n_clicks'),
     Input('city_filter', "value"),
     Input('update','n_clicks'),
     Input('pie-chart', 'clickData'),
     Input('bar-chart-weather', 'clickData'),
     Input('bar-plot-logos', 'clickData'),
     Input('source-pie','clickData'),
     Input('duration-slider', 'value'),
     Input('Terrain', 'value'),
     Input('Occlusion', 'value'),
     Input('VQ', 'value'),
     Input('Camera_Tilt', 'value'),
     Input('Distance_Building', 'value')],
    [State('current-city-data','data'),
     State('reset_button_clicked','data')]
)
def load_dashboards(load_btn, selected_city, update, pie_clickData, 
                    bar_weather_clickData, bar_clickData, pie2_clickData, duration_range,
                    selected_terrain, selected_occluded, selected_VQ, selected_tilt, selected_distance,
                    current_data, reset_clicked):
    global polygon_coordinates
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None

    # Fix #1: Do nothing if the city drop-down (city_filter) is changed without clicking the Load button.
    if triggered_id and triggered_id.startswith('city_filter'):
        return (dash.no_update,) * 30

    if triggered_id != 'pie-chart.clickData':
        pie_clickData = None
    if triggered_id != 'bar-chart-weather.clickData':
        bar_weather_clickData = None    
    if triggered_id != 'bar-plot-logos.clickData':
        bar_clickData = None
    if triggered_id != 'source-pie.clickData':
        pie2_clickData = None 
        
    # Helper function to build dropdown options remains the same.
    def build_options(df, col_name):
        if col_name in df.columns:
            unique_vals = sorted([v for v in df[col_name].unique() if pd.notnull(v)])
            return [{'label': 'All', 'value': 'All'}] + [{'label': str(val), 'value': str(val)} for val in unique_vals]
        return []

    if triggered_id == 'city-filter-btn.n_clicks':
        reset_clicked = False
        # --- Load new city data ---
        sheet_id = cities.loc[cities['City Name'] == selected_city, 'Sheet ID'].iloc[0]
        sheet_range = cities.loc[cities['City Name'] == selected_city, 'Sheet Range'].iloc[0]
        polygon_id = cities.loc[cities['City Name'] == selected_city, 'PolygonID'].iloc[0]
        request = drive_service.files().get_media(fileId=polygon_id)

        file_path = "polygon.txt"
        with open(file_path, "wb") as file:
            file.write(request.execute())
        with open(file_path, "r") as file:
            polygon_data = json.load(file)
        polygon_coordinates = [tuple(coord) for coord in polygon_data]
        city_polygon = Polygon(polygon_coordinates)
        
        polygon_layer = dl.LayerGroup(
            id="polygon-layer",
            children=[dl.Polygon(
                positions=list(city_polygon.exterior.coords),
                color="blue",
                fillColor="cyan",
                fillOpacity=0.6,
            )],
        )
        df_city=pd.DataFrame(current_data)
        df_city = load_city(sheet_id, sheet_range)
        
        table_columns = [{'name': col, 'id': col} for col in df_city.columns]
        terrain_options = build_options(df_city, 'Terrain')
        occlusion_options = build_options(df_city, 'Occluded')
        vq_options = build_options(df_city, 'Video quality')
        camera_tilt_options = build_options(df_city, 'Camera tilt')
        distance_options = build_options(df_city, 'Distance from building')
        terrain_value = occlusion_value = vq_value = camera_tilt_value = distance_value = 'All'
        
        # Generate charts and markers (code omitted for brevity)
        city_logos_bar = generate_interactive_bar_plot_2_city(df_city)
        city_time_of_day_pie = generate_interactive_pie_chart_city(df_city)
        city_weather_bar = generate_interactive_bar_chart_weather_city(df_city)
        city_source_pie = generate_interactive_pie_chart_source(df_city)
        
        if 'Coordinates' in df_city.columns:
            df_city = df_city[df_city['Coordinates'].str.contains(',', na=False)]
            df_city[['Latitude', 'Longitude']] = df_city['Coordinates'].str.split(',', expand=True)
            df_city['Latitude'] = pd.to_numeric(df_city['Latitude'], errors='coerce')
            df_city['Longitude'] = pd.to_numeric(df_city['Longitude'], errors='coerce')
            city_markers = create_map_markers(df_city)
        else:
            city_markers = []
        
        count_within = sum(city_polygon.contains(Point(row['Latitude'], row['Longitude']))
                           for _, row in df_city.iterrows()
                           if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude']))
        pre_out_city = round(((len(df_city) - count_within) / len(df_city) * 100), 2)
        
        if 'Duration' not in df_city.columns:
            df_city['Duration'] = df_city['Finish Time'].apply(convert_to_minutes) - df_city['Start Time'].apply(convert_to_minutes)
        df_city.dropna(subset=['Latitude', 'Longitude'], inplace=True)
        
        min_dur = df_city['Duration'].min() if not df_city['Duration'].empty else 0
        max_dur = df_city['Duration'].max() if not df_city['Duration'].empty else 100
        record_count = f"Total Records: {len(df_city)} , {pre_out_city} % out of Polygon"
        
        if city_markers:
            random_marker = random.choice(city_markers)
            map_center = random_marker.position
        else:
            map_center = (41.9028, 12.4964)
        
        title = f"Airis-Labs: Geo-Location Analysis - {selected_city}"
        
        # Fix #2: Reset the filtered-city-data store with the full new data.
        return (
            map_center,               
            city_markers,             
            polygon_layer,
            terrain_options,          
            terrain_value,            
            occlusion_options,        
            occlusion_value,          
            vq_options,               
            vq_value,                 
            camera_tilt_options,      
            camera_tilt_value,        
            distance_options,         
            distance_value,           
            record_count,             
            min_dur,                  
            max_dur,                  
            [min_dur, max_dur],
            city_time_of_day_pie,     
            city_weather_bar,         
            city_logos_bar,           
            city_source_pie,          
            dash.no_update,           
            dash.no_update,           
            dash.no_update,           
            dash.no_update,           
            title,
            df_city.to_dict('records'),
            table_columns,
            df_city.to_dict('records'),
            reset_clicked
        )
        
    elif triggered_id == 'update.n_clicks':
        reset_clicked = True
        # --- Update existing city data (similar code as above) ---
        sheet_id = cities.loc[cities['City Name'] == selected_city, 'Sheet ID'].iloc[0]
        sheet_range = cities.loc[cities['City Name'] == selected_city, 'Sheet Range'].iloc[0]
        polygon_id = cities.loc[cities['City Name'] == selected_city, 'PolygonID'].iloc[0]
        city_polygon = Polygon(polygon_coordinates)  # using previously loaded polygon_coordinates
        df_updated = pd.DataFrame(current_data)
        df_updated = load_city(sheet_id, sheet_range)
        
        table_columns = [{'name': col, 'id': col} for col in df_updated.columns]
        
        terrain_options = build_options(df_updated, 'Terrain')
        occlusion_options = build_options(df_updated, 'Occluded')
        vq_options = build_options(df_updated, 'Video quality')
        camera_tilt_options = build_options(df_updated, 'Camera tilt')
        distance_options = build_options(df_updated, 'Distance from building')
        terrain_value = occlusion_value = vq_value = camera_tilt_value = distance_value = 'All'
        
        city_logos_bar = generate_interactive_bar_plot_2_city(df_updated)
        city_time_of_day_pie = generate_interactive_pie_chart_city(df_updated)
        city_weather_bar = generate_interactive_bar_chart_weather_city(df_updated)
        city_source_pie = generate_interactive_pie_chart_source(df_updated)
        
        if 'Coordinates' in df_updated.columns:
            df_updated = df_updated[df_updated['Coordinates'].str.contains(',', na=False)]
            df_updated[['Latitude', 'Longitude']] = df_updated['Coordinates'].str.split(',', expand=True)
            df_updated['Latitude'] = pd.to_numeric(df_updated['Latitude'], errors='coerce')
            df_updated['Longitude'] = pd.to_numeric(df_updated['Longitude'], errors='coerce')
            city_markers = create_map_markers(df_updated)
        else:
            city_markers = []
        
        count_within = sum(city_polygon.contains(Point(row['Latitude'], row['Longitude']))
                           for _, row in df_updated.iterrows()
                           if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude']))
        pre_out_city = round(((len(df_updated) - count_within) / len(df_updated) * 100), 2)
        
        if 'Duration' not in df_updated.columns:
            df_updated['Duration'] = df_updated['Finish Time'].apply(convert_to_minutes) - df_updated['Start Time'].apply(convert_to_minutes)
        df_updated.dropna(subset=['Latitude', 'Longitude'], inplace=True)
        
        min_dur = df_updated['Duration'].min() if not df_updated['Duration'].empty else 0
        max_dur = df_updated['Duration'].max() if not df_updated['Duration'].empty else 100
        record_count = f"Total Records: {len(df_updated)} , {pre_out_city} % out of Polygon"
        
        if city_markers:
            random_marker = random.choice(city_markers)
            map_center = random_marker.position
        else:
            map_center = (41.9028, 12.4964)
        
        # Fix #2: Also reset filtered-city-data here.
        return (
            map_center,               
            city_markers,             
            dash.no_update,
            terrain_options,          
            terrain_value,            
            occlusion_options,        
            occlusion_value,          
            vq_options,               
            vq_value,                 
            camera_tilt_options,      
            camera_tilt_value,        
            distance_options,         
            distance_value,           
            record_count,             
            min_dur,                  
            max_dur,                  
            [min_dur, max_dur],
            city_time_of_day_pie,     
            city_weather_bar,         
            city_logos_bar,           
            city_source_pie,          
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            df_updated.to_dict('records'),
            table_columns,
            df_updated.to_dict('records'),
            reset_clicked
        )
    else:
        # --- Filtering branch: Use current data as baseline ---
        reset_clicked = False
        df_current = pd.DataFrame(current_data)
        if df_current.empty:
            # (Reload data if necessary)
            sheet_id = cities.loc[cities['City Name'] == selected_city, 'Sheet ID'].iloc[0]
            sheet_range = cities.loc[cities['City Name'] == selected_city, 'Sheet Range'].iloc[0]
            polygon_id = cities.loc[cities['City Name'] == selected_city, 'PolygonID'].iloc[0]
            request = drive_service.files().get_media(fileId=polygon_id)
            file_path = "polygon.txt"
            with open(file_path, "wb") as file:
                file.write(request.execute())
            with open(file_path, "r") as file:
                polygon_data = json.load(file)
            polygon_coordinates = [tuple(coord) for coord in polygon_data]
            city_polygon = Polygon(polygon_coordinates)
            polygon_layer = dl.LayerGroup(
                id="polygon-layer",
                children=[dl.Polygon(
                    positions=list(city_polygon.exterior.coords),
                    color="blue",
                    fillColor="cyan",
                    fillOpacity=0.6,
                )],
            )
            df_current = load_city(sheet_id, sheet_range)
            table_columns = [{'name': col, 'id': col} for col in df_current.columns]
            terrain_options = build_options(df_current, 'Terrain')
            occlusion_options = build_options(df_current, 'Occluded')
            vq_options = build_options(df_current, 'Video quality')
            camera_tilt_options = build_options(df_current, 'Camera tilt')
            distance_options = build_options(df_current, 'Distance from building')
            terrain_value = occlusion_value = vq_value = camera_tilt_value = distance_value = 'All'
            city_logos_bar = generate_interactive_bar_plot_2_city(df_current)
            city_time_of_day_pie = generate_interactive_pie_chart_city(df_current)
            city_weather_bar = generate_interactive_bar_chart_weather_city(df_current)
            city_source_pie = generate_interactive_pie_chart_source(df_current)
            if 'Coordinates' in df_current.columns:
                df_current = df_current[df_current['Coordinates'].str.contains(',', na=False)]
                temp = df_current['Coordinates'].str.split(',', n=1, expand=True)
                df_current['Latitude'] = pd.to_numeric(temp[0], errors='coerce')
                df_current['Longitude'] = pd.to_numeric(temp[1], errors='coerce')
                city_markers = create_map_markers(df_current)
            else:
                city_markers = []
            city_polygon = Polygon(polygon_coordinates)
            count_within = sum(city_polygon.contains(Point(row['Latitude'], row['Longitude']))
                               for _, row in df_current.iterrows()
                               if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude']))
            pre_out_city = round(((len(df_current) - count_within) / len(df_current) * 100), 2)
            if 'Duration' not in df_current.columns:
                df_current['Duration'] = df_current['Finish Time'].apply(convert_to_minutes) - df_current['Start Time'].apply(convert_to_minutes)
            df_current.dropna(subset=['Latitude', 'Longitude'], inplace=True)
            min_dur = df_current['Duration'].min() if not df_current['Duration'].empty else 0
            max_dur = df_current['Duration'].max() if not df_current['Duration'].empty else 100
            record_count = f"Total Records: {len(df_current)} , {pre_out_city} % out of Polygon"
            if city_markers:
                random_marker = random.choice(city_markers)
                map_center = random_marker.position
            else:
                map_center = (41.9028, 12.4964)
            title = f"Airis-Labs: Geo-Location Analysis - {selected_city}"
            
            return (
                map_center,
                city_markers,
                polygon_layer,
                terrain_options,
                terrain_value,
                occlusion_options,
                occlusion_value,
                vq_options,
                vq_value,
                camera_tilt_options,
                camera_tilt_value,
                distance_options,
                distance_value,
                record_count,
                min_dur,
                max_dur,
                [min_dur, max_dur],
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
                reset_clicked
            )
        else:
            reset_clicked = False
            df_filtered = pd.DataFrame(current_data)
            filtered_df = apply_all_filters2(
                df=df_filtered,
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
            )
            # Generate charts and markers for the filtered DataFrame
            city_logos_bar = generate_interactive_bar_plot_2_city(filtered_df)
            city_time_of_day_pie = generate_interactive_pie_chart_city(filtered_df)
            city_weather_bar = generate_interactive_bar_chart_weather_city(filtered_df)
            city_source_pie = generate_interactive_pie_chart_source(filtered_df)
            if 'Coordinates' in filtered_df.columns:
                filtered_df = filtered_df[filtered_df['Coordinates'].str.contains(',', na=False)]
                temp = filtered_df['Coordinates'].str.split(',', n=1, expand=True)
                filtered_df['Latitude'] = pd.to_numeric(temp[0], errors='coerce')
                filtered_df['Longitude'] = pd.to_numeric(temp[1], errors='coerce')
                city_markers = create_map_markers(filtered_df)
            else:
                city_markers = []
            city_polygon = Polygon(polygon_coordinates)
            count_within = sum(city_polygon.contains(Point(row['Latitude'], row['Longitude']))
                               for _, row in filtered_df.iterrows()
                               if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude']))
            pre_out_city = round(((len(filtered_df) - count_within) / len(filtered_df) * 100), 2)
            if 'Duration' not in filtered_df.columns:
                filtered_df['Duration'] = filtered_df['Finish Time'].apply(convert_to_minutes) - filtered_df['Start Time'].apply(convert_to_minutes)
            filtered_df.dropna(subset=['Latitude', 'Longitude'], inplace=True)
            min_dur = filtered_df['Duration'].min() if not filtered_df['Duration'].empty else 0
            max_dur = filtered_df['Duration'].max() if not filtered_df['Duration'].empty else 100
            record_count = f"Total Records: {len(filtered_df)} , {pre_out_city} % out of Polygon"
            if city_markers:
                random_marker = random.choice(city_markers)
                map_center = random_marker.position
            else:
                map_center = (41.9028, 12.4964)
                        
            return (
                map_center,
                city_markers,
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
                record_count,
                min_dur,
                max_dur,
                [min_dur, max_dur],
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
                reset_clicked
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

if __name__ == '__main__':
    app.run_server(host='100.118.47.56', port=8052, debug=True)
