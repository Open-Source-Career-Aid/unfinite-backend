from django.shortcuts import render
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .openai_api import query_generation_model, questions_generation_model
from .openai_summarizer import summary_generation_model, summary_generation_model_gpt3_5_turbo, summary_stream_gpt_3_5_turbo
import json
from .scrape import attach_links, google_SERP, serphouse, scrapingrobot, scrapeitserp, bingapi
# Create your views here.

# eventually, when the apps are on different machines,
# just copy the api/models.py file to queryhandler/models.py
# for now, import them from the api app
from django.apps import apps
Query = apps.get_model('api', 'Query')
SERP = apps.get_model('api', 'SERP')
Relevantquestions = apps.get_model('api', 'Relevantquestions')
QuestionSummary = apps.get_model('api', 'QuestionSummary')

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

    skeleton, q, was_new = query_generation_model('text-davinci-003', d.get('query_text'), d.get('user_id'))

    if skeleton is None: # :(
        return JsonResponse({'detail':'failure'}, status=500)

    return JsonResponse({'skeleton':skeleton, 'id':q.id, 'was_new': was_new}, status=200)

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
    search_string = f'{skeleton[topic_num]} in {q.query_text}'

    # check if there's an existing SERP object already associated with that search string
    s = SERP.objects.filter(search_string=search_string)

    was_new = True

    if len(s) == 0:
        # no existing SERP - just gotta scrape it!
        serp = scrapingrobot(search_string) # scrape
        new_serp = SERP(search_string=search_string, entries=json.dumps(serp), idx=topic_num) # new SERP
        new_serp.save()
        new_serp.queries.add(q) # relate to the query
        new_serp.save()
        s = new_serp
    else:
        # pull existing SERP
        was_new = False
        serp = json.loads(s[0].entries)
        s[0].queries.add(q) # still relate to query (might already be, but there won't be duplicates)
        s[0].save()
        s = s[0]

    return JsonResponse(data={'serp': serp, 'id':s.id, 'was_new': was_new}, status=200)

@csrf_exempt
@require_internal
def questions(request):
    '''
        getquestions takes a request from the API, providing a Query id and an index into its skeleton.
        It then generates relevant questions using GPT4 and returns them.
    '''

    d = json.loads(request.body)

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
    
    q_text = q.query_text

    # generate questions
    questions, rq, was_new = questions_generation_model('gpt-4', topic_num, q_text)

    return JsonResponse(data={'questions': questions, 'id': rq.id, 'was_new':was_new}, status=200)

@csrf_exempt
@require_internal
def summary(request):

    d = json.loads(request.body)
    
    query_id = d['id']
    topic_num = d['topic']
    ques_num = d['question']
    answer_type = d['answertype']

    # find the query object with id query_id
    qs = Query.objects.filter(id=query_id)
    if len(qs) == 0:
        return JsonResponse(data={'detail':f'Query with ID {query_id} doesn\'t exist'}, status=500)
    
    q = qs[0]

    skeleton = json.loads(q.skeleton)

    if topic_num >= len(skeleton): # make sure that topic_num is a valid index into the skeleton
        return JsonResponse(data={'detail':f'Invalid topic {topic_num}'}, status=500)

    rs = Relevantquestions.objects.filter(query=q, idx=topic_num)
    if len(rs) == 0:
        return JsonResponse(data={'detail':f'No relevant questions for topic {topic_num}'}, status=500)
    
    r = rs[0]

    questions = json.loads(r.questions)[ques_num]

    # generate summary
    # summary, s, was_new = summary_generation_model(ques_num, topic_num, q)
    summary, s, was_new, metadata = summary_generation_model_gpt3_5_turbo(ques_num, topic_num, q, summarytype=int(answer_type))
    # print(metadata)


    return JsonResponse(data={'summary': summary, 'urls':s.urls, 'urlidx':s.urlidx, 'id': s.id, 'was_new':was_new}, status=200)

@csrf_exempt
@require_internal
def summary_stream(request):

    d = json.loads(request.body)
    
    query_id = d['id']
    topic_num = d['topic']
    ques_num = d['question']
    answer_type = d['answertype']

    # find the query object with id query_id
    qs = Query.objects.filter(id=query_id)
    if len(qs) == 0:
        return JsonResponse(data={'detail':f'Query with ID {query_id} doesn\'t exist'}, status=500)
    
    q = qs[0]
    # print(q)

    skeleton = json.loads(q.skeleton)

    if topic_num >= len(skeleton): # make sure that topic_num is a valid index into the skeleton
        return JsonResponse(data={'detail':f'Invalid topic {topic_num}'}, status=500)

    rs = Relevantquestions.objects.filter(query=q, idx=topic_num)
    if len(rs) == 0:
        return JsonResponse(data={'detail':f'No relevant questions for topic {topic_num}'}, status=500)
    
    r = rs[0]

    questions = json.loads(r.questions)[ques_num]

    # generate summary
    # summary, s, was_new = summary_generation_model(ques_num, topic_num, q)
    stream = summary_stream_gpt_3_5_turbo(ques_num, topic_num, q, summarytype=int(answer_type))
    # print(metadata)


    # return JsonResponse(data={'summary': summary, 'urls':s.urls, 'urlidx':s.urlidx, 'id': s.id, 'was_new':was_new}, status=200)
    return StreamingHttpResponse(stream, content_type='application/json')

@csrf_exempt
@require_internal
def references(request):

    d = json.loads(request.body)
    
    query_id = d['id']
    topic_num = d['topic']
    ques_num = d['question']
    answer_type = d['answertype']

    # find the query object with id query_id
    qs = QuestionSummary.objects.filter(query=query_id, idx=topic_num, questionidx=ques_num, answertype=answer_type)
    if len(qs) == 0:
        return JsonResponse(data={'detail':f'Question Summary doesn\'t exist'}, status=500)
    
    urls = qs[0].urls

    return JsonResponse(data={'urls': urls}, status=200)