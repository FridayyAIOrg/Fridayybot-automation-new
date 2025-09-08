from aiohttp import web

async def health_check(request):
    return web.Response(text="OK, v-1.0.0")

def create_health_app():
    app = web.Application()
    app.router.add_get("", health_check)
    return app
