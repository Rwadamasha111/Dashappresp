# Import necessary libraries
from dash import Dash, html, dcc, dash_table
from dash.dash_table.Format import Format, Scheme  # Updated import path for formatters
import pandas as pd
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.dependencies import Output, Input
import plotly.graph_objects as go
import sqlite3 
import re

# Incorporate data
df = pd.read_csv(r'C:\Users\rwad\OneDrive\Documents\classes_distribution\classes.csv')
df = df.sort_values(by='All objects', ascending=False)
df_top = df.head(15)
df_filt = df.iloc[:1 , : ].reset_index()
df_filtered = df.iloc[1: , : ].reset_index()
print(df_filtered)
transposed_df = df.set_index('Video Name').T
df2 = pd.read_csv(r'C:\Users\rwad\OneDrive\Desktop\outputs for project\attribute_summary.csv')
df2 = df2.sort_values(by='oveall_annotated_per_vid', ascending=False)
objects = transposed_df.columns[0]
df2 = df2.head(16)
df3 = pd.read_csv(r"C:\Users\rwad\OneDrive\Desktop\outputs for project\output_transcriptions.csv")
sum_of_nlp_audio = df3["video_length_secs"].sum() / 3600
sum_of_nlp_audio_hour = int(sum_of_nlp_audio)
sum_of_nlp_audio_min = int((sum_of_nlp_audio - sum_of_nlp_audio_hour) * 1000)
sum_of_size = df3["size_in_mb"].sum()
# Load coordinates data for the map chart
coordinates_df = pd.read_csv(r"C:\Users\rwad\OneDrive\Desktop\Coordinates.csv")
sum_of_blurry = df2["blurry"].sum()
sum_of_undecided = df2["undecided"].sum()
sum_of_acceptable = df2["acceptable"].sum()
sum_of_occluded = df2["occluded"].sum()
sum_of_not_occluded = df2["not_occluded"].sum()
partially_occluded = df2["partially_occluded"].sum()
partially_turned = df2["partially_turned"].sum()
turned = df2["turned"].sum()
sum_of_frontal = df2["frontal"].sum()
total_ann = (sum_of_blurry + sum_of_undecided + sum_of_occluded +
             sum_of_acceptable + sum_of_not_occluded + partially_occluded + 
             partially_turned + turned + sum_of_frontal)

blur_df = {
    "blurry": sum_of_blurry,
    "undecided": sum_of_undecided,
    "acceptable": sum_of_acceptable
}

occluded_df = {
    "occluded": sum_of_occluded,
    "not_occluded": sum_of_not_occluded,
    "partially_occluded": partially_occluded
}

pose_df = {
    "partially_turned": partially_turned,
    "turned": turned,
    "frontal": sum_of_frontal
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
                'height': '120px',
                'width': '120px',
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
        # Scatter plot without dropdown
        html.Div([
            html.H3("Bar Plot", style={'textAlign': 'center', 'fontSize': '24px', 'color': colors['text'], 'fontWeight': 'bold'}),
            # Dropdown removed
            dcc.Graph(id='scatter-plot', style={'border': '5px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '20px'})
        ], style={'margin-bottom': '40px', 'padding': '60px', 'backgroundColor': colors['background'], 'borderRadius': '20px' , 'width' : '100%', "margin": "auto"}),

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
                'fontSize' : '20px'
            }
        ),
            create_slider_treemap('my-slider'),  # Use 'my-slider' to match the callback
            dcc.Graph(id='objects-treemap', style={'border': '1px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'})
        ], style={'margin-bottom': '30px', 'padding': '20px', 'backgroundColor': colors['background'], 'borderRadius': '8px'}),

        # Gauge indicator and its dropdown
        html.Div([
            html.H3(f"Pick an object to see the sum of its annotations or scroll down to see the sum of all object", style={'textAlign': 'center', 'fontSize': '24px', 'color': colors['text'], 'fontWeight': 'bold'}),
            create_y_axis_dropdown('y-axis-dropdown-overall', 'total', include_video_name=False),
            dcc.Graph(id='gauge-indicator-total', style={'border': '1px solid #ddd', 'boxShadow': '0px 4px 8px rgba(0, 0, 0, 0.1)', 'borderRadius': '8px'})
        ], style={'margin-bottom': '30px', 'padding': '20px', 'backgroundColor': colors['background'], 'borderRadius': '8px'}),

        # Average annotations gauge (no dropdown)
        html.Div([
            create_average_annotations_gauge()
        ])
    ])

def create_y_axis_dropdown(id, default_value, include_video_name=True):
    """Create a dropdown for selecting the y-axis value."""
    options = [{'label': col, 'value': col} for col in df.columns if include_video_name or col != 'Video Name']
    return dcc.Dropdown(id=id, options=options, value=default_value, clearable=False, style={'width': '50%', 'margin': '0 auto', 'display': 'block'})

num_columns = len(df.columns) - 1  # Exclude 'Video Name' column
total_annotations = df.iloc[1:, 1:-1].sum().sum()
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
    min_val = reset_df['total overall objects'].min()
    max_val = reset_df['total overall objects'].max()
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
                html.Li("Statistics on the whole database:"),
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

# Faces Tab Content
sheet1_content = [
    # Overview Section
    html.Div(
        [
            html.H3("Face Annotation Overview", style={'color': colors['text'], 'textAlign': 'center'}),
            dcc.Graph(
                figure=px.bar(
                    df2,
                    x="Video_Name",
                    y="oveall_annotated_per_vid",
                    title="Overall Annotated per Video",
                    text = "oveall_annotated_per_vid"
                ).update_layout(
                    plot_bgcolor=colors['background'],
                    paper_bgcolor=colors['background'],
                    font_color=colors['text'],
                    yaxis = dict(range = [0 , 70000])
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
                {'label': 'Occlusion', 'value': 'occluded'},
                {'label': 'Pose', 'value': 'pose'}
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
     Input('objects-treemap', 'clickData')]
)
def update_treemap_and_scatter(selected_range, clickData):
    """
    Update the treemap and scatter plot based on the selected range from the slider
    and the clicked segment from the treemap.
    """
    fixed_y_axis = 'All objects'  # Set your desired fixed y-axis column
    filtered_treemap_df = transposed_df.iloc[:, :1].reset_index()
    max_min = filtered_treemap_df.iloc[:-1 , :].reset_index()

    # Update Treemap
    if not selected_range or len(selected_range) != 2:
        # If no range is selected, show the full treemap excluding the last column
        min_val = filtered_treemap_df.iloc[:-1 , :].reset_index()['total overall objects'].min()
        max_val = filtered_treemap_df.iloc[:-1 , :].reset_index()['total overall objects'].max()
    else:
        min_val, max_val = selected_range
        filtered_treemap_df = filtered_treemap_df[
            (filtered_treemap_df['total overall objects'] >= min_val) &
            (filtered_treemap_df['total overall objects'] <= max_val)
        ]

    treemap_fig = px.treemap(
        filtered_treemap_df.iloc[:-1 , :].reset_index(),
        path=['index'],
        values='total overall objects',
        title=f"Treemap: Annotations per Object ({min_val} ≤ x ≤ {max_val})",
        labels={'index': 'Object', 'total overall objects': 'Annotations'}
    )

    treemap_fig.update_traces(
        hovertemplate='<b>%{label}</b><br>Annotations: %{value}<extra></extra>'
    )

    treemap_fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )
    df_top_filtered = df_top.drop(index=df.index[0])
    #print (df)

    # Update Scatter Plot
    if clickData:
        # Extract the clicked object name
        clicked_object = clickData['points'][0]['label']
        # Ensure the clicked object exists as a column in the DataFrame
        if clicked_object in df_filtered.columns:
            # Filter the DataFrame to include only videos containing the clicked object
            filtered_df = df_filtered[df_filtered[clicked_object] > 0]
            scatter_title = f"Videos Containing '{clicked_object}'"
            x_axis = 'Video Name'
            y_axis = fixed_y_axis  # Use the fixed y-axis
        else:
            # If the clicked object is not a valid column, show an empty DataFrame
            filtered_df = pd.DataFrame()
            scatter_title = "No Data Available"
            x_axis = 'Video Name'
            y_axis = fixed_y_axis
    else:
        # If no object is clicked, show the full DataFrame
        filtered_df = df_top_filtered
        scatter_title = f"Scatter Plot: Video Name vs {fixed_y_axis}"
        x_axis = 'Video Name'
        y_axis = fixed_y_axis

    if not filtered_df.empty:
        scatter_fig = px.bar(
            filtered_df,
            x=x_axis,
            y=y_axis,
            title=scatter_title,
            text=y_axis
        )
        scatter_fig.update_traces(
            textposition='outside',
            texttemplate='%{text}',
            marker_color='LightSkyBlue'
        )
    else:
        scatter_fig = px.bar(
            title=scatter_title
        )

    scatter_fig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'], 
        yaxis = dict(range = [0, 70])
    )

    return treemap_fig, scatter_fig

# Callback to update the gauge for total annotations
@app.callback(
    Output('gauge-indicator-total', 'figure'),
    [Input('y-axis-dropdown-overall', 'value')]
)
def update_gauge_total(selected_column):
    """Update the gauge indicator with the total overall objects."""
    
    if selected_column in df_filt.columns:
        total_value = df_filt[selected_column].sum()
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
    elif selected_df == 'pose':
        data = pose_df
        title = "Pose Distribution"
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

# Save the transposed DataFrame
transposed_df.to_csv(r"C:\Users\rwad\OneDrive\Documents\classes_distribution\class.csv", index=True)

# Run the app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)
