"""
Pydantic models for GitGrade API
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Dict, Optional
from datetime import datetime


class AnalyzeRequest(BaseModel):
    """Request model for repository analysis"""
    repo_url: str = Field(..., description="GitHub repository URL")
    
    class Config:
        json_schema_extra = {
            "example": {
                "repo_url": "https://github.com/fastapi/fastapi"
            }
        }


class DimensionScore(BaseModel):
    """Score for a single dimension"""
    score: int
    max_score: int
    signals: List[str]
    formula: str


class AIInsights(BaseModel):
    """AI-generated insights"""
    summary: str
    roadmap: List[Dict[str, str]]
    generated_by: str = "gemini"


class AnalysisResult(BaseModel):
    """Complete analysis result"""
    total_score: int
    max_score: int = 100
    skill_level: str
    percentile: int
    dimensions: Dict[str, DimensionScore]
    ai_insights: AIInsights
    repo_name: str
    repo_url: str
    analyzed_at: datetime = Field(default_factory=datetime.now)


class ProgressUpdate(BaseModel):
    """Progress update for polling"""
    status: str  # starting, analyzing, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[AnalysisResult] = None
    error: Optional[str] = None


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    github_rate_limit: Optional[int] = None
    gemini_available: bool
    cached_repos: int


# Internal data models

class RepoData(BaseModel):
    """Repository metadata"""
    name: str
    description: Optional[str] = None
    url: str
    languages: Dict[str, int]
    readme: str = ""
    license: Optional[str] = None
    stars: int = 0
    forks: int = 0
    contributors: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    has_issues: bool = False
    has_wiki: bool = False
    default_branch: str = "main"
    file_structure: Dict[str, int] = {}


class CodeStructure(BaseModel):
    """AST analysis results"""
    functions: int = 0
    classes: int = 0
    avg_function_length: float = 0.0
    max_nesting_depth: int = 0
    imports: int = 0


class FileMetrics(BaseModel):
    """Code quality metrics for a file"""
    cyclomatic_complexity: float = 0.0
    maintainability_index: float = 0.0
    lines_of_code: int = 0
    comment_ratio: float = 0.0
    halstead_difficulty: float = 0.0
    
    @classmethod
    def default(cls):
        """Return default metrics"""
        return cls()


class GitMetrics(BaseModel):
    """Git workflow metrics"""
    total_commits: int = 0
    recent_commits: int = 0
    avg_commit_message_length: float = 0.0
    unique_contributors: int = 0
    branches: int = 1
    has_conventional_commits: bool = False


class AnalysisData(BaseModel):
    """Complete analysis data (internal)"""
    repo: RepoData
    structure: CodeStructure
    metrics: FileMetrics
    git: GitMetrics
    sample_code: str = ""
