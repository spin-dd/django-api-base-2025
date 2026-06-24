from types import SimpleNamespace

import pytest

from apibase.permissions import Permission, can, has_perms

PERM = "tests.change_parent"
OTHER_PERM = "tests.view_parent"


class _User:
    def __init__(self, *, permissions=(), is_staff=False):
        self.permissions = set(permissions)
        self.is_staff = is_staff

    def has_perm(self, permission):
        return permission in self.permissions


def _request(user, method):
    return SimpleNamespace(user=user, method=method)


def _info(user):
    return SimpleNamespace(context=SimpleNamespace(user=user))


class _PrivatePermission(Permission):
    PERM_CODE = PERM
    PRIVATE = True


class _PublicPermission(Permission):
    PERM_CODE = PERM
    PRIVATE = False


@pytest.mark.parametrize(
    ("user", "permission", "method", "private", "expected"),
    [
        pytest.param(_User(permissions={PERM}), PERM, "POST", True, True, id="has-perm-wins-private-unsafe"),
        pytest.param(_User(is_staff=True), PERM, "POST", True, True, id="staff-wins-private-unsafe"),
        pytest.param(_User(), PERM, "GET", False, True, id="public-safe-read"),
        pytest.param(_User(), PERM, "HEAD", False, True, id="public-safe-head"),
        pytest.param(_User(), PERM, "POST", False, False, id="public-unsafe-write"),
        pytest.param(_User(), PERM, "GET", True, False, id="private-safe-denied-without-privilege"),
        pytest.param(_User(permissions={OTHER_PERM}), PERM, "GET", True, False, id="wrong-permission-denied"),
        pytest.param(None, PERM, "GET", True, False, id="none-user-private-denied"),
        pytest.param(None, PERM, "GET", False, True, id="none-user-public-safe-read"),
        pytest.param(None, PERM, None, False, False, id="none-user-public-methodless-denied"),
    ],
)
def test_can_unifies_permission_staff_and_public_safe_rules(user, permission, method, private, expected):
    assert can(user, permission, method=method, private=private) is expected


@pytest.mark.parametrize(
    ("permission", "user", "method", "expected"),
    [
        pytest.param(_PrivatePermission(), _User(permissions={PERM}), "POST", True, id="explicit-permission"),
        pytest.param(_PrivatePermission(), _User(is_staff=True), "POST", True, id="staff-private-write"),
        pytest.param(_PrivatePermission(), _User(), "GET", False, id="private-safe-denied"),
        pytest.param(_PublicPermission(), _User(), "GET", True, id="public-safe-read"),
        pytest.param(_PublicPermission(), _User(), "POST", False, id="public-unsafe-write"),
        pytest.param(_PublicPermission(), None, "GET", False, id="rest-keeps-missing-user-guard"),
    ],
)
def test_has_permission_delegates_rest_context_to_can(permission, user, method, expected):
    assert permission.has_permission(_request(user, method), view=None) is expected


@pytest.mark.parametrize(
    ("permission", "user", "expected"),
    [
        pytest.param(_PrivatePermission(), _User(permissions={PERM}), True, id="explicit-permission"),
        pytest.param(_PrivatePermission(), _User(is_staff=True), True, id="staff"),
        pytest.param(_PrivatePermission(), _User(), False, id="private-no-privilege"),
        pytest.param(_PublicPermission(), _User(), True, id="public-query-is-safe-read"),
        pytest.param(_PublicPermission(), None, True, id="public-query-allows-none-user"),
    ],
)
def test_has_query_permission_delegates_graphql_query_context_to_can(permission, user, expected):
    assert permission.has_query_permission(queryset=None, info=_info(user)) is expected


@pytest.mark.parametrize(
    ("permission_class", "user", "expected"),
    [
        pytest.param(_PrivatePermission, _User(permissions={PERM}), True, id="explicit-permission"),
        pytest.param(_PrivatePermission, _User(is_staff=True), True, id="staff"),
        pytest.param(_PrivatePermission, _User(), False, id="private-no-privilege"),
        pytest.param(_PublicPermission, _User(), False, id="public-methodless-no-safe-read"),
    ],
)
def test_check_info_delegates_methodless_graphql_context_to_can(permission_class, user, expected):
    assert permission_class.check_info(_info(user)) is expected


def test_has_perms_decorator_uses_methodless_unified_permission():
    def resolver(self, info):
        return "allowed"

    wrapped = has_perms(None, PERM)(resolver)

    assert wrapped(object(), _info(_User(is_staff=True))) == "allowed"
    assert wrapped(object(), _info(_User())) is None
