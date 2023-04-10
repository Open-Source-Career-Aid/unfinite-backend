from django.db import models
from django.utils import timezone
import json, itertools, openai
from .processpdf import gpt3_embedding
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY

def openai_to_pinecone(embedding, document_id):
    page = embedding['index']
    vec = embedding['embedding']

    return (f"{document_id}-{page}", vec, {'document': str(document_id), 'page': str(page), 'dev': False})

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
