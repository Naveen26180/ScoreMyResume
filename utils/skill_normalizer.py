"""
Skill Normalization Utility

Fixes false negatives in skill matching caused by:
- Case differences: "MySQL" vs "mysql"
- Spacing: "My SQL" vs "MySQL"
- Abbreviations: "JS" vs "JavaScript"
"""

from typing import List, Set
import re


class SkillNormalizer:
    """Normalize skills for accurate matching"""
    
    # Common technology aliases
    ALIASES = {
        # Languages
        "js": "javascript",
        "ts": "typescript",
        "py": "python",
        "c++": "cpp",
        "c#": "csharp",
        
        # Databases
        "mysql": "mysql",
        "my sql": "mysql",
        "postgres": "postgresql",
        "postgre": "postgresql",
        "mongo": "mongodb",
        "mongo db": "mongodb",
        
        # Frontend
        "react": "react",
        "reactjs": "react",
        "react.js": "react",
        "vue": "vuejs",
        "vue.js": "vuejs",
        "angular": "angular",
        "angularjs": "angular",
        
        # Backend
        "node": "nodejs",
        "nodejs": "nodejs",
        "node.js": "nodejs",
        "express": "expressjs",
        "express.js": "expressjs",
        
        # ML/AI
        "ml": "machine learning",
        "machinelearning": "machine learning",
        "ai": "artificial intelligence",
        "nlp": "natural language processing",
        "cv": "computer vision",
        
        # Cloud
        "aws": "amazon web services",
        "gcp": "google cloud platform",
        "azure": "microsoft azure",
        
        # Other
        "rest": "rest api",
        "restful": "rest api",
        "graphql": "graphql",
        "docker": "docker",
        "k8s": "kubernetes",
        "git": "git",
        "github": "git",
        "gitlab": "git",
    }
    
    @classmethod
    def normalize(cls, skill: str) -> str:
        """
        Normalize a single skill to its canonical form
        
        Args:
            skill: Raw skill string (e.g., "My SQL", "ReactJS")
            
        Returns:
            Normalized skill (e.g., "mysql", "react")
        """
        if not skill:
            return ""
        
        # Step 1: Lowercase
        normalized = skill.lower()
        
        # Step 2: Remove extra spaces
        normalized = " ".join(normalized.split())
        
        # Step 3: Remove special chars (keep letters, numbers, spaces, +, #, .)
        normalized = re.sub(r'[^a-z0-9\s+#.]', '', normalized)
        
        # Step 4: Apply alias mapping
        normalized = cls.ALIASES.get(normalized, normalized)
        
        # Step 5: Remove spaces for final comparison
        normalized = normalized.replace(" ", "")
        
        return normalized
    
    @classmethod
    def normalize_list(cls, skills: List[str]) -> Set[str]:
        """
        Normalize a list of skills
        
        Args:
            skills: List of raw skill strings
            
        Returns:
            Set of normalized skills
        """
        return {cls.normalize(skill) for skill in skills if skill}
    
    @classmethod
    def match_skills(
        cls,
        resume_skills: List[str],
        required_skills: List[str]
    ) -> tuple[List[str], List[str]]:
        """
        Match resume skills against required skills
        
        Args:
            resume_skills: Skills from resume
            required_skills: Skills from job description
            
        Returns:
            (matched_skills, missing_skills) - both as original strings from JD
        """
        # Normalize both sides
        normalized_resume = cls.normalize_list(resume_skills)
        
        matched = []
        missing = []
        
        for required in required_skills:
            normalized_required = cls.normalize(required)
            
            if normalized_required in normalized_resume:
                matched.append(required)  # Keep original JD format
            else:
                missing.append(required)
        
        return matched, missing
    
    @classmethod
    def create_semantic_variants(cls, skill: str) -> Set[str]:
        """
        Create semantic variants of a skill for fuzzy matching
        
        Args:
            skill: Base skill (e.g., "Python")
            
        Returns:
            Set of variants (e.g., {"python", "py", "python3"})
        """
        variants = {cls.normalize(skill)}
        
        # Add reverse lookups from aliases
        normalized = cls.normalize(skill)
        for alias, canonical in cls.ALIASES.items():
            if canonical == normalized:
                variants.add(alias)
        
        # Add common suffixes for languages
        if normalized in ["python", "java", "javascript", "typescript"]:
            variants.add(f"{normalized}3")  # python3, java3, etc.
        
        return variants


# Example usage and tests
if __name__ == "__main__":
    # Test normalization
    test_cases = [
        ("MySQL", "mysql"),
        ("My SQL", "mysql"),
        ("ReactJS", "react"),
        ("React.js", "react"),
        ("Node", "nodejs"),
        ("Node.js", "nodejs"),
        ("MongoDB", "mongodb"),
        ("Mongo DB", "mongodb"),
        ("JS", "javascript"),
        ("Python", "python"),
        ("Java", "java"),
    ]
    
    print("🧪 Normalization Tests:")
    for input_skill, expected in test_cases:
        result = SkillNormalizer.normalize(input_skill)
        status = "✅" if result == expected else "❌"
        print(f"{status} {input_skill:15s} → {result:15s} (expected: {expected})")
    
    # Test matching
    print("\n🧪 Matching Test:")
    resume_skills = ["Python", "Java", "My SQL", "Mongo DB", "ReactJS"]
    required_skills = ["Python", "Java", "MySQL", "MongoDB", "React"]
    
    matched, missing = SkillNormalizer.match_skills(resume_skills, required_skills)
    print(f"Resume: {resume_skills}")
    print(f"Required: {required_skills}")
    print(f"✅ Matched: {matched}")
    print(f"❌ Missing: {missing}")
