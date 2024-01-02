"""Make pytest-embedded plugin work with ESP-IDF."""

import importlib

from pytest_embedded.utils import lazy_load

from .app import IdfApp
from .linux import LinuxDut, LinuxSerial
from .unity_tester import CaseTester, UnittestMenuCase

__getattr__ = lazy_load(
    importlib.import_module(__name__),
    {
        'IdfApp': IdfApp,
        'LinuxDut': LinuxDut,
        'LinuxSerial': LinuxSerial,
        'CaseTester': CaseTester,
    },
    {
        'IdfSerial': '.serial',
        'IdfDut': '.dut',
    },
)


__all__ = [
    'IdfApp',
    'IdfSerial',
    'IdfDut',
    'CaseTester',
    'LinuxSerial',
    'LinuxDut',
    'UnittestMenuCase',
]

__version__ = '1.6.0'
