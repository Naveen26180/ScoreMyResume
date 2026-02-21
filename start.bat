@echo off
REM Quick Start Script for ScoreMyResume Streamlit App (Windows)

echo ================================
echo ScoreMyResume ATS - Quick Start
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo Starting Streamlit app...
echo The app will open in your browser automatically
echo If not, go to: http://localhost:8501
echo.

REM Run Streamlit
streamlit run streamlit_app.py
