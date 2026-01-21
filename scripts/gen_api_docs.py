"""
mkdocs-gen-files用のAPIドキュメント自動生成スクリプト
"""

import mkdocs_gen_files
from pathlib import Path

# apibaseのモジュール一覧
MODULES = [
    "apibase.viewsets",
    "apibase.serializers",
    "apibase.filters",
    "apibase.fields",
    "apibase.routers",
    "apibase.paginations",
    "apibase.permissions",
    "apibase.renderers",
    "apibase.utils",
    "apibase.urn",
    "apibase.storages",
    "apibase.archives",
    "apibase.consumers",
    "apibase.graphql.mixins",
    "apibase.graphql.fields",
    "apibase.graphql.connections",
    "apibase.graphql.utils",
    "apibase.contrib.schema",
    "apibase.contrib.models",
    "apibase.settings",
]

# リファレンスページのマッピング
MODULE_TO_PAGE = {
    "apibase.viewsets": "reference/viewsets.md",
    "apibase.serializers": "reference/serializers.md",
    "apibase.filters": "reference/filters.md",
    "apibase.fields": "reference/fields.md",
    "apibase.routers": "reference/routers.md",
    "apibase.paginations": "reference/paginations.md",
    "apibase.permissions": "reference/permissions.md",
    "apibase.renderers": "reference/renderers.md",
    "apibase.utils": "reference/utils.md",
    "apibase.urn": "reference/urn.md",
    "apibase.storages": "reference/storages.md",
    "apibase.archives": "reference/archives.md",
    "apibase.consumers": "reference/consumers.md",
    "apibase.graphql.mixins": "reference/graphql/mixins.md",
    "apibase.graphql.fields": "reference/graphql/fields.md",
    "apibase.graphql.connections": "reference/graphql/connections.md",
    "apibase.graphql.utils": "reference/graphql/utils.md",
    "apibase.contrib.schema": "reference/contrib/schema.md",
    "apibase.contrib.models": "reference/contrib/models.md",
    "apibase.settings": "reference/settings.md",
}


def generate_api_docs():
    """APIドキュメントを生成"""
    # このスクリプトはmkdocs-gen-filesプラグインから呼び出される
    # 実際のプロジェクトでは、mkdocstringsを使用してAPIドキュメントを生成
    pass


if __name__ == "__main__":
    generate_api_docs()
