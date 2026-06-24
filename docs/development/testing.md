# テスト方法

テストの実行方法と書き方について説明します。

## テストの実行

### 全テストの実行

```bash
uv run pytest
```

### 詳細出力

```bash
uv run pytest -v
```

### 特定のテストファイル

```bash
uv run pytest tests/test_viewsets.py
```

### 特定のテストクラス/メソッド

```bash
uv run pytest tests/test_viewsets.py::TestProductViewSet
uv run pytest tests/test_viewsets.py::TestProductViewSet::test_list
```

### キーワードでフィルタ

```bash
uv run pytest -k "filter"
```

### カバレッジ

```bash
uv run pytest --cov=apibase --cov-report=html
# htmlcov/index.html でレポートを確認
```

## テストの書き方

### 基本構造

```python
import pytest
from django.test import TestCase
from rest_framework.test import APITestCase

class TestProductViewSet(APITestCase):
    @pytest.fixture(autouse=True)
    def setup(self):
        self.product = Product.objects.create(name='Test', price=1000)

    def test_list(self):
        response = self.client.get('/api/products/')
        assert response.status_code == 200
        assert response.data['count'] == 1
```

### Fixturesの使用

```python
# tests/conftest.py
import pytest
from rest_framework.test import APIClient

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def product(db):
    return Product.objects.create(name='Test Product', price=1000)

@pytest.fixture
def authenticated_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client
```

### Factoryの使用

```python
# tests/factories.py
import factory
from myapp.models import Product

class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Sequence(lambda n: f'Product {n}')
    price = factory.Faker('random_int', min=100, max=10000)
```

```python
# tests/test_products.py
@pytest.mark.django_db
class TestProductViewSet:
    def test_list_products(self, api_client):
        ProductFactory.create_batch(5)
        response = api_client.get('/api/products/')
        assert response.data['count'] == 5
```

## テストカテゴリ

### ユニットテスト

```python
class TestWordFilter:
    def test_filter_with_japanese(self):
        filter = WordFilter(lookups=['name'])
        qs = Product.objects.all()

        result = filter.filter(qs, '商品')
        assert result.exists()
```

### 統合テスト

```python
@pytest.mark.django_db
class TestProductAPI:
    def test_create_and_retrieve(self, authenticated_client):
        # 作成
        response = authenticated_client.post('/api/products/', {
            'name': 'New Product',
            'price': 1000
        })
        assert response.status_code == 201
        product_id = response.data['id']

        # 取得
        response = authenticated_client.get(f'/api/products/{product_id}/')
        assert response.status_code == 200
        assert response.data['name'] == 'New Product'
```

### E2Eテスト

```python
@pytest.mark.django_db
class TestOrderWorkflow:
    def test_complete_order_flow(self, authenticated_client, product):
        # 注文作成
        response = authenticated_client.post('/api/orders/', {
            'customer': 1,
            'items': [{'product': product.id, 'quantity': 2}]
        })
        order_id = response.data['id']

        # 注文確定
        response = authenticated_client.post(f'/api/orders/{order_id}/confirm/')
        assert response.data['status'] == 'confirmed'
```

## モック

### 外部APIのモック

```python
from unittest.mock import patch

@pytest.mark.django_db
class TestPaymentAPI:
    @patch('myapp.services.payment_gateway.charge')
    def test_payment(self, mock_charge, authenticated_client):
        mock_charge.return_value = {'status': 'success', 'transaction_id': '123'}

        response = authenticated_client.post('/api/payments/', {
            'order_id': 1,
            'amount': 1000
        })

        assert response.status_code == 200
        mock_charge.assert_called_once()
```

## テストデータベース

```python
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = tests.settings
```

```python
# tests/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```
