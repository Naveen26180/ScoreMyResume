"""
Deterministic ATS Scoring Engine
================================
Uses Groq-extracted data (not local extraction) + SentenceTransformer embeddings
to calculate a reproducible, context-aware ATS score.

Key concept: "Semantically matched but keyword missing"
  - ML matches Machine Learning semantically → skill IS matched
  - But "Machine Learning" (exact phrase) is not in resume text → keyword gap
  - The improvement report tells user: "Add 'Machine Learning' to your resume"
"""

import re
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# SKILL EQUIVALENCE TABLE (~80 entries)
# Fallback for cases where embeddings might miss abbreviations
# ═══════════════════════════════════════════════════════════
SKILL_ALIASES: Dict[str, List[str]] = {
    # Languages
    "javascript": ["js", "ecmascript", "es6", "es2015"],
    "typescript": ["ts"],
    "python": ["py", "python3"],
    "c++": ["cpp", "cplusplus", "c plus plus"],
    "c#": ["csharp", "c sharp"],
    "golang": ["go"],
    "ruby on rails": ["rails", "ror"],
    
    # Frontend
    "react": ["reactjs", "react.js", "react js"],
    "angular": ["angularjs", "angular.js", "angular js"],
    "vue": ["vuejs", "vue.js", "vue js"],
    "next.js": ["nextjs", "next js", "next"],
    "svelte": ["sveltejs", "sveltekit"],
    "tailwind css": ["tailwindcss", "tailwind"],
    
    # Backend
    "node.js": ["nodejs", "node js", "node"],
    "express": ["expressjs", "express.js"],
    "django": ["django rest framework", "drf"],
    "spring boot": ["spring", "spring framework", "springboot"],
    "flask": ["flask api"],
    "fastapi": ["fast api"],
    ".net": ["dotnet", "asp.net", "asp net"],
    
    # Databases
    "postgresql": ["postgres", "psql", "pg"],
    "mongodb": ["mongo", "mongo db"],
    "mysql": ["my sql"],
    "microsoft sql server": ["mssql", "sql server", "ms sql"],
    "redis": ["redis cache"],
    "elasticsearch": ["elastic search", "elastic"],
    "dynamodb": ["dynamo db", "dynamo"],
    
    # Cloud & DevOps
    "amazon web services": ["aws"],
    "google cloud platform": ["gcp", "google cloud"],
    "microsoft azure": ["azure"],
    "kubernetes": ["k8s", "kube"],
    "docker": ["containerization", "containers"],
    "terraform": ["tf", "iac", "infrastructure as code"],
    "continuous integration": ["ci"],
    "continuous deployment": ["cd"],
    "ci/cd": ["cicd", "ci cd", "continuous integration/continuous deployment"],
    "jenkins": ["jenkins pipeline"],
    "github actions": ["gh actions"],
    
    # AI/ML
    "machine learning": ["ml"],
    "deep learning": ["dl"],
    "artificial intelligence": ["ai"],
    "natural language processing": ["nlp"],
    "computer vision": ["cv"],
    "large language models": ["llm", "llms"],
    "tensorflow": ["tf", "tensor flow"],
    "pytorch": ["torch"],
    "scikit-learn": ["sklearn", "scikit learn"],
    "data science": ["data analytics"],
    
    # Practices
    "agile": ["agile methodology", "agile development"],
    "scrum": ["scrum master", "scrum methodology"],
    "test-driven development": ["tdd"],
    "behavior-driven development": ["bdd"],
    "object-oriented programming": ["oop", "object oriented"],
    "rest api": ["restful", "rest", "restful api"],
    "graphql": ["graph ql"],
    "microservices": ["micro services", "microservice architecture"],
    "serverless": ["lambda", "faas"],
    
    # Tools
    "git": ["github", "gitlab", "version control"],
    "jira": ["jira board"],
    "figma": ["figma design"],
    "postman": ["postman api"],
    "swagger": ["openapi", "swagger ui"],
    "linux": ["unix", "ubuntu", "centos"],
}


class DeterministicATSEngine:
    """
    Deterministic ATS scoring engine.
    
    Flow:
    1. Receives Groq-extracted resume + JD data (skills, roles, etc.)
    2. Matches skills using embeddings + alias table
    3. Detects keyword gaps (semantically matched but exact phrase missing)
    4. Calculates score using weighted formula (seniority-aware)
    5. Returns deterministic score + breakdown + keyword gaps
    """
    
    def __init__(self, embedding_model=None):
        self.model = embedding_model
        self._embedding_cache: Dict[str, np.ndarray] = {}
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding with caching"""
        key = text.lower().strip()
        if key not in self._embedding_cache:
            self._embedding_cache[key] = self.model.encode(key)
        return self._embedding_cache[key]
    
    def _cosine_sim(self, a: np.ndarray, b: np.ndarray) -> float:
        """Cosine similarity between two vectors"""
        dot = np.dot(a, b)
        norm = np.linalg.norm(a) * np.linalg.norm(b)
        if norm == 0:
            return 0.0
        return float(dot / norm)
    
    # ═══════════════════════════════════════════════════════
    # SKILL MATCHING (Embeddings + Aliases + Exact)
    # ═══════════════════════════════════════════════════════
    
    def match_skills(
        self,
        jd_skills: List[str],
        resume_skills: List[str],
        resume_text: str
    ) -> Dict[str, Any]:
        """
        Match JD skills against resume skills using 3 layers:
        1. Exact match (case-insensitive)
        2. Alias table match
        3. Embedding similarity (cosine > 0.78)
        
        Also detects KEYWORD GAPS: skills that match semantically but
        the exact JD phrase is missing from the resume text.
        """
        if not jd_skills:
            return {
                "matched_skills": [],
                "missing_skills": [],
                "keyword_gaps": [],
                "match_ratio": 1.0
            }
        
        resume_text_lower = resume_text.lower()
        resume_skills_lower = [s.lower().strip() for s in resume_skills]
        resume_skills_set = set(resume_skills_lower)
        
        matched = []
        missing = []
        keyword_gaps = []
        
        for jd_skill in jd_skills:
            jd_lower = jd_skill.lower().strip()
            match_result = self._match_single_skill(
                jd_lower, resume_skills_set, resume_skills_lower
            )
            
            if match_result["matched"]:
                matched.append(jd_skill)
                # KEYWORD GAP CHECK
                if jd_lower not in resume_text_lower:
                    keyword_gaps.append({
                        "skill": jd_skill,
                        "matched_via": match_result["matched_via"],
                        "type": match_result["match_type"]
                    })
            else:
                missing.append(jd_skill)
        
        total = len(jd_skills)
        return {
            "matched_skills": matched,
            "missing_skills": missing,
            "keyword_gaps": keyword_gaps,
            "match_ratio": len(matched) / total if total > 0 else 1.0
        }
    
    def _match_single_skill(
        self, jd_skill: str, resume_set: set, resume_list: List[str]
    ) -> Dict[str, Any]:
        """Match a single JD skill against all resume skills"""
        
        # Layer 1: Exact match
        if jd_skill in resume_set:
            return {"matched": True, "matched_via": jd_skill, "match_type": "exact"}
        
        # Layer 1b: Substring containment
        for rs in resume_list:
            if len(jd_skill) >= 3 and len(rs) >= 3:
                if jd_skill in rs or rs in jd_skill:
                    return {"matched": True, "matched_via": rs, "match_type": "substring"}
        
        # Layer 2: Alias table
        alias_match = self._check_alias(jd_skill, resume_list)
        if alias_match:
            return {"matched": True, "matched_via": alias_match, "match_type": "alias"}
        
        # Layer 3: Embedding similarity
        if self.model is not None:
            best_match, best_score = self._embedding_match(jd_skill, resume_list)
            if best_score >= 0.78:
                return {
                    "matched": True,
                    "matched_via": best_match,
                    "match_type": "semantic",
                }
        
        return {"matched": False, "matched_via": None, "match_type": None}
    
    def _check_alias(self, jd_skill: str, resume_skills: List[str]) -> Optional[str]:
        """Check alias table for match"""
        for canonical, aliases in SKILL_ALIASES.items():
            all_forms = [canonical] + aliases
            jd_matches = jd_skill in all_forms
            if jd_matches:
                for rs in resume_skills:
                    if rs in all_forms:
                        return rs
            for rs in resume_skills:
                if rs in all_forms and jd_skill in all_forms:
                    return rs
        return None
    
    def _embedding_match(
        self, jd_skill: str, resume_skills: List[str]
    ) -> Tuple[str, float]:
        """Find best embedding match"""
        if not resume_skills:
            return ("", 0.0)
        
        jd_emb = self._get_embedding(jd_skill)
        best_match = ""
        best_score = 0.0
        
        for rs in resume_skills:
            rs_emb = self._get_embedding(rs)
            score = self._cosine_sim(jd_emb, rs_emb)
            if score > best_score:
                best_score = score
                best_match = rs
        
        return (best_match, best_score)
    
    # ═══════════════════════════════════════════════════════
    # SENIORITY DETECTION
    # ═══════════════════════════════════════════════════════
    
    def detect_seniority(self, extracted_jd: Dict[str, Any]) -> str:
        """Detect job seniority level: entry, mid, senior"""
        seniority = extracted_jd.get("seniority", "").lower()
        role_title = extracted_jd.get("role_title", "").lower()
        years = extracted_jd.get("years_required", 0) or 0
        
        entry_kw = ["junior", "entry", "entry-level", "intern", "graduate", "fresher", "trainee"]
        senior_kw = ["senior", "lead", "principal", "staff", "architect", "director", "head"]
        
        if any(kw in seniority for kw in entry_kw) or any(kw in role_title for kw in entry_kw) or years <= 2:
            return "entry"
        if any(kw in seniority for kw in senior_kw) or any(kw in role_title for kw in senior_kw) or years >= 5:
            return "senior"
        return "mid"
    
    # ═══════════════════════════════════════════════════════
    # EXPERIENCE CALCULATION
    # ═══════════════════════════════════════════════════════
    
    def calculate_experience(self, roles: List[Dict]) -> Dict[str, Any]:
        """Calculate experience metrics from extracted roles"""
        total_months = 0
        internship_months = 0
        production_months = 0
        
        for role in roles:
            title = role.get("title", "").lower()
            is_intern = "intern" in title
            months = self._parse_role_duration(role)
            if months == 0:
                months = 4 if is_intern else 12
            
            total_months += months
            if is_intern:
                internship_months += months
            else:
                production_months += months
        
        return {
            "total_years": round(total_months / 12, 1),
            "production_years": round(production_months / 12, 1),
            "internship_months": internship_months,
            "role_count": len(roles),
            "has_internships": internship_months > 0,
            "has_production": production_months > 0
        }
    
    def _parse_role_duration(self, role: Dict) -> int:
        """Parse role duration in months"""
        try:
            from dateutil import parser as date_parser
            start = role.get("start_date", "")
            end = role.get("end_date", "") or "Present"
            if not start:
                return 0
            start_date = date_parser.parse(start, fuzzy=True)
            end_date = datetime.now() if end.lower() == "present" else date_parser.parse(end, fuzzy=True)
            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            return max(0, months)
        except Exception:
            return 0
    
    # ═══════════════════════════════════════════════════════
    # PENALTIES
    # ═══════════════════════════════════════════════════════
    
    def calculate_formatting_penalty(self, formatting_analysis: Dict[str, Any]) -> float:
        risk = formatting_analysis.get("risk_level", "Low")
        if risk == "High":
            return -10.0
        elif risk == "Medium":
            return -5.0
        return 0.0
    
    def detect_keyword_stuffing(self, resume_skills: List[str], resume_text: str) -> float:
        if len(resume_skills) > 50:
            return -10.0
        text_lower = resume_text.lower()
        for skill in resume_skills[:15]:
            count = text_lower.count(skill.lower())
            if count > 8:
                return -7.0
            if count > 5:
                return -3.0
        return 0.0
    
    # ═══════════════════════════════════════════════════════
    # MAIN SCORING FUNCTION
    # ═══════════════════════════════════════════════════════
    
    def calculate_score(
        self,
        extracted_resume: Dict[str, Any],
        extracted_jd: Dict[str, Any],
        resume_text: str,
        formatting_analysis: Dict[str, Any],
        semantic_score: float
    ) -> Dict[str, Any]:
        """Calculate deterministic ATS score."""
        
        # 1. Detect seniority
        level = self.detect_seniority(extracted_jd)
        years_required = extracted_jd.get("years_required", 0) or 0
        
        # 2. Match skills
        jd_must_have = extracted_jd.get("must_have_skills", [])
        jd_nice_have = extracted_jd.get("nice_to_have_skills", [])
        resume_skills = extracted_resume.get("skills", [])
        
        extra_skills = self._extract_inline_skills(extracted_resume, resume_text)
        all_resume_skills = list(set(
            [s.lower().strip() for s in resume_skills] + 
            [s.lower().strip() for s in extra_skills]
        ))
        
        must_have_result = self.match_skills(jd_must_have, all_resume_skills, resume_text)
        nice_have_result = self.match_skills(jd_nice_have, all_resume_skills, resume_text)
        
        must_have_ratio = must_have_result["match_ratio"]
        nice_have_ratio = nice_have_result["match_ratio"]
        
        # 3. Calculate experience
        roles = extracted_resume.get("roles", [])
        exp = self.calculate_experience(roles)
        
        experience_ratio = 1.0
        if years_required > 0:
            experience_ratio = min(1.0, exp["total_years"] / years_required)
        
        # 4. Title match
        title_score = self._calculate_title_match(extracted_resume, extracted_jd)
        
        # 5. Recency
        recency_score = 1.0 if self._has_recent_experience(roles) else 0.3
        
        # 6. Projects & education (entry level)
        projects = extracted_resume.get("projects", [])
        project_score = min(1.0, len(projects) * 0.25)
        internship_score = min(1.0, exp["internship_months"] / 6)
        
        # 7. Production experience (senior)
        production_score = min(1.0, exp["production_years"] / max(1, years_required))
        
        # 8. Penalties
        formatting_penalty = self.calculate_formatting_penalty(formatting_analysis)
        stuffing_penalty = self.detect_keyword_stuffing(resume_skills, resume_text)
        
        # 9. Normalize semantic score
        semantic_normalized = min(1.0, max(0.0, semantic_score / 100.0))
        
        # ═══════════════════════════════════════════════════
        # WEIGHTED SCORE FORMULA (seniority-aware)
        # ═══════════════════════════════════════════════════
        
        if level == "entry":
            weights = {
                "must_have": (must_have_ratio, 35),
                "nice_to_have": (nice_have_ratio, 10),
                "projects": (project_score, 20),
                "internships": (internship_score, 15),
                "semantic": (semantic_normalized, 10),
                "potential": (min(1.0, len(resume_skills) / 10), 10),
            }
        elif level == "senior":
            weights = {
                "must_have": (must_have_ratio, 50),
                "production": (production_score, 25),
                "experience": (experience_ratio, 15),
                "title_match": (title_score, 5),
                "semantic": (semantic_normalized, 5),
            }
        else:  # mid
            weights = {
                "must_have": (must_have_ratio, 45),
                "nice_to_have": (nice_have_ratio, 15),
                "experience": (experience_ratio, 15),
                "title_match": (title_score, 5),
                "semantic": (semantic_normalized, 10),
                "recency": (recency_score, 5),
                "potential": (min(1.0, len(resume_skills) / 15), 5),
            }
        
        raw_score = sum(ratio * max_pts for ratio, max_pts in weights.values())
        raw_score += formatting_penalty + stuffing_penalty
        raw_score = max(0, min(100, raw_score))
        
        # Deterministic caps (senior roles)
        cap_applied = None
        if level == "senior":
            if must_have_ratio < 0.30:
                raw_score = min(raw_score, 20)
                cap_applied = "Must-have skills < 30%"
            elif must_have_ratio < 0.50:
                raw_score = min(raw_score, 35)
                cap_applied = "Must-have skills < 50%"
            if experience_ratio < 0.50:
                raw_score = min(raw_score, 30)
                cap_applied = "Experience < 50% of required"
            if not exp["has_production"]:
                raw_score = min(raw_score, 25)
                cap_applied = "No production experience"
        
        final_score = round(raw_score, 1)
        
        # Build breakdown
        breakdown = {}
        for key, (ratio, max_pts) in weights.items():
            breakdown[f"{key}_score"] = round(ratio * max_pts, 1)
        breakdown["formatting_penalty"] = formatting_penalty
        breakdown["keyword_stuffing_penalty"] = stuffing_penalty
        
        all_keyword_gaps = must_have_result["keyword_gaps"] + nice_have_result["keyword_gaps"]
        
        logger.info(
            f"Deterministic ATS: score={final_score}, level={level}, "
            f"must_have={must_have_ratio:.0%}, semantic={semantic_normalized:.0%}"
        )
        
        return {
            "final_ats_score": final_score,
            "final_breakdown": self._to_schema_breakdown(breakdown, level),
            "matched_skills": must_have_result["matched_skills"],
            "corrected_missing_skills": must_have_result["missing_skills"],
            "keyword_gaps": all_keyword_gaps,
            "nice_to_have_matched": nice_have_result["matched_skills"],
            "nice_to_have_missing": nice_have_result["missing_skills"],
            "level": level,
            "cap_applied": cap_applied,
            "experience": exp,
            "must_have_ratio": must_have_ratio,
            "nice_have_ratio": nice_have_ratio,
            "semantic_score": semantic_score,
            "recruiter_reasoning": "",
            "confidence": round(0.9 + (must_have_ratio * 0.1), 2),
        }
    
    def _to_schema_breakdown(self, breakdown: Dict, level: str) -> Dict[str, float]:
        return {
            "skills_score": breakdown.get("must_have_score", 0),
            "semantic_score": breakdown.get("semantic_score", 0),
            "experience_score": breakdown.get("experience_score", breakdown.get("projects_score", 0)),
            "must_have_skills_score": breakdown.get("must_have_score", 0),
            "nice_to_have_score": breakdown.get("nice_to_have_score", 0),
            "title_match_score": breakdown.get("title_match_score", 0),
            "experience_match_score": breakdown.get("experience_score", 0),
            "formatting_penalty": breakdown.get("formatting_penalty", 0),
            "keyword_stuffing_penalty": breakdown.get("keyword_stuffing_penalty", 0),
            "recency_bonus": breakdown.get("recency_score", 0),
            "projects_education_score": breakdown.get("projects_score", 0),
            "internship_score": breakdown.get("internships_score", 0),
            "potential_score": breakdown.get("potential_score", 0),
            "production_experience_score": breakdown.get("production_score", 0),
        }
    
    def _extract_inline_skills(self, extracted_resume: Dict, resume_text: str) -> List[str]:
        skills = []
        for role in extracted_resume.get("roles", []):
            for bullet in role.get("bullets", []):
                skills.extend(self._find_tech_in_text(bullet))
        for project in extracted_resume.get("projects", []):
            techs = project.get("technologies", [])
            skills.extend([t.lower().strip() for t in techs])
            desc = project.get("description", "")
            if desc:
                skills.extend(self._find_tech_in_text(desc))
        return list(set(skills))
    
    def _find_tech_in_text(self, text: str) -> List[str]:
        text_lower = text.lower()
        found = []
        for canonical, aliases in SKILL_ALIASES.items():
            for term in [canonical] + aliases:
                if len(term) >= 2 and term in text_lower:
                    found.append(canonical)
                    break
        return found
    
    def _calculate_title_match(
        self, extracted_resume: Dict, extracted_jd: Dict
    ) -> float:
        jd_title = extracted_jd.get("role_title", "").lower()
        if not jd_title:
            return 0.5
        jd_words = set(jd_title.split())
        best = 0.0
        for role in extracted_resume.get("roles", []):
            title = role.get("title", "").lower()
            title_words = set(title.split())
            if jd_title in title or title in jd_title:
                return 1.0
            overlap = len(jd_words & title_words)
            if len(jd_words) > 0:
                score = overlap / len(jd_words)
                best = max(best, score)
        if self.model and best < 0.5:
            for role in extracted_resume.get("roles", []):
                title = role.get("title", "")
                if title:
                    sim = self._cosine_sim(
                        self._get_embedding(jd_title),
                        self._get_embedding(title.lower())
                    )
                    best = max(best, sim)
        return min(1.0, best)
    
    def _has_recent_experience(self, roles: List[Dict]) -> bool:
        try:
            from dateutil import parser as date_parser
            cutoff = datetime.now().replace(year=datetime.now().year - 2)
            for role in roles:
                end = role.get("end_date", "") or "Present"
                if end.lower() == "present":
                    return True
                try:
                    end_date = date_parser.parse(end, fuzzy=True)
                    if end_date >= cutoff:
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        return len(roles) > 0


# ═══════════════════════════════════════════════════════════
# SINGLETON
# ═══════════════════════════════════════════════════════════

_engine_instance: Optional[DeterministicATSEngine] = None


def get_ats_engine(embedding_model=None) -> DeterministicATSEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DeterministicATSEngine(embedding_model)
    elif embedding_model is not None and _engine_instance.model is None:
        _engine_instance.model = embedding_model
    return _engine_instance
