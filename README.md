# ScoreMyResume - Streamlit ATS Application

## 🚀 Complete Setup Instructions

### Project Structure

```
scoremyresume/
│
├── streamlit_app.py          # Main Streamlit application
├── requirements.txt           # Python dependencies
│
├── services/
│   ├── __init__.py
│   └── groq_service.py       # Groq API integration
│
└── utils/
    ├── __init__.py
    ├── document_parser.py     # PDF/DOCX parsing
    ├── skill_normalizer.py    # Skill matching
    ├── boolean_query.py       # Boolean search
    ├── experience_calculator.py  # Experience timeline
    └── skill_evidence.py      # Evidence scoring (NEW)
```

### Step 1: Create Project Structure

```bash
# Create main directory
mkdir scoremyresume
cd scoremyresume

# Create subdirectories
mkdir services utils

# Create __init__.py files
touch services/__init__.py
touch utils/__init__.py
```

### Step 2: Copy Files

**Copy these files to your project:**

1. `streamlit_app.py` → Root directory
2. `requirements.txt` → Root directory
3. `groq_service.py` → `services/` directory
4. `document_parser.py` → `utils/` directory
5. `skill_normalizer.py` → `utils/` directory
6. `boolean_query.py` → `utils/` directory
7. `experience_calculator.py` → `utils/` directory
8. `skill_evidence.py` → `utils/` directory

### Step 3: Install Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Run the Application

```bash
streamlit run streamlit_app.py
```

The application will open in your browser at `http://localhost:8501`

---

## 🎯 Features

### 1. ATS Analysis
- Upload resume (PDF/DOCX)
- Paste or upload job description
- Get comprehensive ATS score with breakdown
- Visual skill matching analysis
- Detailed recommendations

### 2. Resume Optimizer
- Rewrite bullet points to match job description
- Get improvement suggestions
- Optimize keywords naturally

### 3. Skill Evidence Analysis
- Deterministic Python skill scoring
- Evidence-based evaluation:
  - Listed (20 points)
  - Used in projects (30 points)
  - Used in experience (25 points)
  - Frameworks (15 points)
  - Quantified metrics (10 points)
- Weight multiplier calculation

### 4. Analytics Dashboard
- Experience timeline visualization
- Skills distribution analysis
- Projects overview
- Career insights

---

## 🎨 UI Features

### Beautiful Design
- Gradient color schemes
- Interactive charts (Plotly)
- Responsive gauge charts
- Skill badges with colors
- Clean metric cards

### Visualizations
- **Score Gauge**: Beautiful gauge showing ATS score with color coding
- **Skill Match Chart**: Bar chart comparing matched vs missing skills
- **Score Breakdown**: Horizontal bar chart showing point distribution
- **Experience Timeline**: Table view of career progression

### User Experience
- Sidebar navigation
- Tab-based content organization
- Expandable sections for detailed info
- Progress indicators
- Success/warning/error messages
- Keyboard-friendly interface

---

## 🔑 API Key Setup

1. Get your Groq API key from [console.groq.com](https://console.groq.com)
2. Enter it in the sidebar when you open the app
3. The key is stored in session state (not saved to disk)

---

## 📊 How It Works

### ATS Scoring Pipeline

```
1. Upload Resume → Parse PDF/DOCX → Extract structured data
                                          ↓
2. Upload JD → Parse text → Extract requirements (Groq)
                                          ↓
3. Skill Matching → Normalize skills → Compare resume vs JD
                                          ↓
4. Evidence Scoring → Extract Python evidence → Calculate weight
                                          ↓
5. ATS Analysis → Run Groq with all context → Get final score
                                          ↓
6. Display Results → Charts, skills, reasoning, recommendations
```

### Role Tier Classification

- **Junior** (≤1 year): Projects + internships count fully
- **Mid** (2-4 years): Projects + internships at 50% weight
- **Senior** (≥5 years): Only professional experience counts

### Score Caps

- **Senior**: Max 35 if must-have < 50%, Max 30 if experience < 50%
- **Mid**: Max 60 if must-have < 50%
- **Python Evidence**: Reduces must-have score if weight < 0.5

---

## 🧪 Testing

### Test the Application

1. **Prepare test data:**
   - Sample resume (PDF or DOCX)
   - Sample job description

2. **Run through workflow:**
   - Upload resume → Verify parsing
   - Upload JD → Verify extraction
   - Run analysis → Check score and breakdown
   - Test skill evidence → Verify Python scoring
   - Try optimizer → Rewrite a bullet

3. **Check visualizations:**
   - Score gauge displays correctly
   - Skill charts show data
   - Breakdown chart renders
   - All tabs load properly

---

## 🐛 Troubleshooting

### Common Issues

**Issue: "Groq API key required"**
- Solution: Enter your API key in the sidebar

**Issue: "Failed to parse PDF"**
- Solution: Ensure PDF is text-based (not scanned image)
- Try converting to DOCX

**Issue: "Module not found"**
- Solution: Ensure all files are in correct directories
- Check __init__.py files exist
- Verify imports in streamlit_app.py match your structure

**Issue: Charts not rendering**
- Solution: Check Plotly is installed: `pip install plotly`
- Clear Streamlit cache: Delete `.streamlit/` folder

---

## 🔧 Customization

### Change Color Scheme

Edit the CSS in `streamlit_app.py` (line ~40):

```python
background: linear-gradient(120deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
```

### Add More Skills

Edit `skill_evidence.py` to add more skills beyond Python:

```python
def extract_javascript_evidence(extracted_resume):
    # Same logic, different keywords
    pass
```

### Adjust Scoring Weights

Modify weights in `skill_evidence.py`:

```python
# Current: 20, 30, 25, 15, 10
# Change to your preference
```

---

## 📈 Performance

- **Resume parsing**: ~2-3 seconds
- **JD extraction**: ~2-3 seconds
- **ATS analysis**: ~3-5 seconds
- **Skill evidence**: <1 second (deterministic)
- **Total workflow**: ~10-15 seconds

---

## 🚀 Deployment

### Deploy to Streamlit Cloud

1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repository
4. Set main file: `streamlit_app.py`
5. Add secrets (if needed) in Streamlit Cloud settings

### Deploy to Heroku

1. Add `Procfile`:
```
web: streamlit run streamlit_app.py --server.port=$PORT
```

2. Add `setup.sh`:
```bash
mkdir -p ~/.streamlit/
echo "[server]
headless = true
port = $PORT
enableCORS = false
" > ~/.streamlit/config.toml
```

3. Deploy:
```bash
git push heroku main
```

---

## 📝 License

This is a custom ATS system. Modify as needed for your use case.

---

## 🤝 Support

For issues or questions:
1. Check troubleshooting section above
2. Review Streamlit docs: [docs.streamlit.io](https://docs.streamlit.io)
3. Review Groq docs: [console.groq.com/docs](https://console.groq.com/docs)

---

## 🎉 You're Ready!

Run the app:
```bash
streamlit run streamlit_app.py
```

Your beautiful ATS system is now live! 🚀
