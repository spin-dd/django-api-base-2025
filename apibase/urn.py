import re

from django.contrib.sites.shortcuts import get_current_site

from .settings import apibase_settings

URN_ELEMENTS = ["nid", "nss", "app_label", "model_name"]
URL_FORMAT = "{scheme}://{service}{domain}{prefix}/{app_label}/{model_name}/{others}"


def model_urn(instance, nss=None, nid=None):
    opt = getattr(instance, "_meta", None)
    if not opt:
        return ""
    nid = nid or apibase_settings.URN_NID
    nss = nss or apibase_settings.URN_NSS
    return f"urn:{nid}:{nss}:{opt.app_label}:{opt.model_name}:{instance.pk}"


def parse_urn(urn, prefix="urn", nid=None):
    prefix, *ma = re.findall(r"([^:]+)", urn)
    if prefix == prefix and len(ma) >= len(URN_ELEMENTS):
        nid = nid or apibase_settings.URN_NID
        res = dict(others=ma[len(URN_ELEMENTS) :], **dict(zip(URN_ELEMENTS, ma, strict=False)))
        if res["nid"] == nid:
            return res


def rest_endpoint_from_urn(urn, domain=None, nid=None, prefix="/api/rest", request=None):
    if not domain:
        if apibase_settings.DOMAIN:
            domain = apibase_settings.DOMAIN
        else:
            domain = get_current_site(request).domain
            _, domain = re.search(r"(?:([^\.]+)\.)?(.+)", domain).groups()

    nid = nid or apibase_settings.URN_NID
    urn_dict = parse_urn(urn, nid=nid)
    if urn_dict:
        if urn_dict["nss"] == "self":
            service = ""
        else:
            service = urn_dict["nss"] + "."

        others = urn_dict["others"] and ("/".join(urn_dict["others"]) + "/") or ""

        return URL_FORMAT.format(
            scheme=apibase_settings.SCHEME,
            service=service,
            domain=domain,
            prefix=prefix,
            app_label=urn_dict["app_label"],
            model_name=urn_dict["model_name"],
            others=others,
        )
    return None
