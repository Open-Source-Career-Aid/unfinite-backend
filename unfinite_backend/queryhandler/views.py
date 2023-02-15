from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .openai_api import query_generation_model
import json
from .scrape import attach_links, google_SERP
# Create your views here.

from django.apps import apps
Query = apps.get_model('api', 'Query')
SERP = apps.get_model('api', 'SERP')

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

    skeleton, q = query_generation_model('text-davinci-003', d.get('query_text'), d.get('user_id'))

    if skeleton is None:
        return JsonResponse({'detail':'failure'}, status=500)

    #with_links = attach_links(skeleton, q)

    return JsonResponse({'skeleton':skeleton, 'id':q.id}, status=200)

@csrf_exempt
@require_internal
def search(request):

    d = json.loads(request.body)

    query_id = d['id']
    topic_num = d['topic']

    qs = Query.objects.filter(id=query_id)
    if len(qs) == 0:
        return JsonResponse(data={'detail':f'Query with ID {query_id} doesn\'t exist'}, status=500)

    q = qs[0]
    skeleton = json.loads(q.skeleton)

    if topic_num >= len(skeleton):
        return JsonResponse(data={'detail':f'Invalid topic {topic_num}'}, status=500)

    search_string = f'{q.query_text} "{skeleton[topic_num]}"'

    s = SERP.objects.filter(search_string=search_string)

    if len(s) == 0:
        # just gotta scrape it!
        serp = google_SERP(search_string)
        new_serp = SERP(search_string=search_string, entries=json.dumps(serp))
        new_serp.save()
        new_serp.queries.add(q)
        new_serp.save()

    else:
        serp = json.loads(s[0].entries)
        s[0].queries.add(q)
        s[0].save()

    return JsonResponse(data={'serp': serp}, status=200)