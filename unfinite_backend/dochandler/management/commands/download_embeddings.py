# embeds the given document
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from dochandler.models import Document
from django.conf import settings
import pinecone, pickle

def batches(iterable, batch_size):
    it = iter(iterable)
    batch = tuple(itertools.islice(it, batch_size))
    while batch:
        yield batch
        batch = tuple(itertools.islice(it, batch_size))


pinecone.init(api_key=settings.PINECONE_KEY, environment="us-central1-gcp")
index = pinecone.Index('unfinite-embeddings')

class Command(BaseCommand):
    def handle(self, **options):
        docs = Documents.objects.all()
        ids = []
        for doc in docs:
            if doc.num_chunks is not None:
                ids.extend(list(map(lambda x: f"{doc.id}-{x}", range(0, doc.num_chunks))))

        print(f"Number of ids: {len(ids)}")
        data = {}

        for batch in batches(ids, 100):
            vecs = index.fetch(batch)['vectors']
            data.update(vecs)

        with open('vectors.pickle', 'wb') as f:
            pickle.dump(a, f, protocol=pickle.HIGHEST_PROTOCOL)
        

        

        
        
