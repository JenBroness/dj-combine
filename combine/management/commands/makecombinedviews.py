from unittest.mock import patch
import sys
import warnings
from itertools import chain

from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import makemigrations

from django.apps import apps

from django.db.migrations import Migration
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.operations import CreateModel
from django.db.migrations.state import ProjectState
from django.utils.deprecation import RemovedInDjango20Warning

from ...base import CombinedModelViewBase, CombinedModelView
from ...operations import CreateCombinedView, RemoveCombinedView


#Combined view gathering for custom migrations
def combined_models_of_app(appconfig):
    return [ m for m in appconfig.get_models() if issubclass(m, CombinedModelView) ]


def gather_combined_models(labels = None):
    if labels is None:
        configs = apps.get_app_configs()
    else:
        configs = [ apps.get_app_config(label) for label in labels ]
    model_iter = chain.from_iterable(combined_models_of_app(config) for config in configs)
    return { (model._meta.app_label, model._meta.model_name) : model for model in model_iter }


class CombinedViewCheckingCreateModel(CreateModel):
    def references_model(self, name, app_label=None):
        if any(isinstance(base, CombinedModelViewBase) for base in self.bases):
            return False
        return super(CreateModel, self).references_model(name, app_label)


class Command(makemigrations.Command):
    help = 'Runs makemigrations with some injected code that causes makemigrations to ignore combined model views, ' \
           'then adds the combined model views separately.'


    """To avoid the risk of overloading names from the makemigrations.Command class, I've prefixed all attributes
    I assign to this Command class, or an instance thereof, with '_mcv_' (short for 'Make Combined Views'). This
    convention makes it unlikely that my names will ever collide with Django's, even if updates are made to the
    Django makemigrations script."""
    def _mcv_step2_init(self, *app_labels, **options):
        self._mcv_loader = MigrationLoader(None)
        self._mcv_combined_model_nodes = {tup_id: migration
                                          for tup_id, migration in self._mcv_loader.graph.nodes.items()
                                          if any([type(op) == CreateCombinedView for op in migration.operations])}
        self._mcv_current_combined_models = gather_combined_models()
        self._mcv_current_state = self._mcv_loader.project_state()
        self._mcv_latest_combined_model_state = self._mcv_loader.project_state(nodes=list(self._mcv_combined_model_nodes.keys()))

    def handle(self, *app_labels, **options):

        """A filthy hack. Can't be helped so far as I can tell because Django makes the assumption
        that, other than /the class Model/, all classes whose metaclasses inherit from ModelBase are user-defined
        models that need to have normal migration logic applied to them. This usually doesn't matter, since
        CombinedModelViews are forced to be unmanaged (see combine.base.CombinedModelViewBase). However,
        the CreateModel operation is applied even to unmanaged models. So we have to monkey patch it."""
        with patch('django.db.migrations.operations.CreateModel',
                   new=CombinedViewCheckingCreateModel):
            super(Command, self).handle(*app_labels, **options)

        #TODO: Handle wacky makemigrations options such as --dry-run.

        self._mcv_step2_init(*app_labels, **options)

        models_to_add, models_to_remove = self._mcv_get_combined_model_additions_and_removals()
        app_labels_to_use = set([label_and_model[0] for label_and_model in models_to_add]).union(
                            set([label_and_model[0] for label_and_model in models_to_remove]))
        operations = { label: [] for label in app_labels_to_use }
        for app_label, model_name in models_to_add:
            model = self._mcv_current_combined_models[(app_label, model_name)]
            donors = model._combiner.donors
            renames = model._combiner.renames.deconstruct()
            operations[app_label].append(CreateCombinedView(model._meta.object_name, donors, renames))
        changes = {}
        for label, op_list in operations.items():
            subclass = type(str("Migration"), (Migration,), {"operations": op_list, "dependencies": []})
            instance = subclass("combinedview", app_label)
            changes[label] = [instance]
        # TODO: Record model changes among models
        #I don't actually care about autodetecting anything, I just want the arrange_for_graph() method
        autodetector = MigrationAutodetector(
            self._mcv_loader.project_state(),
            ProjectState.from_apps(apps)
        )
        changes = autodetector.arrange_for_graph(changes, self._mcv_loader.graph)
        if changes:
            self.write_migration_files(changes)

    def _mcv_historical_combined_models(self):
        # TODO: Currently counts all combined models that EVER existed, but should instead check the state history to
        # prune out overwritten/deleted combined models
        to_return = {}
        for app_label, migration_name in self._mcv_combined_model_nodes.keys():
            migration = self._mcv_combined_model_nodes[(app_label, migration_name)]
            model_name = [ o for o in migration.operations if type(o) == CreateCombinedView ][0].name.lower()
            to_return[(app_label, model_name)] = self._mcv_latest_combined_model_state.models[(app_label, model_name)]
        return to_return

    def _mcv_get_combined_model_additions_and_removals(self):
        #returns a 2-tuple of sets of (app_label, model) 2-tuples
        historic_combined_model_identifiers = set(self._mcv_historical_combined_models().keys())
        current_combined_model_identifiers = set(self._mcv_current_combined_models.keys())
        models_to_add = current_combined_model_identifiers - historic_combined_model_identifiers
        models_to_remove = historic_combined_model_identifiers - current_combined_model_identifiers
        return (models_to_add, models_to_remove)