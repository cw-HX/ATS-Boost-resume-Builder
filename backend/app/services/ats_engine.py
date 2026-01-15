"""
ATS (Applicant Tracking System) Optimization Engine.
Implements hybrid rule-based and AI-based ATS optimization.
"""
import re
import logging
from typing import List, Dict, Any, Tuple, Optional, Set
from collections import Counter

from app.services.llm_service import groq_service
from app.models.schemas import ProfileResponse

logger = logging.getLogger(__name__)

# Common English stop words for keyword extraction
STOP_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had',
    'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
    'shall', 'can', 'need', 'dare', 'ought', 'used', 'it', 'its', 'this', 'that',
    'these', 'those', 'i', 'you', 'he', 'she', 'we', 'they', 'what', 'which', 'who',
    'whom', 'when', 'where', 'why', 'how', 'all', 'each', 'every', 'both', 'few',
    'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own',
    'same', 'so', 'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there',
    'then', 'once', 'if', 'else', 'because', 'while', 'although', 'though', 'after',
    'before', 'above', 'below', 'between', 'into', 'through', 'during', 'out',
    'about', 'against', 'among', 'any', 'etc', 'our', 'your', 'their', 'his', 'her',
    'up', 'down', 'over', 'under', 'again', 'further', 'am', 'being', 'able',
}


class ATSOptimizationEngine:
    """
    Hybrid ATS Optimization Engine combining rule-based and AI-based logic.
    """
    
    # ATS-recognized section headers
    STANDARD_SECTION_HEADERS = {
        "education", "skills", "projects", "experience", 
        "internships", "certifications", "achievements",
        "work experience", "professional experience", "technical skills"
    }
    
    # Optimal bullet point word count range
    BULLET_MIN_WORDS = 12
    BULLET_MAX_WORDS = 20
    
    def __init__(self):
        """Initialize the ATS engine (lightweight, no ML models)."""
        logger.info("ATS Engine initialized (rule-based mode)")
    
    def _extract_keywords_rule_based(self, text: str) -> List[str]:
        """Extract keywords using simple rule-based extraction (no ML)."""
        # Clean and tokenize
        text_lower = text.lower()
        # Remove special characters but keep hyphens and dots for tech terms
        text_clean = re.sub(r'[^a-z0-9\s\.\-\+\#]', ' ', text_lower)
        words = text_clean.split()
        
        keywords = []
        
        # Extract single words (filter stop words and short words)
        for word in words:
            word = word.strip('.-')
            if word and len(word) > 2 and word not in STOP_WORDS:
                keywords.append(word)
        
        # Extract bigrams (two-word phrases)
        for i in range(len(words) - 1):
            w1, w2 = words[i].strip('.-'), words[i+1].strip('.-')
            if w1 and w2 and w1 not in STOP_WORDS and w2 not in STOP_WORDS:
                if len(w1) > 1 and len(w2) > 1:
                    keywords.append(f"{w1} {w2}")
        
        return list(set(keywords))
    
    # Common technology synonyms for fuzzy matching
    TECH_SYNONYMS = {
        "react": ["reactjs", "react.js", "react js"],
        "reactjs": ["react", "react.js", "react js"],
        "node": ["nodejs", "node.js", "node js"],
        "nodejs": ["node", "node.js", "node js"],
        "javascript": ["js", "es6", "es2015", "ecmascript"],
        "js": ["javascript", "es6"],
        "typescript": ["ts"],
        "ts": ["typescript"],
        "python": ["py", "python3"],
        "py": ["python"],
        "mongodb": ["mongo", "mongo db"],
        "mongo": ["mongodb"],
        "postgresql": ["postgres", "psql", "pg"],
        "postgres": ["postgresql", "psql"],
        "mysql": ["my sql"],
        "amazon web services": ["aws"],
        "aws": ["amazon web services", "amazon"],
        "google cloud": ["gcp", "google cloud platform"],
        "gcp": ["google cloud", "google cloud platform"],
        "microsoft azure": ["azure"],
        "azure": ["microsoft azure"],
        "docker": ["containerization", "containers"],
        "kubernetes": ["k8s"],
        "k8s": ["kubernetes"],
        "machine learning": ["ml", "deep learning", "ai"],
        "ml": ["machine learning"],
        "artificial intelligence": ["ai", "machine learning"],
        "ai": ["artificial intelligence", "machine learning"],
        "natural language processing": ["nlp"],
        "nlp": ["natural language processing"],
        "ci/cd": ["cicd", "continuous integration", "continuous deployment"],
        "rest": ["restful", "rest api", "restful api"],
        "restful": ["rest", "rest api"],
        "api": ["apis", "rest api", "web api"],
        "html": ["html5"],
        "html5": ["html"],
        "css": ["css3", "scss", "sass"],
        "css3": ["css"],
        "sql": ["structured query language"],
        "nosql": ["no sql", "non-relational"],
        "git": ["github", "gitlab", "version control"],
        "github": ["git"],
        "gitlab": ["git"],
        "agile": ["scrum", "kanban"],
        "scrum": ["agile"],
        "express": ["expressjs", "express.js"],
        "expressjs": ["express", "express.js"],
        "django": ["django rest framework", "drf"],
        "flask": ["flask api"],
        "fastapi": ["fast api"],
        "vue": ["vuejs", "vue.js"],
        "vuejs": ["vue", "vue.js"],
        "angular": ["angularjs", "angular.js"],
        "angularjs": ["angular"],
        "next": ["nextjs", "next.js"],
        "nextjs": ["next", "next.js"],
        "tailwind": ["tailwindcss", "tailwind css"],
        "tailwindcss": ["tailwind"],
        "bootstrap": ["twitter bootstrap"],
        "redis": ["redis cache"],
        "elasticsearch": ["elastic search", "elastic"],
        "graphql": ["graph ql"],
        "tensorflow": ["tf"],
        "pytorch": ["torch"],
        "pandas": ["pd"],
        "numpy": ["np"],
        "opencv": ["cv2", "open cv"],
        "linux": ["unix", "ubuntu", "debian", "centos"],
        "c++": ["cpp", "cplusplus"],
        "cpp": ["c++"],
        "c#": ["csharp", "c sharp"],
        "csharp": ["c#"],
        ".net": ["dotnet", "dot net"],
        "dotnet": [".net"],
    }
    
    def _normalize_keyword(self, keyword: str) -> str:
        """Normalize a keyword for comparison."""
        return keyword.lower().strip().replace("-", " ").replace("_", " ")
    
    def _get_keyword_variants(self, keyword: str) -> set:
        """Get all variants of a keyword including synonyms."""
        normalized = self._normalize_keyword(keyword)
        variants = {normalized}
        
        # Add synonyms
        if normalized in self.TECH_SYNONYMS:
            variants.update(self._normalize_keyword(s) for s in self.TECH_SYNONYMS[normalized])
        
        # Also check if any synonym maps to this keyword
        for base, syns in self.TECH_SYNONYMS.items():
            if normalized in [self._normalize_keyword(s) for s in syns]:
                variants.add(self._normalize_keyword(base))
                variants.update(self._normalize_keyword(s) for s in syns)
        
        return variants
    
    def _calculate_keyword_match(
        self,
        profile_keywords: List[str],
        jd_keywords: List[str]
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calculate keyword match percentage between profile and JD.
        Uses fuzzy matching with synonyms for better accuracy.
        
        Returns:
            Tuple of (match_percentage, matched_keywords, missing_keywords)
        """
        # Normalize all profile keywords and get their variants
        profile_variants = set()
        profile_normalized = set()
        for kw in profile_keywords:
            normalized = self._normalize_keyword(kw)
            profile_normalized.add(normalized)
            profile_variants.update(self._get_keyword_variants(kw))
        
        matched = []
        missing = []
        
        for jd_kw in jd_keywords:
            jd_normalized = self._normalize_keyword(jd_kw)
            jd_variants = self._get_keyword_variants(jd_kw)
            
            # Check if any JD keyword variant matches any profile variant
            if jd_variants.intersection(profile_variants):
                matched.append(jd_kw)
            # Also check for substring matches (e.g., "python developer" contains "python")
            elif any(jd_normalized in pv or pv in jd_normalized for pv in profile_variants if len(pv) > 2):
                matched.append(jd_kw)
            else:
                missing.append(jd_kw)
        
        match_percentage = (len(matched) / len(jd_keywords) * 100) if jd_keywords else 0
        
        return match_percentage, matched, missing
    
    def _analyze_bullet_length(self, bullets: List[str]) -> Dict[str, Any]:
        """Analyze bullet points for optimal length."""
        analysis = {
            "total_bullets": len(bullets),
            "optimal_bullets": 0,
            "too_short": 0,
            "too_long": 0,
            "bullet_details": []
        }
        
        for bullet in bullets:
            word_count = len(bullet.split())
            status = "optimal"
            
            if word_count < self.BULLET_MIN_WORDS:
                analysis["too_short"] += 1
                status = "too_short"
            elif word_count > self.BULLET_MAX_WORDS:
                analysis["too_long"] += 1
                status = "too_long"
            else:
                analysis["optimal_bullets"] += 1
            
            analysis["bullet_details"].append({
                "text": bullet[:50] + "..." if len(bullet) > 50 else bullet,
                "word_count": word_count,
                "status": status
            })
        
        analysis["bullet_score"] = (
            analysis["optimal_bullets"] / analysis["total_bullets"] * 100
            if analysis["total_bullets"] > 0 else 0
        )
        
        return analysis
    
    def _check_keyword_stuffing(self, text: str) -> Dict[str, Any]:
        """Check for keyword stuffing."""
        words = text.lower().split()
        word_freq = Counter(words)
        
        # Filter out common words
        stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"}
        word_freq = {k: v for k, v in word_freq.items() if k not in stop_words and len(k) > 2}
        
        # Calculate total word count
        total_words = len(words)
        
        # Check for suspicious repetition (same word appearing more than 3% of total)
        stuffed_keywords = []
        for word, count in word_freq.items():
            frequency = count / total_words * 100
            if frequency > 3 and count > 3:
                stuffed_keywords.append({
                    "word": word,
                    "count": count,
                    "frequency": round(frequency, 2)
                })
        
        return {
            "is_stuffed": len(stuffed_keywords) > 0,
            "stuffed_keywords": stuffed_keywords,
            "recommendation": "Reduce repetition of highlighted keywords" if stuffed_keywords else "No keyword stuffing detected"
        }
    
    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate semantic similarity using simple word overlap (Jaccard similarity).
        This is a lightweight alternative to embedding-based similarity.
        """
        try:
            # Tokenize and clean
            words1 = set(w.lower() for w in re.findall(r'\b\w+\b', text1) if len(w) > 2 and w.lower() not in STOP_WORDS)
            words2 = set(w.lower() for w in re.findall(r'\b\w+\b', text2) if len(w) > 2 and w.lower() not in STOP_WORDS)
            
            if not words1 or not words2:
                return 0.0
            
            # Jaccard similarity
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            return len(intersection) / len(union) if union else 0.0
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def _check_section_headers(self, profile: ProfileResponse) -> Dict[str, Any]:
        """Check if profile uses ATS-recognized section headers."""
        sections_present = []
        
        if profile.education:
            sections_present.append("education")
        if any([
            profile.skills.programming_languages,
            profile.skills.technical_skills,
            profile.skills.developer_tools
        ]):
            sections_present.append("skills")
        if profile.projects:
            sections_present.append("projects")
        if profile.internships:
            sections_present.append("internships")
        if profile.certifications:
            sections_present.append("certifications")
        if profile.achievements:
            sections_present.append("achievements")
        
        return {
            "sections_present": sections_present,
            "all_standard": all(s in self.STANDARD_SECTION_HEADERS for s in sections_present),
            "score": len(sections_present) / 6 * 100
        }
    
    async def analyze_ats_compatibility(
        self,
        profile: ProfileResponse,
        job_description: str,
        jd_keywords: Dict[str, List[str]],
        optimized_content: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive ATS compatibility analysis.
        
        Args:
            profile: User's profile data
            job_description: Job description text
            jd_keywords: Keywords extracted from JD
            optimized_content: Optional optimized content to analyze instead of raw profile
            
        Returns:
            Comprehensive ATS analysis with scores and recommendations
        """
        # Use optimized content if available, otherwise use original profile
        if optimized_content:
            profile_text = self._optimized_content_to_text(optimized_content, profile)
        else:
            profile_text = self._profile_to_text(profile)
        
        profile_keywords = self._extract_keywords_rule_based(profile_text)
        
        # Also add all explicit skills from optimized content as keywords
        if optimized_content and optimized_content.get("skills"):
            opt_skills = optimized_content["skills"]
            profile_keywords.extend(opt_skills.get("programming_languages", []))
            profile_keywords.extend(opt_skills.get("technical_skills", []))
            profile_keywords.extend(opt_skills.get("developer_tools", []))
        
        # Flatten JD keywords - include ALL categories
        all_jd_keywords = (
            jd_keywords.get("keywords", []) +
            jd_keywords.get("skills", []) +
            jd_keywords.get("technologies", []) +
            jd_keywords.get("soft_skills", []) +
            jd_keywords.get("methodologies", [])
        )
        
        # Calculate keyword match
        keyword_match, matched, missing = self._calculate_keyword_match(
            profile_keywords, all_jd_keywords
        )
        
        # Analyze bullets - use optimized bullets if available
        all_bullets = []
        if optimized_content:
            # Use optimized bullets
            for project in optimized_content.get("projects", []):
                all_bullets.extend(project.get("optimized_bullets", []))
            for internship in optimized_content.get("internships", []):
                all_bullets.extend(internship.get("optimized_bullets", []))
        
        # Fall back to original bullets if no optimized content
        if not all_bullets:
            for project in profile.projects:
                all_bullets.extend(project.bullet_points)
            for internship in profile.internships:
                all_bullets.extend(internship.bullet_points)
            for cert in profile.certifications:
                all_bullets.extend(cert.bullet_points)
        
        bullet_analysis = self._analyze_bullet_length(all_bullets)
        
        # Check keyword stuffing
        stuffing_analysis = self._check_keyword_stuffing(profile_text)
        
        # Check section headers
        section_analysis = self._check_section_headers(profile)
        
        # Calculate semantic similarity
        semantic_score = self._calculate_semantic_similarity(profile_text, job_description)
        
        # Calculate overall ATS score
        ats_score = self._calculate_overall_score(
            keyword_match=keyword_match,
            bullet_score=bullet_analysis["bullet_score"],
            section_score=section_analysis["score"],
            semantic_score=semantic_score * 100,
            is_stuffed=stuffing_analysis["is_stuffed"]
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            keyword_match=keyword_match,
            missing_keywords=missing,
            bullet_analysis=bullet_analysis,
            stuffing_analysis=stuffing_analysis,
            section_analysis=section_analysis
        )
        
        return {
            "score": ats_score,
            "keyword_match_percentage": round(keyword_match, 2),
            "aligned_skills": matched,
            "missing_keywords": missing[:20],  # Top 20 missing
            "bullet_analysis": bullet_analysis,
            "section_analysis": section_analysis,
            "keyword_stuffing": stuffing_analysis,
            "semantic_similarity": round(semantic_score * 100, 2),
            "recommendations": recommendations
        }
    
    def _optimized_content_to_text(self, optimized_content: Dict[str, Any], profile: ProfileResponse) -> str:
        """Convert optimized content to searchable text for ATS analysis.
        
        This combines all optimized content into a single text for keyword extraction.
        """
        parts = []
        
        # Professional summary (contains JD keywords) - CRITICAL
        if optimized_content.get("professional_summary"):
            parts.append(optimized_content["professional_summary"])
            logger.info(f"Professional summary included: {len(optimized_content['professional_summary'])} chars")
        
        # Optimized skills - add each skill individually for better matching
        skills = optimized_content.get("skills", {})
        prog_langs = skills.get("programming_languages", [])
        tech_skills = skills.get("technical_skills", [])
        dev_tools = skills.get("developer_tools", [])
        
        parts.extend(prog_langs)
        parts.extend(tech_skills)
        parts.extend(dev_tools)
        
        # Also add skills as space-separated string for phrase matching
        if prog_langs:
            parts.append(" ".join(prog_langs))
        if tech_skills:
            parts.append(" ".join(tech_skills))
        if dev_tools:
            parts.append(" ".join(dev_tools))
        
        logger.info(f"Optimized skills: {len(prog_langs)} langs, {len(tech_skills)} tech, {len(dev_tools)} tools")
        
        # Optimized project bullets
        for project in optimized_content.get("projects", []):
            parts.append(project.get("project_name", ""))
            parts.extend(project.get("optimized_bullets", []))
        
        # Optimized internship bullets  
        for internship in optimized_content.get("internships", []):
            parts.append(internship.get("internship_name", ""))
            parts.append(internship.get("company_name", ""))
            parts.extend(internship.get("optimized_bullets", []))
        
        # Include original tech stacks from projects
        for project in profile.projects:
            parts.extend(project.tech_stack)
        
        # Certifications from original profile
        for cert in profile.certifications:
            parts.append(cert.certificate_name)
            parts.extend(cert.bullet_points)
        
        # Achievements from original profile
        parts.extend(profile.achievements)
        
        # Injected keywords
        parts.extend(optimized_content.get("injected_keywords", []))
        
        return " ".join(parts)
    
    def _profile_to_text(self, profile: ProfileResponse) -> str:
        """Convert profile to searchable text."""
        parts = []
        
        # Skills
        parts.extend(profile.skills.programming_languages)
        parts.extend(profile.skills.technical_skills)
        parts.extend(profile.skills.developer_tools)
        
        # Projects
        for project in profile.projects:
            parts.append(project.project_name)
            parts.extend(project.tech_stack)
            parts.extend(project.bullet_points)
        
        # Internships
        for internship in profile.internships:
            parts.append(internship.internship_name)
            parts.append(internship.company_name)
            parts.extend(internship.bullet_points)
        
        # Certifications
        for cert in profile.certifications:
            parts.append(cert.certificate_name)
            parts.append(cert.issuing_company)
            parts.extend(cert.bullet_points)
        
        # Achievements
        parts.extend(profile.achievements)
        
        return " ".join(parts)
    
    def _calculate_overall_score(
        self,
        keyword_match: float,
        bullet_score: float,
        section_score: float,
        semantic_score: float,
        is_stuffed: bool
    ) -> int:
        """Calculate weighted overall ATS score.
        
        Keyword match is the most important factor for ATS systems.
        """
        # Weights optimized for ATS - keyword matching is king
        weights = {
            "keyword_match": 0.50,  # Most important for ATS
            "bullet_score": 0.15,   # Format matters less
            "section_score": 0.10,  # Sections matter less
            "semantic_score": 0.25  # Semantic relevance helps
        }
        
        # Log component scores for debugging
        logger.info(f"ATS Score Components - Keyword: {keyword_match:.1f}%, Bullet: {bullet_score:.1f}%, Section: {section_score:.1f}%, Semantic: {semantic_score:.1f}%")
        
        score = (
            keyword_match * weights["keyword_match"] +
            bullet_score * weights["bullet_score"] +
            section_score * weights["section_score"] +
            semantic_score * weights["semantic_score"]
        )
        
        # Penalty for keyword stuffing
        if is_stuffed:
            score *= 0.85
        
        final_score = min(100, max(0, int(round(score))))
        logger.info(f"Final ATS Score: {final_score}%")
        
        return final_score
    
    def _generate_recommendations(
        self,
        keyword_match: float,
        missing_keywords: List[str],
        bullet_analysis: Dict[str, Any],
        stuffing_analysis: Dict[str, Any],
        section_analysis: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations for improvement."""
        recommendations = []
        
        if keyword_match < 50:
            recommendations.append(
                f"Low keyword match ({keyword_match:.0f}%). Consider adding these skills: {', '.join(missing_keywords[:5])}"
            )
        elif keyword_match < 75:
            recommendations.append(
                f"Moderate keyword match ({keyword_match:.0f}%). Add more relevant skills from the job description."
            )
        
        if bullet_analysis["too_short"] > 0:
            recommendations.append(
                f"{bullet_analysis['too_short']} bullet points are too short. Aim for 12-20 words each."
            )
        
        if bullet_analysis["too_long"] > 0:
            recommendations.append(
                f"{bullet_analysis['too_long']} bullet points are too long. Condense to 12-20 words."
            )
        
        if stuffing_analysis["is_stuffed"]:
            keywords = [k["word"] for k in stuffing_analysis["stuffed_keywords"]]
            recommendations.append(
                f"Potential keyword stuffing detected. Reduce repetition of: {', '.join(keywords)}"
            )
        
        if section_analysis["score"] < 100:
            recommendations.append(
                "Consider adding more standard resume sections for better ATS compatibility."
            )
        
        if not recommendations:
            recommendations.append("Your resume is well-optimized for ATS systems.")
        
        return recommendations
    
    async def optimize_profile_for_jd(
        self,
        profile: ProfileResponse,
        job_description: str,
        jd_keywords: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """
        Optimize profile content for the given job description.
        
        Args:
            profile: User's profile data
            job_description: Job description text
            jd_keywords: Keywords extracted from JD
            
        Returns:
            Optimized content with enhanced bullets, summary, and injected keywords
        """
        optimized = {
            "professional_summary": "",
            "skills": {},
            "projects": [],
            "internships": [],
            "certifications": [],
            "injected_keywords": []
        }
        
        # Get all target keywords
        target_keywords = (
            jd_keywords.get("skills", []) +
            jd_keywords.get("technologies", [])
        )
        
        # Generate professional summary tailored to the JD
        try:
            profile_data = {
                "skills": {
                    "programming_languages": profile.skills.programming_languages,
                    "technical_skills": profile.skills.technical_skills,
                    "developer_tools": profile.skills.developer_tools
                },
                "projects": [{"project_name": p.project_name, "tech_stack": p.tech_stack} for p in profile.projects],
                "internships": [{"company_name": i.company_name, "internship_name": i.internship_name} for i in profile.internships]
            }
            
            summary = await groq_service.generate_professional_summary(
                profile_data=profile_data,
                job_description=job_description,
                jd_keywords=jd_keywords
            )
            optimized["professional_summary"] = summary
            logger.info(f"Generated professional summary: {summary[:100]}...")
        except Exception as e:
            logger.error(f"Error generating professional summary: {e}")
            optimized["professional_summary"] = ""
        
        # Optimize skills order and add relevant keywords
        try:
            profile_skills = {
                "programming_languages": profile.skills.programming_languages,
                "technical_skills": profile.skills.technical_skills,
                "developer_tools": profile.skills.developer_tools
            }
            
            optimized_skills = await groq_service.optimize_skills_for_jd(
                profile_skills=profile_skills,
                jd_keywords=jd_keywords
            )
            # Store optimized skills returned by LLM
            optimized["skills"] = optimized_skills

            # If LLM suggests additional skills (inferred/related), merge them into skill lists
            skills_added = optimized_skills.get("skills_added", []) or []
            # Ensure lists exist
            optimized["skills"].setdefault("programming_languages", [])
            optimized["skills"].setdefault("technical_skills", [])
            optimized["skills"].setdefault("developer_tools", [])

            # Heuristic: place common programming languages into `programming_languages`
            lang_tokens = {"python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php", "scala", "kotlin", "swift"}
            for s in skills_added:
                s_norm = s.lower()
                placed = False
                for token in lang_tokens:
                    if token in s_norm:
                        if s not in optimized["skills"]["programming_languages"]:
                            optimized["skills"]["programming_languages"].append(s)
                        placed = True
                        break
                if not placed:
                    # Default to technical skills
                    if s not in optimized["skills"]["technical_skills"]:
                        optimized["skills"]["technical_skills"].append(s)

            # Collect prioritized keywords and any added skills as injected keywords
            optimized["injected_keywords"].extend(optimized_skills.get("keywords_prioritized", []))
            optimized["injected_keywords"].extend(skills_added)
            # Deduplicate
            optimized["injected_keywords"] = list(set(optimized["injected_keywords"]))

            logger.info(f"Optimized skills with prioritized keywords; added skills: {skills_added}")
        except Exception as e:
            logger.error(f"Error optimizing skills: {e}")
            optimized["skills"] = {
                "programming_languages": profile.skills.programming_languages,
                "technical_skills": profile.skills.technical_skills,
                "developer_tools": profile.skills.developer_tools
            }
        
        # Optimize project bullets
        for project in profile.projects:
            if project.bullet_points:
                try:
                    result = await groq_service.rewrite_bullets(
                        bullets=project.bullet_points,
                        target_keywords=target_keywords[:10],
                        context=f"Project: {project.project_name}, Tech Stack: {', '.join(project.tech_stack)}"
                    )
                    optimized["projects"].append({
                        "project_name": project.project_name,
                        "original_bullets": project.bullet_points,
                        "optimized_bullets": result.get("rewritten_bullets", project.bullet_points),
                        "keywords_injected": result.get("keywords_injected", [])
                    })
                    optimized["injected_keywords"].extend(result.get("keywords_injected", []))
                except Exception as e:
                    logger.error(f"Error optimizing project bullets: {e}")
                    optimized["projects"].append({
                        "project_name": project.project_name,
                        "original_bullets": project.bullet_points,
                        "optimized_bullets": project.bullet_points,
                        "keywords_injected": []
                    })
        
        # Optimize internship bullets
        for internship in profile.internships:
            if internship.bullet_points:
                try:
                    result = await groq_service.rewrite_bullets(
                        bullets=internship.bullet_points,
                        target_keywords=target_keywords[:10],
                        context=f"Internship: {internship.internship_name} at {internship.company_name}"
                    )
                    optimized["internships"].append({
                        "internship_name": internship.internship_name,
                        "company_name": internship.company_name,
                        "original_bullets": internship.bullet_points,
                        "optimized_bullets": result.get("rewritten_bullets", internship.bullet_points),
                        "keywords_injected": result.get("keywords_injected", [])
                    })
                    optimized["injected_keywords"].extend(result.get("keywords_injected", []))
                except Exception as e:
                    logger.error(f"Error optimizing internship bullets: {e}")
        
        # Remove duplicate injected keywords
        optimized["injected_keywords"] = list(set(optimized["injected_keywords"]))
        
        # Log final optimized content for debugging (keys and counts)
        try:
            skills = optimized.get("skills", {})
            logger.info(
                "Final optimized content: projects=%d, internships=%d, skills_prog=%d, skills_tech=%d, injected_keywords=%d",
                len(optimized.get("projects", [])),
                len(optimized.get("internships", [])),
                len(skills.get("programming_languages", [])),
                len(skills.get("technical_skills", [])),
                len(optimized.get("injected_keywords", []))
            )
        except Exception:
            logger.debug("Unable to log optimized content summary")

        return optimized


# Singleton instance
ats_engine = ATSOptimizationEngine()
