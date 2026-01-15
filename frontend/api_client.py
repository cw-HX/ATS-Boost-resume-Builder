"""
API Client for communicating with FastAPI backend.
All API interactions are centralized here.
"""
import requests
from typing import Dict, Any, Optional, List
import streamlit as st
from config import config


class APIClient:
    """Client for backend API communication."""
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token."""
        headers = {"Content-Type": "application/json"}
        
        token = st.session_state.get(config.TOKEN_KEY)
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors."""
        if response.status_code == 401:
            # Token expired, try to refresh
            if self._refresh_token():
                # Retry the request
                return None  # Signal to retry
            else:
                # Clear session and redirect to login
                self._clear_session()
                st.error("Session expired. Please log in again.")
                st.rerun()
        
        if response.status_code >= 400:
            try:
                error_data = response.json()
                detail = error_data.get("detail", "An error occurred")
                
                # Handle validation errors (FastAPI returns list of errors)
                if isinstance(detail, list):
                    # Extract first validation error message
                    if detail and isinstance(detail[0], dict):
                        error_msg = detail[0].get("msg", "Validation error")
                    else:
                        error_msg = str(detail[0]) if detail else "Validation error"
                else:
                    error_msg = str(detail)
            except:
                error_msg = response.text or "An error occurred"
            raise Exception(error_msg)
        
        return response.json()
    
    def _refresh_token(self) -> bool:
        """Attempt to refresh the access token."""
        refresh_token = st.session_state.get(config.REFRESH_TOKEN_KEY)
        if not refresh_token:
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/auth/refresh",
                json={"refresh_token": refresh_token}
            )
            
            if response.status_code == 200:
                data = response.json()
                st.session_state[config.TOKEN_KEY] = data["access_token"]
                st.session_state[config.REFRESH_TOKEN_KEY] = data["refresh_token"]
                return True
        except:
            pass
        
        return False
    
    def _clear_session(self):
        """Clear authentication session."""
        for key in [config.TOKEN_KEY, config.REFRESH_TOKEN_KEY, config.USER_KEY]:
            if key in st.session_state:
                del st.session_state[key]
    
    # ============== Authentication ==============
    
    def signup(self, email: str, password: str) -> Dict[str, Any]:
        """Register a new user."""
        response = requests.post(
            f"{self.base_url}/auth/signup",
            json={"email": email, "password": password},
            timeout=30
        )
        return self._handle_response(response)
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and get tokens."""
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
            timeout=30
        )
        data = self._handle_response(response)
        
        # Store tokens
        st.session_state[config.TOKEN_KEY] = data["access_token"]
        st.session_state[config.REFRESH_TOKEN_KEY] = data["refresh_token"]
        
        # Get user info
        user_info = self.get_current_user()
        st.session_state[config.USER_KEY] = user_info
        
        return data
    
    def logout(self):
        """Logout user."""
        try:
            requests.post(
                f"{self.base_url}/auth/logout",
                headers=self._get_headers()
            )
        except:
            pass
        
        self._clear_session()
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current user info."""
        response = requests.get(
            f"{self.base_url}/auth/me",
            headers=self._get_headers(),
            timeout=30
        )
        return self._handle_response(response)
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated."""
        return config.TOKEN_KEY in st.session_state
    
    # ============== Profile ==============
    
    def get_profile(self) -> Optional[Dict[str, Any]]:
        """Get user profile."""
        try:
            response = requests.get(
                f"{self.base_url}/profile/",
                headers=self._get_headers()
            )
            return self._handle_response(response)
        except Exception as e:
            if "not found" in str(e).lower():
                return None
            raise
    
    def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create user profile."""
        response = requests.post(
            f"{self.base_url}/profile/",
            headers=self._get_headers(),
            json=profile_data
        )
        return self._handle_response(response)
    
    def update_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile."""
        response = requests.put(
            f"{self.base_url}/profile/",
            headers=self._get_headers(),
            json=profile_data
        )
        return self._handle_response(response)
    
    def add_education(self, education: Dict[str, Any]) -> Dict[str, Any]:
        """Add education entry."""
        response = requests.post(
            f"{self.base_url}/profile/education",
            headers=self._get_headers(),
            json=education
        )
        return self._handle_response(response)
    
    def update_education(self, index: int, education: Dict[str, Any]) -> Dict[str, Any]:
        """Update education entry."""
        response = requests.put(
            f"{self.base_url}/profile/education/{index}",
            headers=self._get_headers(),
            json=education
        )
        return self._handle_response(response)
    
    def delete_education(self, index: int) -> Dict[str, Any]:
        """Delete education entry."""
        response = requests.delete(
            f"{self.base_url}/profile/education/{index}",
            headers=self._get_headers()
        )
        return self._handle_response(response)
    
    def update_skills(self, skills: Dict[str, Any]) -> Dict[str, Any]:
        """Update skills section."""
        response = requests.put(
            f"{self.base_url}/profile/skills",
            headers=self._get_headers(),
            json=skills
        )
        return self._handle_response(response)
    
    def add_project(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Add project entry."""
        response = requests.post(
            f"{self.base_url}/profile/projects",
            headers=self._get_headers(),
            json=project
        )
        return self._handle_response(response)
    
    def update_project(self, index: int, project: Dict[str, Any]) -> Dict[str, Any]:
        """Update project entry."""
        response = requests.put(
            f"{self.base_url}/profile/projects/{index}",
            headers=self._get_headers(),
            json=project
        )
        return self._handle_response(response)
    
    def delete_project(self, index: int) -> Dict[str, Any]:
        """Delete project entry."""
        response = requests.delete(
            f"{self.base_url}/profile/projects/{index}",
            headers=self._get_headers()
        )
        return self._handle_response(response)
    
    def add_internship(self, internship: Dict[str, Any]) -> Dict[str, Any]:
        """Add internship entry."""
        response = requests.post(
            f"{self.base_url}/profile/internships",
            headers=self._get_headers(),
            json=internship
        )
        return self._handle_response(response)
    
    def update_internship(self, index: int, internship: Dict[str, Any]) -> Dict[str, Any]:
        """Update internship entry."""
        response = requests.put(
            f"{self.base_url}/profile/internships/{index}",
            headers=self._get_headers(),
            json=internship
        )
        return self._handle_response(response)
    
    def delete_internship(self, index: int) -> Dict[str, Any]:
        """Delete internship entry."""
        response = requests.delete(
            f"{self.base_url}/profile/internships/{index}",
            headers=self._get_headers()
        )
        return self._handle_response(response)
    
    def add_certification(self, certification: Dict[str, Any]) -> Dict[str, Any]:
        """Add certification entry."""
        response = requests.post(
            f"{self.base_url}/profile/certifications",
            headers=self._get_headers(),
            json=certification
        )
        return self._handle_response(response)
    
    def update_certification(self, index: int, certification: Dict[str, Any]) -> Dict[str, Any]:
        """Update certification entry."""
        response = requests.put(
            f"{self.base_url}/profile/certifications/{index}",
            headers=self._get_headers(),
            json=certification
        )
        return self._handle_response(response)
    
    def delete_certification(self, index: int) -> Dict[str, Any]:
        """Delete certification entry."""
        response = requests.delete(
            f"{self.base_url}/profile/certifications/{index}",
            headers=self._get_headers()
        )
        return self._handle_response(response)
    
    def add_achievement(self, achievement: str) -> Dict[str, Any]:
        """Add achievement."""
        response = requests.post(
            f"{self.base_url}/profile/achievements",
            headers=self._get_headers(),
            params={"achievement": achievement}
        )
        return self._handle_response(response)
    
    def update_achievement(self, index: int, achievement: str) -> Dict[str, Any]:
        """Update achievement."""
        response = requests.put(
            f"{self.base_url}/profile/achievements/{index}",
            headers=self._get_headers(),
            params={"achievement": achievement}
        )
        return self._handle_response(response)
    
    def delete_achievement(self, index: int) -> Dict[str, Any]:
        """Delete achievement."""
        response = requests.delete(
            f"{self.base_url}/profile/achievements/{index}",
            headers=self._get_headers()
        )
        return self._handle_response(response)
    
    # ============== CV Generation ==============
    
    def generate_cv(self, job_description: str) -> Dict[str, Any]:
        """Generate CV based on job description."""
        response = requests.post(
            f"{self.base_url}/cv/generate",
            headers=self._get_headers(),
            json={"job_description": job_description},
            timeout=60  # CV generation can take time
        )
        return self._handle_response(response)
    
    def analyze_ats(self, job_description: str) -> Dict[str, Any]:
        """Analyze ATS compatibility."""
        response = requests.get(
            f"{self.base_url}/cv/analyze",
            headers=self._get_headers(),
            params={"job_description": job_description},
            timeout=30
        )
        return self._handle_response(response)
    
    def get_cv_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get CV generation history."""
        response = requests.get(
            f"{self.base_url}/cv/history",
            headers=self._get_headers(),
            params={"limit": limit}
        )
        return self._handle_response(response)
    
    def get_cv(self, cv_id: str) -> Dict[str, Any]:
        """Get specific CV."""
        response = requests.get(
            f"{self.base_url}/cv/{cv_id}",
            headers=self._get_headers()
        )
        return self._handle_response(response)
    
    def get_cv_latex(self, cv_id: str) -> str:
        """Get CV LaTeX code."""
        response = requests.get(
            f"{self.base_url}/cv/{cv_id}/latex",
            headers=self._get_headers()
        )
        if response.status_code >= 400:
            raise Exception("Failed to get LaTeX code")
        return response.text
    
    def download_pdf(self, cv_id: str) -> bytes:
        """Download CV as PDF."""
        response = requests.get(
            f"{self.base_url}/cv/{cv_id}/download-pdf",
            headers=self._get_headers(),
            timeout=60
        )
        if response.status_code >= 400:
            try:
                error = response.json().get("detail", "Failed to download PDF")
            except:
                error = "Failed to download PDF"
            raise Exception(error)
        return response.content
    
    def download_docx(self, cv_id: str) -> bytes:
        """Download CV as DOCX."""
        response = requests.get(
            f"{self.base_url}/cv/{cv_id}/download-docx",
            headers=self._get_headers(),
            timeout=60
        )
        if response.status_code >= 400:
            try:
                error = response.json().get("detail", "Failed to download DOCX")
            except:
                error = "Failed to download DOCX"
            raise Exception(error)
        return response.content
    
    def delete_cv(self, cv_id: str) -> Dict[str, Any]:
        """Delete a CV."""
        response = requests.delete(
            f"{self.base_url}/cv/{cv_id}",
            headers=self._get_headers()
        )
        return self._handle_response(response)


# Singleton instance
api_client = APIClient()
