import openai, json
from django.http import JsonResponse
from django.conf import settings
from .models import *

from django.apps import apps
Query = apps.get_model('api', 'Query')
Relevantquestions = apps.get_model('api', 'Relevantquestions')

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

def questions_generation_model(model, idx, query_text):
    
    previous_relevant_questions = Relevantquestions.objects.filter(idx=idx, query__query_text=query_text)
    if len(previous_relevant_questions) == 1:
        #print('existing relevant questions found')
        response_questions = parse(previous_relevant_questions[0].questions)
        # increment the found Relevantquestions's num_searched field.
        previous_relevant_questions[0].searched()
        return response_questions, previous_relevant_questions[0], False
    
    query = Query.objects.filter(query_text=query_text)[0]
    topic_text = json.loads(query.skeleton)[idx]
    # if len(topic) == 0:
    #     topic = Topic(topic_text=topic_text, query=query, topic_index_in_query=topic_index_in_query)
    #     topic.save()
    
    # idk why this is here, might be able to move it out of the function
    openai.api_key = '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'

    prompt = f"user prompt: {topic_text} in {query_text}"

    messages = [{
        "role": "user",
        "content": "You are an expert learning designer."
    },
    {
        "role": "user",
        "content": "Take in the user prompt, and break it down into questions to guide the user's learning, with no preamble."
    },
    {
        "role": "assistant",
        "content": "What kind of questions?"
    },
    {
        "role": "user",
        "content": "The questions should be in a logical order and be specific to the user prompt."
    },
    {
        "role": "assistant",
        "content": "Okay, and how specific should I go?"
    },
    {
        "role": "user",
        "content": "Try to capture all the learnable information about the user prompt in as little number questions as possible."
    },
    {
        "role": "assistant",
        "content": "Okay, what format should I out put in?"
    },
    {
        "role": "user",
        "content": "Seperate questions with a semi-colon, don't use any lists."
    },
    {
        "role": "user",
        "content": prompt
    }]

    temperature = 0.2
    max_length = 150
    top_p = 1.0
    frequency_penalty = 0.3
    presence_penalty = 0.0

    try:
        response = openai.ChatCompletion.create(
            model=model, 
            messages=messages, 
            temperature=temperature, 
            max_tokens=max_length, 
            top_p=top_p, 
            frequency_penalty=frequency_penalty, 
            presence_penalty=presence_penalty)
    except openai.error.RateLimitError as e:
        print("OpenAI API rate limit error! See below:")
        print(e)
        return None, None, None
    except Exception as e:
        print("Unknown OpenAI API error! See below:")
        print(e)
        return None, None, None

    response_questions = json.dumps(parse(response['choices'][0]['message']['content']))

    # new Relevantquestions in database!
    q = Relevantquestions(idx=idx, query=query, questions=response_questions, generation_prompt=prompt)
    q.save() # always do this!

    return response_questions, q, True