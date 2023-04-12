# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .utils import get_topics, highlight_topics


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


@require_internal
@csrf_exempt
def get_topics_view(request):
    text = request.POST.get('text')
    num_topics = request.POST.get('num_topics', 5)
    topics = get_topics(text, int(num_topics))
    return JsonResponse({'topics': topics})


@require_internal
@csrf_exempt
def highlight_topics_view(request):
    text = request.POST.get('text')
    num_topics = request.POST.get('num_topics', 5)
    highlighted_text = highlight_topics(text, int(num_topics))
    return JsonResponse({'highlighted_text': highlighted_text})
