from django.urls import path
from . import views

urlpatterns = [
    path('marafik_app__home', views.home, name='home'),
    path('marafik_app__about', views.about, name='about'),
    path('marafik_app__navbar', views.navbar, name='navbar'),
    path('marafik_app__footer', views.footer, name='footer'),
    path('marafik_app__register', views.register, name='register'),
    path('marafik_app__login', views.login_view, name='login'),  # Changé de views.login à views.login_view
    path('marafik_app__logout', views.logout_view, name='logout'),  # Ajouté pour la déconnexion
    path('marafik_app__admin_setup', views.admin_setup, name='admin_setup'),
    path('marafik_app__employee_task', views.employee_task, name='employee_task'),
    path('marafik_app__super_admin_users', views.super_admin_users, name='super_admin_users'),
    path('marafik_app__admin_task_types', views.admin_task_types, name='admin_task_types'),
    path('marafik_app__admin_historique/', views.historique_view, name='historique'),
]