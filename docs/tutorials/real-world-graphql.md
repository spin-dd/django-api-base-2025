# 実例: GraphQL

このページでは、実際のプロジェクトでのGraphQL実装例を紹介します。

## 契約管理システム GraphQL API

REST APIと同じ契約管理システムのGraphQL実装例です。

### 型定義

```python
# contracts/api/gql/types.py
import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from decimal import Decimal

from ...models import Contract, ContractItem


class ContractItemType(DjangoObjectType):
    class Meta:
        model = ContractItem
        fields = [
            'id', 'product', 'quantity',
            'unit_price', 'discount_rate'
        ]
        interfaces = (relay.Node,)

    subtotal = graphene.Decimal()
    product_name = graphene.String()

    def resolve_subtotal(self, info):
        return self.subtotal

    def resolve_product_name(self, info):
        return self.product.name


class ContractType(DjangoObjectType):
    class Meta:
        model = Contract
        fields = [
            'id', 'contract_number', 'title',
            'customer', 'status', 'start_date', 'end_date',
            'total_amount', 'notes', 'attachment',
            'items', 'created_by', 'created_at', 'updated_at'
        ]
        interfaces = (relay.Node,)
        filter_fields = {
            'contract_number': ['exact', 'icontains'],
            'title': ['exact', 'icontains'],
            'status': ['exact', 'in'],
            'start_date': ['exact', 'gte', 'lte'],
            'end_date': ['exact', 'gte', 'lte'],
            'customer': ['exact'],
        }

    status_display = graphene.String()
    customer_name = graphene.String()
    created_by_name = graphene.String()
    items_count = graphene.Int()
    calculated_total = graphene.Decimal()

    def resolve_status_display(self, info):
        return self.get_status_display()

    def resolve_customer_name(self, info):
        return self.customer.name

    def resolve_created_by_name(self, info):
        return self.created_by.username

    def resolve_items_count(self, info):
        return self.items.count()

    def resolve_calculated_total(self, info):
        return sum(item.subtotal for item in self.items.all())

    @classmethod
    def get_queryset(cls, queryset, info):
        """権限に基づくフィルタリング"""
        user = info.context.user
        if not user.is_authenticated:
            return queryset.none()
        if user.is_staff:
            return queryset
        return queryset.filter(created_by=user)


class ContractConnection(relay.Connection):
    class Meta:
        node = ContractType

    total_count = graphene.Int()
    total_amount = graphene.Decimal()

    def resolve_total_count(root, info):
        return root.length

    def resolve_total_amount(root, info):
        from django.db.models import Sum
        if hasattr(root, 'iterable'):
            qs = root.iterable
            if hasattr(qs, 'aggregate'):
                result = qs.aggregate(total=Sum('total_amount'))
                return result['total'] or Decimal('0')
        return Decimal('0')
```

### Query

```python
# contracts/api/gql/queries.py
import graphene
from graphene import relay
from graphene_django.filter import DjangoFilterConnectionField

from ...models import Contract, ContractItem
from .types import ContractType, ContractItemType, ContractConnection


class ContractSummaryType(graphene.ObjectType):
    total_count = graphene.Int()
    draft_count = graphene.Int()
    active_count = graphene.Int()
    expired_count = graphene.Int()
    cancelled_count = graphene.Int()
    total_amount = graphene.Decimal()


class Query(graphene.ObjectType):
    # 単一契約の取得
    contract = relay.Node.Field(ContractType)

    # 契約一覧（ページネーション・フィルタリング対応）
    contracts = DjangoFilterConnectionField(
        ContractType,
        connection_class=ContractConnection,
        search=graphene.String(),
        status_in=graphene.String(),
    )

    # 契約サマリー
    contract_summary = graphene.Field(
        ContractSummaryType,
        customer_id=graphene.ID(),
        start_date_gte=graphene.Date(),
        start_date_lte=graphene.Date(),
    )

    def resolve_contracts(self, info, search=None, status_in=None, **kwargs):
        user = info.context.user
        if not user.is_authenticated:
            return Contract.objects.none()

        qs = Contract.objects.select_related(
            'customer', 'created_by'
        ).prefetch_related('items__product')

        if not user.is_staff:
            qs = qs.filter(created_by=user)

        if search:
            from django.db.models import Q
            qs = qs.filter(
                Q(contract_number__icontains=search) |
                Q(title__icontains=search) |
                Q(customer__name__icontains=search)
            )

        if status_in:
            statuses = status_in.split(',')
            qs = qs.filter(status__in=statuses)

        return qs

    def resolve_contract_summary(self, info, customer_id=None,
                                  start_date_gte=None, start_date_lte=None):
        user = info.context.user
        if not user.is_authenticated:
            return None

        from django.db.models import Sum

        qs = Contract.objects.all()

        if not user.is_staff:
            qs = qs.filter(created_by=user)

        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if start_date_gte:
            qs = qs.filter(start_date__gte=start_date_gte)
        if start_date_lte:
            qs = qs.filter(start_date__lte=start_date_lte)

        total_amount = qs.aggregate(total=Sum('total_amount'))['total'] or 0

        return ContractSummaryType(
            total_count=qs.count(),
            draft_count=qs.filter(status='draft').count(),
            active_count=qs.filter(status='active').count(),
            expired_count=qs.filter(status='expired').count(),
            cancelled_count=qs.filter(status='cancelled').count(),
            total_amount=total_amount,
        )
```

### Mutation

```python
# contracts/api/gql/mutations.py
import graphene
from graphene import relay

from ...models import Contract, ContractItem
from .types import ContractType


class ContractItemInput(graphene.InputObjectType):
    id = graphene.ID()
    product_id = graphene.ID(required=True)
    quantity = graphene.Int(required=True)
    unit_price = graphene.Decimal(required=True)
    discount_rate = graphene.Decimal()


class CreateContractInput(graphene.InputObjectType):
    contract_number = graphene.String(required=True)
    title = graphene.String(required=True)
    customer_id = graphene.ID(required=True)
    start_date = graphene.Date(required=True)
    end_date = graphene.Date(required=True)
    total_amount = graphene.Decimal(required=True)
    notes = graphene.String()
    items = graphene.List(ContractItemInput)


class UpdateContractInput(graphene.InputObjectType):
    title = graphene.String()
    status = graphene.String()
    start_date = graphene.Date()
    end_date = graphene.Date()
    total_amount = graphene.Decimal()
    notes = graphene.String()
    items = graphene.List(ContractItemInput)


class CreateContract(graphene.Mutation):
    class Arguments:
        input = CreateContractInput(required=True)

    contract = graphene.Field(ContractType)
    ok = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, input):
        user = info.context.user
        if not user.is_authenticated:
            return CreateContract(ok=False, errors=['認証が必要です'])

        try:
            items_data = input.pop('items', [])

            contract = Contract.objects.create(
                created_by=user,
                **input
            )

            for item_data in items_data:
                ContractItem.objects.create(
                    contract=contract,
                    **item_data
                )

            return CreateContract(contract=contract, ok=True, errors=[])

        except Exception as e:
            return CreateContract(ok=False, errors=[str(e)])


class UpdateContract(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        input = UpdateContractInput(required=True)

    contract = graphene.Field(ContractType)
    ok = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, input):
        user = info.context.user
        if not user.is_authenticated:
            return UpdateContract(ok=False, errors=['認証が必要です'])

        try:
            # Relay global IDをデコード
            _, pk = relay.Node.from_global_id(id)
            contract = Contract.objects.get(pk=pk)

            # 権限チェック
            if not user.is_staff and contract.created_by != user:
                return UpdateContract(ok=False, errors=['編集権限がありません'])

            items_data = input.pop('items', None)

            # 契約を更新
            for key, value in input.items():
                if value is not None:
                    setattr(contract, key, value)
            contract.save()

            # 明細を更新
            if items_data is not None:
                # 既存の明細をIDで更新、新規は作成
                existing_ids = set()
                for item_data in items_data:
                    item_id = item_data.pop('id', None)
                    if item_id:
                        _, item_pk = relay.Node.from_global_id(item_id)
                        item = ContractItem.objects.get(pk=item_pk, contract=contract)
                        for key, value in item_data.items():
                            setattr(item, key, value)
                        item.save()
                        existing_ids.add(int(item_pk))
                    else:
                        ContractItem.objects.create(contract=contract, **item_data)

            return UpdateContract(contract=contract, ok=True, errors=[])

        except Contract.DoesNotExist:
            return UpdateContract(ok=False, errors=['契約が見つかりません'])
        except Exception as e:
            return UpdateContract(ok=False, errors=[str(e)])


class ActivateContract(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)

    contract = graphene.Field(ContractType)
    ok = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id):
        user = info.context.user
        if not user.is_authenticated:
            return ActivateContract(ok=False, errors=['認証が必要です'])

        try:
            _, pk = relay.Node.from_global_id(id)
            contract = Contract.objects.get(pk=pk)

            if contract.status != 'draft':
                return ActivateContract(
                    ok=False,
                    errors=['下書き状態の契約のみ有効化できます']
                )

            contract.status = 'active'
            contract.save()

            return ActivateContract(contract=contract, ok=True, errors=[])

        except Contract.DoesNotExist:
            return ActivateContract(ok=False, errors=['契約が見つかりません'])


class CancelContract(graphene.Mutation):
    class Arguments:
        id = graphene.ID(required=True)
        reason = graphene.String()

    contract = graphene.Field(ContractType)
    ok = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, id, reason=None):
        user = info.context.user
        if not user.is_authenticated:
            return CancelContract(ok=False, errors=['認証が必要です'])

        try:
            _, pk = relay.Node.from_global_id(id)
            contract = Contract.objects.get(pk=pk)

            if contract.status == 'cancelled':
                return CancelContract(ok=False, errors=['すでにキャンセルされています'])

            contract.status = 'cancelled'
            if reason:
                contract.notes = f"{contract.notes}\n\n【キャンセル理由】{reason}".strip()
            contract.save()

            return CancelContract(contract=contract, ok=True, errors=[])

        except Contract.DoesNotExist:
            return CancelContract(ok=False, errors=['契約が見つかりません'])


class Mutation(graphene.ObjectType):
    create_contract = CreateContract.Field()
    update_contract = UpdateContract.Field()
    activate_contract = ActivateContract.Field()
    cancel_contract = CancelContract.Field()
```

### スキーマ統合

```python
# myproject/schema.py
import graphene
from contracts.api.gql.queries import Query as ContractQuery
from contracts.api.gql.mutations import Mutation as ContractMutation


class Query(ContractQuery, graphene.ObjectType):
    pass


class Mutation(ContractMutation, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
```

### GraphQLクエリ例

```graphql
# 契約一覧（フィルタリング・ページネーション）
query {
  contracts(first: 10, search: "保守", statusIn: "draft,active") {
    totalCount
    totalAmount
    edges {
      node {
        id
        contractNumber
        title
        customerName
        statusDisplay
        startDate
        endDate
        totalAmount
        itemsCount
        items {
          edges {
            node {
              productName
              quantity
              unitPrice
              subtotal
            }
          }
        }
      }
    }
    pageInfo {
      hasNextPage
      endCursor
    }
  }
}

# 契約サマリー
query {
  contractSummary(customerId: "1") {
    totalCount
    draftCount
    activeCount
    expiredCount
    cancelledCount
    totalAmount
  }
}

# 契約作成
mutation {
  createContract(input: {
    contractNumber: "CTR-2024-001"
    title: "年間保守契約"
    customerId: "1"
    startDate: "2024-04-01"
    endDate: "2025-03-31"
    totalAmount: "1200000.00"
    items: [
      { productId: "1", quantity: 12, unitPrice: "100000.00" }
    ]
  }) {
    ok
    errors
    contract {
      id
      contractNumber
      title
      statusDisplay
    }
  }
}

# 契約有効化
mutation {
  activateContract(id: "Q29udHJhY3RUeXBlOjE=") {
    ok
    errors
    contract {
      statusDisplay
    }
  }
}
```

## 次のステップ

- [GraphQL統合ガイド](../guides/graphql.md)
- [GraphQL型定義](../guides/graphql-types.md)
