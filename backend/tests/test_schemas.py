"""
Unit tests for Pydantic schemas.
"""
import pytest
from pydantic import ValidationError
from app.models.schemas import (
    UserCreate,
    PersonalDetails,
    Education,
    Skills,
    Project,
    ProfileCreate
)


class TestUserSchemas:
    """Tests for user schemas."""
    
    def test_user_create_valid(self):
        """Test valid user creation."""
        user = UserCreate(
            email="test@example.com",
            password="TestPassword123!"
        )
        
        assert user.email == "test@example.com"
    
    def test_user_create_invalid_email(self):
        """Test user creation with invalid email."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                password="TestPassword123!"
            )
    
    def test_user_create_weak_password(self):
        """Test user creation with weak password."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="weak"
            )
    
    def test_user_create_password_no_uppercase(self):
        """Test user creation with password missing uppercase."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="testpassword123!"
            )


class TestProfileSchemas:
    """Tests for profile schemas."""
    
    def test_personal_details_valid(self):
        """Test valid personal details."""
        pd = PersonalDetails(
            full_name="John Doe",
            location="New York, NY",
            phone="+1-555-123-4567",
            email="john@example.com",
            linkedin="https://linkedin.com/in/johndoe",
            github="https://github.com/johndoe"
        )
        
        assert pd.full_name == "John Doe"
        assert pd.email == "john@example.com"
    
    def test_personal_details_minimal(self):
        """Test personal details with minimal info."""
        pd = PersonalDetails(
            full_name="John Doe",
            email="john@example.com"
        )
        
        assert pd.full_name == "John Doe"
        assert pd.location == ""
    
    def test_education_valid(self):
        """Test valid education entry."""
        edu = Education(
            college_name="MIT",
            degree="B.S. Computer Science",
            cgpa_or_percentage="3.8/4.0",
            session_year="2018-2022"
        )
        
        assert edu.college_name == "MIT"
        assert edu.degree == "B.S. Computer Science"
    
    def test_skills_valid(self):
        """Test valid skills."""
        skills = Skills(
            programming_languages=["Python", "JavaScript", "Java"],
            technical_skills=["Machine Learning", "Web Development"],
            developer_tools=["Git", "Docker", "AWS"]
        )
        
        assert "Python" in skills.programming_languages
        assert len(skills.technical_skills) == 2
    
    def test_project_valid(self):
        """Test valid project."""
        project = Project(
            project_name="CV Generator",
            project_link="https://github.com/user/cv-generator",
            tech_stack=["Python", "FastAPI", "MongoDB"],
            bullet_points=[
                "Built a production-ready CV generator",
                "Implemented ATS optimization engine"
            ]
        )
        
        assert project.project_name == "CV Generator"
        assert len(project.bullet_points) == 2
    
    def test_profile_create_valid(self):
        """Test valid profile creation."""
        profile = ProfileCreate(
            personal_details=PersonalDetails(
                full_name="John Doe",
                email="john@example.com"
            ),
            education=[
                Education(
                    college_name="MIT",
                    degree="B.S. CS",
                    session_year="2020-2024"
                )
            ],
            skills=Skills(
                programming_languages=["Python"],
                technical_skills=["ML"],
                developer_tools=["Git"]
            )
        )
        
        assert profile.personal_details.full_name == "John Doe"
        assert len(profile.education) == 1
