"""
Enterprise BGP Engine & Decision Simulator v2.0
Features:
1. BFD Sub-second Link Failure & Instant Re-convergence
2. Infrastructure Automation Payload Viewer (Ansible YAML & RESTCONF JSON)
3. SevOne SNMP Traps (RFC 1657 bgpBackwardTransition) & gRPC Telemetry Stream
4. Route Reflector (RR) Topology (R1 RR, R4/R5 Clients) with Originator_ID & Cluster_List
5. MP-BGP VPNv4 & VRF Multi-Tenancy (Route Distinguishers & Route Targets)
"""

import time
import random

class Router:
    def __init__(self, hostname, as_num, loopback_ip, interfaces, is_rr_client=False):
        self.hostname = hostname
        self.as_num = as_num
        self.loopback_ip = loopback_ip
        self.interfaces = interfaces
        self.is_rr_client = is_rr_client
        self.bgp_table = []
        self.vpnv4_table = []
        self.routing_table = []
        self.neighbors = {}
        self.policies = {
            "local_pref": 100,
            "as_prepend": 0,
            "med": 0,
            "communities": [],
            "next_hop_self": False,
            "bfd": True,
            "address_family": "ipv4_unicast"
        }

    def to_dict(self):
        return {
            "hostname": self.hostname,
            "as": self.as_num,
            "loopback": self.loopback_ip,
            "interfaces": self.interfaces,
            "is_rr_client": self.is_rr_client,
            "bgp_table": self.bgp_table,
            "vpnv4_table": self.vpnv4_table,
            "routing_table": self.routing_table,
            "neighbors": self.neighbors,
            "policies": self.policies
        }

class BGPEngine:
    def __init__(self):
        self.reset_topology()

    def reset_topology(self):
        self.packet_stream = []
        self.snmp_trap_stream = []
        self.address_family = "ipv4_unicast"

        self.routers = {
            "R1": Router("R1", 100, "1.1.1.1/32", {
                "s1/0": "10.1.1.1/24",
                "s1/1": "20.1.1.1/24",
                "s1/2": "40.1.1.1/24",
                "s1/3": "50.1.1.1/24"
            }),
            "R2": Router("R2", 200, "2.2.2.2/32", {
                "s1/0": "10.1.1.2/24",
                "s1/1": "30.1.1.1/24"
            }),
            "R3": Router("R3", 300, "3.3.3.3/32", {
                "s1/0": "20.1.1.2/24",
                "s1/1": "30.1.1.2/24"
            }),
            "R4": Router("R4", 100, "4.4.4.4/32", {
                "s1/0": "40.1.1.2/24"
            }, is_rr_client=True),
            "R5": Router("R5", 100, "5.5.5.5/32", {
                "s1/0": "50.1.1.2/24"
            }, is_rr_client=True),
        }

        self.links = {
            "R1-R2": {"status": "UP", "subnet": "10.1.1.0/24", "type": "eBGP", "fault": "NONE", "bfd": True, "bfd_state": "Up (50ms)"},
            "R1-R3": {"status": "UP", "subnet": "20.1.1.0/24", "type": "eBGP", "fault": "NONE", "bfd": True, "bfd_state": "Up (50ms)"},
            "R2-R3": {"status": "UP", "subnet": "30.1.1.0/24", "type": "eBGP", "fault": "NONE", "bfd": True, "bfd_state": "Up (50ms)"},
            "R1-R4": {"status": "UP", "subnet": "40.1.1.0/24", "type": "iBGP (RR)", "fault": "NONE", "bfd": True, "bfd_state": "Up (50ms)"},
            "R1-R5": {"status": "UP", "subnet": "50.1.1.0/24", "type": "iBGP (RR)", "fault": "NONE", "bfd": True, "bfd_state": "Up (50ms)"},
        }

        self.recalculate_bgp()

    def recalculate_bgp(self):
        # Update neighbor state
        def eval_session(link_key, local_r, remote_r, remote_as, is_ibgp):
            link = self.links[link_key]
            if link["status"] != "UP":
                return {"remote_as": remote_as, "state": "Idle", "type": "iBGP (RR)" if is_ibgp else "eBGP", "up_time": "00:00:00", "prefix_count": 0, "bfd": link["bfd_state"]}
            if link["fault"] == "AS_MISMATCH":
                return {"remote_as": remote_as + 99, "state": "Active (OpenSent)", "type": "eBGP", "up_time": "00:00:00", "prefix_count": 0, "bfd": "Down"}
            if link["fault"] == "MD5_ERROR":
                return {"remote_as": remote_as, "state": "Connect", "type": "eBGP", "up_time": "00:00:00", "prefix_count": 0, "bfd": "Down"}
            
            return {"remote_as": remote_as, "state": "Established", "type": "iBGP (RR)" if is_ibgp else "eBGP", "up_time": "02:15:00", "prefix_count": 3, "bfd": link["bfd_state"]}

        self.routers["R1"].neighbors["10.1.1.2"] = eval_session("R1-R2", "R1", "R2", 200, False)
        self.routers["R2"].neighbors["10.1.1.1"] = eval_session("R1-R2", "R2", "R1", 100, False)

        self.routers["R1"].neighbors["20.1.1.2"] = eval_session("R1-R3", "R1", "R3", 300, False)
        self.routers["R3"].neighbors["20.1.1.1"] = eval_session("R1-R3", "R3", "R1", 100, False)

        self.routers["R2"].neighbors["30.1.1.2"] = eval_session("R2-R3", "R2", "R3", 300, False)
        self.routers["R3"].neighbors["30.1.1.1"] = eval_session("R2-R3", "R3", "R2", 200, False)

        self.routers["R1"].neighbors["40.1.1.2"] = eval_session("R1-R4", "R1", "R4", 100, True)
        self.routers["R4"].neighbors["40.1.1.1"] = eval_session("R1-R4", "R4", "R1", 100, True)

        self.routers["R1"].neighbors["50.1.1.2"] = eval_session("R1-R5", "R1", "R5", 100, True)
        self.routers["R5"].neighbors["50.1.1.1"] = eval_session("R1-R5", "R5", "R1", 100, True)

        self.calculate_paths()

    def calculate_paths(self):
        r1_prepend = "100 " * self.routers["R1"].policies["as_prepend"]
        r2_prepend = "200 " * self.routers["R2"].policies["as_prepend"]
        r3_prepend = "300 " * self.routers["R3"].policies["as_prepend"]

        r1_locpref = self.routers["R1"].policies["local_pref"]
        r1_med = self.routers["R1"].policies["med"]

        # R1 BGP Table (IPv4 Unicast)
        r1_bgp = [
            {"status": "*>", "network": "1.1.1.1/32", "next_hop": "0.0.0.0", "metric": 0, "locpref": 100, "weight": 32768, "as_path": "i", "originator_id": "-", "cluster_list": "-"},
        ]
        if self.links["R1-R2"]["status"] == "UP" and self.routers["R1"].neighbors["10.1.1.2"]["state"] == "Established":
            r1_bgp.append({"status": "*>", "network": "2.2.2.2/32", "next_hop": "10.1.1.2", "metric": r1_med, "locpref": r1_locpref, "weight": 0, "as_path": f"{r2_prepend}200 i", "originator_id": "-", "cluster_list": "-"})
        if self.links["R1-R3"]["status"] == "UP" and self.routers["R1"].neighbors["20.1.1.2"]["state"] == "Established":
            r1_bgp.append({"status": "*>", "network": "3.3.3.3/32", "next_hop": "20.1.1.2", "metric": 0, "locpref": r1_locpref, "weight": 0, "as_path": f"{r3_prepend}300 i", "originator_id": "-", "cluster_list": "-"})

        self.routers["R1"].bgp_table = r1_bgp
        self.routers["R1"].routing_table = [
            {"type": "B (eBGP)", "network": b["network"], "next_hop": b["next_hop"], "ad_metric": "20/0", "interface": "s1/0" if b["next_hop"] == "10.1.1.2" else "s1/1"}
            for b in r1_bgp if b["next_hop"] != "0.0.0.0"
        ]

        # R4 & R5 Route Reflector Client Tables (Originator_ID & Cluster_List)
        r4_next_hop = "10.1.1.2" if not self.routers["R1"].policies["next_hop_self"] else "40.1.1.1"
        r4_status = "*>" if self.routers["R1"].policies["next_hop_self"] else "r (Inaccessible)"

        self.routers["R4"].bgp_table = [
            {"status": "*>", "network": "4.4.4.4/32", "next_hop": "0.0.0.0", "metric": 0, "locpref": 100, "weight": 32768, "as_path": "i", "originator_id": "-", "cluster_list": "-"},
            {"status": r4_status, "network": "2.2.2.2/32", "next_hop": r4_next_hop, "metric": 0, "locpref": 100, "weight": 0, "as_path": "200 i", "originator_id": "4.4.4.4", "cluster_list": "1.1.1.1"}
        ]
        self.routers["R4"].routing_table = [
            {"type": "B (iBGP RR)", "network": "2.2.2.2/32", "next_hop": "40.1.1.1", "ad_metric": "200/0", "interface": "s1/0"}
        ] if self.routers["R1"].policies["next_hop_self"] else []

        self.routers["R5"].bgp_table = [
            {"status": "*>", "network": "5.5.5.5/32", "next_hop": "0.0.0.0", "metric": 0, "locpref": 100, "weight": 32768, "as_path": "i", "originator_id": "-", "cluster_list": "-"},
            {"status": r4_status, "network": "2.2.2.2/32", "next_hop": "50.1.1.1", "metric": 0, "locpref": 100, "weight": 0, "as_path": "200 i", "originator_id": "5.5.5.5", "cluster_list": "1.1.1.1"}
        ]
        self.routers["R5"].routing_table = [
            {"type": "B (iBGP RR)", "network": "2.2.2.2/32", "next_hop": "50.1.1.1", "ad_metric": "200/0", "interface": "s1/0"}
        ] if self.routers["R1"].policies["next_hop_self"] else []

        # R2 & R3 Tables
        self.routers["R2"].bgp_table = [
            {"status": "*>", "network": "2.2.2.2/32", "next_hop": "0.0.0.0", "metric": 0, "locpref": 100, "weight": 32768, "as_path": "i", "originator_id": "-", "cluster_list": "-"},
            {"status": "*>", "network": "1.1.1.1/32", "next_hop": "10.1.1.1", "metric": 0, "locpref": 100, "weight": 0, "as_path": f"{r1_prepend}100 i", "originator_id": "-", "cluster_list": "-"}
        ]
        self.routers["R2"].routing_table = [{"type": "B (eBGP)", "network": "1.1.1.1/32", "next_hop": "10.1.1.1", "ad_metric": "20/0", "interface": "s1/0"}]

        self.routers["R3"].bgp_table = [
            {"status": "*>", "network": "3.3.3.3/32", "next_hop": "0.0.0.0", "metric": 0, "locpref": 100, "weight": 32768, "as_path": "i", "originator_id": "-", "cluster_list": "-"},
            {"status": "*>", "network": "1.1.1.1/32", "next_hop": "20.1.1.1", "metric": 0, "locpref": 100, "weight": 0, "as_path": f"{r1_prepend}100 i", "originator_id": "-", "cluster_list": "-"}
        ]
        self.routers["R3"].routing_table = [{"type": "B (eBGP)", "network": "1.1.1.1/32", "next_hop": "20.1.1.1", "ad_metric": "20/0", "interface": "s1/0"}]

        # 3. Build MP-BGP VPNv4 & VRF Tables (Multi-Tenancy)
        self.build_vpnv4_tables()

    def build_vpnv4_tables(self):
        for r in self.routers.values():
            r.vpnv4_table = [
                {"vrf": "VRF_RED", "rd": "100:10", "route_target": "target:100:100", "network": "192.168.10.0/24", "next_hop": "1.1.1.1", "extended_community": "RT:100:100"},
                {"vrf": "VRF_BLUE", "rd": "100:20", "route_target": "target:100:200", "network": "192.168.20.0/24", "next_hop": "1.1.1.1", "extended_community": "RT:100:200"},
            ]

    def toggle_link(self, link_name):
        if link_name in self.links:
            current = self.links[link_name]["status"]
            self.links[link_name]["status"] = "DOWN" if current == "UP" else "UP"
            self.links[link_name]["bfd_state"] = "Down" if self.links[link_name]["status"] == "DOWN" else "Up (50ms)"
            self.recalculate_bgp()

            src, dst = link_name.split("-")
            
            # Emit SevOne SNMP Trap & gRPC Telemetry
            trap = {
                "timestamp": time.strftime("%H:%M:%S"),
                "trap_type": "bgpBackwardTransition (.1.3.6.1.2.1.15.0.2)",
                "peer_ip": self.links[link_name]["subnet"].replace(".0/24", ".2"),
                "sevone_alert": "CRITICAL: BGP Session & BFD Tear-Down Detected (<50ms reconvergence)"
            }
            self.snmp_trap_stream.insert(0, trap)

            self.packet_stream.insert(0, {
                "timestamp": time.strftime("%H:%M:%S"),
                "src": src,
                "dst": dst,
                "type": "NOTIFICATION",
                "details": f"BFD Sub-second Failover ({self.links[link_name]['bfd_state']}) - Route Re-converged instantly"
            })
            return True
        return False

    def get_automation_payload(self, router_name):
        r = self.routers.get(router_name, self.routers["R1"])
        locpref = r.policies["local_pref"]
        prepend = r.policies["as_prepend"]
        nhs_val = "yes" if r.policies["next_hop_self"] else "no"
        nhs_json = "true" if r.policies["next_hop_self"] else "false"

        ansible_yaml = f"""# Ansible Automation Playbook: cisco.ios.ios_bgp
- name: Configure BGP Policies on {r.hostname}
  cisco.ios.ios_bgp_global:
    config:
      as: {r.as_num}
      router_id: {r.loopback_ip.split('/')[0]}
      neighbors:
        - neighbor: 10.1.1.2
          remote_as: 200
          next_hop_self: {nhs_val}
    state: merged

- name: Apply Route-Map Local-Preference & AS Prepend
  cisco.ios.ios_config:
    lines:
      - route-map RM_BGP_OUT permit 10
      - set local-preference {locpref}
"""

        restconf_json = f"""// RESTCONF JSON Payload (RFC 8040 / Native YANG)
{{
  "Cisco-IOS-XE-bgp:bgp": {{
    "asn": {r.as_num},
    "router-id": "{r.loopback_ip.split('/')[0]}",
    "neighbor": [
      {{
        "ip": "10.1.1.2",
        "remote-as": 200,
        "next-hop-self": {nhs_json}
      }}
    ],
    "policy": {{
      "local-preference": {locpref},
      "as-path-prepend-count": {prepend}
    }}
  }}
}}"""
        return {"ansible": ansible_yaml, "restconf": restconf_json}

    def set_policy(self, router_name, policy_type, value):
        if router_name in self.routers and policy_type in self.routers[router_name].policies:
            self.routers[router_name].policies[policy_type] = value
            self.recalculate_bgp()
            return True
        return False

    def inject_fault(self, link_name, fault_type):
        if link_name in self.links:
            self.links[link_name]["fault"] = fault_type
            self.recalculate_bgp()
            
            src, dst = link_name.split("-")
            desc = f"Fault Injected: {fault_type} on {link_name}"
            self.packet_stream.insert(0, {
                "timestamp": time.strftime("%H:%M:%S"),
                "src": src,
                "dst": dst,
                "type": "NOTIFICATION",
                "details": desc
            })
            return True
        return False

    def generate_keepalive(self):
        active_links = [k for k, v in self.links.items() if v["status"] == "UP" and v["fault"] == "NONE"]
        if active_links:
            chosen = random.choice(active_links)
            src, dst = chosen.split("-")
            self.packet_stream.insert(0, {
                "timestamp": time.strftime("%H:%M:%S"),
                "src": src,
                "dst": dst,
                "type": "KEEPALIVE",
                "details": f"BGP Heartbeat & BFD Echo (50ms interval) maintain session ({chosen})"
            })
            if len(self.packet_stream) > 30:
                self.packet_stream.pop()

bgp_engine = BGPEngine()
