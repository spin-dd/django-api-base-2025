from __future__ import annotations

try:
    from drf_spectacular.types import OpenApiTypes
    from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_field
except ImportError:

    def extend_schema(*args: object, **kwargs: object):
        def decorator(target):
            return target

        return decorator

    def extend_schema_field(*args: object, **kwargs: object):
        def decorator(target):
            return target

        return decorator

    class OpenApiParameter:
        PATH = "path"

        def __init__(self, *args: object, **kwargs: object) -> None:
            self.args = args
            self.kwargs = kwargs

    class OpenApiTypes:
        URI = None
        STR = None
