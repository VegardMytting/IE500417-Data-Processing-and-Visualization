import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import statsmodels.api as sm
import plotly.express as px

def page(dataframe, selected_country, selected_year_range):
    st.title("Trend Analysis")
    
    # Load the life expectancy and CO2 data
    life_expectancy_df = pd.read_csv("data/life-expectancy.csv")
    default_df = pd.read_csv("data/owid-co2-data.csv")
    life_expectancy_df['Year'] = life_expectancy_df['Year'].astype(int)  # Ensure year is in integer format

    # Filter the data based on selected countries and year range
    life_expectancy_filtered = life_expectancy_df[ 
        (life_expectancy_df["Entity"].isin(selected_country)) & 
        (life_expectancy_df["Year"] >= selected_year_range[0]) & 
        (life_expectancy_df["Year"] <= selected_year_range[1]) 
    ]
    
    co2_data_filtered = default_df[
        (default_df["country"].isin(selected_country)) & 
        (default_df["year"] >= selected_year_range[0]) & 
        (default_df["year"] <= selected_year_range[1])
    ]
    
    merged_df = pd.merge(co2_data_filtered, life_expectancy_filtered, left_on=["country", "year"], right_on=["Entity", "Year"], how="inner")

    # Ensure data is available
    if merged_df.empty:
        st.warning("No data available for the selected criteria.")
        return None
    
    # --- Correlation Matrix ---
    # Select only the desired columns for correlation analysis
    selected_columns = ['co2_per_capita', 'gdp', 'cement_co2', 'trade_co2']
    correlation_matrix = merged_df[selected_columns].corr()

    # Create the plotly heatmap for correlation matrix
    fig = go.Figure(data=go.Heatmap(
        z=correlation_matrix.values,
        x=correlation_matrix.columns,
        y=correlation_matrix.columns,
        colorscale='RdBu',
        zmin=-1, zmax=1
    ))

    # Update layout for correlation matrix heatmap
    fig.update_layout(
        title="Correlation Matrix for Selected Variables",
        xaxis_title="Variables",
        yaxis_title="Variables",
        template="plotly_dark"
    )

    # Display the correlation matrix heatmap
    st.plotly_chart(fig)

    # --- Scatter Plot Generation ---
    # List of available columns for analysis from the CO2 dataframe
    available_columns = default_df.columns.tolist()
    available_columns.remove('country')  # Remove country column, as it won't be part of the correlation analysis
    
    # Sidebar for selecting X-axis and Y-axis variables
    x_axis_variable = st.sidebar.selectbox('Select Variable for X-Axis:', ['Life expectancy'] + available_columns)
    y_axis_variable = 'co2_per_capita'  # This will remain constant, as you want to analyze CO2 vs other factors

    # Call function to compare metrics (scatter plot + OLS line)
    compare_metrics(default_df, life_expectancy_df, selected_country, selected_year_range, x_axis_variable, y_axis_variable)

def compare_metrics(default_df, life_expectancy_df, selected_country, selected_year_range, x_axis_variable, y_axis_variable):
    # Filter life expectancy data for selected countries and years
    life_expectancy_filtered = life_expectancy_df[ 
        (life_expectancy_df["Entity"].isin(selected_country)) & 
        (life_expectancy_df["Year"] >= selected_year_range[0]) & 
        (life_expectancy_df["Year"] <= selected_year_range[1]) 
    ]
    
    # Filter the CO2 dataframe for selected countries and years
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

    # --- Scatter Plot ---
    fig = go.Figure()

    # Add scatter points for each country (selected variable vs CO2 per Capita)
    for country in selected_country:
        country_data = merged_df[merged_df["country"] == country]
        fig.add_trace(go.Scatter(
            x=country_data[x_axis_variable],  # Selected X-Axis variable
            y=country_data[y_axis_variable],  # CO2 per Capita on Y-Axis
            mode="markers",  # Only markers (no lines)
            name=f"{country} {x_axis_variable} vs {y_axis_variable}",
            marker=dict(size=8)  # Adjust size of points for visibility
        ))

    # --- Add OLS Trendline ---
    X = merged_df[[x_axis_variable]]  # Independent variable (selected X-Axis)
    X = sm.add_constant(X)  # Add constant term for OLS (intercept)
    y = merged_df[y_axis_variable]  # Dependent variable (CO2 per Capita)

    model = sm.OLS(y, X).fit()
    trendline = model.predict(X)  # Predicted values (trendline)

    # Add the OLS trendline to the scatter plot
    fig.add_trace(go.Scatter(
        x=merged_df[x_axis_variable],  # Selected X-Axis for OLS line
        y=trendline,  # Predicted CO2 per Capita values
        mode="lines",
        name="OLS Trendline",
        line=dict(color="white", dash="dash")  # Set line color to white (or any other color)
    ))

    # Update layout and axis titles
    fig.update_layout(
        title=f"{x_axis_variable} vs {y_axis_variable} (Scatter Plot)",
        xaxis_title=x_axis_variable,  # Selected X-Axis variable title
        yaxis_title=y_axis_variable,  # CO2 per Capita title
        template="plotly_dark"
    )

    # Display the plot
    st.plotly_chart(fig, use_container_width=True)
