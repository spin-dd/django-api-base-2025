# テストの書き方

このチュートリアルでは、apibaseを使用したAPIのテスト方法を学びます。

## ゴール

- APIテストの基本
- ViewSetのテスト
- シリアライザのテスト
- フィルタのテスト

## 1. テスト環境のセットアップ

### conftest.py

```python
# tests/conftest.py
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def user():
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def admin_user():
    return User.objects.create_superuser(
        username='admin',
        email='admin@example.com',
        password='adminpass123'
    )
```

## 2. ViewSetのテスト

### 一覧取得のテスト

```python
# tests/test_viewsets.py
import pytest
from django.urls import reverse
from rest_framework import status
from myapp.models import Product


@pytest.mark.django_db
class TestProductViewSet:
    def test_list_products(self, api_client):
        """商品一覧の取得テスト"""
        Product.objects.create(name='Product 1', price=1000)
        Product.objects.create(name='Product 2', price=2000)

        url = reverse('product-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

    def test_list_products_with_pagination(self, api_client):
        """ページネーションのテスト"""
        for i in range(25):
            Product.objects.create(name=f'Product {i}', price=1000 + i)

        url = reverse('product-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 25
        assert len(response.data['results']) == 20  # デフォルトページサイズ
        assert response.data['next'] is not None
```

### 詳細取得のテスト

```python
    def test_retrieve_product(self, api_client):
        """商品詳細の取得テスト"""
        product = Product.objects.create(name='Test Product', price=1500)

        url = reverse('product-detail', kwargs={'pk': product.pk})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['name'] == 'Test Product'
        assert response.data['price'] == 1500
        assert 'endpoint' in response.data
        assert 'urn' in response.data
```

### 作成のテスト

```python
    def test_create_product(self, authenticated_client):
        """商品作成テスト"""
        url = reverse('product-list')
        data = {
            'name': 'New Product',
            'price': 2500,
            'description': 'A new product'
        }

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.count() == 1
        assert Product.objects.first().name == 'New Product'

    def test_create_product_validation_error(self, authenticated_client):
        """バリデーションエラーのテスト"""
        url = reverse('product-list')
        data = {'name': '', 'price': -100}

        response = authenticated_client.post(url, data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'name' in response.data
```

### バッチ操作のテスト

```python
    def test_batch_create(self, authenticated_client):
        """バッチ作成テスト"""
        url = reverse('product-batch-create')
        data = [
            {'name': 'Product 1', 'price': 1000},
            {'name': 'Product 2', 'price': 2000},
        ]

        response = authenticated_client.post(url, data, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        assert Product.objects.count() == 2

    def test_batch_update(self, authenticated_client):
        """バッチ更新テスト"""
        p1 = Product.objects.create(name='Product 1', price=1000)
        p2 = Product.objects.create(name='Product 2', price=2000)

        url = reverse('product-batch-update')
        data = [
            {'id': p1.id, 'price': 1500},
            {'id': p2.id, 'price': 2500},
        ]

        response = authenticated_client.patch(url, data, format='json')

        assert response.status_code == status.HTTP_200_OK

        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.price == 1500
        assert p2.price == 2500
```

## 3. シリアライザのテスト

### 基本的なシリアライザテスト

```python
# tests/test_serializers.py
import pytest
from myapp.api.serializers import ProductSerializer, OrderSerializer
from myapp.models import Product, Order


@pytest.mark.django_db
class TestProductSerializer:
    def test_serialization(self):
        """シリアライズのテスト"""
        product = Product.objects.create(name='Test', price=1000)
        serializer = ProductSerializer(product)

        assert serializer.data['name'] == 'Test'
        assert serializer.data['price'] == 1000
        assert 'endpoint' in serializer.data
        assert 'urn' in serializer.data
        assert 'display' in serializer.data

    def test_deserialization(self):
        """デシリアライズのテスト"""
        data = {'name': 'New Product', 'price': 2000}
        serializer = ProductSerializer(data=data)

        assert serializer.is_valid()
        product = serializer.save()
        assert product.name == 'New Product'
        assert product.price == 2000

    def test_validation(self):
        """バリデーションのテスト"""
        data = {'name': '', 'price': -100}
        serializer = ProductSerializer(data=data)

        assert not serializer.is_valid()
        assert 'name' in serializer.errors
```

### ネストシリアライザのテスト

```python
@pytest.mark.django_db
class TestOrderSerializer:
    def test_create_with_nested_items(self, product):
        """ネストアイテム付き作成テスト"""
        data = {
            'order_number': 'ORD-001',
            'customer_name': 'Test Customer',
            'customer_email': 'test@example.com',
            'items': [
                {'product': product.id, 'quantity': 2, 'unit_price': 1000},
            ]
        }
        serializer = OrderSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        assert order.items.count() == 1
        assert order.items.first().quantity == 2

    def test_update_nested_items(self, order_with_items):
        """ネストアイテム更新テスト"""
        item = order_with_items.items.first()
        data = {
            'items': [
                {'id': item.id, 'quantity': 5},
            ]
        }
        serializer = OrderSerializer(
            order_with_items,
            data=data,
            partial=True
        )

        assert serializer.is_valid(), serializer.errors
        order = serializer.save()

        item.refresh_from_db()
        assert item.quantity == 5
```

## 4. フィルタのテスト

### フィルタテスト

```python
# tests/test_filters.py
import pytest
from django.urls import reverse
from rest_framework import status
from myapp.models import Product


@pytest.mark.django_db
class TestProductFilter:
    @pytest.fixture
    def products(self):
        Product.objects.create(name='Django Book', price=3000, category='programming')
        Product.objects.create(name='Python Guide', price=2500, category='programming')
        Product.objects.create(name='Cooking Recipe', price=1500, category='cooking')
        return Product.objects.all()

    def test_filter_by_category(self, api_client, products):
        """カテゴリフィルタのテスト"""
        url = reverse('product-list')
        response = api_client.get(url, {'category': 'programming'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_filter_by_price_range(self, api_client, products):
        """価格範囲フィルタのテスト"""
        url = reverse('product-list')
        response = api_client.get(url, {
            'price__gte': 2000,
            'price__lte': 3000
        })

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 2

    def test_word_filter(self, api_client, products):
        """WordFilterのテスト"""
        url = reverse('product-list')
        response = api_client.get(url, {'search': 'Python'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
        assert response.data['results'][0]['name'] == 'Python Guide'

    def test_word_filter_multiple_keywords(self, api_client, products):
        """複数キーワード検索のテスト"""
        url = reverse('product-list')
        response = api_client.get(url, {'search': 'Django Book'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1
```

## 5. 権限のテスト

```python
# tests/test_permissions.py
import pytest
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db
class TestProductPermissions:
    def test_list_requires_no_auth(self, api_client):
        """一覧は認証不要"""
        url = reverse('product-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_requires_auth(self, api_client):
        """作成は認証必要"""
        url = reverse('product-list')
        response = api_client.post(url, {'name': 'Test', 'price': 1000})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_with_auth(self, authenticated_client):
        """認証済みで作成可能"""
        url = reverse('product-list')
        response = authenticated_client.post(url, {'name': 'Test', 'price': 1000})
        assert response.status_code == status.HTTP_201_CREATED

    def test_delete_requires_admin(self, authenticated_client, product):
        """削除は管理者のみ"""
        url = reverse('product-detail', kwargs={'pk': product.pk})
        response = authenticated_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_delete(self, admin_authenticated_client, product):
        """管理者は削除可能"""
        url = reverse('product-detail', kwargs={'pk': product.pk})
        response = admin_authenticated_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
```

## 6. ファクトリの使用

### factory_boy を使用したテストデータ生成

```python
# tests/factories.py
import factory
from myapp.models import Product, Order, OrderItem


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f'Product {n}')
    price = factory.Faker('random_int', min=100, max=10000)
    category = factory.Faker('random_element', elements=['programming', 'cooking', 'travel'])


class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order

    order_number = factory.Sequence(lambda n: f'ORD-{n:06d}')
    customer_name = factory.Faker('name')
    customer_email = factory.Faker('email')


class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem

    order = factory.SubFactory(OrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('random_int', min=1, max=10)
    unit_price = factory.LazyAttribute(lambda obj: obj.product.price)
```

### ファクトリを使用したテスト

```python
@pytest.mark.django_db
class TestWithFactories:
    def test_order_total(self):
        order = OrderFactory()
        OrderItemFactory(order=order, quantity=2, unit_price=1000)
        OrderItemFactory(order=order, quantity=1, unit_price=500)

        assert order.total_amount == 2500
```

## 次のステップ

- [テストの実例](../examples/crud-viewset.md)
- [開発者向けテストガイド](../development/testing.md)
