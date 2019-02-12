"""
sample script to disable optionrom for lom nics and set boot mode uefi pxe and hdd
"""

from imcsdk import imchandle
from imcsdk.apis.server.boot import boot_order_precision_set
from imcsdk.mometa.bios.BiosVfLOMPortOptionROM import BiosVfLOMPortOptionROM

# fill ucs details here
UCS_IP = ""
UCS_USER = ""
UCS_PASSWORD = ""
OPTROM_PORTS = {"dn": [{"lom": "sys/rack-unit-1/bios/bios-settings"},
                       {"pcie": "sys/rack-unit-1/bios/bios-defaults"}],
                "ports":
                    {"lom": ["vp_lom_port0_state", "vp_lom_port1_state", "vp_lom_ports_all_state"]}
                }
BOOT_DEV_CONFIG = [{"order": "1", "device-type": "pxe", "name": "ixpe-http-tftp"},
                   {"order": "2", "device-type": "hdd", "name": "local_hdd"}]

# connect to ucs cimc and get handle to pass cimc commands
try:
    handle = imchandle.ImcHandle(UCS_IP, UCS_USER, UCS_PASSWORD)
    handle.login()
except Exception as error:
    print("unable to login to UCS CIMC, check cimc connectivity and/or credentials")
    print(error)
    exit(0)

# disable optrom for slots where naples is not connected
try:
    for dn in OPTROM_PORTS["dn"]:
        state = {}
        if "lom" in dn.keys():
            for port in OPTROM_PORTS["ports"]["lom"]:
                state[port] = "Disabled"
            optrom_mo = BiosVfLOMPortOptionROM(parent_mo_or_dn=dn["lom"], **state)
            handle.add_mo(optrom_mo, True)
except Exception as error:
    print("optionrom state change might have failed")
    print(error)

# change boot mode to uefi, reboot on update
try:
    print("setting boot mode to uefi pxe followed by HDD")
    boot_order_precision_set(handle=handle, reboot_on_update="no", reapply="yes",
                             configured_boot_mode="Uefi", boot_devices=BOOT_DEV_CONFIG)
except Exception as error:
    print("unable to change boot mode")
    print(error)
finally:
    handle.logout()
