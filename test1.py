import aiohttp
from aiohttp import web


users = ["user1", "user2", "user3"]


async def handle_get(request: web.Request) -> web.Response:
		# *  Get the user name from the URL path
		name = request.match_info.get("user_name", "")

		if not name:
			return web.json_response(
				{"error": "User name is required."}, status=400
			)
		
		if name not in users:
			return web.json_response(
				{"error": "User not found."}, status=404
			)
		
		return web.json_response({"message": f"User, {name} exists!"})


async def handle_post(request: web.Request) -> web.Response:
		# * Get the user name and email from the URL path
		user_name = await request.json()
		user_email = request.match_info.get("user_name", "")

		if not user_name:
			return web.json_response(
				{"error": "User name is required."}, status=400
			)
		
		if user_name in users:
			return web.json_response(
				{"error": "User already exists."}, status=400
			)
		
		return web.json_response(
			{"message": f"User, {user_name} created successfuly"}, status=201
		)



# * Create a simple web server using aiohttp
app = web.Application()
# * Define routes for the web server
app.add_routes(
	[
		web.get("/get_user/{user_name}/", handler=handle_get),
		web.post("/add_user/{user_name}/{user_email}/", handler=handle_post),
	]
)


if __name__ == "__main__":
		web.run_app(app)