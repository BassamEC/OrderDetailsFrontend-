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

# Add these functions to your existing ui_components.py file

import io
from utilsfe import fetch_customer_details_from_blob

def render_potential_customers_results(result, company_df):
    """Render potential customers analysis results"""
    if "error" in result:
        st.error(f"Error: {result['error']}")
        return
    
    # Process the backend result (product_name -> list of customer IDs)
    all_customer_ids = set()
    product_stats = []
    
    for product_name, customer_ids in result.items():
        # Convert float IDs to integers for matching
        customer_ids_int = [int(float(id)) for id in customer_ids]
        all_customer_ids.update(customer_ids_int)
        
        product_stats.append({
            "ProductName": product_name,
            "CustomerCount": len(customer_ids_int),
            "CustomerIDs": customer_ids_int
        })
    
    # Display summary statistics only if there are potential customers
    if len(all_customer_ids) > 0:
        st.subheader("📊 Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Potential Customers", len(all_customer_ids))
        with col2:
            st.metric("Products Analyzed", len(result))
        with col3:
            avg_customers_per_product = len(all_customer_ids) / len(result) if result else 0
            st.metric("Avg Customers per Product", f"{avg_customers_per_product:.1f}")
    else:
        st.info("🔍 No potential customers found for the selected products.")
    
    # Get customer details from the company dataframe first
    customer_id_columns = ['CustomerID', 'ID', 'customer_id', 'id']
    customer_id_col = None
    
    for col in customer_id_columns:
        if col in company_df.columns:
            customer_id_col = col
            break
    
    potential_customers_df = pd.DataFrame()
    missing_customer_ids = []
    
    if customer_id_col:
        # Filter company data to get details for potential customers
        company_customers = company_df[company_df[customer_id_col].isin(all_customer_ids)].copy()
        
        if not company_customers.empty:
            potential_customers_df = company_customers
            
            # Find missing customer IDs (not in company data)
            found_ids = set(company_customers[customer_id_col].unique())
            missing_customer_ids = list(all_customer_ids - found_ids)
        else:
            missing_customer_ids = list(all_customer_ids)
    else:
        missing_customer_ids = list(all_customer_ids)
    
    # If there are missing customers, fetch automatically (no button)
    if missing_customer_ids:
        with st.spinner("Fetching missing customer details from database..."):
            blob_result = fetch_customer_details_from_blob(missing_customer_ids)

        if "error" in blob_result:
            st.error(f"Error fetching customer details: {blob_result['error']}")
        else:
            if "customers" in blob_result and blob_result["customers"]:
                blob_customers_df = pd.DataFrame(blob_result["customers"])
                if not potential_customers_df.empty:
                    potential_customers_df = pd.concat([potential_customers_df, blob_customers_df], ignore_index=True)
                else:
                    potential_customers_df = blob_customers_df

                # Calculate unique customers after deduplication
                customer_id_for_count = None
                for col in ['CustomerID', 'ID', 'customer_id', 'id']:
                    if col in potential_customers_df.columns:
                        customer_id_for_count = col
                        break
                
                if customer_id_for_count:
                    unique_count = potential_customers_df[customer_id_for_count].nunique()
                else:
                    unique_count = len(potential_customers_df.drop_duplicates())
                
                st.success(f"✅ Fetched details for {unique_count} unique additional customers!")
            else:
                st.warning("No additional customer details found in database.")    
    
    # Display customer details if we have any
    if not potential_customers_df.empty:
        st.subheader("🎯 Potential Customers Details")
        
        # Define required columns
        required_columns = ['CustomerID', 'FirstName', 'LastName', 'City', 'Country', 'Phone']
        
        # Check for alternative column names and create a mapping
        column_mapping = {}
        for req_col in required_columns:
            if req_col in potential_customers_df.columns:
                column_mapping[req_col] = req_col
            else:
                # Check for alternative names
                alternatives = {
                    'CustomerID': ['ID', 'customer_id', 'id'],
                    'FirstName': ['first_name', 'First_Name', 'fname'],
                    'LastName': ['last_name', 'Last_Name', 'lname'],
                    'City': ['city'],
                    'Country': ['country'],
                    'Phone': ['phone', 'Phone_Number', 'PhoneNumber']
                }
                
                found = False
                for alt_name in alternatives.get(req_col, []):
                    if alt_name in potential_customers_df.columns:
                        column_mapping[req_col] = alt_name
                        found = True
                        break
                
                if not found:
                    column_mapping[req_col] = None
        
        # Create display dataframe with only required columns
        display_columns = []
        for req_col in required_columns:
            if column_mapping[req_col] is not None:
                display_columns.append(column_mapping[req_col])
        
        if display_columns:
            # Select only the required columns
            display_df = potential_customers_df[display_columns].copy()
            
            # Rename columns to standard names
            rename_dict = {v: k for k, v in column_mapping.items() if v is not None}
            display_df = display_df.rename(columns=rename_dict)
            
            # Ensure we have the CustomerID column for deduplication
            customer_id_for_dedup = None
            for col in ['CustomerID', 'ID', 'customer_id', 'id']:
                if col in display_df.columns:
                    customer_id_for_dedup = col
                    break
            
            # Remove duplicates based on CustomerID
            if customer_id_for_dedup:
                display_df = display_df.drop_duplicates(subset=[customer_id_for_dedup])
            else:
                # If no CustomerID column, remove duplicates based on all columns
                display_df = display_df.drop_duplicates()
            
            # Display filters
            col1, col2 = st.columns(2)
            with col1:
                if "Country" in display_df.columns:
                    countries = ["All"] + sorted(display_df["Country"].dropna().unique().tolist())
                    selected_country = st.selectbox("Filter by Country", countries)
                else:
                    selected_country = "All"
            
            with col2:
                if "City" in display_df.columns:
                    cities = ["All"] + sorted(display_df["City"].dropna().unique().tolist())
                    selected_city = st.selectbox("Filter by City", cities)
                else:
                    selected_city = "All"
            
            # Apply filters
            filtered_df = display_df.copy()
            if selected_country != "All" and "Country" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["Country"] == selected_country]
            if selected_city != "All" and "City" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["City"] == selected_city]
            
            # Display filtered results
            st.write(f"Showing {len(filtered_df)} unique potential customers")
            
            st.dataframe(
                filtered_df,
                use_container_width=True,
                hide_index=True
            )
            
            # Download and Phone Numbers buttons
            col1, col2 = st.columns(2)
            
            with col1:
                # Download button
                csv_buffer = io.StringIO()
                filtered_df.to_csv(csv_buffer, index=False)
                st.download_button(
                    label="📥 Download Customer List (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name=f"potential_customers_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Phone Numbers button
                if "Phone" in filtered_df.columns:
                    phone_numbers = filtered_df["Phone"].dropna().unique()
                    if len(phone_numbers) > 0:
                        phone_list = "\n".join(phone_numbers.astype(str))
                        st.download_button(
                            label="📞 Download Phone Numbers",
                            data=phone_list,
                            file_name=f"customer_phones_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.button("📞 No Phone Numbers", disabled=True)
                else:
                    st.button("📞 Phone Numbers Not Available", disabled=True)
            
            # Show phone numbers in expandable section
            if "Phone" in filtered_df.columns:
                with st.expander("📞 View Phone Numbers"):
                    phone_columns = ["FirstName", "LastName", "Phone", "Country"]
                    available_phone_columns = [col for col in phone_columns if col in filtered_df.columns]
                    
                    if available_phone_columns:
                        phone_data = filtered_df[available_phone_columns].copy()
                        phone_data = phone_data.dropna(subset=["Phone"])
                        
                        if not phone_data.empty:
                            st.dataframe(phone_data, use_container_width=True, hide_index=True)
                            st.write(f"Total unique phone numbers: {len(phone_data)}")
                        else:
                            st.write("No phone numbers available for the filtered customers.")
                    else:
                        st.write("Phone number columns not available.")
        else:
            st.warning("Required columns (CustomerID, FirstName, LastName, City, Country, Phone) not found in the data.")
    
    else:
        # Check if we have any customer IDs at all
        if all_customer_ids:
            st.warning("No customer details available. Try fetching from the database using the button above.")
    
    # Display product-wise breakdown
    if product_stats and any(stat['CustomerCount'] > 0 for stat in product_stats):
        st.subheader("📦 Product-wise Breakdown")
        
        breakdown_df = pd.DataFrame(product_stats)
        
        # Display breakdown table
        st.dataframe(
            breakdown_df[["ProductName", "CustomerCount"]], 
            use_container_width=True, 
            hide_index=True
        )
        
        # Show customers interested in each product
        with st.expander("👥 Customers by Product Interest"):
            for product_stat in product_stats:
                st.write(f"**{product_stat['ProductName']}** ({product_stat['CustomerCount']} customers)")
                
                # Get customer details for this product
                product_customer_ids = product_stat['CustomerIDs']
                
                # Check if there are any customer IDs for this product
                if not product_customer_ids:
                    st.write("❌ No leads for this product")
                    st.write("---")  # Separator between products
                    continue
                
                if not potential_customers_df.empty:
                    # Find the customer ID column
                    customer_id_for_filter = None
                    for col in ['CustomerID', 'ID', 'customer_id', 'id']:
                        if col in potential_customers_df.columns:
                            customer_id_for_filter = col
                            break
                    
                    if customer_id_for_filter:
                        # Filter customers for this product
                        product_customers = potential_customers_df[
                            potential_customers_df[customer_id_for_filter].isin(product_customer_ids)
                        ].copy()
                        
                        # Select only name and phone columns
                        display_columns = []
                        column_mapping = {}
                        
                        # Map FirstName
                        for col in ['FirstName', 'first_name', 'First_Name', 'fname']:
                            if col in product_customers.columns:
                                display_columns.append(col)
                                column_mapping[col] = 'FirstName'
                                break
                        
                        # Map LastName
                        for col in ['LastName', 'last_name', 'Last_Name', 'lname']:
                            if col in product_customers.columns:
                                display_columns.append(col)
                                column_mapping[col] = 'LastName'
                                break
                        
                        # Map Phone
                        for col in ['Phone', 'phone', 'Phone_Number', 'PhoneNumber']:
                            if col in product_customers.columns:
                                display_columns.append(col)
                                column_mapping[col] = 'Phone'
                                break
                        
                        if display_columns:
                            product_display = product_customers[display_columns].copy()
                            product_display = product_display.rename(columns=column_mapping)
                            
                            # Remove duplicates
                            product_display = product_display.drop_duplicates()
                            
                            # Sort by name for better readability
                            if 'FirstName' in product_display.columns:
                                product_display = product_display.sort_values('FirstName')
                            
                            st.dataframe(
                                product_display,
                                use_container_width=True,
                                hide_index=True
                            )
                        else:
                            st.write("Customer details not available for this product.")
                    else:
                        st.write("Customer ID column not found.")
                else:
                    st.write("No customer details available.")
                
                st.write("---")  # Separator between products
                
def get_available_products(df):
    """Get list of available products from the dataframe"""
    if "ProductName" in df.columns:
        return sorted(df["ProductName"].dropna().unique().tolist())
    return []
