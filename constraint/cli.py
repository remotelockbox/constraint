import os.path
import sys
from glob import glob

from . import rng
from .terminal import out
from .inventory import load_inventory
from .scenario import load_scenario
from .eval import *


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
        inventory = load_inventory(inventory_file)
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
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return

    if seed is not None:
        random.seed(seed)

    scenario = rng.choose_item(scenarios)

    if not scenario:
        print("no matching scenario. aborting")
        return

    eval_scenario(desired_inventory, inventory, scenario)


def entry():
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


if __name__ == '__main__':
    entry()
