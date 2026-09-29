# ネストシリアライザ

このチュートリアルでは、apibaseのネストシリアライザ機能を使って、関連データを同時に作成・更新する方法を学びます。

## ゴール

- ネストシリアライザの設定
- 関連データの同時作成
- 関連データの同時更新
- シグナルによる通知

## ユースケース

注文（Order）と注文明細（OrderItem）を同時に作成・更新する例を実装します。

## 1. モデルの作成

### orders/models.py

```python
from django.db import models
from django.dispatch import Signal

# ネスト更新完了シグナル
order_items_updated = Signal()


class Product(models.Model):
    name = models.CharField('商品名', max_length=200)
    price = models.PositiveIntegerField('単価')
    stock = models.PositiveIntegerField('在庫', default=0)

    def __str__(self):
        return self.name


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', '処理待ち'),
        ('confirmed', '確定'),
        ('shipped', '発送済み'),
        ('cancelled', 'キャンセル'),
    ]

    order_number = models.CharField('注文番号', max_length=20, unique=True)
    customer_name = models.CharField('顧客名', max_length=100)
    customer_email = models.EmailField('メールアドレス')
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField('備考', blank=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        verbose_name = '注文'
        verbose_name_plural = '注文'

    def __str__(self):
        return f"注文 {self.order_number}"

    @property
    def total_amount(self):
        return sum(item.subtotal for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='注文'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        verbose_name='商品'
    )
    quantity = models.PositiveIntegerField('数量', default=1)
    unit_price = models.PositiveIntegerField('単価')

    class Meta:
        verbose_name = '注文明細'
        verbose_name_plural = '注文明細'

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
```

## 2. シリアライザの作成

### orders/api/serializers.py

```python
from rest_framework import serializers
from apibase.serializers import BaseModelSerializer
from ..models import Product, Order, OrderItem, order_items_updated


class ProductSerializer(BaseModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'name', 'price', 'stock', 'endpoint', 'urn', 'display']


class OrderItemSerializer(BaseModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.IntegerField(read_only=True)

    class Meta:
        model = OrderItem
        fields = [
            'id',
            'product',
            'product_name',
            'quantity',
            'unit_price',
            'subtotal',
        ]

    @classmethod
    def update_or_create(cls, partial=None, id=None, context=None, **validated_data):
        """既存アイテムの更新または新規作成"""
        instance = id and OrderItem.objects.filter(id=id).first()
        serializer = cls(instance=instance, data=validated_data, partial=partial, context=context)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return serializer.instance


class OrderSerializer(BaseModelSerializer):
    # ネストされた注文明細
    items = OrderItemSerializer(many=True, required=False)
    total_amount = serializers.IntegerField(read_only=True)

    # ネストフィールドとして登録
    nested_fields = ['items']
    nested_fields_updateds_signal = order_items_updated

    class Meta:
        model = Order
        fields = [
            'id',
            'order_number',
            'customer_name',
            'customer_email',
            'status',
            'notes',
            'items',
            'total_amount',
            'created_at',
            'updated_at',
            'endpoint',
            'urn',
            'display',
        ]
        read_only_fields = ['created_at', 'updated_at']

    def validate_items(self, value):
        """注文明細のバリデーション"""
        if not value:
            raise serializers.ValidationError('注文明細は1件以上必要です')
        return value

    def patch_children(self, instance, field_name, data):
        """注文明細作成時に単価を自動設定"""
        if field_name == 'items' and 'product' in data:
            product = Product.objects.get(pk=data['product'])
            data.setdefault('unit_price', product.price)
        return data
```

## 3. ViewSetの作成

### orders/api/viewsets.py

```python
from apibase.viewsets import BaseModelViewSet
from ..models import Order
from .serializers import OrderSerializer


class OrderViewSet(BaseModelViewSet):
    queryset = Order.objects.prefetch_related('items__product').all()
    serializer_class = OrderSerializer
```

## 4. 使用例

### 注文と明細の同時作成

```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_number": "ORD-2024-001",
    "customer_name": "山田太郎",
    "customer_email": "yamada@example.com",
    "items": [
      {"product": 1, "quantity": 2},
      {"product": 2, "quantity": 1}
    ]
  }'
```

レスポンス:

```json
{
  "id": 1,
  "order_number": "ORD-2024-001",
  "customer_name": "山田太郎",
  "customer_email": "yamada@example.com",
  "status": "pending",
  "notes": "",
  "items": [
    {
      "id": 1,
      "product": 1,
      "product_name": "商品A",
      "quantity": 2,
      "unit_price": 1000,
      "subtotal": 2000
    },
    {
      "id": 2,
      "product": 2,
      "product_name": "商品B",
      "quantity": 1,
      "unit_price": 1500,
      "subtotal": 1500
    }
  ],
  "total_amount": 3500,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### 注文と明細の同時更新

```bash
curl -X PATCH http://localhost:8000/api/orders/1/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "confirmed",
    "items": [
      {"id": 1, "quantity": 3},
      {"product": 3, "quantity": 1}
    ]
  }'
```

## 5. シグナルの活用

### シグナル受信の設定

```python
# orders/signals.py
from django.dispatch import receiver
from .models import order_items_updated


@receiver(order_items_updated)
def handle_order_items_updated(sender, instance, **kwargs):
    """注文明細更新後の処理"""
    # 在庫の更新
    for item in instance.items.all():
        item.product.stock -= item.quantity
        item.product.save()

    # メール送信
    send_order_confirmation_email(instance)

    # ログ記録
    logger.info(f"Order {instance.order_number} items updated")
```

### apps.py での接続

```python
# orders/apps.py
from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        from . import signals  # noqa
```

## 6. 高度な使用例

### 削除フラグ付きの更新

明細の削除をサポート:

```python
class OrderItemSerializer(BaseModelSerializer):
    _delete = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'quantity', 'unit_price', '_delete']


class OrderSerializer(BaseModelSerializer):
    items = OrderItemSerializer(many=True, required=False)
    nested_fields = ['items']

    def update_nested_field(self, field_name, instance, validated_data, children):
        if field_name == 'items':
            # 削除フラグ付きの処理
            for item_data in children or []:
                if item_data.get('_delete'):
                    OrderItem.objects.filter(
                        order=instance,
                        id=item_data.get('id')
                    ).delete()

            # 削除フラグ以外のデータを処理
            children = [c for c in (children or []) if not c.get('_delete')]

        return super().update_nested_field(field_name, instance, validated_data, children)
```

### GenericRelation のサポート

```python
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType


class Comment(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    text = models.TextField()


class Order(models.Model):
    # ...
    comments = GenericRelation(Comment)
```

`BaseModelSerializer`は`GenericRelation`を自動的に処理します。

## 次のステップ

- [Serializer活用ガイド](../guides/serializers.md)
- [バッチ操作](../guides/batch-operations.md)
