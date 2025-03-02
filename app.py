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
python_files = [f for f in os.listdir(current_dir) if f.endswith(".py") and f != "app.py"]

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

# ✅ Path to your service account key file
SERVICE_ACCOUNT_FILE = "C:/rwad/gentle-bounty-449311-g9-eb09307f62ee.json"

# ✅ FIX: Use correct API scope (Full Edit Access)
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# ✅ Authenticate Google Sheets API
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# ✅ Google Spreadsheet IDs
SPREADSHEET_ID_COORDINATES = "1epNqVVLwcG0a5YI0_kgKQa5G6_q6v3F4eWzX4PD4CUg"
SPREADSHEET_ID_OBJ_ANN = "1JQ960HoB0VVTskzma3zd3Il7khFTWVbPWTlLT8v6NUU"
SPREADSHEET_ID_TRANSCRIPTION = "1ZPcwPcIrGU-brYoGrNLLcjRJbRCNaLfaP3s0shS7ZeI"
SPREADSHEET_ID_OVERALL_FRAMES = "1pSjFV6o0PHzuTc2pCqL6uJH1VAJ2DPSbOBMZQPDZoIs"
SPREADSHEET_ID_OTB = "1SD9vtPyeUwUj366zhRNxlLyegYaLlLca4A7DmT6b020"
SPREADSHEET_ID_ATTRIBUTES = "15NRg3T2B9jPWEn3HzzNXxOgIYe8U0x8a_Ael28d23vk"
SPREADSHEET_ID_POI = "1-XZPzpql4o0Flq5WHZf8GjuPoXTY_vVFqkYq9QKOuMU"
Voice_rec = "1LoUYrB_gFCqaMiZ-D31hc4mENCWF42iPvldxi7e2NGU"

# ✅ Sheet Names
OBJ_ANN_SHEET = "Obj_ann_with_total"
TRANSCRIPTION_SHEET = "output_transcriptions"
COORDINATES_SHEET = "Coordinates"
OVERALL_FRAMES_SHEET = "Overall_ann_od"
ann_per_obj = "Overall_ann_od_per_obj"
OTB_SHEET = "OTB2"
ATTRIBUTES_SHEET = "OTB3"
POI_SHEET = "POI"
Voice_sheet = "800 OG copy"



# ✅ Function to Read Google Sheets into Pandas DataFrame (Fixes Duplicate Headers & Converts Numeric Data)
def read_google_sheet(spreadsheet_id, sheet_name):
    """Reads a Google Sheet into a Pandas DataFrame and ensures unique column headers and numeric conversion."""
    sheet = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    raw_data = sheet.get_all_values()  # Get all values including headers

    if not raw_data or len(raw_data) < 2:
        print(f"❌ Error: The sheet '{sheet_name}' in {spreadsheet_id} is empty or has no data!")
        return pd.DataFrame()  # Return an empty DataFrame
    

    headers = raw_data[0]  # Extract the first row as headers
    records = raw_data[1:]  # Extract remaining rows as data

    # ✅ Ensure unique column names by appending a number if duplicates exist
    unique_headers = []
    seen_headers = {}

    for col in headers:
        if col in seen_headers:
            seen_headers[col] += 1
            new_col = f"{col}_{seen_headers[col]}"  # Rename duplicate headers
        else:
            seen_headers[col] = 0
            new_col = col
        unique_headers.append(new_col)

    # ✅ Convert to Pandas DataFrame
    df = pd.DataFrame(records, columns=unique_headers)

    # ✅ Convert numeric columns automatically
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='ignore')  # Convert numbers where possible

    return df

# ✅ Read Data from Google Sheets
df = read_google_sheet(SPREADSHEET_ID_OBJ_ANN, OBJ_ANN_SHEET)
df3 = read_google_sheet(SPREADSHEET_ID_TRANSCRIPTION, TRANSCRIPTION_SHEET)
coordinates_df = read_google_sheet(SPREADSHEET_ID_COORDINATES, COORDINATES_SHEET)
Overall_frames_ann_per_vid = read_google_sheet(SPREADSHEET_ID_OVERALL_FRAMES, OVERALL_FRAMES_SHEET)
otb = read_google_sheet(SPREADSHEET_ID_OTB, OTB_SHEET)
attributes = read_google_sheet(SPREADSHEET_ID_ATTRIBUTES, ATTRIBUTES_SHEET)
ann_per_ob = read_google_sheet(SPREADSHEET_ID_OVERALL_FRAMES, ann_per_obj)
df2 = read_google_sheet(SPREADSHEET_ID_POI, POI_SHEET)
df_voice = read_google_sheet(Voice_rec, Voice_sheet)




# ✅ Add 'Total_per_video' Column
df["Total_per_video"] = df.select_dtypes(include=['number']).sum(axis=1)

# ✅ Merge DataFrames
joined_df3 = pd.merge(otb, attributes, left_on='Object_Hash', right_on='object_hash', how='left')

# ✅ Drop unnecessary columns (if they exist)
columns_to_drop = ["video_name", "object_hash", "Blurring", "Truncation", "Occlusion"]
joined_df3 = joined_df3.drop(columns=[col for col in columns_to_drop if col in joined_df3.columns])

# ✅ Remove Duplicates
joined_df3 = joined_df3.drop_duplicates()

# ✅ Save as CSV (Optional)
joined_df3.to_csv("merged_data.csv", index=False)

# ✅ Upload Final Data to Google Sheets
MERGED_SPREADSHEET_ID = SPREADSHEET_ID_OBJ_ANN  # Change this if needed
MERGED_SHEET = "Merged_Data"

def upload_to_google_sheets(df, spreadsheet_id, sheet_name):
    """Uploads DataFrame to Google Sheets."""
    try:
          # ✅ Replace Inf and -Inf values with 0 (since Google Sheets doesn't support them)
        df = df.replace([float('inf'), float('-inf')], 0)

        # ✅ Replace NaN values with empty strings (Google Sheets treats empty cells properly)
        df = df.fillna("")
        spreadsheet = client.open_by_key(spreadsheet_id)
        worksheet = spreadsheet.worksheet(sheet_name)  # Select specific sheet
        worksheet.clear()  # Clear old data
        worksheet.update([df.columns.tolist()] + df.values.tolist())  # Upload new data
        print(f"✅ Data successfully uploaded to Google Sheet: {spreadsheet_id} ({sheet_name})")
    except gspread.exceptions.SpreadsheetNotFound:
        print(f"❌ Google Sheet '{spreadsheet_id}' not found. Ensure it exists and is shared with the service account.")
    except gspread.exceptions.WorksheetNotFound:
        print(f"❌ Worksheet '{sheet_name}' not found. Ensure it exists in the spreadsheet.")

# ✅ Upload Merged Data to Google Sheets
upload_to_google_sheets(joined_df3, MERGED_SPREADSHEET_ID, MERGED_SHEET)


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
# Load coordinates data for the map chart

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
    'backgroundColor': colors_tab['tab'],
    'color': 'white',
    'padding': '10px',
    'borderRadius': '5px',
    'margin': '2px'
}

selected_tab_style = {
    'backgroundColor': colors_tab['tab_selected'],
    'color': colors_tab['text'],
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

# Initialize the app
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # For deploying to platforms like Heroku

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

# Close the database connection
conn.close()

def create_objects_tab():
    """Create the 'Objects' tab layout."""
    return dcc.Tab(
        label='Objects',
        children=[
            html.Div(
                style={'display': 'flex', 'justifyContent': 'space-around', 
                       'padding': '20px', 'background': '#F7F7F7', 
                       'align-items': 'center'},  # Aligns all elements at center
                children=[

                    # KPI 1: Color Distribution
                    html.Div(children=[
                        html.H4("Color Distribution", style={'textAlign': 'center', 
                                                              'color': '#333', 
                                                              'fontSize': '18px'}),
                        dcc.Graph(figure=pie_OD_colors(colors_data), 
                                  style={'width': '100%', 'height': '150px', 
                                         'padding': '5px'})  # Reduced height
                    ], style={'width': '25%', 'background': 'white', 
                              'padding': '15px', 'border-radius': '15px', 
                              'box-shadow': '2px 2px 10px lightgray', 
                              'textAlign': 'center'}),
        html.Div(children=[
            html.H4("Face Show", style={'textAlign': 'center', 'color': '#333'}),
            dcc.Dropdown(
                id='df-dropdown_OD',
                options=[
                    {'label': 'Blur', 'value': 'blurry'},
                    {'label': 'Occlusion', 'value': 'occluded'},
                    {'label': 'Truncation', 'value': 'truncated'}
                ],
                value='blurry',  # Ensure this matches one of the available options
                clearable=False,
                style={'width': '50%', 'margin': '0 auto', 'display': 'block'}
            ),
            dcc.Graph(id='OD-pie', style={'border': '1px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'})
        ], style={'width': '30%', 'background': 'white', 'padding': '10px', 'border-radius': '10px', 'box-shadow': '2px 2px 10px lightgray'})
    ]),
        html.H3("select a row to see data for each video. " , style={'textAlign': 'center', 'fontSize': '24px', 'color': colors['text'], 'fontWeight': 'bold'}),
        html.P(
                [
                    "You can also search for a criterion in the search bar above each column in the table and press Enter or you can click the check box to see the video details below."
                ],
                style={
                    'color': colors['text'],
                    'textAlign': 'center',
                    'margin-bottom': '10px', 
                    'fontWeight': 'bold',
                    'fontSize': '20px'
                }
            ),
           create_OD_attributes(),  # Insert DataTable here
            html.Div(id='datatable-interactivity-container-od', style={'margin-top': '20px'}),  # Output container
            html.Ul([
                html.Li("Info on the whole database:"),
                html.Li(f"This table shows the data of '{vid_count}' videos"),
                html.Li(f"There are a total of '{total_frames_ann}' frames annotated")
            ], style={
                'margin-top': '20px',
                'color': colors['text'],
                'fontSize': '16px'
            }),
        html.Div([
            html.H3("Bar Plot", style={'textAlign': 'center', 'fontSize': '24px', 'color': colors['text'], 'fontWeight': 'bold'}),
            create_attributes_axis_dropdown('att_selection'),
            # Dropdown removed
            dcc.Graph(id='scatter-plot', style={'border': '5px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '20px'})
        ], style={'margin-bottom': '40px', 'padding': '60px', 'backgroundColor': colors['background'], 'borderRadius': '20px', 'width': '100%', "margin": "auto"}),

        # Treemap and its slider
        html.Div([
            html.H3("Objects Treemap", style={'textAlign': 'center', 'fontSize': '24px', 'color': colors['text'], 'fontWeight': 'bold'}),
            html.P(
                [
                    "You can click on the object that you want to and it will filter the bar chart above to videos that contain the picked object.",
                    html.Br(),
                    "Also you can interact with the slider below to filter object annotation count in a given range."
                ],
                style={
                    'color': colors['text'],
                    'textAlign': 'center',
                    'margin-bottom': '10px', 
                    'fontWeight': 'bold',
                    'fontSize': '20px'
                }
            ),
            create_slider_treemap('my-slider'),  # Use 'my-slider' to match the callback
            html.Button('Reset Filters', id='reset-button', n_clicks=0, style={'display': 'block', 'margin': '0 auto', 'padding': '10px', 'backgroundColor': '#2ECC40', 'color': 'white', 'border': 'none', 'borderRadius': '8px'}),
            dcc.Graph(id='objects-treemap', style={'border': '1px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'})
        ], style={'margin-bottom': '30px', 'padding': '20px', 'backgroundColor': colors['background'], 'borderRadius': '8px'}),

        html.Div([
    html.H3(
        "This bar chart shows the instances of attributes in the annotations",
        style={'textAlign': 'center', 'fontSize': '24px', 'color': colors['text'], 'fontWeight': 'bold'}
    ),
    dcc.Graph(
        figure=bar_attributes(),  # Call the function and pass the data
        style={'border': '1px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'}
    )
], style={'margin-bottom': '30px', 'padding': '20px', 'backgroundColor': colors['background'], 'borderRadius': '8px'}),

        

        # Pie chart section
        html.Div([
            html.H3("Pick an attribute to see distribution", style={'textAlign': 'center', 'fontSize': '24px', 'color': colors['text'], 'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='df-dropdown_OD',
                options=[
                    {'label': 'Blur', 'value': 'blurry'},
                    {'label': 'Occlusion', 'value': 'occluded'},
                    {'label': 'Truncation', 'value': 'truncated'}
                ],
                value='blurry',  # Ensure this matches one of the available options
                clearable=False,
                style={'width': '50%', 'margin': '0 auto', 'display': 'block'}
            ),
            dcc.Graph(id='OD-pie', style={'border': '1px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'})
        ], style={'margin-bottom': '30px', 'padding': '20px', 'backgroundColor': colors['background'], 'borderRadius': '8px'}),

        # Gauge indicator and its dropdown
        html.Div([
            html.H3("Select an object to view the number of annotations associated with it", style={'textAlign': 'center', 'fontSize': '24px', 'color': colors['text'], 'fontWeight': 'bold'}),
            create_y_axis_dropdown('y-axis-dropdown-overall', 'total', include_video_name=False),
            dcc.Graph(id='gauge-indicator-total', style={'border': '1px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'})
        ], style={'margin-bottom': '30px', 'padding': '20px', 'backgroundColor': colors['background'], 'borderRadius': '8px'}),

        html.Div([
    html.H3(
        "This pie chart represents the instances of colors in the annotations in relation to the overall instances ",
        style={'textAlign': 'center', 'fontSize': '24px', 'color': colors['text'], 'fontWeight': 'bold'}
    ),
    dcc.Graph(
        figure=pie_OD_colors(colors_data),  # Call the function and pass the data
        style={'border': '1px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'}
    )
], style={'margin-bottom': '30px', 'padding': '20px', 'backgroundColor': colors['background'], 'borderRadius': '8px'}),



        # Average annotations gauge (no dropdown)
        html.Div([
            create_average_annotations_gauge()
        ])
    ])

def create_attributes_axis_dropdown(id):
    """Create a dropdown for selecting the y-axis value."""
    options = [{'label': col, 'value': col} for col in OD_ATT.columns]
    return dcc.Dropdown(id=id, options=options, multi= True, clearable=True, style={'width': '50%', 'margin': '0 auto', 'display': 'block'})

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
    """
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
)

    # Pie chart for NLP status
    pie_chart = dcc.Graph(
        figure=pie_NLP(),
        style={'border': '1px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'}
    )

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
            
            table_nlp,  # Insert DataTable here
            html.Div(id='datatable-interactivity-container', style={'margin-top': '20px'}),  # Output container
            html.Ul([
                html.Li("Info on the whole database:"),
                html.Li(f"The total time of the videos is {sum_of_nlp_audio_hour} hour and {sum_of_nlp_audio_min} minutes."),
                html.Li(f"The overall size of the videos is: {sum_of_size} Mbs")
            ], style={
                'margin-top': '20px',
                'color': colors['text'],
                'fontSize': '16px'
            }),
            html.H3("Pie Chart for NLP Status", style={
                'color': colors['text'],
                'textAlign': 'center',
                'margin-top': '40px',
                'margin-bottom': '20px'
            }),
            pie_chart,
            html.H3("Pie Chart for Audio Events", style={
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

# Data Table Tab
def create_table_tab():
    """Create the 'Data Table' tab layout."""
    table = dash_table.DataTable(
        data=df.to_dict('records'),  # Convert DataFrame to list of dicts
        columns=[{"name": i, "id": i} for i in df.columns],
        style_table={'overflowX': 'auto'},  # Enable horizontal scrolling
        style_cell={
            'backgroundColor': colors['background'],
            'color': colors['text'],
            'textAlign': 'left',
            'padding': '5px',
            'fontSize': '14px'
        },
        style_header={
            'backgroundColor': '#444',
            'color': colors['text'],
            'fontWeight': 'bold'
        },
        page_size=15,  # Display 10 rows per page
        sort_action='native',  # Enable sorting
        filter_action='native',  # Enable filtering
    )

    table2 = dash_table.DataTable(
        data=df2.to_dict('records'),  # Convert DataFrame to list of dicts
        columns=[{"name": i, "id": i} for i in df2.columns],
        style_table={'overflowX': 'auto'},  # Enable horizontal scrolling
        style_cell={
            'backgroundColor': colors['background'],
            'color': colors['text'],
            'textAlign': 'left',
            'padding': '5px',
            'fontSize': '14px'
        },
        style_header={
            'backgroundColor': '#444',
            'color': colors['text'],
            'fontWeight': 'bold'
        },
        page_size=15,  # Display 10 rows per page
        sort_action='native',  # Enable sorting
        filter_action='native',  # Enable filtering
    )

    return dcc.Tab(label='Data Table', children=[
        html.Div([
            html.H3("DataFrames Overview", style={
                'textAlign': 'center',
                'color': colors['text'],
                'margin-bottom': '20px'
            }),
            
            # First Table Section
            html.Div([
                html.H4("Objects DataFrame", style={
                    'textAlign': 'center',
                    'color': colors['text'],
                    'margin-bottom': '10px'
                }),
                table
            ], style={
                'margin-bottom': '40px',
                'padding': '10px',
                'backgroundColor': colors['background'],
                'borderRadius': '8px'
            }),
            
            # Second Table Section
            html.Div([
                html.H4("Faces DataFrame", style={
                    'textAlign': 'center',
                    'color': colors['text'],
                    'margin-bottom': '10px'
                }),
                table2
            ], style={
                'padding': '10px',
                'backgroundColor': colors['background'],
                'borderRadius': '8px'
            })
            
        ], style={
            'padding': '20px',
            'backgroundColor': colors['background'],
            'borderRadius': '8px'
        })
    ])



# Heatmap Chart Tab
def heat_map_tab():

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
        html.H3("Network Activities", style={'color': '#333', 'display': 'inline'}),
        dcc.Graph(figure=language_bar(df_voice), style={'color': 'gray', 'margin-left': '10px'})
    ], style={'padding': '10px'})

])


        

def create_empty_tab(label, content=[]):
    """Create an empty tab with the given label and content."""
    return dcc.Tab(label=label, children=[
        html.Div(
            content, style={'padding': '50px', 'backgroundColor': colors['background'], 'borderRadius': '8px', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)'})])

maxx = df2["Overall Frames Annotated"].max()
bar_lim = maxx + 1000
sheet1_content = [
    # Overview Section
    html.Div(
        [
           
            html.H3("Face Annotation Overview", style={'color': colors['text'], 'textAlign': 'center'}),
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
        'backgroundColor': colors['background']
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
            label='DataFrames(source)',
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
        return add_image_to_tab(heat_map_tab())  # Add image to Heatmap tab
    elif tab == 'tab-5':
        return add_image_to_tab(create_table_tab())  # Add image to DataFrames tab
    else:
        return html.Div("Tab not found.", style={
            'textAlign': 'center',
            'fontSize': '24px',
            'color': 'gray'
        })


# Callback to update treemap and scatter plot
@app.callback(
    [Output('objects-treemap', 'figure'),
     Output('scatter-plot', 'figure')],
    [Input('my-slider', 'value'),
     Input('objects-treemap', 'clickData'), 
     Input('att_selection', 'value'),
     Input('reset-button', 'n_clicks')]  # Reset button input
)
def update_treemap_and_scatter(selected_range, clickData, selected_attributes, n_clicks):
    """
    Update the treemap and scatter plot based on:
    1. The selected range from the slider.
    2. The clicked segment from the treemap.
    3. The selected attributes from the multi-dropdown.
    4. Resetting the treemap when the reset button is clicked.
    """
    fixed_y_axis = 'Total_per_video'  # Set fixed y-axis column
    filtered_treemap_df = transposed_df.iloc[:-1, :].reset_index()

    # Range Filtering for Treemap
    if not selected_range or len(selected_range) != 2:
        min_val = filtered_treemap_df['Total'].min()
        max_val = filtered_treemap_df['Total'].max()
    else:
        min_val, max_val = selected_range
        filtered_treemap_df = filtered_treemap_df[
            (filtered_treemap_df['Total'] >= min_val) & 
            (filtered_treemap_df['Total'] <= max_val)
        ]

    # **RESET TREEMAP FILTER** if reset button is clicked
    if n_clicks:
        clickData = None  # Clear treemap selection
    
    treemap_fig = px.treemap(
        filtered_treemap_df,
        path=['index'],
        values='Total',
        title=f"Treemap: Annotations per Object ({min_val} ≤ x ≤ {max_val})",
        labels={'index': 'Object', 'Total': 'Annotations'}
    )

    treemap_fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Annotations: %{value}<extra></extra>'
    )

    treemap_fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

    # Start with full dataset
    df_top_filtered = df_top.drop(index=df.index[0])

    # **Filtering by clicked treemap object**
    if clickData:
        clicked_object = clickData['points'][0]['label']
        if clicked_object in df_filtered.columns:
            filtered_df = df_filtered[df_filtered[clicked_object] > 0]
        else:
            filtered_df = pd.DataFrame()  # No valid data
    else:
        filtered_df = df_top_filtered  # Default case

    # **Filtering by selected attributes in OD_ATT**
    if selected_attributes:
        filtered_videos = OD_ATT.loc[
            OD_ATT[selected_attributes].apply(lambda x: x != "").all(axis=1),
            "Video Name"
        ].unique()
        
        # Apply the video name filter
        filtered_df = filtered_df[filtered_df["Video Name"].isin(filtered_videos)]

    # Generate Scatter Plot (Bar Chart)
    if not filtered_df.empty:
        scatter_fig = px.bar(
            filtered_df,
            x='Video Name',
            y=fixed_y_axis,
            title=f"Videos Matching Attributes: {selected_attributes}",
            text=fixed_y_axis
        )
        scatter_fig.update_traces(
            textposition='outside',
            texttemplate='%{text}',
            marker_color='LightSkyBlue'
        )
    else:
        scatter_fig = px.bar(
            title="No Videos Match the Selected Attributes"
        )

    scatter_fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'], 
        yaxis=dict(range=[0, 70])
    )

    return treemap_fig, scatter_fig



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
            hovertemplate='<b>%{label}</b><br>Annotations: %{value}<extra></extra>'
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
    [Input('df-dropdown_OD', 'value')]
)

def OTB_pie(selected): 
    
     if selected == 'blurry':
        data1 = Blur_df_od
        title1 = "Blur Distribution"
     elif selected == 'occluded':
        data1 = Oc_df_od
        title1 = "Occlusion Distribution" 
     elif selected == 'truncated':
        data1 = Trunc_df_od
        title1 =  "Truncation Distribution" 
     else:
        data1 = {}
        title1 = "No Data Selected"

    # Convert the data into a pie chart
     if data1:
        labels = list(data1.keys())
        values = list(data1.values())
        fig = px.pie(values=values, names=labels, title=title1)
        
        fig.update_layout(
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font_color=colors['text']
        )
        fig.update_traces(
            hovertemplate='<b>%{label}</b><br>Annotations: %{value}<extra></extra>'
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




def pie_OD_colors(colors_data):
    """
    Generate a pie chart showing the distribution of colors with real colors.
    """
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

    filtered_colors = {k: v for k, v in colors_data.items() if k in color_name_to_hex}
    if not filtered_colors:
        return px.pie(title="No Valid Colors Found")

    fig = px.pie(
        values=list(filtered_colors.values()),
        names=list(filtered_colors.keys()),
        title="",
        color=list(filtered_colors.keys()),
        color_discrete_map=color_name_to_hex,
        hole=0.4  # Creates a donut-style chart to match KPI style
    )

    # Adjusting Pie Chart to fit KPI size
    fig.update_layout(
        showlegend=False,  # Hide legend for KPI look
        height=200,  # Adjust height for KPI container
        margin=dict(l=0, r=0, t=30, b=0),  # Remove extra spacing
        font=dict(size=12),  # Reduce font size for better display
        annotations=[dict(
            text=f"{sum(filtered_colors.values())}",  # Show total count in center
            x=0.5, y=0.5, font_size=18, showarrow=False
        )]
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
        marker=dict(color="lightblue")  # Change bar color
    )

    fig.update_layout(
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(color="black"),
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

    fig.update_traces(textinfo='label+percent', marker=dict(colors=["#B6E880", "#FF97FF"]))
    return fig

    
def Face_show() : 
    

    Not_show = (df_voice["Face Showing"] == "No").sum()
    Partly = (df_voice["Face Showing"] == "Partly").sum()
    Showing = (df_voice["Face Showing"] == "Most-All video").sum()

    Face = {"No": Not_show, "Partly": Partly, "Showing_mostly" : Showing}

    fig = px.pie (values=list(Face.values()) ,names=list(Face.keys()) ,title = "Face show distibution")
    fig.update_traces(textinfo='label+percent', marker=dict(colors=["#B6E880", "#FF97FF"]))
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

    fig.update_traces(textinfo='label+percent', marker=dict(colors=["#B6E880", "#FF97FF"]))
    return fig


# Save the transposed DataFrame
#transposed_df.to_csv(r"C:\Users\rwad\OneDrive\Documents\classes_distribution\class.csv", index=True)


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
    'Day Time': 'rgb(236, 255, 0)'
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

button_dropouts = {
    "width": "30%",
    "height": "60px",
    "margin": "-50px 0px 0px 1300px",
    "background-color": 'black',
    "border": "2px solid white",
    "display": "block",
    "font-weight": "bold",
    "color": "white",
    "borderRadius": "50px",    
}

button_clear = {
    "width": "30%",
    "height": "60px",
    "margin": "-60px 0px 0px 1800px",
    "background-color": 'white',
    "border": "2px solid white",
    "display": "block",
    "font-weight": "bold",
    "color": "red",
    "borderRadius": "50px",    
}

button_style15 = {
    "width": "150%",
    "height": "60px",
    "margin": "30px -5px",
    "background-color": 'white',
    "border": "2px solid white",
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
    source_counts['Percentage'] = (source_counts['Count'] / source_counts['Count'].sum()) * 100
    
    fig = px.bar(
        source_counts, 
        x='Logos and text', 
        y='Count', 
        color='Logos and text', 
        color_discrete_map=color_map4_city,
        title='Logos and text Distribution',
        text=source_counts['Percentage'].apply(lambda x: f'{x:.2f}%')  # Adding percentage labels
    )
    
    fig.update_traces(
        marker_line_width=1.5, 
        hovertemplate="Count: %{y}<br>Percentage: %{text}", 
        textposition='outside',
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
            color='yellow',
            gridcolor='gray',
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white'),
            range=[source_counts['Count'].min(), 1.10*(source_counts['Count'].max())]
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

import plotly.express as px

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
        text=weather_counts['Percentage'].apply(lambda x: f'{x:.2f}%')  # Adding percentage labels
    )
    
    fig.update_traces(
        marker_line_width=1.5,
        hovertemplate="Count: %{x}<br>Percentage: %{text}",
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
            zerolinecolor='gray',
            title_font=dict(color='white'),
            tickfont=dict(color='white'),
            range=[0, 1.25*(weather_counts['Count'].max())]  # Adjusted range calculation
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


import plotly.express as px

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
        color_discrete_map=color_map,
        title='Source Distribution'
    )
    
    fig.update_traces(
        marker=dict(line=dict(color='white', width=2)),
        textinfo='label+percent',  # Added percent here
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
            dcc.Store('polygon_drop_active', data=False),
            dcc.Store(id='polygon-coords-store', data=None),
            dcc.Store(id='reset_button_clicked', data=False),
            dcc.Store(id='load_button_clicked', data=False),
            dcc.Store(id='filter_comp_store', data=None),
            

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
                                            value=[], 
                                            multi=True,
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
                                    ]),  
                                ], width=8),
                            ])
                        ], width=6),
                    ]),
                    
                    html.H1(
                        id='record-count',
                        children="Total Records: 0",
                        style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    html.Br(),
                    html.H2(
                        id='drop-pre',
                        children=f"0% out of Poylgon",
                        style={'textAlign': 'center', 'fontWeight': 'bold', 'marginTop': '0', 'color': 'rgb(255,51,153)'}
                    ),
                    dbc.Col(
                        dbc.Button(
                            "Show Dropouts",
                            id='dropouts',
                            color='primary',
                            n_clicks=0,
                            style=button_dropouts
                        ),
                        width=4
                    ), 
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
                    html.Br(),
                    html.H4("Filter by Video Duration (minutes):", className='mb-1', style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}),
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
                        html.H4("Graphical Analysis", className='mb-3', style={'textAlign': 'left', 'color': 'rgb(255,51,153)'}),      
                        html.Div(
                            id="graphs-container",
                            style={"display": "none"},  
                            children=[
                                dbc.Row([
                                    dbc.Col(dcc.Graph(id='pie-chart', figure={}), width=6),
                                    dbc.Col(dcc.Graph(id='bar-chart-weather', figure={}), width=6),
                                    dbc.Col(dcc.Graph(id='bar-plot-logos', figure={}), width=6),
                                    dbc.Col(dcc.Graph(id='source-pie', figure={}), width=6),
                                ]),
                            ],
                        ),
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
    pie_clickData,
    bar_weather_clickData,
    bar_clickData,
    pie2_clickData,
):
    """
    Returns a list containing exactly one row (dict) for the filter table
    if any filter is active. Otherwise, returns an empty list.
    """

    # Gather all filters in one dict
    filters_dict = {
        'Terrain': selected_terrain,
        'Occluded': selected_occluded,
        'Video quality': selected_VQ,
        'Camera tilt': selected_tilt,
        'Distance from building': selected_distance,
        'Time': pie_clickData,
        'Weather': bar_weather_clickData,
        'Logos': bar_clickData,
        'Source': pie2_clickData
    }

    # Build active filters with different conditions:
    # For non-figure filters, we skip the filter if its value is "All".
    # For figure filters (the ones with clickData), we only include if the value is not None.
    active_filters = {}
    for key, value in filters_dict.items():
        if key in ['Time', 'Weather', 'Logos', 'Source']:
            if value is not None:
                active_filters[key] = value
        else:
            if value != 'All':
                active_filters[key] = value

    # If no active filters are applied, return an empty list.
    if not active_filters:
        return []

    # Calculate the percentage of remaining records
    filtered_count = len(filtered_df)
    percentage = (filtered_count / original_total * 100) if original_total else 0

    # Build a single row that aggregates all active filters
    row = {
        "City": city_name,
        "Filters": ", ".join(active_filters.keys()),       # e.g. "Terrain, Occluded"
        "fvalue": ", ".join(str(v) for v in active_filters.values()),  # e.g. "highly, yes"
        "Percentage": f"{percentage:.2f}%"
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
        Output('record-count', 'children'),
        Output('drop-pre', 'children'),
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
        Output('reset_button_clicked','data'),
        Output('graphs-container', 'style'),
        Output('polygon_drop_active','data'),
        Output('polygon-coords-store', 'data'),
        Output('filter_comp', 'data'),            # <-- The table showing filter comparisons
        Output('filter_comp_store','data'),       # <-- Store for filter comparison
        Output('load_button_clicked','data')
    ],
    [
        Input('city-filter-btn', 'n_clicks'),
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
        Input('Distance_Building', 'value'),
        Input('dropouts','n_clicks'),
        Input('clear_table','n_clicks')
    ],
    [
        State('current-city-data','data'),
        State('reset_button_clicked','data'),
        State('polygon_drop_active','data'),
        State('polygon-coords-store', 'data'),
        State('filter_comp_store','data'),
        State('load_button_clicked','data')
    ]
)
def load_dashboards(load_btn, selected_city, update, pie_clickData, bar_weather_clickData,  
bar_clickData, pie2_clickData, duration_range, selected_terrain,  
selected_occluded, selected_VQ, selected_tilt, selected_distance,  
dropouts_n_clicks,clear_button, current_data, reset_clicked, polygon_active,  
polygon_coords_store, filter_comp_store, load_clicked
):

    global original_total  # We'll use this to store the total # of records after city load
    ctx = dash.callback_context
    triggered_id = ctx.triggered[0]['prop_id'] if ctx.triggered else None

    # If city dropdown changes without a button click, do nothing
    if triggered_id and triggered_id.startswith('city_filter'):
        return (dash.no_update,) * 37

    # Reset chart clickData if they weren’t the trigger
    if triggered_id != 'pie-chart.clickData':
        pie_clickData = None
    if triggered_id != 'bar-chart-weather.clickData':
        bar_weather_clickData = None
    if triggered_id != 'bar-plot-logos.clickData':
        bar_clickData = None
    if triggered_id != 'source-pie.clickData':
        pie2_clickData = None
        
    def extract_label(clickData, key='label'):
        if clickData and 'points' in clickData and clickData['points']:
            return clickData['points'][0].get(key, 'All')
        return 'All'
    
    # Helper: Build dropdown options for a given column
    def build_options(df, col_name):
        if col_name in df.columns:
            unique_vals = sorted([v for v in df[col_name].unique() if pd.notnull(v)])
            return [{'label': 'All', 'value': 'All'}] + [{'label': str(val), 'value': str(val)} for val in unique_vals]
        return []

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

    # -------------- Branch 1: Load Button --------------
    if triggered_id == 'city-filter-btn.n_clicks':
        reset_clicked = False
        load_clicked = True

        # Clear filter-comp data on new city load
        filter_comp_data = filter_comp_store

        sheet_ids, sheet_ranges, polygon_ids = load_selected_cities(selected_city)
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
            combined_dfs.append(df_city)

        if combined_dfs:
            df_combined = pd.concat(combined_dfs, ignore_index=True)
        else:
            df_combined = pd.DataFrame()

        # Build polygon layer
        polygon_layers = []
        for poly_coords in polygons_list:
            if poly_coords:
                city_poly = Polygon(poly_coords)
                polygon_layers.append(
                    dl.Polygon(
                        positions=list(city_poly.exterior.coords),
                        color="blue",
                        fillColor="cyan",
                        fillOpacity=0.6,
                    )
                )
        polygon_layer = dl.LayerGroup(children=polygon_layers)

        # Create markers
        if 'Coordinates' in df_combined.columns:
            df_combined = df_combined[df_combined['Coordinates'].str.contains(',', na=False)]
            df_combined[['Latitude', 'Longitude']] = df_combined['Coordinates'].str.split(',', expand=True)
            df_combined['Latitude'] = pd.to_numeric(df_combined['Latitude'], errors='coerce')
            df_combined['Longitude'] = pd.to_numeric(df_combined['Longitude'], errors='coerce')
            city_markers = create_map_markers(df_combined)
        else:
            city_markers = []

        # Check inside polygon
        def is_inside_any(lat, lon, polygons):
            pt = Point(lat, lon)
            for poly in polygons:
                if poly and Polygon(poly).contains(pt):
                    return True
            return False

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

        title = f"Airis-Labs: Geo-Location Analysis - {', '.join(selected_city) if isinstance(selected_city, list) else selected_city}"

        # Store original total for subsequent filter-comparison
        original_total = len(df_combined)

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
            record_count,
            drop_count,
            min_dur,
            max_dur,
            [min_dur, max_dur],
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
            dash.no_update,   # filter_comp => empty on load
            filter_comp_data,   # filter_comp_store => empty on load
            load_clicked
        )

    # -------------- Branch 2: Update & Reset Button --------------
    elif triggered_id == 'update.n_clicks':
        reset_clicked = True
        load_clicked = False
        

        # Reload city data
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
            df_updated = pd.concat(combined_dfs, ignore_index=True)
        else:
            df_updated = pd.DataFrame()

        if 'Coordinates' in df_updated.columns:
            df_updated = df_updated[df_updated['Coordinates'].str.contains(',', na=False)]
            df_updated[['Latitude', 'Longitude']] = df_updated['Coordinates'].str.split(',', expand=True)
            df_updated['Latitude'] = pd.to_numeric(df_updated['Latitude'], errors='coerce')
            df_updated['Longitude'] = pd.to_numeric(df_updated['Longitude'], errors='coerce')
            city_markers = create_map_markers(df_updated)
        else:
            city_markers = []

        def is_inside_any(lat, lon, polygons):
            pt = Point(lat, lon)
            for poly in polygons:
                if poly and Polygon(poly).contains(pt):
                    return True
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

        title = f"Airis-Labs: Geo-Location Analysis - {', '.join(selected_city) if isinstance(selected_city, list) else selected_city}"

        # Now produce a single row for filter-comp if user changed any filters
        # (But since "update" was clicked, presumably we want to reset everything.)
        # We'll keep it empty or you can do the compute_filter_comp if you want.
        # For a strict "reset," we do not compute filters. We'll keep it empty:
        filter_comp_data = []

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
            record_count,
            drop_count,
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
            df_updated.to_dict('records'),
            [{'name': col, 'id': col} for col in df_updated.columns],
            df_updated.to_dict('records'),
            reset_clicked,
            {"display": "block"},
            polygons_list,
            polygons_list,
            dash.no_update,  
            dash.no_update,
            load_clicked
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

        drop_count = f"{dropout_percentage} % out of Polygon" if total_count > 0 else "Nothing to show"

        # Now produce filter_comp row
        city_label = selected_city if isinstance(selected_city, str) else ", ".join(selected_city)
        time_pie= extract_label(pie_clickData, 'label')
        weather_bar = extract_label(bar_weather_clickData, 'y')
        logos_bar = extract_label(bar_clickData, 'x')
        source_pie = extract_label(pie2_clickData, 'label')
        
        filter_comp_data = compute_filter_comp(
            filtered_df=filtered_df,
            original_total=original_total,
            city_name=city_label,
            selected_terrain=selected_terrain,
            selected_occluded=selected_occluded,
            selected_VQ=selected_VQ,
            selected_tilt=selected_tilt,
            selected_distance=selected_distance,
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
            record_count,
            drop_count,
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
            reset_clicked,
            {"display": "block"},
            polygon_active,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            load_clicked
        )


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
            reset_clicked,
            dash.no_update,
            dash.no_update,
            dash.no_update,
            filter_comp_data,  # Single row or empty
            filter_comp_data,
            load_clicked            
        )


    # -------------- Branch 5: Default Filtering (No explicit button) --------------
    else:
        # Possibly user changed a filter or some default fallback
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

            df_current = df_current[df_current['Coordinates'].str.contains(',', na=False)]
            temp = df_current['Coordinates'].str.split(',', n=1, expand=True)
            df_current['Latitude'] = pd.to_numeric(temp[0], errors='coerce')
            df_current['Longitude'] = pd.to_numeric(temp[1], errors='coerce')
            city_markers = create_map_markers(df_current)

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

            city_label = selected_city if isinstance(selected_city, str) else ", ".join(selected_city)
            time_pie= extract_label(pie_clickData, 'label')
            weather_bar = extract_label(bar_weather_clickData, 'x')
            logos_bar = extract_label(bar_clickData, 'x')
            source_pie = extract_label(pie2_clickData, 'label')
            # No filters applied => filter_comp_data = []
            filter_comp_data = compute_filter_comp(
                filtered_df=df_filtered,
                original_total=original_total,
                city_name=city_label,
                selected_terrain=selected_terrain,
                selected_occluded=selected_occluded,
                selected_VQ=selected_VQ,
                selected_tilt=selected_tilt,
                selected_distance=selected_distance,
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
                record_count,
                drop_count,
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
                reset_clicked,
                {"display": "block"},
                polygon_active,
                dash.no_update,
                filter_comp_data,
                filter_comp_data,
                load_clicked
            )
        else:
            # We do have data in current_data => user changed a filter
            df_filtered = apply_all_filters2(
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
                polygon_active=polygon_active
            )

            terrain_options = build_options(df_filtered, 'Terrain')
            occlusion_options = build_options(df_filtered, 'Occluded')
            vq_options = build_options(df_filtered, 'Video quality')
            camera_tilt_options = build_options(df_filtered, 'Camera tilt')
            distance_options = build_options(df_filtered, 'Distance from building')

            df_filtered = df_filtered[df_filtered['Coordinates'].str.contains(',', na=False)]
            temp = df_filtered['Coordinates'].str.split(',', n=1, expand=True)
            df_filtered['Latitude'] = pd.to_numeric(temp[0], errors='coerce')
            df_filtered['Longitude'] = pd.to_numeric(temp[1], errors='coerce')
            city_markers = create_map_markers(df_filtered)

            polygons_list = polygon_coords_store if polygon_coords_store else []
            if polygons_list and len(polygons_list) > 0:
                city_polygon = Polygon(polygons_list[0])
            else:
                city_polygon = None

            count_within = sum(
                city_polygon.contains(Point(row['Latitude'], row['Longitude']))
                for _, row in df_filtered.iterrows()
                if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude'])
            ) if city_polygon else 0

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

            title = f"Airis-Labs: Geo-Location Analysis - {', '.join(selected_city) if isinstance(selected_city, list) else selected_city}"

            # Build final charts
            pie_fig = generate_interactive_pie_chart_city(df_filtered)
            weather_bar_fig = generate_interactive_bar_chart_weather_city(df_filtered)
            logos_bar_fig = generate_interactive_bar_plot_2_city(df_filtered)
            source_pie_fig = generate_interactive_pie_chart_source(df_filtered)
            
        
            # Convert selected_city to a string if it is a list
            city_label = selected_city if isinstance(selected_city, str) else ", ".join(selected_city)
            time_pie= extract_label(pie_clickData, 'label')
            weather_bar = extract_label(bar_weather_clickData, 'y')
            logos_bar = extract_label(bar_clickData, 'x')
            source_pie = extract_label(pie2_clickData, 'label')
            
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
                        pie_clickData = time_pie,
                        bar_weather_clickData=weather_bar,
                        bar_clickData= logos_bar,
                        pie2_clickData= source_pie
                    )[0]  # Assuming compute_filter_comp returns a list

                    # Check if filters and values match
                    filters_match = all(
                        city_entry.get(key) == new_filter_data.get(key)
                        for key in ["Filters", "fvalue"]
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
                record_count,
                drop_count,
                min_dur,
                max_dur,
                [min_dur, max_dur],
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
                load_clicked
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




# Run the app
if __name__ == '__main__':
    app.run_server(host='100.84.182.85', port=8050, debug=True)
