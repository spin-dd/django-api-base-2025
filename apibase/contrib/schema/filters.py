"""
https://django-filter.readthedocs.io/en/master/
"""

from apibase.filters import BaseFilter, FanOutBaseFilter

from .. import models


class UserFilter(FanOutBaseFilter):
    class Meta:
        model = models.User
        exclude = [""]


class GroupFilter(FanOutBaseFilter):
    class Meta:
        model = models.Group
        exclude = [""]


class PermissionFilter(BaseFilter):
    class Meta:
        model = models.Permission
        exclude = [""]


class ContentTypeFilter(BaseFilter):
    class Meta:
        model = models.ContentType
        exclude = [""]
