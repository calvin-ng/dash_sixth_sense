import dash
import os
import dash_core_components as dcc
import dash_html_components as html
import dash_renderer
import dash_table as dt
import dash_bootstrap_components as dbc
import dash_daq as daq
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
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server= app.server
app.config.suppress_callback_exceptions = True


#read data into panda df
if(os.path.isfile('testdata.csv')):
    df = pd.read_csv('testdata.csv')

#dropping any rows with missing values
df.dropna(inplace=True)


app.title = 'CBSD Cases'
#HEADER
header = dbc.Row([html.H1('Cassava Brown Streak Virus Disease Cases (Test Data)', style={'color': '#756263'})])


#BODY
body = html.Div(
    children=[
        dbc.Row([
        #MAP GRAPH
            html.Div(
                dcc.Graph(
                    id='mapgraph',
                    clickData={'points': [{'customdata': '1670'}]},
                    style={'width': '100%','padding': '0px'}
                ),
                className = 'col-lg-10'
            ), #left column

            html.Div(
                children=[
                    html.Div('TOTAL CASES', style={'font-size':'24px', 'text-align':'left', 'color':'#756263', 'font-weight': 'bold', 'margin-left':'5px'}),
                    daq.LEDDisplay(
                        id='total_cases',
                        value= 0,
                        size=80,
                        color="#756263",
                        backgroundColor="#FFFFFF",
                    ),
                    html.Div('CASE INFORMATION', style={'font-size':'20px', 'text-align':'left', 'color':'#756263', 'font-weight': 'bold', 'margin-left':'5px'}),
                    html.Div(id='case_info', style={'background':'#FFFFFF', 'padding':'10px', 'margin-top':'5px', 'font-size':'18px', 'color':'#000000'}),
                ],
                className = 'col-lg-2'
            )


        ], style={"width":"100%"}), #END OF dbc.Row
#================================================================================

        dbc.Row([            # YEAR SLIDER ROW
            html.Div(
                children=[
                    dcc.RangeSlider(
                        id='date-slider',
                        min=df['year'].min(),
                        max=df['year'].max(),
                        value=[df['year'].min(),df['year'].max()],
                        marks={int(year) : str(year) for year in df['year'].unique()},
                        step=None ,
                    ),
                ], className='col-lg-10',
            ), #END OF YEAR SLIDER
        #CHECKLIST FOR CLASS
            html.Div(
                children=[
                    html.Div(id='class-toggle-output', style={'font-size':'16px', 'text-align':'center', 'color':'#756263', 'font-weight': 'bold'}),
                    daq.ToggleSwitch(
                        id='class-toggle',
                        value=True,
                        size=70,
                    )
                ],
                className='col-lg-2',
                style={'padding':'5px'}
            ),

        ], style={'padding': '50px'}),


        dbc.Row([
            dcc.Store(id="store"),
            dbc.Tabs(
                [
                    dbc.Tab(label="Cumulative number of cases by year", tab_id="cum_graph"),
                    dbc.Tab(label="Number of cases per year", tab_id="ind_graph"),
                ],
                id="tabs",
            ),
            html.Div(id="tab-content", className="p-4"),
        ],className='col-lg-12')

    ], style={'margin' : '0px', 'padding':'0px'}) #END of dbc.Container

app.layout = html.Div(
    children=[header, body],
)

#======================================================================
#============app callback and function declarations
#======================================================================

#UPDATE TOTAL CASES
@app.callback(
    Output('total_cases', 'value'),
    [Input('date-slider', 'value'),
    Input('class-toggle', 'value')])
def update_total_cases(year, toggle):
    if toggle:
        classification = 'Infected'
    else:
        classification = 'Not Infected'

    dff = df[(df['year'] >= year[0]) & (df['year'] <=year[1])]
    dff = dff[df['classification'] == classification]

    return dff.shape[0]

#UPDATE CASE INFO
@app.callback(
    Output('case_info', 'children'),
    [Input('mapgraph', 'clickData')]
    )
def update_case_info(clickData):
    if (df[df['number'] == clickData['points'][0]['customdata']].shape[0]) == 0:
        return "No case selected"
    else:
        dff = (df[df['number'] == clickData['points'][0]['customdata']])
        number = dff['number'].values[0]
        user_id = dff['user id'].values[0]
        date = str(dff['date'].values[0]) + "-" + str(dff['year'].values[0])
        classification = dff['classification'].values[0]
        info =  ["Case #: {}".format(number), html.Br(),
            "User ID: {}".format(user_id), html.Br(),
            "Date: {}".format(date), html.Br(),
            "Status: {}".format(classification)]
        return info


#UPDATE TOGGLE DISPLAY
@app.callback(
    Output('class-toggle-output', 'children'),
    [Input('class-toggle', 'value')])
def update_output(value):
    if value:
        return 'Showing infected cases'
    else:
        return 'Showing non-infected cases'


#MAPGRAPH
@app.callback(
    Output('mapgraph', 'figure'),
    [Input('date-slider', 'value'),
    Input('class-toggle', 'value')]
)
def update_map(year, toggle):
    if toggle:
        classification = 'Infected'
    else:
        classification = 'Not Infected'
    #Update dataframe with the passed value
    dff = df[(df['year'] >= year[0]) & (df['year'] <=year[1])]
    #dff_c = dff[dff['classification']=='empty']
    #for classes in classification:
    #    dff_c = dff_c.append(dff[dff['classification'] == classes], ignore_index=True)
    dff_c = dff[df['classification'] == classification]
    # Paint mapbox into the data
    mapdata = go.Data([
        go.Densitymapbox(
            lat=dff_c['latitude'],
            lon=dff_c['longitude'],
            customdata=dff_c['number'],
            colorscale='hot',
            visible=True,
            colorbar=dict(borderwidth=1, xpad=1, ypad=1, thickness=3)
        )
    ])

    # Layout and mapbox properties
    layout = go.Layout(
        #autosize=True,
        hovermode='closest',
        mapbox=dict(
            accesstoken=mapbox_access_token,
            bearing=0,
            pitch=0,
            center=dict(lat=-4.088772, lon=36.369427),
            zoom=4,
            style='mapbox://styles/caldashvinng/ck5i8qzci0t8t1iphlvn9sdz7'
        ),
        margin={
            'l': 0,
            'b': 0,
            't': 0,
            'r': 0
        },
    )

    return go.Figure(
            data = mapdata,
            layout = layout
    )



#YEAR GRAPH
@app.callback(
    Output('store', 'data'),
    [Input('date-slider', 'value')]
)
def by_year(year):
    dff = df[(df['year'] >= year[0]) & (df['year'] <=year[1])]
    # dfff = dff[dff['classification']=='empty']
    classification =['Infected', 'Not Infected']
    for classes in classification:
    #     dfff = dfff.append(dff[dff['classification'] == classes], ignore_index=True)
        dff_counted = dff.groupby(['year','classification'] , as_index=False).count()
    dff_A = dff_counted[dff_counted['classification'] == 'Infected']['number']
    dff_B = dff_counted[dff_counted['classification'] == 'Not Infected']['number']
    y_min = dff_counted['number'].min()
    y_max = dff_counted['number'].max()

    ind_graph = go.Figure(
        data = go.Data([
            go.Bar(
                name='Infected',
                x=np.arange(year[0], year[1]),
                y=dff_A,
                visible = True,
                hoverlabel={
                    'bgcolor': '#FFF',
                },
                marker_color='#407438'
            ),
            go.Bar(
                name='Not Infected',
                # events qty
                x=np.arange(year[0], year[1]),
                # year
                y=dff_B,
                visible = True,
                hoverlabel={
                    'bgcolor': '#FFF',
                },
                marker_color = '#65BC22'
            ),

        ]),  # 54b4e4

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
                'title': 'Number of Cases',
                'range': [y_min, y_max],
                #'dtick': 5
                },
            margin={
                'l': 0,
                'b': 0,
                't': 0,
                'r': 0
                },
                hovermode='closest',
                paper_bgcolor='#F0E4E3',
                plot_bgcolor='#F0E4E3',
                autosize = True,
                )
        )

    cum_graph = go.Figure(
        data = go.Data([
            go.Scatter(
                name='Infected',
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
                name='Not Infected',
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
            )
        ]),

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
                'title': 'Number of Cases',
                'range': [y_min, y_max],
                #'dtick': 5
                },
            margin={
                'l': 0,
                'b': 0,
                't': 0,
                'r': 0
                },
                hovermode='closest',
                paper_bgcolor='#F0E4E3',
                plot_bgcolor='#F0E4E3',
                autosize = True,
        )
    )

    return {"cum_graph":cum_graph, "ind_graph":ind_graph}


#RENDERING TAB CONTENT
@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "active_tab"), Input("store", "data")],
)
def render_tab_content(active_tab, data):
    if active_tab and data is not None:
        if active_tab == "cum_graph":
            return dcc.Graph(figure=data["cum_graph"])
        elif active_tab == "ind_graph":
            return dcc.Graph(figure=data["ind_graph"])
    return data



# html.Div(
#     children = [
#         dcc.Graph(
#             id='by_year',
#             animate = True,
#         )
#     ],
#     className='col-lg-12',)
#=================Commented, saved for later=============#######
#####=============================================##############
# RADIO ITEM LIST
# dcc.RadioItems(
#     id='class-radio',
#     options=[
#         {'label': 'Infected', 'value': 'Infected'},
#         {'label': 'Not-Infected', 'value': 'Not Infected'},
#     ],
#     value='Infected'
# ),
#
# #CHECKLIST FOR CLASS
#     html.Div(
#         dcc.Checklist(
#             id='class-checklist',
#             options=[
#                 {'label': 'Infected', 'value': 'Infected'},
#                 {'label': 'Not-Infected', 'value': 'Not Infected'},
#             ],
#             value=['Infected']
#         ),
#     ), #END OF CHECKLIST FOR CLASS
#
#             html.Div( #col-lg-3 div
#                 children=[
#                     dt.DataTable(
#                         id='case_table',
#                         columns=[{"name": i, "id": i} for i in df.columns],
#                         data=df.to_dict('records'),
#                         style_table={
#                             'maxHeight': '420px',
#                             'maxWidth':'300px',
#                             'overflowY': 'scroll',
#                             'overflowX': 'scroll'
#                         },
#                     ),
#
#                     # html.Div( #div for the graph
#                     #     dcc.Graph(id='CVgraph')
#                     # ),
#                 ],
#
#                 className='col-lg-3',
#             )

#
# #CREATE CV GRAPH
# def create_CV(dff):
#     data = go.Data([
#         go.Scatter(
#             name='CV Graph',
#             x=np.arange(0,100),
#             y=dff.iloc[:,1],
#             mode='lines',
#             visible = True,
#             hoverlabel={
#                 'bgcolor': '#FFF',
#             },
#         ),
#     ])
#
#     layout = go.Layout(
#         xaxis={
#             #'autorange': True,
#             'color': '#000000',
#             'title': 'x',
#             'range': [dff.iloc[:,0].min(), dff.iloc[:,0].max()],
#             'dtick': 1
#         },
#         yaxis={
#             #'autorange': True,
#             'color': '#000000',
#             'title': 'y',
#             'range': [dff.iloc[:,1].min(), dff.iloc[:,1].max()],
#             #'dtick': 5
#         },
#         margin={
#             'l': 0,
#             'b': 0,
#             't': 0,
#             'r': 0
#         },
#         hovermode='closest',
#         paper_bgcolor='#FFFFF0',
#         plot_bgcolor='#FFFFF0',
#         #autosize = True,
#     )
#
#     return go.Figure(
#         data=data,  # 54b4e4
#         layout=layout
#     )
#
#
# #UPDATE CVGRAPH
# @app.callback(
#     Output('CVgraph', 'figure'),
#     [Input('mapgraph', 'clickData')]
#     )
# def update_CV(clickData):
#     dff = df[df['number'] == clickData['points'][0]['customdata']]
#     data = df.iloc[0,8]
#     datastring = StringIO(data)
#     dff = pd.read_csv(datastring, header=None)
#
#     return (create_CV(dff))


# Run dash server
if __name__ == '__main__':
    app.run_server(debug=True)
