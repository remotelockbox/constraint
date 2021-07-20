import random

from collections import Collection
from collections.abc import Iterator
from typing import Optional

import jsonref
import jsonschema
import yaml

from . import rng


def load_inventory(path):
    with open(path) as f, open("schema/inventory.schema.json") as schema_file:
        schema = jsonref.load(schema_file)
        contents = yaml.safe_load(f)
        validator = jsonschema.Draft7Validator(schema)
        errors = validator.iter_errors(contents)
        tree = jsonschema.ErrorTree(errors)
        if tree.total_errors > 0:
            error: jsonschema.ValidationError = jsonschema.exceptions.best_match(
                validator.iter_errors(contents))
            msg = f"error reading {f.name}: {error.message}"
            if len(error.path) >= 1:
                msg += '\n' \
                    f'The error is located in item #{error.path[0]} of the inventory'
            raise ValueError(msg)
        return Inventory(contents)


class Inventory(Collection):
    """ Represents an inventory file and provides
        methods for selecting items from the inventory
    """

    def __init__(self, data: list[dict]):
        self.data: list[dict] = data

    def __contains__(self, o: object) -> bool:
        return self.data.__contains__(o)

    def __iter__(self) -> Iterator[dict]:
        return self.data.__iter__()

    def __len__(self) -> int:
        return self.data.__len__()

    def select_class(self, classname):
        return Inventory([x for x in self.data if x['class'] == classname])

    def select_category(self, category):
        return Inventory([x for x in self.data if 'categories' in x and category in x['categories']])

    def select_not_category(self, category):
        return Inventory([x for x in self.data if 'categories' not in x or category not in x['categories']])

    def select_by_instruction(self, step):
        selection = self
        if 'class' in step:
            selection = selection.select_class(step['class'])
        if 'category' in step:
            selection = selection.select_category(step['category'])
        if 'not_category' in step:
            condition = step['not_category']
            if isinstance(condition, str):
                selection = selection.select_not_category(step['not_category'])
            else:
                for c in condition:
                    selection = selection.select_not_category(c)
        return selection

    def choose_many_items_including_required(self, required_substrings, odds=1.0) -> list[str]:
        choices = []
        shuffled_data = list(self.data)
        random.shuffle(shuffled_data)

        for substring in required_substrings:
            for x in shuffled_data:
                if substring in x['description']:
                    choices.append(x['description'])
                    break

        more = self.choose_many_items(odds)
        for choice in more:
            if choice['description'] not in choices:
                choices.append(choice['description'])
        return choices

    def choose_item_or_required(self, required_substrings, odds=1.0) -> Optional[str]:
        """ if a choice matches a requirement, choose it. Otherwise choose at random according to odds. """
        shuffled_data = list(self.data)
        random.shuffle(shuffled_data)

        for substring in required_substrings:
            for x in shuffled_data:
                if substring in x['description']:
                    return x['description']
        return self.choose_item(odds)

    def choose_item(self, odds=1.0) -> Optional[dict]:
        return rng.maybe_choose_item(self, odds)

    def choose_many_items(self, odds=1.0) -> list[dict]:
        return rng.choose_many_items(self, odds)
