import dash
import pandas as pd
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dcc, html, dash_table
from dash.exceptions import PreventUpdate
import requests
import random
import regex as re
import spacy
from collections import defaultdict

food = pd.read_csv("food.csv")[['fdc_id', 'data_type', 'description', 'food_category_id']]
index = pd.read_csv("nutrient_index.csv")
nutrients = pd.read_csv("food_nutrient.csv")[['fdc_id', 'nutrient_id', 'amount']]
category = pd.read_csv("food_category.csv")[['id', 'description']]
ingredients = nutrients.join(food.set_index('fdc_id'), on='fdc_id').join(index.set_index('id'), on='nutrient_id').join(category.set_index('id'), on='food_category_id', lsuffix='_food', rsuffix='_category')
ing_valid = ingredients.groupby('component').size().sort_values()
select_from_ing = list(ing_valid[ing_valid.values > 100].index)
nlp = spacy.load("en_core_web_sm")

app = dash.Dash(__name__, suppress_callback_exceptions=True)

app.layout = dbc.Container([
    html.Div(
        children=[
            html.Img(
                src="/assets/logo.jpg",
                style={
                    "width" : "800px",
                    "height" : "166px",
                 }
            ),
        ],
    ),

    html.Br(),
    html.H2(''),
    html.Hr(),
    html.H2("What do you desire today?"),

    dcc.Input(
        id="food",
        type='text',
    ),
    html.Br(),
    html.Hr(),
    html.H2('Nutrition assistant'),
    dcc.Dropdown(id='components', options=sorted(select_from_ing), multi=False),
    dbc.Button(
        children="Search Ingredients",
        id="searchIngredients",
        color="secondary",
        style={
            "width": "200px%",
            "height": "50px",
            "lineHeight": "6px",
            "borderWidth": "1px",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "40px",
        },
    ),
    html.Div(id='suggestedIngreds'),
    html.Br(),
    html.H2('Select your criteria here:'),
    html.Div('Cuisine:'),
    dcc.Dropdown(
        id='cuisine',
        options=['african', 'chinese', 'japanese',
                 'korean', 'vietnamese', 'thai', 'indian',
                 'british', 'irish', 'french', 'italian', 'mexican',
                 'spanish', 'middle eastern', 'jewish', 'american', 'cajun',
                 'southern', 'greek', 'german', 'nordic', 'eastern european', 'caribbean', 'latin american'],
        multi=True,
    ),
    html.Div('Diet:'),
    dcc.Dropdown(
        id='diet',
        options=['Vegetarian', 'Vegan'],
        value='None',
    ),
    html.Div("Ingredients to include:"),
    dcc.Input(
        id="ingredients_include",
        type='text',
    ),
    html.Div("Ingredients to exclude:"),
    dcc.Input(
        id="ingredients_exclude",
        type='text',
    ),
    html.Div('Total calories:'),
    dcc.Input(
        id="calorie",
        type='text',
    ),
    html.Div('Total price:'),
    dcc.Input(
        id="price",
        type='text',
    ),
    html.Br(),
    dbc.Button(
        children="Submit",
        id="submit",
        color="secondary",
        style={
            "width": "100px%",
            "height": "50px",
            "lineHeight": "6px",
            "borderWidth": "1px",
            "borderRadius": "5px",
            "textAlign": "center",
            "margin": "40px",
        },
    ),
    html.Hr(),
    html.Div(id='results'),
    html.Div(id='showDetails'),
    dcc.Store(id='AllRecords'),
    dcc.Store(id='selected_recipe'),
    #dcc.Store(id='SelectedRecords'),

])

@app.callback(
    Output('suggestedIngreds', 'children'),
    Input('searchIngredients', 'n_clicks'),
    State('components', 'value')
)
def search_ingred(n_click, components):
    expanded_list = []
    if n_click is None:
        raise PreventUpdate
    else:
        max_amount = max(ingredients[ingredients['component'] == components]['amount'])
        selected_ingredients = ingredients[(ingredients['component'] == components) & (
                    ingredients['amount'] > max_amount / 4)].sort_values('amount', ascending=False)

        for item in selected_ingredients['description_food'].unique():
            expanded_list.extend(re.split(';|,', item))

        ing_list = list(set([i.strip().lower() for i in expanded_list if
                        (not re.findall('[0-9"/\?><)\*\(\!\@#$\-%^&*]', i) and len(i.strip()) > 2 and nlp(i.strip())[0].pos_ == 'NOUN')]))
        ing_means = []
        ing_stds = []
        for ing in ing_list:
            ing_ds = ingredients[(ingredients['component'] == components) & (
                ingredients['description_food'].apply(lambda x: ing.lower() in str(x).lower()))].sort_values('amount',
                                                                                                        ascending=False)['amount']
            ing_means.append(ing_ds.mean())
            ing_stds.append(ing_ds.std())
        ings_df = pd.DataFrame({'ingredient' : ing_list,
                      'mean' : ing_means,
                      'stdev' : ing_stds}).sort_values('mean', ascending=False)





        return html.Div([
            dash_table.DataTable(
                id='ing_datatable',
                data=ings_df.to_dict('records'),
                columns=[{"name":"Suggested ingredient", "id":"ingredient"},
                         {"name":"Mean", "id":"mean"},
                         {"name":"standard deviation", "id":"stdev"}],
                row_selectable='multi',
                selected_rows=[],
            ),
            dbc.Button(
                children="Add to Ingredients",
                id="addToIngredients",
                color="secondary",
                style={
                    "width": "300px%",
                    "height": "50px",
                    "lineHeight": "6px",
                    "borderWidth": "1px",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "40px",
                },
            ),
            dbc.Button(
                children="Exclude Ingredients",
                id="excludeIngredients",
                color="secondary",
                style={
                    "width": "300px%",
                    "height": "50px",
                    "lineHeight": "6px",
                    "borderWidth": "1px",
                    "borderRadius": "5px",
                    "textAlign": "center",
                    "margin": "40px",
                },
            ),







        ])

@app.callback(
    Output('ingredients_include', 'value'),
    Input('addToIngredients', 'n_clicks'),
    State('ing_datatable', 'selected_rows'),
    State('ing_datatable', 'data'),
    prevent_initial_call=True,
)
def selectIngredient(n_click, ing, data):
    if n_click is None:
        raise PreventUpdate
    else:
        return ','.join([data[i]['ingredient'] for i in ing])

@app.callback(
    Output('ingredients_exclude', 'value'),
    Input('excludeIngredients', 'n_clicks'),
    State('ing_datatable', 'selected_rows'),
    State('ing_datatable', 'data'),
    prevent_initial_call=True,
)
def selectIngredient(n_click, ing, data):
    if n_click is None:
        raise PreventUpdate
    else:
        return ','.join([data[i]['ingredient'] for i in ing])



@app.callback(Output('AllRecords', 'data'),
              Input('submit', 'n_clicks'),
              [State('food', 'value'), State('ingredients_include', 'value'), State('ingredients_exclude', 'value'), State('diet', 'value'), State('cuisine', 'value'), State('calorie', 'value')])
def searchRecipe(n_click, food, ingredients_include, ingredients_exclude, diet, cuisine, calorie):
    if n_click is None:
        raise PreventUpdate
    else:
        return get_recipe(food, ingredients_include, ingredients_exclude, diet, cuisine, calorie)

@app.callback(Output('results', 'children'),
              Input('AllRecords', 'data'))
def RandomSelection(data):
    SelectedRecords = titleSelection(data, min(10, len(data)))
    titles = []
    ids = []

    for record in SelectedRecords:
        titles.append(record['title'])
        ids.append(record['id'])

    return html.Div([
        html.Img(
            src="/assets/pans.jpg",
            style={
                "width": "1300px",
            }
        ),
        html.H2('The following recipes match your criteria'),

        dash_table.DataTable(
            id='titles_datatable',
            data=pd.DataFrame({'title':titles, 'id':ids}).to_dict('records'),
            columns=[{"name": "Recipe Title", "id": "title"}],
            row_selectable='single',
            selected_rows=[],
        ),
        dbc.Button(
            children="select Recipe",
            id="selectRecipe",
            color="secondary",
            style={
                "width": "300px%",
                "height": "50px",
                "lineHeight": "6px",
                "borderWidth": "1px",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "40px",
            },
        ),
    ])


@app.callback(Output('selected_recipe', 'data'),
              Input('selectRecipe', 'n_clicks'),
              State('titles_datatable', 'selected_rows'),
              State('titles_datatable', 'data'),
)
def select_Recipe(n_click, row, data):
    if n_click is None:
        print('no click')
        raise PreventUpdate
    else:
        print('recipe is selected')
        print(data[row[0]]['id'])
        return get_recipe_info(data[row[0]]['id'])


@app.callback(Output('showDetails', 'children'),
              Input('selected_recipe', 'data'))
def show_recipe_details(data):
    Ingredients = [item['name'] for item in data['extendedIngredients']]
    amounts = [item['amount'] for item in data['extendedIngredients']]
    units = [item['unit'] for item in data['extendedIngredients']]
    Ing_table = pd.DataFrame({'Item':Ingredients, 'Amount':amounts, 'Unit':units})
    preparationTime = data['readyInMinutes']
    servings = data['servings']
    Instructions = data['instructions']
    ImageURL = data['image']
    Title = data['title']
    print(Ing_table)
    output = html.Div([
        html.Br(),
        html.H2(Title),
        html.Img(
            src=ImageURL,
            style={
                "width": "600px",
            }
        ),
        html.H4('Total preparation time:'),
        html.P(str(preparationTime) + " minutes"),
        html.Br(),
        html.H4('Instructions:'),
        html.P(Instructions),
        html.H4('Ingredients'),
        dash_table.DataTable(
            id='recipeIngredients',
            data=Ing_table.to_dict('records'),
            columns=[{"name": "Item", "id": "Item"},
                     {"name": "Amount", "id": "Amount"},
                     {"name": "Unit", "id": "Unit"}],
        ),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),

    ])



    return output









def get_recipe_info(number):
    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/" + str(number) + "/information"
    querystring = {"includeNutrition": "true"}
    headers = {
        "X-RapidAPI-Host": "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com",
        "X-RapidAPI-Key": "b987c6e289mshcc810c6710e59b5p10b23fjsn53359729f096"
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    return response.json()




def get_recipe(food, ingredients_include, ingredients_exclude, diet, cuisine, calorie):
    url = "https://spoonacular-recipe-food-nutrition-v1.p.rapidapi.com/recipes/complexSearch"
    headers = {
        "X-RapidAPI-Host": "spoonacular-recipe-food-nutrition-v1.p.rapidapi.com",
        "X-RapidAPI-Key": "b987c6e289mshcc810c6710e59b5p10b23fjsn53359729f096"
    }
    querystring = {
        "query": food,
        "offset":"0",
        "number":"100",
        "excludeIngredients":ingredients_exclude,
        "includeIngredients":ingredients_include,
        "diet":diet,
        "cuisine":cuisine,
        "maxCalories":calorie,
    }
    response = requests.request("GET", url, headers=headers, params=querystring)
    totalResults = response.json()['totalResults']
    offsets = random.sample(list(range(1, 1 + totalResults // 100)), min(2, totalResults // 100))
    AllRecords = response.json()['results']
    for o in offsets:
        querystring["offset"] = str(o)
        response = requests.request("GET", url, headers=headers, params=querystring)
        AllRecords.extend(response.json()['results'])


    return AllRecords

def titleSelection(titleList, n):
    return random.sample(titleList, n)

def cost(record):
    url = "https://api.kroger.com/v1/connect/oauth2/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": "Basic c21hcnRjaGVmLWIzNzk0ZWU4YzI1MDFmYTRlMGEwMmFmN2JhMjhjM2U5ODcyMzMzNTE5NzEyNzU3NDYwMTo0aHFkZ2ZwS1FDaXYtOUZtdlc2R2FCTVlxT2xobDRmS2tETkNvV1Fn"
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "product.compact"
    }
    response = requests.request("POST", url, headers=headers, data=data)
    token = response.json()['access_token']
    url = 'https://api.kroger.com/v1/products'
    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + token,
    }


    ingredientList = record['extendedIngredients']
    for item in ingredientList:
        item['name']
        item['measures']['metric']['amount']
        item['measures']['metric']['unitShort']





    querystring = {
        'filter.term': 'apple',
        'filter.locationId': '02900210'
    }



    response = requests.request("GET", url, headers=headers, params=querystring)




if __name__ == '__main__':
    app.run_server(port=8885, debug=True)

