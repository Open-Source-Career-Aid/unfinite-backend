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

## ==================== FOR ANSWER WITH CITATIONS ==================== ##

system_message_with_response_type = """Given the following extracted parts from multiple documents question and a response type, create a final answer with sources cited in the form [#] in the response. 
If you don't know the answer, just say that you don't know. Don't try to make up an answer.
ALWAYS cite the sources in your answer.
========="""

human_message_with_response_type = """{texts}
=========
QUESTION: {question}
RESPONSE TYPE: {responsetype}
=========
FINAL ANSWER WITH IN TEXT CITATIONS OF THE FORM [#]:
========="""

textitem = '''CONTENT: {text}
SOURCE: {source}'''

## ==================== XXX ==================== ##

## ==================== FOR FOLLOW UP QUESTIONS ==================== ##

system_message_for_followup = """You are an expert socratic style teacher. Given the following text, generate three SHORT follow up questions for the user to explore the topic further."""

human_message_for_followup = """{text}
=========
FOLLOW UP QUESTIONS:
========="""

## ==================== XXX ==================== ##

def get_messages(question, listoftexts, listofcorrespondingdocids, dociddict, responsetype='simple and concise'):

    messages = []

    messages.append([1, system_message_with_response_type])

    texts = ''
    for text, id in zip(listoftexts, listofcorrespondingdocids):
        texts += textitem.replace('{text}', text).replace('{source}', f'#{dociddict[id]}')
    
    messages.append([0, human_message_with_response_type.format(texts=texts, question=question, responsetype=responsetype)])

    return messages

def get_followup_messages(text):

    messages = []

    messages.append([1, system_message_for_followup])

    messages.append([0, human_message_for_followup.format(text=text)])

    return messages

def questionspipeline(text, qa, summarymodel='gpt-3.5-turbo'):

    print("starting questions pipeline")

    # stream the response
    temperature = 0.2
    max_length = 128
    top_p = 1.0
    frequency_penalty = 0.2
    presence_penalty = 0.1

    messages = get_followup_messages(text)

    def zero_or_one(x):
        if x == 0:
            return "user"
        return "assistant"

    messagestochat = [{'role': zero_or_one(x[0]), 'content': x[1]} for x in messages]

	# making API request and error checking
    print("making API request")
    try:
        stream = openai.ChatCompletion.create(
            model=summarymodel, 
            messages=messagestochat, 
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

    print('here')
    questions = ''
    for chunk in stream:

        try:
            if chunk.choices[0].finish_reason == 'stop':
                qa.relevantquestions = questions
                qa.save()
                continue
        except:
            c = chunk.choices[0].delta.content
            questions += c

		# print(chunk.choices[0].delta.content)
        yield json.dumps({'data':chunk, 'finalresponse':3})
        yield '\n'
		# response.flush()