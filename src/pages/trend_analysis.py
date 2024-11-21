import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import statsmodels.api as sm

def page(dataframe, selected_country, selected_year_range):
    st.title("Trend Analysis")
    
    # Load the life expectancy data
    life_expectancy_df = pd.read_csv("data/life-expectancy.csv")
    default_df = pd.read_csv("data/owid-co2-data.csv")
    life_expectancy_df['Year'] = life_expectancy_df['Year'].astype(int)  # Ensure year is in integer format

    # Compare metrics
    compare_matrics(default_df, life_expectancy_df, selected_country, selected_year_range)

def compare_matrics(default_df, life_expectancy_df, selected_country, selected_year_range):
    # Filter life expectancy data for selected countries and years
    life_expectancy_filtered = life_expectancy_df[
        (life_expectancy_df["Entity"].isin(selected_country)) & 
        (life_expectancy_df["Year"] >= selected_year_range[0]) & 
        (life_expectancy_df["Year"] <= selected_year_range[1])
    ]

    # Filter the default dataframe (previously metrics) for selected countries and years
    co2_data_filtered = default_df[
        (default_df["country"].isin(selected_country)) & 
        (default_df["year"] >= selected_year_range[0]) & 
        (default_df["year"] <= selected_year_range[1])
    ]

    # Merge life expectancy data with the CO2 data based on Entity (Country) and Year
    merged_df = pd.merge(co2_data_filtered, life_expectancy_filtered, left_on=["country", "year"], right_on=["Entity", "Year"], how="inner")

    # Ensure we have data after merging
    if merged_df.empty:
        st.warning("No data available for the selected criteria.")
        return None

    # Create a line plot for each country (relationship between Life Expectancy and CO2 per Capita)
    fig = go.Figure()

    # Add lines for each country (Life Expectancy vs CO2 per Capita)
    for country in selected_country:
        country_data = merged_df[merged_df["country"] == country]
        fig.add_trace(go.Scatter(
            x=country_data["Life expectancy"],  # Life Expectancy on x-axis (swapped with CO2)
            y=country_data["co2_per_capita"],  # CO2 per Capita on y-axis (swapped with Life Expectancy)
            mode="lines+markers",
            name=f"{country} Life Expectancy vs CO2 per Capita",
            line=dict(width=2)
        ))

    # Calculate and add average OLS trendline for all countries
    X = merged_df[["Life expectancy"]]  # Independent variable (Life Expectancy)
    X = sm.add_constant(X)  # Add constant term for OLS (intercept)
    y = merged_df["co2_per_capita"]  # Dependent variable (CO2 per Capita)

    model = sm.OLS(y, X).fit()
    trendline = model.predict(X)  # Predicted values (trendline)

    # Add the OLS trendline to the plot
    fig.add_trace(go.Scatter(
        x=merged_df["Life expectancy"],  # Life Expectancy on x-axis for OLS line
        y=trendline,  # Predicted CO2 per Capita values
        mode="lines",
        name="Average OLS Trendline",
        line=dict(color="black", dash="dash")
    ))

    # Update layout and axis titles
    fig.update_layout(
        title="Life Expectancy vs CO2 Per Capita",
        xaxis_title="Life Expectancy",  # Swapped to reflect the change
        yaxis_title="CO2 per Capita",  # Swapped to reflect the change
        template="plotly_dark"
    )

    # Display the plot
    st.plotly_chart(fig, use_container_width=True)
