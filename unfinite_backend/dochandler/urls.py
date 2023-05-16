from django.urls import path
from django.urls import re_path
from django.conf.urls import include
from . import routing

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
    path('get_recommendations/', views.get_recommendations, name='get-recommendations'),
    path('get_outline/', views.get_outline, name='get-outline'),
    re_path(r'ws/', include(routing.websocket_urlpatterns)),
]