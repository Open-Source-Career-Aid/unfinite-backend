import openai
import os
import re
import json
import PyPDF2
import io
import numpy as np
import requests

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

def gpt3_3turbo_completion(prompt, summarymodel='gpt-3.5-turbo'):

	messages = [{
		"role": "user",
		"content": "You are an expert summarizer."
	},
	{
		"role": "user",
		"content": "Please summarize the following texts into a detailed and coherent answer to the question."
	},
	{
		"role": "user",
		"content": """Instructions: 
	1. Structure the answer into multiple paragraphs where necessary."""
	},
	{
		"role": "user",
		"content": prompt
	}]

	temperature = 0.0
	max_length = 350
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

def similarity(v1, v2):  # return dot product of two vectors
	return np.dot(v1, v2)

def search_index(text, data, count=10):
	vector = gpt3_embedding(text)
	scores = list()
	for i in data:
		score = similarity(vector, i['vector'])
		#print(score)
		scores.append({'filename': i['filename'], 'page_num': i['page_num'], 'score': score})
	ordered = sorted(scores, key=lambda d: d['score'], reverse=True)
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