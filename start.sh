#!/bin/bash
# Quick Start Script for ScoreMyResume Streamlit App

echo "🚀 ScoreMyResume ATS - Quick Start"
echo "=============================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo "✅ Virtual environment created"
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Starting Streamlit app..."
echo "   The app will open in your browser automatically"
echo "   If not, go to: http://localhost:8501"
echo ""

# Run Streamlit
streamlit run streamlit_app.py
