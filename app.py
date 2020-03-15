import dash
import os
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly
import plotly.graph_objects as go
import plotly.express as px
from toolz import groupby, unique
from io import StringIO
from textwrap import dedent as d
from dash.dependencies import Input, Output, State

mapbox_access_token = 'pk.eyJ1IjoiY2FsZGFzaHZpbm5nIiwiYSI6ImNqcGQzdXlndjAzbnkza3FndWwwZTdoeWoifQ.BDmYzs6179dETDzGW25WEg'



#dash app
server= app.server
app.config.suppress_callback_exceptions = True


#including bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

#read data into panda df
if(os.path.isfile('bfro_report_locations.csv')):
    df = pd.read_csv('bfro_report_locations.csv')

#HEADER
header = dbc.Container([
    html.Div(
        id="header",
        className='header',
        children=[
            html.H1('Sixth Sense')
        ]
    ),
])

#BODY
body = dbc.Container([
    dbc.Row([
    #MAP GRAPH
        dbc.Col([
            dbc.Row([
                dcc.Graph(id='CVgraph')
            ], ),
            dbc.Row([
                dt.DataTable(
                    id='case_table',
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=df.to_dict('records'),
                    style_table={
                        'maxHeight': '300px',
                        'overflowY': 'scroll',
                        'overflowX': 'scroll'
                    },
                )
            ], )
        ], width = 6),

        dbc.Col([
            dcc.Graph(
                id='mapgraph',
                clickData={'points': [{'customdata': '10407'}]}
            ),
        ], width = 6)
    ],
    style={"height": "400px"},
    ), #END OF dbc.Row
#================================================================================


            # YEAR SLIDER ROW
            html.Div(
                className='col',
                children=[
                    dcc.RangeSlider(
                        id='date-slider',
                        min=2000,
                        max=2019,
                        value=[2000,2010],
                        marks={str(year): str(year) for year in df['year'].unique()},
                        step=None,
                    ),
                ],
            ), #END OF YEAR SLIDER

            #CHECKING OUTPUT FROM CHECKLIST
            html.Div(
                id='checklist-output'
            ), #END OF CHECKING OUTPUT FROM CHECKLIST

            #CHECKLIST FOR CLASS
            html.Div(
                dcc.Checklist(
                    id='class-checklist',
                    options=[
                        {'label': 'Class A', 'value': 'Class A'},
                        {'label': 'Class B', 'value': 'Class B'},
                        {'label': 'Class C', 'value': 'Class C'}
                    ],
                    value=['Class A', 'Class A']
                ),
            ), #END OF CHECKLIST FOR CLASS



            #CLICK DATA OUTPUT
            html.Div([
                dcc.Markdown(d("""
                    **Click Data**

                    Click on points in the graph.
                    """
                )),
                html.Pre(id='click-data'),
            ],
                className='three columns'
            ), #CLICK DATA OUTPUT

            #YEAR GRAPH
            html.Div(
                className = 'col',
                children = [
                    dcc.Graph(
                        id='by_year',
                        animate = True,
                        style={
                          'width': '80%',
                          'height': 600,
                        }
                    )
                ]
            ) #END OF YEAR GRAPH
        ]

) #END of dbc.Container

app.layout = html.Div([header, body])


@app.callback(
    Output('click-data', 'children'),
    [Input('mapgraph', 'clickData')])
def display_click_data(clickData):
    return 'Title is "{}"'.format(clickData['points'][0]['customdata'])


@app.callback(
    Output('checklist-output', 'children'),
    [Input('class-checklist', 'value')])
def checklist_output(value):
    string = "Selected classes are "
    for values in value:
        string = string + " " + values
    return string

#MAPGRAPH
@app.callback(
    Output('mapgraph', 'figure'),
    [Input('date-slider', 'value'),
    Input('class-checklist', 'value')]
)
def update_map(year, classification):
    #Update dataframe with the passed value
    dff = df[(df['year'] >= year[0]) & (df['year'] <=year[1])]
    dff_c = dff[dff['classification']=='empty']
    for classes in classification:
        dff_c = dff_c.append(dff[dff['classification'] == classes], ignore_index=True)

    # Paint mapbox into the data
    mapdata = go.Data([
        go.Densitymapbox(
            lat=dff_c['latitude'],
            lon=dff_c['longitude'],
            z=dff_c['magnitude'],
            customdata=dff_c['number'],
            colorscale='hot',
            visible=True,
        )
    ],

        )


    # Layout and mapbox properties
    layout = go.Layout(
        autosize=True,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            pitch=0,
            center=dict(lat=34.5, lon=-94.8),
            zoom=4,
            style='mapbox://styles/caldashvinng/ck5i8qzci0t8t1iphlvn9sdz7'
        ),

    )


    return go.Figure(
            data = mapdata,
            layout = layout
            )


#CREATE CV GRAPH
def create_CV(dff):
    data = go.Data([
        go.Scatter(
            name='CV Graph',
            x=np.arange(0,100),
            y=dff.iloc[:,1],
            mode='lines',
            visible = True,
            hoverlabel={
                'bgcolor': '#FFF',
            },
        ),
    ])

    layout = go.Layout(
        xaxis={
            #'autorange': True,
            'color': '#000000',
            'title': 'x',
            'range': [dff.iloc[:,0].min(), dff.iloc[:,0].max()],
            'dtick': 1
        },
        yaxis={
            #'autorange': True,
            'color': '#000000',
            'title': 'y',
            'range': [dff.iloc[:,1].min(), dff.iloc[:,1].max()],
            #'dtick': 5
        },
        margin={
            'l': 0,
            'b': 0,
            't': 0,
            'r': 0
        },
        hovermode='closest',
        paper_bgcolor='#FFFFF0',
        plot_bgcolor='#FFFFF0',
        autosize = True,
    )

    return go.Figure(
        data=data,  # 54b4e4
        layout=layout
    )


#UPDATE CVGRAPH
@app.callback(
    Output('CVgraph', 'figure'),
    [Input('mapgraph', 'clickData')]
    )
def update_CV(clickData):
    dff = df[df['number'] == clickData['points'][0]['customdata']]
    data = df.iloc[0,8]
    datastring = StringIO(data)
    dff = pd.read_csv(datastring, header=None)

    return (create_CV(dff))


#YEAR GRAPH
@app.callback(
    Output('by_year', 'figure'),
    [Input('date-slider', 'value'),
    Input('class-checklist', 'value')]
)
def by_year(year, classification):
    dff = df[(df['year'] >= year[0]) & (df['year'] <=year[1])]
    dfff = dff[dff['classification']=='empty']
    for classes in classification:
        dfff = dfff.append(dff[dff['classification'] == classes], ignore_index=True)
    dfff = dfff.groupby(['year','classification'] , as_index=False).count()
    dff_A = dfff[dfff['classification'] == 'Class A']['number']
    dff_B = dfff[dfff['classification'] == 'Class B']['number']
    dff_C = dfff[dfff['classification'] == 'Class C']['number']
    y_min = dfff['number'].min()
    y_max = dfff['number'].max()

    data = go.Data([
        go.Scatter(
            name='class A',
            # events qty
            x=np.arange(year[0], year[1]),
            # year
            y=dff_A,

            mode='lines',
            visible = True,
            marker={
                'symbol': 'circle',
                'size': 5,
                'color': '#eb1054'
                },
            hoverlabel={
                'bgcolor': '#FFF',
            },
        ),
        go.Scatter(
            name='class B',
            # events qty
            x=np.arange(year[0], year[1]),
            # year
            y=dff_B,

            mode='lines',
            visible = True,
            marker={
                'symbol': 'circle',
                'size': 5,
                'color': '#C2FF0A'
                },
            hoverlabel={
                'bgcolor': '#FFF',
            },
        ),
        go.Scatter(
            name='class C',
            # events qty
            x=np.arange(year[0], year[1]),
            # year
            y=dff_C,

            mode='lines',
            visible = True,
            marker={
                'symbol': 'circle',
                'size': 5,
                'color': '#52e5ec'
                },
            hoverlabel={
                'bgcolor': '#FFF',
            },
        ),
    ])

    layout = go.Layout(
        xaxis={
            #'autorange': True,
            'color': '#000000',
            'title': 'year',
            'range': [year[0], year[1]],
            'dtick': 1
            },
        yaxis={
            #'autorange': True,
            'color': '#000000',
            'title': 'Count',
            'range': [y_min-50, y_max+50],
            #'dtick': 5
            },
        margin={
            'l': 0,
            'b': 0,
            't': 0,
            'r': 0
            },
            hovermode='closest',
            paper_bgcolor='#FFFFF0',
            plot_bgcolor='#FFFFF0',
            autosize = True,
            )

    return go.Figure(
        data=data,  # 54b4e4
        layout=layout
        )



# Run dash server
if __name__ == '__main__':
    app.run_server(debug=True)
