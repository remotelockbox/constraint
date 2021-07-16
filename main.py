import os.path
import random
import shutil
import textwrap
from collections.abc import Iterator, Iterable
from glob import glob

import yaml
from jinja2 import Template


class Output:
    def __init__(self):
        self._para_written = False
        self.width = min(72, shutil.get_terminal_size()[0])

    def println(self, msg):
        self._para_written = True

        unwrapped_lines = msg.splitlines()
        for unwrapped in unwrapped_lines:
            for line in textwrap.wrap(str(unwrapped),
                                      self.width,
                                      subsequent_indent=self.__count_indent(unwrapped)):
                print(line)

    def start_paragraph(self):
        if self._para_written:
            print()
        self._para_written = False

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


def roll(sides: int):
    return random.randint(1, sides)


# Randomly choose one item from a list weighed by their odds
def choose_one(choices: Iterable[dict]):
    total_weight = sum([x['odds'] for x in choices])

    result = roll(total_weight)

    acc = 0
    for choice in choices:
        acc += choice['odds']
        if acc is not None and acc >= result:
            return choice

    out.println("could not find choice with total odds {}, roll {}".format(total_weight, result))


# Choose one weighted item or None depending on the odds (0-1.0)
def maybe_choose_one(choices: Iterable[dict], odds: float):
    if random.random() < odds:
        return choose_one(choices)
    return None


# Return all choices that passed a 0-100 roll under its odds
def choose_many(choices: Iterable[dict], odds_adjustment=1.0):
    chosen = []
    for choice in choices:
        if roll(100) <= choice['odds'] * odds_adjustment:
            chosen.append(choice)
    return chosen


def print_choices(heading: str, selection: list, env):
    if len(selection) > 0:
        out.start_paragraph()
        out.println(heading)

    for choice in selection:
        out.println('  - ' + choice['description'])
        if 'set' in choice.keys():
            eval_set(env, choice['set'])


def describe_if_not_none(prefix: str, choice: dict, env):
    if choice is not None and ('name' not in choice or choice['name'] != 'none'):
        out.start_paragraph()
        out.println(' - ' + prefix + ' ' + choice['description'])
        if 'set' in choice.keys():
            eval_set(env, choice['set'])


class Inventory:
    def __init__(self, data: list[dict]):
        self.data: list[dict] = data

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

    def choose_many_including_required(self, required_substrings, odds=1.0):
        choices = []
        shuffled_data = list(self.data)
        random.shuffle(shuffled_data)

        for substring in required_substrings:
            for x in shuffled_data:
                if 'description' in x and substring in x['description']:
                    choices.append(x)
                    break

        more = self.choose_many(odds)
        for choice in more:
            if choice not in choices:
                choices.append(choice)
        return choices

    def choose_one_or_required(self, required_substrings, odds=1.0):
        """ if a choice matches a requirement, choose it. Otherwise choose at random according to odds. """
        shuffled_data = list(self.data)
        random.shuffle(shuffled_data)

        for substring in required_substrings:
            for x in shuffled_data:
                if 'description' in x and substring in x['description']:
                    return x
        return self.choose_one(odds)

    def choose_one(self, odds=1.0):
        return maybe_choose_one(self, odds)

    def choose_many(self, odds=1.0):
        return choose_many(self, odds)


def load(path):
    with open(path) as f:
        return yaml.safe_load(f)


def interpolate(obj, env):
    """ interpolate strings inside structures recursively """
    if isinstance(obj, str):
        template = Template(obj)
        return template.render(env)
    elif isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            result[k] = interpolate(v, env)
        return result
    elif isinstance(obj, list):
        return [interpolate(item, env) for item in obj]
    else:
        return obj


def run(scenario_names=None, desired_inventory=None,
        inventory_file='inventory.yaml', scenario_path='scenarios/', seed=None):
    """ Build and print out a scenario.

    Args:
        scenario_names (:obj:`list` of :obj:`str`, optional): If specified,
            choose scenarios that matches the given glob patterns.
            Wildcards are supported. For example, "bed_*" would match all scenario files that start with "bed_".
        desired_inventory (:obj:`list` of :obj:`str`, optional): A list of inventory items that should be chosen
            if the scenario allows. If you plan to wear/use something specific, add it to this list.
            This matches substrings so "cuff" would match "leather cuffs" or "handcuffs". In case of multiple
            matches, one will be chosen at random.
        inventory_file (str): The yaml file to read the inventory from.
        scenario_path (str): search path for scenario files.
        seed (int): Pre-seed the random number generator so every run produces the same results.
    """

    if scenario_names is None:
        scenario_names = ['*']
    if desired_inventory is None:
        desired_inventory = []

    inventory = Inventory(load(inventory_file))

    files = []
    for name in scenario_names:
        if name.split(".")[-1] != 'yaml':
            name = name + ".yaml"

        files += glob(os.path.join(scenario_path, name))

    if not files:
        out.println("Could not find matching scenario files")
        return
    if scenario_names != ['*']:
        out.println("Matching scenarios:\n  " + ', '.join([os.path.basename(f) for f in files]))
        out.start_paragraph()

    scenarios = []
    for file in files:
        scenarios += load(file)

    if seed is not None:
        random.seed(seed)

    scenario = choose_one(scenarios)

    eval(desired_inventory, inventory, scenario)


def eval(desired_inventory, inventory, scenario):
    out.println("Instructions:")

    env = {}

    for instruction in scenario['instructions']:
        # apply template substitutions
        instruction = interpolate(instruction, env)
        description = instruction.get('description')

        odds = instruction.get('odds', 100)

        # if odds is a string, treat it as a variable
        if isinstance(odds, str):
            odds = env[odds]
        if odds is None:
            odds = 100

        # An instruction can alter the odds of a selection from choose_many.
        # Less than 100 will reduce the number of chosen items while
        # greater than 100 will increase the number of items chosen.
        adjust_odds = odds / 100.0

        # Chance of displaying a description or setting a variable (in the absence of a 'choose' statement)
        chance = random.random()

        if 'description' in instruction:
            if 'choose_one' in instruction:
                selection = inventory.select_by_instruction(instruction['choose_one'])
                describe_if_not_none(description, selection.choose_one_or_required(desired_inventory, adjust_odds), env)
            if 'choose_one_of' in instruction:
                selection = Inventory(instruction['choose_one_of'])
                describe_if_not_none(description, selection.choose_one_or_required(desired_inventory, adjust_odds), env)
            elif 'choose_many' in instruction:
                selection = inventory.select_by_instruction(instruction['choose_many'])
                print_choices(description, selection.choose_many_including_required(desired_inventory, adjust_odds), env)
            elif 'choose_many_of' in instruction:
                selection = Inventory(instruction['choose_many_of'])
                print_choices(description, selection.choose_many_including_required(desired_inventory, adjust_odds), env)
            elif 'set' in instruction:
                if odds == 100 or (chance < adjust_odds):
                    eval_set(env, instruction['set'])
            elif instruction.keys() <= {'description', 'odds', 'set'}:
                if odds == 100 or (chance < adjust_odds):
                    out.start_paragraph()
                    out.println(description)


def eval_set(env, set_statement):
    # "set: foo" sets the foo variable to True
    # otherwise, assume it is a name and value dictionary
    if isinstance(set_statement, str):
        env[set_statement] = True
    else:
        env[set_statement['name']] = set_statement['value']


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate a scenario')
    parser.add_argument('--desired-items', nargs='+', metavar='ITEM',
                        help='items that you want the scenario to use if it is able to')
    parser.add_argument('--inventory-file', metavar='FILE',
                        help='path to the inventory file', default='inventory.yaml')
    parser.add_argument('--scenario-path', metavar='PATH',
                        help='the directory to read scenario files from', default='scenarios')
    parser.add_argument('--seed',
                        help='set an rng seed so the program generates the same scenario every time')
    parser.add_argument('scenarios', nargs='*', default=['*'],
                        help='choose scenarios by name. Wildcards (*) are supported.')

    args = parser.parse_args()
    run(scenario_names=args.scenarios,
        desired_inventory=args.desired_items,
        inventory_file=args.inventory_file,
        scenario_path=args.scenario_path,
        seed=args.seed)
