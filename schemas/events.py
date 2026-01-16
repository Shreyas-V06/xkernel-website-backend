from pydantic import BaseModel
from typing import Literal,Optional


class EventInformation(BaseModel):
    event_id:str
    title: str
    description: str
    schedule: str 
    venue: str
    contact_details: str
    image_url: str 
    status: Optional[Literal["Live", "Upcoming", "Expired"]] = None

