"""
Background tasks for ATS scoring, LaTeX compilation, and DOCX conversion.

Note: Celery is optional. When not installed, tasks run synchronously.
"""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import Celery, provide stubs if not available
CELERY_AVAILABLE = False
celery_app = None
AsyncResult = None

try:
    from celery import Celery
    from celery.result import AsyncResult as CeleryAsyncResult
    from app.core.config import settings
    
    # Initialize Celery only if Redis URL is configured
    if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
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
            task_time_limit=300,
            task_soft_time_limit=240,
            worker_prefetch_multiplier=1,
            worker_concurrency=4,
        )
        CELERY_AVAILABLE = True
        AsyncResult = CeleryAsyncResult
        logger.info("Celery initialized with Redis backend")
    else:
        logger.info("Celery disabled: REDIS_URL not configured")
except ImportError:
    logger.info("Celery not installed - tasks run synchronously")
except Exception as e:
    logger.warning(f"Celery initialization failed: {e}")


def compile_pdf_task(latex_code: str, output_filename: str) -> Dict[str, Any]:
    """
    Compile LaTeX code to PDF.
    
    Args:
        latex_code: LaTeX source code
        output_filename: Output filename
        
    Returns:
        Compilation result with PDF path or error
    """
    from app.services.document_compiler import document_compiler
    
    try:
        pdf_path = document_compiler.compile_latex_to_pdf(latex_code, output_filename)
        
        if pdf_path:
            return {
                "success": True,
                "pdf_path": pdf_path,
                "filename": output_filename
            }
        return {
            "success": False,
            "error": "PDF compilation failed"
        }
    except Exception as e:
        logger.error(f"PDF compilation task failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def convert_docx_task(latex_code: str, output_filename: str) -> Dict[str, Any]:
    """
    Convert LaTeX to DOCX.
    
    Args:
        latex_code: LaTeX source code
        output_filename: Output filename
        
    Returns:
        Conversion result with DOCX path or error
    """
    from app.services.document_compiler import document_compiler
    
    try:
        docx_path = document_compiler.convert_latex_to_docx(latex_code, output_filename)
        
        if docx_path:
            return {
                "success": True,
                "docx_path": docx_path,
                "filename": output_filename
            }
        return {
            "success": False,
            "error": "DOCX conversion failed"
        }
    except Exception as e:
        logger.error(f"DOCX conversion task failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def analyze_ats_task(
    profile_dict: Dict[str, Any],
    job_description: str,
    keywords: list
) -> Dict[str, Any]:
    """
    Analyze ATS compatibility.
    
    Args:
        profile_dict: Profile data as dictionary
        job_description: Job description text
        keywords: List of keywords
        
    Returns:
        ATS analysis result
    """
    import asyncio
    from app.services.ats_engine import ats_engine
    from app.models.schemas import ProfileResponse
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        profile = ProfileResponse(**profile_dict)
        
        async def analyze():
            return await ats_engine.analyze_ats_compatibility(
                profile, job_description, keywords
            )
        
        result = loop.run_until_complete(analyze())
        
        return {
            "success": True,
            "analysis": result
        }
    except Exception as e:
        logger.error(f"ATS analysis task failed: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        loop.close()


def generate_cv_full_task(
    user_id: str,
    job_description: str
) -> Dict[str, Any]:
    """
    Full CV generation pipeline.
    
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


def cleanup_old_files_task(max_age_hours: int = 24) -> Dict[str, Any]:
    """
    Cleanup old generated files.
    
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


def get_task_status(task_id: str) -> Dict[str, Any]:
    """
    Get the status of a task.
    
    Args:
        task_id: Task ID
        
    Returns:
        Task status and result
    """
    if not CELERY_AVAILABLE or not AsyncResult:
        return {
            "task_id": task_id,
            "status": "SYNC_EXECUTION",
            "result": None,
            "ready": True,
            "successful": None,
            "message": "Tasks run synchronously - no status tracking available"
        }
    
    result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None,
        "ready": result.ready(),
        "successful": result.successful() if result.ready() else None
    }


# Configure periodic tasks only if Celery is available
if CELERY_AVAILABLE and celery_app:
    celery_app.conf.beat_schedule = {
        "cleanup-old-files": {
            "task": "tasks.cleanup_old_files",
            "schedule": 3600.0,  # Every hour
            "args": (24,)
        }
    }
