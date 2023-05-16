from langchain.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

import os

from langchain.chat_models import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import BaseCallbackHandler
# django streaming response
from django.http import StreamingHttpResponse

os.environ["OPENAI_API_KEY"] = "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"

class MyCustomHandler(BaseCallbackHandler):

    # Get the channel layer
    channel_layer = get_channel_layer()

    room_group_name = 'chatroom'

    async def on_llm_new_token(self, token: str, **kwargs):

        print("\n\nTHIS SHIT IS REAL \n\n")

        await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': token
                }
            )
        
        async def chat_message(self, event):
            message = event['message']

            # Send message to WebSocket
            await self.send(text_data=json.dumps({
                'message': message
            }))

# create a chat model
chat = ChatOpenAI(temperature=0, streaming=True, callbacks=[MyCustomHandler()])

textitem = '''CONTENT: {text}
SOURCE: {source}'''

system_message = """Given the following extracted parts from multiple documents and a question, create a final answer with sources cited in the form [SOURCE] in the response. 
If you don't know the answer, just say that you don't know. Don't try to make up an answer.
ALWAYS cite the sources in your answer.
========="""

system_message_with_response_type = """Given the following extracted parts from multiple documents question and a response type, create a final answer with sources cited in the form [SOURCE] in the response. 
If you don't know the answer, just say that you don't know. Don't try to make up an answer.
ALWAYS cite the sources in your answer.
========="""

system_message_with_response_type_and_follow_up_questions = """Given the following extracted parts from multiple documents question and a response type, create a final answer with sources cited in the form [SOURCE] in the response. Also return 3 follow up questions for the user to explore.
If you don't know the answer, just say that you don't know. Don't try to make up an answer.
ALWAYS cite the sources in your answer.
========="""

human_message_with_response_type_and_follow_up_questions = """{texts}
=========
QUESTION: {question}
RESPONSE TYPE: {responsetype}
=========
FINAL ANSWER WITH IN TEXT CITATIONS OF THE FORM [SOURCE]:
=========
FOLLOW UP QUESTIONS:"""

human_message_with_response_type = """{texts}
=========
QUESTION: {question}
RESPONSE TYPE: {responsetype}
=========
FINAL ANSWER WITH IN TEXT CITATIONS OF THE FORM [SOURCE]:"""

human_message = """{texts}
=========
QUESTION: {question}
=========
FINAL ANSWER WITH IN TEXT CITATIONS OF THE FORM [SOURCE]:"""

#===================================================================================================

## normal cited response

# system_message_prompt = SystemMessagePromptTemplate.from_template(system_message)

# human_message_prompt = HumanMessagePromptTemplate.from_template(human_message)

# chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

# # format the prompt with input values
# prompt_value = chat_prompt.format_prompt(question="What is a sequential chain?", texts=texts)

#===================================================================================================

## analogy cited response

system_message_prompt = SystemMessagePromptTemplate.from_template(system_message_with_response_type)

human_message_prompt = HumanMessagePromptTemplate.from_template(human_message_with_response_type)

chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

# format the prompt with input values
# prompt_value = chat_prompt.format_prompt(question="Example code of a sequential Chain?", texts=texts, responsetype="pedagogical")

#===================================================================================================

## analogy cited response with follow up questions

# system_message_prompt = SystemMessagePromptTemplate.from_template(system_message_with_response_type_and_follow_up_questions)

# human_message_prompt = HumanMessagePromptTemplate.from_template(human_message_with_response_type_and_follow_up_questions)

# chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

# # format the prompt with input values
# prompt_value = chat_prompt.format_prompt(question="How does a blockchain work?", texts=texts, responsetype="pedagogical")

#===================================================================================================

# response = chat(prompt_value.to_messages())

# print(response.content)

def generate_cited_answer_stream(question, listoftexts, responsetype="Simple and Pedagogical"):

    texts = ""
    i = 0
    for text in listoftexts:
        i += 1
        texts += textitem.replace("{text}", text).replace("{source}", f'{i}') + "\n"

    system_message_prompt = SystemMessagePromptTemplate.from_template(system_message_with_response_type)
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_message_with_response_type)

    chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt, human_message_prompt])

    # format the prompt with input values
    prompt_value = chat_prompt.format_prompt(question=question, texts=texts, responsetype=responsetype)

    response = chat(prompt_value.to_messages())

    for chunk in response:

        yield chunk
    # return response

# if __name__ == '__main__':

#     question = "How does a blockchain work?"
#     texts = '''
#     CONTENT: What Is a Blockchain?
#     A blockchain is a distributed database or ledger shared among a computer network's nodes. They are best known for their crucial role in cryptocurrency systems for maintaining a secure and decentralized record of transactions, but they are not limited to cryptocurrency uses. Blockchains can be used to make data in any industry immutable—the term used to describe the inability to be altered.

#     Because there is no way to change a block, the only trust needed is at the point where a user or program enters data. This aspect reduces the need for trusted third parties, which are usually auditors or other humans that add costs and make mistakes.

#     Since Bitcoin's introduction in 2009, blockchain uses have exploded via the creation of various cryptocurrencies, decentralized finance (DeFi) applications, non-fungible tokens (NFTs), and smart contracts.
#     SOURCE: 1
#     CONTENT: 
#     Blockchain overview
#     Blockchain defined: Blockchain is a shared, immutable ledger that facilitates the process of recording transactions and tracking assets in a business network. An asset can be tangible (a house, car, cash, land) or intangible (intellectual property, patents, copyrights, branding). Virtually anything of value can be tracked and traded on a blockchain network, reducing risk and cutting costs for all involved.

#     Why blockchain is important: Business runs on information. The faster it’s received and the more accurate it is, the better. Blockchain is ideal for delivering that information because it provides immediate, shared and completely transparent information stored on an immutable ledger that can be accessed only by permissioned network members. A blockchain network can track orders, payments, accounts, production and much more. And because members share a single view of the truth, you can see all details of a transaction end to end, giving you greater confidence, as well as new efficiencies and opportunities.

#     Key elements of a blockchain
#     Distributed ledger technology
#     All network participants have access to the distributed ledger and its immutable record of transactions. With this shared ledger, transactions are recorded only once, eliminating the duplication of effort that’s typical of traditional business networks.

#     Immutable records
#     No participant can change or tamper with a transaction after it’s been recorded to the shared ledger. If a transaction record includes an error, a new transaction must be added to reverse the error, and both transactions are then visible.

#     Smart contracts
#     To speed transactions, a set of rules — called a smart contract — is stored on the blockchain and executed automatically. A smart contract can define conditions for corporate bond transfers, include terms for travel insurance to be paid and much more.
#     SOURCE: 2
#     CONTENT: Why is there so much hype around blockchain technology?
#     There have been many attempts to create digital money in the past, but they have always failed.

#     The prevailing issue is trust. If someone creates a new currency called the X dollar, how can we trust that they won't give themselves a million X dollars, or steal your X dollars for themselves?

#     Bitcoin was designed to solve this problem by using a specific type of database called a blockchain. Most normal databases, such as an SQL database, have someone in charge who can change the entries (e.g. giving themselves a million X dollars). Blockchain is different because nobody is in charge; it’s run by the people who use it. What’s more, bitcoins can’t be faked, hacked or double spent – so people that own this money can trust that it has some value.
#     SOURCE: 3
#     CONTENT: As explained by Wikipedia, “Blockchain was invented by Satoshi Nakamoto”—the pseudonym of an unknown person or persons—“in 2008 to serve as the public transaction ledger of the cryptocurrency bitcoin… [which] made it the first digital currency to solve the double-spending problem without the need of a trusted authority or central server.”

#     While blockchain is still largely confined to use in recording and storing transactions for cryptocurrencies such as Bitcoin, proponents of blockchain technology are developing and testing other uses for blockchain, including these:

#     Blockchain for payment processing and money transfers. Transactions processed over a blockchain could be settled within a matter of seconds and reduce (or eliminate) banking transfer fees.
#     Blockchain for monitoring of supply chains. Using blockchain, businesses could pinpoint inefficiencies within their supply chains quickly, as well as locate items in real time and see how products perform from a quality-control perspective as they travel from manufacturers to retailers.
#     Blockchain for digital IDs. Microsoft is experimenting with blockchain technology to help people control their digital identities, while also giving users control over who accesses that data.
#     Blockchain for data sharing. Blockchain could act as an intermediary to securely store and move enterprise data among industries.
#     Blockchain for copyright and royalties protection. Blockchain could be used to create a decentralized database that ensures artists maintain their music rights and provides transparent and real-time royalty distributions to musicians. Blockchain could also do the same for open source developers.
#     Blockchain for Internet of Things network management. Blockchain could become a regulator of IoT networks to “identify devices connected to a wireless network, monitor the activity of those devices, and determine how trustworthy those devices are” and to “automatically assess the trustworthiness of new devices being added to the network, such as cars and smartphones.”
#     Blockchain for healthcare. Blockchain could also play an important role in healthcare: “Healthcare payers and providers are using blockchain to manage clinical trials data and electronic medical records while maintaining regulatory compliance.”
#     SOURCE: 4
#     CONTENT: How Does Blockchain Work?
#     The name blockchain is hardly accidental: The digital ledger is often described as a “chain” that’s made up of individual “blocks” of data. As fresh data is periodically added to the network, a new “block” is created and attached to the “chain.” This involves all nodes updating their version of the blockchain ledger to be identical.

#     How these new blocks are created is key to why blockchain is considered highly secure. A majority of nodes must verify and confirm the legitimacy of the new data before a new block can be added to the ledger. For a cryptocurrency, they might involve ensuring that new transactions in a block were not fraudulent, or that coins had not been spent more than once. This is different from a standalone database or spreadsheet, where one person can make changes without oversight.

#     “Once there is consensus, the block is added to the chain and the underlying transactions are recorded in the distributed ledger,” says C. Neil Gray, partner in the fintech practice areas at Duane Morris LLP. “Blocks are securely linked together, forming a secure digital chain from the beginning of the ledger to the present.”

#     Transactions are typically secured using cryptography, meaning the nodes need to solve complex mathematical equations to process a transaction.

#     “As a reward for their efforts in validating changes to the shared data, nodes are typically rewarded with new amounts of the blockchain’s native currency—e.g., new bitcoin on the bitcoin blockchain,” says Sarah Shtylman, fintech and blockchain counsel with Perkins Coie.
#     SOURCE: 5'''

#     listoftexts = texts.split('SOURCE: ')

#     gen = generate_cited_answer_stream(question, listoftexts)

#     while True:
#         try:
#             next = next(gen)
#             print("this", next)
#         except:
#             print('No more answers')
#             break