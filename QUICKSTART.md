# Quick Start Guide - CV Project Recommender

## 🚀 Two Deployment Modes

### Mode 1: Standalone (Simplest)
Run everything in one process - no backend needed.

```bash
# Activate virtual environment
.\ProjectRecommenderVenv\Scripts\Activate.ps1  # Windows
# source ProjectRecommenderVenv/bin/activate  # Linux/Mac

# Run standalone app
streamlit run app.py
```

**Pros**: Simple, one command, no setup  
**Cons**: No API access, can't scale

---

### Mode 2: API-Based (Recommended for Production)
Separate backend and frontend for better scalability.

#### Step 1: Start Backend

**Windows:**
```bash
.\ProjectRecommenderVenv\Scripts\Activate.ps1
.\run_backend.bat
```

**Linux/Mac:**
```bash
source ProjectRecommenderVenv/bin/activate
./run_backend.sh
```

**Or manually:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

✅ Backend will be available at: http://localhost:8000  
✅ API Docs at: http://localhost:8000/api/docs

#### Step 2: Start Frontend (New Terminal)

**Windows:**
```bash
.\ProjectRecommenderVenv\Scripts\Activate.ps1
.\run_frontend.bat
```

**Linux/Mac:**
```bash
source ProjectRecommenderVenv/bin/activate
./run_frontend.sh
```

**Or manually:**
```bash
streamlit run streamlit_app.py --server.port 8501
```

✅ Frontend will be available at: http://localhost:8501

**Pros**: Scalable, API access, can deploy separately  
**Cons**: Need to run two processes

---

## 📋 Prerequisites

1. **Python 3.11+** installed
2. **Virtual environment** created and activated
3. **Dependencies** installed:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment variables** configured in `.env`:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   GITHUB_TOKEN=your_github_token_here  # Optional
   YOUTUBE_API_KEY=your_youtube_api_key_here
   ```

---

## 🧪 Testing the Backend API

### Health Check
```bash
curl http://localhost:8000/api/health
```

### Submit Analysis (using curl)
```bash
curl -X POST "http://localhost:8000/api/analyze" \
  -F "cv_file=@path/to/your/cv.pdf" \
  -F "job_description=Senior Python Developer with 5+ years experience..."
```

### Check Status
```bash
curl http://localhost:8000/api/status/{job_id}
```

### Get Results
```bash
curl http://localhost:8000/api/results/{job_id}
```

---

## 📖 Using the Frontend

1. **Upload CV**: Choose PDF or DOCX file
2. **Paste Job Description**: Complete job posting (min 50 characters)
3. **Click Analyze**: Wait 30-60 seconds for processing
4. **Review Results**:
   - Skill match percentage
   - Identified skill gaps
   - Project recommendations (beginner/intermediate/advanced)
   - Learning resources (GitHub repos + YouTube videos)
5. **Export**: Download results as JSON

---

## 🔧 Architecture Changes

### What Changed?
- ❌ **Removed**: Celery, Flower, Redis (complex background task queue)
- ✅ **Added**: Simple in-memory job manager
- ✅ **Added**: Async FastAPI processing
- ✅ **Added**: Server-Sent Events for real-time progress

### Benefits
- 🎯 **Simpler deployment**: No Redis/Celery setup
- 🚀 **Faster startup**: Fewer dependencies
- 🐛 **Easier debugging**: All in one process
- 📦 **Smaller footprint**: Reduced memory usage

### Trade-offs
- ⏱️ **Blocking requests**: API calls wait for completion (30-60s)
- 💾 **In-memory only**: Jobs cleared after 1 hour
- 📊 **No persistence**: Results lost on restart

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check if port 8000 is in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/Mac

# Try different port
uvicorn backend.main:app --port 8001
```

### Frontend can't connect to backend
1. Verify backend is running: http://localhost:8000/api/health
2. Check `config.py` - ensure `backend_url = "http://localhost:8000"`
3. Check firewall settings

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --upgrade
```

### API key errors
1. Check `.env` file exists
2. Verify API keys are correct
3. No quotes around values in `.env`

---

## 📚 Next Steps

- Read full documentation: `README.md`
- Check API docs: http://localhost:8000/api/docs
- Review examples: `examples/` directory
- Run tests: `pytest tests/`

---

**Built with ❤️ using FastAPI, Streamlit, and LangGraph**
