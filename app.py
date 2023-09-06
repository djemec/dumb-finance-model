import streamlit as st
import matplotlib.pyplot as plt
import altair


from utils import run_model, return_survived_df, plot_stats
from utils import MAX_YEARS, MIN_AMOUNT_TOLERABLE, INFLATION_ON, MONTHLY_MIN, MONTHLY_MAX,TAX,MODELS,DEFAULT_MODEL,DEFAULT_LEVERAGE


st.title('Dumb Finance Model 🤑💰')
st.markdown('Runs a model of investing your principal in the stock you pick with the withdrawal you select. Please keep all financial values in increments of 1000\'s for best results.')
st.markdown('_Nothing in this app constitutes professional and/or financial advice._')

# prompt box
col1, col2, col3 = st.columns(3)
with col1:
    stock = st.selectbox('Which Stock do you want to model', list(MODELS.keys()), index=0)
    leverage = st.number_input('How much leverage on the stock', min_value=0.1, max_value=10.0, value=DEFAULT_LEVERAGE)
    years = st.number_input('Years you want to live off the money', min_value=5, max_value=60, value=MAX_YEARS)

with col2:
    min_tol = st.number_input('Minimum tolerable amount in bank$', min_value=0, max_value=10000000, 
                          value=MIN_AMOUNT_TOLERABLE)
    tax_rate = st.number_input('Tax Rate %', min_value=0, max_value=100, value=int(TAX*100))
    
with col3:
    month_min = st.number_input('Minimum monthly withdrawal $', min_value=0, max_value=20000, value=MONTHLY_MIN)
    month_max = st.number_input('Maximum monthly withdrawal $', min_value=month_min, max_value=20000, value=MONTHLY_MAX)
    inflation = st.checkbox('Include inflation', value=INFLATION_ON)

#button and results
if st.button('Click to run'):
    text = 'Running Model...'
    data_load_state = st.text('Running Model...')
    run_model(MODELS[stock], years,min_tol, tax_rate/100.0, month_min, month_max, inflation, leverage, data_load_state)
    sdf, sdf_stats = return_survived_df()
    data_load_state.empty()
    
    # show summary chart
    st.subheader('Principal needed to support different monthly withdrawals')
    inflation = 'ON' if inflation else 'OFF'
    desc = f'Principal needed to support monthly withdrawals from {month_min} to {month_max} \
            for {years} years at a long term capital gains tax of {tax_rate}, with inflation {inflation} while \
            maintaining a min bank balance of {min_tol}. This assumes the principal is fully invested \
            in {stock} with {leverage}x leverage.'
    st.markdown(desc)

# commenting out tabs since it requires v1.11 which isnt supported in HF
#    tab1, tab2 = st.tabs(['Chart','Table'])

#    with tab1:
        
    fig = plot_stats(sdf)
    st.pyplot(fig)

#    with tab2:
    st.table(data=sdf_stats)
