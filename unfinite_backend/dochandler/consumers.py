# chat/consumers.py
from channels.generic.websocket import AsyncWebsocketConsumer
import json
import redis


### make the redis connection
r = redis.Redis(host='localhost', port=6379, db=0)

# Test connection
try:
    if r.ping():
        print("Redis server is running")
    else:
        print("Redis server is not running")
except redis.ConnectionError:
    print("Error connecting to Redis server")
### ---
### code for redis ends here

class ChatConsumer(AsyncWebsocketConsumer):

    # print something when a connection is made
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        print("Connection made")

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        print(text_data)
        text_data_json = json.loads(text_data)
        print(text_data_json)
        message = text_data_json['message']

        # Send message to room group
        # await self.channel_layer.group_send(
        #     self.room_group_name,
        #     {
        #         'type': 'chat_message',
        #         'message': "yummy!"
        #     }
        # )

        # send the messages from the generator
        for i in self.tennumbergenerator():
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': i
                }
            )

    def tennumbergenerator(self):
        for i in range(10):
            yield i

    async def chat_message(self, event):
        message = event['message']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message
        }))