"""Real database routers for the nested-write transaction tests."""


class NestedWriteRouter:
    def db_for_read(self, model, **hints):
        if model._meta.label_lower in {"tests.parent", "tests.child"}:
            return "nested"
        return None

    def db_for_write(self, model, **hints):
        return self.db_for_read(model, **hints)


class InstanceHintWriteRouter(NestedWriteRouter):
    """Parent updates must follow the database of the existing instance."""

    def db_for_write(self, model, **hints):
        if model._meta.label_lower == "tests.parent":
            return None
        return super().db_for_write(model, **hints)
