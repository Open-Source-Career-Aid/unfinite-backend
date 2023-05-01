from django.urls import path

from . import views

urlpatterns = [
    path('embed_document/', views.embed_document, name='doc-embed'),
    path('summarize_document/', views.summarize_document, name='doc-answer'),
    path('qafeedback/', views.QA_feedback, name='qa-feedback'),
    path('totaldocuments/', views.get_total_documents_indexed, name='total-documents'),
    path('searchgooglescholar/', views.search_google_scholar, name='search-google-scholar'),
    path('searcharxiv/', views.search_arxiv, name='search-arxiv'),
    path('searchunfinite/', views.search_unfinite, name='search-unfinite'),
    path('summarize_document_stream/', views.summarize_document_stream, name='doc-answer-stream'),
]