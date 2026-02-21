# 🎯 ScoreMyResume - Quick Reference Card

## ⚡ Quick Start Commands

```bash
# Linux/Mac
cd scoremyresume
./start.sh

# Windows
cd scoremyresume
start.bat

# Manual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

**Access:** http://localhost:8501

---

## 🎯 Features at a Glance

| Feature | Description | Location |
|---------|-------------|----------|
| 🎯 **ATS Analysis** | Full resume vs JD scoring | Main page |
| ✨ **Resume Optimizer** | AI-powered bullet rewriting | Optimizer tab |
| 🔍 **Skill Evidence** | Evidence-based Python scoring | Evidence tab |
| 📈 **Analytics** | Career timeline & insights | Analytics tab |

---

## 📊 Scoring System

### Role Tiers
- **Junior (≤1 year)**: Projects + internships = full credit
- **Mid (2-4 years)**: Projects + internships = 50% weight
- **Senior (≥5 years)**: Only professional experience counts

### Score Ranges
- 🟢 **75-100**: Excellent match
- 🔵 **60-74**: Good match
- 🟡 **40-59**: Fair match
- 🔴 **0-39**: Poor match

### Skill Evidence (Python)
- Listed in skills: **20 points**
- Used in projects: **30 points**
- Used in experience: **25 points**
- Frameworks detected: **15 points**
- Quantified metrics: **10 points**
- **Total cap: 100 points**

---

## 🔑 Setup Checklist

- [ ] Extract `scoremyresume/` folder
- [ ] Open terminal in project folder
- [ ] Run start script (or manual commands)
- [ ] Get Groq API key from [console.groq.com](https://console.groq.com)
- [ ] Enter API key in sidebar
- [ ] Upload test resume
- [ ] Paste test JD
- [ ] Click "Run Analysis"
- [ ] ✅ Done!

---

## 📁 Project Structure

```
scoremyresume/
├── streamlit_app.py       # Main application (900+ lines)
├── requirements.txt       # Dependencies
├── start.sh / start.bat   # Quick start scripts
├── README.md              # Full documentation
├── UI_GUIDE.md           # Visual guide
├── DEPLOYMENT_GUIDE.md   # Deployment options
│
├── services/
│   └── groq_service.py   # LLM integration
│
└── utils/
    ├── document_parser.py    # PDF/DOCX parsing
    ├── skill_normalizer.py   # Skill matching
    ├── boolean_query.py      # Boolean search
    ├── experience_calculator.py  # Timeline calc
    └── skill_evidence.py     # Evidence scoring
```

---

## 🎨 UI Navigation

```
SIDEBAR:
├── 🔑 Groq API Key Input
├── 📊 Navigation Menu
│   ├── 🎯 ATS Analysis    (Main scoring page)
│   ├── ✨ Resume Optimizer (Bullet rewriting)
│   ├── 🔍 Skill Evidence  (Python scoring)
│   └── 📈 Analytics       (Career insights)
```

---

## 🌐 Deployment Options

### Streamlit Cloud (Free)
```bash
1. Push to GitHub
2. Visit share.streamlit.io
3. Connect repo
4. Deploy
```

### Local Network
```bash
streamlit run streamlit_app.py --server.address 0.0.0.0
# Access via: http://YOUR_IP:8501
```

### Docker
```bash
docker build -t scoremyresume .
docker run -p 8501:8501 scoremyresume
```

---

## 🐛 Common Issues & Fixes

| Issue | Solution |
|-------|----------|
| **Module not found** | `cd scoremyresume && pip install -r requirements.txt` |
| **Groq API error** | Check API key, verify internet |
| **PDF parsing failed** | Use text-based PDF or convert to DOCX |
| **Charts not showing** | `pip install plotly --upgrade` |
| **Port already in use** | `streamlit run streamlit_app.py --server.port 8502` |

---

## 📈 Performance Expectations

- Resume parsing: **2-3 seconds**
- JD extraction: **2-3 seconds**
- ATS analysis: **3-5 seconds**
- Skill evidence: **<1 second** (instant)
- **Total workflow: 10-15 seconds**

---

## 🎯 Workflow Steps

1. **Upload Resume** → PDF or DOCX → Auto-parsed
2. **Add Job Description** → Paste or upload → Auto-analyzed
3. **Run Analysis** → Click button → Wait ~10 seconds
4. **View Results** → 4 tabs with complete breakdown
5. **Optimize (Optional)** → Improve specific bullets
6. **Check Evidence (Optional)** → See skill proof

---

## 🔒 Security Notes

- API keys stored in session only (not saved to disk)
- No data sent to external servers except Groq API
- All processing happens locally
- Resume data cleared on session end

---

## 📞 Documentation

- **Setup Guide**: README.md
- **UI Guide**: UI_GUIDE.md
- **Deployment**: DEPLOYMENT_GUIDE.md
- **This Card**: QUICK_REFERENCE.md

---

## 🎓 First-Time Tips

1. **Test with sample data first** (any tech resume + Python JD)
2. **Check all 4 tabs** to explore features
3. **Try the optimizer** on a weak bullet point
4. **Review evidence scoring** to understand skill depth
5. **Check analytics** to see timeline visualization

---

## ✨ Key Differentiators

✅ **Evidence-based scoring** (not just keywords)
✅ **Role-aware intelligence** (Junior/Mid/Senior)
✅ **Beautiful visualizations** (charts, gauges, badges)
✅ **AI-powered optimization** (bullet rewriting)
✅ **Production-ready** (error handling, validation)
✅ **Single deployment** (no backend/frontend split)

---

## 🚀 Ready to Use!

**Project Name:** ScoreMyResume
**Type:** Streamlit ATS Application
**Status:** Production Ready
**Lines of Code:** 900+ (main app)
**Dependencies:** 8 core packages
**Deployment:** Single command

**Start now:** `./start.sh` or `start.bat`

---

**Keep this card handy for quick reference!** 📋
