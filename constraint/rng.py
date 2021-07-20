import random

from typing import Optional, Collection


def roll(sides: int) -> int:
    return random.randint(1, sides)


# Randomly choose one item from a list weighed by their odds
def choose_item(choices: Collection[dict]) -> Optional[dict]:
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
def maybe_choose_item(choices: Collection[dict], odds: float) -> Optional[dict]:
    if random.random() < odds:
        return choose_item(choices)
    return None


# Return all choices that passed a 0-100 roll under its odds
def choose_many_items(choices: Collection[dict], odds_adjustment=1.0) -> list[dict]:
    chosen = []
    for choice in choices:
        if roll(100) <= choice['odds'] * odds_adjustment:
            chosen.append(choice)
    return chosen
