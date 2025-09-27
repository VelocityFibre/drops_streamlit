# Technical Documentation - QA Photo Reviews Dashboard

## 🔧 Implementation Details

### Application Architecture

The QA Photo Reviews Dashboard is built using Streamlit, a Python web framework designed for data applications. The architecture follows a simple client-server model with direct database connectivity.

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   PostgreSQL     │    │   Streamlit     │
│   Frontend      │◄──►│   Database       │◄──►│   Cloud         │
│   (Browser)     │    │   (Neon)         │    │   (Hosting)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Database Schema

The application connects to two main database tables:

#### `qa_photo_reviews` Table
```sql
- id (Primary Key)
- drop_number (VARCHAR)
- review_date (DATE)
- user_name (VARCHAR)
- assigned_agent (VARCHAR)
- step_01_property_frontage (BOOLEAN)
- step_02_location_before_install (BOOLEAN)
- step_03_outside_cable_span (BOOLEAN)
- step_04_home_entry_outside (BOOLEAN)
- step_05_home_entry_inside (BOOLEAN)
- step_06_fibre_entry_to_ont (BOOLEAN)
- step_07_patched_labelled_drop (BOOLEAN)
- step_08_work_area_completion (BOOLEAN)
- step_09_ont_barcode_scan (BOOLEAN)
- step_10_ups_serial_number (BOOLEAN)
- step_11_powermeter_reading (BOOLEAN)
- step_12_powermeter_at_ont (BOOLEAN)
- step_13_active_broadband_light (BOOLEAN)
- step_14_customer_signature (BOOLEAN)
- completed_photos (INTEGER)
- outstanding_photos (INTEGER)
- outstanding_photos_loaded_to_1map (INTEGER)
- comment (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### `qa_review_steps` Table
```sql
- step_number (INTEGER)
- step_title (VARCHAR)
- step_description (TEXT)
```

### Key Functions and Components

#### Database Connectivity
```python
def get_database_connection():
    """Create and return database connection."""
    # Uses psycopg2 with connection string
    # No connection pooling (creates fresh connections)
```

#### Data Fetching
```python
@st.cache_data(ttl=300)
def get_qa_reviews_data():
    """Fetch all QA reviews data with 5-minute cache."""
    # Cached for performance
    # TTL of 300 seconds (5 minutes)
```

#### Agent Management
```python
def update_agent_assignment(record_id, new_agent):
    """Update agent assignment for a specific record."""
    # Direct database UPDATE operations
    # Real-time updates with immediate commit
```

### Streamlit Components

#### Page Configuration
- **Layout**: Wide layout for dashboard view
- **Page Icon**: 📸 (camera emoji)
- **Sidebar**: Expanded by default with controls
- **Theme**: Custom CSS for enhanced styling

#### Interactive Elements
- **Filters**: Date range picker, agent selector, user filter
- **Data Tables**: Interactive DataFrames with conditional formatting
- **Charts**: Plotly-based heatmaps and visualizations
- **Controls**: Refresh button, agent assignment dropdowns

### Performance Considerations

#### Caching Strategy
- **Data Caching**: 5-minute TTL on main data queries
- **Connection Management**: Fresh connections per request (no pooling)
- **Cache Clearing**: Manual refresh button clears all caches

#### Database Optimization
- **Queries**: Single query to fetch all data, filtered in Python
- **Indexing**: Relies on database indexes for performance
- **Connection**: No persistent connections (creates/closes per request)

## 🚀 Deployment Configuration

### Streamlit Cloud Setup

#### App Configuration
```toml
# .streamlit/config.toml
[theme]
backgroundColor = "#FFFFFF"
primaryColor = "#FF6B6B"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"

[server]
maxUploadSize = 200
enableCORS = false
```

#### Dependencies
```txt
streamlit          # 1.x.x (latest)
pandas            # Data manipulation
psycopg2-binary   # PostgreSQL adapter
plotly            # Interactive visualizations  
numpy             # Numerical computing
```

### Git Configuration

#### SSH Key Management
```bash
# Generated key specifically for this repository
ssh-keygen -t ed25519 -f ~/.ssh/drops_streamlit_deploy -C "drops_streamlit_deploy"

# Added to SSH agent
ssh-add ~/.ssh/drops_streamlit_deploy

# SSH config entry for repository-specific authentication
Host github.com-drops-streamlit
  HostName github.com
  User git
  IdentityFile ~/.ssh/drops_streamlit_deploy
  IdentitiesOnly yes
```

#### Remote Configuration
```bash
# Repository URL using custom SSH host
git@github.com-drops-streamlit:VelocityFibre/drops_streamlit.git

# Auto-deploy from master branch to Streamlit Cloud
```

## 🔒 Security Considerations

### Database Security
- **Connection String**: Currently hardcoded (should be moved to secrets)
- **SSL**: Required SSL connection to Neon database
- **Authentication**: Database user/password authentication

### Streamlit Cloud
- **Public Access**: App is publicly accessible (no authentication)
- **Secrets Management**: Can be configured in Streamlit Cloud dashboard
- **HTTPS**: Automatic HTTPS for all deployed apps

### Recommendations
- [ ] Move database credentials to Streamlit secrets
- [ ] Implement basic authentication for sensitive data
- [ ] Add input validation and sanitization
- [ ] Consider IP whitelisting for production use

## 🎯 Code Quality and Standards

### Python Standards
- **PEP 8**: Following Python style guidelines
- **Docstrings**: Function documentation for key methods
- **Error Handling**: Try-catch blocks for database operations
- **Type Hints**: Could be added for better code documentation

### Streamlit Best Practices
- **Caching**: Appropriate use of `@st.cache_data`
- **Session State**: Not currently used (stateless app)
- **Layout**: Proper use of columns and containers
- **User Experience**: Loading states and error messages

### Database Best Practices
- **Connection Management**: Room for improvement (connection pooling)
- **Query Optimization**: Single query approach is efficient
- **Error Handling**: Proper exception handling implemented
- **Transaction Management**: Commits handled appropriately

## 📊 Monitoring and Maintenance

### Application Monitoring
- **Streamlit Cloud Logs**: Available in dashboard
- **Database Performance**: Monitor via Neon dashboard  
- **User Analytics**: Basic usage stats in Streamlit Cloud

### Maintenance Tasks
- **Regular Updates**: Keep dependencies updated
- **Database Maintenance**: Monitor query performance
- **Security Updates**: Update credentials and access controls
- **Backup Strategy**: Database backups via Neon

### Development Workflow
1. **Local Development**: Use `streamlit run` for testing
2. **Version Control**: Git for source control
3. **Testing**: Manual testing before deployment
4. **Deployment**: Automatic via git push
5. **Monitoring**: Check deployment logs and app performance

---

**Last Updated**: September 27, 2025  
**Document Version**: 1.0  
**Review Cycle**: Monthly