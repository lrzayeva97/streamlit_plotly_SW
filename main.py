import plotly.express as px
import pandas as pd
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

# Load data for loans and verifications
df = pd.read_csv('risk_dumps/historical_loans_PL.csv')
df = df[df['which_month'] == 'current_month']
df['created_date'] = pd.to_datetime(df['created_datetime_dubai']).dt.day

df['net_loss_new'] = np.where(
    (~df['first_missed_date'].isnull()) & (df['n_missed_days'] >= 1),
    df['net_due_amount_newww'], 0)

summary = df.groupby('created_date').agg(
    total_loan_disbursed=('order_amount', 'sum'),
    refund_amount=('settlement_refund_amount', 'sum'),
    total_receivable=('net_due_amount', 'sum'),
    total_repayment=('paytabs_processed_amount', 'sum')
).reset_index()

summary['percentage_loan_disbursed'] = (summary['total_loan_disbursed'] / summary['total_loan_disbursed'].sum()) * 100

# Active loans data
dd = pd.read_csv('risk_dumps/PL_Installments_Report_daily.csv')
dd = dd[dd['which_month'] == 'current_month']
dd['Order Date (UTC Time)'] = pd.to_datetime(dd['Order Date (UTC Time)'])
dd['day'] = dd['Order Date (UTC Time)'].dt.day

summary_active = dd.groupby('day').agg(
    Active_payments=('order_id', 'count')
).reset_index()

# Verifications data
df_verifications = pd.read_csv('risk_dumps/verifications_PL.csv')
df_verifications = df_verifications[df_verifications['which_month'] == 'current_month']
df_verifications['attempted_at'] = pd.to_datetime(df_verifications['attempted_at'])
df_verifications['day'] = df_verifications['attempted_at'].dt.day

verification_totals = df_verifications.groupby('verification_status')['user_id'].count().reset_index()
total_pending = verification_totals[verification_totals['verification_status'] == 'pending']['user_id'].sum()
total_rejected = verification_totals[verification_totals['verification_status'] == 'rejected']['user_id'].sum()
total_verified = verification_totals[verification_totals['verification_status'] == 'verified']['user_id'].sum()

total_users_per_day = df_verifications.groupby('day')['user_id'].count().reset_index().rename(columns={'user_id': 'total_users'})
user_counts = df_verifications.groupby(['day', 'verification_status'])['user_id'].count().reset_index()
user_counts = pd.merge(user_counts, total_users_per_day, on='day')
user_counts['percentage_of_users'] = (user_counts['user_id'] / user_counts['total_users']) * 100
user_counts = user_counts[['day', 'verification_status', 'percentage_of_users']]

# Average order value
healthy_book = pd.read_csv('risk_dumps/healthy_book.csv')
healthy_book = healthy_book[healthy_book['which_month'] == 'current_month']
healthy_book['created_at'] = pd.to_datetime(healthy_book['created_at'])
healthy_book['day_of_created_date'] = healthy_book['created_at'].dt.day
healthy_book['aov_aed'] = healthy_book['aed_amount']
healthy = healthy_book.groupby('day_of_created_date').agg(
    aov=('aov_aed', 'mean')
).reset_index()
healthy['aov'] = healthy['aov'].round(0)

healthy_merchant = healthy_book.groupby('merchant_name').agg(
    aov=('aov_aed', 'mean')
).reset_index()
healthy_merchant['aov'] = healthy_merchant['aov'].round(0)

healthy_merchant_gmv = healthy_book.groupby('merchant_name').agg(
    gmv=('aov_aed', 'sum')
).reset_index()
healthy_merchant_gmv['gmv'] = healthy_merchant_gmv['gmv'].round(0)

healthy_gmv_scat = healthy_book.groupby(['merchant_name', 'day_of_created_date']).agg(
    gmv=('aov_aed', 'sum')
).reset_index()
healthy_gmv_scat['gmv'] = healthy_gmv_scat['gmv'].round(0)

healthy_aov_scat = healthy_book.groupby(['merchant_name', 'day_of_created_date']).agg(
    aov=('aov_aed', 'mean')
).reset_index()
healthy_aov_scat['aov'] = healthy_aov_scat['aov'].round(0)

color_map = {
    'verified': 'green',
    'pending': '#fff033',
    'rejected': 'red'
}

total_loan_disbursed = f"{summary['total_loan_disbursed'].sum():,.0f}"
refund_amount = f"{summary['refund_amount'].sum():,.0f}"
total_receivable = f"{summary['total_receivable'].sum():,.0f}"
total_paid = f"{summary['total_repayment'].sum():,.0f}"
delinquency_rate = f"{df[(df['first_missed_date'].notnull())&(df['net_loss_new']>0)].shape[0]:,.0f}"
active_loans = f"{df[df['order_status']=='ACTIVE'].shape[0]:,.0f}"

pending_count = f"{total_pending:,}"
rejected_count = f"{total_rejected:,}"
verified_count = f"{total_verified:,}"

missed  = pd.read_csv('risk_dumps/PL_Missed_Report_daily.csv')
missed = missed[missed['which_month']=='current_month']
missed['order_date'] = pd.to_datetime(missed['order_date'])
missed['day_of_order_date'] = missed['order_date'].dt.day
grouped = missed.groupby('day_of_order_date').agg(
    missed_count=('inst_status', lambda x: (x == 'MISSED').sum())  ,
    count = ('order_id','count')
).reset_index()

grouped['percentage_of_users'] = (grouped['missed_count'] / grouped['count']) * 100


#######################################################################################################################################################
fig_loan_active = px.line(summary_active, 
                          line_shape='spline', 
                          x='day', 
                          y='Active_payments', 
                          text='Active_payments',
                          title='Active Payments per Day',
                          labels={'day': 'Day of Month', 'Active_payments': 'Active Payments'},
                          markers=True)
fig_loan_active.update_traces(marker=dict(size=8), texttemplate='%{text:.0f}', textposition='top right', line=dict(color='#636efa'))

fig_loan_active.update_xaxes(tickmode='linear', dtick=1)

#######################################################################################################################################################
fig_loan = px.line(summary, 
                   line_shape='spline', 
                   x='created_date', 
                   y='total_loan_disbursed', 
                   text='total_loan_disbursed',
                   title='Total Loans Disbursed per Day',
                   labels={'created_date': 'Day of Month', 'total_loan_disbursed': 'Total Loans'},
                   markers=True)

fig_loan.update_traces(marker=dict(size=8), texttemplate='%{text:.0f}', textposition='top right', line=dict(color='#636efa'))

fig_loan.update_xaxes(tickmode='linear', dtick=1)

#######################################################################################################################################################
fig_verifications = px.line(user_counts, 
                            x='day', 
                            y='percentage_of_users', 
                            color='verification_status', 
                            labels={'day': 'Day of Attempted Verification', 'percentage_of_users': '% of Users'},
                            title='Verification Status per Day',
                            color_discrete_map=color_map,
                            markers=True,  
                            line_shape='spline',  
                            text='percentage_of_users'  
                           )

for trace in fig_verifications.data:
    verification_status = trace.name
    trace_text = user_counts[user_counts['verification_status'] == verification_status]['percentage_of_users'].round(0).astype(int).astype(str) + '%'
    trace.text = trace_text
    trace.textposition = 'top right'

fig_verifications.update_traces(marker=dict(size=8), textposition='top right')

fig_verifications.update_xaxes(tickmode='linear', dtick=1)

#######################################################################################################################################################
fig_aov = px.line(
    healthy, 
    line_shape='spline', 
    x='day_of_created_date', 
    y='aov', 
    text='aov',
    title='Average Order Value per day',  
    labels={'day_of_created_date': 'Day of created date', 'aov': 'Average Order Value'},
    markers=True
)

fig_aov.update_traces(
    marker=dict(size=8), 
    texttemplate='%{text:.0f}', 
    textposition='top right', 
    line=dict(color='#636efa'))

fig_aov.update_layout(
    title={
        'text': 'Average Order Value per day'
    }
)

fig_aov.update_xaxes(tickmode='linear', dtick=1)

#######################################################################################################################################################
merchant_colors = {
    merchant: color for merchant, color in zip(healthy_merchant['merchant_name'].unique(), px.colors.qualitative.Plotly)
}

fig_bar_merchant = px.bar(
    healthy_merchant,  
    x='merchant_name',  
    y='aov', 
    title='Average Order Value by Merchant',  
    labels={'merchant_name': 'Merchant', 'aov': 'Average Order Value'},  
    text='aov',
    color='merchant_name',
    color_discrete_map=merchant_colors
)

fig_bar_merchant.update_layout(
    title={
        'text': 'Average Order Value by Merchant'
    },
    width=1400,  
    height=400,
    yaxis=dict(range=[0, healthy_merchant['aov'].max()+healthy_merchant['aov'].mean()]) 
)

fig_bar_merchant.update_traces(
    texttemplate='%{text:,.0f} QAR', 
    textfont=dict(size=19), 
    textposition='inside'   
)

#######################################################################################################################################################
fig_line_aov = px.line(
    healthy_aov_scat,
    x='day_of_created_date',
    y='aov',
    color='merchant_name',  # Color by merchant
    title='AOV by Merchant daily',
    labels={'day_of_created_date': 'Day', 'aov': 'Average Order Value'},
    markers=True,
    text='aov',
    line_shape='spline'
)

# Update traces to set the line color explicitly for each merchant
for merchant in merchant_colors:
    fig_line_aov.for_each_trace(
        lambda trace: trace.update(line=dict(color=merchant_colors[trace.name])) if trace.name == merchant else ()
    )

fig_line_aov.update_layout(
    font=dict(size=14),
    height=500,
    xaxis=dict(tickmode='linear')
)

fig_line_aov.update_traces(
    textposition="top right",
    texttemplate='%{text:.0f}'
)

#######################################################################################################################################################
fig_bar_merchant_gmv = px.bar(
    healthy_merchant_gmv,  
    x='merchant_name',  
    y='gmv', 
    title='GMV by Merchant',  
    labels={'merchant_name': 'Merchant', 'gmv': 'GMV'},  
    text='gmv',
    color='merchant_name',
    color_discrete_map=merchant_colors
)

fig_bar_merchant_gmv.update_layout(
    title={
        'text': 'GMV by Merchant'
    },
    width=1400,  
    height=400,
    yaxis=dict(range=[0, healthy_merchant_gmv['gmv'].max()+healthy_merchant_gmv['gmv'].mean()]) 
)

fig_bar_merchant_gmv.update_traces(
    texttemplate='%{text:,.0f} QAR', 
    textfont=dict(size=19), 
    textposition='inside'   
)

#######################################################################################################################################################
fig_line_gmv = px.line(
    healthy_gmv_scat, 
    x='day_of_created_date', 
    y='gmv', 
    color='merchant_name',  
    title='GMV by Merchant daily',
    labels={'day_of_created_date': 'Day', 'gmv': 'GMV'},
    markers=True,  
    text='gmv' ,
     line_shape='spline'
)

for merchant in merchant_colors:
    fig_line_gmv.for_each_trace(
        lambda trace: trace.update(line=dict(color=merchant_colors[trace.name])) if trace.name == merchant else ()
    )

fig_line_gmv.update_layout(
    font=dict(size=14), 
    #width=800, 
    height=500,
    xaxis=dict(
        tickmode='linear'  
    )
)

fig_line_gmv.update_traces(
    textposition="top right",  
    texttemplate='%{text:.0f}',  
)

#######################################################################################################################################################
fig_missed = px.line(
    grouped, 
    x='day_of_order_date', 
    y='percentage_of_users', 
    
    title='Missed Installments per Day',
    labels={'day_of_order_date': 'Day of Order Date', 'percentage_of_users': '% of Users'},
    markers=True,  
    line_shape='spline',  
    text='percentage_of_users'  
)

fig_missed.update_traces(
    textposition="top right", 
    texttemplate='%{text:.0f}%', 
    marker=dict(size=8)  
)

fig_missed.update_layout(
    font=dict(size=14),
    height=500,
    xaxis=dict(tickmode='linear', dtick=1) 
   
)
#######################################################################################################################################################

st. set_page_config(layout="wide")

metrics_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        .summary-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
        }}
        .summary-box {{
            background: #f4f4f4;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            width: calc(25% - 20px); /* Adjust width to fit 4 boxes per line */
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            box-sizing: border-box;
        }}
        .summary-box h3 {{
            margin: 10px 0;
            font-size: 1.5em;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="summary-container">
        <div class="summary-box">
            <p>Total Loans Disbursed</p>
            <h3>{total_loan_disbursed} QAR</h3>
        </div>
        <div class="summary-box">
            <p>Refund Amount</p>
            <h3>{refund_amount} QAR</h3>
        </div>
        <div class="summary-box">
            <p>Total Receivable Amount</p>
            <h3>{total_receivable} QAR</h3>
        </div>
        <div class="summary-box">
            <p>Total Paid Amount</p>
            <h3>{total_paid} QAR</h3>
        </div>
        <div class="summary-box">
            <p>Loan Delinquency Rate</p>
            <h3>{delinquency_rate}</h3>
        </div>
        <div class="summary-box">
            <p>Number of Active Loans</p>
            <h3>{active_loans}</h3>
        </div>
    </div>
    
</body>
</html>
"""

metrics_verif_html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
    .verification-container {{
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin-top: 20px;
        }}
        .verification-box {{
            background: #f4f4f4;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            width: calc(29% - 20px);
        }}
        .verification-pending {{
            background-color: #FFF898;
        }}
        .verification-rejected {{
            background-color: #ffe5e5;
        }}
        .verification-verified {{
            background-color: #e5ffe5;
        }}
        .verification-box h4 {{
            margin: 0;
            font-size: 1em;
            color: #555;
        }}
        .verification-box h3 {{
            font-size: 2em;
            margin: 0;
        }}
    </style>
    
    <div class="verification-container">
        <div class="verification-box verification-pending">
            <h4>PENDING</h4>
            <h3>{pending_count}</h3>
        </div>
        <div class="verification-box verification-rejected">
            <h4>REJECTED</h4>
            <h3>{rejected_count}</h3>
        </div>
        <div class="verification-box verification-verified">
            <h4>VERIFIED</h4>
            <h3>{verified_count}</h3>
        </div>
    </div>
    
</body>
</html>
"""

components.html(metrics_html, height=300, scrolling=True)
st.plotly_chart(fig_loan, use_container_width=True)
components.html(metrics_verif_html, height=150, scrolling=True)
st.plotly_chart(fig_verifications, use_container_width=True)
st.plotly_chart(fig_loan_active, use_container_width=True)
st.plotly_chart(fig_aov, use_container_width=True)
st.plotly_chart(fig_bar_merchant, use_container_width=True)
st.plotly_chart(fig_line_aov, use_container_width=True)
st.plotly_chart(fig_bar_merchant_gmv, use_container_width=True)
st.plotly_chart(fig_line_gmv, use_container_width=True)
st.plotly_chart(fig_missed, use_container_width=True)
