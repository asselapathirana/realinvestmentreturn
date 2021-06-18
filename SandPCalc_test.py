import pytest

from SandPCalc import *

def test_currency_list():
    assert currencylist['Afghani']  == 'AFN'
    assert currencylist['Sri Lanka Rupee']  == 'LKR'
    assert currencylist['CFA Franc BCEAO']  == 'XOF'
    assert currencylist['US Dollar'] == 'USD'

def test_no_inflation():
    ret=sap500_end_value(1000, startyear=2001, endyear=2021, adjust_inflation=False)
    print(ret)
    assert ret == pytest.approx([4160, 315.98/100, 1.0], rel=.001)
    
def test_with_inflation():
    ret=sap500_end_value(1000, startyear=2001, endyear=2021, adjust_inflation=True)
    print(ret)
    assert ret == pytest.approx([4159.78, 176.21/100., 0.664], rel=.001)

def test_with_inflation_and_cost():
    ret=sap500_end_value(1000, startyear=2001, endyear=2021, adjust_inflation=True, annual_cost_frac=0.25/100)
    print(ret)
    assert ret == pytest.approx([3956.66, 162.73/100, 0.664], rel=.001)
    
def test_with_inflation_cost_and_dividend_tax():
    ret=sap500_end_value(1000, startyear=2001, endyear=2021, adjust_inflation=True, annual_cost_frac=0.25/100, dividend_tax=0.15)
    print(ret)
    assert ret == pytest.approx([3738.37, 148.23/100., 0.664], rel=.001)

@pytest.mark.xrate 
def test_get_xrate():
    ret=get_xrate(2005,'LKR')
    assert ret == pytest.approx(100.44, rel=0.001)

@pytest.mark.xrate  
def test_get_xrate2():
    ret=get_xrate(1969,'LKR')
    assert ret == pytest.approx(5.95, rel=0.001)
    
@pytest.mark.xrate  
def test_get_xrate_fail():
    with pytest.raises(Exception):
        get_xrate(1881,'LKR') # should fail

@pytest.mark.tg
def test_gross_return():
    ret=calc_interest(1000,2000,2001,2011)
    assert ret == pytest.approx(.07177, rel=0.001)
    
@pytest.mark.trent
def test_rental():
    ret=get_property_return(1000,2000,2001,2011, rental_income_frac=0.03, cost_fraction=0.25)
    assert ret == pytest.approx ((0.06629, 0.08970, 460.9819), rel=0.001)
    
@pytest.mark.trent
def test_exchange_and_invest():
    ret = get_return_value_in_local(1000, "LKR", 2001, 2021, 
                                  annual_cost_frac=0.15/100, 
                                  adjust_inflation=True,
                                  dividend_tax=0.15,
                                  conversion_cost_frac=.02)
    assert ret == pytest.approx ((3663.009, 0.06706, 41.6711, 0.303699, 89.696, 196.114),rel=0.001)
    
    ret = get_return_value_in_local(1000, "LKR", 2001, 2021, 
                                  annual_cost_frac=0.15/100, 
                                  adjust_inflation=False,
                                  dividend_tax=0.15,
                                  conversion_cost_frac=.02)
    assert ret[3] == pytest.approx (0.457366,rel=0.001)    
    # adjust_inflation=False will cause USD inflation to be zero. Then we get only 
    # the devaluation of the local currency compared to USD. 
    
@pytest.mark.integrated
def test_compare_investment():
    results, \
    return_only_property_appreciation, totalreturn_property, \
               value_from_property_income, propertyendvalue, \
               propertyendvalue_inflation_adjusted, \
               property_inflation_adjusted_annual_return, stock_local_currency_end_value, \
               stock_annual_rate_in_local_currency, stock_usd_end_value,\
               ratio_to_older_local,\
               xrate1, xrate2 = compare_investment('LKR', 23000000, 50000000, 2005, 2021, rental_income_frac=0.03, 
                           rental_cost_fraction=0.25,
                           annual_stock_cost_frac=0.015, dividend_tax=0.15, selling_cost_fraction=0.05 ) 
    assert return_only_property_appreciation == pytest.approx(0.04637, rel=0.001)
    assert totalreturn_property == pytest.approx(0.067905, rel=0.001)
    assert value_from_property_income == pytest.approx(18303938, rel=0.001)
    assert property_inflation_adjusted_annual_return == pytest.approx(0.003629, rel=0.001)
    assert stock_local_currency_end_value == pytest.approx(142105732., rel=0.001)
    assert stock_annual_rate_in_local_currency == pytest.approx(0.074653, rel=0.001)
    assert stock_usd_end_value == pytest.approx(739394, rel=0.001)
    assert ratio_to_older_local == pytest.approx(0.37038, rel=0.001)
    assert xrate1 == pytest.approx(100.44, rel=0.001)
    assert xrate2 == pytest.approx(196.11, rel=0.001)
    assert propertyendvalue == pytest.approx(65803938, rel=0.001)
    assert len(results) > 1000
    

if __name__=="__main__":
    #pytest.main()
    test_with_inflation()
    test_with_inflation_and_cost()
    test_with_inflation_cost_and_dividend_tax()
    test_exchange_and_invest()
    print("Done")