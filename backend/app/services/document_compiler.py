"""
Document compilation service for PDF and DOCX generation.
Uses a remote LaTeX API for cloud-based compilation (no local LaTeX needed).
"""
import os
import uuid
import shutil
import asyncio
import tempfile
import logging
import httpx
from typing import Optional, Tuple
from pathlib import Path

from app.core.config import settings
from app.models.schemas import PDFCompilationResult, DOCXConversionResult

logger = logging.getLogger(__name__)

# Free LaTeX compilation API (no auth required)
LATEX_API_URL = "https://latex.ytotech.com/builds/sync"


class DocumentCompiler:
    """
    Service for compiling LaTeX to PDF using a remote API.
    No local LaTeX installation required.
    """
    
    def __init__(self):
        """Initialize the document compiler."""
        self.latex_timeout = settings.LATEX_TIMEOUT
        self.temp_base_dir = Path(settings.LATEX_TEMP_DIR)
        
        # Ensure temp directory exists
        self.temp_base_dir.mkdir(parents=True, exist_ok=True)
    
    async def compile_latex_to_pdf(
        self,
        latex_code: str,
        output_filename: str = "cv"
    ) -> PDFCompilationResult:
        """
        Compile LaTeX code to PDF using remote LaTeX API.
        
        Args:
            latex_code: LaTeX source code
            output_filename: Base name for output file (without extension)
            
        Returns:
            PDFCompilationResult with success status and path or error
        """
        try:
            # Prepare API request payload
            payload = {
                "compiler": "pdflatex",
                "resources": [
                    {
                        "main": True,
                        "content": latex_code
                    }
                ]
            }
            
            async with httpx.AsyncClient(timeout=self.latex_timeout) as client:
                response = await client.post(
                    LATEX_API_URL,
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
            
            # Check for API errors
            if response.status_code != 200:
                # Try to extract error message from response
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", response.text[:500])
                except Exception:
                    error_msg = response.text[:500]
                
                logger.error(f"LaTeX API error: {response.status_code} - {error_msg}")
                return PDFCompilationResult(
                    success=False,
                    error_message=f"LaTeX API error ({response.status_code}): {error_msg}",
                    compilation_log=None
                )
            
            # Check content type
            content_type = response.headers.get("content-type", "")
            if "application/pdf" not in content_type:
                # API returned an error in JSON format
                try:
                    error_data = response.json()
                    logs = error_data.get("logs", "")
                    error_msg = "LaTeX compilation failed"
                    
                    # Extract error lines from logs
                    if logs:
                        error_lines = [l for l in logs.split('\n') if l.startswith('!') or 'Error' in l]
                        if error_lines:
                            error_msg = '\n'.join(error_lines[:10])
                    
                    return PDFCompilationResult(
                        success=False,
                        error_message=error_msg,
                        compilation_log=logs[-5000:] if logs else None
                    )
                except Exception:
                    return PDFCompilationResult(
                        success=False,
                        error_message="Unexpected response from LaTeX API",
                        compilation_log=None
                    )
            
            # Save PDF to output directory
            output_dir = self.temp_base_dir / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            final_pdf = output_dir / f"{uuid.uuid4()}_{output_filename}.pdf"
            final_pdf.write_bytes(response.content)
            
            logger.info(f"PDF compiled successfully: {final_pdf}")
            
            return PDFCompilationResult(
                success=True,
                pdf_path=str(final_pdf),
                error_message=None,
                compilation_log=None
            )
            
        except httpx.TimeoutException:
            logger.error("LaTeX API request timed out")
            return PDFCompilationResult(
                success=False,
                error_message="LaTeX compilation timed out",
                compilation_log=None
            )
        except httpx.RequestError as e:
            logger.error(f"LaTeX API request error: {e}")
            return PDFCompilationResult(
                success=False,
                error_message=f"LaTeX API connection error: {str(e)}",
                compilation_log=None
            )
        except Exception as e:
            logger.error(f"Error compiling LaTeX: {e}")
            return PDFCompilationResult(
                success=False,
                error_message=str(e),
                compilation_log=None
            )
    
    async def convert_latex_to_docx(
        self,
        latex_code: str,
        output_filename: str = "cv"
    ) -> DOCXConversionResult:
        """
        Convert LaTeX to DOCX.
        
        Note: Without local Pandoc, DOCX conversion is not available.
        Consider using python-docx for direct DOCX generation in the future.
        
        Args:
            latex_code: LaTeX source code
            output_filename: Base name for output file (without extension)
            
        Returns:
            DOCXConversionResult with error (not supported in cloud deployment)
        """
        return DOCXConversionResult(
            success=False,
            error_message="DOCX conversion is not available in cloud deployment. Please download the PDF instead."
        )
    
    def read_pdf(self, pdf_path: str) -> Optional[bytes]:
        """
        Read PDF file contents.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            PDF file contents as bytes, or None if not found
        """
        try:
            path = Path(pdf_path)
            if path.exists() and path.suffix == '.pdf':
                return path.read_bytes()
            return None
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return None
    
    def read_docx(self, docx_path: str) -> Optional[bytes]:
        """
        Read DOCX file contents.
        
        Args:
            docx_path: Path to DOCX file
            
        Returns:
            DOCX file contents as bytes, or None if not found
        """
        try:
            path = Path(docx_path)
            if path.exists() and path.suffix == '.docx':
                return path.read_bytes()
            return None
        except Exception as e:
            logger.error(f"Error reading DOCX: {e}")
            return None
    
    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Clean up old generated files.
        
        Args:
            max_age_hours: Maximum age of files to keep
            
        Returns:
            Number of files deleted
        """
        import time
        
        deleted = 0
        output_dir = self.temp_base_dir / "output"
        
        if not output_dir.exists():
            return 0
        
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        
        for file_path in output_dir.iterdir():
            try:
                if current_time - file_path.stat().st_mtime > max_age_seconds:
                    file_path.unlink()
                    deleted += 1
            except Exception as e:
                logger.warning(f"Failed to delete {file_path}: {e}")
        
        return deleted


# Singleton instance
document_compiler = DocumentCompiler()
