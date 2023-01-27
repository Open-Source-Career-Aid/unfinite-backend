import json
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from .models import UnfiniteUser

@require_POST
def login_view(request):
    data = json.loads(request.body)
    username = data.get('username')
    password = data.get('password')

    if username is None or password is None:
        return JsonResponse({'detail': 'Please provide username and password.'}, status=400)

    user = authenticate(username=username, password=password)

    if user is None:
        return JsonResponse({'detail': 'Invalid credentials.'}, status=400)

    login(request, user)
    return JsonResponse({'detail': 'Successfully logged in.'})


def logout_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'detail': 'You\'re not logged in.'}, status=400)

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

    if any(map(lambda x: x == None, [email, password, first_name, last_name])):
        return JsonResponse({'detail': 'One or more fields are empty.'}, status=400)

    if UnfiniteUser.objects.filter(email=email).exists():
        return JsonResponse({'detail': 'Email associated with existing account.'}, status=400)

    user = UnfiniteUser.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name)
    
    login(request, user)
    return JsonResponse({'detail': 'Successfully registered.'})

@ensure_csrf_cookie
def session_view(request):
    if not request.user.is_authenticated:
        return JsonResponse({'isAuthenticated': False})

    return JsonResponse({'isAuthenticated': True})

# now, in future views, use request.user.is_authenticated to check if the user is authenticated