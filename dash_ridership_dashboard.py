import pandas as pd
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from dash.dash_table import DataTable
import holidays
import datetime

# Load and clean the data
file_path = 'https://github.com/lwyay/Ridership-Dashboard/blob/main/Daily%20Ridership%20-%20Data%20View%20(1).csv'
data = pd.read_csv(file_path, encoding='utf-16', delimiter='\t', header=1)

# Convert the 'Date' column to datetime
data['Date'] = pd.to_datetime(data['Date'], errors='coerce')

# Remove commas and convert numeric columns to integers
for column in ['Bus', 'Rail', 'Grand Total']:
    data[column] = data[column].str.replace(',', '').astype(int)

# Add Month, Year, and Day of Week columns for filtering and hover
data['Month'] = data['Date'].dt.month_name()
data['Year'] = data['Date'].dt.year
data['Day'] = data['Date'].dt.day_name()  # Add day of the week (e.g., Mon, Tue)

# Generate US holidays for the years in the dataset
us_holidays = holidays.US(years=range(data['Year'].min(), data['Year'].max() + 1))
holiday_data = pd.DataFrame(
    [{'Date': date, 'Holiday_Name': name} for date, name in us_holidays.items()]
)
holiday_data['Date'] = pd.to_datetime(holiday_data['Date'])

# Merge holidays with the main data
data = pd.merge(data, holiday_data, on='Date', how='left')
data['Holiday'] = data['Holiday_Name'].notna().replace({True: 'Yes', False: 'No'})

# Define significant events
events = [
    {"date": datetime.date(2019, 4, 3), "description": "Cherry Blossom Festival Peak"},
    {"date": datetime.date(2020, 3, 22), "description": "COVID Lockdown Begins"},
    {"date": datetime.date(2020, 11, 3), "description": "U.S. Presidential Election"},
    {"date": datetime.date(2021, 1, 20), "description": "Presidential Inauguration"},
    {"date": datetime.date(2021, 7, 4), "description": "Independence Day"},
    {"date": datetime.date(2022, 1, 3), "description": "Winter Storm Impacts"},
    {"date": datetime.date(2023, 11, 14), "description": "Political Event"},
    {"date": datetime.date(2024, 10, 29), "description": "Pre-Election Event"}
]

# Initialize the Dash app
app = Dash(__name__)
server = app.server
# Layout of the app
app.layout = html.Div([
    html.H1("Daily Ridership Dashboard", style={'text-align': 'center'}),

    html.Div([
        html.Label("Select Month:"),
        dcc.Dropdown(
            id='month-filter',
            options=[{'label': month, 'value': month} for month in data['Month'].unique()],
            value=None,
            placeholder="All Months",
            clearable=True
        )
    ], style={'width': '30%', 'display': 'inline-block'}),

    html.Div([
        html.Label("Select Year:"),
        dcc.Dropdown(
            id='year-filter',
            options=[{'label': year, 'value': year} for year in data['Year'].unique()],
            value=None,
            placeholder="All Years",
            clearable=True
        )
    ], style={'width': '30%', 'display': 'inline-block'}),

    html.Div([
        html.Label("Select Ridership Modes:"),
        dcc.Checklist(
            id='mode-filter',
            options=[
                {'label': 'Bus', 'value': 'Bus'},
                {'label': 'Rail', 'value': 'Rail'},
                {'label': 'Grand Total', 'value': 'Grand Total'}
            ],
            value=['Bus', 'Rail', 'Grand Total'],
            inline=True
        )
    ], style={'margin-top': '20px'}),

    html.Div([
        html.Label("Highlight Holidays and Events:"),
        dcc.Checklist(
            id='holiday-filter',
            options=[
                {'label': 'Show Holidays', 'value': 'Holidays'},
                {'label': 'Show Events', 'value': 'Events'}
            ],
            value=[]
        )
    ], style={'margin-top': '20px'}),

    dcc.Graph(id='ridership-graph'),

    html.Div([
        html.H3("Ridership Insights"),
        DataTable(
            id='summary-table',
            style_table={'overflowX': 'auto'},
            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
            style_cell={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'}
        )
    ], style={'margin-top': '30px'})
])

# Callback to update the graph based on filters
@app.callback(
    Output('ridership-graph', 'figure'),
    [Input('month-filter', 'value'),
     Input('year-filter', 'value'),
     Input('mode-filter', 'value'),
     Input('holiday-filter', 'value')]
)
def update_graph(selected_month, selected_year, selected_modes, filters):
    filtered_data = data.copy()

    # Apply month and year filters
    if selected_month:
        filtered_data = filtered_data[filtered_data['Month'] == selected_month]
    if selected_year:
        filtered_data = filtered_data[filtered_data['Year'] == int(selected_year)]

    # Create the graph
    fig = go.Figure()

    # Plot the ridership data
    for mode in selected_modes:
        fig.add_trace(go.Scatter(
            x=filtered_data['Date'], 
            y=filtered_data[mode],
            mode='lines', 
            name=mode,
            hovertemplate=(
                "%{x|%Y-%m-%d} (%{customdata[0]})<br>"
                f"{mode} Riders: %{{y}}"
            ),
            customdata=filtered_data[['Day']].values
        ))

    # Add vertical dotted lines for holidays
    if 'Holidays' in filters:
        holiday_data = filtered_data[filtered_data['Holiday'] == 'Yes']
        for idx, row in holiday_data.iterrows():
            fig.add_shape(
                type="line",
                x0=row['Date'], x1=row['Date'],
                y0=0, y1=max(filtered_data['Grand Total']),
                line=dict(color="grey", dash="dash")
            )
            fig.add_annotation(
                x=row['Date'],
                y=max(filtered_data['Grand Total']) + 5000,
                text=row['Holiday_Name'],
                showarrow=False,
                yshift=(idx % 2) * 20 - 10,
                bgcolor="white",
                font=dict(size=10, color="grey")
            )

    # Add vertical dotted lines for events
    if 'Events' in filters:
        for idx, event in enumerate(events):
            if pd.Timestamp(event["date"]) in filtered_data['Date'].values:
                fig.add_shape(
                    type="line",
                    x0=event["date"], x1=event["date"],
                    y0=0, y1=max(filtered_data['Grand Total']),
                    line=dict(color="grey", dash="dash")
                )
                fig.add_annotation(
                    x=event["date"],
                    y=max(filtered_data['Grand Total']) - 5000,
                    text=event["description"],
                    showarrow=False,
                    yshift=(idx % 2) * 20 - 10,
                    bgcolor="white",
                    font=dict(size=10, color="grey")
                )

    # Update layout with custom y-axis ticks
    fig.update_layout(
                title="Ridership Trends Over Time",
        xaxis=dict(title="Date", showgrid=True),
        yaxis=dict(
            title="Ridership Count",
            showgrid=True,
            tick0=0,
            dtick=50000
        ),
        legend_title="Ridership Modes",
        hovermode="x unified"
    )

    return fig

# Callback to update the table with insightful data
@app.callback(
    [Output('summary-table', 'data'),
     Output('summary-table', 'columns')],
    [Input('year-filter', 'value'),
     Input('month-filter', 'value')]
)
def update_table(selected_year, selected_month):
    # Default columns structure to return if no data is available
    default_columns = [{"name": "Insight", "id": "Insight"}, 
                       {"name": "Date", "id": "Date"},
                       {"name": "Day", "id": "Day"}, 
                       {"name": "Ridership", "id": "Ridership"}]

    if not selected_year and not selected_month:
        # Default: Show total ridership by year
        yearly_data = data.groupby('Year').agg({'Grand Total': 'sum'}).reset_index()
        yearly_data.rename(columns={'Grand Total': 'Total Ridership'}, inplace=True)
        columns = [{'name': col, 'id': col} for col in yearly_data.columns]
        return yearly_data.to_dict('records'), columns

    if selected_year and not selected_month:
        # Year selected: Show busiest and quietest days of the year
        year_data = data[data['Year'] == selected_year]
        if year_data.empty:
            return [], default_columns  # Return empty data and default columns

        busiest_day = year_data.loc[year_data['Grand Total'].idxmax()]
        quietest_day = year_data.loc[year_data['Grand Total'].idxmin()]
        summary = pd.DataFrame([
            {"Insight": "Busiest Day", "Date": busiest_day['Date'].strftime('%Y-%m-%d'), 
             "Day": busiest_day['Day'], "Ridership": busiest_day['Grand Total']},
            {"Insight": "Quietest Day", "Date": quietest_day['Date'].strftime('%Y-%m-%d'), 
             "Day": quietest_day['Day'], "Ridership": quietest_day['Grand Total']}
        ])
        columns = [{'name': col, 'id': col} for col in summary.columns]
        return summary.to_dict('records'), columns

    if selected_year and selected_month:
        # Year and month selected: Show busiest, quietest day, and monthly total
        month_data = data[(data['Year'] == selected_year) & (data['Month'] == selected_month)]
        if month_data.empty:
            return [], default_columns  # Return empty data and default columns

        busiest_day = month_data.loc[month_data['Grand Total'].idxmax()]
        quietest_day = month_data.loc[month_data['Grand Total'].idxmin()]
        monthly_total = month_data['Grand Total'].sum()
        summary = pd.DataFrame([
            {"Insight": "Busiest Day", "Date": busiest_day['Date'].strftime('%Y-%m-%d'), 
             "Day": busiest_day['Day'], "Ridership": busiest_day['Grand Total']},
            {"Insight": "Quietest Day", "Date": quietest_day['Date'].strftime('%Y-%m-%d'), 
             "Day": quietest_day['Day'], "Ridership": quietest_day['Grand Total']},
            {"Insight": "Monthly Total", "Date": "N/A", "Day": "N/A", "Ridership": monthly_total}
        ])
        columns = [{'name': col, 'id': col} for col in summary.columns]
        return summary.to_dict('records'), columns

    # Fallback: Return empty data and default columns
    return [], default_columns

# Run the Dash app
if __name__ == '__main__':
    app.run_server(debug=True)

