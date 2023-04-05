from django.http import StreamingHttpResponse
import openai

openai.api_key = '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'

def gpt3_3turbo_completion(messages, summarymodel):
    temperature = 0.2
    max_length = 500
    top_p = 1.0
    frequency_penalty = 0.0
    presence_penalty = 0.0

    # making API request and error checking
    print("making API request")
    try:
        response = openai.ChatCompletion.create(
            model=summarymodel, 
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
    
    return response['choices'][0]['message']['content']

def gpt3_3turbo_completion_withstream(messages, summarymodel):
    temperature = 0.2
    max_length = 500
    top_p = 1.0
    frequency_penalty = 0.0
    presence_penalty = 0.0

    # making API request and error checking
    print("making API request")
    try:
        stream = openai.ChatCompletion.create(
            model=summarymodel, 
            messages=messages, 
            temperature=temperature, 
            max_tokens=max_length, 
            top_p=top_p, 
            frequency_penalty=frequency_penalty, 
            presence_penalty=presence_penalty,
            stream=True)
    except openai.error.RateLimitError as e:
        print("OpenAI API rate limit error! See below:")
        print(e)
        return None, None, None
    except Exception as e:
        print("Unknown OpenAI API error! See below:")
        print(e)
        return None, None, None
    
    yield from stream
    
    # for chunk in response:
    #     if chunk['object'] == 'text_completion':
    #         yield chunk['choices'][0]['text']

    # response = StreamingHttpResponse(stream, content_type="text/event-stream")
    # response['Cache-Control'] = 'no-cache'
    # return response
    
    # return response['choices'][0]['message']['content']