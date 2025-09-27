import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# Agent list
AGENTS = ['Unallocated', 'Zander', 'Michael']

# Database configuration
DATABASE_URL = "postgresql://neondb_owner:npg_RIgDxzo4St6d@ep-damp-credit-a857vku0-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"

# Configure Streamlit page
st.set_page_config(
    page_title="QA Photo Reviews Dashboard",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stDataFrame {
        border: 1px solid #ddd;
        border-radius: 5px;
    }
    .outstanding-high { background-color: #ffebee !important; }
    .outstanding-medium { background-color: #fff3e0 !important; }
    .outstanding-low { background-color: #e8f5e8 !important; }
    .completed { background-color: #e8f5e8 !important; }
</style>
""", unsafe_allow_html=True)

# Don't cache connections, create fresh ones each time
def get_database_connection():
    """Create and return database connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        return None

@st.cache_data(ttl=300)
def get_qa_reviews_data():
    """Fetch all QA reviews data."""
    conn = get_database_connection()
    if conn:
        try:
            query = """
            SELECT 
                id, drop_number, review_date, user_name, assigned_agent,
                step_01_property_frontage, step_02_location_before_install, 
                step_03_outside_cable_span, step_04_home_entry_outside,
                step_05_home_entry_inside, step_06_fibre_entry_to_ont,
                step_07_patched_labelled_drop, step_08_work_area_completion,
                step_09_ont_barcode_scan, step_10_ups_serial_number,
                step_11_powermeter_reading, step_12_powermeter_at_ont,
                step_13_active_broadband_light, step_14_customer_signature,
                completed_photos, outstanding_photos,
                outstanding_photos_loaded_to_1map, comment,
                created_at, updated_at
            FROM qa_photo_reviews 
            ORDER BY review_date DESC, created_at DESC
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error fetching QA reviews data: {str(e)}")
            return pd.DataFrame()
    return pd.DataFrame()

def update_agent_assignment(record_id, new_agent):
    """Update agent assignment for a specific record."""
    conn = get_database_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE qa_photo_reviews 
                SET assigned_agent = %s, updated_at = NOW() 
                WHERE id = %s
            """, (new_agent, record_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error updating agent assignment: {str(e)}")
            return False
    return False

def get_qa_review_steps():
    """Fetch QA review steps definitions."""
    conn = get_database_connection()
    if conn:
        try:
            query = """
            SELECT step_number, step_title, step_description
            FROM qa_review_steps 
            ORDER BY step_number
            """
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Error fetching QA review steps: {str(e)}")
            return pd.DataFrame()
    return pd.DataFrame()

def format_step_columns(df):
    """Format step columns for better display."""
    step_columns = [col for col in df.columns if col.startswith('step_')]
    
    for col in step_columns:
        df[col] = df[col].apply(lambda x: '✅' if x else '❌')
    
    return df

def create_completion_heatmap(df):
    """Create a heatmap showing completion status by user and date."""
    if df.empty:
        return None
    
    # Pivot data for heatmap
    heatmap_data = df.groupby(['user_name', 'review_date'])['completed_photos'].mean().reset_index()
    heatmap_pivot = heatmap_data.pivot(index='user_name', columns='review_date', values='completed_photos')
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_pivot.values,
        x=[str(date) for date in heatmap_pivot.columns],
        y=heatmap_pivot.index,
        colorscale='RdYlGn',
        zmin=0,
        zmax=14,
        colorbar=dict(title="Completed Photos")
    ))
    
    fig.update_layout(
        title="Photo Completion Heatmap by User and Date",
        xaxis_title="Review Date",
        yaxis_title="User",
        height=400
    )
    
    return fig

def main():
    # Header
    st.title("📸 QA Photo Reviews Dashboard")
    st.markdown("### Fiber Installation Quality Assurance - Photo Completion Tracking")
    
    # Sidebar
    st.sidebar.header("🔧 Dashboard Controls")
    
    # Connection status
    conn = get_database_connection()
    if conn:
        st.sidebar.success("✅ Database Connected")
        conn.close()
    else:
        st.sidebar.error("❌ Database Connection Failed")
        st.error("Cannot connect to the database. Please check your connection.")
        return
    
    # Data refresh
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Load data
    df = get_qa_reviews_data()
    steps_df = get_qa_review_steps()
    
    if df.empty:
        st.warning("No QA review data found in the database.")
        return
    
    # Filter options
    st.sidebar.subheader("🔍 Filters")
    
    # Date range filter
    min_date = df['review_date'].min()
    max_date = df['review_date'].max()
    
    date_range = st.sidebar.date_input(
        "Select Date Range:",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # User filter
    users = ['All'] + sorted(df['user_name'].unique().tolist())
    selected_user = st.sidebar.selectbox("Select User:", users)
    
    # Agent filter
    agents_in_data = ['All'] + sorted(df['assigned_agent'].unique().tolist())
    selected_agent = st.sidebar.selectbox("Filter by Assigned Agent:", agents_in_data)
    
    # Outstanding photos filter
    outstanding_filter = st.sidebar.selectbox(
        "Outstanding Photos:",
        ["All", "Complete (0 outstanding)", "Incomplete (>0 outstanding)", "High Priority (>5 outstanding)"]
    )
    
    # Apply filters
    filtered_df = df.copy()
    
    # Date filter
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['review_date'] >= date_range[0]) & 
            (filtered_df['review_date'] <= date_range[1])
        ]
    
    # User filter
    if selected_user != 'All':
        filtered_df = filtered_df[filtered_df['user_name'] == selected_user]
    
    # Agent filter
    if selected_agent != 'All':
        filtered_df = filtered_df[filtered_df['assigned_agent'] == selected_agent]
    
    # Outstanding filter
    if outstanding_filter == "Complete (0 outstanding)":
        filtered_df = filtered_df[filtered_df['outstanding_photos'] == 0]
    elif outstanding_filter == "Incomplete (>0 outstanding)":
        filtered_df = filtered_df[filtered_df['outstanding_photos'] > 0]
    elif outstanding_filter == "High Priority (>5 outstanding)":
        filtered_df = filtered_df[filtered_df['outstanding_photos'] > 5]
    
    # Summary metrics
    st.markdown("### 📊 Summary Metrics")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_reviews = len(filtered_df)
        st.metric("Total Reviews", total_reviews)
    
    with col2:
        completed_reviews = len(filtered_df[filtered_df['outstanding_photos'] == 0])
        completion_rate = (completed_reviews / total_reviews * 100) if total_reviews > 0 else 0
        st.metric("Completed Reviews", completed_reviews, f"{completion_rate:.1f}%")
    
    with col3:
        avg_completed = filtered_df['completed_photos'].mean() if not filtered_df.empty else 0
        st.metric("Avg Completed Photos", f"{avg_completed:.1f}")
    
    with col4:
        avg_outstanding = filtered_df['outstanding_photos'].mean() if not filtered_df.empty else 0
        st.metric("Avg Outstanding Photos", f"{avg_outstanding:.1f}")
    
    with col5:
        high_priority = len(filtered_df[filtered_df['outstanding_photos'] > 5])
        st.metric("High Priority (>5)", high_priority)
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 Reviews Grid", "📈 Analytics", "🎯 Step Details", "👥 User Performance", "📊 QA Steps Info", "👤 Agent Assignment"
    ])
    
    with tab1:
        st.subheader("QA Photo Reviews Data Grid")
        
        # Display options
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            show_step_details = st.checkbox("Show Individual Step Status", value=False)
        with col2:
            rows_per_page = st.selectbox("Rows per page:", [25, 50, 100, 200], index=1)
        with col3:
            enable_inline_assignment = st.checkbox("Enable Agent Assignment", value=True)
        
        if show_step_details:
            # Show all columns with step details
            display_df = filtered_df.copy()
            display_df = format_step_columns(display_df)
            
            # Reorder columns for better display
            step_cols = [col for col in display_df.columns if col.startswith('step_')]
            other_cols = ['drop_number', 'assigned_agent', 'user_name', 'review_date', 'completed_photos', 'outstanding_photos']
            remaining_cols = [col for col in display_df.columns if col not in step_cols + other_cols]
            
            column_order = other_cols + step_cols + remaining_cols
            display_df = display_df[column_order]
        else:
            # Show summary view
            display_cols = [
                'drop_number', 'assigned_agent', 'user_name', 'review_date', 'completed_photos', 
                'outstanding_photos', 'outstanding_photos_loaded_to_1map', 'comment', 'created_at'
            ]
            display_df = filtered_df[display_cols].copy()
        
        # Interactive display with agent assignment
        if enable_inline_assignment and not display_df.empty:
            st.markdown("**Interactive Agent Assignment View**")
            
            # Add column headers
            header_cols = st.columns([1.5, 1.5, 1, 1, 1, 1, 0.8, 2])
            with header_cols[0]:
                st.markdown("**Drop Number**")
            with header_cols[1]:
                st.markdown("**Assigned Agent**")
            with header_cols[2]:
                st.markdown("**User**")
            with header_cols[3]:
                st.markdown("**Date**")
            with header_cols[4]:
                st.markdown("**Completed**")
            with header_cols[5]:
                st.markdown("**Outstanding**")
            with header_cols[6]:
                st.markdown("**1Map**")
            with header_cols[7]:
                st.markdown("**Comment**")
            
            st.markdown("---")
            
            # Limit to reasonable number of rows for interactive display
            display_limit = min(rows_per_page, 50)  # Max 50 for performance
            limited_df = display_df.head(display_limit).copy()
            
            # Create interactive assignment interface
            for idx, (_, row) in enumerate(limited_df.iterrows()):
                # Create columns for each row
                cols = st.columns([1.5, 1.5, 1, 1, 1, 1, 0.8, 2])  # Adjust column widths
                
                with cols[0]:
                    st.write(f"**{row['drop_number']}**")
                
                with cols[1]:
                    # Agent dropdown
                    current_agent = row['assigned_agent'] if 'assigned_agent' in row else 'Unallocated'
                    agent_key = f"agent_{row['id'] if 'id' in row else idx}_{idx}"
                    
                    try:
                        current_index = AGENTS.index(current_agent)
                    except ValueError:
                        current_index = 0  # Default to 'Unallocated'
                    
                    new_agent = st.selectbox(
                        "Agent:",
                        options=AGENTS,
                        index=current_index,
                        key=agent_key,
                        label_visibility="collapsed"
                    )
                    
                    # Update if changed
                    if new_agent != current_agent and 'id' in row:
                        if st.button(f"Update", key=f"update_{row['id']}_{idx}", type="secondary"):
                            if update_agent_assignment(row['id'], new_agent):
                                st.success(f"Updated to {new_agent}")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error("Update failed")
                
                with cols[2]:
                    st.write(row['user_name'])
                
                with cols[3]:
                    st.write(str(row['review_date']))
                
                with cols[4]:
                    st.metric("", row['completed_photos'], label_visibility="collapsed")
                
                with cols[5]:
                    outstanding = row['outstanding_photos']
                    if outstanding == 0:
                        st.success(f"✅ {outstanding}")
                    elif outstanding <= 3:
                        st.warning(f"⚠️ {outstanding}")
                    else:
                        st.error(f"❌ {outstanding}")
                
                with cols[6]:
                    if row.get('outstanding_photos_loaded_to_1map', False):
                        st.write("✅")
                    else:
                        st.write("❌")
                
                with cols[7]:
                    comment = str(row.get('comment', ''))[:50]
                    if comment and comment != 'nan':
                        st.caption(f"{comment}..." if len(str(row.get('comment', ''))) > 50 else comment)
                    else:
                        st.write("")
                
                st.markdown("---")
            
            if len(display_df) > display_limit:
                st.info(f"Showing first {display_limit} rows of {len(display_df)} total. Use filters to narrow results or disable agent assignment for full table view.")
        
        else:
            # Standard dataframe display
            def highlight_outstanding(row):
                if row['outstanding_photos'] == 0:
                    return ['background-color: #e8f5e8'] * len(row)  # Green for complete
                elif row['outstanding_photos'] <= 3:
                    return ['background-color: #fff3e0'] * len(row)  # Orange for medium
                else:
                    return ['background-color: #ffebee'] * len(row)  # Red for high priority
            
            styled_df = display_df.style.apply(highlight_outstanding, axis=1)
            st.dataframe(styled_df, use_container_width=True, height=600)
        
        # Download options
        col1, col2 = st.columns(2)
        with col1:
            csv = display_df.to_csv(index=False)
            st.download_button(
                "📥 Download Current View (CSV)",
                data=csv,
                file_name=f"qa_reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            if not filtered_df.empty:
                incomplete_df = filtered_df[filtered_df['outstanding_photos'] > 0]
                if not incomplete_df.empty:
                    incomplete_csv = incomplete_df.to_csv(index=False)
                    st.download_button(
                        "📥 Download Incomplete Only (CSV)",
                        data=incomplete_csv,
                        file_name=f"incomplete_reviews_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
    
    with tab2:
        st.subheader("📈 Analytics Dashboard")
        
        if not filtered_df.empty:
            # Completion rate over time
            col1, col2 = st.columns(2)
            
            with col1:
                daily_stats = filtered_df.groupby('review_date').agg({
                    'completed_photos': 'mean',
                    'outstanding_photos': 'mean',
                    'drop_number': 'count'
                }).reset_index()
                daily_stats.columns = ['review_date', 'avg_completed', 'avg_outstanding', 'total_reviews']
                
                fig = px.line(daily_stats, x='review_date', y='avg_completed', 
                             title="Average Completed Photos Over Time",
                             markers=True)
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # Outstanding photos distribution
                outstanding_dist = filtered_df['outstanding_photos'].value_counts().sort_index()
                fig = px.bar(x=outstanding_dist.index, y=outstanding_dist.values,
                            title="Distribution of Outstanding Photos",
                            labels={'x': 'Outstanding Photos', 'y': 'Number of Reviews'})
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
            
            # Completion heatmap
            heatmap_fig = create_completion_heatmap(filtered_df)
            if heatmap_fig:
                st.plotly_chart(heatmap_fig, use_container_width=True)
    
    with tab3:
        st.subheader("🎯 Individual Step Analysis")
        
        if not filtered_df.empty:
            # Calculate completion rates for each step
            step_cols = [col for col in filtered_df.columns if col.startswith('step_')]
            step_completion = {}
            
            for col in step_cols:
                step_num = col.split('_')[1]
                completion_rate = (filtered_df[col].sum() / len(filtered_df)) * 100
                step_completion[f"Step {step_num}"] = completion_rate
            
            # Create bar chart
            steps_df_chart = pd.DataFrame(list(step_completion.items()), 
                                        columns=['Step', 'Completion Rate'])
            
            fig = px.bar(steps_df_chart, x='Step', y='Completion Rate',
                        title="Completion Rate by QA Step",
                        color='Completion Rate',
                        color_continuous_scale='RdYlGn')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Step completion details table
            st.subheader("Step Completion Details")
            step_details = []
            for col in step_cols:
                step_num = int(col.split('_')[1])
                completed = filtered_df[col].sum()
                total = len(filtered_df)
                rate = (completed / total * 100) if total > 0 else 0
                step_details.append({
                    'Step': step_num,
                    'Completed': completed,
                    'Total Reviews': total,
                    'Completion Rate': f"{rate:.1f}%"
                })
            
            step_details_df = pd.DataFrame(step_details)
            st.dataframe(step_details_df, use_container_width=True)
    
    with tab4:
        st.subheader("👥 User Performance Analysis")
        
        if not filtered_df.empty:
            # User performance summary
            user_stats = filtered_df.groupby('user_name').agg({
                'drop_number': 'count',
                'completed_photos': ['mean', 'sum'],
                'outstanding_photos': 'mean'
            }).round(2)
            
            user_stats.columns = ['Total Reviews', 'Avg Completed', 'Total Completed', 'Avg Outstanding']
            user_stats['Completion Rate'] = ((user_stats['Avg Completed'] / 14) * 100).round(1)
            user_stats = user_stats.sort_values('Completion Rate', ascending=False)
            
            st.dataframe(user_stats, use_container_width=True)
            
            # User performance chart
            fig = px.scatter(x=user_stats.index, y=user_stats['Completion Rate'],
                           size=user_stats['Total Reviews'],
                           title="User Performance: Completion Rate vs Review Volume",
                           labels={'x': 'User', 'y': 'Completion Rate (%)'})
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    with tab5:
        st.subheader("📊 QA Steps Reference Guide")
        
        if not steps_df.empty:
            # Display QA steps with descriptions
            for _, row in steps_df.iterrows():
                with st.expander(f"Step {row['step_number']:02d}: {row['step_title']}"):
                    st.write(row['step_description'])
        
        # Step completion matrix
        if not filtered_df.empty:
            st.subheader("Step Completion Matrix")
            
            step_cols = [col for col in filtered_df.columns if col.startswith('step_')]
            matrix_data = []
            
            for _, review in filtered_df.head(20).iterrows():  # Show first 20 for readability
                row_data = [review['drop_number']]
                for col in step_cols:
                    row_data.append('✅' if review[col] else '❌')
                matrix_data.append(row_data)
            
            matrix_df = pd.DataFrame(matrix_data, 
                                   columns=['Drop Number'] + [f"Step {col.split('_')[1]}" for col in step_cols])
            
            st.dataframe(matrix_df, use_container_width=True)
    
    with tab6:
        st.subheader("👤 Agent Assignment Management")
        
        if not filtered_df.empty:
            st.markdown("### Quick Assignment Interface")
            st.markdown("Select records and assign them to agents:")
            
            # Show unallocated items first
            unallocated_df = filtered_df[filtered_df['assigned_agent'] == 'Unallocated'].copy()
            
            if not unallocated_df.empty:
                st.markdown("#### 🔄 Unallocated Drop Numbers")
                st.info(f"Found {len(unallocated_df)} unallocated drop numbers")
                
                # Display unallocated items with assignment dropdowns
                for idx, row in unallocated_df.iterrows():
                    col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 2, 1])
                    
                    with col1:
                        st.write(f"**{row['drop_number']}**")
                    
                    with col2:
                        st.write(f"{row['user_name']} ({row['review_date']})")
                    
                    with col3:
                        outstanding = row['outstanding_photos']
                        if outstanding == 0:
                            st.success("✅ Complete")
                        else:
                            st.error(f"❌ {outstanding} missing")
                    
                    with col4:
                        # Agent selection dropdown
                        key = f"agent_select_{row['id']}"
                        selected_agent = st.selectbox(
                            "Assign to:",
                            options=AGENTS,
                            index=0,  # Default to 'Unallocated'
                            key=key
                        )
                    
                    with col5:
                        # Update button
                        if st.button(f"Update", key=f"update_{row['id']}"):
                            if selected_agent != 'Unallocated':
                                if update_agent_assignment(row['id'], selected_agent):
                                    st.success(f"Assigned {row['drop_number']} to {selected_agent}")
                                    st.cache_data.clear()  # Clear cache to refresh data
                                    st.rerun()
                                else:
                                    st.error("Failed to update assignment")
                    
                    st.markdown("---")
            
            # Summary by agent
            st.markdown("### 📊 Agent Assignment Summary")
            
            agent_summary = filtered_df['assigned_agent'].value_counts()
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Display summary table
                summary_df = pd.DataFrame({
                    'Agent': agent_summary.index,
                    'Assigned Count': agent_summary.values
                })
                st.dataframe(summary_df, use_container_width=True)
            
            with col2:
                # Pie chart of assignments
                fig = px.pie(values=agent_summary.values, names=agent_summary.index,
                            title="Drop Number Assignment Distribution")
                st.plotly_chart(fig, use_container_width=True)
            
            # Show all assignments with ability to reassign
            st.markdown("### 📝 All Assignments (Reassign if needed)")
            
            # Filter options for this section
            col1, col2 = st.columns(2)
            with col1:
                show_agent_filter = st.selectbox(
                    "Show assignments for:",
                    options=['All Agents'] + AGENTS
                )
            
            with col2:
                show_only_incomplete = st.checkbox("Show only incomplete drops", value=False)
            
            # Apply filters
            assignment_df = filtered_df.copy()
            if show_agent_filter != 'All Agents':
                assignment_df = assignment_df[assignment_df['assigned_agent'] == show_agent_filter]
            
            if show_only_incomplete:
                assignment_df = assignment_df[assignment_df['outstanding_photos'] > 0]
            
            # Display assignment table with inline editing
            if not assignment_df.empty:
                st.write(f"Showing {len(assignment_df)} records:")
                
                # Create editable dataframe
                display_assignment_df = assignment_df[[
                    'drop_number', 'assigned_agent', 'user_name', 'review_date', 
                    'completed_photos', 'outstanding_photos', 'comment'
                ]].copy()
                
                # Style the dataframe
                def highlight_assignment(row):
                    if row['assigned_agent'] == 'Unallocated':
                        return ['background-color: #ffebee'] * len(row)  # Red for unallocated
                    elif row['outstanding_photos'] == 0:
                        return ['background-color: #e8f5e8'] * len(row)  # Green for complete
                    else:
                        return ['background-color: #fff3e0'] * len(row)  # Orange for incomplete
                
                styled_assignment_df = display_assignment_df.style.apply(highlight_assignment, axis=1)
                st.dataframe(styled_assignment_df, use_container_width=True, height=400)
            
            else:
                st.info("No records match the current filters.")
        
        else:
            st.info("No data available for agent assignment.")

if __name__ == "__main__":
    main()
