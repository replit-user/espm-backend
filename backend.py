import fastapi
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import zipfile

modules = {}

app = fastapi.FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/upload")
async def upload_module(
    stack: fastapi.UploadFile = fastapi.File(...),
    stackm: fastapi.UploadFile = fastapi.File(...),
    name: str = fastapi.Form(...),
    version: str = fastapi.Form(...),
):
    """
    Upload a module to the server. Each module name must be unique.
    """
    if name in modules:
        return JSONResponse({"error": "Module already exists"}, status_code=400)
    
    stack_content = await stack.read()
    stackm_content = await stackm.read()
    
    modules[name] = {
        version: {
            "stack": stack_content,
            "stackm": stackm_content
        }
    }
    return JSONResponse({"message": "Module uploaded successfully"})


@app.get("/download/{name}/{version}")
def download_module(name: str, version: str):
    """
    Download a module's files as a ZIP archive.
    """
    if name not in modules or version not in modules[name]:
        return JSONResponse({"error": "Module not found"}, status_code=404)
    if not version == "latest":
    
        module_files = modules[name][version]
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(f"{name}.stack", module_files["stack"])
            zip_file.writestr(f"{name}.stackm", module_files["stackm"])
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={name}_{version}.zip"}
        )
    else:
        versions = []
        for ver in modules[name]:
            versions.append(ver)
        latest_version = max(versions, key=lambda x: tuple(map(int, x.split('.'))))
        module_files = modules[name][latest_version]
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(f"{name}.stack", module_files["stack"])
            zip_file.writestr(f"{name}.stackm", module_files["stackm"])
        
        zip_buffer.seek(0)
        
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={name}_{latest_version}.zip"}
        )


@app.post("/update/{name}/{version}")
async def update_module(
    name: str,
    version: str,
    stack: fastapi.UploadFile = fastapi.File(...),
    stackm: fastapi.UploadFile = fastapi.File(...),
):
    """
    Add a new version to an existing module.
    """
    if name not in modules:
        return JSONResponse({"error": "Module not found"}, status_code=404)
    if version in modules[name]:
        return JSONResponse({"error": "Version already exists"}, status_code=400)
    
    stack_content = await stack.read()
    stackm_content = await stackm.read()
    
    modules[name][version] = {
        "stack": stack_content,
        "stackm": stackm_content
    }
    return JSONResponse({"message": "Module version added successfully"})
