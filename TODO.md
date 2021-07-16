# TODO
Pending work and feature proposals are documented in this file.
An issue tracker may supersede this file in the future.


## Bugs

- none

## Features

- documentation for file formats
- trace logging with logger module
- support sub-sequences of instructions using an inner list governed by the outer odds.
- instruction choices (rendered differently from choose_one_of)
- support referencing scenarios and scene fragments
- allow scenarios to run other scenario
    - references to scenario fragments
    - support tagging, odds, and embedding of scenarios
- be able to set variables and substitute them in to descriptions
  and odds values. This would allow more dynamic scenes where selecting
  one choice may make another choice more or less likely. Choices could
  also influence the language used in later descriptions.
  - also, branching based on variable comparisons.
  - combined with interactive choices, this makes
    choose-your-own-adventure scenes possible.

## Proposed Ideas

- offer interactive choices to the user
- A UI for selecting scenarios and managing inventory
- loading scenarios by URL for easy sharing
