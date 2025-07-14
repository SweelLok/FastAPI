import pathlib
import uvicorn
import httpx
import pytest

from fastapi import (FastAPI, File, Form, UploadFile, 
										 BackgroundTasks, HTTPException, status)
from PIL import Image 
from io import BytesIO


MAX_IMAGE_SIZE = 1024 * 1024 * 10  # 10Mb
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png"}
module_path = pathlib.Path(__file__).parent
app = FastAPI()

async def resize_image(img: bytes, fmt: str, size: tuple[int, int]) -> None:
    """Зміна розміру зображення та конвертація його в чорно-білий колір."""
    image = Image.open(BytesIO(img))
    image = image.convert("RGB").convert("L")
    resized_image = image.resize(size)
    save_path = module_path / f"resized_image_{size[0]}x{size[1]}.{fmt}"
    resized_image.save(save_path)
    print(f"Image saved to: {save_path}")


@app.post("/login/")
async def login(
	username: str = Form(examples=["ukr.vadya@gmail.com"]),
	password: str = Form(examples=["12345678"])
):
	return {"username": username, "password": password}

@app.post("/upload_file/")
async def upload_file(
	file: bytes = File(default=None)):
	with open(module_path / "uploaded_file", mode="wb") as f:
		f.write(file)

	return {"file_size": len(file)}

@app.post("/upload_file2/")
async def upload_file2(file: UploadFile | None = None):
	if file is not None:
		with open(module_path / file.filename, mode="wb") as f2:
			f2.write(await file.read())
			print({"filename": file.filename, "file_size": file.size})

		return {
			"headers": file.headers,
			"file_size": file.size,
			"filename": file.filename
		}
	
	return {"error": "No file uploaded"}

@app.post("/upload_file3/")
async def upload_file3(images: list[UploadFile], desciption: str = Form(...)):
	images_filename = []

	for image in images:
		with open(module_path / image.filename, mode="wb") as f3:
			f3.write(await image.read())
			images_filename.append(image.filename)

	return {"description": desciption, "images": images_filename}

@app.post("/check_file/", status_code=200)
async def check_file(
	bg_tasks: BackgroundTasks, 
	file: UploadFile = File(...),
	width: int = 300,
	height: int = 300
	):
	if file.size > MAX_IMAGE_SIZE:
		raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File size exceeds 10Mb")
	
	if file.content_type not in ALLOWED_IMAGE_TYPES:
		raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Unsupported file type")
	
	bg_tasks.add_task(resize_image, 
									 img=await file.read(), 
									 fmt=file.filename.split(".")[-1],
									 size=(width, height)),

	return {
		"filename": file.filename,
		"size": file.size,
	}

@pytest.mark.asyncio
async def test_upload_file():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://127.0.0.1:8080"
    ) as client:
        with open(module_path / "test.jpg", "rb") as f:
            expected_size = len(f.read())
            f.seek(0)
            files = {
                "file": ("test.jpg", f, "image/jpeg")
            }
            response = await client.post(
                "/upload_file2/",
                files=files,
            )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["filename"] == "test.jpg"
    assert response.json()["file_size"] == expected_size


if __name__ == "__main__":
	uvicorn.run("test11:app", port=8080, reload=True)