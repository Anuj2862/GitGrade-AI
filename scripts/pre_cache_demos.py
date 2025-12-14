"""
Pre-cache demo repositories for instant, reliable demos
Run this 24 hours before the hackathon
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.services.github_fetcher import GitHubFetcher
from backend.services.ast_analyzer import ASTAnalyzer
from backend.services.code_metrics import CodeMetricsAnalyzer
from backend.services.git_analyzer import GitAnalyzer
from backend.services.scoring_engine import ScoringEngine
from backend.services.ai_analyzer import AIAnalyzer
from backend.models import AnalysisData, AnalysisResult
import json
from dotenv import load_dotenv

load_dotenv()

# Demo repositories to cache
DEMO_REPOS = [
    "https://github.com/fastapi/fastapi",
    "https://github.com/pallets/flask",
    "https://github.com/django/django",
    "https://github.com/nodejs/node",
    "https://github.com/facebook/react",
    "https://github.com/microsoft/vscode",
    "https://github.com/python/cpython",
    "https://github.com/torvalds/linux",
    "https://github.com/tensorflow/tensorflow",
    "https://github.com/kubernetes/kubernetes"
]


async def cache_repository(repo_url: str, services: dict) -> dict:
    """Analyze and cache a single repository"""
    print(f"\n📊 Analyzing: {repo_url}")
    
    try:
        # Fetch repository data
        print("  ├─ Fetching repository data...")
        repo_data = await services['github'].fetch_repository(repo_url)
        
        # Analyze structure
        print("  ├─ Analyzing code structure...")
        structure = await services['ast'].analyze_repository(repo_data)
        
        # Calculate metrics
        print("  ├─ Calculating metrics...")
        metrics = await services['metrics'].analyze_code(repo_data)
        
        # Analyze git
        print("  ├─ Analyzing git workflow...")
        git_metrics = await services['git'].analyze_repository(repo_url)
        
        # Calculate scores
        print("  ├─ Calculating scores...")
        analysis_data = AnalysisData(
            repo=repo_data,
            structure=structure,
            metrics=metrics,
            git=git_metrics
        )
        scores = services['scoring'].calculate_score(analysis_data)
        
        # Generate AI insights
        print("  ├─ Generating AI insights...")
        ai_insights = await services['ai'].generate_insights(analysis_data, scores)
        
        # Create result
        result = AnalysisResult(
            total_score=scores['total_score'],
            skill_level=scores['skill_level'],
            percentile=scores['percentile'],
            dimensions=scores['dimensions'],
            ai_insights=ai_insights,
            repo_name=repo_data.name,
            repo_url=repo_url
        )
        
        print(f"  └─ ✓ Complete! Score: {result.total_score}/100 ({result.skill_level})")
        
        return {repo_url: result.dict()}
        
    except Exception as e:
        print(f"  └─ ✗ Failed: {e}")
        return {}


async def main():
    """Cache all demo repositories"""
    print("🚀 GitGrade Demo Cache Generator")
    print("=" * 60)
    
    # Initialize services
    print("\n🔧 Initializing services...")
    try:
        services = {
            'github': GitHubFetcher(),
            'ast': ASTAnalyzer(),
            'metrics': CodeMetricsAnalyzer(),
            'git': GitAnalyzer(),
            'scoring': ScoringEngine(),
            'ai': AIAnalyzer()
        }
        print("✓ All services initialized")
    except Exception as e:
        print(f"✗ Service initialization failed: {e}")
        return
    
    # Cache repositories
    print(f"\n📦 Caching {len(DEMO_REPOS)} repositories...")
    
    cached_results = {}
    for repo_url in DEMO_REPOS:
        result = await cache_repository(repo_url, services)
        cached_results.update(result)
        
        # Small delay to avoid rate limits
        await asyncio.sleep(2)
    
    # Save to cache file
    cache_file = Path(__file__).parent.parent / "cache" / "demo_results.json"
    cache_file.parent.mkdir(exist_ok=True)
    
    with open(cache_file, 'w') as f:
        json.dump(cached_results, f, indent=2, default=str)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Cached {len(cached_results)}/{len(DEMO_REPOS)} repositories")
    print(f"📁 Saved to: {cache_file}")
    print("\n🎯 Demo is ready! All cached repos will load instantly.")
    print("\nCached repositories:")
    for url in cached_results.keys():
        print(f"  • {url}")


if __name__ == "__main__":
    asyncio.run(main())
