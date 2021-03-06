import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from django.contrib.auth import get_user_model
from .models import Message

User = get_user_model()

class ChatConsumer(WebsocketConsumer):


    def fetch_messages(self, data):
        # print('fetch')
        messages = Message.last_10_messages(self)
        content = {
            'messages': self.messages_to_json(messages)
        }
        # print(content)
        self.load_messages(content)

    def new_message(self,data):
        # pass
        author = data['from']
        author_user = User.objects.filter(username=author)[0]
        message = Message.objects.create(author=author_user, content=data['message'], socket_room_name=data['room_name'])
        content = {
            'command' : 'new_message',
            'message': self.message_to_json(message)
        }
        # return self.chat_message(content)
        return self.send_chat_message(content)



    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))
        return result

    def message_to_json(self, message):
        return {
            'author': message.author.username,
            'content': message.content,
            'timestamp': str(message.timestamp)
        }


    commands = {
        'fetch_messages':fetch_messages,
        'new_message':new_message,
    }




    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        # text_data_json = json.loads(text_data)
        # message = text_data_json['message']
        data = json.loads(text_data)
        self.commands[data['command']](self, data)

    def send_chat_message(self, message):
        # message = data['message']

        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )


    def load_messages(self, messages):
        # print(message)
        data = messages['messages']
        for message in data:
            # print(message)
            self.send(text_data=json.dumps(message))

    # Receive message from room group
    def chat_message(self, event):
        message = event['message']
        # print('chat_message method')
        # print(message['message'])

        # Send message to WebSocket
        # self.send(text_data=json.dumps({
        #     'message': message
        # }))
        ## self.send(text_data=json.dumps(message))
        self.send(text_data=json.dumps(message['message']))