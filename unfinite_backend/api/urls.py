from django.urls import path

from . import views

urlpatterns = [
    path('csrf_cookie/', views.get_csrf_cookie, name='api-csrf-cookie'),
    path('login/', views.login_view, name='api-login'),
    path('logout/', views.logout_view, name='api-logout'),
    path('register/', views.register_view, name='api-register'),
    path('query/', views.query, name='api-query'),
    path('search/', views.search, name='api-search'),
    path('is_authenticated/', views.is_authenticated, name='api-is-authenticated'),
    path('feedback/query/', views.query_feedback, name='api-query-feedback'),
    path('feedback/serp/', views.serp_feedback, name='api-serp-feedback'),
    path('completion/', views.get_completion, name='api-get-completion'),
    path('completion/modify/', views.modify_completion, name='api-modify-completion'),
    path('completion/track/', views.track_completion, name='api-track-query'),
    path('completion/trackingcompletions/', views.get_tracking_completions, name='api-get-query-tracking'),
    path('feedback/serp/get/', views.get_thumbs, name='api-get-thumbs'),
    path('questions/', views.questions, name='api-questions'),
    path('summary/', views.summary, name='api-summary'),
    path('summary_stream/', views.summary_stream, name='api-summary-stream'),
    path('references/', views.references, name='api-references'),
    path('summarize_document/', views.summarize_document, name='api-summarize-document'),
    path('index_document/', views.embed_document, name='api-embed-document'),
    path('qafeedback/', views.QA_feedback, name='api-qa-feedback'),
    path('totaldocuments/', views.get_total_documents_indexed, name='api-total-documents'),
    path('searchgooglescholar/', views.search_google_scholar, name='api-search-google-scholar'),
    path('searcharxiv/', views.search_arxiv, name='api-search-arxiv'),
    path('searchunfinite/', views.search_unfinite, name='api-search-unfinite'),
    path('preview/', views.summarize_document_fm_global, name='api-summarize-doc-fm-global'),
    path('get_recommendations/', views.get_recommendations, name='api-get-recommendations'),
]