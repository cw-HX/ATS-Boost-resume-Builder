"""
Groq LLM service for keyword extraction and text enhancement.
Uses LLaMA-3.1-70B with deterministic JSON outputs.
"""
import json
import logging
from typing import List, Dict, Any, Optional
from groq import Groq, AsyncGroq
import re

from app.core.config import settings

logger = logging.getLogger(__name__)


class GroqLLMService:
    """Service for interacting with Groq LLM API."""
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.async_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.temperature = settings.GROQ_TEMPERATURE
        self.max_tokens = settings.GROQ_MAX_TOKENS
    
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response text."""
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', text)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON array
        array_match = re.search(r'\[[\s\S]*\]', text)
        if array_match:
            try:
                return {"data": json.loads(array_match.group())}
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Could not extract JSON from response: {text[:200]}")
    
    async def extract_keywords_from_jd(self, job_description: str) -> Dict[str, List[str]]:
        """
        Extract ALL relevant keywords and skills from a job description for ATS matching.
        
        Args:
            job_description: The job description text
            
        Returns:
            Dictionary containing extracted keywords, skills, technologies, etc.
        """
        prompt = f"""Extract ALL keywords from this job description that an ATS system would scan for.

JOB DESCRIPTION:
{job_description}

EXTRACTION REQUIREMENTS:
1. Extract EVERY technical term, technology, framework, library, tool mentioned
2. Include both full names AND common abbreviations (e.g., "JavaScript" AND "JS")
3. Extract industry-specific terms and methodologies
4. Include action verbs commonly used (develop, design, implement, etc.)
5. Extract soft skills and interpersonal qualities
6. Include any certifications or qualifications mentioned
7. Extract team/project methodologies (Agile, Scrum, etc.)

Respond with ONLY a JSON object:
{{
    "keywords": ["keyword1", "keyword2", ...],
    "skills": ["skill1", "skill2", ...],
    "technologies": ["tech1", "tech2", ...],
    "soft_skills": ["soft_skill1", "soft_skill2", ...],
    "experience_requirements": ["requirement1", "requirement2", ...],
    "action_verbs": ["verb1", "verb2", ...],
    "methodologies": ["method1", "method2", ...]
}}

CATEGORIES:
- keywords: ALL important terms, role titles, domain-specific phrases
- skills: Technical skills, professional competencies (include variations)
- technologies: Programming languages, frameworks, databases, cloud platforms, tools (INCLUDE ABBREVIATIONS)
- soft_skills: Communication, leadership, problem-solving, collaboration, etc.
- experience_requirements: Years of experience, degree requirements, certifications
- action_verbs: Key action verbs that should appear in resume bullets
- methodologies: Agile, Scrum, DevOps, CI/CD, TDD, etc.

BE COMPREHENSIVE - extract 15-30 items per category. ATS matching depends on this."""

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert ATS keyword extraction system. Extract ALL possible keywords that an ATS would scan for. Be comprehensive - missing keywords means lower ATS scores."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,  # Deterministic extraction
                max_tokens=2000,  # Allow more tokens for comprehensive extraction
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Validate structure and add missing keys
            required_keys = ["keywords", "skills", "technologies", "soft_skills", "experience_requirements", "action_verbs", "methodologies"]
            for key in required_keys:
                if key not in result:
                    result[key] = []
            
            # Log extraction stats
            total = sum(len(result[k]) for k in required_keys)
            logger.info(f"Extracted {total} total keywords from JD: technologies={len(result['technologies'])}, skills={len(result['skills'])}, keywords={len(result['keywords'])}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error extracting keywords: {e}")
            raise
    
    async def align_skills(
        self,
        profile_skills: Dict[str, List[str]],
        jd_keywords: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Align profile skills with JD keywords.
        
        Args:
            profile_skills: User's skills from profile
            jd_keywords: Keywords extracted from JD
            
        Returns:
            Dictionary with aligned skills and recommendations
        """
        prompt = f"""Compare the candidate's skills with job requirements.

Candidate Skills:
Programming Languages: {', '.join(profile_skills.get('programming_languages', []))}
Technical Skills: {', '.join(profile_skills.get('technical_skills', []))}
Developer Tools: {', '.join(profile_skills.get('developer_tools', []))}

Job Requirements:
Skills: {', '.join(jd_keywords.get('skills', []))}
Technologies: {', '.join(jd_keywords.get('technologies', []))}

Respond with ONLY a JSON object in this exact format:
{{
    "matched_skills": ["skill1", "skill2", ...],
    "missing_skills": ["skill1", "skill2", ...],
    "transferable_skills": ["skill1", "skill2", ...],
    "skill_match_percentage": 75,
    "recommendations": ["recommendation1", "recommendation2", ...]
}}

- matched_skills: Skills that match between candidate and JD
- missing_skills: Skills in JD that candidate doesn't have
- transferable_skills: Candidate skills that are relevant but not exact matches
- skill_match_percentage: Percentage of JD skills matched (0-100)
- recommendations: Suggestions to improve match"""

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a skill alignment specialist. Always respond with valid JSON only."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error aligning skills: {e}")
            raise
    
    async def rewrite_bullets(
        self,
        bullets: List[str],
        target_keywords: List[str],
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Rewrite bullet points to include target keywords for maximum ATS compatibility.
        
        Args:
            bullets: Original bullet points
            target_keywords: Keywords to incorporate
            context: Additional context (e.g., project name, company)
            
        Returns:
            Dictionary with rewritten bullets and injected keywords
        """
        prompt = f"""Rewrite these bullet points to MAXIMIZE ATS keyword matching.

ORIGINAL BULLET POINTS:
{json.dumps(bullets, indent=2)}

TARGET KEYWORDS TO INJECT (include as many as possible):
{', '.join(target_keywords)}

CONTEXT: {context}

CRITICAL INSTRUCTIONS:
1. Each bullet MUST be 12-20 words (optimal ATS length)
2. Start each bullet with a STRONG ACTION VERB: Developed, Implemented, Engineered, Designed, Built, Created, Optimized, Architected, Integrated, Deployed
3. MUST include at least 2-3 keywords from the target list in each bullet
4. Use EXACT keyword phrases where possible (e.g., "REST API" not just "API")
5. Add technical context using keywords: "utilizing [keyword]", "leveraging [keyword]", "implementing [keyword]"
6. Include metrics/numbers where possible: "reduced by X%", "improved X by Y%", "handled X+ requests"
7. Make implicit skills explicit (if they built a web app, they used HTTP, handled requests, etc.)
8. DO NOT completely fabricate features, but DO emphasize technical aspects using JD terminology

EXAMPLE TRANSFORMATIONS:
Original: "Built a website using React"
Rewritten: "Developed responsive web application using React.js, implementing RESTful API integration and component-based architecture"

Original: "Worked on database"
Rewritten: "Engineered database schema utilizing MongoDB and implemented efficient query optimization for improved performance"

Respond with ONLY a JSON object:
{{
    "rewritten_bullets": ["bullet1", "bullet2", ...],
    "keywords_injected": ["keyword1", "keyword2", ...]
}}"""

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert ATS resume optimizer. Your bullets achieve 90%+ ATS scores by strategically incorporating job description keywords while maintaining truthfulness. Be aggressive with keyword placement."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Rewritten {len(bullets)} bullets, injected keywords: {result.get('keywords_injected', [])}")
            return result
            
        except Exception as e:
            logger.error(f"Error rewriting bullets: {e}")
            raise
    
    async def enhance_text(
        self,
        text: str,
        enhancement_type: str = "general"
    ) -> str:
        """
        Enhance text for resume quality.
        
        Args:
            text: Original text
            enhancement_type: Type of enhancement (general, technical, achievement)
            
        Returns:
            Enhanced text
        """
        prompts = {
            "general": "Improve this text for a professional resume. Make it concise and impactful.",
            "technical": "Enhance this technical description for a resume. Highlight technical expertise.",
            "achievement": "Rewrite this achievement to be more impactful. Include metrics if possible."
        }
        
        prompt = f"""{prompts.get(enhancement_type, prompts['general'])}

Original Text:
{text}

Rules:
1. Keep the same meaning
2. Make it more professional
3. Keep it concise
4. Don't fabricate information

Respond with ONLY a JSON object:
{{
    "enhanced_text": "your enhanced text here"
}}"""

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional resume writer. Enhance text while maintaining accuracy."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get("enhanced_text", text)
            
        except Exception as e:
            logger.error(f"Error enhancing text: {e}")
            return text

    async def generate_professional_summary(
        self,
        profile_data: Dict[str, Any],
        job_description: str,
        jd_keywords: Dict[str, List[str]]
    ) -> str:
        """
        Generate a tailored professional summary based on profile and job description.
        Maximizes keyword inclusion for ATS compatibility.
        
        Args:
            profile_data: User's profile information
            job_description: Target job description
            jd_keywords: Keywords extracted from job description
            
        Returns:
            Tailored professional summary (2-4 sentences)
        """
        # Extract key info from profile
        skills = profile_data.get("skills", {})
        all_skills = (
            skills.get("programming_languages", []) +
            skills.get("technical_skills", []) +
            skills.get("developer_tools", [])
        )
        
        projects = profile_data.get("projects", [])
        project_names = [p.get("project_name", "") for p in projects[:3]]
        project_techs = []
        for p in projects[:3]:
            project_techs.extend(p.get("tech_stack", []))
        
        internships = profile_data.get("internships", [])
        companies = [i.get("company_name", "") for i in internships[:2]]
        
        target_skills = jd_keywords.get("skills", []) + jd_keywords.get("technologies", [])
        all_jd_keywords = target_skills + jd_keywords.get("keywords", [])
        
        prompt = f"""Generate an ATS-OPTIMIZED professional summary that MAXIMIZES keyword matches.

CANDIDATE PROFILE:
- Programming Skills: {', '.join(all_skills[:20])}
- Project Technologies: {', '.join(project_techs[:10])}
- Notable Projects: {', '.join(project_names)}
- Work Experience: {', '.join(companies) if companies else 'Fresh graduate/student'}

JOB DESCRIPTION KEYWORDS TO INCLUDE (use as many as honestly possible):
{', '.join(all_jd_keywords[:20])}

Job Description Excerpt:
{job_description[:600]}

CRITICAL INSTRUCTIONS:
1. Write 3-4 impactful sentences (60-100 words total)
2. MUST include at least 8-10 keywords from the JD keyword list above
3. Use EXACT keyword phrases from the JD (e.g., if JD says "React.js", use "React.js" not just "React")
4. Start with a strong descriptor: "Results-driven", "Detail-oriented", "Passionate", etc.
5. Mention specific technologies that match the JD
6. Include soft skills mentioned in JD if applicable (team player, problem solver, etc.)
7. Quantify if possible (e.g., "developed 5+ projects", "proficient in 10+ technologies")
8. End with career goal aligned to the role

EXAMPLE FORMAT:
"Results-driven Software Developer with hands-on experience in [JD tech 1], [JD tech 2], and [JD tech 3]. 
Developed [X] projects utilizing [JD technologies]. Strong foundation in [JD skills] with demonstrated 
ability in [soft skill]. Seeking to leverage expertise in [role-related skill] to contribute to [company goal]."

Respond with ONLY a JSON object:
{{
    "summary": "Your professional summary here...",
    "keywords_included": ["keyword1", "keyword2", ...]
}}"""

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert ATS resume writer. Your summaries achieve 90%+ ATS scores by strategically including job description keywords while remaining truthful and professional."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            summary = result.get("summary", "")
            keywords = result.get("keywords_included", [])
            logger.info(f"Generated summary with {len(keywords)} JD keywords: {keywords}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating professional summary: {e}")
            return ""

    async def optimize_skills_for_jd(
        self,
        profile_skills: Dict[str, List[str]],
        jd_keywords: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Optimize and reorder skills to match job description priorities.
        Also adds relevant skills from JD that the candidate likely has based on their profile.
        
        Args:
            profile_skills: User's skills from profile
            jd_keywords: Keywords from job description
            
        Returns:
            Optimized skills with JD-relevant skills prioritized and related skills added
        """
        target_skills = jd_keywords.get("skills", []) + jd_keywords.get("technologies", [])
        
        prompt = f"""You are an ATS optimization expert. Optimize these skills sections to maximize ATS score for this job.

CANDIDATE'S CURRENT SKILLS:
- Programming Languages: {', '.join(profile_skills.get('programming_languages', []))}
- Technical Skills: {', '.join(profile_skills.get('technical_skills', []))}
- Developer Tools: {', '.join(profile_skills.get('developer_tools', []))}

JOB REQUIRED SKILLS/TECHNOLOGIES:
{', '.join(target_skills)}

OPTIMIZATION TASKS (DO ALL):
1. Put JD-matching skills FIRST in each category
2. Add commonly accepted variations/synonyms (e.g., "JavaScript" -> "JavaScript (ES6+)", "React" -> "React.js")
3. IMPORTANT: Add related skills from the JD that the candidate LIKELY knows based on their existing skills:
   - If they know React, they likely know JSX, Hooks, Component Design
   - If they know Python, they likely know pip, virtual environments
   - If they know MongoDB, they likely know NoSQL, Database Design
   - If they know Docker, they likely know containers, containerization
   - If they have web development skills, they likely know REST APIs, HTTP
   - If they know Git, they likely know version control, GitHub/GitLab
4. For missing JD skills that are closely related to what they know, add them:
   - Example: If JD wants "Agile" and they have any project experience, add "Agile Methodology"
   - Example: If JD wants "Team Collaboration" and they have internship experience, add it
5. Add soft skills from JD that any developer would have: "Problem Solving", "Analytical Skills", etc.

RULES:
- Each skill category should have 8-15 skills
- Front-load each category with JD-matching keywords
- Use EXACT terminology from the JD where the candidate has matching skills
- Output skills in the exact format they should appear on the resume

Respond with ONLY a JSON object:
{{
    "programming_languages": ["skill1", "skill2", ...],
    "technical_skills": ["skill1", "skill2", ...],
    "developer_tools": ["tool1", "tool2", ...],
    "keywords_prioritized": ["keyword1", "keyword2", ...],
    "skills_added": ["skill1", "skill2", ...]
}}"""

        try:
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an ATS optimization expert. Your goal is to maximize keyword matches while being truthful about the candidate's abilities. Add related skills they would reasonably have based on their existing skills."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,  # Slightly creative for skill inference
                max_tokens=self.max_tokens,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            logger.info(f"Skills optimized. Added: {result.get('skills_added', [])}")
            return {
                "programming_languages": result.get("programming_languages", profile_skills.get("programming_languages", [])),
                "technical_skills": result.get("technical_skills", profile_skills.get("technical_skills", [])),
                "developer_tools": result.get("developer_tools", profile_skills.get("developer_tools", [])),
                "keywords_prioritized": result.get("keywords_prioritized", []),
                "skills_added": result.get("skills_added", [])
            }
            
        except Exception as e:
            logger.error(f"Error optimizing skills: {e}")
            return profile_skills


# Singleton instance
groq_service = GroqLLMService()
