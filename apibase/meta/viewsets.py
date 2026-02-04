from itertools import chain

from django.apps import apps
from django.contrib.contenttypes.models import ContentType

from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from . import serializers


class ModelFieldViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request, app_label=None, model_name=None, *args, **kwargs):
        if model_name:
            models = [ContentType.objects.get_by_natural_key(app_label, model_name).model_class()]
        elif app_label:
            models = apps.get_app_config(app_label).models.values()
        else:
            models = apps.get_models()

        fields = list(chain(*(model_class._meta.fields for model_class in models)))

        ser = serializers.ModelFieldSerializer(fields, many=True)
        return Response(ser.data)

    def retrieve(self, request, app_label, model_name, field_name, *args, **kwargs):
        model_class = ContentType.objects.get_by_natural_key(app_label, model_name).model_class()
        field = model_class._meta.get_field(field_name)
        ser = serializers.ModelFieldSerializer(field)
        return Response(ser.data)
