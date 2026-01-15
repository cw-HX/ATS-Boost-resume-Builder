"""
Document compilation service for PDF and DOCX generation.
Handles sandboxed LaTeX compilation and Pandoc conversion.
"""
import os
import uuid
import shutil
import asyncio
import tempfile
import logging
import subprocess
from typing import Optional, Tuple
from pathlib import Path

from app.core.config import settings
from app.models.schemas import PDFCompilationResult, DOCXConversionResult

logger = logging.getLogger(__name__)


class DocumentCompiler:
    """
    Service for compiling LaTeX to PDF and converting to DOCX.
    Uses sandboxed compilation for security.
    """
    
    def __init__(self):
        """Initialize the document compiler."""
        self.latex_compiler = settings.LATEX_COMPILER
        self.latex_timeout = settings.LATEX_TIMEOUT
        self.pandoc_timeout = settings.PANDOC_TIMEOUT
        self.temp_base_dir = Path(settings.LATEX_TEMP_DIR)
        
        # Ensure temp directory exists
        self.temp_base_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_sandbox_dir(self) -> Path:
        """Create a sandboxed temporary directory for compilation."""
        sandbox_id = str(uuid.uuid4())
        sandbox_dir = self.temp_base_dir / sandbox_id
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        return sandbox_dir
    
    def _cleanup_sandbox(self, sandbox_dir: Path) -> None:
        """Clean up sandbox directory after compilation."""
        try:
            if sandbox_dir.exists():
                shutil.rmtree(sandbox_dir)
        except Exception as e:
            logger.warning(f"Failed to cleanup sandbox {sandbox_dir}: {e}")
    
    async def compile_latex_to_pdf(
        self,
        latex_code: str,
        output_filename: str = "cv"
    ) -> PDFCompilationResult:
        """
        Compile LaTeX code to PDF in a sandboxed environment.
        
        Args:
            latex_code: LaTeX source code
            output_filename: Base name for output file (without extension)
            
        Returns:
            PDFCompilationResult with success status and path or error
        """
        sandbox_dir = self._create_sandbox_dir()
        
        try:
            # Write LaTeX file
            tex_file = sandbox_dir / f"{output_filename}.tex"
            tex_file.write_text(latex_code, encoding='utf-8')
            
            # Compile LaTeX (run twice for references)
            for run in range(2):
                process = await asyncio.create_subprocess_exec(
                    self.latex_compiler,
                    "-interaction=nonstopmode",
                    "-halt-on-error",
                    "-output-directory", str(sandbox_dir),
                    str(tex_file),
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(sandbox_dir)
                )
                
                try:
                    stdout, stderr = await asyncio.wait_for(
                        process.communicate(),
                        timeout=self.latex_timeout
                    )
                except asyncio.TimeoutError:
                    process.kill()
                    return PDFCompilationResult(
                        success=False,
                        error_message="LaTeX compilation timed out",
                        compilation_log=None
                    )
                
                if process.returncode != 0:
                    log_file = sandbox_dir / f"{output_filename}.log"
                    compilation_log = ""
                    if log_file.exists():
                        compilation_log = log_file.read_text(encoding='utf-8', errors='ignore')
                    
                    # Extract error message from log
                    error_lines = []
                    for line in compilation_log.split('\n'):
                        if line.startswith('!') or 'Error' in line:
                            error_lines.append(line)
                    
                    error_msg = '\n'.join(error_lines[:10]) if error_lines else "Compilation failed"
                    
                    return PDFCompilationResult(
                        success=False,
                        error_message=error_msg,
                        compilation_log=compilation_log[-5000:]  # Last 5000 chars
                    )
            
            # Check if PDF was created
            pdf_file = sandbox_dir / f"{output_filename}.pdf"
            if not pdf_file.exists():
                return PDFCompilationResult(
                    success=False,
                    error_message="PDF file was not created",
                    compilation_log=None
                )
            
            # Move PDF to a persistent location
            output_dir = self.temp_base_dir / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            final_pdf = output_dir / f"{uuid.uuid4()}_{output_filename}.pdf"
            shutil.copy2(pdf_file, final_pdf)
            
            return PDFCompilationResult(
                success=True,
                pdf_path=str(final_pdf),
                error_message=None,
                compilation_log=None
            )
            
        except Exception as e:
            logger.error(f"Error compiling LaTeX: {e}")
            return PDFCompilationResult(
                success=False,
                error_message=str(e),
                compilation_log=None
            )
        
        finally:
            self._cleanup_sandbox(sandbox_dir)
    
    async def convert_latex_to_docx(
        self,
        latex_code: str,
        output_filename: str = "cv"
    ) -> DOCXConversionResult:
        """
        Convert LaTeX code to DOCX using Pandoc.
        
        Args:
            latex_code: LaTeX source code
            output_filename: Base name for output file (without extension)
            
        Returns:
            DOCXConversionResult with success status and path or error
        """
        sandbox_dir = self._create_sandbox_dir()
        
        try:
            # Write LaTeX file
            tex_file = sandbox_dir / f"{output_filename}.tex"
            tex_file.write_text(latex_code, encoding='utf-8')
            
            # Output file
            docx_file = sandbox_dir / f"{output_filename}.docx"
            
            # Convert using Pandoc
            process = await asyncio.create_subprocess_exec(
                "pandoc",
                str(tex_file),
                "-o", str(docx_file),
                "--from=latex",
                "--to=docx",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(sandbox_dir)
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.pandoc_timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return DOCXConversionResult(
                    success=False,
                    error_message="Pandoc conversion timed out"
                )
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore')
                return DOCXConversionResult(
                    success=False,
                    error_message=f"Pandoc error: {error_msg}"
                )
            
            # Check if DOCX was created
            if not docx_file.exists():
                return DOCXConversionResult(
                    success=False,
                    error_message="DOCX file was not created"
                )
            
            # Move DOCX to a persistent location
            output_dir = self.temp_base_dir / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            final_docx = output_dir / f"{uuid.uuid4()}_{output_filename}.docx"
            shutil.copy2(docx_file, final_docx)
            
            return DOCXConversionResult(
                success=True,
                docx_path=str(final_docx),
                error_message=None
            )
            
        except FileNotFoundError:
            return DOCXConversionResult(
                success=False,
                error_message="Pandoc is not installed or not in PATH"
            )
        except Exception as e:
            logger.error(f"Error converting to DOCX: {e}")
            return DOCXConversionResult(
                success=False,
                error_message=str(e)
            )
        
        finally:
            self._cleanup_sandbox(sandbox_dir)
    
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
