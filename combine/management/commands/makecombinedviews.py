import sys
import warnings
from itertools import chain

from django.core.management.base import BaseCommand, CommandError
from django.core.management.commands import makemigrations

from django.apps import apps

from django.db.migrations import Migration
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.utils.deprecation import RemovedInDjango20Warning

from ...base import CombinedModelView
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


class Command(makemigrations.Command):
    help = 'Create combined views after makemigrations is run'

    def _handle_init(self, *app_labels, **options):
        self.loader = MigrationLoader(None)
        self.combined_model_nodes = {tup_id: migration
                                     for tup_id, migration in self.loader.graph.nodes.items()
                                     if any([type(op) == CreateCombinedView for op in migration.operations])}
        self.current_combined_models = gather_combined_models()
        self.current_state = self.loader.project_state()
        self.latest_combined_model_state = self.loader.project_state(nodes=list(self.combined_model_nodes.keys()))

        #obligatory copied code from base makemigrations
        #TODO: decide if the 'makecombinedviews' command should ALWAYS call makemigrations
        #in which case we don't have to copy-paste this initializing code. Workflow becomes
        #makecombinedviews -> migrate rather than makemigrations -> makecombinedviews -> migrate
        self.verbosity = options['verbosity']
        self.interactive = options['interactive']
        self.dry_run = options['dry_run']
        self.merge = options['merge']
        self.empty = options['empty']
        self.migration_name = options['name']
        self.exit_code = options['exit_code']

        if self.exit_code:
            warnings.warn(
                "The --exit option is deprecated in favor of the --check option.",
                RemovedInDjango20Warning
            )

        # Make sure the app they asked for exists
        app_labels = set(app_labels)
        bad_app_labels = set()
        for app_label in app_labels:
            try:
                apps.get_app_config(app_label)
            except LookupError:
                bad_app_labels.add(app_label)
        if bad_app_labels:
            for app_label in bad_app_labels:
                self.stderr.write("App '%s' could not be found. Is it in INSTALLED_APPS?" % app_label)
            sys.exit(2)

    def handle(self, *args, **options):
        self._handle_init(*args, **options)

        models_to_add, models_to_remove = self.get_combined_model_additions_and_removals()
        app_labels_to_use = set([label_and_model[0] for label_and_model in models_to_add]).union(
                            set([label_and_model[0] for label_and_model in models_to_remove]))
        changes = { label: [] for label in app_labels_to_use }
        for app_label, model_name in models_to_add:
            model = self.current_combined_models[(app_label, model_name)]
            donors = model._combiner.donors
            renames = model._combiner.renames.deconstruct()
            operation = CreateCombinedView(model._meta.object_name, donors, renames)
            subclass = type(str("Migration"), (Migration,), {"operations": [operation], "dependencies": []})
            instance = subclass("combinedview", app_label)
            changes[app_label].append(instance)
        # TODO: Record model changes among models
        #I don't actually care about autodetecting anything, I just want the arrange_for_graph() method
        autodetector = MigrationAutodetector(
            self.loader.project_state(),
            ProjectState.from_apps(apps)
        )
        changes = autodetector.arrange_for_graph(changes, self.loader.graph)
        if changes:
            self.write_migration_files(changes)

    def historical_combined_models(self):
        # TODO: Currently counts all combined models that EVER existed, but should instead check the state history to
        # prune out overwritten/deleted combined models
        to_return = {}
        for app_label, migration_name in self.combined_model_nodes.keys():
            migration = self.combined_model_nodes[(app_label, migration_name)]
            model_name = [ o for o in migration.operations if type(o) == CreateCombinedView ][0].name.lower()
            to_return[(app_label, model_name)] = self.latest_combined_model_state.models[(app_label, model_name)]
        return to_return

    def get_combined_model_additions_and_removals(self):
        #returns a 2-tuple of sets of (app_label, model) 2-tuples
        historic_combined_model_identifiers = set(self.historical_combined_models().keys())
        current_combined_model_identifiers = set(self.current_combined_models.keys())
        models_to_add = current_combined_model_identifiers - historic_combined_model_identifiers
        models_to_remove = historic_combined_model_identifiers - current_combined_model_identifiers
        return (models_to_add, models_to_remove)

