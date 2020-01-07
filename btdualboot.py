import argparse
import configparser
import os
import pathlib
import subprocess
import time

from Registry import Registry

__version__ = "0.1"


def get_xdg_config_dir():
    return pathlib.Path(
        os.getenv('XDG_CONFIG_HOME', os.path.expanduser("~/.config")))


def load_config(config_file):
    cp = configparser.ConfigParser()
    cp.read([
        get_xdg_config_dir() / "btdualboot.ini",
        config_file,
    ])
    return cp


def format_ascii_hex(value):
    """Format a value encoded in HEX

        >>> format_ascii_hex("AABBCCDDEEFF")
        "AA:BB:CC:DD:EE:FF"

    """
    if not value:
        return value
    return ":".join(value[n:n+2] for n in range(0, len(value), 2))


def format_raw_hex(value):
    r"""Format a bytes value as HEX

        >>> format_raw_hex(b"\xAA\xBB\xCC\xDDxEE\xFF")
        "AA:BB:CC:DD:EE:FF"

    """
    return ":".join(f"{byte:02X}" for byte in value)


def read_link_key(filename):
    cp = configparser.ConfigParser()
    cp.read([filename])
    return cp.get('LinkKey', 'Key', fallback=None)


def mount_partition(device_name):
    p = subprocess.run(["udisksctl", "mount", "-b", device_name])
    return p.returncode == 0


def unmount_partition(device_name):
    p = subprocess.run(["udisksctl", "unmount", "-b", device_name])
    return p.returncode == 0


def main():
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
    for dirname in pathlib.Path('/var/lib/bluetooth').iterdir():
        if ':' in dirname.name:
            print(f"  Host controller {dirname.name}")
            try:
                for subdir in dirname.iterdir():
                    if ':' in subdir.name:
                        print(f"    paired with {subdir.name}")
                        key = read_link_key(subdir / "info")
                        print(f"      link key {format_ascii_hex(key)}")
            except PermissionError:
                print("    unavailable when not running as root")

    del reg

    if mounted:
        for n in range(3):
            if unmount_partition(cp.get("btdualboot", "RegistryPartition")):
                break
            time.sleep(1)
