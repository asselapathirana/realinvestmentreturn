# realinvestmentreturn
Compares the return on a proposed investment with stock market return

## updating
currently exchange rates and s&p500 values are read offline. To update
1. Append s_and_p_500.csv 
2. Run readExchangerates.py (with following comment/uncomment)
    drop_table()
    create_table()
    #dfavg=get_xrate("LKR")
    #writeDB(dfavg)
    get_xrates()
