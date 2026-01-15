"""
Profile management API routes.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends
from bson import ObjectId

from app.core.database import get_profiles_collection
from app.core.dependencies import get_current_user_id
from app.models.schemas import (
    ProfileCreate,
    ProfileUpdate,
    ProfileResponse,
    PersonalDetails,
    Education,
    Skills,
    Project,
    Internship,
    Certification,
)

router = APIRouter(prefix="/profile", tags=["Profile Management"])


@router.post("/", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: ProfileCreate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Create a new user profile.
    
    Args:
        profile_data: Profile data
        user_id: Current user ID
        
    Returns:
        Created profile
    """
    profiles_collection = get_profiles_collection()
    
    # Check if profile already exists
    existing_profile = await profiles_collection.find_one({"user_id": user_id})
    if existing_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile already exists. Use PUT to update."
        )
    
    # Create profile document
    profile_doc = {
        "user_id": user_id,
        "personal_details": profile_data.personal_details.model_dump(),
        "education": [edu.model_dump() for edu in profile_data.education],
        "skills": profile_data.skills.model_dump(),
        "projects": [proj.model_dump() for proj in profile_data.projects],
        "internships": [intern.model_dump() for intern in profile_data.internships],
        "certifications": [cert.model_dump() for cert in profile_data.certifications],
        "achievements": profile_data.achievements,
        "updated_at": datetime.utcnow()
    }
    
    result = await profiles_collection.insert_one(profile_doc)
    profile_doc["_id"] = str(result.inserted_id)
    
    return ProfileResponse(**profile_doc)


@router.get("/", response_model=ProfileResponse)
async def get_profile(user_id: str = Depends(get_current_user_id)):
    """
    Get current user's profile.
    
    Args:
        user_id: Current user ID
        
    Returns:
        User profile
    """
    profiles_collection = get_profiles_collection()
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.put("/", response_model=ProfileResponse)
async def update_profile(
    profile_data: ProfileUpdate,
    user_id: str = Depends(get_current_user_id)
):
    """
    Update current user's profile.
    
    Args:
        profile_data: Updated profile data
        user_id: Current user ID
        
    Returns:
        Updated profile
    """
    profiles_collection = get_profiles_collection()
    
    # Build update document
    update_doc = {"updated_at": datetime.utcnow()}
    
    if profile_data.personal_details:
        update_doc["personal_details"] = profile_data.personal_details.model_dump()
    if profile_data.education is not None:
        update_doc["education"] = [edu.model_dump() for edu in profile_data.education]
    if profile_data.skills:
        update_doc["skills"] = profile_data.skills.model_dump()
    if profile_data.projects is not None:
        update_doc["projects"] = [proj.model_dump() for proj in profile_data.projects]
    if profile_data.internships is not None:
        update_doc["internships"] = [intern.model_dump() for intern in profile_data.internships]
    if profile_data.certifications is not None:
        update_doc["certifications"] = [cert.model_dump() for cert in profile_data.certifications]
    if profile_data.achievements is not None:
        update_doc["achievements"] = profile_data.achievements
    
    # Update profile
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {"$set": update_doc}
    )
    
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found"
        )
    
    # Return updated profile
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


# ============== Education Endpoints ==============

@router.post("/education", response_model=ProfileResponse)
async def add_education(
    education: Education,
    user_id: str = Depends(get_current_user_id)
):
    """Add a new education entry."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$push": {"education": education.model_dump()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.put("/education/{index}", response_model=ProfileResponse)
async def update_education(
    index: int,
    education: Education,
    user_id: str = Depends(get_current_user_id)
):
    """Update an education entry by index."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                f"education.{index}": education.model_dump(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.delete("/education/{index}", response_model=ProfileResponse)
async def delete_education(
    index: int,
    user_id: str = Depends(get_current_user_id)
):
    """Delete an education entry by index."""
    profiles_collection = get_profiles_collection()
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    education_list = profile.get("education", [])
    if index < 0 or index >= len(education_list):
        raise HTTPException(status_code=400, detail="Invalid index")
    
    education_list.pop(index)
    
    await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "education": education_list,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


# ============== Skills Endpoints ==============

@router.put("/skills", response_model=ProfileResponse)
async def update_skills(
    skills: Skills,
    user_id: str = Depends(get_current_user_id)
):
    """Update skills section."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "skills": skills.model_dump(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


# ============== Projects Endpoints ==============

@router.post("/projects", response_model=ProfileResponse)
async def add_project(
    project: Project,
    user_id: str = Depends(get_current_user_id)
):
    """Add a new project entry."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$push": {"projects": project.model_dump()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.put("/projects/{index}", response_model=ProfileResponse)
async def update_project(
    index: int,
    project: Project,
    user_id: str = Depends(get_current_user_id)
):
    """Update a project entry by index."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                f"projects.{index}": project.model_dump(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.delete("/projects/{index}", response_model=ProfileResponse)
async def delete_project(
    index: int,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a project entry by index."""
    profiles_collection = get_profiles_collection()
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    projects_list = profile.get("projects", [])
    if index < 0 or index >= len(projects_list):
        raise HTTPException(status_code=400, detail="Invalid index")
    
    projects_list.pop(index)
    
    await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "projects": projects_list,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


# ============== Internships Endpoints ==============

@router.post("/internships", response_model=ProfileResponse)
async def add_internship(
    internship: Internship,
    user_id: str = Depends(get_current_user_id)
):
    """Add a new internship entry."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$push": {"internships": internship.model_dump()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.put("/internships/{index}", response_model=ProfileResponse)
async def update_internship(
    index: int,
    internship: Internship,
    user_id: str = Depends(get_current_user_id)
):
    """Update an internship entry by index."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                f"internships.{index}": internship.model_dump(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.delete("/internships/{index}", response_model=ProfileResponse)
async def delete_internship(
    index: int,
    user_id: str = Depends(get_current_user_id)
):
    """Delete an internship entry by index."""
    profiles_collection = get_profiles_collection()
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    internships_list = profile.get("internships", [])
    if index < 0 or index >= len(internships_list):
        raise HTTPException(status_code=400, detail="Invalid index")
    
    internships_list.pop(index)
    
    await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "internships": internships_list,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


# ============== Certifications Endpoints ==============

@router.post("/certifications", response_model=ProfileResponse)
async def add_certification(
    certification: Certification,
    user_id: str = Depends(get_current_user_id)
):
    """Add a new certification entry."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$push": {"certifications": certification.model_dump()},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.put("/certifications/{index}", response_model=ProfileResponse)
async def update_certification(
    index: int,
    certification: Certification,
    user_id: str = Depends(get_current_user_id)
):
    """Update a certification entry by index."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                f"certifications.{index}": certification.model_dump(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.delete("/certifications/{index}", response_model=ProfileResponse)
async def delete_certification(
    index: int,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a certification entry by index."""
    profiles_collection = get_profiles_collection()
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    certifications_list = profile.get("certifications", [])
    if index < 0 or index >= len(certifications_list):
        raise HTTPException(status_code=400, detail="Invalid index")
    
    certifications_list.pop(index)
    
    await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "certifications": certifications_list,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


# ============== Achievements Endpoints ==============

@router.post("/achievements", response_model=ProfileResponse)
async def add_achievement(
    achievement: str,
    user_id: str = Depends(get_current_user_id)
):
    """Add a new achievement."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$push": {"achievements": achievement},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.put("/achievements/{index}", response_model=ProfileResponse)
async def update_achievement(
    index: int,
    achievement: str,
    user_id: str = Depends(get_current_user_id)
):
    """Update an achievement by index."""
    profiles_collection = get_profiles_collection()
    
    result = await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                f"achievements.{index}": achievement,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)


@router.delete("/achievements/{index}", response_model=ProfileResponse)
async def delete_achievement(
    index: int,
    user_id: str = Depends(get_current_user_id)
):
    """Delete an achievement by index."""
    profiles_collection = get_profiles_collection()
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    achievements_list = profile.get("achievements", [])
    if index < 0 or index >= len(achievements_list):
        raise HTTPException(status_code=400, detail="Invalid index")
    
    achievements_list.pop(index)
    
    await profiles_collection.update_one(
        {"user_id": user_id},
        {
            "$set": {
                "achievements": achievements_list,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    profile = await profiles_collection.find_one({"user_id": user_id})
    profile["_id"] = str(profile["_id"])
    return ProfileResponse(**profile)
