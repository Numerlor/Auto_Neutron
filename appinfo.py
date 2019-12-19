from collections import namedtuple

from PyQt5.QtCore import QByteArray
from PyQt5.QtGui import QFont

VERSION = "1.456"
APP = "Auto Neutron"
ORG = "Numerlor"
APPID = f"{ORG}|{APP}|{VERSION}"

# script data
FSD = namedtuple('Frame_Shift_Drive', ('max_fuel_usage', 'optimal_mass',
                                       'size_const', 'rating_const'))
SHIP_STATS = {
    'FSD': {'int_hyperdrive_size2_class1': FSD(0.60, 48, 2.00, 11),
            'int_hyperdrive_size2_class2': FSD(0.60, 54, 2.00, 10),
            'int_hyperdrive_size2_class3': FSD(0.60, 60, 2.00, 8),
            'int_hyperdrive_size2_class4': FSD(0.80, 75, 2.00, 10),
            'int_hyperdrive_size2_class5': FSD(0.90, 90, 2.00, 12),
            'int_hyperdrive_size3_class1': FSD(1.20, 80, 2.15, 11),
            'int_hyperdrive_size3_class2': FSD(1.20, 90, 2.15, 10),
            'int_hyperdrive_size3_class3': FSD(1.20, 100, 2.15, 8),
            'int_hyperdrive_size3_class4': FSD(1.50, 125, 2.15, 10),
            'int_hyperdrive_size3_class5': FSD(1.80, 150, 2.15, 12),
            'int_hyperdrive_size4_class1': FSD(2.00, 280, 2.30, 11),
            'int_hyperdrive_size4_class2': FSD(2.00, 315, 2.30, 10),
            'int_hyperdrive_size4_class3': FSD(2.00, 350, 2.30, 8),
            'int_hyperdrive_size4_class4': FSD(2.50, 438, 2.30, 10),
            'int_hyperdrive_size4_class5': FSD(3.00, 525, 2.30, 12),
            'int_hyperdrive_size5_class1': FSD(3.30, 560, 2.45, 11),
            'int_hyperdrive_size5_class2': FSD(3.30, 630, 2.45, 10),
            'int_hyperdrive_size5_class3': FSD(3.30, 700, 2.45, 8),
            'int_hyperdrive_size5_class4': FSD(4.10, 875, 2.45, 10),
            'int_hyperdrive_size5_class5': FSD(5.00, 1050, 2.45, 12),
            'int_hyperdrive_size6_class1': FSD(5.30, 960, 2.60, 11),
            'int_hyperdrive_size6_class2': FSD(5.30, 1080, 2.60, 10),
            'int_hyperdrive_size6_class3': FSD(5.30, 1200, 2.60, 8),
            'int_hyperdrive_size6_class4': FSD(6.60, 1500, 2.60, 10),
            'int_hyperdrive_size6_class5': FSD(8.00, 1800, 2.60, 12),
            'int_hyperdrive_size7_class1': FSD(8.50, 1440, 2.75, 11),
            'int_hyperdrive_size7_class2': FSD(8.50, 1620, 2.75, 10),
            'int_hyperdrive_size7_class3': FSD(8.50, 1800, 2.75, 8),
            'int_hyperdrive_size7_class4': FSD(10.60, 2250, 2.75, 10),
            'int_hyperdrive_size7_class5': FSD(12.80, 2700, 2.75, 12),
            },

    'Booster':
        {
            'int_guardianfsdbooster_size1': 4.0,
            'int_guardianfsdbooster_size2': 6.0,
            'int_guardianfsdbooster_size3': 7.75,
            'int_guardianfsdbooster_size4': 9.25,
            'int_guardianfsdbooster_size5': 10.5,
        }
}

setting_params = namedtuple("SettingParams", ("type", "category"))
settings = {
    "save_on_quit": setting_params(bool, ""),
    "bind": setting_params(str, ""),
    "script": setting_params(str, ""),
    "last_route": setting_params(tuple, ""),
    "copy_mode": setting_params(bool, ""),

    "journal": setting_params(str, "paths"),
    "ahk": setting_params(str, "paths"),
    "csv": setting_params(str, "paths"),
    "alert": setting_params(str, "paths"),

    "geometry": setting_params(QByteArray, "window"),
    "dark": setting_params(bool, "window"),
    "font_size": setting_params(int, "window"),
    "autoscroll": setting_params(bool, "window"),

    "font": setting_params(QFont, "font"),
    "size": setting_params(int, "font"),
    "bold": setting_params(bool, "font"),

    "audio": setting_params(bool, "alerts"),
    "visual": setting_params(bool, "alerts"),
    "threshold": setting_params(int, "alerts"),
}
