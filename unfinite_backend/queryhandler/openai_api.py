import openai
from django.http import JsonResponse
from django.conf import settings
from .models import *

from django.apps import apps
Query = apps.get_model('api', 'Query')
Feedback = apps.get_model('api', 'Feedback')
SERP = apps.get_model('api', 'SERP')
SERPItem = apps.get_model('api', 'SERPItem')

def parse(str):
    return list(map(lambda x: x.strip().strip('.'), str.strip().split(';')))

def query_generation_model(model, query_topic, user_id):

    previous_queries = Query.objects.filter(query_text=query_topic)
    if len(previous_queries) == 1:
        print('existing query found')
        response_topics = parse(previous_queries[0].skeleton)
        return JsonResponse(data={'skeleton': response_topics}, status=200)

    openai.api_key = settings.OPENAI_API_KEY

    prompt = f"""List, as key-phrases, the most necessary sub-topics required to learn about '{query_topic}', 
               in order of importance. The following output is semicolon-seperated:"""
    
    temperature = 0.2
    max_tokens = 100
    model = 'text-davinci-003'

    # try:
    #     response = openai.Completion.create(model=model, prompt=prompt, temperature=temperature, max_tokens=max_tokens)
    # except openai.error.RateLimitError as e:
    #     print("OpenAI API rate limit error! See below:")
    #     print(e)
    #     return JsonResponse(data={'detail': 'Server error.'}, status=503)
    # except Exception as e:
    #     print("Unknown OpenAI API error! See below:")
    #     print(e)
    #     return JsonResponse(data={'detail': 'Unknown server error.'}, status=500)

    # response['choices'][0]['text']
    response = {}
    response['choices'] = [{'text': "\n\nCancer diagnosis; Cancer staging; Cancer treatment options; Surgery; Radiation therapy; Chemotherapy; Targeted therapy; Immunotherapy; Hormone therapy; Clinical trials; Palliative care; Nutrition and exercise; Coping with cancer."}]
    response['usage'] = {'total_tokens':69}
    response_topics = list(map(lambda x: x.strip().strip('.'), response['choices'][0]['text'].strip().split(';')))

    
    q = Query(user_id=user_id, query_text=query_topic, num_tokens=response['usage']['total_tokens'], skeleton=response['choices'][0]['text'])
    q.save()

    return JsonResponse(data={'skeleton': response_topics}, status=200)