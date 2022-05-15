import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.exceptions import PreventUpdate
import requests
import json



app = dash.Dash(__name__, suppress_callback_exceptions=True)


app.layout = dbc.Container([
    html.H1('Test page'),
    dbc.Input(id='name'),
    dbc.Button(id='submit', children='Submit'),
    dcc.Store(id='stored'),
    html.Div(id='output'),
])

@app.callback(Output('stored', 'data'),
              Input('submit', 'n_clicks'),
              State('name', 'value'))
def get_input(n_clicks, zips):
    if n_clicks is None:
        raise PreventUpdate
    else:
        zip = zips.split(',')
        return [zipcode(z) for z in zip]


@app.callback(Output('output', 'children'),
              Input('stored', 'data'))
def printout(namein):

    return [html.P(namein[i]['location']['name']) for i in range(len(namein))]


def zipcode(zip):
    url = "https://weatherapi-com.p.rapidapi.com/current.json"
    querystring = {"q": zip}
    headers = {
        "X-RapidAPI-Host": "weatherapi-com.p.rapidapi.com",
        "X-RapidAPI-Key": "b987c6e289mshcc810c6710e59b5p10b23fjsn53359729f096"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    return response.json()


if __name__ == '__main__':
    app.run_server(port=8886, debug=True)

