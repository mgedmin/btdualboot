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

- if you run the script as root, it'll print all the paired devices and their
  link keys from the Windows registry and ``/var/lib/bluetooth`` (if you run it as
  a regular user, it'll only show the Windows registry)

- you need to tell the script where the registry lives by creating a
  ``btdualboot.ini``

- if you manually edit link keys in /``var/lib/bluetooth`` then you need to
  ``service bluetooth restart`` afterwards for bluetoothd to notice changes
