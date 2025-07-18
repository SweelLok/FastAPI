import json
import uvicorn

from fastapi import FastAPI, Header, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse


app = FastAPI()


@app.get("/check_headers/")
async def check_headers(
	request: Request,  user_agent: str = Header(None),  x_token: str = Header(...)
):
	print(json.dumps(dict(request.headers.items()), indent=4))

	if x_token != "token":
		raise HTTPException(status_code=400, detail="X-Token header invalid")
	
	return {"user_agent": user_agent, "x_token": x_token}

@app.get("/check_auth/")
async def check_auth(
	request: Request, 
	x_api_key = Header(None), 
	authorization = Header(...),
	accept = Header(default="application/json"),
):
	print(json.dumps(dict(request.headers.items()), indent=4))


	token = authorization.split()[1]
	if token != "mysecrettoken":
		raise HTTPException(status_code=400, detail="Authorization header invalid")
	
	data = {"Authorization": "success", "API_KEY": x_api_key}


	if "text/html" in accept:
		content = f"<html><body><h1>Authorization succesfully</h1><p>Api Key: {x_api_key}</p></body></html>"
		response = HTMLResponse(content=content)
	else:
		response = JSONResponse(content=data)


	print({json.dumps(dict(request.headers.items()), indent=4)})

	return response

if __name__ == "__main__":
	uvicorn.run("test7:app", reload=True)