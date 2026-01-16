from pydantic import BaseModel

class CommitteeMember(BaseModel):
    member_id:str
    name: str
    role: str
    image_url:str
