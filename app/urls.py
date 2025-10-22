"""
URL configuration for app project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from symvouloi.views import update_teacher_and_consultant, assign_users_to_group, \
    evaluation_steps_json, add_metakinhsh, serve_document, update_teachers
from metakinhseis.views import metakinhsh_json, apofasi_metakinhshs_preview, katastash_plhrwmhs, import_metakinhseis
from symvouloi.admin import UnfoldPasswordResetView, UnfoldPasswordResetDoneView, UnfoldPasswordResetConfirmView, UnfoldPasswordResetCompleteView


urlpatterns = [
    path('update-teachers/', update_teacher_and_consultant, name='update_teachers'),
    path('update-all-teachers/', update_teachers, name='update_all_teachers'),
    path('assign_users_to_group/', assign_users_to_group, name='assign_users_to_group'),
    path('evaluation-steps-json/', evaluation_steps_json, name='evaluation_steps_json'),
    path('metakinhsh-json/', metakinhsh_json, name='metakinhsh_json'),
    path('add_metakinhsh', add_metakinhsh, name='add_metakinhsh'),
    path('apofasi_metakinhshs/', apofasi_metakinhshs_preview, name='apofasi_metakinhshs'),
    path('import-metakinhseis/', import_metakinhseis, name='import_metakinhseis'),
    path('katastash_plhrwmhs/', katastash_plhrwmhs, name='katastash_plhrwmhs'),
    path('documents/<str:document_name>', serve_document, name='serve_document'),
    path('documents/<str:year>/<str:folder>/<str:document_name>', serve_document, name='serve_document_evaluation'),
    path('impersonate/', include('impersonate.urls')), 
    path('admin/password_reset/', UnfoldPasswordResetView.as_view(), name='admin_password_reset'),
    path('admin/password_reset/done/', UnfoldPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', UnfoldPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', UnfoldPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('', admin.site.urls),
]
