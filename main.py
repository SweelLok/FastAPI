import uvicorn
from fastapi import FastAPI


app = FastAPI()


@app.get("/calculate/") 
async def calculate(operator: str, a: int, b: int) -> dict:
		if operator == "add":
				result = a + b
		elif operator == "subtract":
				result = a - b
		elif operator == "multiply":
				result = a * b
		elif operator == "divide":
				result = a / b
		else:
				return {"error": "Invalid operator"}
		
		return {"result": result}


if __name__ == "__main__":
    uvicorn.run("main1:app", reload=True)