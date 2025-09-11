from django.contrib import admin
from django.urls import include, path
from rest_framework import routers

from apibase.views import DRFAuthenticatedGraphQLView, sdl
from web.demo.viewsets import BookViewSet

router = routers.DefaultRouter()
router.register(r"books", BookViewSet, basename="api-demo-book")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("graphql/", DRFAuthenticatedGraphQLView.as_view(graphiql=True)),
    path("sdl/", sdl),
]
