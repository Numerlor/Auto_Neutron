# Auto_Neutron

Auto_Neutron is a utility tool to help you plot routes created using Spansh's route plotters or for CSV files that use Spansh's syntax.

![](https://i.imgur.com/o10p5mg.png)

## What it does

Auto_Neutron helps you traverse routes generated from outside the game by either copying the next route system into your clipboard, or by executing a custom AHK script that can use the system name.

Example of AHK script in action, with no user keyboard input apart from the hotkey.

![](https://i.imgur.com/ciZ5iQW.jpg)

![](https://i.imgur.com/kTagchR.png)

## Features

* Built in plotters using Spansh's api
* Saving of routes
* Low fuel alert when customisable threshold is reached

## Installation

To install, download the [latest](https://github.com/Numerlor/Auto_Neutron/releases/latest) release of Auto_Neutron, or [run it directly](#running-directly).
You can choose either the self-contained executable file, or the zip archive which contains the application in a directory which is a bit faster to launch.

On the initial launch, Windows will warn you about this being an untrusted application because it doesn't contain a known signed certificate, to ignore this warning, press on `More info` and then click `Run anyway`.

## Usage

On launch, the app will display a popup that allows you to create a new route, either from a CSV file, Spansh, or a previously saved route.\
After creating a route, the popup will close and the main window will be filled with route entries, and the plotter will start.\
When you reach a system in the route, Auto_Neutron will either copy the next system into the clipboard, or it'll feed it to AHK.

In case you want to skip to a system, you can double-click its entry.

Further interactions like editing the system entries, starting a new route, changing [settings](#settings), or saving the current route and its position are available in the right-click context menu of the main window.

In case you want to plot with Spansh, but the source or target systems are not found, you can use the [nearest window](#nearest-window) to find the nearest known system around given coordinates.

## Settings
### Appearance
* The font dropdown, size chooser and bold checkmark let you control the font used in the main window.
* The dark mode checkmark modifies the app's theme

### Behaviour
* The "Save route on window close" checkmark changes where the current route and its position are saved to be reused later when the window is closed
* The copy mode checkmark changes the mode the application runs in - copying to clipboard, or running an AHK script. Before it can be unchecked to use AHK, the path to AHK has to be configured through the AHK Path button to the right
* When the auto scroll checkmark is checked, the app will automatically auto scroll the main window down to the next system if the system that was jumped to is at the top, or the route just started.

### Alerts
* If the taskbar fuel alert checkbox is checked, the app will flash on the taskbar for 5 seconds when low fuel is reached.
* If the sound fuel alert checkbox is checked, the app will play a beep, or the alert file when low fuel is reached.
* The percentage value to be chosen represents the % of the current ship's FSD's maximum usage to be left in the tank before triggering an alert, for example if your FSD can use 4t of fuel at once and the percentage is set to 150%, the alert will trigger with 6t of fuel left in the tank.

### AHK script

![](https://i.imgur.com/RYVthYw.png)

This section defines the AHK script to be used with the AHK mode of the app, standard AHK syntax is used.\
The top text box defines the hot key, the bottom one defines the script to run with that hotkey.\
To access the system to plot in the AHK script, you can use the `system` variable.


## Nearest window
This window provides an interface to Spansh's [nearest](https://www.spansh.co.uk/nearest) API.

![](https://i.imgur.com/X9EQbUm.png)

The `from location` button will copy your current location's coordinates into the input boxes.\
The `from target` button will copy your current target's coordinates into the input boxes. Because the game doesn't expose the target's location, this is an approximation and may not be entirely accurate.

After searching for a system you can copy the result system's name into the source or destination text inputs with their respective buttons.

## Running directly
To run the application directly with python, clone the repository, and then install the project's dependencies and run through poetry.
```shell
$ git clone git@github.com:Numerlor/Auto_Neutron.git  # Clone the project
$ cd Auto_Neutron  # Switch to the cloned folder
$ poetry install --no-dev  # Install the project's dependencies
$ poetry run start  # Start the application
```

Utility for creating custom CSV files usable by this app:
https://github.com/Numerlor/Neutron-CSV-Builder
