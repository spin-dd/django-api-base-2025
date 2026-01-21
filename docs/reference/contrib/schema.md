# contrib.schema

OpenAPIスキーマ拡張を提供するモジュールです。

## 概要

drf-spectacularとの統合機能を提供します。

## 依存関係

```bash
pip install apibase[schema]
```

または

```bash
pip install drf-spectacular
```

## 使用例

### スキーマの設定

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'My API',
    'DESCRIPTION': 'APIドキュメント',
    'VERSION': '1.0.0',
}
```

### ViewSetでのスキーマ拡張

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter
from apibase.viewsets import BaseModelViewSet

class ProductViewSet(BaseModelViewSet):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='category',
                description='カテゴリでフィルタリング',
                required=False,
                type=str,
            ),
        ],
        responses={200: ProductSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
```

### URLの設定

```python
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
```

## フィルタのスキーマ

apibaseのフィルタはdrf-spectacularと互換性があります:

```python
from apibase.contrib.schema.filters import get_filterset_parameters

# FilterSetからOpenAPIパラメータを生成
parameters = get_filterset_parameters(ProductFilter)
```
