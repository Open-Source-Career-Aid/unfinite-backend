from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .openai_api import query_generation_model
import json
# Create your views here.

def require_internal(func):

    def wrap(request):

        if request.META.get("HTTP_AUTHORIZATION") != settings.QUERYHANDLER_KEY:

            print('Unauthorized request to queryhandler.')

            return JsonResponse({'detail':'Forbidden: Invalid Token'}, status=403)

        return func(request)

    return wrap

@csrf_exempt
@require_internal
def test(request):

    return JsonResponse({'detail':'Request recieved and authenticated.'}, status=200)


@csrf_exempt
@require_internal
def query(request):
    '''
        assumes query_text is a field of request.body, and that it's not empty and stuff <- make this precise.
        this means that stuff related to the validity of the query_text should be handled in the API endpoint that this gets POSTed from.
    '''
    d = json.loads(request.body)
    return query_generation_model('text-davinci-003', d.get('query_text'), d.get('user_id'))