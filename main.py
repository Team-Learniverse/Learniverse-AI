import uvicorn
import os
import pandas as pd
from fastapi import FastAPI 
from fastapi.middleware.cors import CORSMiddleware
from routers import test

app = FastAPI()
app.include_router(test.router)

#CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,  
    allow_methods=["*"],  
    allow_headers=["*"],  
)

@app.get("/")
def root():
    return {"message": "Hello, Learni AI!!"}




