"""
Background task API routes.

Note: When Celery is not available, tasks run synchronously.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
import uuid

from app.core.dependencies import get_current_user_id
from app.services.tasks import (
    CELERY_AVAILABLE,
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
    Start CV generation (async if Celery available, sync otherwise).
    
    Args:
        job_description: Job description text
        user_id: Current user ID
        
    Returns:
        Task ID for tracking or immediate result
    """
    if CELERY_AVAILABLE and celery_app:
        task = generate_cv_full_task.delay(user_id, job_description)
        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "CV generation started"
        }
    
    # Run synchronously
    result = generate_cv_full_task(user_id, job_description)
    return {
        "task_id": str(uuid.uuid4()),
        "status": "COMPLETED",
        "result": result,
        "message": "CV generation completed (sync mode)"
    }


@router.post("/compile-pdf-async")
async def compile_pdf_async(
    latex_code: str,
    output_filename: str = "output.pdf",
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Start PDF compilation (async if Celery available, sync otherwise).
    
    Args:
        latex_code: LaTeX source code
        output_filename: Output filename
        user_id: Current user ID
        
    Returns:
        Task ID for tracking or immediate result
    """
    if CELERY_AVAILABLE and celery_app:
        task = compile_pdf_task.delay(latex_code, output_filename)
        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "PDF compilation started"
        }
    
    # Run synchronously
    result = compile_pdf_task(latex_code, output_filename)
    return {
        "task_id": str(uuid.uuid4()),
        "status": "COMPLETED",
        "result": result,
        "message": "PDF compilation completed (sync mode)"
    }


@router.post("/convert-docx-async")
async def convert_docx_async(
    latex_code: str,
    output_filename: str = "output.docx",
    user_id: str = Depends(get_current_user_id)
) -> Dict[str, Any]:
    """
    Start DOCX conversion (async if Celery available, sync otherwise).
    
    Args:
        latex_code: LaTeX source code
        output_filename: Output filename
        user_id: Current user ID
        
    Returns:
        Task ID for tracking or immediate result
    """
    if CELERY_AVAILABLE and celery_app:
        task = convert_docx_task.delay(latex_code, output_filename)
        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "DOCX conversion started"
        }
    
    # Run synchronously
    result = convert_docx_task(latex_code, output_filename)
    return {
        "task_id": str(uuid.uuid4()),
        "status": "COMPLETED",
        "result": result,
        "message": "DOCX conversion completed (sync mode)"
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
