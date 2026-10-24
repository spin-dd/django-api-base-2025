"""Public JOIN fan-out inspection shared by GraphQL and REST consumers."""

from django.contrib.auth.models import User

from apibase.querysets import duplicating_join_aliases
from tests.models import Parent, Vendor, VendorTag


def test_single_valued_joins_do_not_need_distinct():
    """A forward FK and a reverse one-to-one each preserve row count."""
    assert duplicating_join_aliases(VendorTag.objects.filter(vendor__name="v")) == set()
    assert duplicating_join_aliases(Parent.objects.filter(profile__bio="b")) == set()


def test_reverse_fk_m2m_and_generic_relation_report_their_aliases():
    """Each multi-value relation identifies the JOIN that can repeat rows."""
    for queryset in (
        Vendor.all_objects.filter(tags__name="t"),
        User.objects.filter(groups__name="g"),
        Vendor.all_objects.filter(notes__text="n"),
    ):
        aliases = duplicating_join_aliases(queryset)
        assert aliases
        assert aliases <= queryset.query.alias_map.keys()


def test_new_duplicating_join_can_be_distinguished_from_a_base_join():
    """Consumers can tell which fan-out JOIN a filter newly introduced."""
    base = Vendor.all_objects.filter(tags__name="t")
    with_notes = base.filter(notes__text="n")

    expected = {alias for alias, join in with_notes.query.alias_map.items() if join.table_name == "tests_vendornote"}
    assert expected
    assert duplicating_join_aliases(with_notes) - duplicating_join_aliases(base) == expected


def test_unreferenced_duplicating_join_is_excluded():
    """An alias left in alias_map after its reference is removed is ignored."""
    queryset = Vendor.all_objects.filter(tags__name="t")
    tag_alias = next(alias for alias, join in queryset.query.alias_map.items() if join.table_name == "tests_vendortag")
    assert duplicating_join_aliases(queryset) == {tag_alias}

    queryset.query.unref_alias(tag_alias)

    assert queryset.query.alias_refcount[tag_alias] == 0
    assert duplicating_join_aliases(queryset) == set()
