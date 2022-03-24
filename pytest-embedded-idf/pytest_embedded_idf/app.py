import json
import logging
import os
import subprocess
import sys
from typing import Any, Dict, List, NamedTuple, Optional, Tuple

from pytest_embedded.app import App


class FlashFile(NamedTuple):
    offset: int
    file_path: str
    encrypted: bool = False


class IdfApp(App):
    """
    Idf App class

    Attributes:
        app_path (str): App path
        binary_path (str): binary file path
        elf_file (str): elf file path
        parttool_path (str): partition tool path
        sdkconfig (dict[str, str]): dict contains all k-v pairs from the sdkconfig file
        flash_files (list[Tuple[int, str, str]]): list of (offset, file path, encrypted) of files need to be flashed in
        flash_settings (dict[str, Any]): dict of flash settings
        partition_table (dict[str, Any]): dict generated by partition tool
    """

    FLASH_ARGS_FILENAME = 'flasher_args.json'

    def __init__(
        self,
        app_path: Optional[str] = None,
        build_dir: Optional[str] = None,
        part_tool: Optional[str] = None,
        **kwargs,
    ):
        """
        Args:
            app_path: App path
            build_dir: Build directory
            part_tool: Partition tool path
        """
        super().__init__(app_path, build_dir, **kwargs)
        if not self.binary_path:
            logging.debug('Binary path not specified, skipping parsing app...')
            return

        # Required if binary path exists
        self.elf_file = self._get_elf_file()
        self.bin_file = self._get_bin_file()

        self.flash_args, self.flash_files, self.flash_settings = self._parse_flash_args()

        # Optional info
        self._sdkconfig = None
        self._target = None

        # the partition table is used for nvs
        self._parttool = part_tool
        self._partition_table = None

    @property
    def parttool_path(self) -> str:
        parttool_filepath = self._parttool or os.path.join(
            os.getenv('IDF_PATH', ''),
            'components',
            'partition_table',
            'gen_esp32part.py',
        )
        if os.path.isfile(parttool_filepath):
            return os.path.realpath(parttool_filepath)
        raise ValueError('Partition Tool not found. (Default: $IDF_PATH/components/partition_table/gen_esp32part.py)')

    @property
    def sdkconfig(self) -> Dict[str, Any]:
        if self._sdkconfig is not None:
            return self._sdkconfig

        sdkconfig_json_path = os.path.join(self.binary_path, 'config', 'sdkconfig.json')
        if not os.path.isfile(sdkconfig_json_path):
            logging.warning(f'{sdkconfig_json_path} doesn\'t exist. Skipping...')
            self._sdkconfig = {}
        else:
            self._sdkconfig = json.load(open(sdkconfig_json_path))
        return self._sdkconfig

    @property
    def target(self) -> str:
        if self.sdkconfig:
            return self.sdkconfig.get('IDF_TARGET', 'esp32')
        else:
            return self.flash_args.get('extra_esptool_args', {}).get('chip', 'esp32')

    @property
    def partition_table(self) -> Dict[str, Any]:
        if self._partition_table is not None:
            return self._partition_table

        partition_file = os.path.join(
            self.binary_path,
            self.flash_args.get('partition_table', self.flash_args.get('partition-table', {})).get('file', ''),
        )
        process = subprocess.Popen(
            [sys.executable, self.parttool_path, partition_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        raw_data = stdout.decode() if isinstance(stdout, bytes) else stdout

        partition_table = {}
        for line in raw_data.splitlines():
            if line[0] != '#':
                try:
                    _name, _type, _subtype, _offset, _size, _flags = line.split(',')
                    if _size[-1] == 'K':
                        _size = int(_size[:-1]) * 1024
                    elif _size[-1] == 'M':
                        _size = int(_size[:-1]) * 1024 * 1024
                    else:
                        _size = int(_size)
                    _offset = int(_offset, 0)
                except ValueError:
                    continue
                partition_table[_name] = {
                    'type': _type,
                    'subtype': _subtype,
                    'offset': _offset,
                    'size': _size,
                    'flags': _flags,
                }
        self._partition_table = partition_table
        return self._partition_table

    def _get_elf_file(self) -> str:
        for fn in os.listdir(self.binary_path):
            if os.path.splitext(fn)[-1] == '.elf':
                return os.path.realpath(os.path.join(self.binary_path, fn))
        raise ValueError('Elf file not found')

    def _get_bin_file(self) -> str:
        for fn in os.listdir(self.binary_path):
            if os.path.splitext(fn)[-1] == '.bin':
                return os.path.realpath(os.path.join(self.binary_path, fn))
        raise ValueError('Bin file not found')

    def _parse_flash_args(
        self,
    ) -> Tuple[Dict[str, Any], List[FlashFile], Dict[str, str]]:
        flash_args_filepath = None
        for fn in os.listdir(self.binary_path):
            if fn == self.FLASH_ARGS_FILENAME:
                flash_args_filepath = os.path.realpath(os.path.join(self.binary_path, fn))
                break

        if not flash_args_filepath:
            raise ValueError(f'{self.FLASH_ARGS_FILENAME} not found')

        with open(flash_args_filepath) as fr:
            flash_args = json.load(fr)

        def _is_encrypted(_flash_args: Dict[str, Any], _offset: int, _file_path: str):
            for entry in _flash_args.values():
                try:
                    if (entry['offset'], entry['file']) == (_offset, _file_path):
                        return entry['encrypted'] == 'true'
                except (TypeError, KeyError):
                    continue

            return False

        flash_files = []
        for (offset, file_path) in flash_args['flash_files'].items():
            flash_files.append(
                FlashFile(
                    int(offset, 0),
                    os.path.join(self.binary_path, file_path),
                    _is_encrypted(flash_args, offset, file_path),
                )
            )

        flash_files.sort()
        flash_settings = flash_args['flash_settings']
        flash_settings['encrypt'] = any([file.encrypted for file in flash_files])

        return flash_args, flash_files, flash_settings

    def get_sha256(self, path_to_file):
        """
        get sha256 of app

        :param: path: path to file
        :return: sha256 appended to app
        """
        from esptool import LoadFirmwareImage, hexify

        image = LoadFirmwareImage(self.target, path_to_file)
        if image.append_digest:
            return hexify(image.stored_digest).lower()
        return None
