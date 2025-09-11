from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions
from rest_framework.filters import OrderingFilter, SearchFilter

from apibase.viewsets import BaseModelViewSet

from .filters import BookFilter
from .models import Book
from .serializers import BookSerializer


class BookViewSet(BaseModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = BookFilter
    search_fields = ["title", "author"]
    ordering_fields = ["id", "published", "created_at"]
    fields_query = "fields"
