"""
Pydantic models for users, authentication, and profiles.
These models define the data structures used throughout the application.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field, field_validator
from bson import ObjectId
import re


# Custom type for MongoDB ObjectId
class PyObjectId(str):
    """Custom type for MongoDB ObjectId serialization."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v, info=None):
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str):
            if ObjectId.is_valid(v):
                return v
        raise ValueError("Invalid ObjectId")


# ============== User Models ==============

class UserCreate(BaseModel):
    """Schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    
    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Password must contain at least one special character")
        return v


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Schema for user response (excluding sensitive data)."""
    id: str
    email: EmailStr
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserInDB(BaseModel):
    """Schema for user stored in database."""
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    
    class Config:
        populate_by_name = True
        from_attributes = True


# ============== Token Models ==============

class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Schema for decoded JWT payload."""
    sub: str  # user_id
    exp: datetime
    iat: datetime
    type: str


class TokenRefresh(BaseModel):
    """Schema for token refresh request."""
    refresh_token: str


# ============== Profile Models ==============

class PersonalDetails(BaseModel):
    """Schema for personal details section."""
    full_name: str = Field(..., min_length=1, max_length=100)
    location: str = Field(default="", max_length=200)
    phone: str = Field(default="", max_length=20)
    email: EmailStr
    linkedin: str = Field(default="", max_length=200)
    github: str = Field(default="", max_length=200)
    
    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        """Validate phone number format."""
        if v and not re.match(r"^[\d\s\-\+\(\)]+$", v):
            raise ValueError("Invalid phone number format")
        return v


class Education(BaseModel):
    """Schema for education entry."""
    college_name: str = Field(..., min_length=1, max_length=200)
    degree: str = Field(..., min_length=1, max_length=200)
    cgpa_or_percentage: str = Field(default="", max_length=50)
    session_year: str = Field(..., max_length=50)  # e.g., "2018-2022"


class Skills(BaseModel):
    """Schema for skills section."""
    programming_languages: List[str] = Field(default_factory=list)
    technical_skills: List[str] = Field(default_factory=list)
    developer_tools: List[str] = Field(default_factory=list)


class Project(BaseModel):
    """Schema for project entry."""
    project_name: str = Field(..., min_length=1, max_length=200)
    project_link: Optional[str] = Field(default="", max_length=500)
    tech_stack: List[str] = Field(default_factory=list)
    bullet_points: List[str] = Field(default_factory=list)


class Internship(BaseModel):
    """Schema for internship entry."""
    internship_name: str = Field(..., min_length=1, max_length=200)
    company_name: str = Field(..., min_length=1, max_length=200)
    bullet_points: List[str] = Field(default_factory=list)


class Certification(BaseModel):
    """Schema for certification entry."""
    certificate_name: str = Field(..., min_length=1, max_length=200)
    issuing_company: str = Field(..., min_length=1, max_length=200)
    bullet_points: List[str] = Field(default_factory=list)


class ProfileCreate(BaseModel):
    """Schema for creating a new profile."""
    personal_details: PersonalDetails
    education: List[Education] = Field(default_factory=list)
    skills: Skills = Field(default_factory=Skills)
    projects: List[Project] = Field(default_factory=list)
    internships: List[Internship] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    achievements: List[str] = Field(default_factory=list)


class ProfileUpdate(BaseModel):
    """Schema for updating a profile."""
    personal_details: Optional[PersonalDetails] = None
    education: Optional[List[Education]] = None
    skills: Optional[Skills] = None
    projects: Optional[List[Project]] = None
    internships: Optional[List[Internship]] = None
    certifications: Optional[List[Certification]] = None
    achievements: Optional[List[str]] = None


class ProfileResponse(BaseModel):
    """Schema for profile response."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    personal_details: PersonalDetails
    education: List[Education]
    skills: Skills
    projects: List[Project]
    internships: List[Internship]
    certifications: List[Certification]
    achievements: List[str]
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        from_attributes = True


class ProfileInDB(ProfileResponse):
    """Schema for profile stored in database."""
    pass


# ============== CV Generation Models ==============

class JobDescriptionInput(BaseModel):
    """Schema for job description input."""
    job_description: str = Field(..., min_length=50, max_length=10000)


class ATSAnalysis(BaseModel):
    """Schema for ATS analysis results."""
    score: int = Field(..., ge=0, le=100)
    keyword_match_percentage: float
    aligned_skills: List[str]
    missing_keywords: List[str]
    recommendations: List[str]
    bullet_analysis: Dict[str, Any]


class CVGenerationRequest(BaseModel):
    """Schema for CV generation request."""
    job_description: str = Field(..., min_length=50, max_length=10000)


class CVGenerationResponse(BaseModel):
    """Schema for CV generation response."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    job_description: str
    aligned_skills: List[str]
    ats_score: int
    latex_code: str
    created_at: datetime
    
    class Config:
        populate_by_name = True
        from_attributes = True


class GeneratedCVInDB(BaseModel):
    """Schema for generated CV stored in database."""
    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str
    job_description: str
    aligned_skills: List[str]
    ats_score: int
    latex_code: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        from_attributes = True


# ============== Document Models ==============

class PDFCompilationResult(BaseModel):
    """Schema for PDF compilation result."""
    success: bool
    pdf_path: Optional[str] = None
    error_message: Optional[str] = None
    compilation_log: Optional[str] = None


class DOCXConversionResult(BaseModel):
    """Schema for DOCX conversion result."""
    success: bool
    docx_path: Optional[str] = None
    error_message: Optional[str] = None


# ============== LLM Models ==============

class LLMKeywordExtractionResponse(BaseModel):
    """Schema for LLM keyword extraction response."""
    keywords: List[str]
    skills: List[str]
    technologies: List[str]
    soft_skills: List[str]
    experience_requirements: List[str]


class LLMBulletRewriteRequest(BaseModel):
    """Schema for bullet point rewrite request."""
    original_bullets: List[str]
    target_keywords: List[str]
    context: str


class LLMBulletRewriteResponse(BaseModel):
    """Schema for bullet point rewrite response."""
    rewritten_bullets: List[str]
    keywords_injected: List[str]
