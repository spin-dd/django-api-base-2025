from django.apps import AppConfig


def _safe_init_converter():
    try:
        from apibase.utils import init_converter

        init_converter()
    except Exception:
        # Graphene-Django未導入の環境やテスト最小構成でも安全にスキップ
        pass


class DemoConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "web.demo"

    def ready(self):
        # GraphQL フォーム→型コンバータ登録を一度だけ初期化
        _safe_init_converter()
