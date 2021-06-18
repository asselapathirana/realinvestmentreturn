import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from dash_extensions.enrich import MultiplexerTransform, DashProxy
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import readExchangeRates as rer
import SandPCalc as sap
import logging


# ############ Initialize app ############

fontawe='https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css'

app = DashProxy(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, fontawe], transforms=[MultiplexerTransform()])
server = app.server

currencies=[{"label":f"{y} ({x})", "value":y} for x,y in rer.currencylist.items()]

def CustomDropdown(id, options, label, **kwargs):
    return dbc.Card(
        [
        dbc.CardHeader(label),
        dbc.CardBody(      
        [
           dcc.Dropdown(
            id=id,
            options=options,
            clearable=False, 
            **kwargs,
            ),
        ],)
        ],
        
    )

def CustomNumInput(id, value, label,  **kwargs):
    return dbc.Card(
        [
        dbc.CardHeader(label),
        dbc.CardBody(      
        [
           dbc.Input(
            id=id,
            type="number",
            #placeholder="",
            value=value,
            **kwargs,
            ),
        ],)
        ]
    )    

controls = [
    CustomDropdown('curr', currencies, "Currency", value="LKR"),   
    CustomDropdown('byr', [], "Bought in"),  
    CustomNumInput('bval', 100000, "Bought for"),    
    CustomDropdown('syr', [], "Sold in"),   
    CustomNumInput('sval', 200000, "Sold for"),  
    CustomNumInput('scost', 5, "Selling costs(%)"),
    CustomNumInput('rfrac', 3, "Income (% value)"),
    CustomNumInput('rcost', 25, "Costs (% Income)"),
    CustomNumInput('ascf', 0.15, "Stock expense ratio(%)"),
    CustomNumInput('sdt', 15, "Stock dividend tax(%)"),
    CustomNumInput('ccf', 2, "Forex mark-up(%)"),
    #CustomNumInput('divi', 5, "Stock dividend tax(%)"),
]

def card_placeholder(id_,label):
    return dbc.Card(
            [
            dbc.CardHeader(label),
            dbc.CardBody(      
            [
              html.Div(id=id_)
            ],)
            ]    
            )


results=[card_placeholder("left", "The Story"),
         card_placeholder("right", "In Graphics")]
         

advbut=dbc.Button(
            children=html.I(className="far fa-plus-square"),
            id="advanced-button",
            #className="btn-sm",
            size="sm",
            color="Light",
            n_clicks=0,
            #style={'background-color':'transparent'},
        )


headerdiv=dbc.Row([
                dbc.Col(html.Div(
                    children=[html.H1("Property vs Stock Market"),
                              html.H1("Return Calculator")
                              ]
                    ), width='auto'),
                dbc.Col(html.Div(html.Img(id="logo", src=app.get_asset_url("apLogo2.png"))), width=3),
                ], justify='between')


app.layout = dbc.Container([
    dbc.Row(dbc.Col(dbc.CardGroup([dbc.Card(headerdiv)]), width=12), className="m-2"),
    dbc.Row(dbc.Col(dbc.CardGroup(controls[0:1]), width=12), className="m-2") ,   
    dbc.Row(dbc.Col(dbc.CardGroup(controls[1:3]), width=12), className="m-2") ,   
    dbc.Row(dbc.Col(dbc.CardGroup(controls[3:5]), width=12), className="m-2") ,   
    dbc.Row(dbc.Col(advbut, width=1)),
    dbc.Collapse([
        dbc.Row(dbc.Col(dbc.CardGroup(controls[5:]), width=12), className="m-2") ,  
        ], is_open=False, id="advanced",),
    dbc.Row(dbc.Col(dbc.CardGroup(results), width=12), className="m-2")
], )


@app.callback(
    [Output("advanced", "is_open"),
     Output("advanced-button", "children"),
     ],
    [Input("advanced-button", "n_clicks")],
    [State("advanced", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        if is_open: 
            return False, html.I(className="far fa-plus-square")
        else:
            return True, html.I(className="far fa-minus-square")
    return is_open, html.I(className="far fa-plus-square")


@app.callback(
    [Output(component_id='byr', component_property='options'),
     Output(component_id='syr', component_property='options'),
     Output(component_id='byr', component_property='value'),
     Output(component_id='syr', component_property='value'),],    
    [Input(component_id='curr', component_property='value')]
)
def update_output(curr):
    yrs=rer.get_range(curr)
    years=[{"label":y, "value":y} for y in yrs]
    byr=yrs[0] if yrs[0]>2001 else 2001
    syr=yrs[-1]
    return years, years, byr, syr



@app.callback(
    [Output(component_id='left', component_property='children',),
     Output(component_id='right', component_property='children',)],    
    [Input(component_id='curr', component_property='value'),
     Input(component_id='byr',  component_property='value'),   
     Input(component_id='bval', component_property='value'),
     Input(component_id='syr',  component_property='value'),
     Input(component_id='sval', component_property='value'),
     Input(component_id='scost', component_property='value'),
     Input(component_id='rfrac', component_property='value'),
     Input(component_id='rcost', component_property='value'),
     Input(component_id='ascf', component_property='value'),
     Input(component_id='sdt',  component_property='value'),
     Input(component_id='ccf',  component_property='value'),
     #Input(component_id='divi', component_property='value'),
]
)
def update_results(curr, 
byr,  
bval, 
syr,  
sval, 
scost,
rfrac,
rcost,
ascf, 
sdt,  
ccf,  
#divi, 
):
    results, return_only_property_appreciation, \
    totalreturn_property, \
    value_from_property_income,\
    total_property_value, \
    propertyendvalue_inflation_adjusted, \
    property_inflation_adjusted_annual_return, \
    stock_local_currency_end_value, \
    stock_annual_rate_in_local_currency, \
    stock_usd_end_value,\
    ratio_to_older_local,\
    xrate1, xrate2=    sap.compare_investment(curr=curr, 
                           bval=bval, 
                           sval=sval, 
                           byr=byr, syr=syr, 
                           rental_income_frac=rfrac/100., 
                           rental_cost_fraction=rcost/100., 
                           conversion_cost_frac=ccf/100., 
                           annual_stock_cost_frac=ascf/100., 
                           adjust_inflation=True, 
                           dividend_tax=sdt/100., 
                           selling_cost_fraction=scost/100. )
    
    
    colors = ['crimson',] * 2
    colors[1] = 'blue'
    
    
    y=[propertyendvalue_inflation_adjusted, stock_local_currency_end_value*ratio_to_older_local]
    x=['Property', 'Stocks', ]
    fig = go.Figure(data=[go.Bar(
        x=x,
        y=y,
        text=[f"{_:.0f}" for _ in y],
        textposition='inside',        
        marker_color=colors # marker color can be a single color value or an iterable
    )])
    fig.update_layout(title_text='"Inflation Adjusted" End Value',
                      #xaxis_title="",
                      yaxis_title=f"Return ({curr})", font=dict(
            #family="Courier New, monospace",
            size=18, )                     
    )    
    
    y=[property_inflation_adjusted_annual_return*100, stock_annual_rate_in_local_currency*100]
    fig2 = go.Figure(data=[go.Bar(
        x=x,
        y=y,
        text=[f"{_:.3f}" for _ in y],
        textposition='inside',        
        marker_color=colors # marker color can be a single color value or an iterable
    )])
    fig2.update_layout(title_text=f'Rate of Return ({curr})',
                      #xaxis_title="",
                      yaxis_title=f"Annual Return {curr} (%)", font=dict(
            #family="Courier New, monospace",
            size=18, )                     
                      )  
    
      
    # Create subplots: use 'domain' type for Pie subplot
    fig3 = make_subplots(rows=1, cols=2, specs=[[{'type':'domain'}, {'type':'domain'}]])

    fig3.add_trace(go.Pie(labels=['Residual', 'Loss'], values=[ratio_to_older_local, 1-ratio_to_older_local], name=f"{curr}", 
                          textinfo='label+percent'),
                  1, 1)
    usr=ratio_to_older_local*xrate2/xrate1
    fig3.add_trace(go.Pie(labels=['Residual', 'Loss'], values=[usr, 1-usr], name="USD",
                          textinfo='label+percent'),
                  1, 2)
    
    # Use `hole` to create a donut-like pie chart
    fig3.update_traces(hole=.4, hoverinfo="label+percent+name")
    
    fig3.update_layout(
        title_text=f'"Inflation" from {byr} to {syr}',
        # Add annotations in the center of the donut pies.
        annotations=[dict(text=f'{curr}', x=0.18, y=0.5, font_size=20, showarrow=False),
                     dict(text='USD', x=0.82, y=0.5, font_size=20, showarrow=False)],
        margin=go.layout.Margin(
              l=0, #left margin
              r=0, #right margin
              b=0, #bottom margin
              #t=0  #top margin
          ),  
        showlegend=False,
    )
    

    graphs=[dbc.Row(dbc.Card(dcc.Graph(figure=fig))),
            dbc.Row(dbc.Card(dcc.Graph(figure=fig2))),
            dbc.Row(dbc.Card(dcc.Graph(figure=fig3))),
            ]
    
    smallprint=f"""
    ## Small Print
    
    Notice we have used quotation marks with the term inflation ("Inflation"). Here's an explaination. 
    
    The objective of this calculator is to answer the question: "How does an investment in a property in a given country (A), compare to
    a reasonable stock market investment scenario (B)?". 
    "Inflation" figure calculated by:
    
       1. Converting a quantity (X) {curr} to USD at year {byr}
       2. factoring the ratio of consumer price indices  x(CPI{byr})/(CPI{syr})
       3. Converting back to {curr} at year {syr} (Y)
       4. The 'inflation' loss is estimated as 1-(Y/X)
    
    Note we are using the market exchange rate (annual average), as opposed to Purchasing Power Parity (PPP) exchange rate. 
    The implicit assumption here is [Relative Purchasing Power Parity (PPP)](https://en.wikipedia.org/wiki/Relative_purchasing_power_parity),
    an economic theory that indicate a proportionality between long-term exchange rate movement with change in PPP (inflation). 
    Usually this holds well for long-term. (See the [worldbank data ppp converstion factor over market exchange rate.](https://data.worldbank.org/indicator/PA.NUS.PPPC.RF?locations=PK-BD-LK-MV-BT-ID-NP-DE-NI-BR-LU-DK) ) 
    
    See [this for a good explaination](https://saylordotorg.github.io/text_international-economics-theory-and-policy/s20-purchasing-power-parity.html)
    """    
    
    return dcc.Markdown(results+'\n'+smallprint), graphs

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    app.run_server(debug=True)