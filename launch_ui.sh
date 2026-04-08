#!/bin/bash

# Quick launcher for Streamlit Configuration UI

echo "🚀 Starting Veille Configuration UI..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "The UI will open in your browser at:"
echo "  👉 http://localhost:8501"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Virtual environment not detected"
    echo "Activating .venv..."
    source .venv/bin/activate
fi

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "❌ Streamlit not found. Installing..."
    pip install streamlit>=1.20
fi

# Launch streamlit app
streamlit run streamlit_app.py --logger.level=info
