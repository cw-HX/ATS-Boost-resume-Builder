"""
LaTeX CV Generator using Jinja2 templates.
Generates ATS-optimized LaTeX code from user profile and JD optimization.
"""
import os
import re
import logging
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

from app.models.schemas import ProfileResponse

logger = logging.getLogger(__name__)


class LaTeXGenerator:
    """Generator for ATS-optimized LaTeX CVs."""
    
    # Characters that need escaping in LaTeX
    LATEX_ESCAPE_MAP = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }
    
    def __init__(self):
        """Initialize the LaTeX generator with Jinja2 environment."""
        template_dir = Path(__file__).parent.parent / "templates"
        
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=False,  # LaTeX doesn't use HTML escaping
            block_start_string='<%',
            block_end_string='%>',
            variable_start_string='<<',
            variable_end_string='>>',
            comment_start_string='<#',
            comment_end_string='#>',
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self.env.filters['latex_escape'] = self.escape_latex
        # Don't override the built-in join filter - it works correctly
    
    def escape_latex(self, text: str) -> str:
        """
        Escape special LaTeX characters in text.
        
        Args:
            text: Input text
            
        Returns:
            LaTeX-safe text
        """
        if not text:
            return ""
        
        # Handle URLs specially (don't escape within \href{})
        text = str(text)
        
        # Escape special characters
        for char, escape in self.LATEX_ESCAPE_MAP.items():
            if char == '\\':
                continue  # Handle backslash first
            text = text.replace(char, escape)
        
        return text
    
    def _prepare_profile_data(
        self,
        profile: ProfileResponse,
        optimized_content: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Prepare profile data for LaTeX template.
        
        Args:
            profile: User profile data
            optimized_content: Optional optimized content from ATS engine
            
        Returns:
            Template-ready data dictionary
        """
        # Flat personal details
        full_name = self.escape_latex(profile.personal_details.full_name)
        location = self.escape_latex(profile.personal_details.location)
        phone = self.escape_latex(profile.personal_details.phone)
        email = profile.personal_details.email  # Don't escape email
        linkedin = profile.personal_details.linkedin  # URLs not escaped
        github = profile.personal_details.github
        
        # Professional summary (from optimized content)
        professional_summary = ""
        if optimized_content and optimized_content.get("professional_summary"):
            professional_summary = self.escape_latex(optimized_content["professional_summary"])
        
        # Prepare technical skills as dict for items() iteration
        if optimized_content and optimized_content.get("skills") and optimized_content["skills"].get("programming_languages"):
            technical_skills = {
                "Programming Languages": [
                    self.escape_latex(s) for s in optimized_content["skills"].get("programming_languages", [])
                ],
                "Technical Skills": [
                    self.escape_latex(s) for s in optimized_content["skills"].get("technical_skills", [])
                ],
                "Tools & Platforms": [
                    self.escape_latex(s) for s in optimized_content["skills"].get("developer_tools", [])
                ],
            }
        else:
            technical_skills = {
                "Programming Languages": [
                    self.escape_latex(s) for s in profile.skills.programming_languages
                ],
                "Technical Skills": [
                    self.escape_latex(s) for s in profile.skills.technical_skills
                ],
                "Tools & Platforms": [
                    self.escape_latex(s) for s in profile.skills.developer_tools
                ],
            }
        
        # Remove empty skill categories
        technical_skills = {k: v for k, v in technical_skills.items() if v}
        
        # Education priority mapping (higher = appears first)
        def get_education_priority(degree: str) -> int:
            degree_lower = degree.lower()
            if "phd" in degree_lower or "doctorate" in degree_lower:
                return 100
            elif "mtech" in degree_lower or "m.tech" in degree_lower:
                return 95
            elif "mca" in degree_lower or "master of computer" in degree_lower:
                return 90
            elif "mba" in degree_lower or "master of business" in degree_lower:
                return 88
            elif "msc" in degree_lower or "m.sc" in degree_lower or "master of science" in degree_lower:
                return 85
            elif "master" in degree_lower:
                return 80
            elif "btech" in degree_lower or "b.tech" in degree_lower:
                return 75
            elif "bca" in degree_lower or "bachelor of computer" in degree_lower:
                return 70
            elif "bba" in degree_lower or "bachelor of business" in degree_lower:
                return 68
            elif "bsc" in degree_lower or "b.sc" in degree_lower or "bachelor of science" in degree_lower:
                return 65
            elif "bachelor" in degree_lower:
                return 60
            elif "diploma" in degree_lower:
                return 50
            elif "xii" in degree_lower or "12th" in degree_lower or "12" in degree_lower or "senior secondary" in degree_lower or "intermediate" in degree_lower:
                return 40
            elif "x" in degree_lower or "10th" in degree_lower or "10" in degree_lower or "secondary" in degree_lower or "matriculation" in degree_lower:
                return 30
            else:
                return 20
        
        # Prepare education as dynamic list
        education = []
        for edu in profile.education:
            degree_lower = edu.degree.lower()
            priority = get_education_priority(edu.degree)
            logger.info(f"Education: {edu.degree} -> Priority: {priority}")
            
            # Determine if it's CGPA or percentage based on content
            grade_value = self.escape_latex(edu.cgpa_or_percentage)
            is_percentage = "%" in edu.cgpa_or_percentage or float(grade_value.replace('%', '').strip() or '0') > 10
            
            # Determine board for school-level education
            board = None
            if "xii" in degree_lower or "12" in degree_lower or "x" in degree_lower or "10" in degree_lower or "secondary" in degree_lower:
                board = "UP Board"  # Default, can be extended
            
            edu_entry = {
                "degree": self.escape_latex(edu.degree),
                "years": self.escape_latex(edu.session_year),
                "institution": self.escape_latex(edu.college_name),
                "board": board,
                "cgpa": grade_value if not is_percentage else None,
                "percentage": grade_value.replace('%', '').strip() if is_percentage else None,
                "_priority": priority,  # For sorting
            }
            education.append(edu_entry)
        
        # Sort education by priority (highest first)
        education.sort(key=lambda x: x["_priority"], reverse=True)
        logger.info(f"Sorted education order: {[e['degree'] for e in education]}")
        
        # Remove the internal priority field
        for edu in education:
            del edu["_priority"]
        
        # Prepare projects (use optimized bullets if available)
        projects = []
        optimized_projects = {}
        if optimized_content and "projects" in optimized_content:
            for op in optimized_content["projects"]:
                optimized_projects[op["project_name"]] = op.get("optimized_bullets", [])
        
        for project in profile.projects:
            # Use optimized bullets if available, otherwise original
            bullets = optimized_projects.get(
                project.project_name,
                project.bullet_points
            )
            
            projects.append({
                "name": self.escape_latex(project.project_name),
                "type": "Application",  # Default type
                "technologies": [self.escape_latex(t) for t in project.tech_stack],
                "bullets": [self.escape_latex(b) for b in bullets],
            })
        
        # Prepare certifications
        certifications = []
        for cert in profile.certifications:
            certifications.append({
                "title": self.escape_latex(cert.certificate_name),
                "issuer": self.escape_latex(cert.issuing_company),
                "details": [self.escape_latex(b) for b in cert.bullet_points],
            })
        
        # Optional fields
        relevant_coursework = []  # Can be extended
        additional_info = {}  # Can be extended
        
        return {
            "full_name": full_name,
            "location": location,
            "phone": phone,
            "email": email,
            "linkedin": linkedin,
            "github": github,
            "professional_summary": professional_summary,
            "technical_skills": technical_skills,
            "education": education,
            "projects": projects,
            "certifications": certifications,
            "relevant_coursework": relevant_coursework,
            "additional_info": additional_info,
        }
    
    def generate_latex(
        self,
        profile: ProfileResponse,
        optimized_content: Optional[Dict[str, Any]] = None,
        template_name: str = "cv_template.tex"
    ) -> str:
        """
        Generate LaTeX code from profile data.
        
        Args:
            profile: User profile data
            optimized_content: Optional ATS-optimized content
            template_name: Name of the template file
            
        Returns:
            Generated LaTeX code
        """
        try:
            template = self.env.get_template(template_name)
            data = self._prepare_profile_data(profile, optimized_content)
            
            latex_code = template.render(**data)
            
            # Clean up any double escapes or issues
            latex_code = self._cleanup_latex(latex_code)
            
            return latex_code
            
        except Exception as e:
            logger.error(f"Error generating LaTeX: {e}")
            raise
    
    def _cleanup_latex(self, latex_code: str) -> str:
        """
        Clean up generated LaTeX code.
        
        Args:
            latex_code: Raw LaTeX code
            
        Returns:
            Cleaned LaTeX code
        """
        # Remove multiple consecutive blank lines
        latex_code = re.sub(r'\n{3,}', '\n\n', latex_code)
        
        # Remove trailing whitespace from lines
        lines = [line.rstrip() for line in latex_code.split('\n')]
        latex_code = '\n'.join(lines)
        
        return latex_code
    
    def validate_latex(self, latex_code: str) -> Dict[str, Any]:
        """
        Perform basic validation on LaTeX code.
        
        Args:
            latex_code: LaTeX code to validate
            
        Returns:
            Validation result with any issues found
        """
        issues = []
        
        # Check for balanced braces
        open_braces = latex_code.count('{')
        close_braces = latex_code.count('}')
        if open_braces != close_braces:
            issues.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
        
        # Check for document structure
        if r'\begin{document}' not in latex_code:
            issues.append("Missing \\begin{document}")
        if r'\end{document}' not in latex_code:
            issues.append("Missing \\end{document}")
        
        # Check for documentclass
        if r'\documentclass' not in latex_code:
            issues.append("Missing \\documentclass")
        
        # Check for common unescaped characters
        # These patterns check for unescaped special characters not in commands
        if re.search(r'(?<!\\)[&%$#](?!\w)', latex_code):
            issues.append("Possible unescaped special characters detected")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues
        }


# Singleton instance
latex_generator = LaTeXGenerator()
