from django.urls import path

from . import views

urlpatterns = [
    path('query/', views.query, name='queryhandler-query'),
    path('search/', views.search, name='queryhandler-search'),
    path('questions/', views.questions, name='queryhandler-questions'),
]