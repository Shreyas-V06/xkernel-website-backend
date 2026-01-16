import cloudinary.uploader
from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from typing import List, Optional
from pydantic import ValidationError
from schemas.events import EventInformation
from dotenv import load_dotenv
from database import initialize_db
import os
import uuid

load_dotenv()
db = initialize_db()

cloudinary.config( 
    cloud_name = "dcmoyti3h", 
    api_key = "391379798551432", 
    api_secret = os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

event_router = APIRouter()

@event_router.post("/admin/event/create", response_model=EventInformation)
async def create_event(
    title: str = Form(...),
    description: str = Form(...),
    schedule: str = Form(...),
    venue: str = Form(...),
    status: str = Form(...), 
    contact_details: str = Form(...), 
    poster: UploadFile = File(...) 
):
    generated_id = f"XKLEVT{uuid.uuid4().hex[:8].upper()}"

    try:
        upload_result = cloudinary.uploader.upload(poster.file)
        secure_url = upload_result.get("secure_url")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")
    
    try:
        event_data = EventInformation(
            event_id=generated_id,
            title=title,
            description=description,
            schedule=schedule,
            venue=venue,
            image_url=secure_url,
            status=status,
            contact_details=contact_details
        )
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())

    await db.events.insert_one(event_data.model_dump())
    return event_data

@event_router.get("/events/all", response_model=List[EventInformation])
async def get_all_events():
    
    events = await db.events.find().to_list(100)
    return events

@event_router.get("/event/{event_id}", response_model=EventInformation)
async def get_event(event_id: str):
    
    event = await db.events.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@event_router.delete("/admin/event/delete/{event_id}")
async def delete_event(event_id: str):

    result = await db.events.delete_one({"event_id": event_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"message": "Event deleted successfully"}

@event_router.patch("/event/update/{event_id}", response_model=EventInformation)
async def update_event(
    event_id: str,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    schedule: Optional[str] = Form(None),
    venue: Optional[str] = Form(None),
    status: Optional[str] = Form(None),
    contact_details: Optional[str] = Form(None),
    poster: Optional[UploadFile] = File(None)
):

    existing_event = await db.events.find_one({"event_id": event_id})
    if not existing_event:
        raise HTTPException(status_code=404, detail="Event not found")

    update_data = {}
    if title: update_data["title"] = title
    if description: update_data["description"] = description
    if schedule: update_data["schedule"] = schedule
    if venue: update_data["venue"] = venue
    if status: update_data["status"] = status
    if contact_details: update_data["contact_details"] = contact_details
    
    if poster:
        try:
            upload_result = cloudinary.uploader.upload(poster.file)
            update_data["image_url"] = upload_result.get("secure_url")
        except Exception:
            raise HTTPException(status_code=500, detail="Image upload failed")

    if update_data:
        await db.events.update_one({"event_id": event_id}, {"$set": update_data})
    
    updated_event = await db.events.find_one({"event_id": event_id})
    return updated_event