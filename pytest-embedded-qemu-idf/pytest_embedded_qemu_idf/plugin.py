import logging
from types import ModuleType

import pytest

from .dut import IdfQemuDut
from .qemu import IdfQemu


def pytest_addoption(parser):
    group = parser.getgroup('embedded')
    group.addoption('--qemu-image-path', help='QEMU image path, REQUIRED')
    group.addoption(
        '--qemu-prog-path',
        help='QEMU program path. (Default: "qemu-system-xtensa")',
    )
    group.addoption(
        '--qemu-cli-args',
        help='QEMU cli default arguments. (Default: "-nographic -no-reboot -machine esp32")',
    )
    group.addoption(
        '--qemu-extra-args',
        help='QEMU cli extra arguments, will append to the argument list. (Default: None)',
    )
    group.addoption(
        '--qemu-log-path',
        help='QEMU log file path. (Default: "<temp folder>/<timestamp>/serial.log")',
    )
    group.addoption('--qemu-skip-autorun', help='Skip autorun qemu image. (default: False)')


@pytest.fixture
def qemu(app, options) -> IdfQemu:
    """
    Uses :attr:`options['Qemu']` as kwargs to create instance.

    :return: :class:`pytest_embedded_qemu_idf.qemu.IdfQemu` or derived class instance
    """
    qemu_options = options.get('Qemu', {})
    logging.info(qemu_options)
    qemu = IdfQemu(app=app, **qemu_options)
    try:
        yield qemu
    finally:
        qemu.close()


@pytest.fixture
def dut(app, qemu, options) -> IdfQemuDut:
    """
    Uses :attr:`options['Dut']` as kwargs to create instance.

    :return: :class:`pytest_embedded_qemu_idf.dut.IdfQemuDut` or derived class instance
    """
    dut_options = options.get('Dut', {})
    logging.info(dut_options)
    dut = IdfQemuDut(app=app, qemu=qemu, **dut_options)
    try:
        yield dut
    finally:
        dut.close()


@pytest.hookimpl
def pytest_plugin_registered(plugin, manager):
    if not isinstance(plugin, ModuleType) or plugin.__name__ != 'pytest_embedded.plugin':
        return

    plugin.KNOWN_OPTIONS['Qemu'].extend(
        [
            'qemu_image_path',
            'qemu_prog_path',
            'qemu_cli_args',
            'qemu_extra_args',
            'qemu_log_path',
            'qemu_skip_autorun',
        ]
    )