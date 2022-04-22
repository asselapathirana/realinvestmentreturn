import datetime
import pandas as pd
import sqlite3
import logging


DATABASE = "./data/XRATES.db"
TABLENAME = "xrates"
INDEXTABLEN="countries"
CURR_CN = "curr"
YEAR_CN = "year"
RATE_CN = "rate"
COUNTRY_CN="country"

df = pd.read_csv('./data/currency_codes.csv', encoding="ISO-8859-1")
#remove null rows
currencies=df[pd.to_numeric(df['Number'], errors='coerce').notnull()].copy()
currencies['Number'] = currencies['Number'].astype(float)  
currencies.drop(['Number','Country'],inplace=True, axis=1)
currencylist=dict(currencies.values.tolist())

con = sqlite3.connect(DATABASE)

def get_currencies():
    con2 = sqlite3.connect(DATABASE)
    sql = f"""SELECT {CURR_CN}, {COUNTRY_CN} from {INDEXTABLEN} """
    cur = con2.cursor()
    ans=cur.execute(sql).fetchall()
    return ans   

def get_range(currecy):
    con2 = sqlite3.connect(DATABASE)
    sql = f"""SELECT {YEAR_CN} from {TABLENAME} WHERE {CURR_CN}='{currecy}'"""
    cur = con2.cursor()
    ans=cur.execute(sql).fetchall()
    ans=[x[0] for x in ans]
    return ans

def get_rates(currency, fromy, toyear):
    con2 = sqlite3.connect(DATABASE)
    sql = f"""SELECT {YEAR_CN}, {RATE_CN} from {TABLENAME} WHERE {CURR_CN}='{currency}' AND {YEAR_CN}<{toyear} AND {YEAR_CN} > {fromy}"""
    df = pd.read_sql_query(sql, con2)    
    return df

def get_rate(currecy, year):
    con2 = sqlite3.connect(DATABASE)
    sql = f"""SELECT {RATE_CN} from {TABLENAME} WHERE {CURR_CN}='{currecy}' AND {YEAR_CN}={year}"""
    cur = con2.cursor()
    ans=cur.execute(sql).fetchone()[0]  
    con2.close()
    return ans 

def drop_table():
    sql_drop1 = f""" drop table if exists {TABLENAME};"""
    sql_drop2 = f""" drop table if exists {INDEXTABLEN};"""    
    
    cur = con.cursor()
    cur.execute(sql_drop1)
    cur.execute(sql_drop2)
    con.commit()

    

def create_table():
    sql_create_projects_table1 = f""" CREATE TABLE IF NOT EXISTS {TABLENAME} (
                                        {CURR_CN} text NOT NULL,
                                        {YEAR_CN} INTEGER NOT NULL,
                                        {RATE_CN} REAL NOT NULL,
                                        PRIMARY KEY ({CURR_CN}, {YEAR_CN})
                                        ); """     
    sql_create_projects_table2 = f""" CREATE TABLE IF NOT EXISTS {INDEXTABLEN} (
                                        {CURR_CN} text PRIMARY KEY NOT NULL,
                                        {COUNTRY_CN} text NOT NULL
                                      ); """    
    sql_index=f"CREATE UNIQUE INDEX IF NOT EXISTS index_curr_year ON {TABLENAME}({CURR_CN},{YEAR_CN})"

    cur = con.cursor()
    cur.execute(sql_create_projects_table1)
    cur.execute(sql_create_projects_table2)
    cur.execute(sql_index)
    con.commit()    

def get_xrate(currency):
    
    dt = datetime.datetime.today()    
    YEAR=dt.year
    MONTH=f'{dt.month:02}'
    DATE=f'{dt.day:02}'
    CURR=currency    
    print(f"Getting {CURR} until {YEAR}-{MONTH}-{DATE}")
    if CURR=="USD":
        dfavg=pd.DataFrame(range(1900,YEAR), columns=[YEAR_CN])
        dfavg[CURR_CN]=CURR
        dfavg[RATE_CN]=1.0
        return dfavg
    
    try:
        ln=f"https://fxtop.com/en/historical-exchange-rates.php?A=1&C1=USD&C2={CURR}&TR=1&MA=1&DD1=01&MM1=01&YYYY1=0000&B=1&P=&I=1&DD2={DATE}&MM2={MONTH}&YYYY2={YEAR}&btnOK=Go%21"
        df_ = pd.read_html(
            ln, header=0)[-3]
        #months=[x.split("/")[0] for x in list(df['Month'])]
        avgratename = f'Average USD/{CURR}='
        df = df_[["Month", avgratename]].copy()
        df.rename({avgratename: 'rate'}, axis=1, inplace=True)
        df[['month', 'year']] = df['Month'].str.split('/', 1, expand=True)
        df.drop(['Month'], axis=1, inplace=True )
        dfavg=df.groupby('year', as_index=False)['rate'].mean()
        dfavg['curr']=CURR
    except KeyError as ex:
        logging.error(f"Exception raised in getting exchange rate: {avgratename}\n"+
                      f"{ex}"
                      )
        return pd.DataFrame(columns=["Error"])
        
    return dfavg

def writeDB(df):
    #cur = con.cursor()
    df.to_sql(TABLENAME, con, index=False, dtype={"year":"int"}, if_exists='append')
    con.commit()

    
def writeRec(curr, country):
    sql_insert=f"""insert into {INDEXTABLEN} ({CURR_CN}, {COUNTRY_CN}) values
                                ("{curr}", "{country}");"""
    cur = con.cursor()
    cur.execute(sql_insert)    
    con.commit()

def get_xrates():
    for key in currencylist:
        logging.debug(f"Doing {key}")
        code=currencylist[key]
        df=get_xrate(code)
        if not df.empty:
            writeDB(df)
            writeRec(code,key)
        logging.debug(f"{len(df)} values written")

if __name__=="__main__":
    logging.basicConfig(level=logging.DEBUG)
    drop_table()
    create_table()
    #dfavg=get_xrate("LKR")
    #writeDB(dfavg)
    get_xrates()
    
    print(get_rate("LKR",1985))
    print(get_rate("LKR","2021"))
    print(get_range("LKR"))
    print(get_rate("LKR", str(get_range('LKR')[-1])))
    #print(get_currencies())