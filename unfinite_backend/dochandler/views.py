from django.shortcuts import render
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json
from .processpdf import *

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
def extractpdffromURL(request):

    d = json.loads(request.body)

    url = d.get('url')

    if url is None:
        return JsonResponse({'detail':'failure'}, status=500)
    elif url.strip() == '':
        return JsonResponse({'detail':'failure'}, status=500)
    elif url[-4:] != '.pdf':
        return JsonResponse({'detail':'failure'}, status=500)
    
    embeddings = embedpdf(url)

    ### add to the index here, along with the proper metadata

    return JsonResponse({'Detail':'Successfully indexed the document.'}, status=200)

@csrf_exempt
@require_internal
def answerquestion(request):

    d = json.loads(request.body)

    question = d.get('question')
    docids = d.get('docids') # list of docids to search through

    if question is None:
        return JsonResponse({'detail':'failure'}, status=500)
    elif question.strip() == '':
        return JsonResponse({'detail':'failure'}, status=500)
    
    ## vector search here, only through the docids
    ## generate response and return it
    answer = ''

    return JsonResponse({'answer':answer}, status=200)