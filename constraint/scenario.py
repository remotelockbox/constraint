import jsonref
import jsonschema
import yaml


def load_scenario(path):
    with open(path) as f, open("schema/scenario.schema.json") as schema_file:
        schema = jsonref.load(schema_file)
        contents = yaml.safe_load(f)

        validator = jsonschema.Draft7Validator(schema)
        errors = validator.iter_errors(contents)
        tree = jsonschema.ErrorTree(errors)
        if tree.total_errors > 0:
            error: jsonschema.ValidationError = jsonschema.exceptions.best_match(
                validator.iter_errors(contents))
            msg = f"error reading {f.name}: {error.message}"
            if len(error.path) >= 3:
                msg += '\n' \
                    f'The error is located in the #{error.path[2]} ' \
                    f'instruction of the "{contents[error.path[0]]["name"]}" scenario'
            raise ValueError(msg)

        return contents
