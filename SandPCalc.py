# -*- coding: utf-8 -*-
"""
Created on Thu Jun 10 09:07:07 2021

@author: assela.pathirana
"""
import logging


import pandas as pd
import numpy as np

# define Python user-defined exceptions
class DataNotAvailableError(Exception):
    """Base class for other exceptions"""
    pass

spdf = pd.read_csv('./data/s_and_p_500.csv', index_col="Year", 
                   converters={"Value": np.float})
spdf['endvalue']=np.nan

df = pd.read_csv('./data/currency_codes.csv', encoding="ISO-8859-1")
#remove null rows
currencies=df[pd.to_numeric(df['Number'], errors='coerce').notnull()].copy()
currencies['Number'] = currencies['Number'].astype(float)  
currencies.drop(['Number','Country'],inplace=True, axis=1)
currencylist=dict(currencies.values.tolist())


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


def calc_interest(buy_price, sell_price, buy_year, sell_year):
    grossreturn=(1+(sell_price-buy_price)/buy_price)**(1/(sell_year-buy_year))-1
    return grossreturn
 

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

def inflation_calc(startyear, endyear):
    initial_inf=spdf.loc[startyear]['CPI']
    final_inf = spdf.loc[endyear]['CPI'] 
    factor_to_old_dollars=initial_inf/final_inf
    logging.debug("CPI1 {}, CPI2 {}, factor_to_old_dollars {}".format(initial_inf, final_inf, factor_to_old_dollars))
    

    return factor_to_old_dollars
    

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
    ret=sap500_end_value(usd_value, 
                  startyear, endyear, 
                  annual_cost_frac, 
                  adjust_inflation, dividend_tax)
    usd_end_value=ret[0]
    #total_retun_frac=ret[1]
    ratio_to_older_dollars = ret[2]
    
    xrate2=get_xrate(endyear,currency)
    local_currency_end_value = usd_end_value*xrate2*(1-conversion_cost_frac)
    total_stock_return_rate = calc_interest(investment,local_currency_end_value,startyear,endyear)
    #convert inflation to local currency. 
    ratio_to_older_local=ratio_to_older_dollars*xrate1/xrate2
    return local_currency_end_value, total_stock_return_rate, usd_end_value, ratio_to_older_local, xrate1, xrate2, 

"""
returns:
return_only_property_appreciation = Annual return fraction only from property value appreciation
totalreturn_property = total return from property (assuming income is annually invested with the same return as the property appreciation), 
value_from_property_income = 'value' from investing annual income from the property
stock_local_currency_end_value = end value in local currency after converting to USD, investing in stocks, sell and change back
stock_annual_rate_in_local_currency = return in terms of local currency as annual fraction
xrate1 = exchange rate at the begining, 
xrate2 = exchange rate at the end. 
"""
def compare_investment(currency, buy_price, sell_price, buy_year, sell_year, 
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
    xrate1, xrate2                       =get_return_value_in_local(buy_price, 
                                                                    currency, buy_year, 
                                                                    sell_year, 
                                                                    annual_stock_cost_frac, 
                                                                    adjust_inflation, 
                                                                    dividend_tax,  
                                                                    conversion_cost_frac)
    
    return_only_property_appreciation, \
        totalreturn_property, \
        value_from_property_income = get_property_return(
            buy_price, sell_price, buy_year, sell_year, rental_income_frac=rental_income_frac, cost_fraction=rental_cost_fraction, selling_cost_fraction=selling_cost_fraction)
    
    propertyendvalue=value_from_property_income+sell_price*(1-selling_cost_fraction)
    propertyendvalue_inflation_adjusted=propertyendvalue*ratio_to_older_local
    property_inflation_adjusted_return=(propertyendvalue_inflation_adjusted-buy_price)/buy_price
    property_inflation_adjusted_annual_return=(property_inflation_adjusted_return+1)**(1/(sell_year-buy_year))-1
    return return_only_property_appreciation, totalreturn_property, \
           value_from_property_income, propertyendvalue, \
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
    annual_stock_cost_frac=0.015
    dividend_tax=0.15
    conversion_cost_frac=0.02
    selling_cost_fraction=0.05
    return_only_property_appreciation, totalreturn_property, \
               value_from_property_income, total_property_value, property_inflation_adjusted_annual_return, stock_local_currency_end_value, \
               stock_annual_rate_in_local_currency, stock_usd_end_value,\
               ratio_to_older_local,\
               xrate1, xrate2 = compare_investment(curr, bval, sval, byr, syr, rental_income_frac=rental_income_frac, 
                           rental_cost_fraction=rental_cost_fraction,
                           annual_stock_cost_frac=annual_stock_cost_frac, dividend_tax=dividend_tax, conversion_cost_frac=conversion_cost_frac,
                           selling_cost_fraction=selling_cost_fraction)
    print("Bought in {} for {} {}".format(byr,bval,curr))
    print("Sold in {} for {} {}".format(syr,sval,curr))
    print("No expenses at buying. An expense of {:.2%} of selling price at selling.".format(selling_cost_fraction))
    print("In {} value appreciated annually by {:0.2%}".format(curr, return_only_property_appreciation))
    print("Considering an annual rental income of {:0.2%} of the current value of the property, ".format(rental_income_frac))
    print("and assuming the costs of maintenance and rental (including possible empty months)")
    print("cost of {:0.0%} of rental income, ".format(rental_cost_fraction))
    print("rental income invested with same return as the property appreciation rate, ")
    print("the extra investment build-up due to rental income {:.0f} {}. ".format(value_from_property_income, curr))
    print("The total investment build-up upon selling the property {:.0f} {}.".format(value_from_property_income+sval, curr))
    print("Total 'return on investment' (before inflation adjustment) is {:.2%}".format(totalreturn_property))
    print("The USD.{}=x rate in {}={:.2f}, in {}={:.2f} ".format(curr, byr, xrate1, syr, xrate2))
    print("Inflation figures calculated by:")
    print("1. Converting buying price to USD at year {}".format(byr))
    print("2. factoring the ratio of consumer price indecies x(CPI{})/(CPI{})".format(byr,syr))
    print("3. Converting back to {} at year {}".format(curr, syr))
    print("Using the above method, the factor to bring {} {} to {} {} is x{:0.5f}".format(syr, curr, byr, curr, ratio_to_older_local))
    print("The total return of {:.0f} {} in {} {} = {:.0f} ".format(value_from_property_income+sval, curr, byr, 
                                                                    curr, (value_from_property_income+sval)*ratio_to_older_local))
    print("Which is a real annual return of {:.2%}.".format(property_inflation_adjusted_annual_return))
    print("Alternative scenario:")
    print("In {}, {} {} converted to USD (at a cost of {:.2%} and rate USD.{}=x of {:.2f}).".format(byr,bval,curr, conversion_cost_frac, curr, xrate1))
    print("Then it is invested in a S&P500 index fund with expense ratio of {:.2%}".format(annual_stock_cost_frac))
    print("As a non-resident alien investment, the dividend is taxed at {:.2%} (assuming a tax-treaty)".format(dividend_tax))
    print("After tax divident is reinvested.")
    print("The inflation adjusted value of the portfolio in {} will be {:.0f} USD.".format(syr, stock_usd_end_value))
    print("Which will be (at USD.{}=x of {:.2f}), {:.0f} {}".format(curr, xrate2, stock_usd_end_value*(1-conversion_cost_frac)*xrate2, curr))
    print("This represents an annual (inflation adjusted) rate of retun of {:.2%}".format(stock_annual_rate_in_local_currency))
    
    
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