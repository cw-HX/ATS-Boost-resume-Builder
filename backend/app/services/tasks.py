"""
Celery application configuration and tasks.
Handles background processing for ATS scoring, LaTeX compilation, and DOCX conversion.
"""
from celery import Celery
from celery.result import AsyncResult
import logging
from typing import Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Celery
celery_app = Celery(
    "ats_cv_generator",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.services.tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max
    task_soft_time_limit=240,  # 4 minutes soft limit
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
)


@celery_app.task(bind=True, name="tasks.compile_pdf")
def compile_pdf_task(self, latex_code: str, output_filename: str = "cv") -> Dict[str, Any]:
    """
    Background task to compile LaTeX to PDF.
    
    Args:
        latex_code: LaTeX source code
        output_filename: Base filename for output
        
    Returns:
        Compilation result
    """
    import asyncio
    from app.services.document_compiler import document_compiler
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            document_compiler.compile_latex_to_pdf(latex_code, output_filename)
        )
        
        return {
            "success": result.success,
            "pdf_path": result.pdf_path,
            "error_message": result.error_message
        }
        
    except Exception as e:
        logger.error(f"PDF compilation task failed: {e}")
        return {
            "success": False,
            "pdf_path": None,
            "error_message": str(e)
        }
    finally:
        loop.close()


@celery_app.task(bind=True, name="tasks.convert_docx")
def convert_docx_task(self, latex_code: str, output_filename: str = "cv") -> Dict[str, Any]:
    """
    Background task to convert LaTeX to DOCX.
    
    Args:
        latex_code: LaTeX source code
        output_filename: Base filename for output
        
    Returns:
        Conversion result
    """
    import asyncio
    from app.services.document_compiler import document_compiler
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            document_compiler.convert_latex_to_docx(latex_code, output_filename)
        )
        
        return {
            "success": result.success,
            "docx_path": result.docx_path,
            "error_message": result.error_message
        }
        
    except Exception as e:
        logger.error(f"DOCX conversion task failed: {e}")
        return {
            "success": False,
            "docx_path": None,
            "error_message": str(e)
        }
    finally:
        loop.close()


@celery_app.task(bind=True, name="tasks.analyze_ats")
def analyze_ats_task(
    self,
    profile_data: Dict[str, Any],
    job_description: str,
    jd_keywords: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Background task to analyze ATS compatibility.
    
    Args:
        profile_data: User profile data
        job_description: Job description text
        jd_keywords: Extracted JD keywords
        
    Returns:
        ATS analysis result
    """
    import asyncio
    from app.services.ats_engine import ats_engine
    from app.models.schemas import ProfileResponse
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        profile = ProfileResponse(**profile_data)
        
        result = loop.run_until_complete(
            ats_engine.analyze_ats_compatibility(profile, job_description, jd_keywords)
        )
        
        return result
        
    except Exception as e:
        logger.error(f"ATS analysis task failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        loop.close()


@celery_app.task(bind=True, name="tasks.generate_cv_full")
def generate_cv_full_task(
    self,
    user_id: str,
    job_description: str
) -> Dict[str, Any]:
    """
    Background task for full CV generation pipeline.
    
    Args:
        user_id: User ID
        job_description: Job description text
        
    Returns:
        Generated CV result
    """
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    from app.services.llm_service import groq_service
    from app.services.ats_engine import ats_engine
    from app.services.latex_generator import latex_generator
    from app.models.schemas import ProfileResponse
    from datetime import datetime
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def generate():
            # Connect to MongoDB
            client = AsyncIOMotorClient(settings.MONGODB_URL)
            db = client[settings.MONGODB_DATABASE]
            
            # Get profile
            profile_doc = await db.profiles.find_one({"user_id": user_id})
            if not profile_doc:
                return {"success": False, "error": "Profile not found"}
            
            profile_doc["_id"] = str(profile_doc["_id"])
            profile = ProfileResponse(**profile_doc)
            
            # Extract keywords
            jd_keywords = await groq_service.extract_keywords_from_jd(job_description)
            
            # Optimize and generate
            best_score = 0
            best_result = None
            
            for attempt in range(settings.ATS_MAX_RETRIES):
                optimized_content = await ats_engine.optimize_profile_for_jd(
                    profile, job_description, jd_keywords
                )
                
                latex_code = latex_generator.generate_latex(profile, optimized_content)
                
                ats_analysis = await ats_engine.analyze_ats_compatibility(
                    profile, job_description, jd_keywords
                )
                
                if ats_analysis["score"] > best_score:
                    best_score = ats_analysis["score"]
                    best_result = {
                        "latex_code": latex_code,
                        "ats_analysis": ats_analysis
                    }
                
                if ats_analysis["score"] >= settings.ATS_MIN_SCORE:
                    break
            
            if not best_result:
                return {"success": False, "error": "Failed to generate CV"}
            
            # Save to database
            cv_doc = {
                "user_id": user_id,
                "job_description": job_description,
                "aligned_skills": best_result["ats_analysis"]["aligned_skills"],
                "ats_score": best_score,
                "latex_code": best_result["latex_code"],
                "created_at": datetime.utcnow()
            }
            
            result = await db.generated_cvs.insert_one(cv_doc)
            
            client.close()
            
            return {
                "success": True,
                "cv_id": str(result.inserted_id),
                "ats_score": best_score,
                "latex_code": best_result["latex_code"]
            }
        
        return loop.run_until_complete(generate())
        
    except Exception as e:
        logger.error(f"CV generation task failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        loop.close()


@celery_app.task(name="tasks.cleanup_old_files")
def cleanup_old_files_task(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Periodic task to cleanup old generated files.
    
    Args:
        max_age_hours: Maximum age of files to keep
        
    Returns:
        Cleanup result
    """
    from app.services.document_compiler import document_compiler
    
    try:
        deleted = document_compiler.cleanup_old_files(max_age_hours)
        return {
            "success": True,
            "deleted_files": deleted
        }
    except Exception as e:
        logger.error(f"Cleanup task failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# Configure periodic tasks
celery_app.conf.beat_schedule = {
    "cleanup-old-files": {
        "task": "tasks.cleanup_old_files",
        "schedule": 3600.0,  # Every hour
        "args": (24,)
    }
}


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the status of a Celery task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task status and result
    """
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None
    }
