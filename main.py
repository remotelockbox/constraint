import random

import yaml


def roll(sides=6):
    return random.randint(1, sides)


def choose_many(choices):
    chosen = []
    for choice in choices:
        if roll(100) >= choice['odds']:
            chosen.append(choice)
    return chosen


def print_choices(heading, chosen):
    if len(chosen) > 0:
        print()
        print(heading)
    for choice in chosen:
        print('  ' + choice['description'])


def describe_if_not_none(prefix, choice):
    if choice is not None and choice['name'] != 'none':
        print(prefix + ' ' + choice['description'])


def choose_weighted(choices):
    total_weight = sum([x['choice_weight'] for x in choices])

    result = roll(total_weight)

    acc = 0
    for choice in choices:
        acc += choice['choice_weight']
        if acc is not None and acc >= result:
            return choice

    print("could not find choice with total weight {}, roll {}".format(total_weight, result))


class Inventory:
    def __init__(self, data):
        self.data = data

    def select_class(self, classname):
        return [x for x in self.data if x['class'] == classname]

    def choose_class(self, classname):
        return choose_weighted(self.select_class(classname))


def load(path='inventory.yaml'):
    with open(path) as f:
        return Inventory(yaml.safe_load(f)['inventory'])


def run2(seed = None, punished=None):
    inventory = load()

    if seed is not None:
        random.seed(seed)

    print("Instructions:\n")

    describe_if_not_none('Put on', inventory.choose_class('clothing'))
    head_choice = inventory.choose_class('headwear')
    describe_if_not_none('Lock on a', head_choice)

    # if punished, choose punishment, choose additional bondage category gear,
    # and don't consider abdl accessories

    print_choices('Accessories:', choose_many(inventory.select_class('accessories')))


    # XXX
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
    'confined in a loose straightjacket': 6,
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
