"""
Unit tests for ATS engine.
"""
import pytest
from app.services.ats_engine import ATSOptimizationEngine


class TestATSEngine:
    """Tests for ATS optimization engine."""
    
    @pytest.fixture
    def ats_engine(self):
        """Create ATS engine instance."""
        return ATSOptimizationEngine()
    
    def test_bullet_length_analysis_optimal(self, ats_engine):
        """Test bullet analysis with optimal length bullets."""
        bullets = [
            "Developed a machine learning model that improved prediction accuracy by 25% using Python and TensorFlow.",
            "Led a team of five developers in implementing microservices architecture reducing deployment time by 40%."
        ]
        
        analysis = ats_engine._analyze_bullet_length(bullets)
        
        assert analysis["total_bullets"] == 2
        assert analysis["optimal_bullets"] == 2
        assert analysis["too_short"] == 0
        assert analysis["too_long"] == 0
    
    def test_bullet_length_analysis_too_short(self, ats_engine):
        """Test bullet analysis with too short bullets."""
        bullets = [
            "Built a website.",
            "Used Python."
        ]
        
        analysis = ats_engine._analyze_bullet_length(bullets)
        
        assert analysis["too_short"] == 2
        assert analysis["optimal_bullets"] == 0
    
    def test_keyword_match(self, ats_engine):
        """Test keyword matching."""
        profile_keywords = ["python", "machine learning", "aws", "docker"]
        jd_keywords = ["python", "machine learning", "kubernetes", "sql"]
        
        match_pct, matched, missing = ats_engine._calculate_keyword_match(
            profile_keywords, jd_keywords
        )
        
        assert match_pct == 50.0
        assert "python" in matched
        assert "machine learning" in matched
        assert "kubernetes" in missing
        assert "sql" in missing
    
    def test_keyword_stuffing_detection_clean(self, ats_engine):
        """Test keyword stuffing detection with clean text."""
        text = """
        Developed machine learning models using Python and TensorFlow.
        Implemented data pipelines with Apache Spark and AWS services.
        Led cross-functional teams to deliver projects on time.
        """
        
        result = ats_engine._check_keyword_stuffing(text)
        
        assert result["is_stuffed"] is False
    
    def test_keyword_stuffing_detection_stuffed(self, ats_engine):
        """Test keyword stuffing detection with stuffed text."""
        text = """
        Python Python Python developer with Python experience.
        Used Python for Python scripts and Python automation.
        Python Python Python Python Python Python Python.
        """
        
        result = ats_engine._check_keyword_stuffing(text)
        
        assert result["is_stuffed"] is True
        assert any(k["word"] == "python" for k in result["stuffed_keywords"])
