import random

import yaml


def roll(sides=6):
    return random.randint(1, sides)


def choose_many(choices):
    chosen = []
    for choice in choices:
        if roll(100) <= choice['odds']:
            chosen.append(choice)
    return chosen


def print_choices(heading, chosen):
    if len(chosen) > 0:
        print()
        print(heading)
    for choice in chosen:
        print('  ' + choice['description'])
    print()


def describe_if_not_none(prefix, choice):
    if choice is not None and ('name' not in choice or choice['name'] != 'none'):
        print(prefix + ' ' + choice['description'])


def choose_one(choices):
    total_weight = sum([x['odds'] for x in choices])

    result = roll(total_weight)

    acc = 0
    for choice in choices:
        acc += choice['odds']
        if acc is not None and acc >= result:
            return choice

    print("could not find choice with total odds {}, roll {}".format(total_weight, result))


def instruction_filter(step, inventory, selection=None):
    if selection is None:
        selection = inventory.data

    if 'class' in step:
        selection = inventory.select_class(step['class'], selection)
    if 'category' in step:
        selection = inventory.select_category(step['category'], selection)
    if 'not_category' in step:
        condition = step['not_category']
        if isinstance(condition, str):
            selection = inventory.select_not_category(step['not_category'], selection)
        else:
            for c in condition:
                selection = inventory.select_not_category(c, selection)
    return selection


class Inventory:
    def __init__(self, data):
        self.data = data

    def select_class(self, classname, data=None):
        if data is None:
            data = self.data
        return [x for x in data if x['class'] == classname]

    def select_category(self, category, data=None):
        if data is None:
            data = self.data
        return [x for x in data if 'categories' in x and category in x['categories']]

    def select_not_category(self, category, data=None):
        if data is None:
            data = self.data
        return [x for x in data if 'categories' not in x or category not in x['categories']]

    def choose_class(self, classname):
        return choose_one(self.select_class(classname))


def load(path, root):
    with open(path) as f:
        return yaml.safe_load(f)[root]


def run(seed=None, scenario_name=None):
    inventory = Inventory(load('inventory.yaml', 'inventory'))
    scenarios = load('scenarios.yaml', 'scenarios')

    if seed is not None:
        random.seed(seed)

    if scenario_name is None:
        scenario = choose_one(scenarios)
    else:
        candidates = [s for s in scenarios if s['name'] == scenario_name]
        if len(candidates) == 0:
            print("Could not find scenario named '{}'".format(scenario_name))
            return
        if len(candidates) > 1:
            print("Found multiple scenarios named '{}'".format(scenario_name))
            return
        scenario = candidates[0]

    print("Instructions:\n")

    for instruction in scenario['instructions']:
        if 'choose_one' in instruction:
            selection = instruction_filter(instruction['choose_one'], inventory)
            describe_if_not_none(instruction['description'], choose_one(selection))
        if 'choose_one_of' in instruction:
            selection = instruction['choose_one_of']
            describe_if_not_none(instruction['description'], choose_one(selection))
        elif 'choose_many' in instruction:
            selection = instruction_filter(instruction['choose_many'], inventory)
            print_choices(instruction['description'], choose_many(selection))
        elif 'choose_many_of' in instruction:
            selection = instruction['choose_many_of']
            print_choices(instruction['description'], choose_many(selection))
        elif len(instruction) == 1:
            print(instruction['description'])

    print()


if __name__ == '__main__':
    run()
