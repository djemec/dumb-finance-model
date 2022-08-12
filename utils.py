import pandas as pd
import pandas_datareader as data
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import streamlit as st


start_date = '1928-01-01'
end_date = '2022-08-01'


init_amount = 0
max_amount = 30000000
step = 100000
monthly_step = 1000
dump_data = True
data_source = 'yahoo'
result_df = pd.DataFrame(columns = ['start_date','principal','monthly','months_survive','survive'])

MIN_AMOUNT_TOLERABLE = 100000
INFLATION_ON = True
MAX_YEARS = 40
MONTHLY_MIN = 5000
MONTHLY_MAX = 10000
TAX = 0.2
DEFAULT_MODEL = 'S&P500'
MODELS = {'S&P500':'^GSPC','NASDAQ':'^IXIC','DOW':'^DJI','Tres10y':'^TNX','Coke':'KO','GE':'GE','IBM':'IBM'}
DATA_LOAD_STATE = st.text('')
DEFAULT_LEVERAGE = 1.0

def prep_data(source, inflation, leverage):
    # clear DF
    global result_df
    result_df = pd.DataFrame(columns = ['start_date','principal','monthly','months_survive','survive'])
    
    # setups initial frame with rates and cpi
    
    print('prep started')
    # pull raw data
    stock = data.DataReader(source, data_source, start_date, end_date)[['Close']]
    #pull the earliest stock date available
    new_start = stock.index[0]
    cpi = data.DataReader("CPIAUCNS", "fred", new_start, end_date)
    
    # user merger and then fill in monthly from the previous close if possible else the next close
    df = cpi.merge(stock, how='outer', left_index=True, right_index=True)
    df[['Close']] = df[['Close']].fillna(method='ffill').fillna(method='bfill')

    # remove non first month 
    df.dropna(inplace=True)

    # set placeholders
    df['inflation'] = 0.0
    df['change'] = 0.0
    df.reset_index(inplace=True)

    # calculate baseline df
    for i in range(len(df)):
        # skip the first iteration
        if i == 0: continue
        # update inflation
        if inflation:
            p_cpi = df.at[i-1,'CPIAUCNS']
            c_cpi = df.at[i,'CPIAUCNS']
            df.at[i,'inflation']= (c_cpi - p_cpi)/p_cpi
        # update percent change
        p_close = df.at[i-1,'Close']
        c_close = df.at[i,'Close']
        change = (((c_close - p_close)/p_close)*leverage)
        df.at[i,'change'] = change
    print('prep done')
    return df

def model_year(prin, start_date_index, withdrawal, min_amount_tol, df, tax, years):
    # models a specific year
    
    global result_df
    # calculates the model year and inserts into results df
    # returns boolean for making it to the end of the year
    failed = False
    s_date = df.at[start_date_index,'index'].strftime('%Y_%m_%d')
    mnth = f'monthly_{s_date}_{prin}_{withdrawal}'
    prcp = f'principal_{s_date}_{prin}_{withdrawal}'
    df[mnth] = np.nan
    df[prcp] = np.nan
    k=0
    end = start_date_index + years*12 +1
    start = df.at[start_date_index,'index']
    for i in range(start_date_index,end):
        if k==0:
            df.at[i,mnth]= withdrawal
            df.at[i,prcp]= prin
            k+=1
            continue
        if i > len(df):
            break
        p = i-1
        # previous monthly * (1+inflation)
        p_m = df.at[p,mnth]
        c_i = df.at[i,'inflation']
        c_m = p_m*(1+c_i)
        df.at[i,mnth]= c_m
        # (previous principal*(1+change)) - current monthly
        p_p = df.at[p,prcp]
        change = df.at[i,'change'] 
        c_p = p_p*(1+change)-(c_m/(1-tax))
        df.at[i,prcp]= c_p
        failed = (c_p <= min_amount_tol)
        if failed or i == end-1:
            res = pd.DataFrame.from_dict({'start_date': [start], 
                                          'principal': prin, 
                                          'monthly': withdrawal,
                                          'months_survive': [i-start_date_index], 
                                          'survive': [not failed]})
            result_df = pd.concat([result_df,res], ignore_index=True)
            break
    if dump_data:
        df.drop(columns=[mnth,prcp], inplace=True)
    return failed

def seek_year(sdi, p_min, p_max, step, withdrawal, min_amount_tol, baseline_df, tax, years):
    # interates over a series of principals to find the lowest that makes it to the years amount
    # sdi = start date index 
    # p_min = principal min
    # p_max = principal max
    # step = increase step from in to max
    
    # presumes failed state
    failed = True
    for prin in range(p_min,p_max,step):
        failed = model_year(prin, sdi, withdrawal, min_amount_tol, baseline_df, tax, years)
        # exists when succeeds
        if not failed:
            break

## main function for modeling
def run_model(model = MODELS[DEFAULT_MODEL], years=MAX_YEARS,
              min_amount_tol=MIN_AMOUNT_TOLERABLE, tax=TAX,
              monthly_min=MONTHLY_MIN, monthly_max=MONTHLY_MAX, inflation= INFLATION_ON,
              leverage=DEFAULT_LEVERAGE, dls=DATA_LOAD_STATE):
    # runs the modeling
    model_df = prep_data(model, inflation, leverage)
    lsi = int((len(model_df)- years*12)/12)
    for s in range(lsi + 1):
        s_date_i = s*12
        year = model_df.at[s_date_i,'index'].strftime('%Y_%m_%d')
        mm = monthly_max+monthly_step
        print(f'analyzing year: {year} {s+1} of {lsi + 1}')
        dls.text(f'progress {s+1} of {lsi + 1}')
        for mon in range(monthly_min,mm,monthly_step):
            seek_year(s_date_i, init_amount, max_amount, step, mon, min_amount_tol, model_df,tax, years)
            
def return_survived_df():
    # filters and returns results and the distribution
    survive_df = result_df[result_df.survive]
    survive_df= survive_df.astype({'start_date': object, 
                                   'principal': int, 
                                   'monthly': int, 
                                   'months_survive': int, 
                                   'survive': bool})
    
    sdf_summary = survive_df[['principal','monthly']].groupby('monthly').describe()
    sdf_summary.columns = [i[1] for i in sdf_summary.columns]
    sdf_summary = sdf_summary.drop(columns='count')
    sdf_summary.index = ['${:,}'.format(x) for x in sdf_summary.index]
    for c in sdf_summary.columns:
        sdf_summary[c] = sdf_summary[c].apply(lambda x: '${:,.0f}'.format((x)))
    return survive_df,sdf_summary

def return_all_df():
    # filters and returns results
    all_df = result_df.astype({'start_date': object, 
                                   'principal': int, 
                                   'monthly': int, 
                                   'months_survive': int, 
                                   'survive': bool})
    return all_df

def plot_stats(sdf):
    x_l = 'monthly withdrawal'
    y_l = 'principal'

    unique_monthly = sdf.monthly.unique()
    data =[list(sdf[sdf['monthly'] == i].principal) for i in unique_monthly]
    fig, ax = plt.subplots()

    fig.set_size_inches(10, 6)
    ax.boxplot(data)
    ax.set_xticklabels(['${:,}'.format(x) for x in unique_monthly])
    ax.yaxis.set_major_formatter('${x:,.0f}')
    ax.set_ylabel(y_l)
    ax.set_xlabel(x_l)

    return fig
            
            

if __name__ == '__main__':
    run_model()
    sdf, sdf_stats = return_survived_df()
    inf_text = 'Yes' if INFLATION_ON else 'No'
    title = f'principal needed (inflation {inf_text}, min_bal {min_amount_tolerable}, years {MAX_YEARS}, model {default_model})'
    x_l = 'monthly withdrawal'
    y_l = 'Principal[$]'

    sdf.plot.box(column=['principal'], by=['monthly'], title=title, ylabel=y_l, xlabel=x_l, figsize=(10,5))
    print(sdf_stats)
  