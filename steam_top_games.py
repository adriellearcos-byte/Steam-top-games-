import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------------------------------------------------------
# 4. DASHBOARD CREATION & 7. PROPER UTILIZATION OF FONTS/COLORS
# -----------------------------------------------------------------------------
st.set_page_config(page_title="Steam Top Games Dashboard", layout="wide")

# Injecting Custom CSS to style the Key Insight box and typography
st.markdown("""
<style>
    .insight-box {
        background-color: #171a21;
        border-left: 6px solid #66c0f4;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        color: #c7d5e0;
    }
    .insight-title {
        color: #ffffff;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 22px;
        font-weight: 800;
        margin-bottom: 10px;
    }
    .insight-text {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-size: 16px;
        line-height: 1.6;
    }
    .highlight {
        color: #66c0f4;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 1. OPEN DATASET & 3. DATA CLEANING
# -----------------------------------------------------------------------------
@st.cache_data
def load_and_clean_data():
    # Load the local CSV file
    df = pd.read_csv("steam_top_games_2026.csv")
    
    # --- Data Cleaning ---
    # Convert release_date to datetime and extract the year
    df['release_date'] = pd.to_datetime(df['release_date'], errors='coerce')
    df['year'] = df['release_date'].dt.year
    df = df.dropna(subset=['year']) # Drop rows where year couldn't be parsed
    df['year'] = df['year'].astype(int)
    
    # Clean textual columns: fill missing genres with 'Unknown'
    df['genres'] = df['genres'].fillna('Unknown')
    
    # Extract the primary genre (first genre in the comma-separated list) for categorization
    df['primary_genre'] = df['genres'].apply(lambda x: x.split(',')[0].strip() if isinstance(x, str) else 'Unknown')
    
    # Handle missing numerical data
    df['metacritic_score'] = df['metacritic_score'].fillna(0)
    df['price_usd'] = df['price_usd'].fillna(0.0)
    
    # Create derived metrics for better insight analysis
    df['total_reviews'] = df['positive_reviews'] + df['negative_reviews']
    df['positive_ratio'] = (df['positive_reviews'] / df['total_reviews']).fillna(0) * 100
    
    return df

df = load_and_clean_data()

# -----------------------------------------------------------------------------
# 6. RESPONSIVE TO USER INPUTS
# -----------------------------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Steam_icon_logo.svg/512px-Steam_icon_logo.svg.png", width=60)
st.sidebar.header("⚙️ Dashboard Filters")
st.sidebar.write("Adjust the parameters to explore the gaming data.")

# Year Filter
min_year, max_year = int(df['year'].min()), int(df['year'].max())
selected_years = st.sidebar.slider("Select Release Year Range", min_year, max_year, (2010, max_year))

# Price Filter
is_free_filter = st.sidebar.radio("Game Pricing", ["All", "Free to Play Only", "Paid Only"])

# Genre Filter
top_genres = df['primary_genre'].value_counts().head(10).index.tolist()
selected_genres = st.sidebar.multiselect("Select Primary Genre", options=top_genres, default=top_genres[:5])

# Apply filters
filtered_df = df[(df['year'] >= selected_years[0]) & (df['year'] <= selected_years[1])]

if is_free_filter == "Free to Play Only":
    filtered_df = filtered_df[filtered_df['is_free'] == True]
elif is_free_filter == "Paid Only":
    filtered_df = filtered_df[filtered_df['is_free'] == False]

if selected_genres:
    filtered_df = filtered_df[filtered_df['primary_genre'].isin(selected_genres)]


# -----------------------------------------------------------------------------
# DASHBOARD MAIN LAYOUT
# -----------------------------------------------------------------------------
st.title("🎮 Steam Top Games Analytics Dashboard")

# 8. HIGHLIGHT THE KEY INSIGHT
st.markdown("""
<div class="insight-box">
    <div class="insight-title">💡 Key Insight: Critical Acclaim vs. Player Engagement</div>
    <div class="insight-text">
        Exploring the data reveals a stark contrast between <span class="highlight">critical acclaim</span> and <span class="highlight">mass engagement</span>. While highly-priced, single-player RPGs and Action games often secure the highest Metacritic scores, the highest <b>Peak Concurrent Users (CCU)</b> and overall playtime are massively dominated by <b>Free-to-Play, Multiplayer titles</b>. The barrier to entry (price) acts as a strict ceiling on viral engagement, meaning the most "popular" games and the most "critically acclaimed" games are rarely the same.
    </div>
</div>
""", unsafe_allow_html=True)


# 5. RELEVANT KEY PERFORMANCE INDICATORS (KPIs)
st.markdown("### 📊 Market Performance Indicators")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Games in View", f"{len(filtered_df):,}")
with col2:
    st.metric("Avg Price (Paid Games)", f"${filtered_df[filtered_df['is_free']==False]['price_usd'].mean():.2f}")
with col3:
    st.metric("Max Peak CCU", f"{filtered_df['peak_ccu'].max():,.0f}")
with col4:
    st.metric("Avg Positive Review %", f"{filtered_df['positive_ratio'].mean():.1f}%")

st.markdown("---")


# 6. ADVANCED GRAPHS AND CHARTS (Plotly)
colA, colB = st.columns((1, 1))

with colA:
    st.markdown("#### 📈 Price vs. Peak Engagement (CCU)")
    # Advanced Chart 1: Interactive Bubble Scatter Plot
    # We use log scale for Peak CCU because game popularity is exponentially distributed
    fig_scatter = px.scatter(
        filtered_df, 
        x='price_usd', 
        y='peak_ccu', 
        color='primary_genre',
        size='total_reviews',
        hover_name='name',
        hover_data=['positive_ratio', 'developer'],
        log_y=True,
        size_max=40,
        labels={"price_usd": "Price (USD)", "peak_ccu": "Peak Concurrent Users (Log Scale)"},
        template="plotly_dark"
    )
    fig_scatter.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, legend_title="Genre")
    st.plotly_chart(fig_scatter, use_container_width=True)

with colB:
    st.markdown("#### 🕹️ Genre Hierarchy & Average Playtime")
    # Advanced Chart 2: Interactive Sunburst Chart
    # Group by genre and is_free to see playtime hierarchy
    sunburst_data = filtered_df.groupby(['primary_genre', 'is_free'])['avg_playtime_forever'].sum().reset_index()
    sunburst_data['Pricing'] = sunburst_data['is_free'].map({True: 'Free', False: 'Paid'})
    
    fig_sunburst = px.sunburst(
        sunburst_data, 
        path=['primary_genre', 'Pricing'], 
        values='avg_playtime_forever',
        color='avg_playtime_forever',
        color_continuous_scale='Teal',
        template="plotly_dark"
    )
    fig_sunburst.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_sunburst, use_container_width=True)


st.markdown("#### ⭐ Critical Reception over Time (Metacritic)")
# Responsive Box Plot
# Exclude rows where metacritic is 0 (missing) for a cleaner reception timeline
meta_df = filtered_df[filtered_df['metacritic_score'] > 0]
fig_box = px.box(
    meta_df, 
    x='year', 
    y='metacritic_score', 
    color='primary_genre',
    points="all",
    template="plotly_dark",
    labels={"year": "Release Year", "metacritic_score": "Metacritic Score"}
)
fig_box.update_layout(
    margin={"r":0,"t":20,"l":0,"b":0},
    xaxis=dict(tickmode='linear', dtick=1)
)
st.plotly_chart(fig_box, use_container_width=True)

# -----------------------------------------------------------------------------
# 2. PROPER DATA ATTRIBUTION
# -----------------------------------------------------------------------------
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #888; font-size: 13px;">
    <b>Data Attribution:</b><br>
    The data utilized in this dashboard is sourced from the Steam Top 1495 Games Dataset via Kaggle.<br>
    Dataset source: <a href="https://www.kaggle.com/datasets/patelris/steam-top-1495-games-dataset" target="_blank">Kaggle: Steam Top Games</a>
</div>
""", unsafe_allow_html=True)
# Footer (IMPORTANT FOR GRADING)
st.markdown("---")
st.caption("Data Source: https://www.kaggle.com/datasets/patelris/steam-top-1495-games-dataset?resource=download")
st.caption("Team Members: Adrielle Arcos, Charmaine Cachila, Ralph Ilarde")
