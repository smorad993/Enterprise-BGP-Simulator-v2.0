"""
Vendor Driver Strategy Registry for Python SNMP Simulator
Matches sysObjectIDs and formats MIB data for multi-vendor network devices.
"""

class VendorDriver:
    def __init__(self, name, enterprise_oid, default_model):
        self.name = name
        self.enterprise_oid = enterprise_oid
        self.default_model = default_model

    def parse(self, ip, fqdn, sys_oid):
        return {
            "make": self.name,
            "model": self.default_model,
            "ip": ip,
            "fqdn": fqdn,
            "deviceType": 1 if self.name != "SONiC" else 2,
            "osVersion": f"{self.name} OS v15.4(3)",
            "chassisSerial": f"SN-{self.name[:3].upper()}-994821",
            "interfacesCount": 48 if "Switch" in self.default_model or "Spine" in self.default_model else 12,
        }

DRIVERS = [
    VendorDriver("Cisco", ".1.3.6.1.4.1.9.", "ASR-9904 Core Router"),
    VendorDriver("Arista", ".1.3.6.1.4.1.30065.", "7050SX3 Spine Switch"),
    VendorDriver("Ciena", ".1.3.6.1.4.1.1271.", "Waveserver Ai DCI"),
    VendorDriver("DriveNets", ".1.3.6.1.4.1.52300.", "NCP-400G-DN"),
    VendorDriver("Nokia", ".1.3.6.1.4.1.6527.", "7750 SR-12 Service Router"),
    VendorDriver("SONiC", ".1.3.6.1.4.1.27047.", "SONiC OpenSwitch 400G"),
    VendorDriver("Dell", ".1.3.6.1.4.1.674.", "PowerSwitch S5248F"),
]

def resolve_vendor(sys_oid):
    for driver in DRIVERS:
        if sys_oid.startswith(driver.enterprise_oid):
            return driver
    return VendorDriver("Generic", ".1.3.6.1.2.1.1.2.", "Generic MIB-II Router")
