import os
from pathlib import Path
from typing import List

from auto_neutron.constants import JPATH


def get_journals(n: int) -> List[Path]:
    """Get last n journals."""
    return sorted(JPATH.glob("*.log"), key=os.path.getctime, reverse=True)[:n]
