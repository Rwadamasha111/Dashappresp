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

# Initialize the app
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server 


# ✅ Service account and scopes
SERVICE_ACCOUNT_FILE = r"C:\Users\rwad\Downloads\arabic-transcription-435113-c8120df00a35 (1).json"
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
print (OD_ATT)
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

    

    


# Save the transposed DataFrame
#transposed_df.to_csv(r"C:\Users\rwad\OneDrive\Documents\classes_distribution\class.csv", index=True)

# Run the app
if __name__ == '__main__':
    app.run(host='100.84.182.85', port=8050, debug=True)
