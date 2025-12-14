"""
GitHub Repository Fetcher with fallback mechanisms
"""
from github import Github, RateLimitExceededException, UnknownObjectException
from models import RepoData
from utils.helpers import extract_repo_name
import os
import logging

logger = logging.getLogger(__name__)


class EmptyRepositoryError(Exception):
    """Repository has no files"""
    pass


class RateLimitExceeded(Exception):
    """GitHub rate limit exceeded"""
    pass


class RepoNotFound(Exception):
    """Repository not found or private"""
    pass


class GitHubFetcher:
    """Fetch repository data with token rotation"""
    
    def __init__(self):
        # Load all available tokens
        self.tokens = [
            os.getenv("GITHUB_TOKEN"),
            os.getenv("GITHUB_TOKEN_BACKUP_1"),
            os.getenv("GITHUB_TOKEN_BACKUP_2")
        ]
        self.tokens = [t for t in self.tokens if t]
        
        if not self.tokens:
            logger.warning("No GITHUB_TOKEN found - using unauthenticated API (60 req/hr limit)")
            self.github = Github()  # Unauthenticated
            self.tokens = [None]  # Placeholder
        else:
            self.current_index = 0
            self.github = Github(self.tokens[self.current_index])
            logger.info(f"[INFO] GitHubFetcher initialized with {len(self.tokens)} token(s)")
    
    def _rotate_token(self):
        """Switch to next available token"""
        self.current_index = (self.current_index + 1) % len(self.tokens)
        self.github = Github(self.tokens[self.current_index])
        logger.info(f"Rotated to GitHub token {self.current_index + 1}/{len(self.tokens)}")
    
    def check_rate_limit(self) -> int:
        """Check remaining rate limit"""
        try:
            rate_limit = self.github.get_rate_limit()
            return rate_limit.core.remaining
        except:
            return 0
    
    async def fetch_repository(self, repo_url: str) -> RepoData:
        """Fetch repository with automatic token rotation"""
        repo_name = extract_repo_name(repo_url)
        
        for attempt in range(len(self.tokens)):
            try:
                repo = self.github.get_repo(repo_name)
                
                # Check if repo is empty
                if repo.size == 0:
                    raise EmptyRepositoryError("Repository has no files")
                
                # Fetch data
                return RepoData(
                    name=repo.name,
                    description=repo.description or "",
                    url=repo_url,
                    languages=repo.get_languages(),
                    readme=self._fetch_readme(repo),
                    license=repo.license.name if repo.license else None,
                    stars=repo.stargazers_count,
                    forks=repo.forks_count,
                    contributors=repo.get_contributors().totalCount,
                    created_at=repo.created_at,
                    updated_at=repo.updated_at,
                    has_issues=repo.has_issues,
                    has_wiki=repo.has_wiki,
                    default_branch=repo.default_branch,
                    file_structure=self._analyze_structure(repo)
                )
                
            except RateLimitExceededException:
                logger.warning(f"Rate limit on token {self.current_index + 1}")
                if attempt < len(self.tokens) - 1:
                    self._rotate_token()
                else:
                    raise RateLimitExceeded("All GitHub tokens rate limited")
                    
            except UnknownObjectException:
                raise RepoNotFound(f"Repository not found or is private: {repo_name}")
                
            except Exception as e:
                logger.error(f"GitHub fetch failed: {e}")
                raise RepoNotFound(f"Could not fetch repository: {e}")
        
        raise RepoNotFound("All fetch attempts failed")
    
    def _fetch_readme(self, repo) -> str:
        """Fetch README with fallback"""
        try:
            readme = repo.get_readme()
            content = readme.decoded_content.decode('utf-8')
            return content[:10000]  # Limit to 10k chars
        except:
            return ""
    
    def _analyze_structure(self, repo) -> dict:
        """Analyze folder structure"""
        try:
            contents = repo.get_contents("")
            folders = sum(1 for c in contents if c.type == "dir")
            files = sum(1 for c in contents if c.type == "file")
            return {"folders": folders, "files": files}
        except:
            return {"folders": 0, "files": 0}
