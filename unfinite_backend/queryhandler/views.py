from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .openai_api import query_generation_model
import json
from .scrape import attach_links, google_SERP
# Create your views here.

# eventually, when the apps are on different machines,
# just copy the api/models.py file to queryhandler/models.py
# for now, import them from the api app
from django.apps import apps
Query = apps.get_model('api', 'Query')
SERP = apps.get_model('api', 'SERP')

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

# all of these csrf_exempts will be removed once this is on a seperate Django project, nobody can CSRF from the API.
@csrf_exempt
@require_internal
def query(request):
    '''
        assumes query_text is a field of request.body, also user_id, and that they're not empty and stuff <- make this precise.
        this means that stuff related to the validity of the query_text should be handled in the API endpoint that this gets POSTed from.
        this function pretty much just wraps a call to query_generation_model.
    '''
    d = json.loads(request.body) # this assumes that the API sent a well-formed request. TODO: maybe check here...

    skeleton, q = query_generation_model('text-davinci-003', d.get('query_text'), d.get('user_id'))

    if skeleton is None: # :(
        return JsonResponse({'detail':'failure'}, status=500)

    return JsonResponse({'skeleton':skeleton, 'id':q.id}, status=200)

@csrf_exempt
@require_internal
def search(request):
    '''
        search also takes a request from the API, providing a Query id and an index into its skeleton.
        It then scrapes Google search results relating to the Query and sub-topic, and returns them. 
    '''

    d = json.loads(request.body) # also assumes that the required fields exist in the request

    query_id = d['id']
    topic_num = d['topic']

    # find the query object with id query_id
    qs = Query.objects.filter(id=query_id)
    if len(qs) == 0:
        return JsonResponse(data={'detail':f'Query with ID {query_id} doesn\'t exist'}, status=500)

    q = qs[0] # there's only one of such Query objs
    skeleton = json.loads(q.skeleton) # load its skeleton

    if topic_num >= len(skeleton): # make sure that topic_num is a valid index into the skeleton
        return JsonResponse(data={'detail':f'Invalid topic {topic_num}'}, status=500)

    # craft search string to use on Google
    search_string = f'{q.query_text} "{skeleton[topic_num]}"'

    # check if there's an existing SERP object already associated with that search string
    s = SERP.objects.filter(search_string=search_string)

    if len(s) == 0:
        # no existing SERP - just gotta scrape it!
        serp = google_SERP(search_string) # scrape
        new_serp = SERP(search_string=search_string, entries=json.dumps(serp)) # new SERP
        new_serp.save()
        new_serp.queries.add(q) # relate to the query
        new_serp.save()
    else:
        # pull existing SERP
        serp = json.loads(s[0].entries)
        s[0].queries.add(q) # still relate to query (might already be, but there won't be duplicates)
        s[0].save()

    return JsonResponse(data={'serp': serp}, status=200)