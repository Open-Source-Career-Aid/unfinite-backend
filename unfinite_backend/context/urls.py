from django.urls import path

from . import views

urlpatterns = [
    path("context/<int:doc_id>", views.highlight_topics_view, name='doc-context'),
]