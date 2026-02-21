import streamlit as st
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


class SemanticAnalyzer:
    """Semantic similarity analysis using sentence transformers"""
    
    def __init__(self):
        logger.info("Loading sentence transformer model...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        logger.info("Model loaded successfully")
    
    def calculate_semantic_score(
        self,
        extracted_resume: Dict[str, Any],
        extracted_jd: Dict[str, Any]
    ) -> float:
        """Calculate semantic similarity score between resume and job description"""
        
        # Collect resume content
        resume_texts = []
        
        # Add role bullets
        for role in extracted_resume.get("roles", []):
            resume_texts.extend(role.get("bullets", []))
        
        # Add project descriptions
        for project in extracted_resume.get("projects", []):
            desc = project.get("description", "")
            if desc:
                resume_texts.append(desc)
        
        # Add skills
        skills_text = ", ".join(extracted_resume.get("skills", []))
        if skills_text:
            resume_texts.append(f"Skills: {skills_text}")
        
        # Collect JD content
        jd_texts = []
        
        # Add responsibilities
        jd_texts.extend(extracted_jd.get("responsibilities", []))
        
        # Add required skills
        must_have = ", ".join(extracted_jd.get("must_have_skills", []))
        if must_have:
            jd_texts.append(f"Required skills: {must_have}")
        
        nice_to_have = ", ".join(extracted_jd.get("nice_to_have_skills", []))
        if nice_to_have:
            jd_texts.append(f"Preferred skills: {nice_to_have}")
        
        if not resume_texts or not jd_texts:
            logger.warning("Insufficient text for semantic analysis")
            return 50.0
        
        # Calculate embeddings
        resume_embeddings = self.model.encode(resume_texts)
        jd_embeddings = self.model.encode(jd_texts)
        
        # Calculate cosine similarity matrix
        similarities = []
        for jd_emb in jd_embeddings:
            for resume_emb in resume_embeddings:
                similarity = self._cosine_similarity(jd_emb, resume_emb)
                similarities.append(similarity)
        
        # Average similarity
        avg_similarity = np.mean(similarities)
        
        # Convert to 0-100 scale
        score = float((avg_similarity + 1) / 2 * 100)
        score = max(0, min(100, score))
        
        logger.info(f"Semantic score calculated: {score:.2f}")
        return round(score, 2)
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


@st.cache_resource(show_spinner="Loading semantic model… (first run only)")
def get_semantic_analyzer() -> SemanticAnalyzer:
    """Get or create semantic analyzer — cached by Streamlit across reruns."""
    return SemanticAnalyzer()
