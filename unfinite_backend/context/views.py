# Create your views here.
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .utils import get_topics, highlight_topics, preprocess, extract_topics_from_list
from .models import Topic, Edge


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
def highlight_topics_view(request, *args, **kwargs):
    text = request.POST.get('text')
    preprocessed_text = preprocess(text)
    topics = get_topics(preprocessed_text, 5)
    highlighted_text = highlight_topics(text, 5)
    return JsonResponse({'highlighted_text': highlighted_text}, status=200)


@require_internal
@csrf_exempt
def extract_topics_from_text(request, *args, **kwargs):
    text = request.POST.get('text')
    doc_id = args[0]
    text_gen = get_topics(text)
    for text in text_gen:
        if text is not None and isinstance(text, list):
            pass
            # for idx, topic in enumerate(text):
            #     topic_instance = Topic.objects.create(title=topic, synonyms=topic[idx:], doc_id=doc_id)
            #     topic_instance.save()

    return JsonResponse({'topics': ''}, status=200)
