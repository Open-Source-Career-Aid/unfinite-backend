import openai
import os
import re
import json
import PyPDF2
import io
import numpy as np
import requests
from .keyphrasing.kpextraction import *
from .langchainChains import *

# enter openai api key here

def extractpdf(url):
    """
    A function that extracts text from a PDF file given a URL.
    """
    # Get the PDF file from the URL
    response = requests.get(url)
    
    # Read the PDF file
    pdf_file = io.BytesIO(response.content)
    
    # Create a PDF reader
    pdf_reader = PyPDF2.PdfFileReader(pdf_file)
    
    # Get the number of pages
    num_pages = pdf_reader.numPages
    
    # Initialize a list to store the text
    pdf_text = []
    
    # Loop through each page and extract the text
    for page in range(num_pages):
        page_obj = pdf_reader.getPage(page)
        pdf_text.append(page_obj.extractText())
    
    pdf_text = [clean_pdf_text(page) for page in pdf_text]
    
    return pdf_text

# takes in text and returns a vector embedding, i.e. a list of n-dimensions
def gpt3_embedding(content, engine='text-embedding-ada-002'):
	response = openai.Embedding.create(input=content,engine=engine)
	vector = response['data'][0]['embedding']  # this is a normal list
	return vector

def clean_pdf_text(pdf_text):
	"""
	A function that cleans up unnecessary characters and spaces from a PDF text string.
	"""
	# Remove newlines and multiple spaces
	pdf_text = re.sub(r'\s+', ' ', pdf_text.replace('\n', ' ')).strip()

	# Add space between number and following text
	pdf_text = re.sub(r'(\d)(\D)', r'\1 \2', pdf_text)

	# Remove non-alphanumeric characters and punctuations
	pdf_text = re.sub(r'[^\w\s]', '', pdf_text)

	return pdf_text

def gpt3_3turbo_completion(messages, summarymodel='gpt-3.5-turbo'):

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

def gpt3_3turbo_completion_stream(messages, qa, summarymodel='gpt-3.5-turbo'):

	temperature = 0.2
	max_length = 750
	top_p = 1.0
	frequency_penalty = 0.2
	presence_penalty = 0.1

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
	
	#yield from stream

	finalsummary = ''

	prefix = ''

	for chunk in stream:

		try:
			if chunk.choices[0].finish_reason == 'stop':
				questions = re.findall(r'\{(.*?)\}', finalsummary)
				questions = ['{'+x+'}' for x in questions]
				# text is now the answer without the questions
				text = re.sub(r'\{(.*?)\}', '', finalsummary)
				text = match_keyphrases(text)
				# remove unnecessary newlines
				answer = re.sub(r'\n\n+', '\n\n', text)
				answer = '\n\n'.join([x for x in answer.split('\n') if x != ''])
				qa.answer = answer
				# save questions in the qa where questions are enclosed in {}
				qa.relevantquestions = json.dumps(questions)
				qa.save()
				print('this is being returned')
				yield (1, json.dumps({"finalresponse": 1, "data": answer}))
				yield (0, '\n')
				continue
			if chunk.choices[0].delta.role == 'assistant':
				continue
		except:
			c = chunk.choices[0].delta.content
			# if '{' in c:
			# 	t = c[:c.index('{')]
			# 	finalsummary += t
			# 	yield t
			# 	yield '\n'
			# 	raise StopIteration
			finalsummary += c

		# print(chunk.choices[0].delta.content)
		yield (0, json.dumps({'data':chunk, 'finalresponse':0}))
		yield (0, '\n')
		# response.flush()

def similarity(v1, v2):  # return dot product of two vectors
	return np.dot(v1, v2)

def search_index(text, data, count=10):
	vector = gpt3_embedding(text)
	scores = list()
	# perform the vector search
	return ordered[0:count]

def embedpdf(url):
    """
    A function that embeds the text from a PDF file.
    """
    # Get the number of pages
    pdf_text = extractpdf(url)
    num_pages = len(pdf_text)
    
    # Initialize a list to store the embeddings
    embeddings = []
    
    # Loop through each page and embed the text
    for page in range(num_pages):
        embeddings.append(gpt3_embedding(pdf_text[page]))
    
    return embeddings