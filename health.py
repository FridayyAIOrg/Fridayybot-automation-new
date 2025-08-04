# health.py
from aiohttp import web

async def health_check(request):
    return web.Response(text="OK")

def start_health_server():
    app = web.Application()
    app.router.add_get("/", health_check)
    web.run_app(app, port=8080)
