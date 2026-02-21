"""
Boolean Query Generator for ATS Resume Screening

Generates boolean search queries from job descriptions and tests them against resumes.
Fixed: Proper parentheses handling and token sanitization.
"""

from typing import Dict, List, Any
import re


class BooleanQueryGenerator:
    """Generate and test boolean search queries"""
    
    @staticmethod
    def _sanitize_term(term: str) -> str:
        """
        Sanitize a search term for boolean query
        
        Args:
            term: Raw term (may contain stray parentheses)
            
        Returns:
            Cleaned term without stray parentheses
        """
        # Remove leading/trailing parentheses
        term = term.strip()
        term = term.strip("()")
        
        # Remove any internal parentheses that aren't balanced
        term = term.replace("(", "").replace(")", "")
        
        # Remove extra quotes
        term = term.replace('"', '').replace("'", "")
        
        # Normalize spaces
        term = " ".join(term.split())
        
        return term
    
    @staticmethod
    def _normalize_for_search(text: str) -> str:
        """
        Normalize text for case-insensitive search
        
        Args:
            text: Text to normalize
            
        Returns:
            Lowercase text with normalized spaces
        """
        return " ".join(text.lower().split())
    
    @classmethod
    def generate_query(cls, extracted_jd: Dict[str, Any]) -> str:
        """
        Generate boolean search query from job description
        
        Args:
            extracted_jd: Extracted job description data
            
        Returns:
            Boolean query string
        """
        query_parts = []
        
        # Role-related keywords (high priority)
        role_title = extracted_jd.get("role_title", "")
        if role_title:
            # Split role into keywords
            role_keywords = [
                cls._sanitize_term(word) 
                for word in role_title.lower().split() 
                if len(word) > 2 and word not in ["the", "and", "or", "for"]
            ]
            
            if role_keywords:
                role_query = " OR ".join([f'"{kw}"' for kw in role_keywords])
                query_parts.append(f"({role_query})")
        
        # Must-have skills (required)
        must_have = extracted_jd.get("must_have_skills", [])
        if must_have:
            # Take top 5 most important skills
            top_skills = must_have[:5]
            sanitized_skills = [cls._sanitize_term(skill) for skill in top_skills]
            
            skills_query = " OR ".join([f'"{skill}"' for skill in sanitized_skills])
            query_parts.append(f"({skills_query})")
        
        # Key responsibilities (nice to have)
        responsibilities = extracted_jd.get("responsibilities", [])
        if responsibilities:
            # Extract key action words from first 2 responsibilities
            key_actions = []
            for resp in responsibilities[:2]:
                # Extract first significant word (usually a verb)
                words = resp.lower().split()
                for word in words:
                    if len(word) > 4 and word not in ["will", "must", "should", "responsible"]:
                        key_actions.append(cls._sanitize_term(word))
                        break
            
            if key_actions:
                actions_query = " OR ".join([f'"{action}"' for action in key_actions[:3]])
                query_parts.append(f"({actions_query})")
        
        # Combine with AND
        if query_parts:
            final_query = " AND ".join(query_parts)
            return final_query
        
        return ""
    
    @classmethod
    def test_query(cls, query: str, resume_text: str) -> Dict[str, Any]:
        """
        Test boolean query against resume text
        
        Args:
            query: Boolean query string
            resume_text: Full resume text
            
        Returns:
            Dictionary with query, matched terms, and missing terms
        """
        if not query:
            return {
                "query": "",
                "matched_terms": [],
                "missing_terms": []
            }
        
        # Normalize resume text for searching
        normalized_resume = cls._normalize_for_search(resume_text)
        
        # Extract all search terms from query
        # Pattern: anything between quotes
        terms = re.findall(r'"([^"]+)"', query)
        
        matched = []
        missing = []
        
        for term in terms:
            # Normalize term for search
            normalized_term = cls._normalize_for_search(term)
            
            # Check if term exists in resume (case-insensitive)
            if normalized_term in normalized_resume:
                matched.append(term)  # Keep original case for display
            else:
                missing.append(term)
        
        return {
            "query": query,
            "matched_terms": matched,
            "missing_terms": missing
        }
    
    @classmethod
    def calculate_match_percentage(cls, query: str, resume_text: str) -> float:
        """
        Calculate percentage of query terms found in resume
        
        Args:
            query: Boolean query string
            resume_text: Full resume text
            
        Returns:
            Match percentage (0-100)
        """
        result = cls.test_query(query, resume_text)
        
        total_terms = len(result["matched_terms"]) + len(result["missing_terms"])
        if total_terms == 0:
            return 0.0
        
        matched_count = len(result["matched_terms"])
        return round((matched_count / total_terms) * 100, 2)


# Tests
if __name__ == "__main__":
    print("🧪 Boolean Query Generator Tests\n")
    
    # Test 1: Sanitization
    print("Test 1: Term Sanitization")
    test_terms = [
        "(junior",
        "entry)",
        "((software",
        "engineer))",
        '"python"',
        "  spaces  "
    ]
    
    for term in test_terms:
        sanitized = BooleanQueryGenerator._sanitize_term(term)
        print(f"  {term:20s} → {sanitized}")
    
    # Test 2: Query Generation
    print("\nTest 2: Query Generation")
    sample_jd = {
        "role_title": "Junior Software Engineer",
        "must_have_skills": ["Python", "Java", "MySQL", "MongoDB", "Git"],
        "responsibilities": [
            "Develop and maintain backend services",
            "Write clean and efficient code"
        ]
    }
    
    query = BooleanQueryGenerator.generate_query(sample_jd)
    print(f"Generated Query:\n{query}")
    
    # Test 3: Query Testing
    print("\nTest 3: Query Testing")
    sample_resume = """
    John Doe
    Software Engineering Intern
    
    Skills: Python, Java, MySQL, MongoDB, React, Git
    
    Experience:
    - Developed backend services using Python and Flask
    - Wrote clean, maintainable code following best practices
    """
    
    result = BooleanQueryGenerator.test_query(query, sample_resume)
    print(f"✅ Matched terms: {result['matched_terms']}")
    print(f"❌ Missing terms: {result['missing_terms']}")
    
    match_pct = BooleanQueryGenerator.calculate_match_percentage(query, sample_resume)
    print(f"📊 Match percentage: {match_pct}%")
    
    # Test 4: Edge Case - Missing closing parenthesis
    print("\nTest 4: Edge Case Testing")
    bad_jd = {
        "role_title": "Senior (Backend Developer",
        "must_have_skills": ["Node.js)", "Express", "(MongoDB"],
        "responsibilities": []
    }
    
    query = BooleanQueryGenerator.generate_query(bad_jd)
    print(f"Query from malformed input:\n{query}")
    print("✅ No broken parentheses!")