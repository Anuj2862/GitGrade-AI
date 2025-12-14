"""
GitGrade - Main FastAPI Application
Repository Mirror: AI explains scores, doesn't guess them
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import (
    AnalyzeRequest, AnalysisResult, ProgressUpdate, HealthCheck
)
from services.github_fetcher import GitHubFetcher
from services.ast_analyzer import ASTAnalyzer
from services.code_metrics import CodeMetricsAnalyzer
from services.git_analyzer import GitAnalyzer
from services.scoring_engine import ScoringEngine
from services.ai_analyzer import AIAnalyzer
from utils.helpers import generate_task_id, is_valid_github_url
import asyncio
import logging
from pathlib import Path
import json
from dotenv import load_dotenv
import os

# Load environment variables from parent directory
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Configure logging - Write to file to avoid Windows console encoding issues
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backend.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(
    title="GitGrade API",
    description="Repository Mirror - See your GitHub through a recruiter's eyes",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global state
analysis_progress = {}
CACHED_RESULTS = {}
OFFLINE_MODE = os.getenv("OFFLINE_MODE", "false").lower() == "true"

# Load cached results at startup
cache_file = Path("cache/demo_results.json")
if cache_file.exists():
    try:
        with open(cache_file) as f:
            CACHED_RESULTS = json.load(f)
        logger.info(f"[INFO] Loaded {len(CACHED_RESULTS)} cached results")
    except Exception as e:
        logger.warning(f"Could not load cache: {e}")

# Initialize services
try:
    github_fetcher = GitHubFetcher()
    ast_analyzer = ASTAnalyzer()
    code_metrics = CodeMetricsAnalyzer()
    git_analyzer = GitAnalyzer()
    scoring_engine = ScoringEngine()
    ai_analyzer = AIAnalyzer()
    logger.info("[INFO] All services initialized successfully")
except Exception as e:
    logger.error(f"Service initialization failed: {e}")
    raise


@app.on_event("startup")
async def startup_event():
    """Startup tasks"""
    logger.info("🚀 GitGrade API starting...")
    logger.info(f"Offline mode: {OFFLINE_MODE}")
    logger.info(f"Cached repositories: {len(CACHED_RESULTS)}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GitGrade API - Repository Mirror",
        "docs": "/docs",
        "health": "/api/health"
    }


@app.get("/api/health", response_model=HealthCheck)
async def health_check():
    """Health check endpoint"""
    try:
        # Check GitHub rate limit
        rate_limit = github_fetcher.check_rate_limit()
        
        # Check Gemini availability
        gemini_available = ai_analyzer.check_availability()
        
        return HealthCheck(
            status="healthy",
            github_rate_limit=rate_limit,
            gemini_available=gemini_available,
            cached_repos=len(CACHED_RESULTS)
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheck(
            status="degraded",
            gemini_available=False,
            cached_repos=len(CACHED_RESULTS)
        )


@app.post("/api/analyze")
async def analyze_repository(request: AnalyzeRequest):
    """
    Analyze a GitHub repository
    
    Returns cached result if available (instant demo)
    Otherwise performs live analysis with comprehensive fallbacks
    """
    repo_url = request.repo_url.strip()
    
    # Validate URL
    if not is_valid_github_url(repo_url):
        raise HTTPException(
            status_code=400,
            detail="Invalid GitHub URL. Format: https://github.com/username/repository"
        )
    
    # Check cache first (ALWAYS - for demo reliability)
    if repo_url in CACHED_RESULTS:
        logger.info(f"[INFO] Using cached result for {repo_url}")
        task_id = generate_task_id()
        analysis_progress[task_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Analysis complete (cached)",
            "result": CACHED_RESULTS[repo_url]
        }
        return {
            "task_id": task_id,
            "cached": True,
            "message": "Using cached result for instant demo"
        }
    
    # If offline mode, only use cache
    if OFFLINE_MODE:
        available_repos = list(CACHED_RESULTS.keys())[:5]
        raise HTTPException(
            status_code=503,
            detail=f"Offline mode: Only cached repositories available. Try: {available_repos}"
        )
    
    # Start live analysis
    task_id = generate_task_id()
    analysis_progress[task_id] = {
        "status": "starting",
        "progress": 0,
        "message": "Initializing analysis..."
    }
    
    # Run analysis in background
    asyncio.create_task(run_analysis(repo_url, task_id))
    
    return {
        "task_id": task_id,
        "cached": False,
        "message": "Analysis started. Poll /api/progress/{task_id} for updates"
    }


@app.get("/api/progress/{task_id}", response_model=ProgressUpdate)
async def get_progress(task_id: str):
    """Get analysis progress (for polling)"""
    if task_id not in analysis_progress:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return ProgressUpdate(**analysis_progress[task_id])


async def run_analysis(repo_url: str, task_id: str):
    """
    Run complete analysis with comprehensive error handling
    """
    try:
        # Step 1: Fetch repository data
        update_progress(task_id, 10, "Fetching repository data...")
        repo_data = await github_fetcher.fetch_repository(repo_url)
        
        # Step 2: Analyze code structure
        update_progress(task_id, 30, "Analyzing code structure...")
        structure = await ast_analyzer.analyze_repository(repo_data)
        
        # Step 3: Calculate code metrics
        update_progress(task_id, 50, "Calculating code quality metrics...")
        metrics = await code_metrics.analyze_code(repo_data)
        
        # Step 4: Analyze git workflow
        update_progress(task_id, 70, "Analyzing git workflow...")
        git_metrics = await git_analyzer.analyze_repository(repo_url)
        
        # Step 5: Calculate scores
        update_progress(task_id, 80, "Calculating scores...")
        from models import AnalysisData
        analysis_data = AnalysisData(
            repo=repo_data,
            structure=structure,
            metrics=metrics,
            git=git_metrics
        )
        scores = scoring_engine.calculate_score(analysis_data)
        
        # Step 6: Generate AI insights
        update_progress(task_id, 90, "Generating AI insights...")
        ai_insights = await ai_analyzer.generate_insights(analysis_data, scores)
        
        # Step 7: Compile final result
        result = AnalysisResult(
            total_score=scores['total_score'],
            skill_level=scores['skill_level'],
            percentile=scores['percentile'],
            dimensions=scores['dimensions'],
            ai_insights=ai_insights,
            repo_name=repo_data.name,
            repo_url=repo_url
        )
        
        # Cache successful result
        CACHED_RESULTS[repo_url] = result.dict()
        save_cache()
        
        # Mark as completed
        analysis_progress[task_id] = {
            "status": "completed",
            "progress": 100,
            "message": "Analysis complete!",
            "result": result.dict()
        }
        
        logger.info(f"[SUCCESS] Analysis completed for {repo_url}: {result.total_score}/100")
        
    except Exception as e:
        logger.error(f"Analysis failed for {repo_url}: {e}")
        analysis_progress[task_id] = {
            "status": "failed",
            "progress": 0,
            "message": "Analysis failed",
            "error": str(e)
        }


def update_progress(task_id: str, progress: int, message: str):
    """Update analysis progress"""
    if task_id in analysis_progress:
        analysis_progress[task_id].update({
            "status": "analyzing",
            "progress": progress,
            "message": message
        })


def save_cache():
    """Save cached results to file"""
    try:
        cache_file = Path("cache/demo_results.json")
        cache_file.parent.mkdir(exist_ok=True)
        with open(cache_file, 'w') as f:
            json.dump(CACHED_RESULTS, f, indent=2, default=str)
        logger.info(f"[INFO] Saved {len(CACHED_RESULTS)} cached results")
    except Exception as e:
        logger.warning(f"Could not save cache: {e}")


if __name__ == "__main__":
    # Fix for Windows console encoding
    import sys
    import codecs
    if sys.platform == 'win32':
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

    import uvicorn
    import traceback
    try:
        print("[INFO] GitGrade API starting...")
        port = int(os.getenv("PORT", 8000))
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        print("\n[ERROR] CRITICAL STARTUP ERROR:")
        traceback.print_exc()
        # Keep window open if crashed
        import time
        time.sleep(5)
