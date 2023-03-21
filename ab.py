import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import plotly.express as px
import numpy as np


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

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Define app layout
app.layout = html.Div([
    html.H1('Airbnb Dashboard'),
    dcc.Dropdown(
    id='price-dropdown',
    options=[{'label': cat, 'value': cat} for cat in sorted(df['price_category'].unique(), key=lambda x: float(x.split('-')[0]))],
    value='All',
    placeholder="Select a price category",
    style={"width": "200px"},
    clearable=True
    ),
    # Graph showing the number of hosts in each neighborhood group based on the selected price category
    dcc.Graph(
        id='graph',
        figure={}
    ),
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
        )
    ], style={'display': 'flex'})
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

if __name__ == '__main__':
    app.run_server(debug=False,port=80,host = '0.0.0.0')