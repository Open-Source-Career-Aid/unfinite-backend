import json, requests
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt, get_token
from django.views.decorators.http import require_POST
from .models import UnfiniteUser, BetaKey
from django.conf import settings
from django_ratelimit.decorators import ratelimit

def requires_authentication(func):

    def wrap(request):

        if not request.user.is_authenticated:
            return JsonResponse({'detail': 'Unauthenticated.'}, status=400)
        
        return func(request)

    return wrap

@ensure_csrf_cookie
def get_csrf_cookie(request):
    return JsonResponse({}, status=200)

@require_POST
def login_view(request):
    data = json.loads(request.body)
    email = data.get('email')
    password = data.get('password')

    if email is None or password is None:
        return JsonResponse({'detail': 'One or more required fields are empty'}, status=400)

    user = authenticate(email=email, password=password)

    if user is None:
        return JsonResponse({'detail': 'Invalid credentials.'}, status=403)

    login(request, user)
    return JsonResponse({'detail': 'Successfully logged in.'})

@require_POST
@requires_authentication
def logout_view(request):
    logout(request)
    return JsonResponse({'detail': 'Successfully logged out.'})

@require_POST
def register_view(request):
    data = json.loads(request.body)
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("cfm_password")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    beta_key = data.get("beta_key")

    if any(map(lambda x: x == None, [email, password, first_name, last_name])):
        return JsonResponse({'detail': 'One or more required fields are empty'}, status=400)

    if UnfiniteUser.objects.filter(email=email).exists():
        return JsonResponse({'detail': 'Email associated with an existing account.'}, status=400)

    key_objs = BetaKey.objects.filter(user_email=email)

    if len(key_objs) != 1:
        return JsonResponse({'detail': 'Not an approved beta user.'}, status=400)

    if not key_objs[0].validate_key(beta_key):
        return JsonResponse({'detail': 'Wrong registration key.'}, status=400)

    # to delete the key after use, or not: that is the question...
    key_objs[0].delete()

    user = UnfiniteUser.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name)
    user.is_beta = True
    user.save()
    login(request, user)
    return JsonResponse({'detail': 'Successfully registered.'})

@ensure_csrf_cookie
def session_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'isAuthenticated': False})

    return JsonResponse({'isAuthenticated': True})

# now, in future views, use request.user.is_authenticated to check if the user is authenticated

@require_POST
@requires_authentication
@ratelimit(key='user', rate='1/10s') # limits authenticated users to one query per ten seconds. This may need adjusting. Prevents blatant abuse of the endpoint.
def query(request):

    data = json.loads(request.body)
    query_text = data.get('query_text')

    if query_text == None:
        return JsonResponse({'detail': 'Bad request, query_text not provided.'}, status=400)

    query_text = query_text.strip()

    if query_text == '':
        return JsonResponse({'detail': 'Bad request, query_text empty.'}, status=400)
    
    # eventually, make a django config variable corresponding to the queryhandler url
    response = requests.post('http://127.0.0.1:8000/queryhandler/query/', headers={'Authorization':settings.QUERYHANDLER_KEY}, json={'query_text': query_text, 'user_id': request.user.id})

    if response.status_code != 200:
        return JsonResponse(data={'detail':'Query failed'}, status=500)

    skeleton = response.json()['skeleton']

    return JsonResponse(data={'skeleton': json.dumps(skeleton)}, status=200)

def test(request):
    response = requests.post('http://127.0.0.1:8000/queryhandler/test/', headers={'Authorization':settings.QUERYHANDLER_KEY}, data={'detail':'some sensitive stuff'})
    return JsonResponse(response.json())