from __future__ import annotations

from functools import wraps
from logging import getLogger
from typing import Any

from rest_framework import permissions

logger = getLogger(__name__)


def has_perms(func: Any, permission: str | None, *args: Any, **kwargs: Any) -> Any:
    def wrapper(resolver: Any) -> Any:
        @wraps(resolver)
        def wrapped(self: Any, info: Any, *func_args: Any, **func_kwargs: Any) -> Any:
            if not can(info.context.user, permission, method=None, private=True):
                return None
            return resolver(self, info, *func_args, **func_kwargs)

        return wrapped

    return wrapper


def is_safe_method(request: Any) -> bool:
    method = getattr(request, "method", request)
    return method in permissions.SAFE_METHODS


def can(user: Any, perm: str | None, *, method: str | None = None, private: bool = True) -> bool:
    has_perm = getattr(user, "has_perm", None)
    if callable(has_perm) and has_perm(perm):
        return True
    if getattr(user, "is_staff", False):
        return True
    if not private and is_safe_method(method):
        return True
    return False


class Permission(permissions.IsAuthenticated):
    PERM_CODE = None
    PRIVATE = True

    @classmethod
    def has(cls, func: Any) -> Any:
        @wraps(func)
        def wrapped(self: Any, info: Any, *func_args: Any, **func_kwargs: Any) -> Any:
            if not cls.check_info(info, *func_args, **func_kwargs):
                return None
            return func(self, info, *func_args, **func_kwargs)

        return wrapped

    @classmethod
    def check_info(cls, info: Any, *args: Any, **kwargs: Any) -> bool:
        return can(info.context.user, cls.PERM_CODE, method=None, private=cls.PRIVATE)

    def has_permission(self, request: Any, view: Any) -> bool:
        if not request.user:
            return False
        isvalid = can(request.user, self.PERM_CODE, method=request.method, private=self.PRIVATE)
        if not isvalid:
            logger.info(f"{request.user} has not {self.PERM_CODE}")
        return isvalid

    def has_query_permission(self, queryset: Any, info: Any, permcode: str | None = None) -> bool:
        """check for graphql query"""
        permcode = permcode or self.PERM_CODE
        return can(info.context.user, permcode, method="GET", private=self.PRIVATE)
