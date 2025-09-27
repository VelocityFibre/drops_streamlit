# QA Photo Reviews Dashboard

A Streamlit web application for tracking and managing Quality Assurance photo reviews for fiber installation projects at VelocityFibre.

## 📋 Project Overview

This dashboard provides a comprehensive interface for monitoring photo completion status across fiber installation QA reviews. It connects to a PostgreSQL database to display real-time data about installation steps, photo completion rates, and agent assignments.

## 🚀 Live Application

The application is deployed on Streamlit Cloud and automatically updates when changes are pushed to the GitHub repository:

- **Repository**: [VelocityFibre/drops_streamlit](https://github.com/VelocityFibre/drops_streamlit)
- **Deployment**: Streamlit Cloud (auto-deploys from `master` branch)
- **Main File**: `qa_photo_reviews_dashboard.py`

## 🏗️ Architecture

```
Local Development → GitHub Repository → Streamlit Cloud → Live Application
      ↓                    ↓                  ↓              ↓
   Code Changes    →    Git Push    →    Auto-Deploy  →   Live Updates
```

## 📁 Project Structure

```
/home/louisdup/VF/Apps/streamlit/
├── qa_photo_reviews_dashboard.py   # Main Streamlit application
├── qa_photo_reviews_schema.sql     # Database schema definition
├── start_dashboard.sh              # Local development script
├── requirements.txt                # Python dependencies
├── .streamlit/
│   └── config.toml                # Streamlit configuration
├── .git/                          # Git repository
└── README.md                      # This documentation
```

## 🔧 Files Description

### Core Files

- **`qa_photo_reviews_dashboard.py`**: Main Streamlit application with dashboard logic, database connections, and UI components
- **`qa_photo_reviews_schema.sql`**: SQL schema for the QA reviews database tables
- **`requirements.txt`**: Python package dependencies for deployment
- **`start_dashboard.sh`**: Shell script for local development server

### Configuration

- **`.streamlit/config.toml`**: Streamlit app configuration settings
- **SSH Keys**: Custom deploy key for this repository (`~/.ssh/drops_streamlit_deploy`)

## 🚦 Development Workflow

### Auto-Deploy Process
1. **Make changes** to your code locally (like `qa_photo_reviews_dashboard.py`)
2. **Commit and push** to GitHub:
   ```bash
   git add .
   git commit -m "Your update message"
   git push
   ```
3. **Streamlit Cloud automatically detects** the changes and redeploys your app
4. **Your hosted app updates** within a few minutes

### Local Development
```bash
# Start local development server
./start_dashboard.sh

# Or run directly with streamlit
streamlit run qa_photo_reviews_dashboard.py
```

## 🔐 SSH Configuration

A dedicated SSH key was created for this repository:
- **Key Name**: `drops_streamlit_deploy`
- **SSH Config Host**: `github.com-drops-streamlit`
- **Remote URL**: `git@github.com-drops-streamlit:VelocityFibre/drops_streamlit.git`

### SSH Config Entry
```
# Drops Streamlit specific
Host github.com-drops-streamlit
  HostName github.com
  User git
  IdentityFile ~/.ssh/drops_streamlit_deploy
  IdentitiesOnly yes
```

## 📊 Database Connection

The application connects to a PostgreSQL database (Neon) for QA review data:
- **Tables**: `qa_photo_reviews`, `qa_review_steps`
- **Connection**: Configured in the main application file
- **Features**: Real-time data fetching, agent assignment updates

## 🎯 Key Features

- **Real-time Dashboard**: Live data from PostgreSQL database
- **Photo Completion Tracking**: Monitor completion status across installation steps
- **Agent Management**: Assign and track work across team members
- **Visual Analytics**: Heatmaps and charts for performance insights
- **Responsive Design**: Works on desktop and mobile devices

## 📦 Dependencies

```
streamlit          # Web application framework
pandas            # Data manipulation and analysis
psycopg2-binary   # PostgreSQL database adapter
plotly            # Interactive visualizations
numpy             # Numerical computing
```

## 🔄 Deployment History

### Initial Setup (2025-09-27)
1. ✅ Created git repository and SSH configuration
2. ✅ Generated dedicated SSH deploy key (`drops_streamlit_deploy`)
3. ✅ Configured SSH host alias for repository-specific authentication
4. ✅ Created and pushed initial codebase to GitHub
5. ✅ Added `requirements.txt` for Streamlit Cloud compatibility
6. ✅ Deployed to Streamlit Cloud with auto-deploy enabled

### Git Timeline
- **Initial commit**: QA photo reviews dashboard with main application files
- **Second commit**: Added requirements.txt for cloud deployment

## 🛠️ Maintenance Notes

### Pro Tips for Updates
- Changes typically take 1-3 minutes to reflect on the live app
- Watch deployment progress in the Streamlit Cloud dashboard  
- If you update `requirements.txt`, dependencies will reinstall automatically
- Manual redeploy option available in Streamlit Cloud interface if needed

### Troubleshooting
- Check SSH key permissions if push fails
- Verify database connection if app shows connection errors
- Monitor Streamlit Cloud logs for deployment issues

## 📈 Future Enhancements

Potential improvements and features to consider:
- [ ] Environment-based configuration (dev/staging/prod)
- [ ] Database connection pooling
- [ ] User authentication and role-based access
- [ ] Export functionality for reports
- [ ] Email notifications for outstanding items
- [ ] Mobile-optimized responsive design improvements

---

**Last Updated**: September 27, 2025  
**Maintainer**: VelocityFibre Development Team  
**Environment**: Ubuntu Linux, Python 3.x, Streamlit Cloud