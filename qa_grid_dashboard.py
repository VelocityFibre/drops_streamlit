import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
import time
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode

# Agent list
AGENTS = ['Unallocated', 'Zander', 'Michael']

# Database configuration
DATABASE_URL = "postgresql://neondb_owner:npg_RIgDxzo4St6d@ep-damp-credit-a857vku0-pooler.eastus2.azure.neon.tech/neondb?sslmode=require&channel_binding=require"

# Configure Streamlit page
st.set_page_config(
    page_title="QA Photo Reviews - Grid Dashboard",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for AG Grid styling
st.markdown("""
<style>
    .stDataFrame {
        border: 1px solid #ddd;
        border-radius: 8px;
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .grid-container {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    .refresh-indicator {
        position: fixed;
        top: 80px;
        right: 20px;
        background: #4CAF50;
        color: white;
        padding: 8px 16px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 1000;
    }
    .status-complete { background-color: #d4edda !important; color: #155724; }
    .status-warning { background-color: #fff3cd !important; color: #856404; }
    .status-danger { background-color: #f8d7da !important; color: #721c24; }
</style>
""", unsafe_allow_html=True)

def get_database_connection():
    """Create and return database connection."""
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        st.error(f"Failed to connect to database: {str(e)}")
        return None

def get_qa_reviews_data():
    """Fetch all QA reviews data with proper error handling."""
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
            conn.close()
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
            if conn:
                conn.close()
            return False
    return False

def update_step_status(record_id, step_column, status):
    """Update step status for a specific record."""
    conn = get_database_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE qa_photo_reviews 
                SET {step_column} = %s, updated_at = NOW() 
                WHERE id = %s
            """, (status, record_id))
            conn.commit()
            cursor.close()
            conn.close()
            return True
        except Exception as e:
            st.error(f"Error updating step status: {str(e)}")
            if conn:
                conn.close()
            return False
    return False

def prepare_grid_data(df):
    """Prepare data for AG Grid display."""
    if df.empty:
        return pd.DataFrame()
    
    # Create a copy for display
    grid_df = df.copy()
    
    # Format dates
    grid_df['review_date'] = pd.to_datetime(grid_df['review_date']).dt.strftime('%Y-%m-%d')
    grid_df['created_at'] = pd.to_datetime(grid_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Convert boolean columns to checkboxes (True/False for AG Grid)
    step_columns = [col for col in grid_df.columns if col.startswith('step_')]
    for col in step_columns:
        grid_df[col] = grid_df[col].astype(bool)
    
    # Add status column based on outstanding photos
    def get_status(outstanding):
        if outstanding == 0:
            return "Complete"
        elif outstanding <= 3:
            return "Warning"
        else:
            return "Urgent"
    
    grid_df['status'] = grid_df['outstanding_photos'].apply(get_status)
    
    return grid_df

def configure_grid_options(df):
    """Configure AG Grid options."""
    gb = GridOptionsBuilder.from_dataframe(df)
    
    # Configure general grid options
    gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=50)
    gb.configure_side_bar()
    gb.configure_selection(selection_mode="multiple", use_checkbox=True)
    gb.configure_default_column(
        groupable=True, 
        value=True, 
        enableRowGroup=True, 
        aggFunc="sum", 
        editable=False,
        resizable=True,
        sortable=True,
        filter=True
    )
    
    # Configure specific columns
    # Drop Number - pinned left and emphasized
    gb.configure_column("drop_number", 
                       header_name="Drop Number",
                       width=120,
                       pinned="left",
                       cellStyle={"font-weight": "bold"})
    
    # Agent assignment - editable dropdown
    gb.configure_column("assigned_agent", 
                       header_name="Agent",
                       width=120,
                       editable=True,
                       cellEditor='agSelectCellEditor',
                       cellEditorParams={'values': AGENTS})
    
    # Status column with conditional formatting
    status_cell_style = JsCode("""
    function(params) {
        if (params.value == 'Complete') {
            return {'background-color': '#d4edda', 'color': '#155724'};
        } else if (params.value == 'Warning') {
            return {'background-color': '#fff3cd', 'color': '#856404'};
        } else if (params.value == 'Urgent') {
            return {'background-color': '#f8d7da', 'color': '#721c24'};
        }
        return {};
    }
    """)
    
    gb.configure_column("status",
                       header_name="Status",
                       width=100,
                       cellStyle=status_cell_style)
    
    # Photo metrics
    gb.configure_column("completed_photos", header_name="Completed", width=100)
    gb.configure_column("outstanding_photos", header_name="Outstanding", width=100)
    
    # Step columns as checkboxes
    step_columns = [col for col in df.columns if col.startswith('step_')]
    for col in step_columns:
        step_num = col.split('_')[1]
        gb.configure_column(col, 
                           header_name=f"S{step_num}",
                           width=60,
                           editable=True,
                           cellRenderer='agCheckboxCellRenderer',
                           cellEditor='agCheckboxCellEditor')
    
    # Other columns
    gb.configure_column("user_name", header_name="User", width=120)
    gb.configure_column("review_date", header_name="Date", width=100)
    gb.configure_column("comment", header_name="Comment", width=200, wrapText=True, autoHeight=True)
    gb.configure_column("outstanding_photos_loaded_to_1map", 
                       header_name="1Map", 
                       width=80,
                       cellRenderer='agCheckboxCellRenderer')
    
    # Hide ID column but keep it for updates
    gb.configure_column("id", hide=True)
    
    return gb.build()

def main():
    # Initialize session state for refresh control
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = time.time()
    
    # Header with auto-refresh indicator
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.title("📋 QA Photo Reviews - Grid Dashboard")
        st.markdown("### Interactive Spreadsheet View with Real-time Updates")
    
    with col2:
        auto_refresh = st.checkbox("🔄 Auto Refresh (10s)", value=False, key="auto_refresh")
        if auto_refresh:
            current_time = time.time()
            time_since_refresh = current_time - st.session_state.last_refresh
            st.caption(f"Last updated: {int(time_since_refresh)}s ago")
    
    with col3:
        if st.button("🔄 Refresh Now"):
            st.cache_data.clear()
            st.session_state.last_refresh = time.time()
            st.rerun()
    
    # Sidebar controls
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
    
    # Load data with improved caching
    @st.cache_data(ttl=30 if auto_refresh else 300)
    def cached_get_data():
        return get_qa_reviews_data()
    
    df = cached_get_data()
    
    if df.empty:
        st.warning("No QA review data found in the database.")
        return
    
    # Sidebar filters
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
    
    # Status filter
    status_filter = st.sidebar.selectbox(
        "Status Filter:",
        ["All", "Complete", "Warning", "Urgent"]
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
    
    # Status filter
    if status_filter != 'All':
        if status_filter == 'Complete':
            filtered_df = filtered_df[filtered_df['outstanding_photos'] == 0]
        elif status_filter == 'Warning':
            filtered_df = filtered_df[(filtered_df['outstanding_photos'] > 0) & (filtered_df['outstanding_photos'] <= 3)]
        elif status_filter == 'Urgent':
            filtered_df = filtered_df[filtered_df['outstanding_photos'] > 3]
    
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
        urgent_count = len(filtered_df[filtered_df['outstanding_photos'] > 3])
        st.metric("Urgent (>3)", urgent_count)
    
    # Main AG Grid
    st.markdown("### 📋 Interactive Data Grid")
    st.markdown("*Click on cells to edit • Use filters and sorting • Select multiple rows with checkboxes*")
    
    if not filtered_df.empty:
        # Prepare data for grid
        grid_df = prepare_grid_data(filtered_df)
        
        # Configure grid options
        grid_options = configure_grid_options(grid_df)
        
        # Display grid with the container styling
        with st.container():
            st.markdown('<div class="grid-container">', unsafe_allow_html=True)
            
            # Display the AG Grid
            grid_response = AgGrid(
                grid_df,
                gridOptions=grid_options,
                height=600,
                width='100%',
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                fit_columns_on_grid_load=False,
                allow_unsafe_jscode=True,
                enable_enterprise_modules=True,
                theme='streamlit'
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle grid updates
        if grid_response['data'] is not None:
            updated_df = pd.DataFrame(grid_response['data'])
            
            # Check for changes in agent assignments
            if not updated_df.empty and len(updated_df) == len(grid_df):
                for idx, (original_row, updated_row) in enumerate(zip(grid_df.itertuples(), updated_df.itertuples())):
                    # Check agent assignment changes
                    if hasattr(updated_row, 'assigned_agent') and hasattr(original_row, 'assigned_agent'):
                        if updated_row.assigned_agent != original_row.assigned_agent:
                            record_id = original_row.id
                            if update_agent_assignment(record_id, updated_row.assigned_agent):
                                st.success(f"Updated agent for {original_row.drop_number} to {updated_row.assigned_agent}")
                                if not auto_refresh:
                                    st.cache_data.clear()
                                    time.sleep(1)
                                    st.rerun()
                    
                    # Check step status changes
                    step_columns = [col for col in updated_df.columns if col.startswith('step_')]
                    for step_col in step_columns:
                        if hasattr(updated_row, step_col) and hasattr(original_row, step_col):
                            original_val = getattr(original_row, step_col)
                            updated_val = getattr(updated_row, step_col)
                            if updated_val != original_val:
                                record_id = original_row.id
                                if update_step_status(record_id, step_col, updated_val):
                                    st.success(f"Updated {step_col} for {original_row.drop_number}")
                                    if not auto_refresh:
                                        st.cache_data.clear()
                                        time.sleep(1)
                                        st.rerun()
        
        # Selection info
        selected_rows = grid_response['selected_rows']
        if selected_rows:
            st.markdown("### 📑 Selected Rows")
            st.markdown(f"**{len(selected_rows)} rows selected**")
            
            # Show selected drops
            selected_drops = [row['drop_number'] for row in selected_rows]
            st.write("Selected drop numbers:", ", ".join(selected_drops))
            
            # Bulk operations
            st.markdown("#### 🔄 Bulk Operations")
            col1, col2 = st.columns(2)
            
            with col1:
                bulk_agent = st.selectbox("Assign Agent to Selected:", AGENTS, key="bulk_agent")
                if st.button("Apply Bulk Agent Assignment"):
                    success_count = 0
                    for row in selected_rows:
                        if update_agent_assignment(row['id'], bulk_agent):
                            success_count += 1
                    
                    if success_count > 0:
                        st.success(f"Updated {success_count} records to agent: {bulk_agent}")
                        if not auto_refresh:
                            st.cache_data.clear()
                            time.sleep(1)
                            st.rerun()
    
    # Auto-refresh implementation with better timing
    if auto_refresh:
        current_time = time.time()
        time_since_refresh = current_time - st.session_state.last_refresh
        
        # Only refresh if 10 seconds have passed
        if time_since_refresh >= 10:
            st.session_state.last_refresh = current_time
            st.cache_data.clear()
            st.rerun()
        else:
            # Wait for remaining time, but don't block UI
            time.sleep(1)  # Just a small sleep to prevent excessive CPU usage
            st.rerun()

if __name__ == "__main__":
    main()