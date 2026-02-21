"""
Skill Evidence Scoring

Deterministic evidence-based scoring for technical skills.
Start with Python, extensible to other skills.

Scoring breakdown:
- Base listing: 20 points
- Used in projects: +30 points
- Used in experience roles: +25 points
- Framework/library usage: +15 points
- Quantified impact: +10 points
- Cap at 100 points
"""

import re
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class SkillEvidenceScorer:
    """Evidence-based skill scoring (deterministic)"""
    
    # Python-related frameworks and libraries
    PYTHON_FRAMEWORKS = {
        "django", "flask", "fastapi", "pyramid", "tornado",
        "pandas", "numpy", "scipy", "scikit-learn", "sklearn",
        "tensorflow", "pytorch", "keras", "transformers",
        "requests", "beautifulsoup", "scrapy", "selenium",
        "pytest", "unittest", "sqlalchemy", "celery"
    }
    
    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Normalize text for matching: lowercase, no special chars"""
        if not text:
            return ""
        return re.sub(r'[^a-z0-9\s]', '', text.lower())
    
    @classmethod
    def contains_metrics(cls, text: str) -> bool:
        """
        Check if text contains quantified metrics
        
        Patterns:
        - Percentages: 50%, 99.9%
        - Multipliers: 2x, 10x
        - Large numbers: 1000+, 10k, 1M
        - Time: 50ms, 2s
        - Users/scale: 100k users, 1M requests
        """
        if not text:
            return False
        
        patterns = [
            r'\d+%',  # 50%
            r'\d+x',  # 2x
            r'\d+k',  # 10k
            r'\d+m',  # 1M
            r'\d+\s*(users|requests|records|rows|queries)',  # 100k users
            r'\d+\s*(ms|seconds?|minutes?|hours?)',  # 50ms
            r'(increased|reduced|improved|decreased)\s+by\s+\d+',  # improved by 20
        ]
        
        text_lower = text.lower()
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    @classmethod
    def extract_python_evidence(cls, extracted_resume: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract evidence of Python skill usage from resume.
        
        Returns:
        {
            "listed": bool,
            "projects": bool,
            "experience": bool,
            "frameworks": bool,
            "metrics": bool,
            "score": int (0-100)
        }
        """
        evidence = {
            "listed": False,
            "projects": False,
            "experience": False,
            "frameworks": False,
            "metrics": False,
            "score": 0
        }
        
        # Check 1: Listed in skills section (20 points)
        skills = extracted_resume.get("skills", [])
        skills_normalized = [cls.normalize_text(s) for s in skills]
        
        if "python" in skills_normalized or "py" in skills_normalized:
            evidence["listed"] = True
            evidence["score"] += 20
            logger.info("✓ Python listed in skills (+20)")
        
        # Check 2: Used in projects (30 points)
        projects = extracted_resume.get("projects", [])
        for project in projects:
            # Check technologies
            technologies = project.get("technologies", [])
            tech_text = " ".join([cls.normalize_text(t) for t in technologies])
            
            # Check description
            description = cls.normalize_text(project.get("description", ""))
            
            if "python" in tech_text or "python" in description or "py" in tech_text:
                evidence["projects"] = True
                evidence["score"] += 30
                logger.info("✓ Python used in projects (+30)")
                break
        
        # Check 3: Used in experience roles (25 points)
        roles = extracted_resume.get("roles", [])
        for role in roles:
            # Check bullets
            bullets = role.get("bullets", [])
            bullets_text = " ".join([cls.normalize_text(b) for b in bullets])
            
            # Check title
            title_text = cls.normalize_text(role.get("title", ""))
            
            if "python" in bullets_text or "python" in title_text:
                evidence["experience"] = True
                evidence["score"] += 25
                logger.info("✓ Python used in experience (+25)")
                break
        
        # Check 4: Framework/library usage (15 points)
        # Search across all text for Python frameworks
        all_text = cls.normalize_text(
            " ".join(skills) + " " +
            " ".join([p.get("description", "") for p in projects]) + " " +
            " ".join([" ".join(p.get("technologies", [])) for p in projects]) + " " +
            " ".join([" ".join(r.get("bullets", [])) for r in roles])
        )
        
        for framework in cls.PYTHON_FRAMEWORKS:
            if framework in all_text:
                evidence["frameworks"] = True
                evidence["score"] += 15
                logger.info(f"✓ Python framework detected: {framework} (+15)")
                break
        
        # Check 5: Quantified impact (10 points)
        # Look for metrics in Python-related bullets/projects
        python_related_text = []
        
        # Get Python-related project descriptions
        for project in projects:
            tech_text = " ".join([cls.normalize_text(t) for t in project.get("technologies", [])])
            if "python" in tech_text:
                python_related_text.append(project.get("description", ""))
        
        # Get Python-related role bullets
        for role in roles:
            for bullet in role.get("bullets", []):
                if "python" in cls.normalize_text(bullet):
                    python_related_text.append(bullet)
        
        # Check for metrics in Python context
        for text in python_related_text:
            if cls.contains_metrics(text):
                evidence["metrics"] = True
                evidence["score"] += 10
                logger.info("✓ Quantified Python impact detected (+10)")
                break
        
        # Cap at 100
        evidence["score"] = min(evidence["score"], 100)
        
        logger.info(f"Python evidence score: {evidence['score']}/100 "
                   f"(listed:{evidence['listed']}, projects:{evidence['projects']}, "
                   f"experience:{evidence['experience']}, frameworks:{evidence['frameworks']}, "
                   f"metrics:{evidence['metrics']})")
        
        return evidence
    
    @classmethod
    def compute_python_weight(cls, evidence: Dict[str, Any]) -> float:
        """
        Convert Python evidence score to ATS weight (0.0-1.0)
        
        Args:
            evidence: Output from extract_python_evidence
            
        Returns:
            Weight multiplier (0.0 to 1.0)
        """
        score = evidence.get("score", 0)
        weight = score / 100.0
        
        logger.info(f"Python weight: {weight:.2f} (score: {score}/100)")
        return weight
    
    @classmethod
    def apply_skill_evidence_to_must_have(
        cls,
        must_have_skills: List[str],
        evidence_scores: Dict[str, Dict[str, Any]],
        base_must_have_points: float = 50.0
    ) -> float:
        """
        Apply evidence-based weighting to must-have skills scoring
        
        Args:
            must_have_skills: List of required skills from JD
            evidence_scores: Dict mapping skill_name -> evidence dict
            base_must_have_points: Maximum points for must-have section
            
        Returns:
            Adjusted must-have points based on evidence weights
        """
        if not must_have_skills:
            return 0.0
        
        # For now, only handle Python
        # Future: extend to all must-have skills
        python_in_must_have = any(
            "python" in skill.lower() or skill.lower() == "py"
            for skill in must_have_skills
        )
        
        if not python_in_must_have:
            # Python not required, return full base points
            # (assuming other skills are matched via existing logic)
            return base_must_have_points
        
        # Get Python evidence
        python_evidence = evidence_scores.get("python", {})
        python_weight = cls.compute_python_weight(python_evidence)
        
        # Calculate weighted must-have score
        # If Python is 1 of 5 skills and has 60% weight:
        # - Other 4 skills: (4/5) * 50 = 40 points
        # - Python: (1/5) * 50 * 0.6 = 6 points
        # - Total: 46 points (reduced from 50)
        
        # Simplified: Apply Python weight to the entire must-have score
        # (This assumes Python is a significant skill in must-have list)
        weighted_score = base_must_have_points * python_weight
        
        logger.info(f"Must-have adjusted: {base_must_have_points} → {weighted_score:.1f} "
                   f"(Python weight: {python_weight:.2f})")
        
        return weighted_score


# Tests
if __name__ == "__main__":
    print("🧪 Skill Evidence Scoring Tests\n")
    
    # Test 1: Extract Python evidence
    print("Test 1: Python Evidence Extraction")
    
    sample_resume = {
        "skills": ["Python", "Java", "JavaScript", "MySQL"],
        "projects": [
            {
                "name": "ML Pipeline",
                "description": "Built data pipeline using Python and pandas to process 1M records",
                "technologies": ["Python", "Pandas", "NumPy"]
            },
            {
                "name": "Web Scraper",
                "description": "Automated data collection",
                "technologies": ["Node.js"]
            }
        ],
        "roles": [
            {
                "company": "Tech Corp",
                "title": "Software Engineer",
                "bullets": [
                    "Developed backend APIs using Python and FastAPI",
                    "Reduced query time by 40% through optimization",
                    "Wrote comprehensive unit tests"
                ]
            }
        ]
    }
    
    evidence = SkillEvidenceScorer.extract_python_evidence(sample_resume)
    print(f"Evidence: {evidence}")
    print(f"Score: {evidence['score']}/100")
    
    # Test 2: Weight calculation
    print("\nTest 2: Weight Calculation")
    weight = SkillEvidenceScorer.compute_python_weight(evidence)
    print(f"Weight: {weight:.2f}")
    
    # Test 3: Must-have adjustment
    print("\nTest 3: Must-Have Score Adjustment")
    must_have_skills = ["Python", "SQL", "Git"]
    evidence_scores = {"python": evidence}
    
    adjusted = SkillEvidenceScorer.apply_skill_evidence_to_must_have(
        must_have_skills,
        evidence_scores,
        base_must_have_points=50.0
    )
    print(f"Adjusted must-have: {adjusted:.1f}/50.0")
    
    # Test 4: Low evidence
    print("\nTest 4: Low Evidence Scenario")
    low_evidence_resume = {
        "skills": ["Python"],
        "projects": [],
        "roles": []
    }
    
    low_evidence = SkillEvidenceScorer.extract_python_evidence(low_evidence_resume)
    print(f"Low evidence: {low_evidence}")
    low_weight = SkillEvidenceScorer.compute_python_weight(low_evidence)
    print(f"Low weight: {low_weight:.2f}")
