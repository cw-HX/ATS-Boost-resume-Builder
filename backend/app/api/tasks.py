"""
Background task API routes.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any

from app.core.dependencies import get_current_user_id
from app.services.tasks import (
    celery_app,
    compile_pdf_task,
    convert_docx_task,
    generate_cv_full_task,
    get_task_status
)

router = APIRouter(prefix="/tasks", tags=["Background Tasks"])


@router.post("/generate-cv-async")
async def generate_cv_async(
    job_description: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Start asynchronous CV generation.
    
    Args:
        job_description: Job description text
        user_id: Current user ID
        
    Returns:
        Task ID for tracking
    """
    task = generate_cv_full_task.delay(user_id, job_description)
    
    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "CV generation started"
    }


@router.post("/compile-pdf-async")
async def compile_pdf_async(
    latex_code: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Start asynchronous PDF compilation.
    
    Args:
        latex_code: LaTeX source code
        user_id: Current user ID
        
    Returns:
        Task ID for tracking
    """
    task = compile_pdf_task.delay(latex_code)
    
    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "PDF compilation started"
    }


@router.post("/convert-docx-async")
async def convert_docx_async(
    latex_code: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Start asynchronous DOCX conversion.
    
    Args:
        latex_code: LaTeX source code
        user_id: Current user ID
        
    Returns:
        Task ID for tracking
    """
    task = convert_docx_task.delay(latex_code)
    
    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "DOCX conversion started"
    }


@router.get("/status/{task_id}")
async def get_task_status_endpoint(
    task_id: str,
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Get the status of a background task.
    
    Args:
        task_id: Task ID
        user_id: Current user ID
        
    Returns:
        Task status and result
    """
    return get_task_status(task_id)
