# Dumb Finance Model

This is not financial advice, it's just a really dumb simulation of money if it was invested at different time point in a certain stock. Nothing in this app constitutes professional and/or financial advice. If you base your decisions off of this reevaluate your financial choices.


## What this actually does
Based on the inputs, this pulls as much data as it can from yahoo finance for the given stock ticker you pick. It then starts simulating an investment for each year available for the duration of the years invested you pick until it runs out of years (e.g. if you pick 40 years, and your stock has data to 1978 it runs a simulation for 1978, 1979, 1980, and 1981). 

In the simulation, for each month it:
1. changes your principle by the amount that stock changed each month `adj_principle=principle*(1+stock_change)`
2. calculates how much your monthly withdrawal amount has changed based on the change in CPI `adj_withdrawal=withdrawal*(1+cpi_change)`
3. calculates how much pretax you need to withdraw to have the withdrawal amount post tax `tax_adj_withdrawal=adj_withdrawal/(1-tax)`
4. subtracts the withdrawal from the new principle `adj_principle-tax_adj_withdrawal`


It keeps running this until you either hit the account minimum you select or it hits the max years. It will increase the principle incrementally until, for a certain withdrawal and a certain start year, you're able to reach the max years.  

The output is a table showing the different principles required across the simulations for a range of monthly withdrawals.

**Note** that this assumes the total principle is in the stock ticker you pick. 


## Frontend Instructions
The frontend for this app is streamlit based. To get the UI, do the following. By default it will run in your browser at http://127.0.0.1:8501.

`streamlit run app.py`