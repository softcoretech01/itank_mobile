# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.utils import get_openapi
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
import json
import logging
import os

# Database initialization
from app.database import init_db, engine, SessionLocal
from app.seed import init_seed_data

# Import all routers
from app.routers import (
    tank_details, regulations_master,
    cargo_master, cargo_tank,
    tank_certificate, tank_drawings,
    valve_test_report, ppt_router,
    tank_image_router, tank_inspection_router, auth_router,
    validation_router, to_do_list_router, tank_checklist_router,
    tank_valve_router, tank_gauge_router,
    tank_valve_and_shell_router, other_images_router,
    tank_code_master_router
)
from app.routers.tank_checkpoints_router import router as tank_checkpoints_router
from app.routers import master_router

logger = logging.getLogger("uvicorn.error")

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title="ISO Tank API",
    docs_url="/docs",           # keep default, easier locally
    openapi_url="/openapi.json",
    root_path="/iti-web",       # this is the prefix used in UAT
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "https://uat.spairyx.com/iti",
        "https://www.uat.spairyx.com/iti"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)




# Uniform response middleware
class UniformResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)

            # Don't wrap docs, openapi, static files, uploads, or streaming responses
            path = request.url.path
            if path.startswith("/docs") or path.startswith("/redoc") or path.startswith("/openapi") or path.startswith("/static") or path.startswith("/uploads"):
                return response

            # Skip wrapping for streaming or file responses
            content_type = response.headers.get("content-type", "")
            if "application/json" not in content_type:
                return response

            # Check if response is a streaming response
            if hasattr(response, "body_iterator") and response.body_iterator is not None:
                return response

            # For JSONResponse objects, we can safely access .body
            try:
                body_bytes = getattr(response, "body", None)
                if body_bytes is None:
                    return response
                body = json.loads(body_bytes.decode())
            except Exception:
                return response

            # If already in uniform format, return as-is
            if isinstance(body, dict) and set(("success", "message", "data")).issubset(body.keys()):
                return response

            # Wrap the original body as data
            wrapped = {"success": True, "message": "Operation successful", "data": body if body is not None else {}}
            return JSONResponse(content=wrapped, status_code=response.status_code)

        except Exception as exc:
            import traceback
            traceback.print_exc()
            logger.exception("Error in UniformResponseMiddleware")
            return JSONResponse(content={"success": False, "message": f"Internal server error: {str(exc)}", "data": {}}, status_code=500)


# Attach middleware
app.add_middleware(UniformResponseMiddleware)


# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(content={"success": False, "message": msg or "Error", "data": {}}, status_code=exc.status_code)


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(content={"success": False, "message": "Internal server error", "data": {}}, status_code=500)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    try:
        errors = jsonable_encoder(exc.errors())
        msg = "Request validation error"
    except Exception:
        errors = None
        msg = "Request validation error"
    return JSONResponse(content={"success": False, "message": msg, "data": {"errors": errors or {}}}, status_code=422)


# Include all routers
app.include_router(auth_router.router)
app.include_router(tank_details.router, prefix="/api/tanks", tags=["Tanks"])
app.include_router(tank_inspection_router.router)
app.include_router(tank_certificate.router, prefix="/api/tank-certificates", tags=["Tank Certificates"])
# Reload trigger 2
app.include_router(regulations_master.router, prefix="/api/regulations-master", tags=["Regulations Master"])
app.include_router(cargo_master.router, prefix="/api/cargo-master", tags=["Cargo Master"])
app.include_router(cargo_tank.router, prefix="/api/cargo-tank", tags=["Cargo Tank"])
app.include_router(tank_drawings.router, prefix="/api/tank-drawings", tags=["Tank Drawings"])
app.include_router(tank_valve_router.router, prefix="/api/tank-valves", tags=["Tank Valves"])
app.include_router(tank_gauge_router.router, prefix="/api/tank-gauges", tags=["Tank Gauges"])
app.include_router(tank_valve_and_shell_router.router, prefix="/api/tank-valve-and-shell", tags=["Tank Valve And Shell"])
app.include_router(other_images_router.router, prefix="/api/other-images", tags=["Other Images"])
app.include_router(valve_test_report.router, prefix="/api/valve-test-reports", tags=["Valve Test Reports"])
app.include_router(ppt_router.router, prefix="/api/ppt", tags=["PPT Generation"])
app.include_router(tank_image_router.router)
app.include_router(tank_checkpoints_router)
app.include_router(to_do_list_router.router)
app.include_router(tank_checklist_router.router)
app.include_router(validation_router.router)
app.include_router(master_router.router)
app.include_router(tank_code_master_router.router)
# Serve uploaded images statically
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")  # TODO: New files are served via S3/CloudFront; this mount is for legacy local uploads only


# Startup event
@app.on_event("startup")
def on_startup():
    # 1. Initialize standard tables
    init_db()
    

    # 3. SEEDING: Insert initial values for Master tables
    db = SessionLocal()
    try:
        print("Checking for seed data...")
        init_seed_data(db)
        print("Seeding check completed.")
    except Exception as e:
        print(f"Error during seeding: {e}")
    finally:
        db.close()


# Root endpoints
@app.get("/")
def root():
    return {"message": "ISO Tank API is running"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}


# Custom OpenAPI (Bearer Auth)
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=getattr(app, "description", None),
        routes=app.routes,
    )
    openapi_schema["servers"] = [
    {"url": "/iti-web"}      # in UAT this becomes https://uat.spairyx.com/iti-web
    ]
    # Add Bearer auth security scheme
    openapi_schema.setdefault("components", {}).setdefault("securitySchemes", {})
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }

    # Optionally require it globally
    for path, path_item in openapi_schema.get("paths", {}).items():
        for method, operation in path_item.items():
            if not isinstance(operation, dict):
                continue
            security = operation.setdefault("security", [])
            if {"BearerAuth": []} not in security:
                security.append({"BearerAuth": []})

    app.openapi_schema = openapi_schema
    return app.openapi_schema


# Attach custom openapi
app.openapi = custom_openapi
