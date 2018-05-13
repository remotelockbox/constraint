import random
import textwrap
from glob import glob

import yaml


class Output:
    def __init__(self):
        self._written = False

    def println(self, msg):
        self._written = True

        unwrapped_lines = msg.splitlines()
        for unwrapped in unwrapped_lines:
            for line in textwrap.wrap(str(unwrapped), 68, subsequent_indent=self.__count_indent(unwrapped)):
                print(line)
        
    def start_paragraph(self):
        if self._written:
            print()
        self._written = False

    @staticmethod
    def __count_indent(msg):
        indent = ''
        for c in msg:
            if c in [' ', '-']:
                indent += ' '
            else:
                break
        return indent


out = Output()


def roll(sides):
    return random.randint(1, sides)


# Randomly choose one item from a list weighed by their odds
def choose_one(choices):
    total_weight = sum([x['odds'] for x in choices])

    result = roll(total_weight)

    acc = 0
    for choice in choices:
        acc += choice['odds']
        if acc is not None and acc >= result:
            return choice

    out.println("could not find choice with total odds {}, roll {}".format(total_weight, result))


# Choose one weighted item or None depending on the odds (0-1.0)
def maybe_choose_one(choices, odds: float):
    if random.random() < odds:
        return choose_one(choices)
    return None


# Return all choices that passed a 0-100 roll under its odds
def choose_many(choices, odds_adjustment=1.0):
    chosen = []
    for choice in choices:
        if roll(100) <= choice['odds'] * odds_adjustment:
            chosen.append(choice)
    return chosen


def print_choices(heading, selection):
    if len(selection) > 0:
        out.start_paragraph()
        out.println(heading)

    for choice in selection:
        out.println('  - ' + choice['description'])


def describe_if_not_none(prefix, choice):
    if choice is not None and ('name' not in choice or choice['name'] != 'none'):
        out.start_paragraph()
        out.println(' - ' + prefix + ' ' + choice['description'])


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

    def choose_one(self, odds=1.0):
        return maybe_choose_one(self, odds)

    def choose_many(self, odds=1.0):
        return choose_many(self, odds)


def load(path):
    with open(path) as f:
        return yaml.safe_load(f)


def run(scenario_name='*', seed=None):
    inventory = Inventory(load('inventory.yaml'))

    files = glob('scenarios/{}.yaml'.format(scenario_name))

    if len(files) == 0:
        out.println("Could not find files matching name: ".format(scenario_name))
        return

    scenarios = []
    for file in files:
        scenarios += load(file)

    if seed is not None:
        random.seed(seed)

    scenario = choose_one(scenarios)

    out.println("Instructions:")

    for instruction in scenario['instructions']:
        # An instruction can alter the odds of a selection from choose_many.
        # Less than 100 will reduce the number of chosen items while
        # greater than 100 will increase the number of items chosen.
        adjust_odds = instruction.get('odds', 100) / 100.0

        if 'choose_one' in instruction:
            selection = inventory.select_by_instruction(instruction['choose_one'])
            describe_if_not_none(instruction['description'], selection.choose_one(adjust_odds))
        if 'choose_one_of' in instruction:
            selection = Inventory(instruction['choose_one_of'])
            describe_if_not_none(instruction['description'], selection.choose_one(adjust_odds))
        elif 'choose_many' in instruction:
            selection = inventory.select_by_instruction(instruction['choose_many'])
            print_choices(instruction['description'], selection.choose_many(adjust_odds))
        elif 'choose_many_of' in instruction:
            selection = Inventory(instruction['choose_many_of'])
            print_choices(instruction['description'], selection.choose_many(adjust_odds))
        elif len(instruction) == 1:
            out.start_paragraph()
            out.println(instruction['description'])


if __name__ == '__main__':
    run()
