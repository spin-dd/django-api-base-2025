# 実例: REST API

このページでは、実際のプロジェクトでのapibaseの使用例を紹介します。

## 契約管理システム

taihei-cvm-serverプロジェクトを参考にした契約管理APIの実装例です。

### モデル構成

```python
# contracts/models.py
from django.db import models


class Contract(models.Model):
    """契約"""
    STATUS_CHOICES = [
        ('draft', '下書き'),
        ('active', '有効'),
        ('expired', '期限切れ'),
        ('cancelled', 'キャンセル'),
    ]

    contract_number = models.CharField('契約番号', max_length=50, unique=True)
    title = models.CharField('件名', max_length=200)
    customer = models.ForeignKey(
        'customers.Customer',
        on_delete=models.PROTECT,
        related_name='contracts',
        verbose_name='顧客'
    )
    status = models.CharField('ステータス', max_length=20, choices=STATUS_CHOICES, default='draft')
    start_date = models.DateField('開始日')
    end_date = models.DateField('終了日')
    total_amount = models.DecimalField('契約金額', max_digits=12, decimal_places=2)
    notes = models.TextField('備考', blank=True)
    attachment = models.FileField('添付ファイル', upload_to='contracts/', blank=True)
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.PROTECT,
        related_name='created_contracts',
        verbose_name='作成者'
    )

    class Meta:
        verbose_name = '契約'
        verbose_name_plural = '契約'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.contract_number} - {self.title}"


class ContractItem(models.Model):
    """契約明細"""
    contract = models.ForeignKey(
        Contract,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name='契約'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.PROTECT,
        verbose_name='商品'
    )
    quantity = models.PositiveIntegerField('数量')
    unit_price = models.DecimalField('単価', max_digits=10, decimal_places=2)
    discount_rate = models.DecimalField('割引率', max_digits=5, decimal_places=2, default=0)

    class Meta:
        verbose_name = '契約明細'
        verbose_name_plural = '契約明細'

    @property
    def subtotal(self):
        return self.quantity * self.unit_price * (1 - self.discount_rate / 100)
```

### シリアライザ

```python
# contracts/api/serializers.py
from rest_framework import serializers
from apibase.serializers import BaseModelSerializer, BatchSerializerMixin, BatchListSerializer
from ..models import Contract, ContractItem


class ContractItemSerializer(BatchSerializerMixin, BaseModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = ContractItem
        fields = [
            'id', 'product', 'product_name', 'quantity',
            'unit_price', 'discount_rate', 'subtotal'
        ]
        list_serializer_class = BatchListSerializer


class ContractSerializer(BaseModelSerializer):
    items = ContractItemSerializer(many=True, required=False)
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    nested_fields = ['items']

    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number', 'title',
            'customer', 'customer_name',
            'status', 'status_display',
            'start_date', 'end_date',
            'total_amount', 'notes', 'attachment',
            'items',
            'created_by', 'created_by_name',
            'created_at', 'updated_at',
            'endpoint', 'urn', 'display'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)

    def validate(self, data):
        """契約期間のバリデーション"""
        start_date = data.get('start_date', getattr(self.instance, 'start_date', None))
        end_date = data.get('end_date', getattr(self.instance, 'end_date', None))

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError({
                'end_date': '終了日は開始日以降である必要があります。'
            })

        return data
```

### フィルタ

```python
# contracts/api/filters.py
import django_filters
from apibase.filters import BaseFilter, WordFilter, MonthFromToRangeFilter
from ..models import Contract


class ContractFilter(BaseFilter):
    search = WordFilter(
        label='検索',
        lookups=['contract_number', 'title', 'customer__name', 'notes']
    )

    # 契約期間フィルタ
    start_date_range = MonthFromToRangeFilter(field_name='start_date')
    end_date_range = MonthFromToRangeFilter(field_name='end_date')

    # 金額範囲
    amount_min = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='gte',
        label='最低金額'
    )
    amount_max = django_filters.NumberFilter(
        field_name='total_amount',
        lookup_expr='lte',
        label='最高金額'
    )

    # ステータス（複数選択）
    status_in = django_filters.CharFilter(method='filter_status_in')

    class Meta:
        model = Contract
        fields = {
            'contract_number': ['exact', 'contains'],
            'customer': ['exact'],
            'status': ['exact'],
            'start_date': ['exact', 'gte', 'lte'],
            'end_date': ['exact', 'gte', 'lte'],
            'created_by': ['exact'],
        }

    def filter_status_in(self, queryset, name, value):
        if value:
            statuses = value.split(',')
            return queryset.filter(status__in=statuses)
        return queryset
```

### ViewSet

```python
# contracts/api/viewsets.py
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apibase.viewsets import BaseModelViewSet
from ..models import Contract
from .serializers import ContractSerializer
from .filters import ContractFilter


class ContractViewSet(BaseModelViewSet):
    queryset = Contract.objects.select_related(
        'customer', 'created_by'
    ).prefetch_related(
        'items__product'
    ).all()
    serializer_class = ContractSerializer
    filterset_class = ContractFilter
    permission_classes = [IsAuthenticated]
    ordering_fields = [
        'contract_number', 'title', 'start_date',
        'end_date', 'total_amount', 'created_at'
    ]
    search_fields = ['contract_number', 'title', 'customer__name']

    # CSVエクスポート用
    fields_query = 'fields'

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """契約を有効化"""
        contract = self.get_object()

        if contract.status != 'draft':
            return Response(
                {'error': '下書き状態の契約のみ有効化できます。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        contract.status = 'active'
        contract.save()

        serializer = self.get_serializer(contract)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """契約をキャンセル"""
        contract = self.get_object()
        reason = request.data.get('reason', '')

        if contract.status == 'cancelled':
            return Response(
                {'error': 'すでにキャンセルされています。'},
                status=status.HTTP_400_BAD_REQUEST
            )

        contract.status = 'cancelled'
        contract.notes = f"{contract.notes}\n\n【キャンセル理由】{reason}".strip()
        contract.save()

        serializer = self.get_serializer(contract)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        """契約サマリー"""
        queryset = self.filter_queryset(self.get_queryset())

        summary = {
            'total_count': queryset.count(),
            'by_status': {
                status: queryset.filter(status=status).count()
                for status, _ in Contract.STATUS_CHOICES
            },
            'total_amount': queryset.aggregate(
                total=models.Sum('total_amount')
            )['total'] or 0
        }

        return Response(summary)

    @action(detail=True, methods=['get'])
    def duplicate(self, request, pk=None):
        """契約を複製"""
        original = self.get_object()

        # 新しい契約番号を生成
        new_number = self._generate_new_contract_number(original.contract_number)

        # 契約を複製
        new_contract = Contract.objects.create(
            contract_number=new_number,
            title=f"{original.title} (複製)",
            customer=original.customer,
            status='draft',
            start_date=original.start_date,
            end_date=original.end_date,
            total_amount=original.total_amount,
            notes=original.notes,
            created_by=request.user
        )

        # 明細を複製
        for item in original.items.all():
            ContractItem.objects.create(
                contract=new_contract,
                product=item.product,
                quantity=item.quantity,
                unit_price=item.unit_price,
                discount_rate=item.discount_rate
            )

        serializer = self.get_serializer(new_contract)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _generate_new_contract_number(self, original_number):
        import datetime
        today = datetime.date.today()
        return f"CTR-{today.strftime('%Y%m%d')}-{Contract.objects.count() + 1:04d}"
```

### URL設定

```python
# contracts/api/urls.py
from rest_framework.routers import DefaultRouter
from .viewsets import ContractViewSet

router = DefaultRouter()
router.register('contracts', ContractViewSet, basename='contract')

urlpatterns = router.urls
```

### APIの使用例

```bash
# 契約一覧（検索・フィルタリング）
curl "http://localhost:8000/api/contracts/?search=重要&status_in=draft,active"

# 契約作成（明細付き）
curl -X POST http://localhost:8000/api/contracts/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token xxx" \
  -d '{
    "contract_number": "CTR-2024-001",
    "title": "年間保守契約",
    "customer": 1,
    "start_date": "2024-04-01",
    "end_date": "2025-03-31",
    "total_amount": "1200000.00",
    "items": [
      {"product": 1, "quantity": 12, "unit_price": "100000.00"}
    ]
  }'

# 契約を有効化
curl -X POST http://localhost:8000/api/contracts/1/activate/ \
  -H "Authorization: Token xxx"

# 契約サマリー
curl "http://localhost:8000/api/contracts/summary/" \
  -H "Authorization: Token xxx"

# 添付ファイルダウンロード
curl -O "http://localhost:8000/api/contracts/1/attachment/download/"

# CSV出力
curl -H "Accept: text/csv" \
  "http://localhost:8000/api/contracts/?fields=contract_number,title,customer_name,status_display,total_amount"
```

## 次のステップ

- [実例: GraphQL](real-world-graphql.md)
- [ViewSet活用ガイド](../guides/viewsets.md)
