import os
import dash
import dash_core_components as dcc
import dash_html_components as html
#import numpy as np
import pandas as pd
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import ctx, dash_table
import plotly.express as px
from dash.exceptions import PreventUpdate
from bs4 import BeautifulSoup
from urllib.request import urlopen
import requests



title_df= pd.read_csv(os.path.join(os.path.dirname(__file__), "title_level_df.csv"))
title_df.averageRating = title_df.averageRating.astype(float,errors = 'ignore').round(1)

title_df.startYear = title_df.startYear.astype(int)

title_start_options =sorted([{"label": name, "value": name} for name in title_df.startYear.unique()], key = lambda x: x['label'])
title_end_options =sorted([{"label": name, "value": name} for name in title_df.startYear.unique()], key = lambda x: x['label'])

title_type_options =sorted([{"label": name, "value": name} for name in title_df.titleType.unique()], key = lambda x: x['label'])

title_df['runtimeMinutes'] = title_df['runtimeMinutes'].astype(float)
def run_time_cate(x):
    if x<20:
        return 'less than 20min'
    elif x<=150:
        return 'between 20 and 150min'
    elif x>150:
        return 'more than 150min'
    else:
        return 'unknown'
title_df['run_time_cate'] = title_df['runtimeMinutes'].apply(run_time_cate)
title_df.run_time_cate = title_df.run_time_cate.astype(object,copy=False)
run_time_options=sorted([{"label": name, "value": name} for name in title_df.run_time_cate.unique()], key = lambda x: x['label'])

genre_columns =['action', 'adult', 'adventure', 'animation',
                                                          'biography',
       'comedy', 'crime', 'documentary', 'drama', 'family', 'fantasy',
       'film-noir', 'game-show', 'history', 'horror', 'music', 'musical',
       'mystery', 'news', 'reality-tv', 'romance', 'sci-fi', 'short', 'sport',
       'talk-show', 'thriller', 'war', 'western']
genre_options=sorted([{"label": name, "value": name} for name in genre_columns], key = lambda x: x['label'])

title_options =sorted([{"label": name, "value": name} for name in title_df[title_df.numVotes>=10000].primaryTitle.unique()], key = lambda x: x['label'])

empty_fig = {
    "layout": {
        "xaxis": {
            "visible": False
        },
        "yaxis": {
            "visible": False
        },
        "annotations": [
            {
                "text": "No matching data found",
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {
                    "size": 28
                }
            }
        ]
    }
}


external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.VAPOR,
    external_stylesheets])

server = app.server
app.config['suppress_callback_exceptions']=True

navbar = dbc.NavbarSimple(
    brand='IMDb Film Data Analysis',
    color='info',
    fluid=True,
    dark=True,
    brand_style={"fontSize": 36}
)

tab_style = {
    'borderTop': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}


app.layout = html.Div([
    navbar,
    html.Br(),
    dbc.Tabs([
        dbc.Tab(label = 'Rating Analytics',tab_id='tab1',
                style=tab_style, activeTabClassName="fw-bold fst-italic",
                children=[
                    html.Div([
                        dbc.Row([
                            dbc.Col([
                                html.P('Year Starts'),
                                dcc.Dropdown(
                                    id='year_start',style={'color': 'black'},
                                    options = title_start_options,
                                    multi=False,
                                    value=title_df.startYear.min()
                                )
                            ], width=1),
                            dbc.Col([
                                html.P('Year Ends'),
                                dcc.Dropdown(
                                    id='year_end', style={'color': 'black'},
                                    options = title_end_options,
                                    multi=False,
                                    value=title_df.startYear.max()
                                ),
                            ], width=1),
                            dbc.Col([
                                html.P('Run Time'),
                                dcc.Dropdown(
                                    id='run-time-dropdown',style={'color': 'black'},
                                    options = run_time_options,
                                    multi=True,
                                    value =['less than 20min','between 20 and 150min']
                                ),
                            ]),
                            dbc.Col([
                                html.P('Genre'),
                                dcc.Dropdown(
                                    id='genre-dropdown',style={'color': 'black'},
                                    options = genre_options,
                                    multi=True,
                                    value=['action','comedy','crime']
                                ),
                            ]),
                            dbc.Col([
                                html.P('Title Type'),
                                dcc.Dropdown(
                                    id='title-type-dropdown',style={'color': 'black'},
                                    options = title_type_options,
                                    multi=True,
                                    value=['short','movie']
                                ),
                            ]),
                        ]),
                        html.Br(),
                        dbc.Row([
                            dbc.Col([
                                html.Div(id='category-container'),
                                html.Br(),
                                dbc.Button("Run Time", id='run-time-button', n_clicks=0, color="info",
                                           n_clicks_timestamp='1',
                                           outline=True,className="me-1"),
                                dbc.Button("Genre", id='genre-button',n_clicks=0, color="primary",
                                           n_clicks_timestamp='0',
                                           outline=True, className="me-1"),
                                dbc.Button("Type", id='type-button',n_clicks=0, color="warning",
                                           n_clicks_timestamp='0',
                                           outline=True, className="me-1"),
                            ], width={"size": 'auto', "offset": 0},),
                            dbc.Col([
                                html.Div(id='top-bottom-container'),
                                html.Br(),
                                dbc.Button("Top 10",id='top10', n_clicks=0,color="success",
                                           n_clicks_timestamp='1', className="me-1"),
                                dbc.Button("Bottom 10",id='bottom10',n_clicks=0, color="danger",
                                           n_clicks_timestamp='0', className="me-1"),
                            ], width={"size": 'auto', "offset": 6},)
                        ], justify="left"),
                    html.Br(),
                    dbc.Row([
                        dbc.Col([
                            dbc.Spinner(
                                html.Div(
                                    dcc.Graph(id='rate-over-time-plot',
                                              style={'width': '95%', 'height': '80vh'}
                                            )
                            ), color="info")
                        ], width=8),
                        dbc.Col([
                            dbc.Spinner(
                                html.Div(
                                    dash_table.DataTable(
                                        id='top-bottom-rate',
                                        export_format='csv',
                                        export_headers='display',
                                        editable=True,
                                        style_table={'display': 'inline-block',
                                                     'display': 'flex'},
                                        style_header={
                                            'backgroundColor': 'rgb(30, 30, 30)',
                                            'color': 'white',
                                            'border': '2px solid pink',
                                            'align': 'center'
                                        },
                                        style_cell={'padding': '5px','fontSize': '18',  'textAlign': 'center'},
                                        style_data={
                                           'backgroundColor': '#190617',
                                            "color": "rgb(255,255,255)",
                                            'whiteSpace': 'normal',
                                            'height': 'auto',
                                            'font-weight': 'normal'
                                        },
                                        style_as_list_view=True,
                                        style_data_conditional=[
                                            {
                                            'if': {
                                                'column_id':'Average Rating',
                                            },
                                            'type':'numeric', 'format': {'specifier': '.1f'}
                                            }
                                        ]
                                    )
                            ), color="info")
                        ], width=4),
                ], justify='left'),

            ])

        ]),
        dbc.Tab(label='Rating Deep Dive',tab_id='tab2',
                style=tab_style, activeTabClassName="fw-bold fst-italic",
                children=[
                    dbc.Row([
                        dbc.Col([
                            # dbc.Card([
                            #     dbc.CardBody([
                                    html.P('Search by Movie Title'),
                                    dcc.Dropdown(
                                        id='title-dropdown',style={'color': 'black'},
                                            options = title_options,
                                            multi=False,
                                            value='Jurassic World'
                                    ),
                            #     ])
                            # ],color="warning", inverse=False, outline=True)
                        ],width=4),
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.Spinner(
                                dbc.CardImg(
                                    id='movie-card-1',
                                    src='https://m.media-amazon.com/images/M/MV5BNzQ3OTY4NjAtNzM5OS00N2ZhLWJlOWUtYzYwZjNmOWRiMzcyXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_.jpg',
                                    top=True,
                                    title='', alt='Oops, no movie poster found!'), color="info"),
                                dbc.Spinner(
                                dbc.CardImg(
                                    id='movie-card-2',
                                    src='https://m.media-amazon.com/images/M/MV5BNzIzOTE0MjUyMF5BMl5BanBnXkFtZTgwODAxMjM5NTE@._V1_.jpg',
                                    bottom=True,
                                    title='', alt='Oops, no movie poster found!'), color="info"),
                            ],
                            color='warning',
                            inverse=True,
                            outline=True,style={"width": "40rem"}
                            ),
                        ], width = 5),
                        dbc.Col([
                            dbc.Card([
                                dbc.Spinner(
                                dbc.CardBody([
                                    html.P(id='deep-dive-avg-score')
                               ]), color="info"),
                            ],color="secondary", inverse=False, outline=True),
                            html.Br(),
                            dbc.Card([
                                dbc.CardBody(
                                    [ dbc.Spinner(
                                        dcc.Graph(id='vote-dist-graph'), color="info"),
                                        html.Br(),
                                        dbc.Spinner(
                                        dcc.Graph(id='age-vote-dist-graph'), color="info"),
                                        html.Br(),
                                    ]),
                            ],
                            color='info',
                            inverse=False,
                            outline=True
                            ),
                        ],width=7),
                    ],className="g-0"),
                    html.Br()
                ]),
    ],active_tab='tab2')
], style={'marginLeft': 40, 'marginRight': 40, 'marginTop': 20, 'marginBottom': 20,
         'padding': '10px'
          }
)

@app.callback(
    Output('category-container', 'children'),
    Input('run-time-button', 'n_clicks_timestamp'),
    Input('genre-button', 'n_clicks_timestamp'),
    Input('type-button', 'n_clicks_timestamp')
)
def displayClick(btn1, btn2,btn3):
    msg = "View By Run Time/Genre/Type"
    if int(btn1) > int(btn2) and int(btn1) > int(btn3):
        msg = "View By Run Time"
    elif int(btn2) > int(btn1) and int(btn2) > int(btn3):
        msg = "View By Genre"
    elif int(btn3) > int(btn1) and int(btn3) > int(btn2):
        msg = "View By Type"
    return html.Div(msg)

@app.callback(
    Output('rate-over-time-plot', 'figure'),
    Input('run-time-button', 'n_clicks_timestamp'),
    Input('genre-button', 'n_clicks_timestamp'),
    Input('type-button', 'n_clicks_timestamp'),
    Input('year_start','value'),
    Input('year_end','value'),
    Input('run-time-dropdown','value'),
    Input('genre-dropdown','value'),
    Input('title-type-dropdown','value')
)
def displayClick(btn1, btn2,btn3,y1,y2,time,genre,type):
    if btn1==0 and btn2==0 and btn3==0:
        raise PreventUpdate
    fig = px.line()
    base_df = title_df[(title_df.startYear >=y1) &(title_df.startYear <=y2)]
    base_df = base_df[base_df.run_time_cate.isin(time)]
    base_df = base_df[base_df.titleType.isin(type)]
    genre_check = pd.DataFrame()
    for i in genre:
        sub_df = base_df[base_df[i] == 1]
        sub_df = sub_df[['tconst', 'averageRating', 'numVotes', 'titleType', 'primaryTitle',
                         'originalTitle', 'isAdult', 'startYear', 'endYear', 'runtimeMinutes',
                         'genres', 'run_time_cate']].copy()
        sub_df['genre_detailed_type'] = i
        genre_check = pd.concat([genre_check, sub_df])
    genre_check_list = genre_check[genre_check.genre_detailed_type.isin(genre)].tconst.unique()
    plot_df = base_df[base_df.tconst.isin(genre_check_list)].copy()
    if int(btn1) > int(btn2) and int(btn1) > int(btn3):
        plot_df = pd.DataFrame(plot_df.groupby(['run_time_cate','startYear'])['averageRating'].mean()).reset_index()
        fig = px.line(plot_df, x='startYear', y='averageRating', color='run_time_cate', markers=True,
                      labels={"run_time_cate": "Run Time","genre_detailed_type": "Genre","titleType": "Type",
                              'startYear':'Year','averageRating':'Average Rating'},
                      color_discrete_sequence=px.colors.qualitative.Set1)
    elif int(btn2) > int(btn1) and int(btn2) > int(btn3):
        plot_df = pd.DataFrame(genre_check.groupby(['genre_detailed_type','startYear'])['averageRating'].mean()).reset_index()
        fig = px.line(plot_df, x='startYear', y='averageRating', color='genre_detailed_type', markers=True,
                      labels={"run_time_cate": "Run Time","genre_detailed_type": "Genre","titleType": "Type",
                              'startYear':'Year','averageRating':'Average Rating'},
                      color_discrete_sequence=px.colors.qualitative.Safe)
    elif int(btn3) > int(btn1) and int(btn3) > int(btn2):
        plot_df = pd.DataFrame(plot_df.groupby(['titleType','startYear'])['averageRating'].mean()).reset_index()
        fig = px.line(plot_df, x='startYear', y='averageRating', color='titleType', markers=True,
                      labels={"run_time_cate": "Run Time","genre_detailed_type": "Genre","titleType": "Type",
                              'startYear':'Year','averageRating':'Average Rating'},
                      color_discrete_sequence=px.colors.qualitative.T10)
    fig.update_layout(
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01,
            xanchor="right",
            x=1
        ),margin=dict(l=20, r=20, t=40, b=20),
        xaxis =  {'showgrid': False},
        yaxis = {'showgrid': False}
    )
    return fig

@app.callback(
    Output('top-bottom-rate', 'data'),
    Output('top-bottom-rate', 'columns'),
    Input('top10', 'n_clicks_timestamp'),
    Input('bottom10', 'n_clicks_timestamp'),
    Input('year_start','value'),
    Input('year_end','value'),
    Input('run-time-dropdown','value'),
    Input('genre-dropdown','value'),
    Input('title-type-dropdown','value')
)
def displayClick(btn1, btn2,y1,y2,time,genre,type):
    if btn1==0 and btn2==0 :
        raise PreventUpdate
    base_df = title_df[(title_df.startYear >=y1) &(title_df.startYear <=y2)]
    base_df = base_df[base_df.run_time_cate.isin(time)]
    base_df = base_df[base_df.titleType.isin(type)]
    base_df = base_df[base_df.numVotes>10000]
    genre_check = pd.DataFrame()
    for i in genre:
        sub_df = base_df[base_df[i] == 1]
        sub_df = sub_df[['tconst', 'averageRating', 'numVotes', 'titleType', 'primaryTitle',
                         'originalTitle', 'isAdult', 'startYear', 'endYear', 'runtimeMinutes',
                         'genres', 'run_time_cate']].copy()
        sub_df['genre_detailed_type'] = i
        genre_check = pd.concat([genre_check, sub_df])
    genre_check_list = genre_check[genre_check.genre_detailed_type.isin(genre)].tconst.unique()
    plot_df = base_df[base_df.tconst.isin(genre_check_list)].copy()
    top_bottom_df = pd.DataFrame()
    if int(btn1)>int(btn2):
        title_list = plot_df.nlargest(10, ['averageRating','numVotes']).tconst.unique()
        top_bottom_df['tconst'] = plot_df[plot_df.tconst.isin(title_list)].tconst
        top_bottom_df['primaryTitle'] = plot_df[plot_df.tconst.isin(title_list)].primaryTitle
        top_bottom_df['numVotes'] = plot_df[plot_df.tconst.isin(title_list)].numVotes
        top_bottom_df['averageRating'] = plot_df[plot_df.tconst.isin(title_list)].averageRating
        top_bottom_df = top_bottom_df.sort_values(by = ["averageRating",'numVotes'],ascending = False)
    else:
        title_list = plot_df.sort_values(by = ["averageRating",'numVotes'],ascending = [True, False]).head(n=10).tconst.unique()
        top_bottom_df['tconst'] = plot_df[plot_df.tconst.isin(title_list)].tconst
        top_bottom_df['primaryTitle'] = plot_df[plot_df.tconst.isin(title_list)].primaryTitle
        top_bottom_df['numVotes'] = plot_df[plot_df.tconst.isin(title_list)].numVotes
        top_bottom_df['averageRating'] = plot_df[plot_df.tconst.isin(title_list)].averageRating.astype(float,errors = 'ignore').round(1)
        top_bottom_df = top_bottom_df.sort_values(by = ["averageRating",'numVotes'],ascending = [True, False])
    top_bottom_df.columns =['ID','Title','Total Votes', 'Average Rating']
    return top_bottom_df.to_dict('records'), [{"name": i, "id": i} for i in top_bottom_df.columns]


@app.callback(
    Output('top-bottom-container', 'children'),
    Input('top10', 'n_clicks'),
    Input('bottom10', 'n_clicks')
)
def displayClick(btn1, btn2):
    if int(btn1)>int(btn2):
        msg = "View By Top 10"
    else:
        msg = "View By Bottom 10"
    return html.Div(msg)

@app.callback(
    Output('vote-dist-graph','figure'),
    Output('age-vote-dist-graph','figure'),
    Output('movie-card-1','src'),
    Output('movie-card-2','src'),
    Output('deep-dive-avg-score','children'),
    Input('title-dropdown','value')
)
def displaygraph(title):
    tt_id = title_df[title_df.primaryTitle == title].tconst.unique()[0]
    rate_link = "https://www.imdb.com/title/" +tt_id+"/ratings/?ref_=tt_ov_rt"
    req = requests.get(rate_link)
    try:
        url_link1 = "https://www.imdb.com/title/" + tt_id + "/mediaviewer/rm2047901184/?ref_=tt_ov_i"
        html_page1 = urlopen(url_link1).read()
        soup1 = BeautifulSoup(html_page1, features='html.parser')
        link1 = soup1.findAll('img')[0].get('src')
        url_link2 = "https://www.imdb.com/title/" + tt_id + "/mediaviewer/rm10105600/?ref_=tt_ov_i"
        html_page2 = urlopen(url_link2).read()
        soup2 = BeautifulSoup(html_page2, features='html.parser')
        link2 = soup2.findAll('img')[1].get('src')

        if req.status_code==200:
            soup = BeautifulSoup(req.text, 'html.parser')
            vote_cnt=[]
            vote_score_cate=[]
            i=1
            while i <=10:
                vote_cnt.append(int(soup.find_all(class_="leftAligned")[i].get_text(separator=" ").replace(',','')))
                vote_score_cate.append(11-i)
                i=i+1
            avg_score = title_df[title_df.primaryTitle == title].averageRating.unique()[0]
            total_cnt = title_df[title_df.primaryTitle == title].numVotes.unique()[0]
            #vote_cnt = [56211, 55379, 139835, 192628, 106486, 45201, 19020, 9341, 5475, 7171]
            #vote_score_cate = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]

            score_dist_df = pd.DataFrame(data={'count': vote_cnt, 'cate': vote_score_cate})
            score_dist_df['count_perc'] = score_dist_df['count'] / sum(score_dist_df['count'])*100
            score_dist_df['count_perc'] = score_dist_df['count_perc'].round(0).astype(str)+'%'
            vote_dis_fig = px.bar(score_dist_df, x="cate", y='count', color='count',
                                  hover_data=['count', 'count_perc'],
                                  labels={
                                      "cate": "Vote Score",
                                      "count": "Vote Count",
                                      "count_perc": "Vote Count %"
                                  },
                                  color_continuous_scale=px.colors.sequential.Purp,
                                  title='Vote Distribution')

            ### vote by age

            age_score=[]
            age_count=[]
            age_cate=['<18','18-29','30-44','45+']
            i=1
            while i <=4:
                try:
                    age_count.append(int(soup.find_all(class_="smallcell")[i].get_text(separator=" ").split('\n')[2].replace(',', '')))
                except ValueError:
                    age_count.append(0)
                i = i+1
            i=1
            while i <=4:
                try:
                    age_score.append(float(soup.find_all(class_="bigcell")[i].get_text(separator=" ")))
                except ValueError:
                    age_score.append(0)
                i = i+1
            age_score_dist_df = pd.DataFrame(data={'count': age_count, 'cate': age_cate,'age_score':age_score})
            age_score_dist_df['count_perc'] = age_score_dist_df['count'] / sum(age_score_dist_df['count']) *100
            age_score_dist_df['count_perc'] = age_score_dist_df['count_perc'].round(0).astype(str) + '%'
            age_vote_dis_fig = px.bar(age_score_dist_df, x="cate", y='age_score', color='count',
                                      text_auto='.1f',
                                      hover_data=['cate','age_score','count', 'count_perc'],
                                    labels={
                                          "cate": "Age",
                                          "count": "Vote Count",
                                          "count_perc": "Vote Count %",
                                          "age_score": "Average Vote Score"
                                      },
                                    color_continuous_scale=px.colors.sequential.amp,
                                    title='Vote Distribution by Age')
            return vote_dis_fig, age_vote_dis_fig, link1, link2,'The average weighted vote score is: {}. The total vote count is {:,}.'.format(avg_score,total_cnt)
        else:
            return empty_fig,empty_fig, html.P('Oops, no movie poster found!'),html.P('Oops, no movie poster found!'), html.P('Opps no movie info found!')
    except:
        return empty_fig,empty_fig, html.P('Oops, no movie poster found!'), html.P('Oops, no movie poster found!'), html.P('Opps no movie info found!')





if __name__ == '__main__':
    app.run_server(debug=True,port=8040)