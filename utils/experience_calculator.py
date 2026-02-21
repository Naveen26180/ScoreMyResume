from typing import Dict, List, Any
from dateutil import parser
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExperienceCalculator:
    """Calculate years of experience per skill"""
    
    @staticmethod
    def calculate_timeline(
        extracted_resume: Dict[str, Any],
        extracted_jd: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate experience timeline for relevant skills"""
        
        skill_years = {}
        
        # Get all relevant skills from JD
        relevant_skills = set()
        relevant_skills.update([s.lower() for s in extracted_jd.get("must_have_skills", [])])
        relevant_skills.update([s.lower() for s in extracted_jd.get("nice_to_have_skills", [])])
        
        # Process each role
        for role in extracted_resume.get("roles", []):
            role_duration = ExperienceCalculator._calculate_role_duration(role)
            
            if role_duration == 0:
                continue
            
            # Check bullets for skill mentions
            bullets = role.get("bullets", [])
            role_text = " ".join(bullets).lower()
            
            for skill in relevant_skills:
                if skill in role_text or skill in role.get("title", "").lower():
                    skill_years[skill] = skill_years.get(skill, 0) + role_duration
        
        # Also check projects
        for project in extracted_resume.get("projects", []):
            project_text = (
                project.get("description", "") + " " + 
                " ".join(project.get("technologies", []))
            ).lower()
            
            # Assume 0.5 years per project (rough estimate)
            for skill in relevant_skills:
                if skill in project_text:
                    skill_years[skill] = skill_years.get(skill, 0) + 0.5
        
        # Calculate total experience
        all_roles = extracted_resume.get("roles", [])
        total_experience = sum(
            ExperienceCalculator._calculate_role_duration(role) 
            for role in all_roles
        )
        
        # Round all values
        skill_years = {k: round(v, 1) for k, v in skill_years.items()}
        
        return {
            "skill_years": skill_years,
            "total_experience_years": round(total_experience, 1)
        }
    
    @staticmethod
    def _calculate_role_duration(role: Dict[str, Any]) -> float:
        """Calculate duration of a role in years"""
        try:
            start = role.get("start_date", "")
            end = role.get("end_date", "Present")
            
            if not start:
                return 0
            
            start_date = parser.parse(start, fuzzy=True)
            end_date = datetime.now() if end.lower() == "present" else parser.parse(end, fuzzy=True)
            
            months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
            years = months / 12
            
            return max(0, years)
            
        except Exception as e:
            logger.warning(f"Could not parse role dates: {e}")
            return 0
