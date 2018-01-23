#SQL writing
INDENT2 = "  "
INDENT7 = "       "
X_AS_Y = "{x} AS {y}"

DROP_VIEW = """
DROP VIEW IF EXISTS {db_view}"""

CREATE_VIEW = """
CREATE OR REPLACE VIEW {db_view} AS
{selection}"""

SELECTION_WITH_UNION =\
INDENT2 + "SELECT {id_construction}{fields_and_renames}" +\
INDENT2 + INDENT7 + "FROM {db_table}\n" + \
INDENT2 + "UNION\n" +\
"{next_selection}"

SELECTION_FINAL =\
INDENT2 + "SELECT {id_construction}{fields_and_renames}" +\
INDENT2 + INDENT7 + "FROM {db_table}"

ID_CONSTRUCTION = X_AS_Y.format(x="concat('{model_table}.', {model_pk}::text)", y="{id}")

FIELDS_AND_RENAMES =",\n" +\
INDENT2 + INDENT7 + "{field_and_rename}{fields_and_renames}"

def construction_sql(view_model, donors, renames):
    db_view = view_model._meta.db_table
    selection = selection_sql(view_model, donors, renames)
    return CREATE_VIEW.format(db_view=db_view, selection=selection)


def destruction_sql(view_model):
    db_view = view_model._meta.db_table
    return DROP_VIEW.format(db_view=db_view)


def id_construction(view_model, contributor_model):
    return ID_CONSTRUCTION.format(model_table=contributor_model._meta.db_table,
                                  model_pk=contributor_model._meta.pk.name,
                                  id=view_model._meta.pk.name)


def selection_sql(view_model, donors, renames):
    reverse_donors = list(reversed(donors))
    final_contributor = reverse_donors.pop(0)
    selection = SELECTION_FINAL.format(id_construction=id_construction(view_model, final_contributor),
                                       fields_and_renames=fields_and_renames(view_model, final_contributor, renames),
                                       db_table=final_contributor._meta.db_table)
    for contributor_model in reverse_donors:
        selection = SELECTION_WITH_UNION.format(id_construction=id_construction(view_model, contributor_model),
                                                fields_and_renames=fields_and_renames(view_model, contributor_model, renames),
                                                db_table=contributor_model._meta.db_table,
                                                next_selection=selection)
    return selection + '\n'


def fields_and_renames(view_model, contributing_model, renames):
    fields = [ field for field in list(reversed(view_model._meta.fields)) if field is not view_model._meta.pk ]
    fields_and_renames = ""
    for field in fields:
        fields_and_renames = FIELDS_AND_RENAMES.format(field_and_rename=field_and_rename(field, contributing_model, renames),
                                                       fields_and_renames=fields_and_renames)
    return fields_and_renames + '\n'


def field_and_rename(field, contributing_model, renames):
    new_column = field.column
    old_column = None
    try:
        old_column = renames[new_column][contributing_model]
    except KeyError:
        pass
    if old_column is None:
        return new_column
    return X_AS_Y.format(x=old_column,
                         y=new_column)