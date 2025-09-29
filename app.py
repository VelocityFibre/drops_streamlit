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
    page_title="QA Photo Reviews",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for clean professional look
st.markdown("""
<style>
    /* Hide Streamlit branding and menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Remove padding and margins for full-page feel */
    .main > div {
        padding-top: 1rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    
    /* Clean grid container */
    .grid-container {
        border: 1px solid #e1e5e9;
        border-radius: 4px;
        margin: 0;
        padding: 0;
    }
    
    /* Status colors for grid */
    .status-complete { background-color: #d4edda !important; color: #155724; }
    .status-warning { background-color: #fff3cd !important; color: #856404; }
    .status-danger { background-color: #f8d7da !important; color: #721c24; }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
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

@st.cache_data(ttl=10)  # Cache for 10 seconds
def get_qa_reviews_data():
    """Fetch all QA reviews data with caching."""
    conn = get_database_connection()
    if conn:
        try:
            query = """
            SELECT 
                id, drop_number, review_date, user_name, assigned_agent, project,
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
            if conn:
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
            # Clear cache to get fresh data
            st.cache_data.clear()
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
            # Clear cache to get fresh data
            st.cache_data.clear()
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
    
    grid_df = df.copy()
    
    # Format dates
    grid_df['review_date'] = pd.to_datetime(grid_df['review_date']).dt.strftime('%Y-%m-%d')
    grid_df['created_at'] = pd.to_datetime(grid_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Convert boolean columns for AG Grid
    step_columns = [col for col in grid_df.columns if col.startswith('step_')]
    for col in step_columns:
        grid_df[col] = grid_df[col].astype(bool)
    
    # Add status column
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
    
    # Configure general options
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
        filter=True,
        wrapHeaderText=True,  # Enable header text wrapping
        autoHeaderHeight=True  # Auto adjust header height
    )
    
    # Configure specific columns
    gb.configure_column("drop_number", 
                       header_name="Drop Number",
                       width=130,  # Wider to show full drop number
                       pinned="left",
                       cellStyle={"font-weight": "bold"})
    
    # Project column - important for filtering between Lawley and Velo Test
    gb.configure_column("project", 
                       header_name="Project",
                       width=90,  # Adequate for "Lawley" and "Velo Test"
                       pinned="left",  # Keep it visible
                       cellStyle={"font-weight": "bold", "color": "#0066cc"})
    
    gb.configure_column("assigned_agent", 
                       header_name="Agent",
                       width=100,  # Adequate for agent names
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
                       width=80,  # Compact status column
                       cellStyle=status_cell_style)
    
    # Photo metrics
    gb.configure_column("completed_photos", header_name="Completed", width=90)
    gb.configure_column("outstanding_photos", header_name="Outstanding", width=90)
    
    # Step columns as checkboxes with full descriptive names
    step_columns = [col for col in df.columns if col.startswith('step_')]
    step_labels = {
        'step_01_property_frontage': 'Property Frontage',
        'step_02_location_before_install': 'Location on Wall (Before Install)',
        'step_03_outside_cable_span': 'Outside Cable Span (Pole → Pigtail screw)',
        'step_04_home_entry_outside': 'Home Entry Point – Outside',
        'step_05_home_entry_inside': 'Home Entry Point – Inside',
        'step_06_fibre_entry_to_ont': 'Fibre Entry to ONT (After Install)',
        'step_07_patched_labelled_drop': 'Patched & Labelled Drop',
        'step_08_work_area_completion': 'Overall Work Area After Completion',
        'step_09_ont_barcode_scan': 'ONT Barcode – Scan barcode + photo',
        'step_10_ups_serial_number': 'Mini-UPS Serial Number (Gizzu)',
        'step_11_powermeter_reading': 'Powermeter Reading (Drop/Feeder)',
        'step_12_powermeter_at_ont': 'Powermeter at ONT (Before Activation)',
        'step_13_active_broadband_light': 'Active Broadband Light',
        'step_14_customer_signature': 'Customer Signature'
    }
    
    for col in step_columns:
        header_name = step_labels.get(col, col.replace('_', ' ').title())
        gb.configure_column(col, 
                           header_name=header_name,
                           width=120,  # Optimal width for readability with wrapping
                           editable=True,
                           cellRenderer='agCheckboxCellRenderer',
                           cellEditor='agCheckboxCellEditor',
                           wrapHeaderText=True,  # Allow header text wrapping
                           autoHeaderHeight=True)  # Auto adjust header height
    
    # Other columns with proper widths
    gb.configure_column("user_name", header_name="User", width=100)
    gb.configure_column("review_date", header_name="Date", width=100)
    gb.configure_column("comment", header_name="Comment", width=180, wrapText=True, autoHeight=True)
    gb.configure_column("outstanding_photos_loaded_to_1map", 
                       header_name="1Map", 
                       width=60,
                       cellRenderer='agCheckboxCellRenderer')
    gb.configure_column("created_at", header_name="Created", width=120)
    
    # Hide ID column
    gb.configure_column("id", hide=True)
    
    return gb.build()

def main():
    # Sidebar controls (minimal)
    st.sidebar.header("Filters")
    
    # Auto-refresh option
    auto_refresh = st.sidebar.checkbox("Enable Auto Refresh", value=True)
    
    # Load data
    df = get_qa_reviews_data()
    
    if df.empty:
        st.warning("No QA review data found in the database.")
        return
    
    # Sidebar filters
    
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
    
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df['review_date'] >= date_range[0]) & 
            (filtered_df['review_date'] <= date_range[1])
        ]
    
    if selected_user != 'All':
        filtered_df = filtered_df[filtered_df['user_name'] == selected_user]
    
    if selected_agent != 'All':
        filtered_df = filtered_df[filtered_df['assigned_agent'] == selected_agent]
    
    if status_filter != 'All':
        if status_filter == 'Complete':
            filtered_df = filtered_df[filtered_df['outstanding_photos'] == 0]
        elif status_filter == 'Warning':
            filtered_df = filtered_df[(filtered_df['outstanding_photos'] > 0) & (filtered_df['outstanding_photos'] <= 3)]
        elif status_filter == 'Urgent':
            filtered_df = filtered_df[filtered_df['outstanding_photos'] > 3]
    
    # Main Grid (clean, no headers)
    # Remove all metrics and headers for clean professional look
    
    if not filtered_df.empty:
        grid_df = prepare_grid_data(filtered_df)
        grid_options = configure_grid_options(grid_df)
        
        # Display AG Grid
        with st.container():
            st.markdown('<div class="grid-container">', unsafe_allow_html=True)
            
            grid_response = AgGrid(
                grid_df,
                gridOptions=grid_options,
                height=800,  # Larger height for full page feel
                width='100%',
                data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
                update_mode=GridUpdateMode.MODEL_CHANGED,
                fit_columns_on_grid_load=False,  # Don't auto-fit, use our custom widths
                columns_auto_size_mode='FIT_CONTENTS',  # Size columns to fit content
                allow_unsafe_jscode=True,
                enable_enterprise_modules=True,
                theme='streamlit',
                key='main_grid'  # Add key for stability
            )
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Handle updates
        if grid_response['data'] is not None:
            updated_df = pd.DataFrame(grid_response['data'])
            
            # Process changes
            if not updated_df.empty and len(updated_df) == len(grid_df):
                changes_made = False
                
                for idx, (original_row, updated_row) in enumerate(zip(grid_df.itertuples(), updated_df.itertuples())):
                    # Check agent changes
                    if hasattr(updated_row, 'assigned_agent') and hasattr(original_row, 'assigned_agent'):
                        if updated_row.assigned_agent != original_row.assigned_agent:
                            record_id = original_row.id
                            if update_agent_assignment(record_id, updated_row.assigned_agent):
                                st.success(f"✅ Updated agent for {original_row.drop_number} → {updated_row.assigned_agent}")
                                changes_made = True
                    
                    # Check step changes
                    step_columns = [col for col in updated_df.columns if col.startswith('step_')]
                    for step_col in step_columns:
                        if hasattr(updated_row, step_col) and hasattr(original_row, step_col):
                            original_val = getattr(original_row, step_col)
                            updated_val = getattr(updated_row, step_col)
                            if updated_val != original_val:
                                record_id = original_row.id
                                if update_step_status(record_id, step_col, updated_val):
                                    step_display = step_col.replace('step_', 'Step ')
                                    status = "✅ Completed" if updated_val else "❌ Unchecked"
                                    st.success(f"✅ {step_display} for {original_row.drop_number} → {status}")
                                    changes_made = True
                
                # Only rerun if changes were made
                if changes_made:
                    time.sleep(1)  # Brief pause to show success messages
                    st.rerun()
        
        # Selection info
        selected_rows = grid_response['selected_rows']
        if selected_rows:
            st.markdown("### 📑 Selected Rows")
            col1, col2 = st.columns([2, 1])
            
            with col1:
                selected_drops = [row['drop_number'] for row in selected_rows]
                st.write(f"**{len(selected_rows)} drops selected:** {', '.join(selected_drops[:5])}" + 
                        (f" ...and {len(selected_rows)-5} more" if len(selected_rows) > 5 else ""))
            
            with col2:
                bulk_agent = st.selectbox("Bulk Assign Agent:", AGENTS, key="bulk_agent")
                if st.button("Apply to Selected", key="bulk_apply"):
                    success_count = 0
                    for row in selected_rows:
                        if update_agent_assignment(row['id'], bulk_agent):
                            success_count += 1
                    
                    if success_count > 0:
                        st.success(f"✅ Updated {success_count} records → {bulk_agent}")
                        time.sleep(2)
                        st.rerun()
    
    # Auto-refresh (seamless)
    if auto_refresh:
        # Use a placeholder for seamless refresh
        time.sleep(10)
        st.rerun()

if __name__ == "__main__":
    main()