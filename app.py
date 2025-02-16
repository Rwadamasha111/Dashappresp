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

# ✅ Sheet Names
OBJ_ANN_SHEET = "Obj_ann_with_total"
TRANSCRIPTION_SHEET = "output_transcriptions"
COORDINATES_SHEET = "Coordinates"
OVERALL_FRAMES_SHEET = "Overall_ann_od"
ann_per_obj = "Overall_ann_od_per_obj"
OTB_SHEET = "OTB2"
ATTRIBUTES_SHEET = "OTB3"

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
df2 = pd.read_csv(r'C:\Users\rwad\OneDrive\Documents\classes_distribution\POI_csv.csv')
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
    'background': '#111111',
    'text': '#7FDBFF'
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
tab_style = {
    'backgroundColor': colors['background'],
    'color': colors['text'],
    'border': '1px solid #333',
    'borderRadius': '8px',
    'padding': '10px'
}
selected_tab_style = {
    'backgroundColor': '#444',
    'color': colors['text'],
    'border': '1px solid #333',
    'borderRadius': '8px',
    'padding': '10px'
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
    return dcc.Tab(label='Objects', children=[
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
    """Create the 'Heatmap Chart' tab layout."""
    fig = px.density_mapbox(
        coordinates_df,
        lat='Latitude',
        lon='Longitude',
        hover_name='City',
        hover_data={'Source': True , 'Latitude': True, 'Longitude': True },
        radius=10, 
        zoom=3,
        mapbox_style='carto-positron'
    )
    fig.update_layout(
        paper_bgcolor=colors['background'],  # Outer background
        plot_bgcolor=colors['background'],  # Plot area background
        font_color=colors['text']           # Font color for labels
    )
    return dcc.Tab(label='Heatmap Chart', children=[
        html.Div([
            html.H3("Heatmap of Coordinate Density", style={'textAlign': 'center', 'color': colors['text']}),
            dcc.Graph(figure=fig, style={'border': '1px solid #333', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.5)', 'borderRadius': '20px'})
        ], style={'padding': '20px'})
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
            label='Heatmap Chart',
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
            'color': colors['text']
        })


# Callback to update treemap and scatter plot
@app.callback(
    [Output('objects-treemap', 'figure'),
     Output('scatter-plot', 'figure')],
    [Input('my-slider', 'value'),
     Input('objects-treemap', 'clickData'), 
     Input('att_selection' , 'value')]
   
)
def update_treemap_and_scatter(selected_range, clickData, selected_attributes):
    """
    Update the treemap and scatter plot based on:
    1. The selected range from the slider.
    2. The clicked segment from the treemap.
    3. The selected attributes from the multi-dropdown.
    """
    fixed_y_axis = 'Total_per_video'  # Set fixed y-axis column
    filtered_treemap_df = transposed_df.iloc[:-1, :].reset_index()

    # Range Filtering for Treemap
    if not selected_range or len(selected_range) != 2:
        min_val = filtered_treemap_df.iloc[:-1, :]['Total'].min()
        max_val = filtered_treemap_df.iloc[:-1, :]['Total'].max()
    else:
        min_val, max_val = selected_range
        filtered_treemap_df = filtered_treemap_df[
            (filtered_treemap_df['Total'] >= min_val) &
            (filtered_treemap_df['Total'] <= max_val)
        ]

    treemap_fig = px.treemap(
        filtered_treemap_df.reset_index(),
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

    # Filtering by clicked treemap object
    if clickData:
        clicked_object = clickData['points'][0]['label']
        if clicked_object in df_filtered.columns:
            filtered_df = df_filtered[df_filtered[clicked_object] > 0]
        else:
            filtered_df = pd.DataFrame()  # No valid data
    else:
        filtered_df = df_top_filtered  # Default case

    # Filtering by selected attributes in OD_ATT
    if selected_attributes:
        filtered_videos = OD_ATT.loc[
            OD_ATT[selected_attributes].apply(lambda x: x != "").any(axis=1),
            "Video Name"
        ].unique()
        
        # Filter df_top based on the videos from OD_ATT
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

    Parameters:
        colors_data (dict): A dictionary where keys are color names and values are counts.

    Returns:
        fig: A Plotly pie chart figure.
    """
    # Validate input is a dictionary
    if not isinstance(colors_data, dict):
        raise ValueError("Input should be a dictionary with color names as keys and counts as values.")

    # Define the mapping of color names to real color codes
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

    # Ensure only colors in the mapping are included
    filtered_colors = {k: v for k, v in colors_data.items() if k in color_name_to_hex}
    if not filtered_colors:
        raise ValueError("No matching color names found in the color mapping.")

    # Create the pie chart
    fig = px.pie(
        values=list(filtered_colors.values()),
        names=list(filtered_colors.keys()),
        title="Color Distribution",
        color=list(filtered_colors.keys()),  # Match the colors by name
        color_discrete_map=color_name_to_hex  # Use the real colors
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



# Save the transposed DataFrame
#transposed_df.to_csv(r"C:\Users\rwad\OneDrive\Documents\classes_distribution\class.csv", index=True)

# Run the app
if __name__ == '__main__':
    app.run_server(host='100.84.182.85', port=8050, debug=True)
