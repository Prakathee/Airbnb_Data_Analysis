import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import numpy as np
import dash_table

df = pd.read_csv("Airbnb_Open_Data.csv")# Create Dash app

df.drop(columns = ['id'], inplace = True)
df.drop(columns = ['host name','country', 'country code', 'last review', 'reviews per month','license'], inplace = True)
df.drop(columns = ['house_rules'], inplace = True)

#removing rows with null values in all othercolumns, as they are very small

df.dropna(subset = ['NAME', 'host_identity_verified', 'neighbourhood group', 'neighbourhood',
                   'lat', 'long','instant_bookable', 'cancellation_policy','Construction year','price','service fee',
                   'minimum nights','number of reviews','review rate number','calculated host listings count',
                    'availability 365'],
          inplace = True)
          
          
df['price'] = df.price.str.strip(' ')

df['price'] = df['price'].apply(lambda x: x.replace('$',""))
df['price'] = df['price'].apply(lambda x: x.replace(',',""))

#cleaning Installs Columns
df['price'] =df['price'].astype(np.int64)

price_bins = [0, 250, 500, 750, 1000, 1200]
price_labels = ['0-250','250-500',
                '500-750','750-1000','1000.0-1200.0']

# create the new price category column
#f['price_category']=pd.cut(df.price,10, labels=price_labels)
df['price_category'] = pd.cut(df['price'], bins=price_bins, labels=price_labels)
# Create Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

year = df.groupby('Construction year', as_index=False).agg({'price':'sum','host id':'count'}).\
rename(columns = {'host id':'No of Airbnbs'})

room_type_counts = df.groupby('room type').size().reset_index(name='count')

app.layout = html.Div([
    html.H1(html.U(html.I('Airbnb Dashboard')), style={'fontSize':50, 'textAlign':'center', 'color':'Red'}),
    html.P(' '),
    html.P('Airbnb is a service that lets property owners rent out their spaces to travelers looking for a place to stay.\
           It was founded in 2008 and since then it has grown exponentially. I have created this dashboard using plotly dash. \
           This Dashboard gives insights on various Airbnb Properties in New-York City', style={ 'fontSize':20}),
    html.P(' '),

    html.Label('Select a Price Category', style={'fontWeight': 'bold'}),
    dcc.Dropdown(
        
        id='price-dropdown',
        options=[{'label': cat, 'value': cat} for cat in sorted(df['price_category'].unique(), key=lambda x: float(x.split('-')[0]))],
        value='All',
        placeholder="Select a price category",
        style={"width": "200px"},
        clearable=True
    ),
    # Graph showing the number of hosts in each neighborhood group based on the selected price category
    html.Div([
        dcc.Graph(
            id='graph',
            figure={}
        ),
        dcc.Graph(
            id='pie-chart',
            figure=px.pie(df, names='room type', title='Room Type Distribution').update_traces(hoverinfo='label+percent', textinfo='label+percent')
        ),
    ], style={'display': 'flex'}),
            # Table and last graph
    html.Div([
    # Table
    html.Div([
        html.H5('Top 10 Airbnb Listing in Each Price Category'),
        dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in ['NAME', 'review rate number']],
            data=df.nlargest(10, 'review rate number')[['NAME','review rate number']].to_dict('records'),
            style_cell={'textAlign': 'center', 'minWidth': '50px', 'width': '100px', 'maxWidth': '200px', 'whiteSpace': 'normal'},
            style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
            style_table={'width': '80%'},
            page_action='native',
            page_size=20,
            filter_action='native',
            sort_action='native',
            sort_mode='multi'
        )
    ], style={'flex': '1'}),
    
    # Graph showing the count of verified hosts by neighbourhood
    html.Div([
        html.Label('Select a Neighbourhood', style={'fontWeight': 'bold'}),
        dcc.Dropdown(
                id='neighbourhood-dropdown',
                options=[{'label': neighbourhood, 'value': neighbourhood} for neighbourhood in df['neighbourhood'].unique()],
                value=df['neighbourhood'].unique()[0],
                placeholder="Select a Neighbourhood",
                style={"width": "200px"}
            ),
        dcc.Graph(
            id='identity-verified-count',
            )
    ], style={'flex': '1'})
], style={'display': 'flex'}),

    html.Div([
        # Plot 1
        dcc.Graph(
            id='plot1',
            figure=px.box(df, x='room type', y='service fee').update_layout(title='Service Fee by Room Type')
        ),
        # Plot 2
        dcc.Graph(
            id='plot2',
            figure=px.scatter(df, x='price', y='service fee', color='room type', hover_data=['NAME']).update_layout(title='Price vs. Service Fee by Room Type')
        ),
    ], style={'display': 'flex'}),
    html.Div([
        # Plot 3
        dcc.Graph(
            id='plot3',
            figure=px.line(year, x='Construction year', y='price', hover_data=['No of Airbnbs']).update_layout(title='Number of Properties Constructed in Every year')
        )
    ], className='row'),
])

@app.callback(
    dash.dependencies.Output('graph', 'figure'),
    [dash.dependencies.Input('price-dropdown', 'value')]
)
def update_graph(price_category):
    # Filter the data based on the selected price category
    if price_category == 'All':
        filtered_df = df
    else:
        filtered_df = df[df['price_category'] == price_category]

    # Count the number of hosts in each neighborhood group
    counts = filtered_df.groupby('neighbourhood group').size().reset_index(name='counts')

    # Create the graph
    fig = px.bar(counts, x='neighbourhood group', y='counts', color='neighbourhood group')
    fig.update_layout(title=f"Number of Hosts by Neighborhood Group ({price_category})",
                      xaxis_title="Neighborhood Group",
                      yaxis_title="Number of Hosts")
    return fig


@app.callback(
    dash.dependencies.Output('pie-chart', 'figure'),
    [dash.dependencies.Input('price-dropdown', 'value')]
)
def update_pie_chart(price_category):
    # Filter the data based on the selected price category
    if price_category == 'All':
        filtered_df = df
    else:
        filtered_df = df[df['price_category'] == price_category]

    # Count the number of listings in each room type
    counts = filtered_df['room type'].value_counts().reset_index(name='counts')

    # Create the graph
    fig = px.pie(counts, names='index', values='counts', title=f"Number of Listings by Room Type ({price_category})")
    return fig

@app.callback(
    dash.dependencies.Output('table', 'data'),
    [dash.dependencies.Input('price-dropdown', 'value')]
)
def update_table(price_category):
    # Filter the data based on the selected price category
    if price_category == 'All':
        filtered_df = df
    else:
        filtered_df = df[df['price_category'] == price_category]

    # Get the top 10 listings by rating rate number
    top_listings = filtered_df[['NAME', 'review rate number', 'price']].sort_values(by='review rate number', ascending=False).head(10)

    # Convert the data to a list of dictionaries for display in the table
    data = top_listings.to_dict('records')

    # Add a column for displaying the rank of each listing
    for i, row in enumerate(data):
        row['Rank'] = i + 1

    return data

# Define the callback that updates the chart based on the selected neighbourhood
@app.callback(
    dash.dependencies.Output('identity-verified-count', 'figure'),
    [dash.dependencies.Input('neighbourhood-dropdown', 'value')]
)
def update_identity_verified_count(neighbourhood):
    filtered_df = df[df['neighbourhood'] == neighbourhood]
    identity_verified_count = filtered_df['host_identity_verified'].value_counts()
    fig = px.bar(identity_verified_count, x=identity_verified_count.index, y=identity_verified_count.values)
    fig.update_xaxes(title='Neighbourhood')
    fig.update_yaxes(title='Number of Hosts')
    fig.update_layout(title=f'Number of Verified in {neighbourhood}')
    return fig

#server=app.server

if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)