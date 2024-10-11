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


def display_instructions(
    host_controller: MacAddress,
    mac: MacAddress,
    link_key: HexStr,
) -> None:
    print("About to run chntpw.")
    print("You will want to execute the following commands:")
    hc = host_controller.replace(':', '').lower()
    print(f"  > cd ControlSet001\\Services\\BTHPORT\\Parameters\\Keys\\{hc}")
    key = mac.replace(':', '').lower()
    print(f"  > ed {key}")
    print("  new length: (press Enter to keep same)")
    print(f"  . : 0 {link_key.replace(':', ' ')}")
    print("  . s")
    print("  > q")


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
    parser.add_argument(
        "--edit-registry", action="store_true",
        help="run chntpw to edit the Windows registry")
    args = parser.parse_args()
    cp = load_config(args.config_file)

    registry_file = cp.get("btdualboot", "RegistryFile").replace(
        '$USER', os.getenv('USER')
    )
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

    hc = "xxxxxxxxxxxx"  # a placeholder for instruction display
    windows_keys = {}
    mismatches = {}
    print("Windows registry information:")
    for subkey in key.subkeys():
        hc = subkey.name().replace(':', '')
        print(f"  Host controller {format_ascii_hex(subkey.name())}")
        for value in subkey.values():
            mac = format_ascii_hex(value.name().upper())
            link_key = format_raw_hex(value.value())
            print(f"    paired with {mac}")
            print(f"      link key {link_key}")
            windows_keys[mac] = link_key
    print("Linux information:")
    try:
        for dirname in pathlib.Path('/var/lib/bluetooth').iterdir():
            if ':' in dirname.name:
                print(f"  Host controller {dirname.name}")
                hc = dirname.name.replace(':', '')
                for subdir in dirname.iterdir():
                    if ':' in subdir.name:
                        device = read_link_key(subdir / "info", subdir.name)
                        print(f"    paired with {device.name} ({device.mac})")
                        key = format_ascii_hex(device.link_key)
                        print(f"      link key {key}")
                        if device.mac in windows_keys:
                            if key != windows_keys[device.mac]:
                                mismatches[device.mac] = key
    except PermissionError:
        print("  unavailable when not running as root")

    del reg

    if args.edit_registry:
        dev = "yyyyyyyyyyyy"  # placeholder for instruction display
        key = "XX" * 16
        if mismatches:
            dev, key = list(mismatches.items())[0]
        # TODO: check if rlwrap is installed
        # TODO: check if chntpw is installed, print error message if not
        display_instructions(hc, dev, key)
        subprocess.run(["rlwrap", "chntpw", "-e", registry_file])

    if mounted:
        for n in range(3):
            if unmount_partition(cp.get("btdualboot", "RegistryPartition")):
                break
            time.sleep(1)
