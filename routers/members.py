import os
import cloudinary.uploader
from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import ValidationError
from dotenv import load_dotenv
from database import initialize_db
from schemas.members import CommitteeMember 

load_dotenv()
db = initialize_db()


cloudinary.config( 
    cloud_name = "dcmoyti3h", 
    api_key = "391379798551432", 
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

committee_router = APIRouter()


@committee_router.post("/admin/committee/create", response_model=CommitteeMember)
async def create_member(
    member_id: str = Form(...),
    name: str = Form(...),
    role: str = Form(...),
    profile_pic: UploadFile = File(...) 
):
    try:
        upload_result = cloudinary.uploader.upload(profile_pic.file)
        secure_url = upload_result.get("secure_url")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")
    
    try:
        member_data = CommitteeMember(
            member_id=member_id,
            name=name,
            role=role,
            image_url=secure_url
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    await db.committee.insert_one(member_data.model_dump())
    return member_data


@committee_router.get("/committee/all", response_model=List[CommitteeMember])
async def get_all_members():
    members = await db.committee.find().to_list(100)
    return members


@committee_router.get("/committee/{member_id}", response_model=CommitteeMember)
async def get_member(member_id: str):
    member = await db.committee.find_one({"member_id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    return member

@committee_router.delete("/admin/committee/delete/{member_id}")
async def delete_member(member_id: str):
    result = await db.committee.delete_one({"member_id": member_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    return {"message": "Committee member removed successfully"}

@committee_router.patch("/admin/committee/update/{member_id}", response_model=CommitteeMember)
async def update_member(
    member_id: str,
    name: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    profile_pic: Optional[UploadFile] = File(None)
):
    existing_member = await db.committee.find_one({"member_id": member_id})
    if not existing_member:
        raise HTTPException(status_code=404, detail="Member not found")

    update_data = {}
    if name: update_data["name"] = name
    if role: update_data["role"] = role
    
    if profile_pic:
        try:
            upload_result = cloudinary.uploader.upload(profile_pic.file)
            update_data["image_url"] = upload_result.get("secure_url")
        except Exception as e:
            raise HTTPException(status_code=500, detail="Image upload failed")

    if update_data:
        await db.committee.update_one({"member_id": member_id}, {"$set": update_data})
    
    updated_member = await db.committee.find_one({"member_id": member_id})
    return updated_member