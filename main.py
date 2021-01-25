import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import numpy as np
import json
from dash.dependencies import Input, Output


sc_global = pd.read_csv('Data/sunburst_cases.csv')
sd_global = pd.read_csv('Data/sunburst_deaths.csv')

us_data = pd.read_csv('Data/data.csv')

recent_data = pd.read_csv('Data/US_data_update.csv')

scatter_data = pd.read_csv('Data/4_weeks_data.csv')
scatter_data['R_minus'] = scatter_data['R_mean'] - scatter_data['R_low']
scatter_data['R_plus'] = scatter_data['R_high'] - scatter_data['R_mean']
scatter_data['dailycases_p100k_7d_avg'] = scatter_data['dailycases_p100k_7d_avg'].round(
    5)
scatter_data['per_100k'] = (
    scatter_data['dailycases_p100k_7d_avg'] / scatter_data['Population']) * 100000

date_list = list(scatter_data.Date.unique())
states = list(scatter_data.Province_State.unique())

scatter_data.rename(columns={'Province_State': 'State',
                             'dailycases_p100k_7d_avg': 'Average',
                             'R_mean': 'R mean',
                             'R_low': 'R Low',
                             'R_high': 'R High',
                             'per_100k': 'Daily Cases'},
                    inplace=True)

us_data['Date'] = pd.to_datetime(us_data['Date'])
recent_date = us_data['Date'].dt.strftime("%d-%B-%Y").iloc[-1]

us_data['Country'] = 'US'

recent_us = us_data[us_data['Date'] == recent_date]

global_df = pd.read_csv('Data/global_data.csv')

global_cases = global_df['Global Cases'][0]
global_deaths = global_df['Global Deaths'][0]
global_recovered = global_df['Global recovered'][0]

def sunburst_visual(df, type_tracked):
    sunburst_fig = px.sunburst(
    df,
    path=['Continent', 'Country/Region'],
    values=str(type_tracked),
    branchvalues='total',
    labels={
        str(type_tracked): 'Total ' + str(type_tracked),
        },
    title="Highest five confirmed total " + str(type_tracked).lower() + "<br>by countries in each<br>continent",
    color='Continent',
    color_discrete_map= {
        'Europe' : 'green',
        'Africa' : 'orange',
        'North America': 'blue',
        'South America' : 'darkturquoise',
        'Asia' : 'red'
        }
    )
    return sunburst_fig

sunburst_cases = sunburst_visual(sc_global, 'Confirmed')
sunburst_deaths = sunburst_visual(sd_global, 'Deaths')

total_us = us_data.copy()
total_us = total_us.groupby(['Date']).sum()

t_c = total_us['Confirmed'].iloc[-1]
t_d = total_us['Deaths'].iloc[-1]

us_barchart = go.Figure(data=[
    go.Bar(name='Cases',
           x=total_us.index,
           y=total_us['Daily Confirmed'],
           marker_color='blue',
           hovertemplate='Cases: %{y}<br><extra></extra>'),
    go.Bar(name='Deaths',
           x=total_us.index,
           y=total_us['Daily Deaths'],
           marker_color='red',
           hovertemplate='Deaths: %{y}<br><extra></extra>')
])
us_barchart.update_layout(title_text=f"United States<br>Total Cases: {t_c:,d} Total Deaths: {t_d:,d}",
                          barmode='stack')

us_barchart.add_trace(go.Scatter(x=total_us.index,
                                 y=total_us['7_day_avg'],
                                 mode='lines',
                                 name='7 Day Average',
                                 line=dict(color='rgb(184,55,223)'),
                                 hovertemplate='7 Day Average: %{y}<br><extra></extra>'
                                 )
                      )
us_barchart.update_layout(
    title={
        'y': .91,
        'x': 0.5,
        'xanchor': 'center',
        'yanchor': 'top'},
    xaxis_title="Date",
    yaxis_title="Daily Count",
    hovermode="x",
    width=1200
)

choro_map = px.choropleth(recent_data, locations='abv', locationmode="USA-states", scope="usa", color='R_mean',
                          labels={
                              'R_mean': 'Reproduction Rate <br>mean'},
                          color_continuous_scale="reds",
                          hover_name=recent_data['Province_State'],
                          range_color=[0, recent_data['R_mean'].max()]
                          )
layout = go.Layout(geo=dict(bgcolor='rgba(0,0,0,0)'),
                   title=go.layout.Title(
                       text="United States Reproduction Rate by State",
                       x=0.5
),
    font=dict(size=16),
    width=1000,
)

choro_map.update_layout(layout)


low_x = scatter_data['R mean'].min()
high_x = scatter_data['R mean'].max()
low_y = scatter_data['Daily Cases'].min()
high_y = scatter_data['Daily Cases'].max()

scatter_dict = {
    "data": [],
    "layout": {},
    "frames": []
}

# fill in most of layout
scatter_dict["layout"]["xaxis"] = {"range": [
    low_x, high_x], "title": "Reproduction Rate<br>(bubble size indicates population)"}
scatter_dict["layout"]["yaxis"] = {"range": [
    low_y, high_y], "title": "Daily Cases (7 day average per 100k population)"}
scatter_dict["layout"]["width"] = 1000
scatter_dict["layout"]["height"] = 1000
scatter_dict["layout"]["hoverlabel"] = dict(bgcolor="white",
                                            font_size=16,
                                            font_family="Rockwell",
                                            )

scatter_dict["layout"]["hovermode"] = "closest"
scatter_dict["layout"]["shapes"] = [dict(
    type='line',
    x0=1,
    x1=1,
    y0=low_y-10,
    y1=high_y,
    line=dict(
        color='Black',
        dash='dash'))
]
scatter_dict["layout"]["title"] = {
    'text': 'United States R-rate for each state<br>(Last 30 days)',
            'font_size': 20,
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'}

scatter_dict["layout"]["updatemenus"] = [
    {
        "buttons": [
            {
                "args": [None, {"frame": {"duration": 500, "redraw": False},
                                "fromcurrent": True, "transition": {"duration": 300,
                                                                    "easing": "quadratic-in-out"}}],
                "label": "Play",
                "method": "animate"
            },
            {
                "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                  "mode": "immediate",
                                  "transition": {"duration": 0}}],
                "label": "Pause",
                "method": "animate"
            }
        ],
        "direction": "left",
        "pad": {"r": 10, "t": 87},
        "showactive": False,
        "type": "buttons",
        "x": 0.1,
        "xanchor": "right",
        "y": 0,
        "yanchor": "top"
    }
]

sliders_dict = {
    "active": 0,
    "yanchor": "top",
    "xanchor": "left",
    "currentvalue": {
        "font": {"size": 20},
        "prefix": "Date:",
        "visible": True,
        "xanchor": "right"
    },
    "transition": {"duration": 300, "easing": "cubic-in-out"},
    "pad": {"b": 10, "t": 50},
    "len": 0.9,
    "x": 0.1,
    "y": 0,
    "steps": []
}

# make data
date = list(scatter_data.Date.unique())[0]
for State in states:
    dataset_by_date = scatter_data[scatter_data["Date"] == date]
    dataset_by_date_and_cont = dataset_by_date[
        dataset_by_date["State"] == State]

    data_dict = {
        "x": list(dataset_by_date_and_cont["R mean"]),
        "error_x": dict(type='data',
                        symmetric=False,
                        array=dataset_by_date_and_cont['R_plus'],
                        arrayminus=dataset_by_date_and_cont['R_minus'],
                        thickness=0.5,
                        ),
        "y": list(dataset_by_date_and_cont["Daily Cases"]),
        "mode": "markers",
        "marker": dict(size=np.log(dataset_by_date_and_cont['Population'])),
        "hovertemplate": dataset_by_date_and_cont['State'] +
        '<br>R Rate (mean): %{x:.2f}' +
        '<br>Daily Cases: %{y}<br><extra></extra>',
        "text": list(dataset_by_date_and_cont["State"]),
        "name": State
    }
    scatter_dict["data"].append(data_dict)

# make frames
for Date in date_list:
    frame = {"data": [], "name": str(Date)}
    for State in states:
        dataset_by_Date = scatter_data[scatter_data["Date"] == Date]
        dataset_by_Date_and_cont = dataset_by_Date[
            dataset_by_Date["State"] == State]

        data_dict = {
            "x": list(dataset_by_Date_and_cont["R mean"]),
            "error_x": dict(type='data',
                            symmetric=False,
                            array=dataset_by_Date_and_cont['R_plus'],
                            arrayminus=dataset_by_Date_and_cont['R_minus'],
                            thickness=0.5,
                            ),
            "y": list(dataset_by_Date_and_cont["Daily Cases"]),
            "mode": "markers",
            "marker": dict(size=np.log(dataset_by_Date_and_cont['Population'])),
            "hovertemplate": dataset_by_Date_and_cont['State'] +
            '<br>R Rate (mean): %{x:.2f}' +
            '<br>Daily Cases: %{y}<br><extra></extra>',
            "text": list(dataset_by_Date_and_cont["State"]),
            "name": State
        }
        frame["data"].append(data_dict)

    scatter_dict["frames"].append(frame)
    slider_step = {"args": [
        [Date],
        {"frame": {"duration": 300, "redraw": False},
         "mode": "immediate",
         "transition": {"duration": 300}}
    ],
        "label": Date,
        "method": "animate"}
    sliders_dict["steps"].append(slider_step)


scatter_dict["layout"]["sliders"] = [sliders_dict]

scatter_plot = go.Figure(scatter_dict)


sunburst_states = px.sunburst(
    recent_us,
    path=['Country', 'Province_State'],
    values='Confirmed',
    labels={
        'Confirmed': 'Total Confirmed'
    },
    title='Total Confirmed Covid-19 Cases by State as of ' + str(recent_date)
)

external_stylesheets = [dbc.themes.LUX]

app = dash.Dash(
    __name__, external_stylesheets=external_stylesheets, title='Covid-19')

server = app.server

app.config.suppress_callback_exceptions = True

app.layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col(),
            dbc.Col(html.H1('Visualizing COVID-19'),
                    className="mb-2", width=6),
            dbc.Col()
        ]),
        dbc.Row([
            html.P('This website is a project I have been working on with one of my mentors and former professor.' +
                   ' The hope was to create interactive and intuitive visuals for tracking the spread of Covid-19 in the United States.'
                   + ' All data is sourced directly from the Johns Hopkins University data repository on Github.'
                   + ' Data imported and processed using Pandas library in Python.'
                   + ' R-rate calculations were done using the EpiEstim library in R studio.'
                   + ' Visuals were created with Plotly while the webpage was designed using Dash.'
                   + ' The page is hosted using Google Cloud Platform.')
        ]),
        dbc.Row([
            dbc.Col(),
            dbc.Col(html.H5('Links to the data and libraries used:'), width=6),
            dbc.Col()
        ]),
        dbc.Row([
            html.Hr()
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Link('Johns Hopkins GitHub',
                         href='https://github.com/CSSEGISandData/COVID-19'),
                html.P('Data stored tracking global confirmed cases and deaths from the coronavirus (Covid-19)')]
            ),
            dbc.Col([
                dcc.Link('Plotly/Dash', href='https://plotly.com/'),
                html.P('Interactive data visualization library in Python and R')]
            ),
            dbc.Col([
                dcc.Link(
                    'EpiEstim Library', href='https://cran.r-project.org/web/packages/EpiEstim/index.html'),
                html.P('Epidemic estimation library for reproduction rate calculations for a virus')]
            ),
            dbc.Col([
                dcc.Link(
                    'CDC article', href='https://wwwnc.cdc.gov/eid/article/26/6/20-0357_article'),
                html.P(
                    'CDC released paper outlining the estimated Serial Interval values for the virus')
            ])
        ]),
        dbc.Row([
            html.Hr()
        ]),
        dbc.Row([
            dbc.Col(),
            dbc.Col(html.H5('Check out some of my other work:'), width=6),
            dbc.Col()
        ]),
        dbc.Row([
            html.Br()
        ]),
        dbc.Row([
            html.Hr()
        ]),
        dbc.Row([
            dbc.Col([
                dcc.Link('My portfolio website',
                         href='https://danielbsimpson.github.io/'),
                html.P(
                    "Personal website I set up to showcase some of the work I've done related to Data Scince")
            ]),
            dbc.Col([
                dcc.Link('About the Author',
                         href='https://danielbsimpson.github.io/generic.html'),
                html.P(
                    "If you wish to know a little bit more about me or want to get in contact, I'm always looking for new projects")
            ]),
            dbc.Col([
                dcc.Link('My GitHub page',
                         href='https://github.com/danielbsimpson'),
                html.P("You can view some of my code in my GitHub repositories")
            ]),
            dbc.Col([
                dcc.Link(
                    'LinkedIn', href='https://www.linkedin.com/in/daniel-b-simpson/'),
                html.P('Connect with me professionally on my LinkedIn page')
            ])
        ]),
        dbc.Row([
            html.Br()
        ]),
        dbc.Row([
            dbc.Col(dbc.Card(html.H3(children='Data updated as of ' + str(recent_date),
                                     className="text-center text-light bg-dark"),
                             body=True, color="dark"),
                    className="mb-4"
                    )
        ]),
        dbc.Row([
            dbc.Col(),
            dbc.Col(html.H2('Global Data')),
            dbc.Col()
        ]),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H2('Cases'),
                html.H4(f"{global_cases:,d}")
            ]
            ))),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H2('Deaths'),
                html.H4(f"{global_deaths:,d}")
            ]
            ))),
            dbc.Col(dbc.Card(dbc.CardBody([
                html.H2('Recovered'),
                html.H4(f"{global_recovered:,d}")
            ]
            ))),
        ]),
        dbc.Row([
            html.Hr()
        ]),
        dbc.Row([
            html.H2('Global sunburst visuals'),
            html.P('These visuals display the five countries with the highest confirmed cases and deaths on each continent.'
                   + ' Australian continent was not included because the total cases and deaths were so much smaller than other continents that'
                   + ' the values would not be visible on the sunburst infographic. These are interactive so if you click on a continent '
                   + ' you can get a better idea for the proportion of each country in that continent.')
        ]),
        dbc.Row([
            dbc.Col(dcc.Graph(id='sunburst_cases', figure=sunburst_cases)),
            dbc.Col(dcc.Graph(id='sunburst_deaths', figure=sunburst_deaths))
        ]),
        dbc.Row([
            html.Hr()
        ]),
        dbc.Row([
            html.H2('Cases and Deaths in the United States'),
            html.P('This visual gives an idea of the total cases and deaths confirmed each day in the United States.'
                   + ' By hovering over the graph, you can see specific days and the total cases and deaths for that day.'
                   + ' A seven day running average of confirmed cases is also shown as a line, giving an idea of the overall'
                   + ' trend of cases for the last seven days.')
        ]),
        dbc.Row([
            html.Br()
        ]),
        dbc.Row([
            dcc.Graph(id='us_barchart', figure=us_barchart),
        ]),
        dbc.Row([
            html.H2('United States Choropleth Map of R-rate per State'),
            html.P('This is a visual of the most recent reproduction rate of the virus for each state as a whole.'
                   + ' Hover over a state to see the current reproduction rate mean value for that state.')
        ]),
        dbc.Row([
            dcc.Graph(id='Choropleth_map', figure=choro_map)
        ]
        ),
        dbc.Row([
            html.H2('Scatter plot of R-rate and seven Day Average'),
            html.P('The visual shows the reproduction rate and the previous seven day average for diagnosed cases per 100,000 population over the last 30 days.'
                   + " If zoomed in the error bars for the reproduction rate can be seen for each state with 95% confidence."
                   + ' You can unselect a specific state by selecting it on the right side legend.'
                   + ' Double clicking on the legend on the right will unselect all states and then individual states can be selected'
                   + ' allowing the user to only view the state they wish to see.'
                   + ' A zoom box can also be created by clicking and dragging on the scatter plot.')
        ]),
        dbc.Row([
            dcc.Graph(id='r-scatter-states', figure=scatter_plot)
        ]),
        dbc.Row([
            html.Hr(),
            html.Hr()
        ]),
        dbc.Row([
            html.H2('Proportion of states with the most cases'),
            html.P('Similar to the sunburst visuals above, this gives a snapshot of which states have had the highest infections in the US as a proportion of the total.')
        ]),
        dcc.Graph(id='sunburst_states', figure=sunburst_states),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(
                [
                    html.H3(
                        'Select a state to see the cases, deaths and r-rate over time', className="card-title"),
                ]
            ))
            ),
        ],
            align="center",
        ),
        dcc.Dropdown(id='drop_bar',
                     options=[{'label': x, 'value': x}
                              for x in us_data.Province_State.unique()],
                     value='Alabama',
                     multi=False,
                     ),
        dbc.Row([
            html.Br(),
        ]),
        dbc.Row([
            html.H2(
                'Confirmed cases and deaths for each day since the first case was reported'),
            html.P('This bar chart gives and idea of the confirmed cases and deaths each day for the states.'
                   + ' The blue bars represent confirmed cases, while the red bars sitting on top represent the deaths from'
                   + ' covid-19. The seven day average for diagnosed cases is displayed to give an idea of the trend.')
        ]),
        dcc.Graph(
            id='time_graph',
            figure={}
        ),
        dbc.Row([
            html.H2('Reproducton rate by state'),
            html.P('This is the reprodction rate of the state, showing the cofidence interval from the EpiEstim library of 0.05-0.95.'
                   + 'Standard deviation SI and mean SI were taken from a CDC released paper that estimated the values for the spread of the virus.')
        ]),
        dcc.Graph(
            id='R_rate',
            figure={}
        ),
        dbc.Row(
            [
                dbc.Col(
                    dbc.Card(dbc.CardBody(
                        [
                            html.H2(
                                'Select a county to see the cases and r-rate over time', className="card-title"),
                            html.H5(
                                'This will update the list of counties depending on the state selected above', className="card-subtitle"
                            ),
                            html.P(
                                "(If the graph doesn't update there is not enough data to estimate a reproduction rate)", className="card-body")
                        ]
                    ))
                ),
            ],
            align="center",
        ),
        html.Hr(),
        dcc.Dropdown(
            id='county_drop_bar',
            value = 'Autauga'),
        dcc.Graph(
            id='county_cases',
            figure={}
        ),
        dcc.Graph(
            id='county_r-rate',
            figure={}
        ),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(
                [
                    html.H3(
                        'Select a state to view recent information on county level', className="card-title"),
                    html.P(
                        '(This can take up to 5 seconds to update the visuals)', className="card-subtitle")
                ]
            ))
            ),
        ],
            align="center",
        ),
        dcc.Dropdown(id='drop_bar_state',
                     options=[{'label': x, 'value': x}
                              for x in us_data.Province_State.unique()],
                     value='Alabama',
                     multi=False,
                     ),
        dbc.Row([
            html.H2('Choropleth and sunburst for state counties'),
            html.P('Similar to choropleth map and sunburst infographic above, these visualize the reproduction rate and total confirmed cases'
                   + ' per county for the selected state.')
        ]),
        dbc.Row([
                dbc.Col(
                    dcc.Graph(
                        id='county_choro',
                        figure={}
                    )
                ),
                dbc.Col(
                    dcc.Graph(
                        id='county_sunburst',
                        figure={}
                    )
                )
                ]),
        dbc.Row([
            dbc.Col(dbc.Card(dbc.CardBody(
                [
                    html.H3(
                        'Select a state to view scatter plot containing the last four weeks of data on county level', className="card-title"),
                    html.P(
                        '(This can take some time to load the animation visual)', className="card-subtitle")
                ]
            ))
            ),
        ],
            align="center",
        ),
        dcc.Dropdown(id='drop_bar_state2',
                     options=[{'label': x, 'value': x}
                              for x in us_data.Province_State.unique()],
                     value='Alabama',
                     multi=False,
                     ),
        dbc.Row([
            html.H2('Scatter plot of r-rate and average cases per county'),
            html.P('Similar to the scatter plot above, this animation shows the r-rate vs the average daily cases'
                   + ' per county for the selected state. Once again this animation is interactive so you can'
                   + ' select or unselect counties on the right hand margin as well as zoom in.')
        ]),
        dbc.Row([
            dcc.Graph(
                id = 'county_scatter',
                figure = {}
            )
        ])
        ])
])


@app.callback(
    [Output(component_id='time_graph', component_property='figure'),
     Output(component_id='R_rate', component_property='figure'),
     Output(component_id='county_drop_bar', component_property='options')],
    [Input(component_id='drop_bar', component_property='value')]
)
def update_graph(option_State):

    dff = us_data.copy()
    dff = dff[dff['Province_State'] == option_State]
    dff = dff[dff['Confirmed'] >= 1]

    total_c = dff['Confirmed'].iloc[-1]
    total_d = dff['Deaths'].iloc[-1]

    us_barchart = go.Figure(data=[
        go.Bar(name='Cases',
               x=dff['Date'],
               y=dff['Daily Confirmed'],
               marker_color='blue',
               hovertemplate='Cases: %{y}<br><extra></extra>'),
        go.Bar(name='Deaths',
               x=dff['Date'],
               y=dff['Daily Deaths'],
               marker_color='red',
               hovertemplate='Deaths: %{y}<br><extra></extra>')
    ])
    us_barchart.update_layout(title_text=f"{option_State} State<br>Total Cases: {total_c:,d} Total Deaths: {total_d:,d}",
                              barmode='stack')

    us_barchart.add_trace(go.Scatter(x=dff['Date'],
                                     y=dff['7_day_avg'],
                                     mode='lines',
                                     name='7 Day Average',
                                     line=dict(color='rgb(184,55,223)'),
                                     hovertemplate='7 Day Average: %{y}<br><extra></extra>'
                                     )
                          )
    us_barchart.update_layout(
        title={
            'y': .91,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_title="Date",
        yaxis_title="Daily Count",
        hovermode="x",
    )

    r_df = pd.read_csv('Data/R files/' + str(option_State) + '_r.csv')
    r_df['Date'] = pd.to_datetime(r_df['Date'])
    type(r_df['Mean'] - r_df['0.05'])
    type(r_df['Mean'])
    r_rate_use = go.Figure([
        go.Scatter(
            name='R mean',
            x=r_df['Date'],
            y=r_df['Mean'],
            mode='lines',
            line=dict(color='rgb(31, 119, 180)'),
        ),
        go.Scatter(
            name='Upper Bound',
            x=r_df['Date'],
            y=r_df['Mean']+(r_df['0.95'] - r_df['Mean']),
            mode='lines',
            marker=dict(color="#444"),
            line=dict(width=0),
            showlegend=False
        ),
        go.Scatter(
            name='Lower Bound',
            x=r_df['Date'],
            y=r_df['Mean']-(r_df['Mean'] - r_df['0.05']),
            marker=dict(color="#444"),
            line=dict(width=0),
            mode='lines',
            fillcolor='rgba(68, 68, 68, 0.3)',
            fill='tonexty',
            showlegend=False
        )
    ])
    r_rate_use.update_layout(
        yaxis_title='R rate',
        title='Reproduction rate of Covid-19 in '
        + str(option_State)
        + ' State with 95% CI<br>Mean SI = 3.96<br>Standard deviation SI = 4.75',
        hovermode="x"
    )
    df = pd.read_csv('Data/States/'
                     + str(option_State)
                     + '_data.csv')

    county_list = [{'label': i, 'value': i} for i in df.Admin2.unique()]

    return us_barchart, r_rate_use, county_list


@app.callback(
    [Output(component_id='county_cases', component_property='figure'),
     Output(component_id='county_r-rate', component_property='figure')],
    [Input(component_id='county_drop_bar', component_property='value'),
     Input(component_id='drop_bar', component_property='value')])
def set_display_children(county_selected, state_selected):

    cases_data = pd.read_csv('Data/States/'
                             + str(state_selected)
                             + '_data.csv')
    cases_data = cases_data[cases_data['Admin2'] == county_selected]
    cases_data = cases_data[cases_data['Confirmed'] >= 1]
    total_cases = cases_data['Confirmed'].iloc[-1]
    #total_deaths = cases_data['Deaths'].iloc[-1]

    county_barchart = go.Figure(data=[
        go.Bar(name='Cases',
               x=cases_data['Date'],
               y=cases_data['Daily Confirmed'],
               marker_color='blue',
               hovertemplate='Cases: %{y}<br><extra></extra>'),
        # go.Bar(name='Deaths',
        #        x=cases_data['Date'],
        #        y=cases_data['Daily Deaths'],
        #        marker_color='red',
        #        hovertemplate='Deaths: %{y}<br><extra></extra>')
    ])
    county_barchart.update_layout(title_text=f"{county_selected} County<br>Total Cases: {total_cases:,d} "
                                            # + f"Total Deaths: {total_deaths:,d}",
                                  # barmode='stack'
                                  )

    county_barchart.add_trace(go.Scatter(x=cases_data['Date'],
                                         y=cases_data['7_day_avg'],
                                         mode='lines',
                                         name='7 Day Average',
                                         line=dict(color='rgb(184,55,223)'),
                                         hovertemplate='7 Day Average: %{y}<br><extra></extra>'
                                         )
                              )
    county_barchart.update_layout(
        title={
            'y': .91,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top'},
        xaxis_title="Date",
        yaxis_title="Daily Count",
        hovermode="x",
    )

    r_rate_data = pd.read_csv('Data/States/R files/'
                              + str(state_selected)
                              + '/'
                              + str(state_selected)
                              + '_r_'
                              + str(county_selected)
                              + '.csv')
    r_rate_county = go.Figure([
        go.Scatter(
            name='R mean',
            x=r_rate_data['Date'],
            y=r_rate_data['Mean'],
            mode='lines',
            line=dict(color='rgb(31, 119, 180)'),
        ),
        go.Scatter(
            name='Upper Bound',
            x=r_rate_data['Date'],
            y=r_rate_data['Mean']+(r_rate_data['0.95'] - r_rate_data['Mean']),
            mode='lines',
            marker=dict(color="#444"),
            line=dict(width=0),
            showlegend=False
        ),
        go.Scatter(
            name='Lower Bound',
            x=r_rate_data['Date'],
            y=r_rate_data['Mean']-(r_rate_data['Mean'] - r_rate_data['0.05']),
            marker=dict(color="#444"),
            line=dict(width=0),
            mode='lines',
            fillcolor='rgba(68, 68, 68, 0.3)',
            fill='tonexty',
            showlegend=False
        )
    ])
    r_rate_county.update_layout(
        yaxis_title='R rate',
        title='Reproduction rate of Covid-19 in '
        + str(county_selected)
        + ', '
        + str(state_selected)
        + ' with 95% CI<br>Mean SI = 3.96<br>Standard deviation SI = 4.75',
        hovermode="x"
    )

    return county_barchart, r_rate_county


@app.callback(
    [Output(component_id='county_choro', component_property='figure'),
     Output(component_id='county_sunburst', component_property='figure')],
    [Input(component_id='drop_bar_state', component_property='value')]
)
def update_state(state_option):

    with open('geojson-counties-fips.json') as f:
        state_counties = json.load(f)

    weeks_df = pd.read_csv('Data/States/'
                           + str(state_option)
                           + '/' + str(state_option)
                           + '_4_week_data.csv',
                           dtype={'FIPS': str})
    last_date = weeks_df['Date'].iloc[-1]
    weeks_df = weeks_df[weeks_df['Date'] == last_date]
    weeks_df['FIPS'] = weeks_df['FIPS'].str.replace("\.0", "", regex=True)
    weeks_df.dropna(inplace=True)
    if (len(weeks_df['FIPS'].iloc[-1]) == 4):
        weeks_df['FIPS'] = str(0) + weeks_df['FIPS']

    county_choro = px.choropleth(weeks_df, geojson=state_counties, locations='FIPS', color='Mean',
                                 scope="usa",
                                 labels={
                                     'Mean': 'Reproduction Rate <br>mean'},
                                 color_continuous_scale="reds",
                                 hover_name=weeks_df['Admin2'],
                                 range_color=[0, weeks_df['Mean'].max()]
                                 )
    layout = go.Layout(geo=dict(bgcolor='rgba(0,0,0,0)'),
                       title=go.layout.Title(
        text=str(state_option) +
        " Reproduction Rate by County<br>(" + str(recent_date) + ')',
        x=0.5,
        y=0.96
    ),
        font=dict(size=16)
    )

    county_choro.update_layout(layout)

    if (state_option != 'Alaska'):
        county_choro.update_geos(fitbounds="locations",
                                 visible=True,
                                 )

    county_sunburst = px.sunburst(
        weeks_df,
        path=['Province_State', 'Admin2'],
        values='Confirmed',
        branchvalues='total',
        labels={
            'Confirmed': 'Total Cases',
        },
        title="Confirmed Total Cases by county<br>(" + str(recent_date) + ')'
    )
    return county_choro, county_sunburst

@app.callback(
    Output(component_id='county_scatter', component_property='figure'),
    [Input(component_id='drop_bar_state2', component_property='value')]
)
def get_scatter(drop_state):
    scatter_data = pd.read_csv('Data/States/'
                             + str(drop_state)
                             + '/'
                             + str(drop_state)
                             + '_4_week_data.csv')
    low_x = scatter_data['Mean'].min()
    high_x = 3
    low_y = scatter_data['7_day_avg'].min()
    high_y = scatter_data['7_day_avg'].max()

    scatter_data['R_minus'] = scatter_data['Mean'] - scatter_data['0.05']
    scatter_data['R_plus'] = scatter_data['0.95'] - scatter_data['Mean']
    scatter_data['7_day_avg'] = scatter_data['7_day_avg'].round(5)

    date_list = list(scatter_data.Date.unique())
    county = list(scatter_data.Admin2.unique())

    scatter_dict = {
    "data": [],
    "layout": {},
    "frames": []
    }

    scatter_dict["layout"]["xaxis"] = {"range": [
        low_x, high_x], "title": "Reproduction Rate"}
    scatter_dict["layout"]["yaxis"] = {"range": [
        low_y, high_y], "title": "Daily cases 7 day average"}
    scatter_dict["layout"]["width"] = 1000
    scatter_dict["layout"]["height"] = 1000
    scatter_dict["layout"]["hoverlabel"] = dict(bgcolor="white",
                                                font_size=16,
                                                font_family="Rockwell",
                                                )

    scatter_dict["layout"]["hovermode"] = "closest"
    scatter_dict["layout"]["shapes"] = [dict(
        type='line',
        x0=1,
        x1=1,
        y0=low_y-10,
        y1=high_y,
        line=dict(
            color='Black',
            dash='dash'))
    ]
    scatter_dict["layout"]["title"] = {
        'text': str(drop_state) + ' R-rate for each county<br>(Last 30 days)',
                'font_size': 20,
                'y': 0.95,
                'x': 0.5,
                'xanchor': 'center',
                'yanchor': 'top'}

    scatter_dict["layout"]["updatemenus"] = [
        {
            "buttons": [
                {
                    "args": [None, {"frame": {"duration": 500, "redraw": False},
                                    "fromcurrent": True, "transition": {"duration": 300,
                                                                        "easing": "quadratic-in-out"}}],
                    "label": "Play",
                    "method": "animate"
                },
                {
                    "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                    "mode": "immediate",
                                    "transition": {"duration": 0}}],
                    "label": "Pause",
                    "method": "animate"
                }
            ],
            "direction": "left",
            "pad": {"r": 10, "t": 87},
            "showactive": False,
            "type": "buttons",
            "x": 0.1,
            "xanchor": "right",
            "y": 0,
            "yanchor": "top"
        }
    ]

    sliders_dict = {
        "active": 0,
        "yanchor": "top",
        "xanchor": "left",
        "currentvalue": {
            "font": {"size": 20},
            "prefix": "Date:",
            "visible": True,
            "xanchor": "right"
        },
        "transition": {"duration": 300, "easing": "cubic-in-out"},
        "pad": {"b": 10, "t": 50},
        "len": 0.9,
        "x": 0.1,
        "y": 0,
        "steps": []
    }

    # make data
    date = list(scatter_data.Date.unique())[0]

    for County in county:
        dataset_by_date = scatter_data[scatter_data["Date"] == date]
        dataset_by_date_and_cont = dataset_by_date[
            dataset_by_date["Admin2"] == County]

        data_dict = {
            "x": list(dataset_by_date_and_cont["Mean"]),
            "error_x": dict(type='data',
                            symmetric=False,
                            array=dataset_by_date_and_cont['R_plus'],
                            arrayminus=dataset_by_date_and_cont['R_minus'],
                            thickness=0.5,
                            ),
            "y": list(dataset_by_date_and_cont["7_day_avg"]),
            "mode": "markers",
            "hovertemplate": dataset_by_date_and_cont['Admin2'] +
            '<br>R Rate (mean): %{x:.2f}' +
            '<br>7_day_avg: %{y}<br><extra></extra>',
            "text": list(dataset_by_date_and_cont["Admin2"]),
            "name": County
        }
        scatter_dict["data"].append(data_dict)

    # make frames
    for Date in date_list:
        frame = {"data": [], "name": str(Date)}
        for County in county:
            dataset_by_Date = scatter_data[scatter_data["Date"] == Date]
            dataset_by_Date_and_cont = dataset_by_Date[
                dataset_by_Date["Admin2"] == County]

            data_dict = {
                "x": list(dataset_by_Date_and_cont["Mean"]),
                "error_x": dict(type='data',
                                symmetric=False,
                                array=dataset_by_Date_and_cont['R_plus'],
                                arrayminus=dataset_by_Date_and_cont['R_minus'],
                                thickness=0.5,
                                ),
                "y": list(dataset_by_Date_and_cont["7_day_avg"]),
                "mode": "markers",
                "hovertemplate": dataset_by_Date_and_cont['Admin2'] +
                '<br>R Rate (mean): %{x:.2f}' +
                '<br>Daily Cases: %{y}<br><extra></extra>',
                "text": list(dataset_by_Date_and_cont["Admin2"]),
                "name": County
            }
            frame["data"].append(data_dict)

        scatter_dict["frames"].append(frame)
        slider_step = {"args": [
            [Date],
            {"frame": {"duration": 300, "redraw": False},
            "mode": "immediate",
            "transition": {"duration": 300}}
        ],
            "label": Date,
            "method": "animate"}
        sliders_dict["steps"].append(slider_step)


    scatter_dict["layout"]["sliders"] = [sliders_dict]

    scatter_plot = go.Figure(scatter_dict)

    return scatter_plot

if __name__ == '__main__':
    app.run_server(host = '0.0.0.0', port=8080, debug=True)
