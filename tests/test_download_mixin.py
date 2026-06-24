import builtins
from types import SimpleNamespace

from django.http import HttpResponse

from apibase.viewsets import DownloadMixin


class _DownloadViewSet(DownloadMixin):
    def __init__(self):
        self.instance = SimpleNamespace(document=object())
        self.captured_format = None

    def get_object(self):
        return self.instance

    def create_download_filefield_response(self, request, instance, field, format=None):
        self.captured_format = format
        return HttpResponse("download")

    def get_download_filefield_name(self, instance, field):
        return "document.pdf"


def test_download_filefield_passes_action_format_to_response_factory():
    viewset = _DownloadViewSet()

    viewset.download_filefield(request=object(), pk=1, format="pdf", field="document")

    assert viewset.captured_format == "pdf"
    assert viewset.captured_format is not builtins.format
