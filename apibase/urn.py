from .settings import apibase_settings


def model_urn(instance, nss=None, nid=None):
    opt = getattr(instance, "_meta", None)
    if not opt:
        return ""
    nid = nid or apibase_settings.URN_NID
    nss = nss or apibase_settings.URN_NSS
    return f"urn:{nid}:{nss}:{opt.app_label}:{opt.model_name}:{instance.pk}"
