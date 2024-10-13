Bluetooth & dual-boot
=====================

Problem: when you dual-boot two OSes on your laptop, each of them assigns its
own private keys for paired Bluetooth devices, but the Bluetooth device expects
the same key from the same paired laptop no matter what OS you've booted into!

Solution: synchronize the keys manually.

Linux stores Bluetooth keys in INI files under
``/var/lib/bluetooth/$host_controller_mac/$paired_device_mac/info``, with ::

  [LinkKey]
  Key=AABBCCDD...

Windows stores Bluetooth keys in the registry under
``HKLM\System\ControlSet001\Services\BTHPORT\Parameters\Keys\${hcmac}\${devmac}``

This script can automate some of the work.

Current status:

- you need to tell the script where the registry lives by editing
  ``btdualboot.ini``

- if you run the script as root, it'll print all the paired devices and their
  link keys from the Windows registry and ``/var/lib/bluetooth`` (if you run it as
  a regular user, it'll only show the Windows registry)

- if you manually edit link keys in ``/var/lib/bluetooth`` then you need to
  ``service bluetooth restart`` afterwards for bluetoothd to notice changes

- you can manually edit link keys in the Windows registry by using ``chntpw``,
  this is partially automated passing ``--edit-registry`` to the script.


Here's an example session::

    sudo apt install chntpw rlwrap
    udisksctl mount -b /dev/disk/by-label/Windows
    cd /media/$USER/Windows/Windows/System32/config/
    rlwrap chntpw -e SYSTEM
    > dir ControlSet001\Services\BTHPORT\Parameters\Keys
    > cd ControlSet001\Services\BTHPORT\Parameters\Keys\xxxxxxxxxxxx
    > dir
    > ed yyyyyyyyyyyy
    new length: same
    . : 0 ZZ ZZ ZZ ZZ ZZ ZZ ZZ ZZ ZZ ZZ ZZ ZZ ZZ ZZ ZZ ZZ
    . a 0
    . s
    > q


Alternatives
------------

- https://github.com/x2es/bt-dualboot is mentioned by the ArchLinux wiki
