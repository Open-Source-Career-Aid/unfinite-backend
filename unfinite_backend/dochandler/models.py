from django.db import models
from django.utils import timezone
import json, itertools, openai
import uuid
from .processpdf import gpt3_embedding
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY
devstr = '' if settings.IS_PRODUCTION else 'dev-'

# 0 = user, 1 = assistant
messages = [(0, "You are an expert summarizer and teacher."), (0, "Please summarize the following texts into a short and coherent answer to the question. Make the answer accessible, break it down into points and keep paragraphs short where you can."),
            (0, """Instructions: 
	1. Structure the answer into multiple paragraphs where necessary.
    2. When the answer is a list of things, always produce a list, not paragraph.
    3. Highlight the answer to the query in the text between ``````.""")]

def openai_to_pinecone(embedding, document_id):
    page = embedding['index']
    vec = embedding['embedding']

    return (f"{devstr}{document_id}-{page}", vec, {'document': str(document_id), 'page': str(page), 'dev': not settings.IS_PRODUCTION})

def chunks(iterable, batch_size=100):
    it = iter(iterable)
    chunk = tuple(itertools.islice(it, batch_size))

    while chunk:
        yield chunk
        chunk = tuple(itertools.islice(it, batch_size))

# Create your models here.
class Document(models.Model):
    url = models.URLField(max_length=400, unique=True)
    user = models.ForeignKey('api.UnfiniteUser', on_delete=models.SET_NULL, null=True)
    document_pages = models.TextField() # JSON.dumps of list of page text
    num_pages = models.IntegerField()

    created = models.DateTimeField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(Document, self).save(*args, **kwargs)

    def embed(self, index):

        page_texts = json.loads(self.document_pages)
        response = openai.Embedding.create(input=page_texts,engine='text-embedding-ada-002')
        embeddings = response['data']

        f = lambda x: openai_to_pinecone(x, self.id)

        to_upsert = map(f, embeddings)

        for chunk in chunks(to_upsert):
            print(index.upsert(chunk))

# Model - Thread | Contains - unique id, a list of q/a models, userid foreign key, prompt messages, time stamp.
class Thread(models.Model):

    id = models.TextField(primary_key=True, default=uuid.uuid4().hex[:16], editable=False)
    qamodels = models.TextField(default=json.dumps([])) # JSON.dumps of list of qamodel objects
    promptmessages = models.TextField(default=json.dumps([]), blank=True, null=True) # JSON.dumps of list of prompt messages, e.g. [('user', 'message'), ('assistant', 'message')]
    user = models.ForeignKey('api.UnfiniteUser', on_delete=models.SET_NULL, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.updated = timezone.now()
        self.promptmessages = json.dumps(messages)
        return super(Thread, self).save(*args, **kwargs)
    
    def get_qamodels(self):
        return json.loads(self.qamodels)
    
    def get_promptmessages(self):
        return json.loads(self.promptmessages)
    
    def set_promptmessages(self, promptmessages):
        self.promptmessages = json.dumps(promptmessages)
    
    def set_qamodels(self, qamodels):
        self.qamodels = json.dumps(qamodels)

    def add_qamodel(self, qamodel):
        qamodels = self.get_qamodels()
        qamodels.append(qamodel)
        self.set_qamodels(qamodels)

# Model - Feedback | Contains - unique id, object id, name of the model that it is connected to, thumbs, feedback text, time stamp, user id.
class FeedbackModel(models.Model):

    id = models.AutoField(primary_key=True)
    thumbs = models.IntegerField(default=0) # 0 = neutral, 1 = up, -1 = down
    textfeedback = models.TextField(default="", blank=True, null=True)
    created = models.DateTimeField()

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        return super(FeedbackModel, self).save(*args, **kwargs)
    
    def get_thumbs(self):
        return self.thumbs
    
    def get_feedback(self):
        return self.feedback

    def set_thumbs(self, thumbs):
        self.thumbs = thumbs

    def set_feedback(self, feedback):
        self.feedback = feedback

# Model - QAModel | Contains - unique id, question, answer, document ids list, time stamp, feedback.
class QA(models.Model):
        
        id = models.AutoField(primary_key=True)
        question = models.TextField()
        answer = models.TextField()
        docids = models.TextField() # JSON.dumps of list of document ids
        created = models.DateTimeField()
        thread = models.ForeignKey('Thread', on_delete=models.SET_NULL, null=True)
        feedback = models.ForeignKey('FeedbackModel', on_delete=models.SET_NULL, null=True)
        user = models.ForeignKey('api.UnfiniteUser', on_delete=models.SET_NULL, null=True)
    
        def save(self, *args, **kwargs):
            ''' On save, update timestamps '''
            if not self.id:
                self.created = timezone.now()
            return super(QA, self).save(*args, **kwargs)
        
        def get_question(self):
            return self.question
        
        def get_answer(self):
            return self.answer
        
        def get_docids(self):
            return json.loads(self.docids)
        
        def set_question(self, question):
            self.question = question

        def set_answer(self, answer):
            self.answer = answer

        def set_docids(self, docids):
            self.docids = json.dumps(docids)
