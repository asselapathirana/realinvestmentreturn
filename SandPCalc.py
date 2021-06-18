# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 09:07:07 2021

@author: assela.pathirana
"""
import logging


import pandas as pd
import numpy as np

from readExchangeRates import get_rate, currencylist

# define Python user-defined exceptions
class DataNotAvailableError(Exception):
    """Base class for other exceptions"""
    pass

spdf = pd.read_csv('./data/s_and_p_500.csv', index_col="Year", 
                   converters={"Value": float})
spdf['endvalue']=np.nan

def inflation_calc(startyear, endyear):
    initial_inf=spdf.loc[startyear]['CPI']
    final_inf = spdf.loc[endyear]['CPI'] 
    factor_to_old_dollars=initial_inf/final_inf
    logging.debug("CPI1 {}, CPI2 {}, factor_to_old_dollars {}".format(initial_inf, final_inf, factor_to_old_dollars))    
    return factor_to_old_dollars

def calc_interest(buy_price, sell_price, buy_year, sell_year):
    grossreturn=(1+(sell_price-buy_price)/buy_price)**(1/(sell_year-buy_year))-1
    return grossreturn

def get_xrate(year, currency):
    return get_rate(currency, year)


def xrate_check(df, year):
    #check for sanity
    # get the months available in df
    months=[x.split("/")[0] for x in list(df['Month'])]
    if not (len(months) and set(df['Month'])==set([ '{}/{}'.format(x,year) for x in months])):
        raise DataNotAvailableError

def calc_ret(myspdf, annual_cost_frac=0, dividend_tax=0.0):
    EVCOL=myspdf.columns.get_loc('endvalue')
    DYPER=myspdf.columns.get_loc('DividendYield_percent')
    iv_=myspdf.iloc[0, myspdf.columns.get_loc('Value')]
    myspdf.iloc[0,EVCOL] = 1./iv_
    for index in range(len(myspdf))[1:]:
        myspdf.iloc[index, EVCOL]=myspdf.iloc[index-1, EVCOL]*(1+myspdf.iloc[index, DYPER]*(1-dividend_tax))*(1-annual_cost_frac)
    return myspdf

def get_property_return(buy_price, sell_price, buy_year, sell_year, 
                        rental_income_frac=0.03, cost_fraction=0.25, selling_cost_fraction=0.05):
    exvalue=0.0
    
    returnonappreciation_nosalescost = calc_interest(buy_price, sell_price, buy_year, sell_year)
    returnonappreciation = calc_interest(buy_price, sell_price*(1-selling_cost_fraction), buy_year, sell_year)
    cv=buy_price
    exvalue=cv*rental_income_frac # first year rent calculated as end of year 
    cv*=(1+returnonappreciation_nosalescost)
    for yy in range(buy_year+1,sell_year):   
        exvalue += cv*rental_income_frac*(1-cost_fraction) # add rent
        exvalue *=(1+returnonappreciation_nosalescost) # bring to next year
        cv *= (1+returnonappreciation_nosalescost) # bring to next year
    print(cv)
    totalreturn=calc_interest(buy_price, sell_price*(1-selling_cost_fraction)+exvalue, buy_year, sell_year)
    return returnonappreciation, totalreturn, exvalue # first return value appreciation, amount from rental income




"""
Calculagtes the final value of an investment with 

returns a list of value (final value, total return percentage, ratio_to_older_dollars = multiplier to calculate older dollars from new dollar value)
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
        ratio_to_older_dollars = inflation_calc(startyear, endyear)
        ret=(ret+1)*(ratio_to_older_dollars)-1
    else:
        ratio_to_older_dollars = 1.0
    logging.debug("inflation calculated as {} for usd. {} for local currency".format(ratio_to_older_dollars, ret))
        
    return fiv, ret, ratio_to_older_dollars


    

def get_xrate_direct(year, currency):
    YEAR=year
    CURR=currency
    ln=f"https://fxtop.com/en/historical-exchange-rates.php?A=1&C1=USD&C2={CURR}&MA=1&DD1=01&MM1=01&YYYY1={YEAR}&B=1&P=&I=1&DD2=31&MM2=12&YYYY2={YEAR}&btnOK=Go%21"
    df = pd.read_html(
        ln, header=0)[-3]
    xrate_check(df, year)
    return df.mean().iloc[0] 



"""Convert local currency to USD, invest it, then convert back at the end of the period"""
def get_return_value_in_local(investment, currency="LKR",  
                  startyear=2001, endyear=2021, 
                  annual_cost_frac=0.0, 
                  adjust_inflation=False, dividend_tax=.0, conversion_cost_frac=.02 ):
    xrate1=get_xrate(startyear,currency)
    usd_value=investment/xrate1*(1-conversion_cost_frac)
    ret=sap500_end_value(usd_value, 
                  startyear, endyear, 
                  annual_cost_frac, 
                  adjust_inflation, dividend_tax)
    usd_end_value=ret[0]
    #total_retun_frac=ret[1]
    ratio_to_older_dollars = ret[2]
    
    xrate2=get_xrate(endyear,currency)
    ratio_to_older_local=ratio_to_older_dollars*xrate1/xrate2
    local_currency_end_value = usd_end_value*1/ratio_to_older_dollars*xrate2*(1-conversion_cost_frac)*ratio_to_older_local
    total_stock_return_rate = calc_interest(investment,local_currency_end_value,startyear,endyear)
    #convert inflation to local currency. 
    
    return local_currency_end_value, total_stock_return_rate, usd_end_value, ratio_to_older_local, xrate1, xrate2, 

"""
returns:
return_only_property_appreciation = Annual return fraction only from property value appreciation
totalreturn_property = total return from property (assuming income is annually invested with the same return as the property appreciation), 
value_from_property_income = 'value' from investing annual income from the property
stock_local_currency_end_value = gross end value in local currency after converting to USD, investing in stocks, sell and change back
stock_annual_rate_in_local_currency = return in terms of local currency as annual fraction
xrate1 = exchange rate at the begining, 
xrate2 = exchange rate at the end. 
"""
def compare_investment(curr, bval, sval, byr, syr, 
                        rental_income_frac=0.03, 
                        rental_cost_fraction=0.25,
                        conversion_cost_frac=0.02,
                        annual_stock_cost_frac=0.0015, 
                        adjust_inflation=True, dividend_tax=0.15, 
                        selling_cost_fraction=0.05,
                        ):
    stock_local_currency_end_value, \
    stock_annual_rate_in_local_currency, \
    stock_usd_end_value, \
    ratio_to_older_local,\
    xrate1, xrate2                       =get_return_value_in_local(bval, 
                                                                    curr, byr, 
                                                                    syr, 
                                                                    annual_stock_cost_frac, 
                                                                    adjust_inflation, 
                                                                    dividend_tax,  
                                                                    conversion_cost_frac)
    
    return_only_property_appreciation, \
        totalreturn_property, \
        value_from_property_income = get_property_return(
            bval, sval, byr, syr, 
            rental_income_frac=rental_income_frac, 
            cost_fraction=rental_cost_fraction, 
            selling_cost_fraction=selling_cost_fraction)
    
    propertyendvalue=value_from_property_income+sval*(1-selling_cost_fraction)
    propertyendvalue_inflation_adjusted=propertyendvalue*ratio_to_older_local
    property_inflation_adjusted_return=(propertyendvalue_inflation_adjusted-bval)/bval
    property_inflation_adjusted_annual_return=(property_inflation_adjusted_return+1)**(1/(syr-byr))-1
    
    logging.debug(f"")
    
    results=f"""
    ## Property Investment
    
    1. Bought in {byr} for {bval} {curr}. (Assume no expenses at buying.)
    2. Sold in {syr} for {sval} {curr}. (An expense of {selling_cost_fraction:.2%} of selling price at selling.)
    
    * In {curr}, property value appreciated annually by {return_only_property_appreciation:0.2%}
    * Considering an annual rental income of {rental_income_frac:0.2%} of the current value of the property, 
    and assuming the costs of maintenance and rental (including possible empty months)
    cost of {rental_cost_fraction:0.0%} of rental income.
    * Rental income invested with same return as the property appreciation rate.
    * The extra investment build-up due to rental income {value_from_property_income:.0f} {curr}. 
    * The total investment build-up upon selling the property {value_from_property_income+sval:.0f} {curr}. ({propertyendvalue:.0f} {curr} after selling cost.)
    * Total 'return on investment' (before "inflation" adjustment) is {totalreturn_property:.2%}
    * The USD.{curr}=x rate in {byr}={xrate1:.2f}, in {syr}={xrate2:.2f}.     
    * The factor to bring {syr} {curr} to {byr} {curr} is x{ratio_to_older_local:0.5f} (See 'small print' for the method)
    * The total return of {propertyendvalue:.0f} {curr} (Before adjusting for "inflation".) 
    * Ajusted for "inflation" (in {byr} LKR) {propertyendvalue_inflation_adjusted:.0f} {curr}. Important Note: See 'small print' below. 
    * Which is a real annual return of {property_inflation_adjusted_annual_return:.2%}.
    
    ## Alternative scenario:
    
    * In {byr}, {bval} {curr} converted to USD (at a cost of {conversion_cost_frac:.2%} and rate USD.{curr}=x of {xrate1:.2f}).
    (= {bval/xrate1*(1-conversion_cost_frac):0.0f} USD.)
    * Then it is invested in a S&P500 index fund with expense ratio of {annual_stock_cost_frac:.2%}
    * As a non-resident alien investment, the dividend is taxed at {dividend_tax:.2%} (assuming a tax-treaty)
    After tax dividend is reinvested.")
    * The gross (not inflation adjusted) value of the portfolio in {syr} will be {stock_usd_end_value:.0f} USD.
    * Which will be (at USD.{curr}=x of {xrate2:.2f}), {stock_usd_end_value*(1-conversion_cost_frac)*xrate2:.0f} {curr}, gross.
    * The 'inflation' adjsuted value is {stock_usd_end_value*(1-conversion_cost_frac)*xrate2*ratio_to_older_local} {curr}.
    * This represents an net annual ("inflation" adjusted) return {curr} of {stock_annual_rate_in_local_currency:.2%}"""  
   
    
    return results, return_only_property_appreciation, totalreturn_property, \
           value_from_property_income, propertyendvalue, \
           propertyendvalue_inflation_adjusted, \
           property_inflation_adjusted_annual_return, stock_local_currency_end_value, \
           stock_annual_rate_in_local_currency, stock_usd_end_value,\
           ratio_to_older_local,\
           xrate1, xrate2       


       
    
    

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    #ret=get_return_value_in_local(1000, "LKR", 2001, 2021, 
    #                                  annual_cost_frac=0.15/100, 
    #                                  dividend_tax=0.15,
    #                                  conversion_cost_frac=.02)    
    #print(ret)
    curr='LKR'
    bval=23000000
    sval=46000000
    byr=2005
    syr=2021
    rental_income_frac=0.03
    rental_cost_fraction=0.25
    annual_stock_cost_frac=0.0015
    dividend_tax=0.15
    conversion_cost_frac=0.02
    selling_cost_fraction=0.05
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
        xrate1, xrate2 = compare_investment(curr, bval, sval, byr, syr, rental_income_frac=rental_income_frac, 
                    rental_cost_fraction=rental_cost_fraction,
                    annual_stock_cost_frac=annual_stock_cost_frac, dividend_tax=dividend_tax, conversion_cost_frac=conversion_cost_frac,
                    selling_cost_fraction=selling_cost_fraction)

    print(results)
    
    #ret=get_property_return(1000,2000,2001,2011,)
    # ret=get_return_value_in_local(1000, "LKR", 2001, 2021, 
    #                               annual_cost_frac=0.15/100, 
    #                               dividend_tax=0.15,
    #                               conversion_cost_frac=.02)
    # print(ret)
    # ev = sap500_end_value(1000, adjust_inflation=False)
    # print("Final value: {}, return on invstment {:.2%}".format(*ev))
    # ev = get_end_value(1000, adjust_inflation=True)
    # print("Final value: {}, return on invstment {:.2%}".format(*ev))
    # ev = get_end_value(1000, adjust_inflation=True, 
    #                    annual_cost_frac=0.25/100)
    # print("Final value: {}, return on invstment {:.2%}".format(*ev))
    # ev = get_end_value(1000, startyear=2001, endyear=2021, 
    #                    adjust_inflation=True, annual_cost_frac=0.25/100, dividend_tax=0.15)
    # print("Final value: {}, return on invstment {:.2%}".format(*ev))
    # ret=get_xrate(2021,'LKR')
    # print(ret)