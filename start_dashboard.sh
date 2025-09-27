#!/bin/bash

# QA Photo Reviews Dashboard Startup Script
echo "Starting QA Photo Reviews Dashboard..."

# Navigate to the correct directory
cd /home/louisdup/VF/Apps/streamlit

# Activate virtual environment
source streamlit_env/bin/activate

# Kill any existing streamlit processes
pkill -f streamlit 2>/dev/null

# Wait a moment for processes to stop
sleep 2

# Start the dashboard
echo "Dashboard starting on http://0.0.0.0:8501"
echo "Access from web browser at: http://localhost:8501"
echo "Or from network: http://[YOUR_IP]:8501"
echo ""
echo "Available agents: Unallocated (default), Zander, Michael"
echo "Use Ctrl+C to stop the dashboard"
echo ""

streamlit run qa_photo_reviews_dashboard.py --server.address=0.0.0.0 --server.port=8501