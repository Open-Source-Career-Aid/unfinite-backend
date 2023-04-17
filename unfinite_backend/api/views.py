import json, requests
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt, get_token
from django.views.decorators.http import require_POST
from .models import UnfiniteUser, BetaKey
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from .models import Query, SERP, Feedback, SERPFeedback, Completion
from .signals import log_signal

def requires_authentication(func):
    # an nice little wrapper to require users to be logged in
    def wrap(request):

        if not request.user.is_authenticated:
            return JsonResponse({'detail': 'Unauthenticated.'}, status=400)
        
        return func(request)

    return wrap

def is_authenticated(request):
    if request.user.is_authenticated:
        return JsonResponse({'is_authenticated': True}, status=200)

    return JsonResponse({'is_authenticated': False}, status=200)

@csrf_exempt
def get_csrf_cookie(request):
    # a nice little function that the front-end can use to get a CSRF token if
    # it needs to. Might not be needed.
    t = get_token(request)
    return JsonResponse({'csrfToken': t}, status=200)

@require_POST
def login_view(request):
    '''
        POSTed to by login form. Requires a JSON with an email and a password in the request body.
        User is logged-in if email+password are correct.
    '''
    data = json.loads(request.body)
    email = data.get('email')
    password = data.get('password')

    # can't be None!
    if email is None or password is None:
        return JsonResponse({'detail': 'One or more required fields are empty'}, status=400)

    # use Django to handle authentication. 
    user = authenticate(email=email, password=password)

    # failure
    if user is None:
        return JsonResponse({'detail': 'Invalid credentials.'}, status=403)

    # success! log them in.
    login(request, user)
    log_signal.send(sender=None, user_id=user.id, desc="Logged in")
    return JsonResponse({'detail': 'Successfully logged in.'})

@require_POST
@requires_authentication
def logout_view(request):
    # logout a user. Doesn't require anything other than the CSRF token.
    user = request.user
    logout(request)
    log_signal.send(sender=None, user_id=user.id, desc="Logged out")
    return JsonResponse({'detail': 'Successfully logged out.'})

@require_POST
def register_view(request):
    '''
        Registers a user, requires them to provide an email, password (and confirmation password), full name (first name + last name),
        and a beta key.
    '''
    data = json.loads(request.body)
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("cfm_password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    #beta_key = data.get("beta_key") # no longer needed as of 4/4/23

    # check for None!
    if any(map(lambda x: x == None, [email, password, first_name, last_name])):
        return JsonResponse({'detail': 'One or more required fields are empty'}, status=400)

    # check for existing accounts with the same email
    if UnfiniteUser.objects.filter(email=email).exists():
        return JsonResponse({'detail': 'Email associated with an existing account.'}, status=400)

    # DISREGARD FOLLOWING AS OF 4/4/23
    # find the beta key associated with the email
    #key_objs = BetaKey.objects.filter(user_email=email)

    # it must exist... otherwise:
    #if len(key_objs) != 1:
    #    return JsonResponse({'detail': 'Not an approved beta user.'}, status=400)

    # make sure they provided a matching key!
    #if not key_objs[0].validate_key(beta_key):
    #    return JsonResponse({'detail': 'Wrong registration key.'}, status=400)

    user = UnfiniteUser.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name)
    user.is_beta = True
    user.save()
    log_signal.send(sender=None, user_id=user.id, desc="Registered")
    # to delete the key after use, or not: that is the question...
    # do this after user account is created! Otherwise, if the registration failed,
    # they'd no longer have a key and wouldn't be able to try again!
    
    #key_objs[0].delete() # also removed as of 4/4/23

    # log them in. for convenience. 
    login(request, user)
    log_signal.send(sender=None, user_id=user.id, desc="Logged in")
    return JsonResponse({'detail': 'Successfully registered.'})

# TODO: probably can delete this. 
# @ensure_csrf_cookie
# def session_view(request):
#     if not request.user.is_authenticated:
#         return JsonResponse({'isAuthenticated': False})

#     return JsonResponse({'isAuthenticated': True})

@require_POST
@requires_authentication
@ratelimit(key='user', rate='1/10s') # limits authenticated users to one query per ten seconds. This may need adjusting. Prevents blatant abuse of the endpoint.
def query(request):

    data = json.loads(request.body)
    query_text = data.get('query_text')

    # if you're making a query, you have to provide a query...
    if query_text == None:
        return JsonResponse({'detail': 'Bad request, query_text not provided.'}, status=400)

    # formatting
    query_text = query_text.strip()

    # if you're making a query, you have to provide a query... (whitespace/newlines don't count as a query)
    if query_text == '':
        return JsonResponse({'detail': 'Bad request, query_text empty.'}, status=400)
    
    # eventually, make a django config variable corresponding to the queryhandler url
    # make a request to the queryhandler. Send Authorization key. It needs the query text and the id of the user making it.
    response = requests.post(f'{settings.QUERYHANDLER_URL}query/', headers={'Authorization':settings.QUERYHANDLER_KEY}, json={'query_text': query_text, 'user_id': request.user.id})

    # if there's an error, oops.
    if response.status_code != 200:
        return JsonResponse(data={'detail':'Query failed'}, status=500)

    r = response.json()
    r2 = {k: v for k, v in r.items() if k != 'was_new'}
    # forward the response from the queryhandler.
    log_signal.send(sender=None, user_id=request.user.id, query_id=r['id'], query_was_new=r['was_new'], desc="Queried")
    return JsonResponse(data=r2, status=200)

@require_POST
@requires_authentication
@ratelimit(key='user', rate='1/1s')
def search(request):

    data = json.loads(request.body)
    query_id = data.get('id')
    topic_num = data.get('topic')

    # all fields must be provided!
    if query_id is None or topic_num is None:
        return JsonResponse(data={'detail':'Missing query_id or topic'}, status=400)

    if len(Query.objects.filter(id=query_id)) == 0:
        return JsonResponse(data={'detail':'No such query'}, status=400)

    # ask queryhandler to make the search. Provide Authorization key. Can just forward the request body JSON here.
    response = requests.post(f'{settings.QUERYHANDLER_URL}search/', headers={'Authorization':settings.QUERYHANDLER_KEY}, json=data)

    # oops
    if response.status_code != 200:
        return JsonResponse(data={'detail':'Search failed'}, status=500)

    r = response.json()
    r2 = {k: v for k, v in r.items() if k not in ['was_new', 'id']}
    # forward the response.
    log_signal.send(sender=None, user_id=request.user.id, query_id=query_id, serp_id=r['id'], serp_was_new=r['was_new'], desc="Searched")
    return JsonResponse(data=r2, status=200)

@require_POST
@requires_authentication
def questions(request):

    data = json.loads(request.body)
    query_id = data.get('id')
    topic_num = data.get('topic')

    # all fields must be provided!
    if query_id is None or topic_num is None:
        return JsonResponse(data={'detail':'Missing query_id or topic'}, status=400)
    
    if len(Query.objects.filter(id=query_id)) == 0:
        return JsonResponse(data={'detail':'No such query'}, status=400)
    
    # ask queryhandler to get the questions. Provide Authorization key. Can just forward the request body JSON here.
    response = requests.post(f'{settings.QUERYHANDLER_URL}questions/', headers={'Authorization':settings.QUERYHANDLER_KEY}, json=data)

    # oops
    if response.status_code != 200:
        return JsonResponse(data={'detail':'Questions failed'}, status=500)
    
    r = response.json()
    r2 = {k: v for k, v in r.items() if k not in ['was_new', 'id']}
    # forward the response.
    # log_signal.send(sender=None, user_id=request.user.id, query_id=query_id, questions_id=r['id'], questions_was_new=r['was_new'], desc="Questions")
    return JsonResponse(data=r2, status=200)

@require_POST
@requires_authentication
def summary(request):

    data = json.loads(request.body)
    query_id = data.get('id')
    topic_num = data.get('topic')
    ques_num = data.get('question')

    # all fields must be provided!
    if query_id is None or topic_num is None or ques_num is None:
        return JsonResponse(data={'detail':'Missing query_id or topic or question'}, status=400)
    
    if len(Query.objects.filter(id=query_id)) == 0:
        return JsonResponse(data={'detail':'No such query'}, status=400)
    
    # ask queryhandler to get the summary. Provide Authorization key. Can just forward the request body JSON here.
    response = requests.post(f'{settings.QUERYHANDLER_URL}summary/', headers={'Authorization':settings.QUERYHANDLER_KEY}, json=data)

    # oops
    if response.status_code != 200:
        return JsonResponse(data={'detail':'Summary failed'}, status=500)
    
    r = response.json()
    r2 = {k: v for k, v in r.items() if k not in ['was_new', 'id']}
    # forward the response.
    # log_signal.send(sender=None, user_id=request.user.id, query_id=query_id, summary_id=r['id'], summary_was_new=r['was_new'], desc="Summary")
    return JsonResponse(data=r2, status=200)

def summary_stream(request):

    data = json.loads(request.body)
    query_id = data.get('id')
    topic_num = data.get('topic')
    ques_num = data.get('question')

    # all fields must be provided!
    if query_id is None or topic_num is None or ques_num is None:
        return JsonResponse(data={'detail': 'Missing query_id or topic or question'}, status=400)

    if len(Query.objects.filter(id=query_id)) == 0:
        return JsonResponse(data={'detail': 'No such query'}, status=400)

    # ask queryhandler to get the summary. Provide Authorization key. Can just forward the request body JSON here.
    response = requests.post(f'{settings.QUERYHANDLER_URL}summary_stream/', headers={'Authorization': settings.QUERYHANDLER_KEY}, json=data, stream=True)

    # oops
    # if response.status_code != 200:
    #     return JsonResponse(data={'detail': 'Summary failed'}, status=500)

    def stream_response(response):
        for chunk in response.iter_content(chunk_size=32):
            if chunk:
                yield chunk

    # Forward the response as a streaming response
    r = StreamingHttpResponse(stream_response(response), content_type='text/event-stream')

    # Set any headers that are required for the response
    r['Content-Disposition'] = f'attachment; filename="{query_id}.json"'

    return r

@require_POST
@requires_authentication
def query_feedback(request):

    data = json.loads(request.body)
    query_id = data.get('id')
    feedback_text = data.get('feedback_text')

    # all fields must be provided!
    if feedback_text is None:
        return JsonResponse(data={'detail':'Missing query_id or feedback_text'}, status=400)

    if query_id is not None:
        q = Query.objects.get(id=query_id)

        if q is None:
            return JsonResponse(data={'detail':'no such query'}, status=400)

        f = Feedback.objects.create(user=request.user, query=q, text=feedback_text)
    else:
        f = Feedback.objects.create(user=request.user, text=feedback_text)
    f.save()

    return JsonResponse({'detail':'Feedback submitted'}, status=200)

@require_POST
@requires_authentication
def serp_feedback(request):

    data = json.loads(request.body)
    query_id = data.get('id')
    topic_idx = data.get('topic')
    serp_idx = data.get('serp')
    thumb = data.get('thumb') # 0, 1 for thumbdown, thumbup

    # all fields must be provided!
    if None in [query_id, thumb, topic_idx, serp_idx]:
        return JsonResponse(data={'detail':'Missing one or more fields'}, status=400)

    q = Query.objects.get(id=query_id)

    if q is None:
        return JsonResponse(data={'detail':'no such query'}, status=400)

    if topic_idx < 0 or topic_idx >= len(json.loads(q.skeleton)):
        return JsonResponse(data={'detail':'no such topic'}, status=400)

    skeleton = json.loads(q.skeleton)
    serp = SERP.objects.filter(queries__in=[q.id]).filter(search_string__contains=skeleton[topic_idx])[0]
    thumbs = ['TD', 'TU']

    if serp_idx < 0 or serp_idx >= len(json.loads(serp.entries)):
        return JsonResponse(data={'detail':'no such serp'}, status=400)

    resource = json.loads(serp.entries)[serp_idx]
    f = SERPFeedback.objects.create(user=request.user, query=q, serp=serp, rating=thumbs[thumb], resource=json.dumps(resource), serp_idx=serp_idx, topic_idx=topic_idx)
    f.save()

    return JsonResponse({'detail':'Feedback submitted'}, status=200)


@requires_authentication
def get_completion(request):

    #data = json.loads(request.body)
    query_id = request.GET.get('id', '')
    
    cs = Completion.objects.filter(query__in=[query_id], user__in=[request.user.id])

    if len(cs) == 0:
        c = create_blank_completion(query_id, request.user.id)
    else:
        c = cs[0]
    
    return JsonResponse(data={'completion': json.dumps(c.completion), 'track': c.track}, status=200)

@require_POST
@requires_authentication
def track_completion(request):

    query_id = json.loads(request.body).get('id')

    cs = Completion.objects.get(query_id=query_id, user=request.user)

    cs.track = 1-cs.track
    cs.save()

    if cs.track == 1:
        return JsonResponse(data={'detail':'Now tracking this completion.', 'status':200}, status=200)
    
    return JsonResponse(data={'detail':'No longer tracking this completion.', 'status':200}, status=200)

@require_POST
@requires_authentication
def modify_completion(request):

    data = json.loads(request.body)
    query_id = data.get('id')
    topic_id = data.get('topic')

    if None in [query_id, topic_id]:
        return JsonResponse(data={'detail':'query id/topic missing'}, status=400)

    if Query.objects.filter(id=query_id).count() == 0:
        return JsonResponse(data={'detail':'no such query'}, status=400)

    c = Completion.objects.get(query__in=[query_id], user__in=[request.user.id])

    if c is None:
        c = create_blank_completion(query_id, request.user.id)

    q = Query.objects.get(id=query_id)

    if topic_id < 0 or topic_id >= len(json.loads(q.skeleton)):
        return JsonResponse(data={'detail':'no such topic'}, status=400)

    completion = json.loads(c.completion)

    completion[topic_id] = 1 - completion[topic_id] # flip it!

    c.completion = json.dumps(completion)

    c.save()

    log_signal.send(sender=None, user_id=request.user.id, query_id=query_id, completion_id=c.id, completion_idx=topic_id, desc="Completion modified")
    return JsonResponse(data={'detail':'success'}, status=200)
    

def create_blank_completion(query_id, user_id):

    q = Query.objects.get(id=query_id)
    completion = [0 for i in range(len(json.loads(q.skeleton)))]
    c = Completion.objects.create(query_id=query_id, user_id=user_id, completion=completion)
    c.save()

    return c


# @require_POST
# @requires_authentication
# def track(request):

#     data = json.loads(request.body)
#     query_id = data.get('id')

#     if query_id is None: return JsonResponse(data={'detail':'No query_id provided'}, status=400)

#     qs = Query.objects.filter(id=query_id)

#     if not len(qs): return JsonResponse(data={'detail':'No such query'}, status=400)

#     q = qs[0]

#     request.user.in_progress.add(q)

#     return JsonResponse(data={'detail':'Query successfully tracked!'}, status=200)


# @requires_authentication
# def get_tracking(request):

#     out = []

#     for query in request.user.in_progress.all():

#         completion = json.loads(Completion.objects.get(user=request.user, query=query).completion)
#         out.append({'query_text':query.query_text, 'completion':completion})

#     return JsonResponse(data={'completions':json.dumps(out)}, status=200)

@requires_authentication
def get_tracking_completions(request):

    cs = Completion.objects.filter(user=request.user, track=1)
    #[print(x.query.id, x.query.query_text, x.completion) for x in cs]

    return JsonResponse(data={'completions':[{'id':c.query.id, 'title':c.query.query_text, 'completion':json.dumps(c.completion)} for c in cs]}, status=200)


@require_POST
@requires_authentication
def get_thumbs(request):

    query_id = request.GET.get('id', '')
    topic_idx = request.GET.get('topic', '')

    if query_id == '' or topic_idx == '': return JsonResponse(data={'detail':'No query_id or topic provided'}, status=400)


    if not Query.objects.filter(id=query_id).exists():

        return JsonResponse(data={'detail':'No such query'}, status=400)

    q = Query.objects.get(id=query_id)

    s = SERP.objects.get(query=q, idx=topic)

    fbs = sorted(SERPFeedback.objects.filter(query=query, serp=s, user=request.user), key=lambda x: x.serp_idx)

    out = []
    m = ['TU', 'TD', 'TN']

    j = 0
    for i in range(len(json.loads(s.entries))):
        if fbs[j].serp_idx == i:
            out.append(m.index(fbs[j].rating))
            j += 1
            continue
        out.append(2)

    return JsonResponse(data={'thumbs':json.dumps(out)}, status=200)


@require_POST
@requires_authentication
def references(request):

    data = json.loads(request.body)
    query_id = data.get('id')
    topic_num = data.get('topic')
    ques_num = data.get('question')

    # all fields must be provided!
    if query_id is None or topic_num is None or ques_num is None:
        return JsonResponse(data={'detail': 'Missing query_id or topic or question'}, status=400)

    if len(Query.objects.filter(id=query_id)) == 0:
        return JsonResponse(data={'detail': 'No such query'}, status=400)
    
    response = requests.post(f'{settings.QUERYHANDLER_URL}references/', headers={'Authorization': settings.QUERYHANDLER_KEY}, json=data, stream=True)

    if response.status_code != 200:
        return JsonResponse(data={'detail': 'QueryHandler returned error'}, status=400)
    
    urls = json.loads(response.content)
    
    # print(response.content)
    return JsonResponse(data=urls, status=200)


@requires_authentication
def embed_document(request):

    data = json.loads(request.body)

    url = data.get('url')
    if url is None:
        return JsonResponse({'detail':'failure'}, status=500)
    elif url.strip() == '':
        return JsonResponse({'detail':'failure'}, status=500)
    elif url[-4:] != '.pdf':
        return JsonResponse({'detail':'failure'}, status=500)

    data['user'] = request.user.id

    response = requests.post(f'{settings.DOCHANDLER_URL}embed_document/', headers={'Authorization': settings.QUERYHANDLER_KEY}, json=data)

    if response.status_code != 200:
        return JsonResponse(data={'detail': 'QueryHandler returned error'}, status=400)
    return JsonResponse(data=response.json(), status=200)


@requires_authentication
def summarize_document(request):

    data = json.loads(request.body)

    question = data.get('question')
    docids = data.get('docids') 

    if question is None:
        return JsonResponse({'detail':'failure'}, status=400)
    elif question.strip() == '':
        return JsonResponse({'detail':'failure'}, status=400)

    if len(json.loads(docids)) == 0:
        return JsonResponse({'detail':'no document provided'}, status=400)
    
    data['user'] = request.user.id

    response = requests.post(f'{settings.DOCHANDLER_URL}summarize_document/', headers={'Authorization': settings.QUERYHANDLER_KEY}, json=data)

    if response.status_code != 200:
        return JsonResponse(data={'detail': 'QueryHandler returned error'}, status=400)

    return JsonResponse(data=response.json(), status=200)

@requires_authentication
def QA_feedback(request):

    data = json.loads(request.body)

    qaid = data.get('qaid')

    if qaid is None:
        return JsonResponse({'detail':'failure'}, status=400)

    response = requests.post(f'{settings.DOCHANDLER_URL}qafeedback/', headers={'Authorization': settings.QUERYHANDLER_KEY}, json=data)

    if response.status_code != 200:
        return JsonResponse(data={'detail': 'QueryHandler returned error'}, status=400)

    return JsonResponse(data=response.json(), status=200)

@requires_authentication
def get_total_documents_indexed(request):

    response = requests.get(f'{settings.DOCHANDLER_URL}get_total_documents_indexed/', headers={'Authorization': settings.QUERYHANDLER_KEY})

    if response.status_code != 200:
        return JsonResponse(data={'detail': 'QueryHandler returned error'}, status=400)

    return JsonResponse(data=response.json(), status=200)