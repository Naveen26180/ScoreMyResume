# 🚀 ScoreMyResume Streamlit - Complete Deployment Guide

## ✅ What You Have

A **complete, production-ready Streamlit ATS application** with:

### 📁 Project Structure
```
scoremyresume/
├── streamlit_app.py          # Main application (30KB, 900+ lines)
├── requirements.txt           # All dependencies
├── README.md                  # Setup instructions
├── UI_GUIDE.md                # Visual interface guide
├── start.sh                   # Quick start (Linux/Mac)
├── start.bat                  # Quick start (Windows)
│
├── services/
│   ├── __init__.py
│   └── groq_service.py       # LLM integration with role tiers
│
└── utils/
    ├── __init__.py
    ├── document_parser.py     # PDF/DOCX parsing
    ├── skill_normalizer.py    # Skill matching
    ├── boolean_query.py       # Boolean search queries
    ├── experience_calculator.py  # Timeline calculation
    └── skill_evidence.py      # Evidence-based scoring (NEW!)
```

### 🎯 Features Included

#### 1. **ATS Analysis** 🎯
- Upload resume (PDF/DOCX)
- Parse job description (paste or upload)
- Run comprehensive ATS scoring
- Visual score gauge (0-100)
- Skill matching analysis
- Score breakdown charts
- Detailed recommendations

#### 2. **Resume Optimizer** ✨
- Select any bullet point
- AI-powered rewriting
- Match job description keywords
- Add quantifiable metrics
- Show improvement suggestions

#### 3. **Skill Evidence** 🔍
- Deterministic Python scoring
- 5-level evidence system:
  - Listed in skills (20 pts)
  - Used in projects (30 pts)
  - Used in experience (25 pts)
  - Frameworks detected (15 pts)
  - Quantified metrics (10 pts)
- Weight multiplier (0.0-1.0)
- Visual evidence breakdown

#### 4. **Analytics Dashboard** 📈
- Experience timeline
- Skills distribution
- Projects overview
- Career insights

### 🎨 UI Features

✅ Beautiful gradient color scheme (purple/blue)
✅ Interactive Plotly charts
✅ Responsive gauge visualizations
✅ Color-coded skill badges
✅ Tab-based navigation
✅ Expandable sections
✅ Loading indicators
✅ Success/warning/error messages

---

## 🏃 Quick Start (3 Steps)

### Option A: Automated (Recommended)

**Linux/Mac:**
```bash
cd scoremyresume
chmod +x start.sh
./start.sh
```

**Windows:**
```cmd
cd scoremyresume
start.bat
```

### Option B: Manual

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run
streamlit run streamlit_app.py
```

**Done!** App opens at `http://localhost:8501`

---

## 🔑 First-Time Setup

1. **Get Groq API Key**
   - Go to [console.groq.com](https://console.groq.com)
   - Sign up (free)
   - Get API key

2. **Enter API Key**
   - Open app
   - Sidebar → "Groq API Key"
   - Paste key → Enter
   - See "✅ API Key Configured"

3. **Start Using**
   - Upload resume
   - Upload/paste JD
   - Click "Run ATS Analysis"
   - View results!

---

## 📊 How to Use

### Complete Workflow

```
1. Upload Resume
   └→ PDF or DOCX
   └→ Auto-parsed
   └→ View extracted data

2. Add Job Description  
   └→ Paste text OR upload file
   └→ Auto-analyzed
   └→ View requirements

3. Run Analysis
   └→ Click "Run ATS Analysis"
   └→ Wait 10-15 seconds
   └→ See comprehensive results

4. Explore Results
   └→ Overview: Charts + gauge
   └→ Skills: Matched vs missing
   └→ Reasoning: AI explanation
   └→ Details: Full breakdown

5. Optional: Optimize
   └→ Go to "Resume Optimizer"
   └→ Select bullet to improve
   └→ Get AI-enhanced version

6. Optional: Check Evidence
   └→ Go to "Skill Evidence"
   └→ See Python skill proof
   └→ Get improvement tips
```

---

## 🎯 Role Tier System

The app automatically detects role level:

### Junior (≤1 year)
- Projects count **fully** ✅
- Internships count **fully** ✅
- Target score: 75-90
- Focus: Potential + learning

### Mid (2-4 years)
- Projects count **50%** ⚖️
- Internships count **50%** ⚖️
- **CAP: Max 60 if skills < 50%** 🔒
- Focus: Balance experience + potential

### Senior (≥5 years)
- Projects: **Ignored** ❌
- Internships: **0 points** ❌
- **STRICT CAPS:** 🔒
  - Must-have < 50% → Max 35
  - Experience < 50% → Max 30
- Focus: Production experience only

---

## 🧪 Testing Examples

### Test Case 1: Junior Role
```
Resume: Recent grad, 2 Python projects, 1 internship
JD: Junior Python Developer, 0-1 years
Expected: Score 75-85 (good match)
```

### Test Case 2: Skill Stuffer
```
Resume: Lists Python but no usage evidence
JD: Requires Python
Expected: Low Python weight (0.2), reduced score
```

### Test Case 3: Senior Mismatch
```
Resume: 2 years experience, few skills
JD: Senior role, 5+ years, many skills
Expected: Capped at 30-35 (experience + skills gaps)
```

---

## 🐛 Troubleshooting

### "Module not found" error
```bash
# Ensure you're in the project root
cd scoremyresume

# Check virtual environment is activated
which python  # Should show venv path

# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### "Groq API error"
- Check API key is correct
- Check internet connection
- Verify Groq service is online
- Try regenerating API key

### "Failed to parse PDF"
- Ensure PDF is text-based (not scanned image)
- Try converting to DOCX
- Check file isn't corrupted
- Try a different PDF reader/converter

### Charts not displaying
```bash
# Clear Streamlit cache
rm -rf ~/.streamlit/cache

# Reinstall Plotly
pip install plotly --upgrade

# Restart app
streamlit run streamlit_app.py
```

### Slow performance
- First run is slower (model loading)
- Subsequent runs are faster
- Large PDFs take longer to parse
- Complex JDs take longer to analyze

---

## 🌐 Deployment Options

### 1. **Streamlit Cloud** (Easiest, Free)

**Steps:**
1. Push code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Sign in with GitHub
4. Click "New app"
5. Select repository
6. Set main file: `streamlit_app.py`
7. Click "Deploy"

**Secrets Management:**
- In Streamlit Cloud settings
- Add under "Secrets"
- Format:
  ```toml
  GROQ_API_KEY = "your-key-here"
  ```

**URL:** `https://your-app.streamlit.app`

---

### 2. **Local Network Deployment**

For company internal use:

```bash
# Run on specific port
streamlit run streamlit_app.py --server.port 8501

# Allow external connections
streamlit run streamlit_app.py --server.address 0.0.0.0

# Both
streamlit run streamlit_app.py \
  --server.port 8501 \
  --server.address 0.0.0.0
```

Access from other computers: `http://YOUR_IP:8501`

---

### 3. **Heroku Deployment**

**Files needed:**
1. `Procfile`:
```
web: streamlit run streamlit_app.py --server.port=$PORT --server.address=0.0.0.0
```

2. `setup.sh`:
```bash
mkdir -p ~/.streamlit/
echo "\
[server]\n\
headless = true\n\
port = $PORT\n\
enableCORS = false\n\
" > ~/.streamlit/config.toml
```

**Deploy:**
```bash
heroku create your-app-name
git push heroku main
heroku open
```

---

### 4. **Docker Deployment**

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Build & Run:**
```bash
docker build -t scoremyresume-ats .
docker run -p 8501:8501 scoremyresume-ats
```

---

## 🔧 Customization

### Change Colors

Edit `streamlit_app.py` line ~40:
```python
background: linear-gradient(120deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
```

### Add More Skills

Edit `utils/skill_evidence.py`:
```python
def extract_javascript_evidence(extracted_resume):
    # Copy Python logic, change keywords
    pass
```

### Adjust Scoring Weights

Edit `utils/skill_evidence.py`:
```python
# Current weights: 20, 30, 25, 15, 10
# Change to your preference
evidence["score"] += YOUR_VALUE
```

### Add Custom Features

The app is modular:
- Add new pages: Create function + add to sidebar
- Add new charts: Use Plotly
- Add new analysis: Create utility function

---

## 📈 Performance Metrics

**Expected Timing:**
- Resume parsing: 2-3 seconds
- JD extraction: 2-3 seconds  
- ATS analysis: 3-5 seconds
- Skill evidence: <1 second (deterministic)
- Bullet optimization: 2-3 seconds
- **Total workflow: 10-15 seconds**

**Resource Usage:**
- RAM: ~200MB
- CPU: Light (mostly API calls)
- Storage: <10MB

---

## 🎓 Tutorial Videos (Recommended)

Create these tutorials for your users:

1. **First-Time Setup** (2 min)
   - Getting API key
   - Entering key in app
   - Uploading first resume

2. **Running Analysis** (3 min)
   - Upload resume
   - Add JD
   - Interpret results

3. **Understanding Scores** (5 min)
   - What each metric means
   - How caps work
   - Reading recommendations

4. **Optimizing Resume** (3 min)
   - Using bullet optimizer
   - Checking skill evidence
   - Improving weak areas

---

## 🆘 Support Resources

### Documentation
- **Streamlit Docs**: [docs.streamlit.io](https://docs.streamlit.io)
- **Groq API Docs**: [console.groq.com/docs](https://console.groq.com/docs)
- **Plotly Docs**: [plotly.com/python](https://plotly.com/python)

### Community
- **Streamlit Forum**: [discuss.streamlit.io](https://discuss.streamlit.io)
- **GitHub Issues**: Create issues for bugs
- **Discord**: Streamlit community

---

## ✅ Pre-Deployment Checklist

Before sharing with users:

- [ ] Test with 5+ different resumes
- [ ] Test with 5+ different JDs
- [ ] Verify all tabs load correctly
- [ ] Check charts render properly
- [ ] Test on different browsers
- [ ] Test on mobile (responsive)
- [ ] Verify API key security
- [ ] Add usage instructions
- [ ] Create sample data
- [ ] Set up error monitoring

---

## 🎉 You're Ready!

Your complete ATS system is ready to use!

**Start Now:**
```bash
cd scoremyresume
./start.sh  # or start.bat on Windows
```

**Or Deploy:**
```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
# Then deploy to Streamlit Cloud
```

---

## 📞 Need Help?

1. Check **README.md** for setup
2. Check **UI_GUIDE.md** for interface
3. Check **Troubleshooting** section above
4. Review Streamlit/Groq documentation
5. Check error logs in terminal

---

**Happy Analyzing! 🎯**
