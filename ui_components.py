import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
import plotly.express as px
from utilsfe import customer_continent_graph


def image_to_base64(buf):
    return base64.b64encode(buf.getvalue()).decode()


plt.rcParams['figure.dpi'] = 600  # Higher DPI for display in Streamlit
plt.rcParams['savefig.dpi'] = 600 # Higher DPI if you were to save the figure

def display_data_preview(df):
    """Displays a preview of the DataFrame."""
    st.write("### Preview:", df.head())

def display_clustered_data(clustered_df):
    """Displays the clustered DataFrame."""
    st.write("### Clustered Data")
    st.dataframe(clustered_df)


def create_and_display_heatmap(clustered_df):
    st.write("### Customer Distribution Heatmap")

    heatmap_data = clustered_df.set_index('Country')[['Premium', 'Frequent', 'Budget']]
    heatmap_data['Total'] = heatmap_data.sum(axis=1)
    heatmap_data = heatmap_data.sort_values('Total', ascending=False).drop('Total', axis=1)

    # Figure size: width reduced to limit horizontal length
    # Height scaled by number of countries (rows)
    fig_width = 5  # in inches, smaller width to reduce horizontal length
    fig_height = max(4, len(heatmap_data) * 0.35)  # dynamic height
    
    fig, ax = plt.subplots(figsize=(fig_width, fig_height))

    sns.heatmap(
        heatmap_data,
        annot=True,
        fmt='d',
        cmap='Blues',
        cbar_kws={'label': 'Number of Customers'},
        linewidths=0.5,
        linecolor='white',
        ax=ax,
        annot_kws={"size": 8}
    )

    ax.set_title('Customer Distribution by Country and Cluster', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Customer Clusters', fontsize=12, fontweight='bold')
    ax.set_ylabel('Countries', fontsize=12, fontweight='bold')

    ax.xaxis.tick_top()
    ax.xaxis.set_label_position('top')

    plt.xticks(rotation=0)
    plt.yticks(rotation=0)
    plt.tight_layout()

    buf = io.BytesIO()

    # DPI controls image quality and file size/render time
    # Typical DPI range:
    # - Low quality: 72 dpi (fast render, lower detail)
    # - Medium quality: 150 dpi (balanced)
    # - High quality: 300 dpi (sharp, but slower render)
    dpi_setting = 300  # Change to 150 or 72 to speed up rendering if needed

    fig.savefig(buf, format='png', dpi=dpi_setting, bbox_inches='tight')
    plt.close(fig)
    buf.seek(0)

    b64 = image_to_base64(buf)

    # Center image with fixed width
    # Adjust width here to control horizontal size (in pixels)
    display_width_px = 600  # reduce length a bit, increase if you want bigger

    st.markdown(
        f"""
        <div style="display: flex; justify-content: center;">
            <img src="data:image/png;base64,{b64}" style="width:{display_width_px}px; border-radius: 15px;"/>
        </div>
        """,
        unsafe_allow_html=True,
    )

    return heatmap_data

def display_summary_statistics(heatmap_data):
    """Displays key summary statistics."""
    st.write("### Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Countries", len(heatmap_data))
    with col2:
        st.metric("Premium Customers", heatmap_data['Premium'].sum())
    with col3:
        st.metric("Frequent Customers", heatmap_data['Frequent'].sum())
    with col4:
        st.metric("Budget Customers", heatmap_data['Budget'].sum())

def display_top_countries_by_cluster(heatmap_data):
    """Displays the top countries for each customer cluster."""
    st.write("### Top Countries by Cluster")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**Premium Cluster**")
        top_premium = heatmap_data.nlargest(5, 'Premium')['Premium']
        for country, count in top_premium.items():
            if count > 0:
                st.write(f"• {country}: {count}")

    with col2:
        st.write("**Frequent Cluster**")
        top_frequent = heatmap_data.nlargest(5, 'Frequent')['Frequent']
        for country, count in top_frequent.items():
            if count > 0:
                st.write(f"• {country}: {count}")

    with col3:
        st.write("**Budget Cluster**")
        top_budget = heatmap_data.nlargest(5, 'Budget')['Budget']
        for country, count in top_budget.items():
            if count > 0:
                st.write(f"• {country}: {count}")

def process_and_display_results(result):
    """
    Processes the raw clustering result and displays the clustered data,
    heatmap, summary statistics, and top countries by cluster.
    """
    try:
        # Convert to DataFrame format
        clustered_df = pd.DataFrame.from_dict(result, orient='index')

        # Reset index to make country names a column
        clustered_df.reset_index(inplace=True)
        clustered_df.rename(columns={'index': 'Country'}, inplace=True)

        # Rename cluster columns with descriptive names
        cluster_names = {
            '0': 'Premium',
            '1': 'Frequent',
            '2': 'Budget'
        }
        clustered_df.rename(columns=cluster_names, inplace=True)

        display_clustered_data(clustered_df)

        heatmap_data = create_and_display_heatmap(clustered_df)

        display_summary_statistics(heatmap_data)

        display_top_countries_by_cluster(heatmap_data)

    except Exception as e:
        st.error(f"Error processing clustering results: {str(e)}")
        st.write("### Raw Results")
        st.json(result)

import plotly.express as px
import streamlit as st

def render_user_chart(df):
    """Render a pie chart for continent data."""
    st.markdown("---")
    st.subheader("🌍 Continent Data (Pie Chart)")

    cdata = customer_continent_graph(df)

    fig = px.pie(
        cdata,
        names='Continent',
        values='Customer_Count',
        color='Continent',
        color_discrete_sequence=px.colors.qualitative.Set3,
        title='Customer Distribution by Continent',
        hole=0.3  # optional: donut chart effect
    )

    fig.update_traces(textposition='inside', textinfo='percent+label')

    fig.update_layout(
        title_x=0.5,
        showlegend=True,
        legend_title="Continent",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )

    st.plotly_chart(fig, use_container_width=True)

def render_backend_continent_analysis(continent_data):
    """
    Render continent analysis pie charts using backend data.
    """
    st.markdown("---")
    st.subheader("🌍 Continent Analysis")

    # Convert backend data to DataFrame
    data_list = []
    for continent, metrics in continent_data.items():
        data_list.append({
            'Continent': continent,
            'Customer_Count': metrics['customer_count'],
            'Total_Revenue': metrics['total_revenue']
        })

    df_continent = pd.DataFrame(data_list)
    df_continent = df_continent.sort_values('Total_Revenue', ascending=False)

    # Create two columns for side-by-side charts
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("👥 Customer Distribution")
        fig1 = px.pie(
            df_continent,
            names='Continent',
            values='Customer_Count',
            color='Continent',
            color_discrete_sequence=px.colors.qualitative.Set3,
            title="Customer Count by Continent"
        )
        fig1.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig1, use_container_width=True)

    with col2:
        st.subheader("💰 Revenue Distribution")
        fig2 = px.pie(
            df_continent,
            names='Continent',
            values='Total_Revenue',
            color='Continent',
            color_discrete_sequence=px.colors.qualitative.Pastel,
            title="Revenue by Continent"
        )
        fig2.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig2, use_container_width=True)

    # Summary metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        total_customers = df_continent['Customer_Count'].sum()
        st.metric("Total Customers", f"{total_customers:,}")

    with col2:
        total_revenue = df_continent['Total_Revenue'].sum()
        st.metric("Total Revenue", f"${total_revenue:,.2f}")

    with col3:
        avg_revenue_per_customer = total_revenue / total_customers if total_customers > 0 else 0
        st.metric("Avg Revenue/Customer", f"${avg_revenue_per_customer:.2f}")
