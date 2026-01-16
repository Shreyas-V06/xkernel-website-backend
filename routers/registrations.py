import uuid
import io
import csv
import cloudinary.uploader
from fastapi import APIRouter, Form, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import List, Optional
from dotenv import load_dotenv
from database import initialize_db

load_dotenv()
db = initialize_db()

registration_router = APIRouter()

@registration_router.post("/register/{event_id}", response_model=dict)
async def register_student(
    event_id: str, 
    student_name: str = Form(...),
    student_roll_no: str = Form(...),      
    student_year: str = Form(...),
    student_department: str = Form(...),
    student_section: str = Form(...),       
    quantity: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    transaction_id: str = Form(...),       
    payment_ss: UploadFile = File(...)
):
    event = await db.events.find_one({"event_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    try:
        upload_result = cloudinary.uploader.upload(payment_ss.file)
        ss_url = upload_result.get("secure_url")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Screenshot upload failed: {str(e)}")

    ticket_id = f"XKT{uuid.uuid4().hex[:8].upper()}"

    registration_data = {
        "event_id": event_id,
        "student_name": student_name,
        "student_roll_no": student_roll_no,
        "student_year": student_year,
        "student_department": student_department,
        "student_section": student_section,
        "quantity": quantity,
        "email": email,
        "phone": phone,
        "transaction_id": transaction_id,
        "payment_ss_url": ss_url,
        "ticket_id": ticket_id
    }

    await db.registrations.insert_one(registration_data)

    return {
        "message": "Registration Successful",
        "ticket_id": ticket_id,
        "event_title": event.get("title")
    }


@registration_router.patch("/admin/registration/update/{ticket_id}", response_model=dict)
async def update_registration(
    ticket_id: str,
    student_name: Optional[str] = Form(None),
    student_roll_no: Optional[str] = Form(None),
    student_year: Optional[str] = Form(None),
    student_department: Optional[str] = Form(None),
    student_section: Optional[str] = Form(None),
    quantity: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    phone: Optional[str] = Form(None),
    transaction_id: Optional[str] = Form(None),
    payment_ss: Optional[UploadFile] = File(None)
):
    existing_reg = await db.registrations.find_one({"ticket_id": ticket_id})
    if not existing_reg:
        raise HTTPException(status_code=404, detail="Ticket ID not found")

    update_data = {}

    fields = [
        "student_name", "student_roll_no", "student_year", 
        "student_department", "student_section", "quantity", 
        "email", "phone", "transaction_id"
    ]
    
    for field in fields:
        val = locals().get(field)
        if val is not None: 
            update_data[field] = val

    if payment_ss:
        try:
            upload_result = cloudinary.uploader.upload(payment_ss.file)
            update_data["payment_ss_url"] = upload_result.get("secure_url")
        except Exception:
            raise HTTPException(status_code=500, detail="Screenshot update failed")

    if not update_data:
        return {"message": "No changes provided"}

    await db.registrations.update_one({"ticket_id": ticket_id}, {"$set": update_data})
    return {"message": f"Registration {ticket_id} updated successfully"}

@registration_router.delete("/admin/registration/delete/{ticket_id}")
async def delete_registration(ticket_id: str):
    result = await db.registrations.delete_one({"ticket_id": ticket_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ticket ID not found")
    return {"message": f"Ticket {ticket_id} deleted successfully"}

@registration_router.get("/admin/registrations/{event_id}", response_model=List[dict])
async def get_event_registrations(event_id: str):
    registrations = await db.registrations.find({"event_id": event_id}).to_list(1000)
    for reg in registrations:
        reg["_id"] = str(reg["_id"])
    return registrations

@registration_router.get("/admin/export/{event_id}/csv")
async def export_registrations_csv(event_id: str):
    registrations = await db.registrations.find({"event_id": event_id}).to_list(1000)
    
    if not registrations:
        raise HTTPException(status_code=404, detail="No registrations found for this event")

    output = io.StringIO()
    writer = csv.writer(output)

    header = [
        "Ticket ID", "Student Name", "Roll No", "Email", "Phone", 
        "Department", "Year", "Section", "Quantity", "Transaction ID", "Payment URL"
    ]
    writer.writerow(header)

    for reg in registrations:
        writer.writerow([
            reg.get("ticket_id"),
            reg.get("student_name"),
            reg.get("student_roll_no"),
            reg.get("email"),
            reg.get("phone"),
            reg.get("student_department"),
            reg.get("student_year"),
            reg.get("student_section"),
            reg.get("quantity"),
            reg.get("transaction_id"),
            reg.get("payment_ss_url")
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=registrations_{event_id}.csv"}
    )