import streamlit as st
import pandas as pd
import plotly.express as px
import re
# Set page config
st.set_page_config(page_title="Global Health & Economy Dashboard", layout="wide")

# Load datasets
@st.cache_data
def load_data():
    gdp = pd.read_csv("data/gdp_pcap.csv")
    life = pd.read_csv("data/life_expectancy.csv")
    pop = pd.read_csv("data/population.csv")
    return gdp, life, pop

gdp_raw, life_raw, pop_raw = load_data()

# Preprocess

def convert_string_to_number(val):
    if isinstance(val, str):
        val = val.replace(',', '').replace('$', '').strip()
        if re.match(r'^\d+(\.\d+)?[kMB]$', val):
            num = float(re.findall(r'\d+\.?\d*', val)[0])
            if 'k' in val:
                return num * 1e3
            elif 'M' in val:
                return num * 1e6
            elif 'B' in val:
                return num * 1e9
        try:
            return float(val)
        except:
            return None
    return val

def preprocess(df):
    df = df.dropna()
    for col in df.columns[1:]:
        df[col] = df[col].apply(convert_string_to_number)
    return df


gdp = preprocess(gdp_raw)
life = preprocess(life_raw)
pop = preprocess(pop_raw)

# Melt data
def melt_data(df, name):
    df_melted = df.melt(id_vars=["country"], var_name="year", value_name=name)
    df_melted["year"] = df_melted["year"].astype(int)
    return df_melted

gdp_m = melt_data(gdp, "gdp_per_cap")
life_m = melt_data(life, "life_exp")
pop_m = melt_data(pop, "population")

# Merge
df = gdp_m.merge(life_m, on=["country", "year"]).merge(pop_m, on=["country", "year"])
df.dropna(inplace=True)

# Title
st.title("🌍 GDP vs Life Expectancy Over Time")
st.caption("An interactive dashboard visualizing 100+ years of change in global health and economy.")

# Tabs
tab1, tab2, tab3 = st.tabs(["📈 Global Overview", "🌐 Compare Countries", "📊 Rankings"])

# --- TAB 1: Global Overview ---
with tab1:
    year = st.slider("Select Year", min_value=df["year"].min(), max_value=df["year"].max(), value=2000, step=1)
    df_year = df[df["year"] == year]

    fig = px.scatter(
        df_year,
        x="gdp_per_cap",
        y="life_exp",
        size="population",
        color="country",
        hover_name="country",
        size_max=60,
        log_x=True,
        title=f"GDP per Capita vs Life Expectancy ({year})",
        labels={"gdp_per_cap": "GDP per Capita", "life_exp": "Life Expectancy"}
    )
    st.plotly_chart(fig, use_container_width=True)

    # Download CSV
    st.download_button(
        label="📥 Download Yearly Data (CSV)",
        data=df_year.to_csv(index=False),
        file_name=f"gdp_life_pop_{year}.csv",
        mime="text/csv"
    )

# --- TAB 2: Compare Countries ---
with tab2:
    countries = st.multiselect("Select Countries to Compare", options=df["country"].unique(), default=["India", "China", "United States"])
    compare_df = df[df["country"].isin(countries)]

    col1, col2, col3 = st.columns(3)

    with col1:
        fig_gdp = px.line(compare_df, x="year", y="gdp_per_cap", color="country", title="GDP per Capita Over Time")
        st.plotly_chart(fig_gdp, use_container_width=True)

    with col2:
        fig_life = px.line(compare_df, x="year", y="life_exp", color="country", title="Life Expectancy Over Time")
        st.plotly_chart(fig_life, use_container_width=True)

    with col3:
        fig_pop = px.line(compare_df, x="year", y="population", color="country", title="Population Over Time")
        st.plotly_chart(fig_pop, use_container_width=True)

# --- TAB 3: Rankings ---
with tab3:
    year_r = st.selectbox("Select Year for Rankings", sorted(df["year"].unique()), index=120)
    df_rank = df[df["year"] == year_r].sort_values("gdp_per_cap", ascending=False)

    st.subheader(f"🌟 Top 10 Countries by GDP per Capita ({year_r})")
    st.dataframe(df_rank[["country", "gdp_per_cap", "life_exp", "population"]].head(10), use_container_width=True)

    st.subheader(f"⚠️ Bottom 10 Countries by GDP per Capita ({year_r})")
    st.dataframe(df_rank[["country", "gdp_per_cap", "life_exp", "population"]].tail(10), use_container_width=True)
