# 🚀 GitGrade - Quick Setup Guide

## Step 1: Install Dependencies

```bash
cd C:\Users\Admin\OneDrive\Desktop\gitgrade
pip install -r requirements.txt
```

## Step 2: Get API Keys

### GitHub Token
1. Go to https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `read:user`
4. Copy the token

### Gemini API Key
1. Go to https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

**Get 3 of each for backup!**

## Step 3: Configure Environment

```bash
# Copy example file
copy .env.example .env

# Edit .env file and add your keys:
# GITHUB_TOKEN=ghp_your_token_here
# GEMINI_API_KEY=AIza_your_key_here
```

## Step 4: Test Backend

```bash
cd backend
python main.py
```

You should see:
```
🚀 GitGrade API starting...
✓ All services initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Step 5: Test Frontend

Open a new terminal:

```bash
cd frontend
python -m http.server 3000
```

Then open: http://localhost:3000

## Step 6: Test Analysis

1. In the browser, enter: `https://github.com/fastapi/fastapi`
2. Click "Analyze Repository"
3. Wait for results (30-60 seconds)

## Step 7: Pre-Cache Demo Repos (Optional)

For instant demos:

```bash
python scripts/pre_cache_demos.py
```

This caches 10 popular repos for instant results!

## 🎯 Quick Test

```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Should return:
# {"status":"healthy","github_rate_limit":5000,"gemini_available":true,"cached_repos":0}
```

## 🐛 Troubleshooting

### "Module not found"
```bash
pip install -r requirements.txt
```

### "GITHUB_TOKEN is required"
- Make sure `.env` file exists
- Check that GITHUB_TOKEN is set

### "Gemini API failed"
- Check GEMINI_API_KEY in `.env`
- Verify key is valid at https://makersuite.google.com

### Frontend not loading
- Make sure backend is running on port 8000
- Check browser console for errors
- Update API_URL in `frontend/app.js` if needed

## ✅ You're Ready!

Your GitGrade is now running:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

**Next Steps:**
1. Test with a few repositories
2. Run pre-cache script for demos
3. Deploy to Render + GitHub Pages
4. Record demo video

**Good luck with the hackathon! 🏆**
