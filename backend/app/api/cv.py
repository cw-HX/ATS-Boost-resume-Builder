"""
CV Generation API routes.
Handles JD processing, ATS optimization, and document generation.
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from fastapi.responses import Response
from bson import ObjectId
import logging

from app.core.database import get_profiles_collection, get_generated_cvs_collection
from app.core.dependencies import get_current_user_id
from app.core.config import settings
from app.models.schemas import (
    CVGenerationRequest,
    CVGenerationResponse,
    ProfileResponse,
    ATSAnalysis,
)
from app.services.llm_service import groq_service
from app.services.ats_engine import ats_engine
from app.services.latex_generator import latex_generator
from app.services.document_compiler import document_compiler

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cv", tags=["CV Generation"])


async def get_user_profile(user_id: str) -> ProfileResponse:
    """Fetch user profile from database."""
    profiles_collection = get_profiles_collection()
    profile = await profiles_collection.find_one({"user_id": user_id})
    
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found. Please create your profile first."
        )
    
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.post("/generate", response_model=CVGenerationResponse)
async def generate_cv(
    request: CVGenerationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Generate an ATS-optimized CV based on job description.
    
    This endpoint:
    1. Extracts keywords from the job description using LLM
    2. Analyzes profile against JD requirements
    3. Optimizes content for ATS compatibility
    4. Generates LaTeX code
    5. Ensures ATS score >= 90 (regenerates if needed)
    
    Args:
        request: Job description input
        user_id: Current user ID
        
    Returns:
        Generated CV with LaTeX code and ATS analysis
    """
    try:
        # Get user profile
        profile = await get_user_profile(user_id)
        
        # Extract keywords from JD using LLM
        logger.info(f"Extracting keywords for user {user_id}")
        jd_keywords = await groq_service.extract_keywords_from_jd(
            request.job_description
        )
        logger.info(f"Extracted JD keywords: {jd_keywords}")
        
        # Attempt to generate CV with ATS score >= 90
        best_result = None
        best_score = 0
        
        for attempt in range(settings.ATS_MAX_RETRIES):
            logger.info(f"CV generation attempt {attempt + 1} for user {user_id}")
            
            # Optimize profile for JD
            optimized_content = await ats_engine.optimize_profile_for_jd(
                profile=profile,
                job_description=request.job_description,
                jd_keywords=jd_keywords
            )
            logger.info(f"Optimized content generated with {len(optimized_content.get('injected_keywords', []))} injected keywords")
            
            # Generate LaTeX
            latex_code = latex_generator.generate_latex(
                profile=profile,
                optimized_content=optimized_content
            )
            
            # Analyze ATS compatibility using OPTIMIZED content
            ats_analysis = await ats_engine.analyze_ats_compatibility(
                profile=profile,
                job_description=request.job_description,
                jd_keywords=jd_keywords,
                optimized_content=optimized_content  # Pass optimized content for accurate scoring
            )
            
            current_score = ats_analysis["score"]
            logger.info(f"ATS score for attempt {attempt + 1}: {current_score}%")
            
            if current_score > best_score:
                best_score = current_score
                best_result = {
                    "latex_code": latex_code,
                    "ats_analysis": ats_analysis,
                    "optimized_content": optimized_content
                }
            
            if current_score >= settings.ATS_MIN_SCORE:
                logger.info(f"Achieved ATS score {current_score} for user {user_id}")
                break
            
            logger.info(f"ATS score {current_score} < {settings.ATS_MIN_SCORE}, retrying...")
        
        if not best_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate CV"
            )
        
        # Save generated CV to database
        cvs_collection = get_generated_cvs_collection()
        cv_doc = {
            "user_id": user_id,
            "job_description": request.job_description,
            "aligned_skills": best_result["ats_analysis"]["aligned_skills"],
            "ats_score": best_score,
            "latex_code": best_result["latex_code"],
            "created_at": datetime.utcnow()
        }
        
        result = await cvs_collection.insert_one(cv_doc)
        cv_doc["_id"] = str(result.inserted_id)
        
        return CVGenerationResponse(**cv_doc)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating CV: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating CV: {str(e)}"
        )


@router.post("/preview_optimized")
async def preview_optimized(
    request: CVGenerationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Return the raw `optimized_content` JSON for the given JD and current user.
    Use this to inspect exactly what the LLM produced before LaTeX generation.
    """
    try:
        profile = await get_user_profile(user_id)

        jd_keywords = await groq_service.extract_keywords_from_jd(request.job_description)

        optimized_content = await ats_engine.optimize_profile_for_jd(
            profile=profile,
            job_description=request.job_description,
            jd_keywords=jd_keywords
        )

        return optimized_content

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing optimized content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating preview: {str(e)}"
        )


@router.get("/analyze", response_model=ATSAnalysis)
async def analyze_ats_compatibility(
    job_description: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Analyze ATS compatibility without generating CV.
    
    Args:
        job_description: Job description text
        user_id: Current user ID
        
    Returns:
        ATS analysis results
    """
    try:
        profile = await get_user_profile(user_id)
        
        jd_keywords = await groq_service.extract_keywords_from_jd(job_description)
        
        analysis = await ats_engine.analyze_ats_compatibility(
            profile=profile,
            job_description=job_description,
            jd_keywords=jd_keywords
        )
        
        return ATSAnalysis(
            score=analysis["score"],
            keyword_match_percentage=analysis["keyword_match_percentage"],
            aligned_skills=analysis["aligned_skills"],
            missing_keywords=analysis["missing_keywords"],
            recommendations=analysis["recommendations"],
            bullet_analysis=analysis["bullet_analysis"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing ATS compatibility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing CV: {str(e)}"
        )


@router.get("/history", response_model=List[CVGenerationResponse])
async def get_cv_history(
    limit: int = 10,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get user's CV generation history.
    
    Args:
        limit: Maximum number of results
        user_id: Current user ID
        
    Returns:
        List of generated CVs
    """
    cvs_collection = get_generated_cvs_collection()
    
    cursor = cvs_collection.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit)
    
    results = []
    async for cv in cursor:
        cv["_id"] = str(cv["_id"])
        results.append(CVGenerationResponse(**cv))
    
    return results


@router.get("/{cv_id}", response_model=CVGenerationResponse)
async def get_cv(
    cv_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get a specific generated CV.
    
    Args:
        cv_id: CV document ID
        user_id: Current user ID
        
    Returns:
        Generated CV data
    """
    cvs_collection = get_generated_cvs_collection()
    
    cv = await cvs_collection.find_one({
        "_id": ObjectId(cv_id),
        "user_id": user_id
    })
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )
    
    cv["_id"] = str(cv["_id"])
    return CVGenerationResponse(**cv)


@router.get("/{cv_id}/latex")
async def get_cv_latex(
    cv_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Get LaTeX code for a generated CV.
    
    Args:
        cv_id: CV document ID
        user_id: Current user ID
        
    Returns:
        LaTeX code as plain text
    """
    cvs_collection = get_generated_cvs_collection()
    
    cv = await cvs_collection.find_one({
        "_id": ObjectId(cv_id),
        "user_id": user_id
    })
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )
    
    return Response(
        content=cv["latex_code"],
        media_type="text/plain"
    )


@router.post("/{cv_id}/compile-pdf")
async def compile_cv_to_pdf(
    cv_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Compile CV LaTeX to PDF.
    
    Args:
        cv_id: CV document ID
        user_id: Current user ID
        
    Returns:
        PDF compilation result with download path
    """
    cvs_collection = get_generated_cvs_collection()
    
    cv = await cvs_collection.find_one({
        "_id": ObjectId(cv_id),
        "user_id": user_id
    })
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )
    
    result = await document_compiler.compile_latex_to_pdf(
        latex_code=cv["latex_code"],
        output_filename="cv"
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF compilation failed: {result.error_message}"
        )
    
    return {
        "success": True,
        "pdf_path": result.pdf_path,
        "message": "PDF compiled successfully"
    }


@router.get("/{cv_id}/download-pdf")
async def download_cv_pdf(
    cv_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Download CV as PDF.
    
    Args:
        cv_id: CV document ID
        user_id: Current user ID
        
    Returns:
        PDF file download
    """
    cvs_collection = get_generated_cvs_collection()
    
    cv = await cvs_collection.find_one({
        "_id": ObjectId(cv_id),
        "user_id": user_id
    })
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )
    
    # Compile PDF
    result = await document_compiler.compile_latex_to_pdf(
        latex_code=cv["latex_code"],
        output_filename="cv"
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF compilation failed: {result.error_message}"
        )
    
    # Read PDF content
    pdf_content = document_compiler.read_pdf(result.pdf_path)
    
    if not pdf_content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read PDF file"
        )
    
    return Response(
        content=pdf_content,
        media_type="application/pdf",
        headers={
            "Content-Disposition": "attachment; filename=cv.pdf"
        }
    )


@router.post("/{cv_id}/convert-docx")
async def convert_cv_to_docx(
    cv_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Convert CV LaTeX to DOCX.
    
    Args:
        cv_id: CV document ID
        user_id: Current user ID
        
    Returns:
        DOCX conversion result with download path
    """
    cvs_collection = get_generated_cvs_collection()
    
    cv = await cvs_collection.find_one({
        "_id": ObjectId(cv_id),
        "user_id": user_id
    })
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )
    
    result = await document_compiler.convert_latex_to_docx(
        latex_code=cv["latex_code"],
        output_filename="cv"
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DOCX conversion failed: {result.error_message}"
        )
    
    return {
        "success": True,
        "docx_path": result.docx_path,
        "message": "DOCX converted successfully"
    }


@router.get("/{cv_id}/download-docx")
async def download_cv_docx(
    cv_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Download CV as DOCX.
    
    Args:
        cv_id: CV document ID
        user_id: Current user ID
        
    Returns:
        DOCX file download
    """
    cvs_collection = get_generated_cvs_collection()
    
    cv = await cvs_collection.find_one({
        "_id": ObjectId(cv_id),
        "user_id": user_id
    })
    
    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )
    
    # Convert to DOCX
    result = await document_compiler.convert_latex_to_docx(
        latex_code=cv["latex_code"],
        output_filename="cv"
    )
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DOCX conversion failed: {result.error_message}"
        )
    
    # Read DOCX content
    docx_content = document_compiler.read_docx(result.docx_path)
    
    if not docx_content:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to read DOCX file"
        )
    
    return Response(
        content=docx_content,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": "attachment; filename=cv.docx"
        }
    )


@router.delete("/{cv_id}")
async def delete_cv(
    cv_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """
    Delete a generated CV.
    
    Args:
        cv_id: CV document ID
        user_id: Current user ID
        
    Returns:
        Deletion confirmation
    """
    cvs_collection = get_generated_cvs_collection()
    
    result = await cvs_collection.delete_one({
        "_id": ObjectId(cv_id),
        "user_id": user_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="CV not found"
        )
    
    return {"message": "CV deleted successfully"}
