from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.events import event_router
from routers.members import committee_router
from routers.registrations import registration_router


app=FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"], 
    expose_headers=["Content-Type"], 
)
app.include_router(event_router)
app.include_router(committee_router)
app.include_router(registration_router)
