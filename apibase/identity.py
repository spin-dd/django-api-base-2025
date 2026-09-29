from __future__ import annotations

from typing import Any, Protocol, TypeVar

from django.urls import reverse

from .urn import model_urn

_Fallback = TypeVar("_Fallback")


class AbsoluteUriBuilder(Protocol):
    def build_absolute_uri(self, location: str | None = None) -> str: ...


def urn(instance: Any, nss: str | None = None, nid: str | None = None) -> str:
    return model_urn(instance, nss=nss, nid=nid)


def endpoint(instance: Any, url_name: str | None = None, pk_name: str = "pk") -> str | None:
    try:
        if hasattr(instance, "get_endpoint_url"):
            return instance.get_endpoint_url()

        opts = instance._meta
        name = url_name or f"api-{opts.app_label}-{opts.model_name}-detail"
        return reverse(name, kwargs={pk_name: instance.pk})
    except Exception:
        # Optional display field: fail soft to "" rather than 500 the whole
        # serialization (matches the pre-refactor drf_endpoint contract).
        return ""


def display(instance: Any) -> str:
    return str(instance)


def absolute_uri(
    path: str | None,
    *,
    builder: AbsoluteUriBuilder | None,
    fallback: _Fallback,
) -> str | _Fallback:
    if builder is not None:
        return builder.build_absolute_uri(path)
    return fallback
