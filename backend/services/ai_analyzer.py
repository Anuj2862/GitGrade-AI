"""
AI Analyzer with Gemini 1.5 Pro and comprehensive fallbacks
AI does not guess scores. It explains them.
"""
import google.generativeai as genai
from models import AIInsights, AnalysisData
import os
import logging
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class AIAnalyzer:
    """Generate AI insights with multiple fallback layers"""
    
    def __init__(self):
        # Load all available API keys
        self.api_keys = [
            os.getenv("GEMINI_API_KEY"),
            os.getenv("GEMINI_API_KEY_BACKUP_1"),
            os.getenv("GEMINI_API_KEY_BACKUP_2")
        ]
        self.api_keys = [k for k in self.api_keys if k]
        
        if not self.api_keys:
            logger.warning("No Gemini API keys found - will use rule-based fallback")
            self.model = None
        else:
            self.current_key_index = 0
            self._configure_api()
            logger.info(f"[INFO] AIAnalyzer initialized with {len(self.api_keys)} key(s)")
        
        # Load cache
        self.cache = self._load_cache()
    
    def _configure_api(self):
        """Configure Gemini with current API key"""
        try:
            genai.configure(api_key=self.api_keys[self.current_key_index])
            self.model = genai.GenerativeModel('gemini-1.5-pro')
        except Exception as e:
            logger.error(f"Gemini configuration failed: {e}")
            self.model = None
    
    def _rotate_key(self):
        """Switch to next API key"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self._configure_api()
        logger.info(f"Rotated to Gemini key {self.current_key_index + 1}/{len(self.api_keys)}")
    
    def check_availability(self) -> bool:
        """Check if Gemini is available"""
        return self.model is not None
    
    async def generate_insights(self, data: AnalysisData, scores: dict) -> AIInsights:
        """Generate AI insights with fallback chain"""
        
        # Layer 1: Check cache
        cache_key = data.repo.url
        if cache_key in self.cache:
            logger.info("Using cached AI insights")
            return AIInsights(**self.cache[cache_key])
        
        # Layer 2: Try Gemini API
        if self.model:
            for attempt in range(len(self.api_keys)):
                try:
                    insights = await self._call_gemini(data, scores)
                    # Cache successful result
                    self.cache[cache_key] = insights.dict()
                    self._save_cache()
                    return insights
                except Exception as e:
                    logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")
                    if attempt < len(self.api_keys) - 1:
                        self._rotate_key()
        
        # Layer 3: Rule-based fallback (ALWAYS works)
        logger.info("Using rule-based AI fallback")
        return self._generate_rule_based_insights(data, scores)
    
    async def _call_gemini(self, data: AnalysisData, scores: dict) -> AIInsights:
        """Call Gemini API with structured prompt"""
        
        # Create structured summary (NOT raw code)
        summary = self._create_summary(data, scores)
        
        # Create dynamic context with file proofs to force unique content
        file_proofs = ", ".join(list(data.repo.file_structure.get('files', []))[:5])
        sinals_str = "; ".join([s for d in scores.values() for s in d.signals])
        
        prompt = f"""You are a senior software engineer mentoring a student at a Hackathon.
        
        Analyze this SPECIFIC repository. Do not give generic advice.
        
        REPO METRICS:
        - Files detected: {file_proofs}...
        - Key Signals: {sinals_str}
        - Description: {data.repo.description}
        - Readme Snippet: {data.repo.readme[:200]}...

        Your Goal: Provide HIGHLY SPECIFIC feedback based on the files and signals above.
        Mention specific file names or signals in your summary to prove you read it.

        Format your response as JSON with these exact keys:
        {{
          "summary": "2-3 sentences. start with 'I noticed you have [specific file/feature]...'. Be very encouraging.",
          "roadmap": [
            {{"item": "Specific Step 1 (mention a file)", "reason": "Why this helps"}},
            {{"item": "Specific Step 2", "reason": "Why this helps"}},
            {{"item": "Specific Step 3", "reason": "Why this helps"}},
            {{"item": "Specific Step 4", "reason": "Why this helps"}},
            {{"item": "Specific Step 5", "reason": "Why this helps"}}
          ]
        }}
        """
        
        response = self.model.generate_content(
            prompt,
            generation_config={
                'response_mime_type': 'application/json',
                'temperature': 0.7
            }
        )
        
        # Parse response
        result = json.loads(response.text)
        
        return AIInsights(
            summary=result['summary'],
            roadmap=result['roadmap'],
            generated_by="gemini"
        )
    
    def _create_summary(self, data: AnalysisData, scores: dict) -> str:
        """Create structured summary for AI (NOT raw code)"""
        return f"""
Repository: {data.repo.name}
URL: {data.repo.url}
Languages: {', '.join(data.repo.languages.keys())}
Stars: {data.repo.stars} | Forks: {data.repo.forks} | Contributors: {data.repo.contributors}

Overall Score: {scores['total_score']}/100 ({scores['skill_level']})
Percentile: Better than {scores['percentile']}% of repositories

Dimension Scores:
- Code Quality: {scores['dimensions']['code_quality'].score}/18
- Documentation: {scores['dimensions']['documentation'].score}/15
- Testing: {scores['dimensions']['testing'].score}/12
- Security: {scores['dimensions']['security'].score}/10
- Git Workflow: {scores['dimensions']['git_workflow'].score}/13
- Architecture: {scores['dimensions']['architecture'].score}/12
- Real-world: {scores['dimensions']['real_world'].score}/12
- Innovation: {scores['dimensions']['innovation'].score}/8

Key Metrics:
- Complexity: {data.metrics.cyclomatic_complexity}
- Maintainability: {data.metrics.maintainability_index}
- Comments: {data.metrics.comment_ratio:.1%}
- Commits: {data.git.total_commits} (recent: {data.git.recent_commits})

README Preview:
{data.repo.readme[:500]}...
"""
    
    def _generate_rule_based_insights(self, data: AnalysisData, scores: dict) -> AIInsights:
        """Rule-based fallback (NEVER fails)"""
        
        score = scores['total_score']
        level = scores['skill_level']
        
        # Generate summary based on score
        if score >= 80:
            summary = (
                f"This repository demonstrates strong software engineering practices "
                f"with a score of {score}/100 ({level}). The code quality is excellent, "
                f"and the project structure is well-organized. This reflects professional-level "
                f"development that would impress recruiters."
            )
        elif score >= 60:
            summary = (
                f"This repository shows solid fundamentals with a score of {score}/100 ({level}). "
                f"The project has a good foundation, and with improvements to testing and "
                f"documentation, it could reach professional quality. You're on the right track!"
            )
        elif score >= 40:
            summary = (
                f"This repository demonstrates basic competency with a score of {score}/100 ({level}). "
                f"There's clear potential here, but significant improvements in code quality, "
                f"documentation, and development practices would make this more recruiter-ready."
            )
        else:
            summary = (
                f"This repository is a good start with a score of {score}/100 ({level}). "
                f"Focus on the fundamentals: clean code, clear documentation, and consistent "
                f"git practices. Every expert was once a beginner - keep building!"
            )
        
        # Generate roadmap from weakest dimensions
        roadmap = self._generate_roadmap_from_scores(scores['dimensions'])
        
        return AIInsights(
            summary=summary,
            roadmap=roadmap,
            generated_by="rule-based-fallback"
        )
    
    def _generate_roadmap_from_scores(self, dimensions: dict) -> list:
        """Generate roadmap based on weakest dimensions"""
        
        # Calculate percentage for each dimension
        dim_percentages = {
            name: (dim.score / dim.max_score) * 100
            for name, dim in dimensions.items()
        }
        
        # Sort by percentage (weakest first)
        sorted_dims = sorted(dim_percentages.items(), key=lambda x: x[1])
        
        # Map dimensions to improvements
        improvements = {
            'code_quality': {
                'item': 'Reduce code complexity and improve maintainability',
                'reason': 'Lower complexity makes code easier to understand and modify'
            },
            'documentation': {
                'item': 'Add comprehensive README with setup and usage instructions',
                'reason': 'Good documentation helps users and shows professionalism'
            },
            'testing': {
                'item': 'Implement unit tests for core functionality',
                'reason': 'Tests improve reliability and make refactoring safer'
            },
            'git_workflow': {
                'item': 'Use conventional commit messages and consistent workflow',
                'reason': 'Clear commit history shows professional development practices'
            },
            'security': {
                'item': 'Add input validation and error handling',
                'reason': 'Security best practices are essential for production code'
            },
            'architecture': {
                'item': 'Improve folder structure and separation of concerns',
                'reason': 'Clean architecture makes the codebase more maintainable'
            },
            'real_world': {
                'item': 'Add production-ready features and deployment instructions',
                'reason': 'Shows the project is ready for real-world use'
            },
            'innovation': {
                'item': 'Implement advanced features or unique solutions',
                'reason': 'Innovation demonstrates technical depth and creativity'
            }
        }
        
        # Return top 5 improvements
        roadmap = []
        for dim_name, _ in sorted_dims[:5]:
            if dim_name in improvements:
                roadmap.append(improvements[dim_name])
        
        return roadmap
    
    def _load_cache(self) -> dict:
        """Load cached AI responses"""
        cache_file = Path("cache/ai_cache.json")
        if cache_file.exists():
            try:
                with open(cache_file) as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_cache(self):
        """Save AI cache"""
        try:
            cache_file = Path("cache/ai_cache.json")
            cache_file.parent.mkdir(exist_ok=True)
            with open(cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save AI cache: {e}")
