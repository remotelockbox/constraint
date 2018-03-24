import random

import yaml


def roll(sides):
    return random.randint(1, sides)


def choose_one(choices):
    total_weight = sum([x['odds'] for x in choices])

    result = roll(total_weight)

    acc = 0
    for choice in choices:
        acc += choice['odds']
        if acc is not None and acc >= result:
            return choice

    print("could not find choice with total odds {}, roll {}".format(total_weight, result))


def choose_many(choices):
    chosen = []
    for choice in choices:
        if roll(100) <= choice['odds']:
            chosen.append(choice)
    return chosen


def print_choices(heading, selection):
    if len(selection) > 0:
        print()
        print(heading)
    for choice in selection:
        print('  ' + choice['description'])
    print()


def describe_if_not_none(prefix, choice):
    if choice is not None and ('name' not in choice or choice['name'] != 'none'):
        print(prefix + ' ' + choice['description'])


class Inventory:
    def __init__(self, data):
        self.data = data

    def __iter__(self):
        return self.data.__iter__()

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

    def choose_one(self):
        return choose_one(self)

    def choose_many(self):
        return choose_many(self)


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
            selection = inventory.select_by_instruction(instruction['choose_one'])
            describe_if_not_none(instruction['description'], selection.choose_one())
        if 'choose_one_of' in instruction:
            selection = Inventory(instruction['choose_one_of'])
            describe_if_not_none(instruction['description'], selection.choose_one())
        elif 'choose_many' in instruction:
            selection = inventory.select_by_instruction(instruction['choose_many'])
            print_choices(instruction['description'], choose_many(selection))
        elif 'choose_many_of' in instruction:
            selection = Inventory(instruction['choose_many_of'])
            print_choices(instruction['description'], selection.choose_many())
        elif len(instruction) == 1:
            print(instruction['description'])

    print()


if __name__ == '__main__':
    run()
