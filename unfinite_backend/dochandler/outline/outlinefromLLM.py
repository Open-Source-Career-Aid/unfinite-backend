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
    
	# remove the '- ' from each line of the outline
    outlinelist = [x[2:] for x in outline.split('\n')]
    outlinelist = [x.split(': ') for x in outlinelist if x != '']

    return outline

def get_outline_from_pdf_chunks(pdf_chunks):

	abstract = ''

	for chunk in pdf_chunks:
		# Get abstract
		if "abstract" in chunk.lower():
			abstract_start = chunk[
				chunk.lower().index("abstract"):
			]
			try:
				abstract = abstract_start[
					:abstract_start.lower().index(".\n")
				]
			except:
				abstract = abstract_start
		
		if abstract != '':
			break
	
	# For get all lines which might be headers
	poss_outline_lines = []
	for chunk in pdf_chunks:
		for line in chunk.split('\n'):
            # Shorten each line
			line = line[:100].lower()
			if (10 < len(line) < 100) and (0 < len(line.split(" ")) < 5):
				if sum([c.isalpha() for c in line]) / len(line) > 0.7\
                    and not any([x in line.replace(".", "") for x in ("et al", "@")]):
					poss_outline_lines.append(line)
	
	poss_outline_lines = [x for x in poss_outline_lines if poss_outline_lines.count(x) == 1]

    # Generate prompt
	lines = '\n'.join(poss_outline_lines[:80])
    
    #poop

	prompt = f"""
    Here is an abstract and rough extraction of lines from a research paper which may or may not be a section header.
    Remember that not all lines are relevant for an outline so ignore some!

    Abstract:
    {abstract}

    Possible outline lines:
    {lines}

    Give me a concise outline of the paper with just a few words per line. Just respond with the outline.
    """.strip("\n")

	response = openai.ChatCompletion.create(
      model="gpt-3.5-turbo",
      messages=[
          {"role": "system", "content": "You are a helpful research paper analysis assistant."},
          {"role": "user", "content": prompt}
      ]
    )

	rawoutline = response["choices"][0]["message"]["content"]

	# break into lines
	outlinelist = rawoutline.split('\n')

	# remove any numbering or bullets and strip whitespace
	outlinelist = [' '.join(x.split(' ')[1:]) for x in outlinelist]

	# remove any empty lines
	outlinelist = [x for x in outlinelist if x != '']

	outline = [[x, x] for x in outlinelist]

	return outline