from django.shortcuts import render
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json, pinecone, openai
from .processpdf import *
from api.signals import log_signal
from .models import Document, Thread, QA, FeedbackModel
import re
import uuid
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY
pinecone.init(api_key=settings.PINECONE_KEY, environment="us-central1-gcp")
index = pinecone.Index('unfinite-embeddings')

# a functuon that uses regex to verify that a text is a url
def is_url(text):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, text) is not None

# Create your views here.
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
def embed_document(request):

    d = json.loads(request.body)
    
    url = d.get('url').strip()
    user_id = d.get('user') # make sure these exist elsewhere: ../api/views.py

    # create a new thread for this request
    new_id = uuid.uuid4().hex[:16]
    while Thread.objects.filter(id=new_id).exists():
        new_id = uuid.uuid4().hex[:16]

    thread = Thread(id=new_id, user_id=user_id)
    thread.save()
    threadid = thread.id

    if not is_url(url):
        return JsonResponse({'detail':'Invalid URL'}, status=400)

    if len(Document.objects.filter(url=url)) != 0:
        return JsonResponse({'detail':'Document already embedded', 'document_id': Document.objects.get(url=url).id, 'thread_id':threadid}, status=200)

    pdf_text = extractpdf(url)
    doc = Document.objects.create(url=url, user_id=user_id, document_pages=json.dumps(pdf_text), num_pages=len(pdf_text))
    doc.save()
    doc.embed(index)
    log_signal.send(sender=None, user_id=user_id, desc="User indexed new document")
    return JsonResponse({'Detail':'Successfully indexed the document.', 'document_id': doc.id, 'thread_id': threadid}, status=200)

# def matches_to_text(result):

#     document_id = int(result['metadata']['document'])
#     page_number = int(result['metadata']['page'])

#     return JsonResponse({'Detail':'Successfully indexed the document.', 'document_id': doc.id, 'thread_id':threadid}, status=200)

def matches_to_text(result):

    document_id = int(result['metadata']['document'])
    page_number = int(result['metadata']['page'])

    print(page_number)

    try:
        return json.loads(Document.objects.get(id=document_id).document_pages)[page_number]
    except:
        return ""

@csrf_exempt
@require_internal
def summarize_document(request):

    d = json.loads(request.body)

    threadid = d.get('threadid')
    question = d.get('question')
    docids = d.get('docids') # list of docids to search through
    user_id = d.get('user')
    
    ## vector search here, only through the docids
    ## generate response and return it

    # load thread
    thread = Thread.objects.get(id=threadid)

    # load the messages
    messages = thread.get_promptmessages()

    # create a new QA object
    qa = QA.objects.create(thread=thread, question=question)

    # create a new feedback model
    feedback = FeedbackModel.objects.create(qa=qa)

    # TODO: save the question embeddings for future use
    response = openai.Embedding.create(input=question, engine='text-embedding-ada-002')
    question_embedding = response['data'][0]['embedding']

    similar = index.query(
        vector=question_embedding,
        filter={
            "document": {"$in": list(map(str, json.loads(docids)))},
            "dev": {"$eq": not settings.IS_PRODUCTION},
        },
        top_k=1,
        include_metadata=True
    )

    print(similar)

    text_to_summarize = list(map(matches_to_text, similar['matches']))

    text = ""
    for chunk in text_to_summarize:
        text += chunk+"\n"

    prompt = text + f'QUESTION: {question}'

    # messages.append([0, prompt])

    def zero_or_one(x):
        if x == 0:
            return "user"
        return "assistant"

    messagestochat = [{'role': zero_or_one(x[0]), 'content': x[1]} for x in messages]
    
    print(messagestochat)
    answer = gpt3_3turbo_completion(messagestochat)
    # messages.append([1, answer])

    # update the qa object and save it
    qa.docids = docids
    qa.user_id = user_id
    qa.feedback = feedback
    qa.answer = answer
    qa.save()

    # update the thread object and save it
    qaid = qa.id
    thread.add_qamodel(qaid)
    # thread.promptmessages = json.dumps(messages)
    thread.save()

    return JsonResponse({'answer': answer}, status=200)

@csrf_exempt
@require_internal
def QA_feedback(request):

    d = json.loads(request.body)

    qaid = d.get('qaid')
    feedback = d.get('feedback')
    thumbs = d.get('thumbs')

    # load the qa object
    qa = QA.objects.get(id=qaid)

    # load the feedback model
    feedbackmodel = qa.feedback

    # update the feedback model
    feedbackmodel.set_feedback(feedback)
    feedbackmodel.set_thumbs(thumbs)

    # save the feedback model
    feedbackmodel.save()

    # update the qa object
    qa.feedback = feedbackmodel

    # save the qa object
    qa.save()

    return JsonResponse({'detail':'Feedback successfully recorded.'}, status=200)
