
# Deployment Guide – ScoreMyResume

## Local
streamlit run streamlit_app.py

Access: https://scoremyresumebot.streamlit.app/

## Streamlit Cloud
1. Push to GitHub
2. Go to share.streamlit.io
3. Select repo
4. Set main file: streamlit_app.py
5. Deploy

Add secret:
GROQ_API_KEY = "your-key"

## Docker

FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit","run","streamlit_app.py","--server.address=0.0.0.0"]

Build:
docker build -t scoremyresume .
Run:
docker run -p 8501:8501 scoremyresume
