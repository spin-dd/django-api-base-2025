# WebSocket

WebSocket通信の実装例です。

## チャットルーム

### Consumer

```python
# chat/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        # グループに参加
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # 参加通知
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_join',
                'user': str(self.scope['user'])
            }
        )

    async def disconnect(self, close_code):
        # グループから離脱
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive_json(self, content):
        message_type = content.get('type', 'message')

        if message_type == 'message':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'user': str(self.scope['user']),
                    'message': content.get('message', '')
                }
            )

    async def chat_message(self, event):
        await self.send_json({
            'type': 'message',
            'user': event['user'],
            'message': event['message']
        })

    async def user_join(self, event):
        await self.send_json({
            'type': 'join',
            'user': event['user']
        })
```

### ルーティング

```python
# chat/routing.py
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/chat/(?P<room_name>\w+)/$', consumers.ChatConsumer.as_asgi()),
]
```

### クライアント

```javascript
const roomName = 'general';
const socket = new WebSocket(`ws://localhost:8000/ws/chat/${roomName}/`);

socket.onopen = function(e) {
    console.log('Connected to chat');
};

socket.onmessage = function(e) {
    const data = JSON.parse(e.data);

    if (data.type === 'message') {
        console.log(`${data.user}: ${data.message}`);
    } else if (data.type === 'join') {
        console.log(`${data.user} joined the room`);
    }
};

// メッセージ送信
function sendMessage(message) {
    socket.send(JSON.stringify({
        type: 'message',
        message: message
    }));
}
```

## リアルタイム通知

### Consumer

```python
# notifications/consumers.py
from channels.generic.websocket import AsyncJsonWebsocketConsumer

class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope['user']
        if not user.is_authenticated:
            await self.close()
            return

        self.user_group = f'user_{user.id}'

        await self.channel_layer.group_add(
            self.user_group,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'user_group'):
            await self.channel_layer.group_discard(
                self.user_group,
                self.channel_name
            )

    async def notification(self, event):
        await self.send_json({
            'type': 'notification',
            'title': event['title'],
            'body': event['body'],
            'data': event.get('data', {})
        })
```

### シグナルからの通知

```python
# orders/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Order

@receiver(post_save, sender=Order)
def order_created(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'user_{instance.customer.id}',
            {
                'type': 'notification',
                'title': '注文が作成されました',
                'body': f'注文番号: {instance.order_number}',
                'data': {'order_id': instance.id}
            }
        )
```

## 進捗通知

### Consumer

```python
class ProgressConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.task_group = f'task_{self.task_id}'

        await self.channel_layer.group_add(
            self.task_group,
            self.channel_name
        )

        await self.accept()

    async def progress_update(self, event):
        await self.send_json({
            'type': 'progress',
            'current': event['current'],
            'total': event['total'],
            'percentage': event['percentage'],
            'message': event.get('message', '')
        })

    async def task_complete(self, event):
        await self.send_json({
            'type': 'complete',
            'result': event['result']
        })
```

### タスクからの進捗送信

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def process_large_task(task_id, items):
    channel_layer = get_channel_layer()
    total = len(items)

    for i, item in enumerate(items, 1):
        process_item(item)

        # 進捗を送信
        async_to_sync(channel_layer.group_send)(
            f'task_{task_id}',
            {
                'type': 'progress_update',
                'current': i,
                'total': total,
                'percentage': int(i / total * 100),
                'message': f'Processing {item.name}'
            }
        )

    # 完了通知
    async_to_sync(channel_layer.group_send)(
        f'task_{task_id}',
        {
            'type': 'task_complete',
            'result': {'processed': total}
        }
    )
```
