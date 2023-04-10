from django.shortcuts import render
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json, pinecone, openai
from .processpdf import *
from .models import Document
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY
pinecone.init(api_key=settings.PINECONE_KEY, environment="us-central1-gcp")
index = pinecone.Index('unfinite-embeddings')

# Create your views here.

def require_internal(func):
    # cool and nice wrapper that keeps anybody other than the API from making 
    # a request to the wrapped function! Checks for correct Authorization KEY in 
    # request headers. 
    def wrap(request):

        if request.META.get("HTTP_AUTHORIZATION") != settings.QUERYHANDLER_KEY:

            print('Unauthorized request to queryhandler.')

            return JsonResponse({'detail':'Forbidden: Invalid Token'}, status=403)

        return func(request)

    return wrap

@csrf_exempt
@require_internal
def embed_document(request):

    d = json.loads(request.body)
    
    url = d.get('url')
    user_id = d.get('user') # make sure these exist elsewhere: ../api/views.py

    if len(Document.objects.filter(url=url)) != 0:
        return JsonResponse({'detail':'Document already embedded', 'document_id': Document.objects.get(url=url).id}, status=200)

    pdf_text = extractpdf(url)
    doc = Document.objects.create(url=url, user_id=user_id, document_pages=json.dumps(pdf_text), num_pages=len(pdf_text))
    doc.save()
    doc.embed(index)

    return JsonResponse({'Detail':'Successfully indexed the document.', 'document_id': doc.id}, status=200)

def matches_to_text(result):
    document_id = int(result['metadata']['document'])
    page_number = int(result['metadata']['page'])

    return json.loads(Document.objects.get(id=document_id).document_pages)[page_number]

@csrf_exempt
@require_internal
def summarize_document(request):

    d = json.loads(request.body)

    question = d.get('question')
    docids = d.get('docids') # list of docids to search through
    
    ## vector search here, only through the docids
    ## generate response and return it

    response = openai.Embedding.create(input=question, engine='text-embedding-ada-002')
    question_embedding = response['data'][0]['embedding']

    similar = index.query(
        vector=question_embedding,
        filter={
            "document": {"$in": list(map(str, json.loads(docids)))},
        },
        top_k=3,
        include_metadata=True
    )

    text_to_summarize = list(map(matches_to_text, similar['matches']))

    text = ""
    for chunk in text_to_summarize:
        text += chunk+"\n"

    prompt = text + f'QUESTION: {question}'
    
    answer = gpt3_3turbo_completion(prompt)

    return JsonResponse({'answer': answer}, status=200)