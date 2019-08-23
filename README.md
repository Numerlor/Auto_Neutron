# Auto-Neutron
Auto Neutron is an utility tool for neutron routes created using Spansh's route plotter or for CSV files that use spansh's syntax

![](https://i.imgur.com/o10p5mg.png)


# Installation
```
$ cd Auto-Neutron
$ pip intall -r requirements.txt
$ python "Auto Neutron.py"
```
or download latest release

# Usage
After initial launch a popup window will show up if Auto Hot Key is not detected in ints default directory, if you wish to use it (install it) and select its executable.
Otherwise press cancel
### Copy mode
In copy mode, the script will automatically copy the next system in route to the clipboard when the current target is reached

### AHK Mode
With AHK the script will launch a new intance of a custom AHK script, that is editable in settings, and replace the "|SYSTEMNAME|" string in it with the next system in route.

If the AHK script is not working, make sure all of the keybinds are correct or increase sleep timeouts

## Features
* Built in neutron plotter using Spansh's api
* Saving of routes
* Skipping jumps using doubleclick
* Low fuel alert when customisable threshold is reached




![](https://i.imgur.com/kTagchR.png)

![](https://i.imgur.com/RYVthYw.png)

Example of AHK script in action
![](https://i.imgur.com/ciZ5iQW.jpg)
