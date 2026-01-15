"""
Pytest configuration and fixtures.
"""
import pytest
import asyncio
from typing import Generator


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_profile_data():
    """Sample profile data for testing."""
    return {
        "personal_details": {
            "full_name": "John Doe",
            "location": "San Francisco, CA",
            "phone": "+1-555-123-4567",
            "email": "john.doe@example.com",
            "linkedin": "https://linkedin.com/in/johndoe",
            "github": "https://github.com/johndoe"
        },
        "education": [
            {
                "college_name": "Stanford University",
                "degree": "M.S. Computer Science",
                "cgpa_or_percentage": "3.9/4.0",
                "session_year": "2020-2022"
            },
            {
                "college_name": "UC Berkeley",
                "degree": "B.S. Computer Science",
                "cgpa_or_percentage": "3.7/4.0",
                "session_year": "2016-2020"
            }
        ],
        "skills": {
            "programming_languages": ["Python", "JavaScript", "Java", "C++"],
            "technical_skills": ["Machine Learning", "Web Development", "Data Analysis"],
            "developer_tools": ["Git", "Docker", "Kubernetes", "AWS"]
        },
        "projects": [
            {
                "project_name": "ML Pipeline",
                "project_link": "https://github.com/johndoe/ml-pipeline",
                "tech_stack": ["Python", "TensorFlow", "AWS"],
                "bullet_points": [
                    "Built end-to-end ML pipeline processing 1M+ records daily",
                    "Reduced model training time by 40% through optimization"
                ]
            }
        ],
        "internships": [
            {
                "internship_name": "Software Engineering Intern",
                "company_name": "Google",
                "bullet_points": [
                    "Developed microservices handling 10K requests per second",
                    "Collaborated with team of 5 engineers on critical features"
                ]
            }
        ],
        "certifications": [
            {
                "certificate_name": "AWS Solutions Architect",
                "issuing_company": "Amazon Web Services",
                "bullet_points": ["Professional level certification"]
            }
        ],
        "achievements": [
            "Won first place in university hackathon",
            "Published research paper in top ML conference"
        ]
    }


@pytest.fixture
def sample_job_description():
    """Sample job description for testing."""
    return """
    Senior Software Engineer
    
    We are looking for a Senior Software Engineer to join our team.
    
    Requirements:
    - 5+ years of experience in software development
    - Strong proficiency in Python and JavaScript
    - Experience with cloud platforms (AWS, GCP, Azure)
    - Knowledge of machine learning and data analysis
    - Experience with containerization (Docker, Kubernetes)
    - Strong communication and teamwork skills
    
    Responsibilities:
    - Design and implement scalable software solutions
    - Lead technical discussions and code reviews
    - Mentor junior developers
    - Collaborate with cross-functional teams
    
    Nice to have:
    - Experience with TensorFlow or PyTorch
    - Knowledge of microservices architecture
    - Open source contributions
    """
