import os.path
import random
import shutil
import sys
import textwrap
from collections.abc import Iterator, Iterable
from glob import glob
from typing import Optional

import jsonref
import jsonschema
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
            print('')
        self._para_written = False

    def print_paragraph(self, msg):
        self.start_paragraph()
        if msg:
            self.println(msg)

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


def roll(sides: int) -> int:
    return random.randint(1, sides)


# Randomly choose one item from a list weighed by their odds
def choose_item(choices: Iterable[dict]) -> Optional[dict]:
    if len(choices) <= 1:
        return next(iter(choices), None)

    total_weight = sum([x.get('odds', 1) for x in choices])

    result = roll(total_weight)

    acc = 0
    for choice in choices:
        acc += choice.get('odds', 1)
        if acc is not None and acc >= result:
            return choice

    raise ValueError(f"could not find choice with total odds {total_weight}, roll {result}")


# Choose one weighted item or None depending on the odds (0-1.0)
def maybe_choose_item(choices: Iterable[dict], odds: float) -> Optional[dict]:
    if random.random() < odds:
        return choose_item(choices)
    return None


# Return all choices that passed a 0-100 roll under its odds
def choose_many_items(choices: Iterable[dict], odds_adjustment=1.0) -> list[dict]:
    chosen = []
    for choice in choices:
        if roll(100) <= choice['odds'] * odds_adjustment:
            chosen.append(choice)
    return chosen


def describe_choice(prefix: Optional[str], choice: dict):
    if prefix:
        out.print_paragraph(prefix + ' ' + choice['text'])
    else:
        out.print_paragraph(choice['text'])


def describe_many(heading: Optional[str], selection: list[dict]):
    if heading and len(selection) > 0:
        out.print_paragraph(heading)

    for entry in selection:
        out.println('  - ' + entry['text'])


def describe_item(prefix: str, item: Optional[dict]) -> bool:
    if item is not None and ('name' not in item or item['name'] != 'none'):
        out.print_paragraph(prefix + ' ' + item['description'])
        return True
    return False


def describe_items(heading: str, selection: list[str]) -> bool:
    if len(selection) > 0:
        out.print_paragraph(heading)
    else:
        return False

    for choice in selection:
        out.println('  - ' + choice)
    return True


class Inventory:
    """ Represents an inventory file and provides
        methods for selecting items from the inventory
    """

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
        return maybe_choose_item(self, odds)

    def choose_many_items(self, odds=1.0) -> list[dict]:
        return choose_many_items(self, odds)


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
            out.println(f"error reading {f.name}: {error.message}")
            if len(error.path) >= 1:
                out.println(
                    f'The error is located in item #{error.path[0]} of the inventory')
            out.start_paragraph()
            raise ValueError("error while parsing file")
        return contents


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
            out.println(f"error reading {f.name}: {error.message}")
            if len(error.path) >= 3:
                out.println(
                    f'The error is located in the #{error.path[2]} '
                    f'instruction of the "{contents[error.path[0]]["name"]}" scenario')
            out.start_paragraph()
            raise ValueError("error while parsing file")

        return contents


def interpolate(obj, env):
    """ interpolate strings inside instructions recursively """
    if isinstance(obj, str):
        template = Template(obj)
        return template.render(env)
    elif isinstance(obj, dict):
        result = {}
        for k, v in obj.items():
            # don't interpolate instructions within instructions. Those need to be evaluated individually.
            if k in {'do', 'choose_instruction', 'choose_some_instruction'}:
                result[k] = v
            else:
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

    try:
        inventory = Inventory(load_inventory(inventory_file))
    except ValueError:
        print("cannot read inventory. aborting", file=sys.stderr)
        return

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
    try:
        for file in files:
            scenarios += load_scenario(file)
    except ValueError:
        print("cannot read a scenario file. aborting", file=sys.stderr)
        return

    if seed is not None:
        random.seed(seed)

    scenario = choose_item(scenarios)

    if not scenario:
        print("no matching scenario. aborting")
        return

    eval_scenario(desired_inventory, inventory, scenario)


def eval_scenario(desired_inventory, inventory, scenario):
    out.println("Instructions:")

    env = {}

    for instruction in scenario['instructions']:
        eval_instruction(desired_inventory, inventory, instruction, env)


def eval_instruction(desired_inventory, inventory, instruction, env):
    # apply template substitutions
    instruction = interpolate(instruction, env)

    description = instruction.get('text')

    odds = instruction.get('odds', 100)

    # if odds is a string, treat it as a variable
    if isinstance(odds, str):
        odds = env[odds]
    if odds is None:
        odds = 100

    # An instruction can alter the odds of a selection from choose_many_items.
    # Less than 100 will reduce the number of chosen items while
    # greater than 100 will increase the number of items chosen.
    adjust_odds = odds / 100.0

    # Chance of displaying a description or setting a variable (in the absence of a 'choose' statement)
    chance = random.random()

    if 'choose_item' in instruction:
        eligible = inventory.select_by_instruction(instruction['choose_item'])
        selection = eligible.choose_item_or_required(desired_inventory, adjust_odds)
        if describe_item(description, selection):
            eval_set(env, instruction)
    elif 'choose_many_items' in instruction:
        eligible = inventory.select_by_instruction(instruction['choose_many_items'])
        selection = eligible.choose_many_items_including_required(desired_inventory, adjust_odds)
        if describe_items(description, selection):
            eval_set(env, instruction)
    elif 'choose_text' in instruction:
        selection = maybe_choose_item(instruction['choose_text'], adjust_odds)
        if selection:
            describe_choice(description, selection)
            eval_set(env, instruction)
            eval_set(env, selection)
    elif 'choose_some_of' in instruction:
        selection = choose_many_items(instruction['choose_some_of'], adjust_odds)
        if selection:
            describe_many(description, selection)
            eval_set(env, instruction)
            eval_set(env, selection)
    elif 'choose_instruction' in instruction:
        instruction_list = instruction['choose_instruction']
        chosen = maybe_choose_item(instruction_list, adjust_odds)
        if chosen:
            out.print_paragraph(description)
            eval_set(env, instruction)
            eval_instruction(desired_inventory, inventory, chosen, env)
    elif 'choose_some_instructions' in instruction:
        if odds == 100 or (chance < adjust_odds):
            instruction_list = instruction['choose_some_instructions']
            chosen = choose_many_items(instruction_list, adjust_odds)
            if chosen:
                out.print_paragraph(description)
                eval_set(env, instruction)
                eval_set(env, chosen)
                for inner in chosen:
                    eval_instruction(desired_inventory, inventory, inner, env)
    elif 'do' in instruction:
        if odds == 100 or (chance < adjust_odds):
            out.print_paragraph(description)
            eval_set(env, instruction)
            for inner in instruction['do']:
                eval_instruction(desired_inventory, inventory, inner, env)
    elif 'text' in instruction:
        if odds == 100 or (chance < adjust_odds):
            out.print_paragraph(description)
            eval_set(env, instruction)


def eval_set(env, instruction):
    if 'set' not in instruction:
        return

    set_statement = instruction['set']
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
