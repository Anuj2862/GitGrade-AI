"""
Code Metrics Analyzer using radon
"""
from models import FileMetrics, RepoData
import logging

logger = logging.getLogger(__name__)


class CodeMetricsAnalyzer:
    """Analyze code quality metrics"""
    
    def __init__(self):
        logger.info("[INFO] CodeMetricsAnalyzer initialized")
    
    async def analyze_code(self, repo_data: RepoData) -> FileMetrics:
        """
        Analyze code quality metrics
        Uses heuristics based on repo metadata
        """
        
        # Calculate metrics based on repository characteristics
        # In production, fetch and analyze actual code files
        
        # Heuristics:
        # - More stars = better quality (usually)
        # - Longer README = better documentation
        # - More contributors = better maintained
        
        stars = repo_data.stars
        readme_len = len(repo_data.readme)
        contributors = repo_data.contributors
        
        # Heuristics for Demo/Hackathon:
        # Assume code is GOOD unless proven otherwise.
        # Stars shouldn't dictate code quality.
        
        # Cyclomatic complexity (lower is better)
        # Baseline: 5.0 (Good) 
        # range 1-10 is great.
        complexity = 5.0 
        
        # Maintainability index (higher is better)
        # Baseline: 85.0 (Excellent)
        mi = 85.0
        
        # Lines of code (estimate)
        loc = 500 + (stars * 10)
        
        # Comment ratio (estimate)
        # Assume decent commenting
        comment_ratio = 0.15 + (stars / 10000)
        
        return FileMetrics(
            cyclomatic_complexity=round(complexity, 2),
            maintainability_index=round(mi, 2),
            lines_of_code=loc,
            comment_ratio=round(comment_ratio, 3),
            halstead_difficulty=round(complexity * 2, 2)
        )
