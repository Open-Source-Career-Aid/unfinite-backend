import openai

openai.api_key = "sk-<your key here>"

messages = [[0, '''Use the abstract to generate a roadmap of topics. Use keyphrases, keep the topics short, and follow a mastery learning plan. Generate short keyphrases for display in a key: value pair format.

Example: LangChain is a framework for developing applications powered by language models. We believe that the most powerful and differentiated applications will not only call out to a language model via an API, but will also:

Be data-aware: connect a language model to other sources of data

Be agentic: allow a language model to interact with its environment

The LangChain framework is designed with the above principles in mind.

This is the Python specific portion of the documentation. For a purely conceptual guide to LangChain, see here. For the JavaScript documentation, see here.
"- Langchain: What is Langchain?
- Langchain principles: What are the Principles of the Langchain Framework?"''']]

def gpt3_5turbo_completion(messages, summarymodel='gpt-3.5-turbo'):

	temperature = 0.2
	max_length = 750
	top_p = 1.0
	frequency_penalty = 0.2
	presence_penalty = 0.1

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


def get_outline_from_text(text, messages=messages):
	
    messagestemp = messages
    messagestemp.append([1, text])
    
    print(messagestemp)

    def zero_or_one(x):
        if x == 0:
            return "user"
        return "assistant"

    messagestochat = [{'role': zero_or_one(x[0]), 'content': x[1]} for x in messagestemp]

    outline = gpt3_5turbo_completion(messagestochat)

    return outline