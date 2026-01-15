"""
Unit tests for LaTeX generator.
"""
import pytest
from app.services.latex_generator import LaTeXGenerator


class TestLaTeXGenerator:
    """Tests for LaTeX generator."""
    
    @pytest.fixture
    def latex_gen(self):
        """Create LaTeX generator instance."""
        return LaTeXGenerator()
    
    def test_escape_latex_special_chars(self, latex_gen):
        """Test LaTeX special character escaping."""
        text = "Test & Co. with 50% discount #1"
        escaped = latex_gen.escape_latex(text)
        
        assert r"\&" in escaped
        assert r"\%" in escaped
        assert r"\#" in escaped
    
    def test_escape_latex_empty_string(self, latex_gen):
        """Test escaping empty string."""
        assert latex_gen.escape_latex("") == ""
        assert latex_gen.escape_latex(None) == ""
    
    def test_validate_latex_valid(self, latex_gen):
        """Test validation of valid LaTeX."""
        latex = r"""
        \documentclass{article}
        \begin{document}
        Hello World
        \end{document}
        """
        
        result = latex_gen.validate_latex(latex)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
    
    def test_validate_latex_missing_document(self, latex_gen):
        """Test validation of LaTeX missing document tags."""
        latex = r"""
        \documentclass{article}
        Hello World
        """
        
        result = latex_gen.validate_latex(latex)
        
        assert result["valid"] is False
        assert any("document" in issue.lower() for issue in result["issues"])
    
    def test_validate_latex_unbalanced_braces(self, latex_gen):
        """Test validation of LaTeX with unbalanced braces."""
        latex = r"""
        \documentclass{article}
        \begin{document}
        \textbf{Hello World
        \end{document}
        """
        
        result = latex_gen.validate_latex(latex)
        
        assert result["valid"] is False
        assert any("brace" in issue.lower() for issue in result["issues"])
