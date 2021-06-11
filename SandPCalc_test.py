import pytest

from SandPCalc import *


def test_no_inflation():
    ret=get_end_value(1000, startyear=2001, endyear=2021, adjust_inflation=False)
    print(ret)
    assert ret == pytest.approx([4160, 315.98/100], rel=.001)
    
def test_with_inflation():
    ret=get_end_value(1000, startyear=2001, endyear=2021, adjust_inflation=True)
    print(ret)
    assert ret == pytest.approx([4159.78, 176.21/100.], rel=.001)

def test_with_inflation_and_cost():
    ret=get_end_value(1000, startyear=2001, endyear=2021, adjust_inflation=True, annual_cost_frac=0.25/100)
    print(ret)
    assert ret == pytest.approx([3956.66, 162.73/100.], rel=.001)
    
def test_with_inflation_cost_and_dividend_tax():
    ret=get_end_value(1000, startyear=2001, endyear=2021, adjust_inflation=True, annual_cost_frac=0.25/100, dividend_tax=0.15)
    print(ret)
    assert ret == pytest.approx([3738.37, 148.23/100.], rel=.001)

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
    with pytest.raises(DataNotAvailableError):
        get_xrate(1881,'LKR') # should fail

 


@pytest.mark.tg
def test_gross_return():
    ret=calc_interest(1000,2000,2001,2011)
    assert ret == pytest.approx(.07177, rel=0.001)
    
@pytest.mark.trent
def test_rental():
    ret=get_property_return(1000,2000,2001,2011, rental_icome_frac=0.03, cost_fraction=0.25)
    assert ret == pytest.approx ((0.07177346253629313, 0.09423560830639643, 460.98197949220827), rel=0.001)
    
@pytest.mark.trent
def test_exchange_and_invest():
    ret = get_return_value_in_local(1000, "LKR", 2001, 2021, 
                                  annual_cost_frac=0.15/100, 
                                  dividend_tax=0.15,
                                  conversion_cost_frac=.02)
    assert ret == pytest.approx ((8008.911933150266, 0.10963124194493212, 89.696771, 196.1156705),rel=0.001)

if __name__=="__main__":
    pytest.main()
    