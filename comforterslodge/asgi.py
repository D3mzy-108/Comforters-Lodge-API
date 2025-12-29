import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "comforterslodge.settings")

django_asgi_app = get_asgi_application()

# FastAPI app (mounted at /api)
from lodge.fastapi_app import api as fastapi_app

from starlette.applications import Starlette
from starlette.routing import Mount

# IMPORTANT:
# We build a single ASGI "router" app that sends:
# - /api/*  -> FastAPI
# - everything else -> Django
application = Starlette(
    routes=[
        Mount("/api", app=fastapi_app),
        Mount("/", app=django_asgi_app),
    ]
)
