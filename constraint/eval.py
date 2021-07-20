import random
from typing import Optional

from . import rng
from .cli import out
from jinja2 import Template


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
        selection = rng.maybe_choose_item(instruction['choose_text'], adjust_odds)
        if selection:
            describe_choice(description, selection)
            eval_set(env, instruction)
            eval_set(env, selection)
    elif 'choose_some_of' in instruction:
        selection = rng.choose_many_items(instruction['choose_some_of'], adjust_odds)
        if selection:
            describe_many(description, selection)
            eval_set(env, instruction)
            eval_set(env, selection)
    elif 'choose_instruction' in instruction:
        instruction_list = instruction['choose_instruction']
        chosen = rng.maybe_choose_item(instruction_list, adjust_odds)
        if chosen:
            out.print_paragraph(description)
            eval_set(env, instruction)
            eval_instruction(desired_inventory, inventory, chosen, env)
    elif 'choose_some_instructions' in instruction:
        if odds == 100 or (chance < adjust_odds):
            instruction_list = instruction['choose_some_instructions']
            chosen = rng.choose_many_items(instruction_list, adjust_odds)
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
