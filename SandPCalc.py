# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 09:07:07 2021

@author: assela.pathirana
"""

import pandas as pd
import numpy as np

# define Python user-defined exceptions
class DataNotAvailableError(Exception):
    """Base class for other exceptions"""
    pass

spdf = pd.read_csv('./data/s_and_p_500.csv', index_col="Year", 
                   converters={"Value": np.float})

spdf['endvalue']=np.nan
    
    
def calc_ret(myspdf, annual_cost_frac=0, dividend_tax=0.0):
    EVCOL=myspdf.columns.get_loc('endvalue')
    DYPER=myspdf.columns.get_loc('DividendYield_percent')
    iv_=myspdf.iloc[0, myspdf.columns.get_loc('Value')]
    myspdf.iloc[0,EVCOL] = 1./iv_
    for index in range(len(myspdf))[1:]:
        myspdf.iloc[index, EVCOL]=myspdf.iloc[index-1, EVCOL]*(1+myspdf.iloc[index, DYPER]*(1-dividend_tax))*(1-annual_cost_frac)
    return myspdf

def get_property_return(buy_price, sell_price, buy_year, sell_year, 
                        rental_icome_frac=0.03, cost_fraction=0.25):
    exvalue=0.0
    returnonappreciation = calc_interest(buy_price, sell_price, buy_year, sell_year)
    
    cv=buy_price
    exvalue=cv*rental_icome_frac # first year rent calculated as end of year 
    cv*=(1+returnonappreciation)
    for yy in range(buy_year+1,sell_year):   
        exvalue += cv*rental_icome_frac*(1-cost_fraction) # add rent
        exvalue *=(1+returnonappreciation) # bring to next year
        cv *= (1+returnonappreciation) # bring to next year
    print(cv)
    totalreturn=calc_interest(buy_price, sell_price+exvalue, buy_year, sell_year)
    return returnonappreciation, totalreturn, exvalue # first retern value appreciation, amount from rental income


def calc_interest(buy_price, sell_price, buy_year, sell_year):
    grossreturn=(1+(sell_price-buy_price)/buy_price)**(1/(sell_year-buy_year))-1
    return grossreturn
 

"""
Calculagtes the final value of an investment with 

returns a list of value (final value, total return percentage)
"""
def sap500_end_value(investment, 
                  startyear=2001, endyear=2021, 
                  annual_cost_frac=0.0, 
                  adjust_inflation=False, dividend_tax=.0 ):
    
    myspdf=spdf
    myspdf=calc_ret(myspdf, annual_cost_frac=annual_cost_frac, dividend_tax=dividend_tax)
    final_n=myspdf.loc[endyear]['endvalue']
    initial_n=myspdf.loc[startyear]['endvalue']
    initial_v=myspdf.loc[startyear]['Value']
    final_v=myspdf.loc[endyear]['Value']

    
    fiv=(final_n*final_v)/(initial_n*initial_v)*investment
    ret=(fiv-investment)/investment
    
    if adjust_inflation:
        inf = inflation_calc(startyear, endyear)
        ret=(ret+1)/(inf+1)-1
        
    return fiv, ret

def inflation_calc(startyear, endyear):
    initial_inf=spdf.loc[startyear]['CPI']
    final_inf = spdf.loc[endyear]['CPI']        
    inf=(final_inf-initial_inf)/initial_inf
    return inf
    

def get_xrate(year, currency):
    YEAR=year
    CURR=currency
    ln=f"https://fxtop.com/en/historical-exchange-rates.php?A=1&C1=USD&C2={CURR}&MA=1&DD1=01&MM1=01&YYYY1={YEAR}&B=1&P=&I=1&DD2=31&MM2=12&YYYY2={YEAR}&btnOK=Go%21"
    df = pd.read_html(
        ln, header=0)[-3]
    xrate_check(df, year)
    return df.mean().iloc[0] 

def xrate_check(df, year):
    #check for sanity
    # get the months available in df
    months=[x.split("/")[0] for x in list(df['Month'])]
    if not (len(months) and set(df['Month'])==set([ '{}/{}'.format(x,year) for x in months])):
        raise DataNotAvailableError

"""Convert local currency to USD, invest it, then convert back at the end of the period"""
def get_return_value_in_local(investment, currency="LKR",  
                  startyear=2001, endyear=2021, 
                  annual_cost_frac=0.0, 
                  adjust_inflation=False, dividend_tax=.0, conversion_cost_frac=.02 ):
    xrate1=get_xrate(startyear,currency)
    usd_value=investment/xrate1*(1-conversion_cost_frac)
    usd_end_value=sap500_end_value(usd_value, 
                  startyear, endyear, 
                  annual_cost_frac, 
                  adjust_inflation, dividend_tax)[0]
    xrate2=get_xrate(endyear,currency)
    local_currency_end_value = usd_end_value*xrate2*(1-conversion_cost_frac)
    rate = calc_interest(investment,local_currency_end_value,startyear,endyear)
    return local_currency_end_value, rate, xrate1, xrate2
    

if __name__ == "__main__":
    #ret=get_property_return(1000,2000,2001,2011,)
    # ret=get_return_value_in_local(1000, "LKR", 2001, 2021, 
    #                               annual_cost_frac=0.15/100, 
    #                               dividend_tax=0.15,
    #                               conversion_cost_frac=.02)
    # print(ret)
    ev = sap500_end_value(1000, adjust_inflation=False)
    print("Final value: {}, return on invstment {:.2%}".format(*ev))
    # ev = get_end_value(1000, adjust_inflation=True)
    # print("Final value: {}, return on invstment {:.2%}".format(*ev))
    # ev = get_end_value(1000, adjust_inflation=True, 
    #                    annual_cost_frac=0.25/100)
    # print("Final value: {}, return on invstment {:.2%}".format(*ev))
    # ev = get_end_value(1000, startyear=2001, endyear=2021, 
    #                    adjust_inflation=True, annual_cost_frac=0.25/100, dividend_tax=0.15)
    # print("Final value: {}, return on invstment {:.2%}".format(*ev))
    ret=get_xrate(2021,'LKR')
    print(ret)