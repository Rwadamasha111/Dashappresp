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
    
def convert_to_minutes_2(duration):
    try:
        minutes, seconds = map(int, duration.split(':'))
        total_seconds = minutes * 60 + seconds
        return total_seconds / 60.0
    except (ValueError, AttributeError):
        return None

    
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
    "border": "2px solid black",
    "display": "block",
    "font-weight": "bold",
    "color": "black",
}

button_style1 = {
    "width": "20%",
    "height": "60px",
    "margin": "30px",
    "background-color": 'orange',
    "border": "2px solid black",
    "display": "block",
    "font-weight": "bold",
    "color": "black",
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



# ---------------------------- London Tab Data and Layout ----------------------------

def load_london_data():
    # Google Sheet ID and Range for London
    SHEET_ID_LONDON = '1QeShjzs41NEDLQ2nlI8NkAHkmBCC89y7eVK9X7j_aeU'
    RANGE_LONDON = 'Geolocation_coordinates_annotation - London_try!A1:X587'

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
df_london['Duration'] = df_london['Duration'].apply(convert_to_minutes)
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

# Create Map Markers
markers_london = [
    dl.Marker(position=eval(coord), children=[dl.Popup(name)] , id= "london-mark" + str(i))
    for  i , (coord, name)  in enumerate( zip(df_london['Coordinates'], df_london['Terrain'] ) )
]
mark_ids_london = [ Input("london-mark" + str(i), 'clickData')  for  i , (coord, name)  in enumerate( zip(df_london['Coordinates'], df_london['Terrain'] ) )  ] 

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
            dcc.Interval(id='london-interval-component', interval=1*10000, n_intervals=0),
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
                                    dl.LayerGroup(id="london-map-layer", children=markers_london)
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
        Input('london-duration-slider', 'value'),
        Input('london-Terrain', 'value'),
        Input('london-Occlusion', 'value'),
        Input('london-Category', 'value'),
        Input('london-Camera_Tilt', 'value'),
        Input('london-Distance_Building', 'value'),
        Input('london-map-layer', 'clickData'),
        Input('london-interval-component', 'n_intervals')
    ] + mark_ids_london,
)
def handle_table_and_refresh_london(
    bar_clickData, pie_clickData, reset_clicks, duration_range,
    selected_terrain, selected_occluded, selected_category, selected_tilt,
    selected_distance, map_clickData, n_intervals, gen_in, updated_bar_plotl, updated_pie_chartl, *ping_marker
):
    true_marker = [mark for mark in ping_marker if mark is not None]
    ctx = dash.callback_context
    triggered = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    try:
        global df_london, filtered_df, min_dur_london, max_dur_london


        df_london = load_london_data()
        df_london['Duration'] = df_london['Duration'].apply(convert_to_minutes)
        min_dur_london = df_london['Duration'].min()
        max_dur_london = df_london['Duration'].max()
        
        # Recreate markers
        markers_london = [
            dl.Marker(position=eval(coord), children=[dl.Popup(name)], id="london-mark" + str(i))
            for i, (coord, name) in enumerate(zip(df_london['Coordinates'], df_london['Terrain']))
        ]
        gen_in = general_insights_london(df_london)

        filtered_df = df_london.copy()

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
            
        # Apply Map Pin Click Filter
        if len(true_marker) > 0:
            clicked_latlng = true_marker[0]['latlng']
            clicked_coord = (clicked_latlng['lat'], clicked_latlng['lng'])
            filtered_df['Coordinates'] = filtered_df['Coordinates'].apply(eval)
            filtered_df = filtered_df[filtered_df['Coordinates'] == clicked_coord]
            if filtered_df.empty:
                raise dash.exceptions.PreventUpdate

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
        record_count_text = f"Total Records: {len(filtered_df)}"

        # Recreate markers
        markers_london = [
            dl.Marker(position=eval(coord), children=[dl.Popup(name)], id="london-mark" + str(i))
            for i, (coord, name) in enumerate(zip(df_london['Coordinates'], df_london['Terrain']))
        ]
        
        gen_in = general_insights_london(filtered_df)
        # Generate updated figures after filtering
        updated_bar_plotl = generate_interactive_bar_plot_london(filtered_df)
        updated_pie_chartl = generate_interactive_pie_chart_london(filtered_df)
        
        # On interval update, reload the data (if needed)  
        if triggered == 'n_intervals':
            df_london = load_london_data()
            df_london['Duration'] = df_london['Duration'].apply(convert_to_minutes)
            min_dur_london = df_london['Duration'].min()
            max_dur_london = df_london['Duration'].max()
            gen_in = general_insights_london(df_london)
            updated_bar_plotl = generate_interactive_bar_plot_london(df_london)
            updated_pie_chartl = generate_interactive_pie_chart_london(df_london)
            
            return (
                df_london.to_dict('records'),    # data
                markers_london,                  # children
                'All',                           # Terrain.value
                'All',                           # Occlusion.value
                'All',                           # Category.value
                'All',                           # Camera_Tilt.value
                'All',                           # Distance_Building.value
                f"Total Records: {len(df_london)}", # record-count.children
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
        # Handle Reset button
        elif triggered == 'london-reset-btn.n_clicks':
            # Reset filters
            df_london.reset_index(drop=True, inplace=True)
            filtered_df = df_london.copy()  # filtered_df reset as well

            # Recreate markers
            markers_london = [
                dl.Marker(position=eval(coord), children=[dl.Popup(name)], id="london-mark" + str(i))
                for i, (coord, name) in enumerate(zip(df_london['Coordinates'], df_london['Terrain']))
            ]
            gen_in = general_insights_london(filtered_df)
            updated_bar_plotl = generate_interactive_bar_plot_london(filtered_df)
            updated_pie_chartl = generate_interactive_pie_chart_london(filtered_df)

            return (
                df_london.to_dict('records'),
                markers_london,
                'All', 'All', 'All', 'All', 'All',
                f"Total Records: {len(df_london)}",
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

            
        # Normal return (no special trigger)
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
            None,
            None
        )

    except Exception as e:
        print(f"Error: {e}")
        raise dash.exceptions.PreventUpdate
    


# ---------------------------- Rome Tab Data and Layout ----------------------------

def load_rome_data():
    # Google Sheet ID and Range for Rome
    SHEET_ID_ROME = '1_t43FcoPzBofIk4tI74u9lP2xdCazv1svncDvtJZQZg'
    RANGE_ROME = 'Sheet1!A1:Z153'

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

# Convert 'Duration' column
df_rome['Duration'] = df_rome['Duration'].apply(convert_to_minutes)
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

# Create Map Markers
markers_rome = [
    dl.Marker(position=eval(coord), children=[dl.Popup(name)] , id= "rome-mark" + str(i))
    for  i , (coord, name)  in enumerate( zip(df_rome['Coordinates'], df_rome['Terrain'] ) )
]

def tab2_layout():
    return html.Div(
        style=background_style_rome,
        children=[
            dcc.Interval(id='rome-interval-component', interval=1*10000, n_intervals=0),            
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
                                    dl.LayerGroup(id="rome-map-layer", children=markers_rome)
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
        Input('rome-duration-slider', 'value'),
        Input('rome-Terrain', 'value'),
        Input('rome-Occlusion', 'value'),
        Input('rome-VQ', 'value'),
        Input('rome-Camera_Tilt', 'value'),
        Input('rome-Distance_Building', 'value'),
        Input('rome-interval-component', 'n_intervals')
    ]
)
def handle_table_and_refresh_rome(
    bar_clickData, pie_clickData, pie_weather_clickData, bar_2_clickData, reset_clicks, duration_range,
    selected_terrain, selected_occluded, selected_VQ, selected_tilt, selected_distance, n_intervals
):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    
    try:
        global df_rome, min_dur_rome, max_dur_rome
        # If the interval triggered the callback, reload the data
        if triggered_id == 'n_intervals':
            df_rome = load_rome_data()
            df_rome['Duration'] = df_rome['Duration'].apply(convert_to_minutes)
            min_dur_rome = df_rome['Duration'].min()
            max_dur_rome = df_rome['Duration'].max()

            # Recalculate general insights
            most_common_source_rome = df_rome['Source'].mode().iloc[0] if not df_rome['Source'].dropna().mode().empty else None
            most_common_tod_rome = df_rome['Time of the day'].mode().iloc[0] if not df_rome['Time of the day'].dropna().mode().empty else None
            most_common_terrain_rome = df_rome['Terrain'].mode().iloc[0] if not df_rome['Terrain'].dropna().mode().empty else None
            most_common_tilt_rome = df_rome['Camera tilt'].mode().iloc[0] if not df_rome['Camera tilt'].dropna().mode().empty else None
            avg_dur_rome = round(df_rome['Duration'].mean(), 2)

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

            # Create updated markers for the map
            if 'Coordinates' in df_rome.columns and 'Terrain' in df_rome.columns:
                markers_rome = [
                    dl.Marker(position=eval(coord), children=[dl.Popup(name)])
                    for coord, name in zip(df_rome['Coordinates'], df_rome['Terrain'])
                    if pd.notnull(coord) and pd.notnull(name)
                ]
            else:
                markers_rome = []

            # Refresh the graphs
            updated_bar_plot = generate_interactive_bar_plot_rome(filtered_df)
            updated_pie_chart = generate_interactive_pie_chart_rome(filtered_df)
            updated_pie_chart_weather = generate_interactive_pie_chart_2_rome(filtered_df)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_rome(filtered_df)

            # Return the refreshed data
            return (
                df_rome.to_dict('records'),
                markers_rome,
                'All', 'All', 'All', 'All', 'All',
                f"Total Records: {len(df_rome)}",
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

        if triggered_id == 'rome-reset-btn.n_clicks':
            # Reset filters and map markers
            if 'Coordinates' in df_rome.columns and 'Terrain' in df_rome.columns:
                markers_rome = [
                    dl.Marker(position=eval(coord), children=[dl.Popup(name)])
                    for coord, name in zip(df_rome['Coordinates'], df_rome['Terrain'])
                    if pd.notnull(coord) and pd.notnull(name)
                ]
            else:
                markers_rome = []

            # Reset graphs to their initial state
            updated_bar_plot = generate_interactive_bar_plot_rome(df_rome)
            updated_pie_chart = generate_interactive_pie_chart_rome(df_rome)
            updated_pie_chart_weather = generate_interactive_pie_chart_2_rome(df_rome)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_rome(df_rome)

            # Recalculate general insights
            most_common_source_rome = df_rome['Source'].mode().iloc[0] if not df_rome['Source'].dropna().mode().empty else None
            most_common_tod_rome = df_rome['Time of the day'].mode().iloc[0] if not df_rome['Time of the day'].dropna().mode().empty else None
            most_common_terrain_rome = df_rome['Terrain'].mode().iloc[0] if not df_rome['Terrain'].dropna().mode().empty else None
            most_common_tilt_rome = df_rome['Camera tilt'].mode().iloc[0] if not df_rome['Camera tilt'].dropna().mode().empty else None
            avg_dur_rome = round(df_rome['Duration'].mean(), 2)

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
                df_rome.to_dict('records'),
                markers_rome,
                'All', 'All', 'All', 'All', 'All',
                f"Total Records: {len(df_rome)}",
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

        # Default filtering logic (apply dropdowns, charts, etc.)
        filtered_df = df_rome.copy()

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
        if 'Coordinates' in filtered_df.columns and 'Terrain' in filtered_df.columns:
            markers_rome = [
                dl.Marker(position=eval(coord), children=[dl.Popup(name)])
                for coord, name in zip(filtered_df['Coordinates'], filtered_df['Terrain'])
                if pd.notnull(coord) and pd.notnull(name)
            ]
        else:
            markers_rome = []

        # Count the records after filtering
        record_count_text = f"Total Records: {len(filtered_df)}"

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
            None,
            None,
            None,
            None
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
    SHEET_ID_MADRID = '1hZohrG1LwnLm3pvqeD8n8_1yECklyiM8hezLTQXAy2Q'
    RANGE_MADRID = 'Sheet1!A1:Y660'

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
replacements = {
    'NaN': np.nan,
    'NULL': np.nan,
    'None': np.nan,
    '': np.nan,
}

# Option 2: If you prefer a column-by-column approach
for col in df_madrid.columns[9:-1]:
    df_madrid[col] = df_madrid[col].replace(replacements)
    
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

# Convert 'Duration' column
df_madrid['Duration'] = df_madrid['Duration'].apply(convert_to_minutes)
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
        children=[dl.Popup(name)], 
        id="madrid-mark" + str(i)
    )
    for i, (coord, name) in enumerate(zip(df_madrid['Coordinates'], df_madrid['Terrain']))
    if ',' in coord  # Ensure coord is valid
    for lat, lon in [coord.split(',')]  # Safely split latitude and longitude
]

df_madrid = df_madrid[df_madrid['Coordinates'].str.contains(',', na=False)]
df_madrid[['Latitude', 'Longitude']] = df_madrid['Coordinates'].str.split(',', expand=True)
df_madrid['Latitude'] = df_madrid['Latitude'].astype(float)
df_madrid['Longitude'] = df_madrid['Longitude'].astype(float)


def tab3_layout():
    return html.Div(
        style=background_style_madrid,
        children=[
            dcc.Interval(id='madrid-interval-component', interval=1*10000, n_intervals=0),
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
                                    dl.LayerGroup(id="madrid-map-layer", children=markers_madrid)
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
    ],
    [
        Input('madrid-bar-plot', 'clickData'),
        Input('madrid-pie-chart', 'clickData'),
        Input('madrid-pie-chart-weather', 'clickData'),
        Input('madrid-bar-plot-logos','clickData'),
        Input('madrid-reset-btn', 'n_clicks'),
        Input('madrid-duration-slider', 'value'),
        Input('madrid-Terrain', 'value'),
        Input('madrid-Occlusion', 'value'),
        Input('madrid-VQ', 'value'),
        Input('madrid-Camera_Tilt', 'value'),
        Input('madrid-Distance_Building', 'value'),
        Input('madrid-interval-component', 'n_intervals')
    ]
)
def handle_table_and_refresh_madrid(
    bar_clickData, pie_clickData, pie_weather_clickData, bar_2_clickData, reset_clicks, duration_range,
    selected_terrain, selected_occluded, selected_VQ, selected_tilt, selected_distance, n_intervals
):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    
    try:
        global df_madrid, min_dur_madrid, max_dur_madrid
        # If the interval triggered the callback, reload the data
        if triggered_id == 'madrid-interval-component.n_intervals':
    # Reload the data
            df_madrid = load_madrid_data()
            df_madrid['Duration'] = df_madrid['Duration'].apply(convert_to_minutes)
            min_dur_madrid = df_madrid['Duration'].min()
            max_dur_madrid = df_madrid['Duration'].max()
            df_madrid = df_madrid[df_madrid['Coordinates'].str.contains(',', na=False)]
            df_madrid[['Latitude', 'Longitude']] = df_madrid['Coordinates'].str.split(',', expand=True)
            df_madrid['Latitude'] = df_madrid['Latitude'].astype(float)
            df_madrid['Longitude'] = df_madrid['Longitude'].astype(float)

            # Apply current filters to the refreshed data
            filtered_df = df_madrid.copy()

            if duration_range:
                filtered_df = filtered_df[
                    (filtered_df['Duration'] >= duration_range[0]) & 
                    (filtered_df['Duration'] <= duration_range[1])
                ]
            if selected_terrain != 'All':
                filtered_df = filtered_df[filtered_df['Terrain'].notna() & (filtered_df['Terrain'] == selected_terrain)]
            if selected_occluded != 'All':
                filtered_df = filtered_df[filtered_df['Occluded'].notna() & (filtered_df['Occluded'] == selected_occluded)]
            if selected_VQ != 'All':
                filtered_df = filtered_df[filtered_df['Video quality'].notna() & (filtered_df['Video quality'] == selected_VQ)]
            if selected_tilt != 'All':
                filtered_df = filtered_df[filtered_df['Camera tilt'].notna() & (filtered_df['Camera tilt'] == selected_tilt)]
            if selected_distance != 'All':
                filtered_df = filtered_df[filtered_df['Distance from building'].notna() & (filtered_df['Distance from building'] == selected_distance)]


            # Generate updated map markers
            markers_madrid = [
                dl.Marker(position=eval(coord), children=[dl.Popup(name)])
                for coord, name in zip(filtered_df['Coordinates'], filtered_df['Terrain'])
                if pd.notnull(coord) and pd.notnull(name)
            ]

            # Count the records after filtering
            record_count_text = f"Total Records: {len(filtered_df)}"

            # Refresh graphs for filtered data
            updated_bar_plot = generate_interactive_bar_plot_madrid(filtered_df)
            updated_pie_chart = generate_interactive_pie_chart_madrid(filtered_df)
            updated_pie_chart_weather = generate_interactive_pie_chart_2_madrid(filtered_df)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_madrid(filtered_df)

            # Recalculate general insights
            most_common_source_madrid = filtered_df['Source'].mode().iloc[0] if not filtered_df['Source'].dropna().mode().empty else None
            most_common_tod_madrid = filtered_df['Time of the day'].mode().iloc[0] if not filtered_df['Time of the day'].dropna().mode().empty else None
            most_common_terrain_madrid = filtered_df['Terrain'].mode().iloc[0] if not filtered_df['Terrain'].dropna().mode().empty else None
            most_common_tilt_madrid = filtered_df['Camera tilt'].mode().iloc[0] if not filtered_df['Camera tilt'].dropna().mode().empty else None
            avg_dur_madrid = round(filtered_df['Duration'].mean(), 2)

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
                                f"The majority of the videos are from {most_common_source_madrid}.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"They were mostly shot in {most_common_tilt_madrid} tilt, in "
                                f"{most_common_tod_madrid} and in {most_common_terrain_madrid} terrain.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"The average video duration is {avg_dur_madrid} seconds.",
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
                dash.no_update,
                dash.no_update,  # Preserve Terrain filter
                dash.no_update,  # Preserve Occlusion filter
                dash.no_update,  # Preserve VQ filter
                dash.no_update,  # Preserve Camera Tilt filter
                dash.no_update,  # Preserve Distance from Building filter
                dash.no_update,
                min_dur_madrid,
                max_dur_madrid,
                duration_range,
                dash.no_update,  # Preserve Terrain filter
                dash.no_update,  # Preserve Occlusion filter
                dash.no_update,  # Preserve VQ filter
                dash.no_update,  # Preserve Camera Tilt filter
                dash.no_update,
                None,
                None,
                None,
                None
            )

        if triggered_id == 'madrid-reset-btn.n_clicks':
            # Reset filters and map markers
            if 'Coordinates' in df_madrid.columns and 'Terrain' in df_madrid.columns:
                markers_madrid = [
                    dl.Marker(position=eval(coord), children=[dl.Popup(name)])
                    for coord, name in zip(df_madrid['Coordinates'], df_madrid['Terrain'])
                    if pd.notnull(coord) and pd.notnull(name)
                ]
            else:
                markers_madrid = []

            # Reset graphs to their initial state
            updated_bar_plot = generate_interactive_bar_plot_madrid(df_madrid)
            updated_pie_chart = generate_interactive_pie_chart_madrid(df_madrid)
            updated_pie_chart_weather = generate_interactive_pie_chart_2_madrid(df_madrid)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_madrid(df_madrid)

            # Recalculate general insights
            most_common_source_madrid = df_madrid['Source'].mode().iloc[0] if not df_madrid['Source'].dropna().mode().empty else None
            most_common_tod_madrid = df_madrid['Time of the day'].mode().iloc[0] if not df_madrid['Time of the day'].dropna().mode().empty else None
            most_common_terrain_madrid = df_madrid['Terrain'].mode().iloc[0] if not df_madrid['Terrain'].dropna().mode().empty else None
            most_common_tilt_madrid = df_madrid['Camera tilt'].mode().iloc[0] if not df_madrid['Camera tilt'].dropna().mode().empty else None
            avg_dur_madrid = round(df_madrid['Duration'].mean(), 2)

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
                                f"The majority of the videos are from {most_common_source_madrid}.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"They were mostly shot in {most_common_tilt_madrid} tilt, in "
                                f"{most_common_tod_madrid} and in {most_common_terrain_madrid} terrain.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            ),
                            html.Li(
                                f"The average video duration is {avg_dur_madrid} seconds.",
                                style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                            )
                        ],
                        style={'padding': '10px', 'marginLeft': '10px'}
                    ),
                ],
                style={'padding': '10px'}
            )

            return (
                df_madrid.to_dict('records'),
                markers_madrid,
                'All', 'All', 'All', 'All', 'All',
                f"Total Records: {len(df_madrid)}",
                min_dur_madrid,
                max_dur_madrid,
                [min_dur_madrid, max_dur_madrid],
                updated_bar_plot,
                updated_pie_chart,
                updated_pie_chart_weather,
                updated_bar_plot_logos,
                general_insights,
                None,
                None,
                None,
                None
            )

        # Default filtering logic (apply dropdowns, charts, etc.)
        filtered_df = df_madrid.copy()

        # Apply filters from duration range and dropdowns
        filtered_df = filtered_df[
            (filtered_df['Duration'] >= duration_range[0]) &
            (filtered_df['Duration'] <= duration_range[1])
        ]
        if selected_terrain != 'All':
            filtered_df = filtered_df[filtered_df['Terrain'].notna() & (filtered_df['Terrain'] == selected_terrain)]
        if selected_occluded != 'All':
            filtered_df = filtered_df[filtered_df['Occluded'].notna() & (filtered_df['Occluded'] == selected_occluded)]
        if selected_VQ != 'All':
            filtered_df = filtered_df[filtered_df['Video quality'].notna() & (filtered_df['Video quality'] == selected_VQ)]
        if selected_tilt != 'All':
            filtered_df = filtered_df[filtered_df['Camera tilt'].notna() & (filtered_df['Camera tilt'] == selected_tilt)]
        if selected_distance != 'All':
            filtered_df = filtered_df[filtered_df['Distance from building'].notna() & (filtered_df['Distance from building'] == selected_distance)]


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
        if 'Coordinates' in filtered_df.columns and 'Terrain' in filtered_df.columns:
            markers_madrid = [
                dl.Marker(position=eval(coord), children=[dl.Popup(name)])
                for coord, name in zip(filtered_df['Coordinates'], filtered_df['Terrain'])
                if pd.notnull(coord) and pd.notnull(name)
            ]
        else:
            markers_madrid = []

        # Count the records after filtering
        record_count_text = f"Total Records: {len(filtered_df)}"

        # Refresh graphs for filtered data
        updated_bar_plot = generate_interactive_bar_plot_madrid(filtered_df)
        updated_pie_chart = generate_interactive_pie_chart_madrid(filtered_df)
        updated_pie_chart_weather = generate_interactive_pie_chart_2_madrid(filtered_df)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_madrid(filtered_df)

        # Recalculate general insights
        most_common_source_madrid = filtered_df['Source'].mode().iloc[0] if not filtered_df['Source'].dropna().mode().empty else None
        most_common_tod_madrid = filtered_df['Time of the day'].mode().iloc[0] if not filtered_df['Time of the day'].dropna().mode().empty else None
        most_common_terrain_madrid = filtered_df['Terrain'].mode().iloc[0] if not filtered_df['Terrain'].dropna().mode().empty else None
        most_common_tilt_madrid = filtered_df['Camera tilt'].mode().iloc[0] if not filtered_df['Camera tilt'].dropna().mode().empty else None
        avg_dur_madrid = round(filtered_df['Duration'].mean(), 2)

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
                            f"The majority of the videos are from {most_common_source_madrid}.",
                            style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                        ),
                        html.Li(
                            f"They were mostly shot in {most_common_tilt_madrid} tilt, in "
                            f"{most_common_tod_madrid} and in {most_common_terrain_madrid} terrain.",
                            style={'fontSize': '18px', 'marginBottom': '10px', 'fontWeight': 'bold', 'textAlign': 'justify', 'color': 'white'}
                        ),
                        html.Li(
                            f"The average video duration is {avg_dur_madrid} seconds.",
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
            markers_madrid,
            selected_terrain,
            selected_occluded,
            selected_VQ,
            selected_tilt,
            selected_distance,
            record_count_text,
            min_dur_madrid,
            max_dur_madrid,
            duration_range,
            updated_bar_plot,
            updated_pie_chart,
            updated_pie_chart_weather,
            updated_bar_plot_logos,
            general_insights,
            None,
            None,
            None,
            None
        )

    except Exception as e:
        print(f"Error: {e}")
        raise dash.exceptions.PreventUpdate

def load_barcelona_data():
    global df_bar
    # Google Sheet ID and Range for barcelona
    SHEET_ID_barcelona = '14hSdXXSL_ehJO3tdogLQcVahqIuDy6UREUEv7LusVU8'
    RANGE_barcelona = 'Barcelona!A1:Q305'

    # Access the Google Sheet for barcelona
    result = sheet.values().get(spreadsheetId=SHEET_ID_barcelona, range=RANGE_barcelona).execute()
    values = result.get('values', [])

    # Convert the data to a pandas DataFrame
    if values:
        headers = values[0]  # Assuming the first row is the header
        data = values[1:]    # Rest is the data
        df_bar = pd.DataFrame(data, columns=headers)
    else:
        print("No data found for barcelona.")
        df_bar = pd.DataFrame()

    return df_bar

df_bar = load_barcelona_data()
df_barcelona=df_bar.copy()

# Process barcelona Data
first_column_name_barcelona = df_barcelona.columns[0]
df_barcelona[first_column_name_barcelona] = df_barcelona[first_column_name_barcelona].apply(
    lambda x: f"[{x}]({x})" if pd.notnull(x) else x
)
replacements = {
    'NaN': np.nan,
    'NULL': np.nan,
    '': np.nan,
}

# Option 2: If you prefer a column-by-column approach
for col in df_barcelona.columns[8:-1]:
    df_barcelona[col] = df_barcelona[col].replace(replacements)
    
unique_tod_barcelona = df_barcelona['Time of the day'].dropna().unique()
unique_weather_barcelona = df_barcelona['Weather'].dropna().unique()
unique_terrain_barcelona = df_barcelona['Terrain'].dropna().unique()
unique_occluded_barcelona = df_barcelona['Occluded'].dropna().unique()
unique_tilt_barcelona = df_barcelona['Camera tilt'].dropna().unique()
unique_distance_barcelona = df_barcelona['Distance from building'].dropna().unique()
unique_vq_barcelona = df_barcelona['Video quality'].dropna().unique()

most_common_tod_barcelona = df_barcelona['Time of the day'].mode().iloc[0] if not df_barcelona['Time of the day'].dropna().mode().empty else None
most_common_terrain_barcelona = df_barcelona['Terrain'].mode().iloc[0] if not df_barcelona['Terrain'].dropna().mode().empty else None
most_common_tilt_barcelona = df_barcelona['Camera tilt'].mode().iloc[0] if not df_barcelona['Camera tilt'].dropna().mode().empty else None

# Convert 'Duration' column
df_barcelona ['Duration'] = (df_barcelona['Finish Time'].apply(convert_to_minutes_2) - df_barcelona['Start Time'].apply(convert_to_minutes_2))
avg_dur_barcelona = round(df_barcelona['Duration'].mean(), 2)
min_dur_barcelona = df_barcelona['Duration'].min()
max_dur_barcelona = df_barcelona['Duration'].max()


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


background_style_barcelona = {
     "background-size": "cover",
    "background-position": "center",
    "height": "250vh",
    "padding": "10px",
    "background-color": 'black',
}



def generate_interactive_bar_plot_2_barcelona(df_barcelona):
    source_counts = df_barcelona['Logos and text'].value_counts().reset_index()
    source_counts.columns = ['Logos and text', 'Count']

    fig = px.bar(
        source_counts, 
        x='Logos and text', 
        y='Count', 
        color='Logos and text', 
        color_discrete_map=color_map2_barcelona,
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
        ),
    )

    return fig

def generate_interactive_pie_chart_barcelona(df_barcelona):
    tod_counts = df_barcelona['Time of the day'].value_counts().reset_index()
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
        title_font=dict(color='white',size=24),
        hoverlabel=dict(font=dict(size=24, color='white'))

    )

    return fig

def generate_interactive_bar_chart_weather_barcelona(df_barcelona):
    # Calculate the counts for each Weather category
    weather_counts = df_barcelona['Weather'].value_counts().reset_index()
    weather_counts.columns = ['Weather', 'Count']
    
    # Create a bar chart
    fig = px.bar(
        weather_counts,
        x='Weather',
        y='Count',
        color='Weather',
        color_discrete_map=color_map3_barcelona,  # Same color map you used for the pie chart
        title='Weather'
    )
    
    # Customize the bar traces
    fig.update_traces(
        marker_line_width=1.5,
        hovertemplate="Count: %{y}"
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
        title_font=dict(color='white',size=24),
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

def generate_interactive_pie_chart_status(df_barcelona):
    color_map ={'done': '#006400',
                'not started': '#FF0000',
                'not found': '	#DC143C',
                'irrelevant': '#00FFFF'}
    
    status_counts = df_barcelona['Status'].value_counts().reset_index()
    status_counts.columns = ['Status', 'Count']
    
    fig = px.pie(
        status_counts,
        names='Status',
        values='Count',
        color='Status',
        color_discrete_sequence= color_map,
        title='Status'
    )
    
    depth_values = [0.05 + i * 0.01 for i in range(len(status_counts))]
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
        title_font=dict(color='white',size=24),
        hoverlabel=dict(font=dict(size=24, color='white'))
    )

    return fig

# Update dropdown options to include an "All" option
unique_occluded_barcelona_1 = ['All'] + list(unique_occluded_barcelona)
unique_terrain_barcelona_1 = ['All'] + list(unique_terrain_barcelona)
unique_tilt_barcelona_1 = ['All'] + list(unique_tilt_barcelona)
unique_distance_barcelona_1 = ['All'] + list(unique_distance_barcelona)
unique_vq_barcelona_1 = ['All'] + list(unique_vq_barcelona)

# Create Map Markers
markers_barcelona = [
    dl.Marker(
        position=(float(lat), float(lon)), 
        children=[dl.Popup(name)], 
        id="barcelona-mark" + str(i)
    )
    for i, (coord, name) in enumerate(zip(df_barcelona['Coordinates'], df_barcelona['Terrain']))
    if ',' in coord  # Ensure coord is valid
    for lat, lon in [coord.split(',')]  # Safely split latitude and longitude
]

df_barcelona = df_barcelona[df_barcelona['Coordinates'].str.contains(',', na=False)]
df_barcelona[['Latitude', 'Longitude']] = df_barcelona['Coordinates'].str.split(',', expand=True)
df_barcelona['Latitude'] = df_barcelona['Latitude'].astype(float)
df_barcelona['Longitude'] = df_barcelona['Longitude'].astype(float)
    


def tab4_layout():
    return html.Div(
        style=background_style_barcelona,
        children=[
            dcc.Interval(id='barcelona-interval-component', interval=1*10000, n_intervals=0),
            dcc.ConfirmDialog(
                id='barcelona-confirm-dialog',
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
                                    dl.LayerGroup(id="barcelona-map-layer", children=markers_barcelona)
                                ],
                                center=(41.4035011,2.1743682),  # Updated to barcelona coordinates
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
                        id='barcelona-record-count',
                        style={'textAlign': 'left', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
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
                                min=min_dur_barcelona,
                                max=max_dur_barcelona,
                                step=0.1,
                                value=[min_dur_barcelona, max_dur_barcelona],
                                updatemode='mouseup',
                                marks={int(min_dur_barcelona): str(int(min_dur_barcelona)), int(max_dur_barcelona): str(int(max_dur_barcelona))},
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
                                    dcc.Graph(id='barcelona-pie-chart', figure=generate_interactive_pie_chart_barcelona(df_barcelona)),
                                    width=6
                                ),
                                dbc.Col(
                                    dcc.Graph(id='barcelona-pie-chart-weather', figure=generate_interactive_bar_chart_weather_barcelona(df_barcelona)),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                                dbc.Col(
                                    dcc.Graph(id='barcelona-bar-plot-logos', figure=generate_interactive_bar_plot_2_barcelona(df_barcelona)),
                                    width=6,
                                    style={'marginTop': '30px'}
                                ),
                                dbc.Col(
                                    dcc.Graph(id='barcelona-status-pie', figure=generate_interactive_pie_chart_status(df_barcelona)),
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
                        children=[
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
                                ] + [{"name": i, "id": i} for i in df_barcelona.columns[1:]],
                                data=df_barcelona.to_dict('records'),
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

# ---------------------------- barcelona Callback ----------------------------

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
        Output('barcelona-bar-plot-logos','figure'),
        Output('barcelona-status-pie','figure'),
        Output('barcelona-general-insights', 'children'),
        Output('barcelona-pie-chart', 'clickData'),
        Output('barcelona-pie-chart-weather', 'clickData'),
        Output('barcelona-bar-plot-logos','clickData'),
    ],
    [
        Input('barcelona-pie-chart', 'clickData'),
        Input('barcelona-pie-chart-weather', 'clickData'),
        Input('barcelona-bar-plot-logos','clickData'),
        Input('barcelona-status-pie','clickData'),
        Input('barcelona-reset-btn', 'n_clicks'),
        Input('barcelona-duration-slider', 'value'),
        Input('barcelona-Terrain', 'value'),
        Input('barcelona-Occlusion', 'value'),
        Input('barcelona-VQ', 'value'),
        Input('barcelona-Camera_Tilt', 'value'),
        Input('barcelona-Distance_Building', 'value'),
        Input('barcelona-interval-component', 'n_intervals')
    ]
)
def handle_table_and_refresh_barcelona(
    pie_clickData, pie_weather_clickData, bar_2_clickData,status_pie_clickData, reset_clicks, duration_range,
    selected_terrain, selected_occluded, selected_VQ, selected_tilt, selected_distance, n_intervals
):
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None
    
    try:
        # Make sure df_barcelona, min_dur_barcelona, max_dur_barcelona
        # are accessible (using global or otherwise).
        global df_barcelona, min_dur_barcelona, max_dur_barcelona
        
        # ---------------------------------------------------------------------
        # 1) If the interval triggered the callback -> Reload/refresh data
        # ---------------------------------------------------------------------
        if triggered_id == 'barcelona-interval-component.n_intervals':
            # Reload data
            df_bar = load_barcelona_data()
            df_barcelona = df_bar.copy()

            # Recalculate Duration
            df_barcelona['Duration'] = (
                df_barcelona['Finish Time'].apply(convert_to_minutes_2)
                - df_barcelona['Start Time'].apply(convert_to_minutes_2)
            )
            min_dur_barcelona = df_barcelona['Duration'].min()
            max_dur_barcelona = df_barcelona['Duration'].max()

            # Convert coordinates
            df_barcelona = df_barcelona[df_barcelona['Coordinates'].str.contains(',', na=False)]
            df_barcelona[['Latitude', 'Longitude']] = df_barcelona['Coordinates'].str.split(',', expand=True)
            df_barcelona['Latitude'] = df_barcelona['Latitude'].astype(float)
            df_barcelona['Longitude'] = df_barcelona['Longitude'].astype(float)

            # Apply current filters to the refreshed data
            filtered_df = df_barcelona.copy()

            if duration_range:
                filtered_df = filtered_df[
                    (filtered_df['Duration'] >= duration_range[0]) &
                    (filtered_df['Duration'] <= duration_range[1])
                ]
            if selected_terrain != 'All':
                filtered_df = filtered_df[filtered_df['Terrain'].notna() & (filtered_df['Terrain'] == selected_terrain)]
            if selected_occluded != 'All':
                filtered_df = filtered_df[filtered_df['Occluded'].notna() & (filtered_df['Occluded'] == selected_occluded)]
            if selected_VQ != 'All':
                filtered_df = filtered_df[filtered_df['Video quality'].notna() & (filtered_df['Video quality'] == selected_VQ)]
            if selected_tilt != 'All':
                filtered_df = filtered_df[filtered_df['Camera tilt'].notna() & (filtered_df['Camera tilt'] == selected_tilt)]
            if selected_distance != 'All':
                filtered_df = filtered_df[
                    filtered_df['Distance from building'].notna()
                    & (filtered_df['Distance from building'] == selected_distance)
                ]

            # Markers
            markers_barcelona = [
                dl.Marker(
                    position=(row['Latitude'], row['Longitude']),
                    children=[dl.Popup(row['Terrain'])]
                )
                for _, row in filtered_df.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            ]

            record_count_text = f"Total Records: {len(filtered_df)}"
            updated_pie_chart = generate_interactive_pie_chart_barcelona(filtered_df)
            updated_pie_chart_weather = generate_interactive_bar_chart_weather_barcelona(filtered_df)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_barcelona(filtered_df)
            updated_status_pie = generate_interactive_pie_chart_status(filtered_df)

            # General insights
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
            avg_dur_barcelona = round(filtered_df['Duration'].mean(), 2)

            general_insights = html.Div(
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
                            ),
                        ],
                        style={'padding': '10px', 'marginLeft': '10px'}
                    ),
                ],
                style={'padding': '10px'}
            )

            #
            # IMPORTANT: Return *all 18 outputs* in the correct order
            #
            return (
                filtered_df.to_dict('records'),      # 1) table data
                markers_barcelona,                   # 2) map-layer children
                selected_terrain,                    # 3) Terrain dropdown value
                selected_occluded,                   # 4) Occlusion dropdown value
                selected_VQ,                         # 5) VQ dropdown value
                selected_tilt,                       # 6) Camera Tilt dropdown value
                selected_distance,                   # 7) Distance Building dropdown value
                record_count_text,                   # 8) record-count text
                min_dur_barcelona,                   # 9) slider min
                max_dur_barcelona,                   # 10) slider max
                duration_range,                      # 11) slider value
                updated_pie_chart,                   # 12) pie chart figure
                updated_pie_chart_weather,           # 13) weather pie figure
                updated_bar_plot_logos,              # 14) bar plot figure
                updated_status_pie,
                general_insights,                    # 15) general insights children
                None,                                # 16) pie-chart clickData (reset)
                None,                                # 17) pie-chart-weather clickData (reset)
                None                                 # 18) bar-plot-logos clickData (reset)
            )

        # ---------------------------------------------------------------------
        # 2) If the Reset button was clicked
        # ---------------------------------------------------------------------
        if triggered_id == 'barcelona-reset-btn.n_clicks':
            # Reset everything
            markers_barcelona = [
                dl.Marker(
                    position=(row['Latitude'], row['Longitude']),
                    children=[dl.Popup(row['Terrain'])]
                )
                for _, row in df_barcelona.iterrows()
                if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
            ]
            updated_pie_chart = generate_interactive_pie_chart_barcelona(df_barcelona)
            updated_pie_chart_weather = generate_interactive_bar_chart_weather_barcelona(df_barcelona)
            updated_bar_plot_logos = generate_interactive_bar_plot_2_barcelona(df_barcelona)
            updated_status_pie = generate_interactive_pie_chart_status(df_barcelona)

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
            avg_dur_barcelona = round(df_barcelona['Duration'].mean(), 2)

            general_insights = html.Div(
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
                            ),
                        ],
                        style={'padding': '10px', 'marginLeft': '10px'}
                    ),
                ],
                style={'padding': '10px'}
            )

            record_count_text = f"Total Records: {len(df_barcelona)}"

            #
            # Return all 18 outputs in the correct order
            #
            return (
                df_barcelona.to_dict('records'),     # 1) table data
                markers_barcelona,                   # 2) map-layer children
                'All',                               # 3) Terrain reset
                'All',                               # 4) Occluded reset
                'All',                               # 5) VQ reset
                'All',                               # 6) Tilt reset
                'All',                               # 7) Distance reset
                record_count_text,                   # 8) record-count
                min_dur_barcelona,                   # 9) slider min
                max_dur_barcelona,                   # 10) slider max
                [min_dur_barcelona, max_dur_barcelona],  # 11) slider value
                updated_pie_chart,                   # 12) updated chart
                updated_pie_chart_weather,           # 13) updated weather chart
                updated_bar_plot_logos,              # 14) updated bar chart
                updated_status_pie,
                general_insights,                    # 15) insights
                None,                                # 16) reset pie-chart click
                None,                                # 17) reset weather click
                None                                 # 18) reset bar-logos click
            )

        # ---------------------------------------------------------------------
        # 3) Otherwise, apply normal filtering logic
        # ---------------------------------------------------------------------
        filtered_df = df_barcelona.copy()

        # Duration slider filter
        filtered_df = filtered_df[
            (filtered_df['Duration'] >= duration_range[0]) &
            (filtered_df['Duration'] <= duration_range[1])
        ]
        # Dropdown filters
        if selected_terrain != 'All':
            filtered_df = filtered_df[filtered_df['Terrain'].notna() & (filtered_df['Terrain'] == selected_terrain)]
        if selected_occluded != 'All':
            filtered_df = filtered_df[filtered_df['Occluded'].notna() & (filtered_df['Occluded'] == selected_occluded)]
        if selected_VQ != 'All':
            filtered_df = filtered_df[filtered_df['Video quality'].notna() & (filtered_df['Video quality'] == selected_VQ)]
        if selected_tilt != 'All':
            filtered_df = filtered_df[filtered_df['Camera tilt'].notna() & (filtered_df['Camera tilt'] == selected_tilt)]
        if selected_distance != 'All':
            filtered_df = filtered_df[
                filtered_df['Distance from building'].notna()
                & (filtered_df['Distance from building'] == selected_distance)
            ]

        # Pie chart (Time of day) click
        if pie_clickData:
            clicked_tod = pie_clickData['points'][0]['label']
            filtered_df = filtered_df[filtered_df['Time of the day'] == clicked_tod]

        # Pie chart (Weather) click
        if pie_weather_clickData:
            clicked_weather = pie_weather_clickData['points'][0]['label']
            filtered_df = filtered_df[filtered_df['Weather'] == clicked_weather]

        # Bar chart (Logos and text) click
        if bar_2_clickData:
            clicked_logo = bar_2_clickData['points'][0]['x']
            filtered_df = filtered_df[filtered_df['Logos and text'] == clicked_logo]
            
        if status_pie_clickData:
            clicked_logo = status_pie_clickData['points'][0]['x']
            filtered_df = filtered_df[filtered_df['Status'] == clicked_logo]            

        # Create markers
        markers_barcelona = [
            dl.Marker(
                position=(row['Latitude'], row['Longitude']),
                children=[dl.Popup(row['Terrain'])]
            )
            for _, row in filtered_df.iterrows()
            if not pd.isnull(row['Latitude']) and not pd.isnull(row['Longitude'])
        ]

        record_count_text = f"Total Records: {len(filtered_df)}"

        # Refresh graphs
        updated_pie_chart = generate_interactive_pie_chart_barcelona(filtered_df)
        updated_pie_chart_weather = generate_interactive_bar_chart_weather_barcelona(filtered_df)
        updated_bar_plot_logos = generate_interactive_bar_plot_2_barcelona(filtered_df)
        updated_status_pie = generate_interactive_pie_chart_status(filtered_df)

        # Insights
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
        avg_dur_barcelona = round(filtered_df['Duration'].mean(), 2)

        general_insights = html.Div(
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
                        ),
                    ],
                    style={'padding': '10px', 'marginLeft': '10px'}
                ),
            ],
            style={'padding': '10px'}
        )

        #
        # Return all 18 outputs in the correct order
        #
        return (
            filtered_df.to_dict('records'),     # 1) table data
            markers_barcelona,                  # 2) map-layer children
            selected_terrain,                   # 3) Terrain value
            selected_occluded,                  # 4) Occlusion value
            selected_VQ,                        # 5) VQ value
            selected_tilt,                      # 6) Camera Tilt value
            selected_distance,                  # 7) Distance Bldg value
            record_count_text,                  # 8) record-count text
            min_dur_barcelona,                  # 9) slider min
            max_dur_barcelona,                  # 10) slider max
            duration_range,                     # 11) slider value
            updated_pie_chart,                  # 12) pie chart figure
            updated_pie_chart_weather,          # 13) weather pie figure
            updated_bar_plot_logos,             # 14) bar plot figure
            updated_status_pie,
            general_insights,                   # 15) general insights
            None,                               # 16) pie-chart clickData
            None,                               # 17) pie-chart-weather clickData
            None                                # 18) bar-plot-logos clickData
        )

    except Exception as e:
        print(f"Error: {e}")
        raise dash.exceptions.PreventUpdate

    
    
app.layout = html.Div(
    [
        dcc.Tabs(
            [
                dcc.Tab(label='Geo-Location-London', children=tab1_layout(),style=tab_style, selected_style=selected_tab_style,),
                dcc.Tab(label='Geo-Location-Rome', children=tab2_layout(),style=tab_style,selected_style=selected_tab_style),
                dcc.Tab(label='Geo-Location-Madrid', children=tab3_layout(),style=tab_style,selected_style=selected_tab_style),
                dcc.Tab(label='Geo-Location-Barcelona', children=tab4_layout(),style=tab_style,selected_style=selected_tab_style),

            ]
        )
    ]
)

if __name__ == '__main__':
    app.run_server(host='100.118.47.56', port=8050, debug=True)