"""Remove non dev packages, and move dev packages to default."""

import json

with open("Pipfile.lock") as file:
    pipfile = json.load(file)

pipfile["default"] = pipfile["develop"]
pipfile["develop"] = {}

with open("Pipfile.lock", "w") as file:
    json.dump(pipfile, file)
