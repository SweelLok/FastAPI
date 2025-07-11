import pathlib

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status


module_path = pathlib.Path(__file__).parent

app = FastAPI()


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

if __name__ == "__main__":
	uvicorn.run("test11:app", port=8080, reload=True)