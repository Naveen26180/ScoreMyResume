from groq import Groq
import json
import logging
import time
from typing import Dict, Any, List, Optional
import asyncio
from functools import partial

logger = logging.getLogger(__name__)


class GroqAPIError(Exception):
    """Structured error for Groq API failures."""
    def __init__(self, message: str, error_type: str, retryable: bool = False, wait_seconds: int = 0):
        super().__init__(message)
        self.error_type = error_type      # 'rate_limit' | 'auth' | 'server' | 'network' | 'parse'
        self.retryable = retryable
        self.wait_seconds = wait_seconds


def _classify_error(exc: Exception) -> GroqAPIError:
    """Turn any Groq/HTTP exception into a structured GroqAPIError."""
    msg = str(exc).lower()
    if "rate limit" in msg or "429" in msg or "too many" in msg:
        return GroqAPIError(
            "You've hit the Groq rate limit. Please wait ~60 seconds and try again.",
            error_type="rate_limit", retryable=True, wait_seconds=60
        )
    if "401" in msg or "403" in msg or "invalid api key" in msg or "authentication" in msg:
        return GroqAPIError(
            "Your Groq API key is invalid or unauthorised. Please double-check your key.",
            error_type="auth", retryable=False
        )
    if "500" in msg or "503" in msg or "502" in msg:
        return GroqAPIError(
            "Groq servers are temporarily unavailable. Please try again in a moment.",
            error_type="server", retryable=True, wait_seconds=10
        )
    if "timeout" in msg or "connection" in msg or "network" in msg:
        return GroqAPIError(
            "Network error connecting to Groq. Check your internet connection and retry.",
            error_type="network", retryable=True, wait_seconds=5
        )
    return GroqAPIError(f"Groq API error: {exc}", error_type="unknown", retryable=True, wait_seconds=5)


def _safe_parse_json(text: str) -> dict:
    """Robustly extract a JSON object from LLM output.

    Handles:
    - Markdown code fences (```json ... ```)
    - Trailing 'json' prefix
    - Truncated JSON (finds outermost balanced { })
    """
    import re
    # Strip markdown fences
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Drop first and last line if they are fence markers
        inner = []
        for i, line in enumerate(lines):
            if i == 0 and line.startswith("```"):
                continue
            if i == len(lines) - 1 and line.strip() in ("```", ""):
                continue
            inner.append(line)
        text = "\n".join(inner).strip()
    if text.startswith("json"):
        text = text[4:].strip()

    # Try direct parse first (happy path)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the outermost {...} block
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in LLM response")

    depth = 0
    end = -1
    in_string = False
    escape_next = False
    for i, ch in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue
        if ch == "\\" and in_string:
            escape_next = True
            continue
        if ch == '"' and not escape_next:
            in_string = not in_string
        if not in_string:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break

    if end != -1:
        # Found a complete balanced block
        try:
            return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

    # JSON is truncated — try appending closing braces
    candidate = text[start:] if end == -1 else text[start:end]
    for suffix in ("}]}}}", "}]}", "}}", "}"):
        try:
            return json.loads(candidate + suffix)
        except json.JSONDecodeError:
            continue

    raise json.JSONDecodeError(f"Cannot parse JSON from LLM response (length={len(text)})", text, 0)


class GroqService:
    """Service for interacting with Groq API — extracts, reasons, and coaches."""

    # Simple per-instance call counter for rate-limit UI display
    _MAX_RETRIES = 2
    _RETRY_DELAY = 5  # seconds between retries

    def __init__(self, api_key: str):
        import os
        os.environ['GROQ_API_KEY'] = api_key
        self.client = Groq()
        self.model = "llama-3.1-8b-instant"
        self.call_count = 0          # total calls made this session
        self.error_count = 0         # errors encountered this session
        self.last_error: Optional[str] = None

    def _call_with_retry(self, fn, *args, **kwargs):
        """Execute fn, retrying up to _MAX_RETRIES times on retryable errors."""
        last_exc = None
        for attempt in range(self._MAX_RETRIES + 1):
            try:
                result = fn(*args, **kwargs)
                self.call_count += 1
                return result
            except Exception as exc:
                api_err = _classify_error(exc)
                self.error_count += 1
                self.last_error = api_err.error_type
                last_exc = api_err
                if api_err.retryable and attempt < self._MAX_RETRIES:
                    wait = api_err.wait_seconds or self._RETRY_DELAY
                    logger.warning(f"Attempt {attempt+1} failed ({api_err.error_type}). Retrying in {wait}s…")
                    time.sleep(wait)
                else:
                    raise api_err from exc
        raise last_exc  # type: ignore

    # ═══════════════════════════════════════════════════════════
    # EXTRACTION
    # ═══════════════════════════════════════════════════════════
    
    async def extract_resume(self, resume_text: str) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_resume_sync, resume_text)
    
    def _extract_resume_sync(self, resume_text: str) -> Dict[str, Any]:
        prompt = f"""Extract structured information from this resume. Return ONLY valid JSON with no markdown formatting.

Resume:
{resume_text}

Extract into this exact JSON structure:
{{
  "name": "Full Name",
  "email": "email@example.com",
  "phone": "phone number",
  "linkedin": "LinkedIn URL",
  "github": "GitHub URL",
  "education": [
    {{
      "institution": "University Name",
      "degree": "Degree Type",
      "field": "Field of Study",
      "graduation_year": "Year"
    }}
  ],
  "roles": [
    {{
      "company": "Company Name",
      "title": "Job Title",
      "start_date": "MM/YYYY",
      "end_date": "MM/YYYY or Present",
      "bullets": ["achievement 1", "achievement 2"]
    }}
  ],
  "projects": [
    {{
      "name": "Project Name",
      "description": "Brief description",
      "technologies": ["tech1", "tech2"]
    }}
  ],
  "skills": ["skill1", "skill2", "skill3"]
}}

Return ONLY the JSON object, no other text."""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4096
            )
            response_text = completion.choices[0].message.content.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
            result = json.loads(response_text)
            logger.info("Successfully extracted resume data")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse resume extraction JSON: {e}")
            raise ValueError(f"Failed to parse resume extraction: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting resume: {e}")
            raise
    
    async def extract_job_description(self, jd_text: str) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._extract_job_description_sync, jd_text)
    
    def _extract_job_description_sync(self, jd_text: str) -> Dict[str, Any]:
        prompt = f"""Extract structured information from this job description. Return ONLY valid JSON with no markdown formatting.

Job Description:
{jd_text}

Extract into this exact JSON structure:
{{
  "role_title": "Job Title",
  "seniority": "Junior/Mid/Senior/Lead/Entry-Level/Intern/Fresher",
  "must_have_skills": ["required skill 1", "required skill 2"],
  "nice_to_have_skills": ["preferred skill 1", "preferred skill 2"],
  "responsibilities": ["responsibility 1", "responsibility 2"],
  "soft_skills": ["communication", "leadership"],
  "education": "Education requirement",
  "years_required": 0,
  "location_type": "Remote/Hybrid/Onsite"
}}

IMPORTANT:
- For seniority, detect from job title and description.
- For years_required, extract the actual number. If not specified, use 0.

Return ONLY the JSON object, no other text."""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4096
            )
            response_text = completion.choices[0].message.content.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
            result = json.loads(response_text)
            logger.info("Successfully extracted job description data")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JD extraction JSON: {e}")
            raise ValueError(f"Failed to parse JD extraction: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting job description: {e}")
            raise
    
    # ═══════════════════════════════════════════════════════════
    # AI RECRUITER REASONING (explains the deterministic score)
    # ═══════════════════════════════════════════════════════════
    
    async def generate_recruiter_reasoning(
        self,
        extracted_resume: Dict[str, Any],
        extracted_jd: Dict[str, Any],
        score_result: Dict[str, Any]
    ) -> str:
        loop = asyncio.get_event_loop()
        func = partial(
            self._generate_recruiter_reasoning_sync,
            extracted_resume, extracted_jd, score_result
        )
        return await loop.run_in_executor(None, func)
    
    def _generate_recruiter_reasoning_sync(
        self,
        extracted_resume: Dict[str, Any],
        extracted_jd: Dict[str, Any],
        score_result: Dict[str, Any]
    ) -> str:
        score = score_result.get("final_ats_score", 0)
        matched = score_result.get("matched_skills", [])
        missing = score_result.get("corrected_missing_skills", [])
        keyword_gaps = score_result.get("keyword_gaps", [])
        level = score_result.get("level", "mid")
        cap = score_result.get("cap_applied")
        exp = score_result.get("experience", {})
        role_title = extracted_jd.get("role_title", "this role")
        
        gap_summary = ""
        if keyword_gaps:
            gap_items = [f"'{g['skill']}' (found as '{g['matched_via']}')" for g in keyword_gaps[:5]]
            gap_summary = f"\nKEYWORD GAPS (matched semantically but exact phrase missing): {', '.join(gap_items)}"
        
        cap_note = f"\nSCORE CAP APPLIED: {cap}" if cap else ""
        
        prompt = f"""You are an experienced tech recruiter. A candidate's resume has been scored against a job description.

ROLE: {role_title}
SENIORITY: {level.upper()}-LEVEL
SCORE: {score}/100

MATCHED SKILLS ({len(matched)}): {', '.join(matched[:15])}
MISSING SKILLS ({len(missing)}): {', '.join(missing[:10])}
{gap_summary}
EXPERIENCE: {exp.get('total_years', 0)} years total, {exp.get('production_years', 0)} years production
{cap_note}

Write 2-3 sentences explaining WHY the candidate received {score}/100 for the {role_title} role.
- Be specific about strengths and gaps
- If there are keyword gaps, mention the resume has the skills but should use exact JD terminology
- If a cap was applied, explain why
- Do NOT suggest a different score — the score is final

Return ONLY the reasoning text, no JSON, no markdown."""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating reasoning: {e}")
            return (
                f"The candidate scored {score}/100 for the {role_title} role. "
                f"They matched {len(matched)} skills and are missing {len(missing)} required skills. "
                f"{'Score was capped because: ' + cap + '.' if cap else ''}"
            )
    
    # ═══════════════════════════════════════════════════════════
    # IMPROVEMENT REPORT (multi-mode coaching)
    # ═══════════════════════════════════════════════════════════
    
    async def generate_improvement_report(
        self,
        resume_text: str,
        extracted_resume: Dict[str, Any],
        extracted_jd: Dict[str, Any],
        ats_result: Dict[str, Any],
        semantic_score: float
    ) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        func = partial(
            self._generate_improvement_report_sync,
            resume_text, extracted_resume, extracted_jd, ats_result, semantic_score
        )
        return await loop.run_in_executor(None, func)
    
    def _calculate_experience_years(self, extracted_resume: Dict[str, Any]) -> float:
        roles = extracted_resume.get('roles', [])
        if not roles:
            return 0
        total_months = 0
        for role in roles:
            if 'intern' in role.get('title', '').lower():
                total_months += 4
            else:
                total_months += 12
        return round(total_months / 12, 1)
    
    def _analyze_match_type(
        self,
        score: float,
        matched_skills: list,
        missing_skills: list,
        extracted_resume: Dict[str, Any],
        extracted_jd: Dict[str, Any]
    ) -> Dict[str, Any]:
        jd_required_count = len(extracted_jd.get('must_have_skills', []))
        match_ratio = min(1.0, len(matched_skills) / jd_required_count) if jd_required_count > 0 else 0
        years_required = extracted_jd.get('years_required', 0) or 0
        resume_years = self._calculate_experience_years(extracted_resume)
        num_roles = len(extracted_resume.get('roles', []))
        has_internships_only = all(
            'intern' in r.get('title', '').lower()
            for r in extracted_resume.get('roles', [])
        ) if num_roles > 0 else True
        
        candidate_level = "entry-level/student"
        if num_roles >= 3 and not has_internships_only:
            candidate_level = "mid-level"
        if num_roles >= 5:
            candidate_level = "senior"
        
        resume_domain = ', '.join(extracted_resume.get('skills', [])[:5])
        jd_title = extracted_jd.get('role_title', 'Unknown')
        
        if score < 40 and match_ratio < 0.2:
            return {"mode": "domain_mismatch", "severity": "incompatible", "can_fix": False,
                    "timeline": None, "candidate_level": candidate_level, "resume_domain": resume_domain,
                    "jd_title": jd_title, "match_ratio": round(match_ratio, 2),
                    "resume_years": resume_years, "years_required": years_required}
        if years_required >= 5 and resume_years < 2:
            return {"mode": "level_mismatch", "severity": "experience_gap", "can_fix": False,
                    "timeline": f"{max(1, years_required - resume_years):.0f} years",
                    "candidate_level": candidate_level, "resume_domain": resume_domain,
                    "jd_title": jd_title, "match_ratio": round(match_ratio, 2),
                    "resume_years": resume_years, "years_required": years_required}
        if 40 <= score < 70 and match_ratio < 0.5:
            return {"mode": "skill_gap", "severity": "learnable", "can_fix": True,
                    "timeline": "3-6 months", "candidate_level": candidate_level,
                    "resume_domain": resume_domain, "jd_title": jd_title,
                    "match_ratio": round(match_ratio, 2), "missing_count": len(missing_skills),
                    "resume_years": resume_years, "years_required": years_required}
        if score >= 85:
            return {"mode": "nearly_perfect", "severity": "minimal", "can_fix": True,
                    "timeline": "1 hour", "candidate_level": candidate_level,
                    "resume_domain": resume_domain, "jd_title": jd_title,
                    "match_ratio": round(match_ratio, 2), "resume_years": resume_years,
                    "years_required": years_required}
        return {"mode": "optimization", "severity": "minor_gaps", "can_fix": True,
                "timeline": "1-2 weeks", "candidate_level": candidate_level,
                "resume_domain": resume_domain, "jd_title": jd_title,
                "match_ratio": round(match_ratio, 2), "resume_years": resume_years,
                "years_required": years_required}
    
    def _generate_improvement_report_sync(
        self,
        resume_text: str,
        extracted_resume: Dict[str, Any],
        extracted_jd: Dict[str, Any],
        ats_result: Dict[str, Any],
        semantic_score: float
    ) -> Dict[str, Any]:
        current_score = ats_result.get('final_ats_score', 0)
        matched_skills = ats_result.get('matched_skills', [])
        missing_skills = ats_result.get('corrected_missing_skills', [])
        
        mode_info = self._analyze_match_type(
            current_score, matched_skills, missing_skills, extracted_resume, extracted_jd
        )
        mode = mode_info["mode"]
        candidate_level = mode_info["candidate_level"]
        jd_title = mode_info["jd_title"]
        resume_domain = mode_info["resume_domain"]
        
        common_context = f"""
RESUME SKILLS: {', '.join(extracted_resume.get('skills', []))}
JD ROLE: {jd_title}
JD REQUIRED SKILLS: {', '.join(extracted_jd.get('must_have_skills', []))}
MATCHED SKILLS: {matched_skills}
MISSING SKILLS: {missing_skills}
ATS SCORE: {current_score}/100
CANDIDATE LEVEL: {candidate_level}
"""
        
        if mode == "domain_mismatch":
            prompt = f"""You are a career counselor. The candidate has applied for a role in a completely different field.

{common_context}

RESUME TEXT:
{resume_text[:2000]}

CANDIDATE'S BACKGROUND: {resume_domain}
TARGET ROLE: {jd_title}
MATCH: {current_score}/100 (Very Low - Different Field)

Return ONLY this JSON:
{{
  "score_analysis": {{
    "current_score": {current_score},
    "potential_score": {current_score},
    "why_low": "This role requires field-specific expertise that doesn't match your background.",
    "main_issues": ["Different domain", "Missing field-specific skills", "Different career path"]
  }},
  "domain_explanation": "2-3 sentence explanation of why the domains don't match",
  "alternative_roles": [
    {{"title": "Role matching their skills", "match_estimate": "80-90%", "why": "Why this fits"}},
    {{"title": "Another matching role", "match_estimate": "70-80%", "why": "Reason"}},
    {{"title": "Stretch role", "match_estimate": "60-75%", "why": "Reason"}}
  ],
  "confidence_boosts": [
    "Specific skill that IS valuable",
    "Career direction recommendation"
  ],
  "expert_tips": [
    "Focus your job search on roles where your skills are valued",
    "Your experience positions you well for alternative fields"
  ]
}}

Return ONLY valid JSON."""
        
        elif mode == "level_mismatch":
            years_gap = mode_info.get("timeline", "3+ years")
            prompt = f"""You are a career coach. The candidate is in the right field but this role requires significantly more experience.

{common_context}

EXPERIENCE GAP: Role needs {mode_info.get('years_required', 5)}+ years, candidate has ~{mode_info.get('resume_years', 0)} years

Return ONLY this JSON:
{{
  "score_analysis": {{
    "current_score": {current_score},
    "potential_score": {min(current_score + 10, 60)},
    "why_low": "This role requires {mode_info.get('years_required', 5)}+ years. Resume tweaks can't bridge the experience gap.",
    "main_issues": ["Experience gap: need {years_gap} more", "Missing senior-level responsibilities", "Role expects proven track record"]
  }},
  "domain_explanation": "You're in the right field but this role needs {mode_info.get('years_required', 5)}+ years.",
  "alternative_roles": [
    {{"title": "Entry/mid-level version of this role", "match_estimate": "70-85%", "why": "Right field, achievable level"}},
    {{"title": "Growth role that leads here", "match_estimate": "60-75%", "why": "Stepping stone to target role"}}
  ],
  "learning_roadmap": [
    {{
      "week": "Now - Month 3",
      "title": "Build depth in current role",
      "tasks": ["Take on more responsibilities", "Lead a small project", "Document measurable achievements"],
      "resume_addition": "Add leadership experience and metrics"
    }},
    {{
      "week": "Month 3 - Month 6",
      "title": "Develop missing skills",
      "tasks": ["Learn a specific missing skill", "Build portfolio project"],
      "resume_addition": "Add new project demonstrating growth"
    }}
  ],
  "quick_wins": [
    {{"action": "Apply to lower-level version of this role now", "time": "Today", "impact": "Get hired faster"}},
    {{"action": "Add metrics to existing bullets", "time": "30 min", "impact": "Stronger impact statements"}}
  ],
  "confidence_boosts": [
    "You're in the right field — that's the hardest part",
    "Growth trajectory matters more than current title"
  ],
  "expert_tips": [
    "Apply to roles 1 level below this — you'll grow into it",
    "Focus on demonstrating impact, not years served"
  ]
}}

Return ONLY valid JSON."""
        
        elif mode == "skill_gap":
            prompt = f"""You are a career strategist. The candidate is in a related field but missing key skills.

{common_context}

RESUME TEXT:
{resume_text[:2000]}

EXTRACTED RESUME:
{json.dumps(extracted_resume, indent=2)}

JD DATA:
{json.dumps(extracted_jd, indent=2)}

SKILL MATCH: {len(matched_skills)}/{len(matched_skills) + len(missing_skills)} required skills
MISSING: {missing_skills}

Return ONLY this JSON:
{{
  "score_analysis": {{
    "current_score": {current_score},
    "potential_score": {min(current_score + 15, 75)},
    "why_low": "You have {len(matched_skills)} of {len(matched_skills) + len(missing_skills)} required skills. The gap is learnable.",
    "main_issues": ["Missing {len(missing_skills)} key skills", "Gap requires learning, not just keyword additions"]
  }},
  "domain_explanation": "You're in a related field! But this role needs skills you haven't demonstrated yet.",
  "alternative_roles": [
    {{"title": "Role matching current skills", "match_estimate": "75-85%", "why": "Uses your existing strengths"}},
    {{"title": "Stepping stone role", "match_estimate": "65-80%", "why": "Builds toward target role"}}
  ],
  "learning_roadmap": [
    {{
      "week": "Week 1-4",
      "title": "Learn highest-impact missing skill",
      "tasks": ["Find a specific free course for the missing skill", "Build a small project using it", "Add to portfolio"],
      "resume_addition": "Add: 'Built [project] using [missing skill]'"
    }},
    {{
      "week": "Week 5-8",
      "title": "Learn second missing skill",
      "tasks": ["Find another specific resource", "Extend existing project"],
      "resume_addition": "Add skill integration to existing project"
    }},
    {{
      "week": "Week 9-12",
      "title": "Polish and apply",
      "tasks": ["Combine skills in portfolio project", "Update resume", "Start applying"],
      "resume_addition": "Full project showcasing learned skills"
    }}
  ],
  "recommendations": [
    {{
      "id": "rec_1",
      "priority": "critical",
      "category": "enhance_existing",
      "title": "Quick keyword fix for existing content",
      "current_situation": "Why this change matters for ATS",
      "impact_points": 3,
      "difficulty": "easy",
      "time_estimate": "5 min",
      "confidence": "HIGH",
      "locations": [{{
        "section": "skills",
        "current_text": "[COPY exact text from resume above]",
        "suggested_text": "[Your improved version with JD keywords added naturally]",
        "keywords_added": ["specific keywords added"],
        "explanation": "Why: adds missing keyword"
      }}]
    }}
  ],
  "quick_wins": [
    {{"action": "Apply to a specific alternative role today", "time": "Now", "impact": "Higher chance of interview"}},
    {{"action": "Add commonly implied skill to skills section", "time": "2 min", "impact": "+2 ATS points"}}
  ],
  "confidence_boosts": [
    "Name a SPECIFIC skill from their resume that is valuable",
    "Name SPECIFIC experience that transfers"
  ],
  "expert_tips": [
    "Path 1 (recommended): Apply to roles where you're already a strong match",
    "Path 2: Learn the missing skill in 4 weeks to become competitive"
  ]
}}

CRITICAL RULES:
1. ALL current_text values MUST be copied VERBATIM from the resume text. Never use placeholder text.
2. ALL suggested_text MUST be real improved versions.
3. NEVER invent company names. NEVER reference companies not in the resume.
4. ALL confidence_boosts must reference SPECIFIC skills or experience from THIS candidate's resume.

Return ONLY valid JSON."""
        
        elif mode == "nearly_perfect":
            prompt = f"""You are a supportive career coach. The candidate is an EXCELLENT match for this role.

{common_context}

RESUME TEXT:
{resume_text}

EXTRACTED RESUME:
{json.dumps(extracted_resume, indent=2)}

JD DATA:
{json.dumps(extracted_jd, indent=2)}

SCORE: {current_score}/100 — EXCELLENT MATCH

Return ONLY this JSON:
{{
  "score_analysis": {{
    "current_score": {current_score},
    "potential_score": {min(int(current_score) + 5, 95)},
    "why_low": "Your score of {current_score}/100 is excellent! These are minor polish suggestions only.",
    "main_issues": ["Minor keyword optimization possible", "Small phrasing improvements"]
  }},
  "quick_wins": [
    {{"action": "Name a specific keyword from the JD to add to skills section", "time": "2 min", "impact": "+1-2 ATS points"}},
    {{"action": "Name a specific bullet to slightly rephrase", "time": "5 min", "impact": "+1 point"}}
  ],
  "confidence_boosts": [
    "Name a SPECIFIC matched skill that's a perfect match",
    "Name SPECIFIC experience that directly maps to this role",
    "You should apply NOW — you're ready"
  ],
  "recommendations": [
    {{
      "id": "rec_1",
      "priority": "low",
      "category": "enhance_existing",
      "title": "Minor tweak: enhance existing phrase",
      "current_situation": "Already good, can be slightly better",
      "impact_points": 2,
      "difficulty": "easy",
      "time_estimate": "2 min",
      "confidence": "HIGH",
      "locations": [{{
        "section": "experience",
        "current_text": "[COPY VERBATIM from RESUME TEXT above — must be real text]",
        "suggested_text": "[Slightly improved version with one JD keyword added]",
        "keywords_added": ["the keyword you added"],
        "explanation": "Why: adds exact JD phrasing"
      }}]
    }}
  ],
  "expert_tips": [
    "Apply now — your core skills match perfectly",
    "Focus on interview prep, not resume tweaks"
  ]
}}

RULES:
- Be POSITIVE. Score 85+ means they're ready.
- Only 2-3 minor recommendations max
- ALL current_text MUST be copied VERBATIM from RESUME TEXT above
- NEVER invent company names

Return ONLY valid JSON."""
        
        else:  # optimization mode
            resume_lower = resume_text.lower()
            keyword_counts = {}
            for skill in (matched_skills + missing_skills):
                skill_lower = skill.lower()
                count = resume_lower.count(skill_lower)
                keyword_counts[skill] = count
            
            keyword_freq_summary = "\n".join(
                f"  - \"{skill}\": appears {count} time(s)"
                for skill, count in keyword_counts.items()
            )
            
            if current_score >= 70:
                potential_increase = min(15, 95 - current_score)
                focus = "strategic keyword placement"
            elif current_score >= 50:
                potential_increase = min(25, 90 - current_score)
                focus = "significant keyword gaps"
            else:
                potential_increase = min(35, 85 - current_score)
                focus = "major improvements needed"
            
            potential_score = min(95, int(current_score + potential_increase))
            
            prompt = f"""You are an ATS optimization expert. Generate targeted improvement suggestions.

{common_context}

RESUME TEXT:
{resume_text}

EXTRACTED RESUME:
{json.dumps(extracted_resume, indent=2)}

JD DATA:
{json.dumps(extracted_jd, indent=2)}

POTENTIAL: {potential_score}/100 (+{potential_increase} points achievable)
FOCUS: {focus}

KEYWORD FREQUENCY:
{keyword_freq_summary}

Return ONLY this JSON:
{{
  "score_analysis": {{
    "current_score": {current_score},
    "potential_score": {potential_score},
    "why_low": "Assessment of current score and what's needed",
    "main_issues": ["Issue 1", "Issue 2", "Issue 3"]
  }},
  "recommendations": [
    {{
      "id": "rec_1",
      "priority": "critical",
      "category": "enhance_existing",
      "title": "Enhance: '[quote from resume]' with JD keywords",
      "current_situation": "Why this change matters for ATS scoring",
      "impact_points": 5,
      "difficulty": "easy",
      "time_estimate": "2 min",
      "confidence": "HIGH",
      "locations": [{{
        "section": "experience",
        "current_text": "[COPY VERBATIM from RESUME TEXT above — must be a real line from the resume]",
        "suggested_text": "[Your enhanced version of that exact line with JD keywords woven in]",
        "keywords_added": ["kw1", "kw2"],
        "explanation": "Why: adds JD phrase naturally"
      }}]
    }},
    {{
      "id": "rec_2",
      "priority": "medium",
      "category": "add_to_related",
      "title": "Add a missing skill or keyword",
      "current_situation": "Why this change matters",
      "impact_points": 3,
      "difficulty": "easy",
      "time_estimate": "3 min",
      "confidence": "MEDIUM",
      "locations": [{{
        "section": "skills",
        "current_text": "[COPY VERBATIM from RESUME TEXT above]",
        "suggested_text": "[Your enhanced version]",
        "keywords_added": ["tech"],
        "explanation": "Why: standard practice"
      }}]
    }}
  ],
  "section_summary": {{
    "skills": {{"status": "needs_improvement", "missing_exact_phrases": ["p1", "p2"], "quick_wins": "Add JD phrases"}},
    "experience": {{"status": "fair", "issues": ["issue"], "quick_wins": "Enhance bullets"}},
    "projects": {{"status": "good", "suggestions": "Add tech mentions"}}
  }},
  "expert_tips": [
    "Specific tip referencing keyword frequency data above",
    "Tip naming an exact JD phrase to mirror",
    "Metrics suggestion based on actual resume content",
    "Placement strategy for missing keywords"
  ],
  "keyword_density": {{
    "skill_name": {{"current": 1, "recommended": "3-5", "status": "too_low"}}
  }}
}}

CRITICAL RULES:
1. 4-8 recommendations
2. ALL current_text values MUST be copied VERBATIM from RESUME TEXT above
3. ALL suggested_text MUST be real improved versions
4. NEVER invent company names
5. Total impact_points ≈ {potential_increase}
6. potential_score MUST be {potential_score}
7. Do NOT suggest experience the candidate ({candidate_level}) doesn't have

Return ONLY valid JSON."""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=6000
            )
            response_text = completion.choices[0].message.content.strip()
            result = _safe_parse_json(response_text)
            result["mode"] = mode_info
            logger.info(f"Generated improvement report, mode={mode}")
            return result
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse improvement report JSON (after recovery attempt): {e}")
            return {
                "mode": mode_info,
                "score_analysis": {
                    "current_score": current_score,
                    "potential_score": current_score + 10,
                    "why_low": "Could not generate detailed analysis.",
                    "main_issues": ["Analysis generation failed"]
                },
                "recommendations": [],
                "expert_tips": ["Please try running the analysis again."]
            }
        except Exception as e:
            logger.error(f"Error generating improvement report: {e}")
            raise
    
    # ═══════════════════════════════════════════════════════════
    # AI TOOLS (Bullet Rewriting + Summary)
    # ═══════════════════════════════════════════════════════════
    
    async def rewrite_bullet(
        self,
        bullet: str,
        job_description: str,
        context: str = None
    ) -> Dict[str, Any]:
        loop = asyncio.get_event_loop()
        func = partial(self._rewrite_bullet_sync, bullet, job_description, context)
        return await loop.run_in_executor(None, func)
    
    def _rewrite_bullet_sync(
        self,
        bullet: str,
        job_description: str,
        context: str = None
    ) -> Dict[str, Any]:
        context_text = f"\n\nAdditional Context:\n{context}" if context else ""
        
        prompt = f"""Rewrite this resume bullet point to better match the job description.

Original Bullet:
{bullet}

Target Job Description:
{job_description}{context_text}

Requirements:
- Use strong action verbs
- Add quantifiable metrics where possible
- Incorporate relevant keywords from job description
- Keep it concise (1-2 lines)
- Maintain truthfulness

Return JSON:
{{
  "rewritten": "The improved bullet point",
  "improvements": ["improvement 1", "improvement 2", "improvement 3"]
}}

Return ONLY the JSON object, no other text."""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2048
            )
            response_text = completion.choices[0].message.content.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            if response_text.startswith("json"):
                response_text = response_text[4:].strip()
            result = json.loads(response_text)
            result["original"] = bullet
            return result
        except Exception as e:
            logger.error(f"Error rewriting bullet: {e}")
            raise
    
    def generate_summary_stream(
        self,
        resume_data: Dict[str, Any],
        job_description: str,
        tone: str = "professional"
    ):
        """Generate tailored summary with streaming (synchronous generator)"""
        
        prompt = f"""Create a compelling professional summary for this resume tailored to the job description.

Resume Data:
{json.dumps(resume_data, indent=2)}

Target Job Description:
{job_description}

Tone: {tone}

Requirements:
- 3-4 sentences
- Highlight most relevant experience
- Include key skills from job description
- Show value proposition

Generate the summary as plain text."""

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2048,
                stream=True
            )
            for chunk in completion:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise