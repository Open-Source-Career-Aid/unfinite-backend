from django.shortcuts import render
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from wsgiref.util import FileWrapper
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import json, pinecone, openai
from .processpdf import *
from itertools import chain
from api.signals import log_signal
from django.db import models
from .models import Document, Thread, QA, FeedbackModel
import re
import uuid
from django.conf import settings
from .pdfChunks import pdftochunks_url, extract_text_from_pdf_url, pdfdchunks_file
from django.core.files.uploadhandler import FileUploadHandler
# import kpextraction.py from keyphrasing folder
from .keyphrasing.kpextraction import *
from .outline.pdfoutliner import title_from_uploadedpdf, title_from_pdf
#from .LayeronePrompting import *
from .arxivscraper import *
from .pinecone_hybrid_search_retriever import PineconeHybridSearchRetriever, RemoteSparseEncoder
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter
from .outline.outlinefromLLM import *
from .youtubescraper import *
from .generalscraping import *
from .langchainChains import *
from .OpenAIprompts import *

openai.api_key = settings.OPENAI_API_KEY
os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
pinecone.init(api_key=settings.PINECONE_KEY, environment=settings.PINECONE_ENV)
embeddings = OpenAIEmbeddings()
sparse = RemoteSparseEncoder(settings.MODEL_SERVER_URL, settings.MODEL_SERVER_KEY)
index = pinecone.Index(settings.PINECONE_INDEX_NAME)

retriever = PineconeHybridSearchRetriever(embeddings=embeddings, sparse_encoder=sparse, index=index)
retriever.alpha = 0.7
#text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=100, chunk_overlap=16)
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size = 512,
    chunk_overlap  = 64,
    length_function = len,
)

special_prompts = {1: 'Simplify for a non expert', 2: 'Dumbsplain', 3: 'Technical and quick explanation', 4: 'Analogy'}

def scrape_youtube_and_save(url, user_id):
    chunks = scrape_youtube(url)
    d = Document.objects.create(url=url, title=url, user_id=user_id, document_chunks=json.dumps(chunks), num_chunks=len(chunks))
    # embed
    d.embed(retriever)
    d.save()
    return d

def scrape_url_and_save(url, user_id):
    chunks, title = make_chunks_from_url(url)
    d = Document.objects.create(url=url, title=title, user_id=user_id, document_chunks=json.dumps(chunks), num_chunks=len(chunks))
    # embed
    d.embed(retriever)
    d.save()
    return d

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
    """ this function takes a url or a pdf and embeds it into the pinecone index
    it also creates a new thread and a new document in the database
    pdfs are converted to text and then embedded
     """
    file = request.FILES.get("pdf")
    print(1)
    if file is not None:
        print(2)
        # for pdfs, we need to extract the text from the pdf and then embed it
        d = request.POST.dict() # get the data from the request
        handler = FileUploadHandler(request=request)
        handler.new_file(file, file_name=file.name, content_type=file.content_type, content_length=file.size)
        content = file.read()
        handler.upload_complete()
        if content:
            print(3)
            # embed the pdf file
            pdf_text = pdfdchunks_file(content)
            user_id = int(d.get('user')) if d.get('user').isnumeric() else None
            pdf_name = d.get('name')
            new_id = uuid.uuid4().hex[:16]
            while Thread.objects.filter(id=new_id).exists():
                new_id = uuid.uuid4().hex[:16]

            thread = Thread(id=new_id, user_id=user_id)
            thread.save()
            threadid = thread.id
            # make sure the pdf was embedded and not empty
            if pdf_text is not None:
                print(4)
                # print("file complete", content, "line 80")
                if len(Document.objects.filter(url=pdf_name)) != 0:
                    print(5)
                    return JsonResponse(
                        {'detail': 'Document already embedded', 'document_id': Document.objects.get(url=pdf_name).id,
                         'thread_id': threadid, 'title': Document.objects.get(url=pdf_name).title}, status=200)

                doc = Document.objects.create(url=pdf_name, user_id=user_id, document_chunks=json.dumps(pdf_text), num_chunks=len(pdf_text))
                doc.title = title_from_uploadedpdf(content)
                doc.save()
                doc.embed(index)
                log_signal.send(sender=None, user_id=user_id, desc="User indexed new document")
                return JsonResponse({'Detail':'Successfully indexed the document.', 'document_id': doc.id, 'thread_id': threadid, "title": doc.title}, status=200)

            return JsonResponse({'Detail':'Failed to index the document.', 'thread_id': threadid}, status=400)
    else:
        print(6)
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

        if not is_url(url) and not url.endswith('pdf'):
            print(7)
            print("Invalid URL")
            return JsonResponse({'detail':'Invalid URL'}, status=400)
            
        if len(Document.objects.filter(url=url)) != 0:
            print(8)

             # load the document
            doc = Document.objects.get(url=url)

             # check if the title is already there
            if doc.title:
                return JsonResponse({'detail':'Document already embedded', 'document_id': doc.id, 'thread_id':threadid, 'title': doc.title}, status=200)

            # get the title
            title = title_from_pdf(url)

            # update the document
            doc.title = title
            doc.save()
            return JsonResponse({'detail':'Document already embedded', 'document_id': Document.objects.get(url=url).id, 'thread_id':threadid, 'title': Document.objects.get(url=url).title}, status=200)
          
        # if url is a pdf or a youtube or a general url
        if url.endswith('pdf'):
            print(9)
            pdf = extract_text_from_pdf_url(url)
            pdf_chunks = list(map(lambda x: x.page_content, text_splitter.create_documents([pdf])))
            title = title_from_pdf(url)
            doc = Document.objects.create(url=url, user_id=user_id, document_chunks=json.dumps(pdf_chunks), num_chunks=len(pdf_chunks), title=title)
            # print(pdf_text)
            doc.save()
            doc.embed(retriever)
        elif url.startswith('https://www.youtube.com/watch?v='):
            print(10)
            # youtube video
            # video_id = url.split('=')[1]
            # title = title_from_youtube(video_id)            
            doc = scrape_youtube_and_save(url, user_id)
            # title = d['title']
            title = doc.title
        else:
            print(11)
            # general url
            doc = scrape_url_and_save(url, user_id)
            title = doc.title
        log_signal.send(sender=None, user_id=user_id, desc="User indexed new document")
        return JsonResponse({'Detail':'Successfully indexed the document.', 'document_id': doc.id, 'thread_id': threadid, 'title': title }, status=200)

# def matches_to_text(result):

#     document_id = int(result['metadata']['document'])
#     page_number = int(result['metadata']['page'])

#     return JsonResponse({'Detail':'Successfully indexed the document.', 'document_id': doc.id, 'thread_id':threadid}, status=200)

def matches_to_text_old(result):

    # print(result)
    document_id = int(result['metadata']['document'])
    # print(document_id)
    try:
        chunk_number = int(result['metadata']['chunk'])
    except:
        return ""

    try:
        return json.loads(Document.objects.get(id=document_id).document_chunks)[chunk_number]
    except:
        return ""

@csrf_exempt
@require_internal
# TODO: change the name from summarize_document to something that makes more sense, e.g. answer_question
def summarize_document(request):

    d = json.loads(request.body)

    threadid = d.get('threadid')
    question = d.get('question')
    docids = d.get('docids') # list of docids to search through
    user_id = d.get('user')
    special_id = d.get('special_id')

    is_overview = False

    if question == "Overview":
        is_overview = True
        question = "Use the abstract, title, and author names to introduce the document and provide 3 follow up questions without answers for the user. Encapsulate each question between curly braces."
    
    ## vector search here, only through the docids
    ## generate response and return it

    # load thread
    thread = Thread.objects.get(id=threadid)

    # load the messages
    messages = thread.get_promptmessages()

    associated_qas = sorted(list(QA.objects.filter(thread=thread)), key = lambda x: x.index)

    # create a new QA object
    qa = QA.objects.create(thread=thread, question=question, index=len(associated_qas))

    # create a new feedback model
    feedback = FeedbackModel.objects.create(qa=qa)

    if special_id:
        # simplify the last answer
        last_qa = associated_qas[-1]
        text = last_qa.txttosummarize
        last_question = last_qa.question
        last_answer = last_qa.answer
        prompt = text + f'QUESTION: {last_question}'

        messages.append([0, prompt])
        messages.append([1, last_answer])
        messages.append([0, f"{special_prompts[special_id]}"])
    
    else:

        # based on the query decide whether to summarize the whole document or perform a dedicated vector search
        #modus_operandi = get_modus_operandi(question)

        if False: #modus_operandi != 'The answer is very specific':

            all_chunks = index.query(
                vector=[0 for x in range(1536)],
                filter={
                    "document": {"$in": list(map(str, json.loads(docids)))},
                    "dev": {"$eq": not settings.IS_PRODUCTION},
                },
                include_values=True,
                top_k=500
            )
            average_embedding = np.mean([v['values'] for v in all_chunks['matches']], axis=0)

            similar = index.query(
                vector=list(average_embedding),
                filter={
                    "document": {"$in": list(map(str, json.loads(docids)))},
                    "dev": {"$eq": not settings.IS_PRODUCTION},
                },
                include_metadata=True,
                top_k=5
            )

            # the following code should be abstracted. since it's written twice. I wasn't sure if   
            # there was a reason for organizing it this way, so I left it how it was.
            
            text_to_summarize = list(map(matches_to_text, similar['matches']))

            text = ""
            for chunk in text_to_summarize:
                text += chunk+"\n"

            prompt = text + f'QUESTION: {question}'

            print(prompt)

            messages.append([0, prompt])

            def zero_or_one(x):
                if x == 0:
                    return "user"
                return "assistant"

            messagestochat = [{'role': zero_or_one(x[0]), 'content': x[1]} for x in messages]
            
            answer = gpt3_3turbo_completion(messagestochat)
            # messages.append([1, answer])

            # update the qa object and save it
            qa.docids = docids
            qa.user_id = user_id
            qa.feedback = feedback
            qa.answer = answer
            qa.txttosummarize = text
            qa.save()

            # update the thread object and save it
            #qaid = qa.id
            #thread.add_qamodel(qaid)
            # thread.promptmessages = json.dumps(messages)
            thread.save()

            return JsonResponse({'answer': answer}, status=200)
        
        # elif modus_operandi == 'The answer is very specific':
        # TODO: save the question embeddings for future use
        # if is_overview is False
        if is_overview is False:
            response = openai.Embedding.create(input=question, engine='text-embedding-ada-002')
            question_embedding = response['data'][0]['embedding']

            similar = index.query(
                vector=question_embedding,
                filter={
                    "document": {"$in": list(map(str, json.loads(docids)))},
                    "dev": {"$eq": not settings.IS_PRODUCTION},
                },
                top_k=5,
                include_metadata=True
            )

            # print(similar)

            text_to_summarize = list(map(matches_to_text, similar['matches']))
        else:
            # get the first 2 chunks
            text_to_summarize = json.loads(Document.objects.get(id=json.loads(docids)[0]).document_chunks)[:2]
        
        text = ""
        for chunk in text_to_summarize:
            text += chunk+"\n"
        

        prompt = text + f"QUESTION: {question} \n Provide 3 follow up questions without answers for the user. Encapsulate each question between curly braces."

        print(prompt)

        messages.append([0, prompt])

    def zero_or_one(x):
        if x == 0:
            return "user"
        return "assistant"

    messagestochat = [{'role': zero_or_one(x[0]), 'content': x[1]} for x in messages]
    print(messagestochat)
    if json.loads(docids)[0] == 458:
        answer = gpt3_3turbo_completion(messagestochat, summarymodel="gpt-4")
        print("did summarization with gpt-4")
    else:
        answer = gpt3_3turbo_completion(messagestochat)

    # answercopy = answer
    # break answer into text and questions, a question is encapsulated between curly braces

    questions = re.findall(r'\{(.*?)\}', answer)
    questions = ['{'+x+'}' for x in questions]

    # text is now the answer without the questions
    text = re.sub(r'\{(.*?)\}', '', answer)

    text = match_keyphrases(text)

    # remove unnecessary newlines
    answer = re.sub(r'\n\n+', '\n\n', text)

    # remove unnecessary spaces
    answer = '\n\n'.join([x for x in answer.split('\n') if x != ''])
        
    # messages.append([1, answer])

    # update the qa object and save it
    qa.docids = docids
    qa.user_id = user_id
    qa.feedback = feedback
    qa.answer = answer
    qa.relevantquestions = json.dumps(questions)
    qa.txttosummarize = text
    qa.save()

    # update the thread object and save it
    #qaid = qa.id
    #thread.add_qamodel(qaid)
    # thread.promptmessages = json.dumps(messages)
    thread.save()

    return JsonResponse({'answer': answer + ''.join(questions)}, status=200)

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

@csrf_exempt
@require_internal
def get_total_documents_indexed(request):
    return JsonResponse({'detail':Document.objects.all().count()}, status=200)

@csrf_exempt
@require_internal
def search_google_scholar(request):
    d = json.loads(request.body)
    query = d.get('query')

    results = google_scholar_scrape(query, num_result=4)

    toreturn = []
    for result in results:
        toreturn.append([results[result]['title'], results[result]['pdf_link']])

    return JsonResponse({'detail':json.dumps(toreturn)}, status=200)

@csrf_exempt
@require_internal
def search_arxiv(request):
    d = json.loads(request.body)
    query = d.get('query')

    results = arxiv_search(query)

    toreturn = []
    for result in results:
        toreturn.append([results[result]['title'], results[result]['pdf_link']])

    print(toreturn)
    return JsonResponse({'detail':json.dumps(toreturn)}, status=200)

@csrf_exempt
@require_internal
def search_unfinite(request):
    d = json.loads(request.body)
    query = d.get('query')

    # response = openai.Embedding.create(input=query, engine='text-embedding-ada-002')
    # query_embedding = response['data'][0]['embedding']

    # # get top 4 similar documents
    # similar = index.query(
    #     vector=query_embedding,
    #     filter={
    #         "dev": {"$eq": not settings.IS_PRODUCTION},
    #     },
    #     top_k=50,
    #     include_metadata=True
    # )

    relevant = retriever.get_relevant_documents(query)

    def gettitleandurl(result):

        docid = int(result.metadata['document'])

        doc = Document.objects.get(id=docid)

        return [doc.title, doc.url]

    # print(similar)

    toreturn  = set()
    for match in relevant:
        # toreturn.append(gettitleandurl(match))\
        title, url = gettitleandurl(match)
        toreturn.add((title, url))
    
    toreturn = list(toreturn)
    toreturn = [list(x) for x in toreturn][:4]

    return JsonResponse({'detail':json.dumps(toreturn)}, status=200)

@csrf_exempt
@require_internal
# TODO: change the name from summarize_document to something that makes more sense, e.g. answer_question
def summarize_document_stream_OLD(request):

    d = json.loads(request.body)

    threadid = d.get('threadid')
    question = d.get('question')
    docids = d.get('docids') # list of docids to search through
    user_id = d.get('user')
    special_id = d.get('special_id')

    is_overview = False

    if question == "Overview":
        is_overview = True
        question = "Use the abstract, title, and author names to introduce the document and provide 3 follow up questions without answers for the user. Encapsulate each question between curly braces.\nAnswer:"
    
    ## vector search here, only through the docids
    ## generate response and return it

    # load thread
    thread = Thread.objects.get(id=threadid)

    # load the messages
    messages = thread.get_promptmessages()

    associated_qas = sorted(list(QA.objects.filter(thread=thread)), key = lambda x: x.index)

    # create a new QA object
    qa = QA.objects.create(thread=thread, question=question, index=len(associated_qas))

    # create a new feedback model
    feedback = FeedbackModel.objects.create(qa=qa)

    if special_id:

        # simplify the last answer
        last_qa = associated_qas[-1]

        text = last_qa.txttosummarize
        last_question = last_qa.question
        last_answer = last_qa.answer
        prompt = text + f'QUESTION: {last_question}'

        messages.append([0, prompt])
        messages.append([1, last_answer])
        messages.append([0, f"{special_prompts[special_id]}"])
    
    else:

        # based on the query decide whether to summarize the whole document or perform a dedicated vector search
        #modus_operandi = get_modus_operandi(question)

        if False: #modus_operandi != 'The answer is very specific':

            all_chunks = index.query(
                vector=[0 for x in range(1536)],
                filter={
                    "document": {"$in": list(map(str, json.loads(docids)))},
                    "dev": {"$eq": not settings.IS_PRODUCTION},
                },
                include_values=True,
                top_k=500
            )
            average_embedding = np.mean([v['values'] for v in all_chunks['matches']], axis=0)

            similar = index.query(
                vector=list(average_embedding),
                filter={
                    "document": {"$in": list(map(str, json.loads(docids)))},
                    "dev": {"$eq": not settings.IS_PRODUCTION},
                },
                include_metadata=True,
                top_k=5
            )

            # the following code should be abstracted. since it's written twice. I wasn't sure if   
            # there was a reason for organizing it this way, so I left it how it was.
            
            text_to_summarize = list(map(matches_to_text, similar['matches']))

            text = ""
            for chunk in text_to_summarize:
                text += chunk+"\n"

            prompt = text + f'QUESTION: {question}'

            print(prompt)

            messages.append([0, prompt])

            def zero_or_one(x):
                if x == 0:
                    return "user"
                return "assistant"

            messagestochat = [{'role': zero_or_one(x[0]), 'content': x[1]} for x in messages]
            
            answer = gpt3_3turbo_completion(messagestochat)
            # messages.append([1, answer])

            # update the qa object and save it
            qa.docids = docids
            qa.user_id = user_id
            qa.feedback = feedback
            qa.answer = answer
            qa.txttosummarize = text
            qa.save()

            # update the thread object and save it
            #qaid = qa.id
            #thread.add_qamodel(qaid)
            # thread.promptmessages = json.dumps(messages)
            thread.save()

            return JsonResponse({'answer': answer}, status=200)
        
        # elif modus_operandi == 'The answer is very specific':
        # TODO: save the question embeddings for future use
        # if is_overview is False
        if is_overview is False:
            # response = openai.Embedding.create(input=question, engine='text-embedding-ada-002')
            # question_embedding = response['data'][0]['embedding']

            # similar = index.query(
            #     vector=question_embedding,
            #     filter={
            #         "document": {"$in": list(map(str, json.loads(docids)))},
            #         "dev": {"$eq": not settings.IS_PRODUCTION},
            #     },
            #     top_k=5,
            #     include_metadata=True
            # )

            # # print(similar)

            # text_to_summarize = list(map(matches_to_text, similar['matches']))
            relevant = retriever.get_relevant_documents(question, doc_ids=json.loads(docids))
            text_to_summarize = list(map(lambda x: x.page_content, relevant))
            
        else:
            # get the first 2 chunks
            text_to_summarize = json.loads(Document.objects.get(id=json.loads(docids)[0]).document_chunks)[:2]

        text = ""
        for chunk in text_to_summarize:
            text += chunk+"\n"

        prompt = text + f"QUESTION: {question} \n Provide 3 follow up questions without answers for the user. Encapsulate each question between curly braces.\nAnswer:"

        print(prompt)

        messages.append([0, prompt])

    def zero_or_one(x):
        if x == 0:
            return "user"
        return "assistant"

    messagestochat = [{'role': zero_or_one(x[0]), 'content': x[1]} for x in messages]
    print(messagestochat)
    #if json.loads(docids)[0] == 458:
    #    answer = gpt3_3turbo_completion(messagestochat, summarymodel="gpt-4")
    #    print("did summarization with gpt-4")
    qa.docids = docids
    qa.user_id = user_id
    qa.feedback = feedback
    qa.txttosummarize = text
    qa.save()
    stream = gpt3_3turbo_completion_stream(messagestochat, qa)
    thread.save()

    def stream_generator():
        for chunk in stream:
            # Encode each chunk as JSON
            yield chunk

    chunk_size = 32

    # return JsonResponse(data={'summary': summary, 'urls':s.urls, 'urlidx':s.urlidx, 'id': s.id, 'was_new':was_new}, status=200)
    response =  StreamingHttpResponse(stream_generator(), content_type='application/json')
    response.block_size = chunk_size

    return response
  
def get_recommendations(request):

    d = json.loads(request.body)
    docid = d.get('docid')

    # get the document
    doc = Document.objects.get(id=docid)

    # get the document's title
    title = doc.title

    # use google scholar to get the top 5 results
    results = google_scholar_scrape(title, num_result=5)

    toreturn = []
    for result in results:
        toreturn.append([results[result]['title'], results[result]['pdf_link'], results[result]['authors'], results[result]['year'], results[result]['publisher']])

    return JsonResponse({'detail':json.dumps(toreturn)}, status=200)

@csrf_exempt
@require_internal
def get_outline(request):

    d = json.loads(request.body)
    docid = d.get('docid')

    # get the document
    doc = Document.objects.get(id=docid)

    # take the first two chunks
    chunks = json.loads(doc.document_chunks)[:2]

    # get outline from doc
    outline = doc.outline

    if len(outline) > 0:
        return JsonResponse({'detail':outline}, status=200)

    # if the doc url is a youtube video
    # if 'youtube.com' in doc.url:
    #     generatedoutline = get_outline_from_text('\n'.join(json.loads(doc.document_chunks)[:5]))
    # # get the outline
    # else:
    generatedoutline = get_outline_from_text('\n'.join(chunks))

    # remove the '- ' from each line of the outline
    outlinelist = [x[2:] for x in generatedoutline.split('\n')]
    outlinelist = [x.split(': ') for x in outlinelist if x != '']

    # save the outline in the document
    doc.outline = json.dumps(outlinelist)
    doc.save()

    # return the outline
    return JsonResponse({'detail':json.dumps(outlinelist)}, status=200)

def matches_to_text(result):

    # print(result)
    document_id = int(result['metadata']['document'])
    # print(document_id)
    try:
        chunk_number = int(result['metadata']['chunk'])
    except:
        return ""

    try:
        return json.loads(Document.objects.get(id=document_id).document_chunks)[chunk_number], document_id
    except:
        return None

@csrf_exempt
@require_internal
# TODO: change the name from summarize_document to something that makes more sense, e.g. answer_question
def summarize_document_stream(request):

    d = json.loads(request.body)

    threadid = d.get('threadid')
    question = d.get('question')
    docids = d.get('docids') # list of docids to search through
    user_id = d.get('user')
    special_id = d.get('specialID')

    is_overview = False

    response_type = 'simple and concise'
    if question == "Overview":
        is_overview = True
        response_type = "overview: short and quick, 3-5 lines."

    print("special_id", special_id)
    if special_id:
        response_type = special_prompts[special_id]
    
    ## vector search here, only through the docids
    ## generate response and return it

    # load thread
    thread = Thread.objects.get(id=threadid)

    # load the messages
    messages = thread.get_promptmessages()

    associated_qas = sorted(list(QA.objects.filter(thread=thread)), key = lambda x: x.index)

    # create a new QA object
    qa = QA.objects.create(thread=thread, question=question, index=len(associated_qas))

    # create a new feedback model
    feedback = FeedbackModel.objects.create(qa=qa)
    
    # TODO: save the question embeddings for future use
    # if is_overview is False
    if is_overview==False:

        response = openai.Embedding.create(input=question, engine='text-embedding-ada-002')
        question_embedding = response['data'][0]['embedding']

        similar = index.query(
            vector=question_embedding,
            filter={
                "document": {"$in": list(map(str, json.loads(docids)))},
                "dev": {"$eq": not settings.IS_PRODUCTION},
            },
            top_k=5,
            include_metadata=True
        )
        # print(similar)

        text_to_summarize = list(map(matches_to_text, similar['matches']))
        text_to_summarize = [x for x in text_to_summarize if x is not None]
        print(text_to_summarize)
        text = [x[0] for x in text_to_summarize if x is not None]
        docids = [x[1] for x in text_to_summarize if x is not None]
    else:
        # get the first 2 chunks
        text_to_summarize = json.loads(Document.objects.get(id=json.loads(docids)[0]).document_chunks)[:3]
        print(text_to_summarize)
        text = text_to_summarize
        docids = [json.loads(docids)[0]]

    # dict so that we can map docids to numbers
    dociddict = {}
    i = 1
    for docid in docids:
        if docid not in dociddict:
            dociddict[docid] = i
            i += 1

    references = []
    for docid in dociddict:
        references.append(Document.objects.get(id=docid).url)
    
    print("references", references)

    # print(text_to_summarize)
    text = [x for x in text if x != '']
    messages = get_messages(question=question, listoftexts=text, listofcorrespondingdocids=docids, dociddict=dociddict, responsetype=response_type)

    def zero_or_one(x):
        if x == 0:
            return "user"
        return "assistant"

    messagestochat = [{'role': zero_or_one(x[0]), 'content': x[1]} for x in messages]
    # print(messagestochat)
    #if json.loads(docids)[0] == 458:
    #    answer = gpt3_3turbo_completion(messagestochat, summarymodel="gpt-4")
    #    print("did summarization with gpt-4")
    qa.docids = docids
    qa.user_id = user_id
    qa.feedback = feedback
    qa.txttosummarize = json.dumps(text_to_summarize)
    qa.save()
    stream = gpt3_3turbo_completion_stream(messagestochat, qa)
    # stream = queryresponsepipeline(question=question, listoftexts=text_to_summarize, qa=qa, response_type=response_type)
    thread.save()

    def stream_generator():
        answer = ''
        # answer
        for chunk in stream:
            # Encode each chunk as JSON
            if chunk[0]==1:
                answer = json.loads(chunk[1])['data']
            yield chunk[1]
        # references
        yield json.dumps({'finalresponse': 2, 'urls':['>>>PART<<<']})
        yield '\n'
        yield json.dumps({'finalresponse': 2, 'urls': references})
        yield '\n'
        # questions
        yield json.dumps({'finalresponse': 2, 'urls':['>>>PART<<<']})
        yield '\n'
        questionsgenerator = questionspipeline(answer, qa)
        # yield 'here'
        for chunk in questionsgenerator:
            yield chunk
        # ending message
        yield json.dumps({'finalresponse': 4, 'detail':'>>>END<<<'})
        yield '\n'

    chunk_size = 32

    # return JsonResponse(data={'summary': summary, 'urls':s.urls, 'urlidx':s.urlidx, 'id': s.id, 'was_new':was_new}, status=200)
    response =  StreamingHttpResponse(stream_generator(), content_type='application/json')
    response.block_size = chunk_size

    return response