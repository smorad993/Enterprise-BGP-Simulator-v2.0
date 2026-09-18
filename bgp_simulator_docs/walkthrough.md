# 🚀 Enterprise BGP Simulator v2.0 Walkthrough

We upgraded the **BGP Engine & Decision Simulator** with sub-second BFD failover, Ansible/RESTCONF automation payload code viewer, SevOne SNMP Traps & Telemetry simulation, Route Reflector (RR) topology with R4 and R5, and MP-BGP VPNv4 VRF multi-tenancy. All documentation is stored in [`bgp_simulator_docs/`](file:///bgp_simulator_docs/).

---

## ⚡ 1. BFD (Bidirectional Forwarding Detection) Integration
* **Sub-second Failover (50ms)**: Standard BGP timers (60s keepalive, 180s hold) are bypassed when BFD is enabled.
* **Instant Re-convergence**: Toggling link `R1-R2` drops the link status to `DOWN` and `bfd_state` to `Down`. The engine instantly tears down the BGP adjacency (<50ms) and re-converges routes without waiting for hold timer expiration.
* **Console Indicator**: `show ip bgp summary` displays real-time BFD session state (`Up (50ms)` vs `Down`).

---

## 🛠 2. Infrastructure Automation Payload Viewer
* **GUI-to-Code Translation**: Clicking **"🛠 View Ansible & RESTCONF Code"** opens a modal that converts GUI policy changes into production-ready configuration code.
* **Ansible Playbook (YAML)**: Generates `cisco.ios.ios_bgp` tasks reflecting Local Preference, AS-Path Prepend, and `next-hop-self` settings.
* **RESTCONF API Payload (JSON)**: Generates RFC 8040 / Native YANG JSON payloads (`Cisco-IOS-XE-bgp:bgp`) for programmatic network orchestration platforms.

---

## 📡 3. SevOne SNMP Traps & Telemetry Simulation
* **RFC 1657 `bgpBackwardTransition` Traps**: When link failures or fault injections (AS Mismatch, MD5 Auth Error) occur, routers fire observable telemetry traps (`.1.3.6.1.2.1.15.0.2`).
* **SevOne Platform Stream**: The **SevOne Telemetry Stream** pane displays real-time CRITICAL alerts indicating BGP session state transitions and BFD teardowns, simulating what upstream performance and discovery platforms like IBM SevOne ingest during network events.

---

## 🔁 4. Route Reflector (RR) Topology & iBGP Loop Prevention
* **RR Cluster Architecture**: AS 100 features **R1** as the Route Reflector (Cluster ID `1.1.1.1`) with **R4** and **R5** as Route Reflector Clients.
* **`Originator_ID` & `Cluster_List` Attributes**: In `show ip bgp`, R4 and R5 show `Originator_ID` (`4.4.4.4` / `5.5.5.5`) and `Cluster_List` (`1.1.1.1`) attributes, demonstrating how routers prevent routing loops when standard iBGP split-horizon rules are bypassed.

---

## 🏢 5. Multiprotocol BGP (MP-BGP) & VRFs (VPNv4 Multi-Tenancy)
* **Address Family Selector**: Users can toggle between **IPv4 Unicast** and **VPNv4 MP-BGP (VRFs)**.
* **Multi-Tenant Route Isolation**: `show ip bgp vpnv4 all` displays VPNv4 routes for isolated tenant instances:
  * **`VRF_RED`**: Route Distinguisher `100:10`, Route Target `target:100:100`, Prefix `192.168.10.0/24`
  * **`VRF_BLUE`**: Route Distinguisher `100:20`, Route Target `target:100:200`, Prefix `192.168.20.0/24`

---

## 🔍 6. 10-Step BGP Best-Path Decision Tie-Breaker Evaluator
Clicking **"🔍 Open 10-Step Tie-Breaker Breakdown"** opens an evaluation table comparing competing paths to prefix **2.2.2.2/32** on R1:

| Step | BGP Tie-Breaker Rule | Path via R2 (`10.1.1.2`) | Path via R3 (`20.1.1.2`) | Winner |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Highest Weight (Cisco Proprietary) | `0` | `0` | Tie |
| **2** | Highest Local Preference | `100` (or `200`) | `100` | ★ Path via R2 (if LocPref=200) |
| **3** | Locally Originated (`0.0.0.0`) | No | No | Tie |
| **4** | Shortest AS-Path Length | `[200]` (Length: 1) | `[300, 200]` (Length: 2) | ★ Path via R2 |
| **5** | Lowest Origin Type ($i < e < ?$) | IGP (`i`) | IGP (`i`) | Tie |
| **6** | Lowest MED (Multi-Exit Discriminator) | `0` | `0` | Tie |
| **7** | eBGP over iBGP Path | eBGP (AD 20) | eBGP (AD 20) | Tie |
| **8** | Lowest IGP Metric to Next-Hop | `0` | `0` | Tie |

---

## 🧪 Verification Summary

- **Live URL**: `http://127.0.0.1:5050`
- **CLI Commands Verified**: `show ip bgp summary`, `show ip bgp`, `show ip route bgp`, `show ip bgp vpnv4 all`
- **API Endpoints**:
  - `GET /api/bgp/state` (Topology, Neighbor states, BFD status, SNMP Traps)
  - `GET /api/bgp/automation?router=R1` (Ansible YAML & RESTCONF JSON)
  - `POST /api/bgp/policy` (LocalPref, AS-Prepend, next-hop-self)
  - `POST /api/bgp/link/toggle` (Sub-second BFD failover)

