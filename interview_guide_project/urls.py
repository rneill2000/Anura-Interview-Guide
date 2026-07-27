from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from core import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('generate/', views.generate_guide, name='generate_guide'),
    path('finalize/', views.finalize_guide, name='finalize_guide'),
    path('download/<str:filename>/', views.download_guide, name='download_guide'),
    path('fetch-news/', views.fetch_news, name='fetch_news'),
    path('fetch-about-info/', views.fetch_about_info, name='fetch_about_info'),
    path('fetch-interviewer-notes/', views.fetch_interviewer_notes, name='fetch_interviewer_notes'),
    path('guides/', views.guides_list, name='guides_list'),
    path('guides/<int:guide_id>/download/', views.guide_download, name='guide_download'),
    path('guides/<int:guide_id>/payload/', views.guide_payload, name='guide_payload'),
    path('templates/', views.list_templates, name='list_templates'),
    path('templates/save/', views.save_template, name='save_template'),
    path('templates/<int:template_id>/', views.get_template, name='get_template'),
    path('templates/<int:template_id>/delete/', views.delete_template, name='delete_template'),
    path('bullhorn/candidates/', views.bullhorn_candidate_search, name='bullhorn_candidate_search'),
    path('bullhorn/candidates/<int:candidate_id>/resume/', views.bullhorn_candidate_resume, name='bullhorn_candidate_resume'),
    path('bullhorn/jobs/', views.bullhorn_job_search, name='bullhorn_job_search'),
    path('debug/claude/', views.debug_claude, name='debug_claude'),
]
