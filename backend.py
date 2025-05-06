from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import zipfile

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

modules = {}

@app.post("/upload")
async def upload_module(
    stack: UploadFile = File(...),
    stackm: UploadFile = File(...),
    name: str = Form(...),
    version: str = Form(...),
):
    if name in modules:
        raise HTTPException(status_code=400, detail="Module already exists")
    stack_content = await stack.read()
    stackm_content = await stackm.read()
    modules[name] = {version: {"stack": stack_content, "stackm": stackm_content}}
    return {"message": "Module uploaded successfully"}

@app.get("/download/{name}/{version}")
async def download_module(name: str, version: str):
    if name not in modules:
        raise HTTPException(status_code=404, detail="Module not found")
    available_versions = modules[name]
    if version == "latest":
        sorted_versions = sorted(available_versions.keys(), key=lambda v: tuple(map(int, v.split('.'))), reverse=True)
        if not sorted_versions:
            raise HTTPException(status_code=404, detail="No versions available")
        selected_version = sorted_versions[0]
    else:
        if version not in available_versions:
            raise HTTPException(status_code=404, detail="Version not found")
        selected_version = version
    module_data = available_versions[selected_version]
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr(f"{name}.stack", module_data["stack"])
        zip_file.writestr(f"{name}.stackm", module_data["stackm"])
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{name}_{selected_version}.zip"'}
    )

@app.post("/update/{name}/{version}")
async def update_module(
    name: str,
    version: str,
    stack: UploadFile = File(...),
    stackm: UploadFile = File(...),
):
    if name not in modules:
        raise HTTPException(status_code=404, detail="Module not found")
    if version in modules[name]:
        raise HTTPException(status_code=400, detail="Version already exists")
    stack_content = await stack.read()
    stackm_content = await stackm.read()
    modules[name][version] = {"stack": stack_content, "stackm": stackm_content}
    return {"message": "Module version added successfully"}

@app.get("/modules")
async def list_modules():
    simplified_modules = {name: list(versions.keys()) for name, versions in modules.items()}
    return JSONResponse(content=simplified_modules)
