import openai, json
from django.http import JsonResponse
from django.conf import settings
from .models import *

from django.apps import apps
Query = apps.get_model('api', 'Query')

def parse(str):
    # takes the output of an LLM and parses it, assumes str is semicolon separated 
    return list(map(lambda x: x.strip().strip('.'), str.strip().split(';')))

def query_generation_model(model, query_topic, user_id):
    # takes a topic to query (query_topic) as a string and either returns an existing 
    # skeleton, or requests OpenAI's <model> to come up with one. Requires user_id
    # in order to instantiate a new Query object...

    # TODO: this is messy code, make it nice

    # checking for existing queries with identical query_text
    previous_queries = Query.objects.filter(query_text=query_topic)
    if len(previous_queries) == 1:
        #print('existing query found')
        response_topics = parse(previous_queries[0].skeleton)
        # increment the found Query's num_searched field.
        previous_queries[0].searched()
        return response_topics, previous_queries[0], False

    # idk why this is here, might be able to move it out of the function
    openai.api_key = settings.OPENAI_API_KEY

    # the prompt to be used to generate the skeleton/roadmap
    prompt = f"""List, as key phrases, the most necessary topics pertaining to the following guiding question: '{query_topic}'. The following is semicolon-separated and ranked in order of importance:"""
    
    # model decoding parameters
    temperature = 0.2
    max_tokens = 250
    model = 'text-davinci-003'

    # making API request and error checking
    try:
        response = openai.Completion.create(model=model, prompt=prompt, temperature=temperature, max_tokens=max_tokens)
    except openai.error.RateLimitError as e:
        print("OpenAI API rate limit error! See below:")
        print(e)
        return None, None
    except Exception as e:
        print("Unknown OpenAI API error! See below:")
        print(e)
        return None, None

    # response = {}
    # response['choices'] = [{'text': "\n\nCancer diagnosis; Cancer staging; Cancer treatment options; Surgery; Radiation therapy; Chemotherapy; Targeted therapy; Immunotherapy; Hormone therapy; Clinical trials; Palliative care; Nutrition and exercise; Coping with cancer."}]
    # response['usage'] = {'total_tokens':69}
    
    response_topics = json.dumps(parse(response['choices'][0]['text']))

    # new Query in database!
    q = Query(user_id=user_id, query_text=query_topic, num_tokens=response['usage']['total_tokens'], skeleton=response_topics)
    q.save() # always do this!

    return response_topics, q, True