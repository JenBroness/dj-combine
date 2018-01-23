from django.db.migrations.operations.base import Operation
from django.db import router

from .sqlfuncs import construction_sql, destruction_sql


class CombinedViewOperation(Operation):

    reduces_to_sql = True
    reversible = True

    def __init__(self, name, donors, renames, hints=None):
        self.name = name
        self.donors = donors # (app_label, model) list
        self.renames = renames
        self.hints = hints

    def state_forwards(self, app_label, state):
        # model should be added as unmanaged already so python state should not change
        pass

    def _database_create(self, app_label, schema_editor, state):
        view_model = self._get_reconstructed_view_model(app_label, state)
        donors = self._get_reconstructed_donors(state)
        renames = self._get_reconstructed_renames(state)
        create_sql = construction_sql(view_model, donors, renames)
        self._run_sql(create_sql, schema_editor, app_label)

    def _database_remove(self, app_label, schema_editor, state):
        view_model = self._get_reconstructed_view_model(app_label, state)
        remove_sql = destruction_sql(view_model)
        self._run_sql(remove_sql, schema_editor, app_label)

    def _run_sql(self, sqls, schema_editor, app_label):
        if router.allow_migrate(schema_editor.connection.alias, app_label, **self.hints):
            statements = schema_editor.connection.ops.prepare_sql_script(sqls)
            for statement in statements:
                schema_editor.execute(statement, params=None)

    def _get_reconstructed_view_model(self, app_label, state):
        return state.apps.get_model(app_label, self.name)

    def _get_reconstructed_donors(self, state):
        return [state.apps.get_model(app_label, donor_name) for app_label, donor_name in self.donors]

    def _get_reconstructed_renames(self, state):
        renames = {}
        for new_field_name, renames_for_field in self.renames.items():
            renames[new_field_name] = {}
            for app_label, donor_name, old_field_name in renames_for_field:
                renames[new_field_name][state.apps.get_model(app_label, donor_name)] = old_field_name
        return renames

    def describe(self):
        return "Create view model {} combining {}".format(self.name, self.donors)

class CreateCombinedView(CombinedViewOperation):

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        self._database_create(app_label, schema_editor, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        self._database_remove(app_label, schema_editor, from_state)

    def describe(self):
        return "Create view model {} combining {}".format(self.name, self.donors)

class RemoveCombinedView(CombinedViewOperation):

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        self._database_remove(app_label, schema_editor, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        self._database_create(app_label, schema_editor, from_state)

    def describe(self):
        return "Create view model {} combining {}".format(self.name, self.donors)