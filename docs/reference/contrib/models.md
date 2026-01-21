# contrib.models

モデルユーティリティを提供するモジュールです。

## 概要

Djangoモデルのユーティリティメソッドとミックスインを提供します。

## 使用例

### タイムスタンプモデル

```python
from django.db import models

class TimestampMixin(models.Model):
    """作成日時・更新日時を持つミックスイン"""
    created_at = models.DateTimeField('作成日時', auto_now_add=True)
    updated_at = models.DateTimeField('更新日時', auto_now=True)

    class Meta:
        abstract = True

class Product(TimestampMixin, models.Model):
    name = models.CharField('名前', max_length=200)
    price = models.PositiveIntegerField('価格')
```

### ソフトデリートモデル

```python
from django.db import models
from django.utils import timezone

class SoftDeleteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)

class SoftDeleteMixin(models.Model):
    """ソフトデリート対応ミックスイン"""
    deleted_at = models.DateTimeField('削除日時', null=True, blank=True)

    objects = SoftDeleteManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.deleted_at = timezone.now()
        self.save(update_fields=['deleted_at'])

    def hard_delete(self):
        super().delete()

    def restore(self):
        self.deleted_at = None
        self.save(update_fields=['deleted_at'])
```

### UUIDプライマリキー

```python
import uuid
from django.db import models

class UUIDMixin(models.Model):
    """UUIDをプライマリキーとするミックスイン"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True
```

### 順序付きモデル

```python
from django.db import models

class OrderedMixin(models.Model):
    """順序付きミックスイン"""
    order = models.PositiveIntegerField('順序', default=0)

    class Meta:
        abstract = True
        ordering = ['order']

    def move_up(self):
        prev = self.__class__.objects.filter(order__lt=self.order).order_by('-order').first()
        if prev:
            prev.order, self.order = self.order, prev.order
            prev.save(update_fields=['order'])
            self.save(update_fields=['order'])

    def move_down(self):
        next_item = self.__class__.objects.filter(order__gt=self.order).order_by('order').first()
        if next_item:
            next_item.order, self.order = self.order, next_item.order
            next_item.save(update_fields=['order'])
            self.save(update_fields=['order'])
```
