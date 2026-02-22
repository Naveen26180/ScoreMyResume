
# ScoreMyResume

ScoreMyResume is a Streamlit-based ATS (Applicant Tracking System) analyzer that evaluates a resume against a job description and provides a structured compatibility score with detailed feedback.

The system combines deterministic skill analysis with LLM-based reasoning to simulate how modern ATS systems and recruiters evaluate resumes.

---

## Overview

This project allows users to:

- Upload a resume (PDF or DOCX)
- Provide a job description
- Receive an ATS compatibility score (0–100)
- View matched and missing skills
- Analyze role seniority alignment
- Optimize resume bullet points
- Evaluate depth of Python skill evidence
- Visualize career timeline and skill distribution

The goal of this project is to build a structured, explainable ATS scoring engine rather than a simple keyword matcher.

---

## Tech Stack

- Python  
- Streamlit  
- Groq LLM API  
- Plotly  
- PDF/DOCX parsing libraries  
- Custom deterministic scoring modules  

---

## Project Structure

```
scoremyresume/
│
├── streamlit_app.py
├── requirements.txt
│
├── services/
│   └── groq_service.py
│
└── utils/
    ├── document_parser.py
    ├── skill_normalizer.py
    ├── boolean_query.py
    ├── experience_calculator.py
    └── skill_evidence.py
```

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/scoremyresume.git
cd scoremyresume
```

Create a virtual environment:

```bash
python -m venv venv
```

Activate it:

Windows:
```bash
venv\Scripts\activate
```

Mac/Linux:
```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run streamlit_app.py
```

The app will be available at:

https://scoremyresumebot.streamlit.app/

---

## How It Works

### 1. Resume Parsing
The uploaded PDF/DOCX file is parsed into structured sections:
- Skills
- Experience
- Projects
- Education

### 2. Job Description Extraction
The job description is analyzed to extract:
- Must-have skills
- Nice-to-have skills
- Required experience level

### 3. Skill Matching
Skills are normalized and compared between resume and job description.

### 4. Evidence-Based Skill Scoring

For Python, scoring is not based on keyword presence alone.

Points are awarded based on evidence:

- Listed in skills section (20)
- Used in projects (30)
- Used in work experience (25)
- Framework/library mentions (15)
- Quantified achievements (10)

### 5. Role Tier Logic

Junior (≤1 year):
- Projects and internships fully counted

Mid (2–4 years):
- Projects and internships weighted at 50%

Senior (≥5 years):
- Only professional experience considered

Score caps are applied when must-have skills or experience alignment is weak.

---

## Features

### ATS Analysis
- Compatibility score (0–100)
- Skill match breakdown
- Recruiter-style reasoning
- Structured feedback

### Resume Optimizer
- Bullet point rewriting
- Metric injection
- Keyword alignment

### Skill Evidence
- Depth-based Python evaluation
- Weight multiplier calculation

### Analytics
- Experience timeline
- Skill distribution summary
- Project overview

---

## Performance

- Resume parsing: ~2–3 seconds  
- JD extraction: ~2–3 seconds  
- ATS analysis: ~3–5 seconds  
- Total workflow: ~10–15 seconds  

---

## Deployment

The app can be deployed using:

- Streamlit Cloud  
- Docker  
- Heroku  
- Local server  

---

## License

This project is intended for educational and portfolio use.

---

## Design Decisions

- Combined deterministic and LLM scoring for explainability
- Implemented role-tier caps to simulate recruiter behavior
- Modular architecture for future skill expansion

---

