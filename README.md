# Constraint

A kinky scene generator for use by individuals or with partners.
It's like a choose-your-own-adventure book but you write the story and
the computer chooses for you.

This program is driven by information about what items you have available
to you and what kinds of scenes you want to carry out.

Your items are managed in `inventory.yaml` where you can add or remove items,
change the odds of them appearing in a scene, or tag them with categories that
affect what situations they'll be chosen for.

The `scenarios` directory is where individual scenarios are stored.
You can craft your own scenarios using the included ones as inspiration.

## Running the program

### Windows

1. Install [Python 3.9](https://www.python.org/downloads/windows/)
2. double-click `build.ps1` to build the project
3. double-click `run.ps1` to run the program or execute `run.ps1`
   in the Command Prompt


### Mac and Linux

1. Install Python 3.9 using homebrew (`brew install python@3.9`)
    or your linux package manager.
2. Run `./build.sh`
3. Run the program with `run.sh`


## Development

If you are editing the source code, you can use the same instructions as above
to set up a virtualenv with all the project's dependencies.

You then have the choice of using the run scripts to activate the virtualenv
and run the program or you can activate it yourself with `venv/bin/activate`
and run `python3.9 -m constraint.cli` directly.

If you use a smart editor like PyCharm or Visual Studio Code,
you can configure your editor to auto-complete YAML and highlight errors
by linking the included json schema with the YAML files.
Instructions for doing this varies by editor.
