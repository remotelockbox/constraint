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


def run2(seed=None, scenario_name=None):
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
    run2()


# XXXXXXXXXXXXXXXXXXX

# Generate scenarios for being locked in the cage
# There are two broad types of scenarios
# that might be generated. Longer periods of time
# with little or no bondage or heavily bound
# but for a shorter period of time.


# roll die to choose which clothing to wear
clothing = {
    1: 'no clothing at all.\nRemove the cushion and put a pee pad down just in case.',
    2: 'just diapers',
    4: 'locked plastic pants',
    5: 'a locked sleeper',
    6: 'sissy clothes',
}

# roll die for what goes on the head
head = {
    1: None,
    2: 'collar',
    5: 'muzzle',
}

# accessories available under any circumstances
# the number is the minimum roll required for each accessory
accessories = {
    'butt plug': 5,
    'plushie': 4,
}

# accessories only appropriate while heavily bound
bound_accessories = {
    'ear plugs': 5,
    'blindfold': 6,
    'pup hood': 5,
    'timeout hood (takes the place of other headpieces)': 6,
}

# accessories appropriate only while not heavily bound
restricted_accessories = {
    'bottle': 4,
    'blankie': 5,
    'pacifier': 5,
}

# smaller chance of being heavily bound
bondage = {
    'bound with your arms and legs tied to sides of the cage': 6,
    'bound with your arms behind your back cuffed to the cage': 6,
    'confined in a loose straitjacket': 6,
}

# if not bound, maybe have various light bondage
restrictions = {
    'mitts on hands': 3,
    'leashed to end of cage': 4,
    'legs shackled to one end': 4,
}

# time span in cage
normal_timespan = {
    1: '20 minutes',
    2: '25 minutes',
    3: '30 minutes',
    4: '45 minutes',
    5: '1 hour',
}

# shorter times when heavily bound
bound_timespan = {
    1: '10 minutes. You must roll again after your punishment is complete.',
    2: '15 minutes',
    4: '20 minutes',
    5: '25 minutes',
    6: '30 minutes',
}


def choose(choices):
    result = roll()
    try:
        return choices[result]
    except KeyError:
        # if there is no choice for this number, try the next number down
        while True:
            result -= 1

            if result == 0:
                result = 6

            try:
                choice = choices[result]
                break
            except KeyError:
                pass

        return choice


def printIfNotNone(prefix, choice):
    if choice is not None:
        print(prefix + ' ' + choice)


def chooseMany(heading, choices):
    chosen = []
    for choice, minimumRoll in choices.items():
        if roll() >= minimumRoll:
            chosen.append(choice)

    if len(chosen) > 0:
        print()
        print(heading)
    for choice in chosen:
        print('  ' + choice)


def choosePunishment():
    for method, minimumRoll in bondage.items():
        if roll() >= minimumRoll:
            return method
    return False


# Run with an optional random seed.
# If you need to control punishment, set the punished argument.
# Otherwise it is random.
def run(seed = None, punished=None):
    if seed is not None:
        random.seed(seed)

    print("Instructions:\n")

    printIfNotNone('Put on', choose(clothing))
    head_choice = choose(head)
    printIfNotNone('Lock on a', head_choice)

    chooseMany('Accessories:', accessories)

    bound = False
    if punished is None:
        bound = choosePunishment()
    if punished is True:
        bound = False
        while not bound:
            bound = choosePunishment()

    # either be bound or just restricted
    if bound is not False:
        print()
        print("You will be punished!")
        printIfNotNone('You will be', bound)
        chooseMany('Additional Accessories:', bound_accessories)
        print("\nYou will be locked in this position for " + choose(bound_timespan))
    else:
        chooseMany('Restrictions:', restrictions)
        if head_choice != 'muzzle':
            chooseMany('Additional Accessories:', restricted_accessories)
        print("\nYou will be locked in the cage for " + choose(normal_timespan))

    print()

#run(7) # cubby pup mode
#run(10) # nap time
#run(5) # run(13) # very punishing!
#run(14) # loong pup nap
