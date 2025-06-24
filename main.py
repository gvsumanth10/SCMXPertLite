from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
# Import routers
from routes.user_routes import user_router as user_router
from routes.shipment_routes import router as shipment_router
from routes.device_routes import router as device_router

# Load .env variables
load_dotenv()

app = FastAPI(title="SCMXPertLite-EXF Backend API")

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, set frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(user_router, prefix="/api", tags=["Users"])
app.include_router(shipment_router, prefix="/api", tags=["Shipments"])
app.include_router(device_router, prefix='/api', tags=['Devices'])
# app.include_router(device_router, prefix="/api", tags=["Devices"])  # Optional

# Root route (for sanity check)
# @app.get("/")
# def root():
#     return {"msg": "🚀 EXF FastAPI backend is running"}


# Serve static HTML (frontend)
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")


# Serve index.html at root
@app.get("/", include_in_schema=False)
async def serve_signup():
    return FileResponse("frontend/signup.html")

@app.get("/login", include_in_schema=False)
async def serve_login():
    return FileResponse("frontend/login.html")


@app.get("/dashboard", include_in_schema=False)
async def serve_dashboard():
    return FileResponse("frontend/dashboard.html")

@app.get("/create-shipment", include_in_schema=False)
async def serve_create_shipment():
    return FileResponse("frontend/create-shipment.html")

@app.get("/shipments", include_in_schema=False)
async def serve_shipments():
    return FileResponse("frontend/shipments.html")

@app.get("/my-shipments", include_in_schema=False)
async def serve_my_shipments():
    return FileResponse("frontend/my-shipments.html")


@app.get("/manage-users", include_in_schema=False)
async def serve_manage_users():
    return FileResponse("frontend/manage-users.html")

@app.get("/account", include_in_schema=False)
async def serve_account():
    return FileResponse("frontend/account.html")

@app.get("/device-data", include_in_schema=False)
async def serve_device_data():
    return FileResponse("frontend/device-data.html")


