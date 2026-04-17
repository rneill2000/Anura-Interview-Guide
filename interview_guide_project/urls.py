from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('generate/', views.generate_guide, name='generate_guide'),
    path('download/<str:filename>/', views.download_guide, name='download_guide'),
    path('fetch-news/', views.fetch_news, name='fetch_news'),
    path('bullhorn/candidates/', views.bullhorn_candidate_search, name='bullhorn_candidate_search'),
    path('bullhorn/jobs/', views.bullhorn_job_search, name='bullhorn_job_search'),
    path('debug/claude/', views.debug_claude, name='debug_claude'),
]
