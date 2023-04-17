from django.urls import path

from . import views

urlpatterns = [
    path('embed_document/', views.embed_document, name='doc-embed'),
    path('summarize_document/', views.summarize_document, name='doc-answer'),
    path('qafeedback/', views.QA_feedback, name='qa-feedback'),
    path('totaldocuments/', views.get_total_documents_indexed, name='total-documents'),
]