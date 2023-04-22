# this script takes a csv of arxiv papers, in the format returned by the arxivscraper
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
from dochandler.models import Document
from django.conf import settings
import pandas, pinecone

pinecone.init(api_key=settings.PINECONE_KEY, environment="us-central1-gcp")
index = pinecone.Index('unfinite-embeddings')

class Command(BaseCommand):
    def handle(self, **options):
        csv_fname = input("Filename (with extension):\n-> ")
        df = pandas.read_csv(csv_fname).iloc[::-1]
        limit = int(input("Number of documents to index (starting from top of CSV):\n-> "))
        done = 0
        for row in df.itertuples():
            if done >= limit: break
            try:
                Document.objects.get(url=row[-1])
                print(f"'{row[3]}' already indexed")
            except Exception:
                print(f"indexing '{row[3]}'")
                d = Document.objects.create(url=row[-1], title=row[3])
                d.save()
                try: 
                    d.scrape()
                except Exception:
                    continue
                try:
                    d.embed(index)
                    done += 1
                except Exception:
                    print("Tried to embed too long of a chunk")
