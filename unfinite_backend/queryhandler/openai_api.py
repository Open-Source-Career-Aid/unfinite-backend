import openai
from django.http import JsonResponse
from django.conf import settings

def query_generation_model(model, query_topic):

    openai.api_key = settings.OPENAI_API_KEY

    prompt = f"""List, as key-phrases, the most necessary sub-topics required to learn about '{query_topic}', 
               in order of importance. The following output is semi-colon seperated:"""
    
    temperature = 0.2
    max_tokens = 100
    model = 'text-davinci-003'

    try:
        response = openai.Completion.create(model=model, prompt=prompt, temperature=temperature, max_tokens=max_tokens)
    except openai.error.RateLimitError as e:
        print("OpenAI API rate limit error! See below:")
        print(e)
        return JsonResponse(data={'detail': 'Server error.'}, status=503)
    except Exception as e:
        print("Unknown OpenAI API error! See below:")
        print(e)
        return JsonResponse(data={'detail': 'Unknown server error.'}, status=500)

    response_topics = list(map(lambda x: x.strip(), response['choices']['text'].strip().split(';')))

    return JsonResponse(data={'skeleton': response_topics}, status=200)