"""
Mock SNMP Engine Simulator for OID Walks & Protocol Handling
"""

import random
import time
from vendor_drivers import resolve_vendor

# Mock OID Mappings
SYS_OBJECT_IDS = {
    "cisco": ".1.3.6.1.4.1.9.1.2223",
    "arista": ".1.3.6.1.4.1.30065.1.20",
    "ciena": ".1.3.6.1.4.1.1271.2.5",
    "drivenets": ".1.3.6.1.4.1.52300.1.1",
    "nokia": ".1.3.6.1.4.1.6527.1.3",
    "sonic": ".1.3.6.1.4.1.27047.4.1",
}

class MockSNMPEngine:
    def __init__(self):
        self.active_workers = 0

    def discover_device(self, fqdn, ip, snmp_string="public", port=161):
        self.active_workers += 1
        start_time = time.time()

        # Simulate UDP network roundtrip latency (10-45ms)
        time.sleep(random.uniform(0.01, 0.045))

        # Select mock OID based on hostname hints or random fallback
        fqdn_lower = (fqdn or "").lower()
        if "cisco" in fqdn_lower or "ar" in fqdn_lower or "r1" in fqdn_lower:
            sys_oid = SYS_OBJECT_IDS["cisco"]
        elif "arista" in fqdn_lower or "sw" in fqdn_lower or "spine" in fqdn_lower:
            sys_oid = SYS_OBJECT_IDS["arista"]
        elif "ciena" in fqdn_lower or "dci" in fqdn_lower:
            sys_oid = SYS_OBJECT_IDS["ciena"]
        elif "drivenets" in fqdn_lower or "dn" in fqdn_lower:
            sys_oid = SYS_OBJECT_IDS["drivenets"]
        elif "nokia" in fqdn_lower:
            sys_oid = SYS_OBJECT_IDS["nokia"]
        elif "sonic" in fqdn_lower:
            sys_oid = SYS_OBJECT_IDS["sonic"]
        else:
            # Deterministic selection based on IP hash
            keys = list(SYS_OBJECT_IDS.values())
            sys_oid = keys[sum(ord(c) for c in ip) % len(keys)]

        vendor_driver = resolve_vendor(sys_oid)
        result = vendor_driver.parse(ip, fqdn, sys_oid)

        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        result["sysObjectID"] = sys_oid
        result["latencyMs"] = elapsed_ms
        result["snmpPort"] = port

        self.active_workers = max(0, self.active_workers - 1)
        return result

snmp_engine = MockSNMPEngine()
