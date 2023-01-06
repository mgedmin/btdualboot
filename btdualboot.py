import argparse
import configparser
import os
import pathlib
import subprocess
import time
from typing import NamedTuple, Optional

from Registry import Registry

__version__ = "0.2"


def get_xdg_config_dir() -> pathlib.Path:
    return pathlib.Path(
        os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config")))


def load_config(config_file: os.PathLike) -> configparser.ConfigParser:
    cp = configparser.ConfigParser()
    cp.read([
        get_xdg_config_dir() / "btdualboot.ini",
        config_file,
    ])
    return cp


HexStr = str                # a hex string with colon separators
CompactHexStr = str         # a hex string without separators
MacAddress = HexStr                 # MAC address with colon separators
CompactMacAddress = CompactHexStr   # MAC address without separators
LinkKey = CompactHexStr              # 32-character hex string w/o separators


def format_ascii_hex(value: CompactHexStr | None) -> HexStr | None:
    """Format a value encoded in HEX

        >>> format_ascii_hex("AABBCCDDEEFF")
        "AA:BB:CC:DD:EE:FF"

    """
    if not value:
        return value
    return ":".join(value[n:n+2] for n in range(0, len(value), 2))


def format_raw_hex(value: bytes) -> HexStr:
    r"""Format a bytes value as HEX

        >>> format_raw_hex(b"\xAA\xBB\xCC\xDDxEE\xFF")
        "AA:BB:CC:DD:EE:FF"

    """
    return ":".join(f"{byte:02X}" for byte in value)


class DeviceInfo(NamedTuple):
    mac: MacAddress
    name: Optional[str]
    link_key: Optional[LinkKey]


def read_link_key(filename: os.PathLike, mac: MacAddress) -> DeviceInfo:
    cp = configparser.ConfigParser()
    cp.read([filename])
    name = cp.get('General', 'Name', fallback=None)
    link_key = cp.get('LinkKey', 'Key', fallback=None)
    return DeviceInfo(mac=mac, name=name, link_key=link_key)


def mount_partition(device_name: str) -> bool:
    p = subprocess.run(["udisksctl", "mount", "-b", device_name])
    return p.returncode == 0


def unmount_partition(device_name: str) -> bool:
    p = subprocess.run(["udisksctl", "unmount", "-b", device_name])
    return p.returncode == 0


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Synchronize Bluetooth pairing keys between Linux and Windows"))
    parser.add_argument(
        "--version", action="version",
        version="%(prog)s version " + __version__)
    parser.add_argument(
        "-c", "--config-file", default="btdualboot.ini",
        help="use a different configuration file (default: %(default)s)")
    args = parser.parse_args()
    cp = load_config(args.config_file)

    registry_file = cp.get("btdualboot", "RegistryFile")
    registry_partition = cp.get("btdualboot", "RegistryPartition",
                                fallback=None)
    if not os.path.exists(registry_file) and registry_partition:
        mounted = mount_partition(registry_partition)
    else:
        mounted = False

    reg = Registry.Registry(registry_file)
    # NB: I think we want HKEY_CURRENT_CONFIG actually, but I don't know how to
    # determine which one that is!
    key = reg.open("ControlSet001\\Services\\BTHPort\\Parameters\\Keys")

    print("Windows registry information:")
    for subkey in key.subkeys():
        print(f"  Host controller {format_ascii_hex(subkey.name())}")
        for value in subkey.values():
            print(f"    paired with {format_ascii_hex(value.name())}")
            print(f"      link key {format_raw_hex(value.value())}")
    print("Linux information:")
    try:
        for dirname in pathlib.Path('/var/lib/bluetooth').iterdir():
            if ':' in dirname.name:
                print(f"  Host controller {dirname.name}")
                for subdir in dirname.iterdir():
                    if ':' in subdir.name:
                        device = read_link_key(subdir / "info", subdir.name)
                        print(f"    paired with {device.name} ({device.mac})")
                        key = format_ascii_hex(device.link_key)
                        print(f"      link key {key}")
    except PermissionError:
        print("  unavailable when not running as root")

    del reg

    if mounted:
        for n in range(3):
            if unmount_partition(cp.get("btdualboot", "RegistryPartition")):
                break
            time.sleep(1)
