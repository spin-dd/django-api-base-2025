# WebSocket/Channels

apibaseは、Django Channelsを使用したWebSocket通信をサポートします。

## 概要

- Django Channelsとの統合
- GraphQL Subscriptionサポート
- リアルタイム通知

## 設定

### 依存関係

```bash
pip install channels channels-redis
```

### settings.py

```python
INSTALLED_APPS = [
    # ...
    'channels',
    'channels_redis',
]

ASGI_APPLICATION = 'myproject.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}
```

### asgi.py

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')

django_asgi_app = get_asgi_application()

from myapp.routing import websocket_urlpatterns

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
```

## Consumerの作成

### 基本的なConsumer

apibaseの`consumers`モジュールを使用:

```python
# myapp/consumers.py
from apibase.consumers import BaseConsumer

class NotificationConsumer(BaseConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'notifications_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        message = content.get('message', '')
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'notification_message',
                'message': message
            }
        )

    async def notification_message(self, event):
        await self.send_json({
            'message': event['message']
        })
```

### ルーティング

```python
# myapp/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/notifications/(?P<room_name>\w+)/$', consumers.NotificationConsumer.as_asgi()),
]
```

## GraphQL Subscription

### 設定

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'channels_graphql_ws',
]
```

### スキーマ

```python
# myapp/schema.py
import graphene
from channels_graphql_ws import Subscription

class OnNewBook(Subscription):
    book = graphene.Field(BookType)

    class Arguments:
        author_id = graphene.ID()

    @staticmethod
    def subscribe(root, info, author_id=None):
        return [f'author_{author_id}'] if author_id else ['all_books']

    @staticmethod
    def publish(payload, info, author_id=None):
        return OnNewBook(book=payload['book'])

class Subscription(graphene.ObjectType):
    on_new_book = OnNewBook.Field()

schema = graphene.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription
)
```

### クライアント側

```javascript
const socket = new WebSocket('ws://localhost:8000/graphql/');

socket.onopen = () => {
    socket.send(JSON.stringify({
        type: 'connection_init',
        payload: {}
    }));

    socket.send(JSON.stringify({
        id: '1',
        type: 'subscribe',
        payload: {
            query: `
                subscription {
                    onNewBook {
                        book {
                            id
                            title
                        }
                    }
                }
            `
        }
    }));
};

socket.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

## 通知の送信

### ビューからの送信

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def create_book(request):
    book = Book.objects.create(...)

    # WebSocket通知を送信
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'author_{book.author_id}',
        {
            'type': 'notification_message',
            'message': f'New book: {book.title}'
        }
    )

    return Response({'id': book.id})
```

### シグナルからの送信

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=Book)
def book_saved(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            'all_books',
            {
                'type': 'book.created',
                'book_id': instance.id
            }
        )
```

## 認証

### WebSocket認証

```python
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class TokenAuthMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        token = self.get_token_from_query(scope)
        scope['user'] = await self.get_user(token)
        return await self.app(scope, receive, send)

    def get_token_from_query(self, scope):
        query_string = scope.get('query_string', b'').decode()
        params = dict(x.split('=') for x in query_string.split('&') if '=' in x)
        return params.get('token')

    @database_sync_to_async
    def get_user(self, token):
        if token:
            try:
                # トークンからユーザーを取得
                return User.objects.get(auth_token=token)
            except User.DoesNotExist:
                pass
        return AnonymousUser()
```

### Consumer内での認証チェック

```python
class SecureConsumer(BaseConsumer):
    async def connect(self):
        if self.scope['user'].is_anonymous:
            await self.close()
            return

        await self.accept()
```

## テスト

```python
from channels.testing import WebsocketCommunicator
from myproject.asgi import application
import pytest

@pytest.mark.asyncio
async def test_notification_consumer():
    communicator = WebsocketCommunicator(
        application,
        '/ws/notifications/test/'
    )

    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_json_to({'message': 'Hello'})
    response = await communicator.receive_json_from()
    assert response['message'] == 'Hello'

    await communicator.disconnect()
```

## 次のステップ

- [WebSocketの実例](../examples/websocket.md)
- [GraphQL Subscriptionの詳細](graphql.md)
