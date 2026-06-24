from __future__ import annotations

from typing import Any

from django.urls import NoReverseMatch, reverse

from .urn import model_urn


def urn(instance: Any, nss: str | None = None, nid: str | None = None) -> str:
    return model_urn(instance, nss=nss, nid=nid)


def endpoint(instance: Any, url_name: str | None = None, pk_name: str = "pk") -> str | None:
    try:
        if hasattr(instance, "get_endpoint_url"):
            return instance.get_endpoint_url()

        opts = instance._meta
        name = url_name or f"api-{opts.app_label}-{opts.model_name}-detail"
        return reverse(name, kwargs={pk_name: instance.pk})
    except (AttributeError, NoReverseMatch):
        return ""


def display(instance: Any) -> str:
    return str(instance)
