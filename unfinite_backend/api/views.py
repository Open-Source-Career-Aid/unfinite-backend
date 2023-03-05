import json, requests
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt, get_token
from django.views.decorators.http import require_POST
from .models import UnfiniteUser, BetaKey
from django.conf import settings
from django_ratelimit.decorators import ratelimit
from .models import Query, SERP, Feedback, SERPFeedback, Completion

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
    return JsonResponse({'detail': 'Successfully logged in.'})

@require_POST
@requires_authentication
def logout_view(request):
    # logout a user. Doesn't require anything other than the CSRF token.
    logout(request)
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
    beta_key = data.get("beta_key")

    # check for None!
    if any(map(lambda x: x == None, [email, password, first_name, last_name])):
        return JsonResponse({'detail': 'One or more required fields are empty'}, status=400)

    # check for existing accounts with the same email
    if UnfiniteUser.objects.filter(email=email).exists():
        return JsonResponse({'detail': 'Email associated with an existing account.'}, status=400)

    # find the beta key associated with the email
    key_objs = BetaKey.objects.filter(user_email=email)

    # it must exist... otherwise:
    if len(key_objs) != 1:
        return JsonResponse({'detail': 'Not an approved beta user.'}, status=400)

    # make sure they provided a matching key!
    if not key_objs[0].validate_key(beta_key):
        return JsonResponse({'detail': 'Wrong registration key.'}, status=400)

    user = UnfiniteUser.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name)
    user.is_beta = True
    user.save()

    # to delete the key after use, or not: that is the question...
    # do this after user account is created! Otherwise, if the registration failed,
    # they'd no longer have a key and wouldn't be able to try again!
    key_objs[0].delete()

    # log them in. for convenience. 
    login(request, user)
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
    response = requests.post('http://127.0.0.1:8000/queryhandler/query/', headers={'Authorization':settings.QUERYHANDLER_KEY}, json={'query_text': query_text, 'user_id': request.user.id})

    # if there's an error, oops.
    if response.status_code != 200:
        return JsonResponse(data={'detail':'Query failed'}, status=500)

    r = response.json()
    # forward the response from the queryhandler.
    return JsonResponse(data=r, status=200)

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

    # ask queryhandler to make the search. Provide Authorization key. Can just forward the request body JSON here.
    response = requests.post('http://127.0.0.1:8000/queryhandler/search/', headers={'Authorization':settings.QUERYHANDLER_KEY}, json=data)

    # oops
    if response.status_code != 200:
        return JsonResponse(data={'detail':'Search failed'}, status=500)

    r = response.json()
    # forward the response.
    return JsonResponse(data=r, status=200)

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
    f = SERPFeedback.objects.create(user=request.user, query=q, serp=serp, rating=thumbs[thumb], resource=json.dumps(resource))
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
    
    return JsonResponse(data={'completion':json.dumps(c.completion)}, status=200)

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

    return JsonResponse(data={'detail':'success'}, status=200)
    

def create_blank_completion(query_id, user_id):

    q = Query.objects.get(id=query_id)
    completion = [0 for i in range(len(json.loads(q.skeleton)))]
    c = Completion.objects.create(query_id=query_id, user_id=user_id, completion=completion)
    c.save()

    return c