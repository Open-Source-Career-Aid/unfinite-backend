from django.urls import path

from . import views

urlpatterns = [
    path('csrf_cookie/', views.get_csrf_cookie, name='api-csrf-cookie'),
    path('login/', views.login_view, name='api-login'),
    path('logout/', views.logout_view, name='api-logout'),
    path('register/', views.register_view, name='api-register'),
    path('query/', views.query, name='api-query'),
]