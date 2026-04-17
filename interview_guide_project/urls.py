from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="index"),
    path("generate/", views.generate_guide, name="generate_guide"),
    path("download/<str:filename>/", views.download_guide, name="download_guide"),
]
