# embeds the given document
from django.core.management.base import BaseCommand, CommandError
from dochandler.models import Document
import pickle


class Command(BaseCommand):
    def handle(self, **options):
        docs = Documents.objects.all()
        data = {}
        for doc in docs:
            try:
                data[doc.id] = doc.num_chunks 
            except Exception:
                # some failure, means doc isn't uploaded, which is fine.
                continue
        print(f"Got information from {len(data)} documents.")

        with open('documents.pickle', 'wb') as f:
            pickle.dump(data, f, protocol=pickle.HIGHEST_PROTOCOL)