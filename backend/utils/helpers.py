"""
Helper utility functions
"""
import uuid
import re
from datetime import datetime, timedelta


def generate_task_id() -> str:
    """Generate unique task ID"""
    return str(uuid.uuid4())[:8]


def is_valid_github_url(url: str) -> bool:
    """Validate GitHub repository URL"""
    pattern = r'^https://github\.com/[\w-]+/[\w.-]+/?$'
    return bool(re.match(pattern, url))


def extract_repo_name(url: str) -> str:
    """Extract owner/repo from GitHub URL"""
    # https://github.com/owner/repo -> owner/repo
    match = re.search(r'github\.com/([\w-]+/[\w.-]+)', url)
    if match:
        return match.group(1).rstrip('/')
    raise ValueError(f"Could not extract repo name from {url}")


def is_recent(timestamp: datetime, days: int = 30) -> bool:
    """Check if timestamp is within last N days"""
    if isinstance(timestamp, (int, float)):
        timestamp = datetime.fromtimestamp(timestamp)
    return datetime.now() - timestamp < timedelta(days=days)


def calculate_percentile(score: int) -> int:
    """
    Calculate percentile based on score
    In production, use actual historical data
    """
    if score >= 90:
        return 95
    elif score >= 80:
        return 85
    elif score >= 70:
        return 70
    elif score >= 60:
        return 55
    elif score >= 50:
        return 40
    elif score >= 40:
        return 30
    else:
        return max(10, score // 2)
