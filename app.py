import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

@st.cache_data
def load_data():
    df = pd.read_csv("Matiks_dataset.csv")

    df['Signup_Date'] = pd.to_datetime(df['Signup_Date'], errors='coerce')
    df['Last_Login'] = pd.to_datetime(df['Last_Login'], errors='coerce')

    df = df.dropna(subset=['Last_Login'])

    df['Week'] = df['Last_Login'].dt.to_period('W').astype(str)
    df['Month'] = df['Last_Login'].dt.to_period('M').astype(str)

    return df


df = load_data()

# --- Sidebar Filters ---
st.sidebar.header("Filter Options")
countries = st.sidebar.multiselect("Country", df['Country'].unique())
games = st.sidebar.multiselect("Game Title", df['Game_Title'].unique())
subscription_tiers = st.sidebar.multiselect("Subscription Tier", df['Subscription_Tier'].unique())

df_filtered = df.copy()
if countries:
    df_filtered = df_filtered[df_filtered['Country'].isin(countries)]
if games:
    df_filtered = df_filtered[df_filtered['Game_Title'].isin(games)]
if subscription_tiers:
    df_filtered = df_filtered[df_filtered['Subscription_Tier'].isin(subscription_tiers)]

# --- KPI Cards ---
st.title("🎮 Gaming Analytics Dashboard")
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Total Users", df_filtered['User_ID'].nunique())
kpi2.metric("Total Revenue (USD)", f"${df_filtered['Total_Revenue_USD'].sum():,.2f}")
kpi3.metric("Avg Session Duration (min)", f"{df_filtered['Avg_Session_Duration_Min'].mean():.2f}")

# --- DAU / WAU / MAU ---
st.subheader("User Activity")
dau = df_filtered.groupby('Last_Login')['User_ID'].nunique().reset_index(name='DAU')
dau_chart = px.line(dau, x='Last_Login', y='DAU', title="Daily Active Users")
st.plotly_chart(dau_chart, use_container_width=True)

wau = df_filtered.groupby('Week')['User_ID'].nunique().reset_index(name='WAU')
wau_chart = px.line(wau, x='Week', y='WAU', title="Weekly Active Users")
st.plotly_chart(wau_chart, use_container_width=True)

mau = df_filtered.groupby('Month')['User_ID'].nunique().reset_index(name='MAU')
mau_chart = px.line(mau, x='Month', y='MAU', title="Monthly Active Users")
st.plotly_chart(mau_chart, use_container_width=True)

# --- Revenue Trend ---
st.subheader("Revenue Trends Over Time")
revenue_over_time = df_filtered.groupby('Month')['Total_Revenue_USD'].sum().reset_index()
revenue_chart = px.bar(revenue_over_time, x='Month', y='Total_Revenue_USD', title="Monthly Revenue")
st.plotly_chart(revenue_chart, use_container_width=True)

# --- Breakdown Charts ---
st.subheader("Breakdowns")
device_chart = px.pie(df_filtered, names='Device_Type', title='Device Type Distribution')
st.plotly_chart(device_chart, use_container_width=True)

segment_chart = px.bar(df_filtered.groupby('Subscription_Tier')['Total_Revenue_USD'].sum().reset_index(),
                       x='Subscription_Tier', y='Total_Revenue_USD', title='Revenue by Subscription Tier')
st.plotly_chart(segment_chart, use_container_width=True)

mode_chart = px.box(df_filtered, x='Preferred_Game_Mode', y='Avg_Session_Duration_Min',
                    title='Session Duration by Game Mode')
st.plotly_chart(mode_chart, use_container_width=True)

# --- Insights ---
st.subheader("📊 Key Insights")

# High Retention or High Value Users
high_value = df_filtered[df_filtered['Total_Revenue_USD'] > df_filtered['Total_Revenue_USD'].quantile(0.9)]
high_retention = df_filtered[df_filtered['Total_Play_Sessions'] > df_filtered['Total_Play_Sessions'].quantile(0.9)]
st.markdown(f"**High Value Users:** {high_value['User_ID'].nunique()} users")
st.markdown(f"**High Retention Users:** {high_retention['User_ID'].nunique()} users")

# Churn Risk
st.markdown("**Churn Risk Users**: Those with large gaps between last session and today or very few sessions")
now = pd.Timestamp.now()
df_filtered['Days_Since_Last_Login'] = (now - df_filtered['Last_Login']).dt.days
churn_risk = df_filtered[(df_filtered['Days_Since_Last_Login'] > 30) | (df_filtered['Total_Play_Sessions'] <= 2)]
st.markdown(f"**Potential Churn Users:** {churn_risk['User_ID'].nunique()} users")

# Suggestions
st.subheader("💡 Suggestions to Improve Retention/Revenue")

# Key metrics
total_users = df_filtered['User_ID'].nunique()
churned_users = churn_risk['User_ID'].nunique()
churn_pct = churned_users / total_users * 100
mid_tier_users = df_filtered[df_filtered['Subscription_Tier'] == 'Mid']['User_ID'].nunique()
low_session_users = df_filtered[df_filtered['Total_Play_Sessions'] <= 2]['User_ID'].nunique()
high_value_users = high_value['User_ID'].nunique()

st.markdown(f"- 🎯 **{churn_pct:.1f}% of users ({churned_users} out of {total_users}) show clear churn signals** — either low session count or >30 days inactivity. Send them aggressive reactivation offers or mark them for downgrade prevention.")

st.markdown(f"- 🧪 **{low_session_users} users played only once or twice**. Stop wasting engagement budget on these. Instead, A/B test onboarding tweaks or drop-off intercepts in first 2 sessions.")

st.markdown(f"- 💰 **{high_value_users} users generate over 90% of revenue**. Identify their patterns (e.g. game mode, session length) and build lookalike audiences. Don't spread campaigns too wide — go where the money is.")

st.markdown(f"- 💸 **{mid_tier_users} users on 'Mid' subscription — likely to churn**. Either convert them to high-tier by bundling high-usage game modes, or offer ‘pause’ options instead of letting them drop out completely.")
st.markdown("- Offer targeted incentives or rewards for users nearing churn.")
st.markdown("- Promote popular game modes among low-retention users.")
st.markdown("- Encourage social features or competition to increase engagement.")
st.markdown("- Consider tailored pricing or trial extensions for mid-tier subscribers.")
