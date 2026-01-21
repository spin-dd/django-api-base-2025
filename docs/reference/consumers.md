# consumers

WebSocketコンシューマを提供するモジュールです。

## 概要

Django Channelsと統合されたWebSocketコンシューマの基底クラスを提供します。

## クラス

### BaseConsumer

WebSocketコンシューマの基底クラスです。

```python
from apibase.consumers import BaseConsumer
```

**継承元**

- `channels.generic.websocket.AsyncJsonWebsocketConsumer`

---

## 使用例

### 基本的なコンシューマ

```python
from apibase.consumers import BaseConsumer

class NotificationConsumer(BaseConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'notifications_{self.room_name}'

        # グループに参加
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # グループから離脱
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        message = content.get('message', '')

        # グループにメッセージを送信
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'notification_message',
                'message': message
            }
        )

    async def notification_message(self, event):
        # クライアントにメッセージを送信
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
    re_path(
        r'ws/notifications/(?P<room_name>\w+)/$',
        consumers.NotificationConsumer.as_asgi()
    ),
]
```

### ASGI設定

```python
# myproject/asgi.py
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

### クライアント側

```javascript
const socket = new WebSocket('ws://localhost:8000/ws/notifications/room1/');

socket.onopen = function(e) {
    console.log('WebSocket connected');
};

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    console.log('Received:', data.message);
};

socket.send(JSON.stringify({
    'message': 'Hello, World!'
}));
```
