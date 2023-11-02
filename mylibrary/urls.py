from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("librarymanagement/", include("librarymanagement.urls")),
    path("admin/", admin.site.urls),
]
