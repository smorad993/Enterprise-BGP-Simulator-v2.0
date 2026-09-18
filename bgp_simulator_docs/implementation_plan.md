# 🛠 Interactive BGP 3-Router Neighbor & Message Exchange Simulator (`bgp-simulator`)
## Implementation Plan & Architectural Specification

**Goal**: Build a Python Flask & SVG/JavaScript interactive BGP protocol simulator replicating the exact 3-AS network topology (AS 100, AS 200, AS 300) with R1, R2, R3, and R4. The simulator visualizes eBGP/iBGP neighbor FSM state transitions, animated packet exchanges (OPEN, KEEPALIVE, UPDATE, NOTIFICATION), BGP table calculations, AS-Path evaluation, and eBGP AD=20 / iBGP AD=200 administrative distance routing tables.

---

## 📐 Topology & BGP Parameters (From Image)

```text
               ┌──────────────────────────────────────────┐
               │                 AS 100                   │
               │   R4 (40.1.1.2) ──(iBGP)── R1 (1.1.1.1) │
               └──────────────┬───────────────────┬───────┘
                              │ 10.1.1.0/24       │ 20.1.1.0/24
                       (eBGP) │                   │ (eBGP)
                              ▼                   ▼
               ┌───────────────────────┐   ┌───────────────────────┐
               │        AS 200         │   │        AS 300         │
               │      R2 (2.2.2.2)     │◄──┤      R3 (3.3.3.3)     │
               └───────────────────────┘   └───────────────────────┘
                          30.1.1.0/24 (eBGP)
```

### Topology Details:
1. **AS 100**:
   - **R1**: Loopback `1.1.1.1/32`. Interfaces: `s1/0` (`10.1.1.1/24`), `s1/1` (`20.1.1.1/24`), `s1/2` (`40.1.1.1/24`).
   - **R4**: Loopback `4.4.4.4/32`. Interface: `s1/0` (`40.1.1.2/24`).
2. **AS 200**:
   - **R2**: Loopback `2.2.2.2/32`. Interfaces: `s1/0` (`10.1.1.2/24`), `s1/1` (`30.1.1.1/24`).
3. **AS 300**:
   - **R3**: Loopback `3.3.3.3/32`. Interfaces: `s1/0` (`20.1.1.2/24`), `s1/1` (`30.1.1.2/24`).

### Administrative Distances:
- **eBGP AD = 20** (External BGP across AS boundaries)
- **iBGP AD = 200** (Internal BGP within same AS)

---

## 🏗 Component Breakdown

1. **`bgp_engine.py` (BGP Protocol State Machine)**:
   - **BGP FSM States**: `Idle` $\rightarrow$ `Connect` $\rightarrow$ `Active` $\rightarrow$ `OpenSent` $\rightarrow$ `OpenConfirm` $\rightarrow$ `Established`.
   - **BGP Message Generators**:
     * `OPEN`: Version 4, My AS, Hold Time (180s), BGP Identifier (Loopback IP).
     * `KEEPALIVE`: Sent every 3s to maintain established peering.
     * `UPDATE`: Advertises or withdraws NLRI prefixes (Prefix, Next-Hop, AS-Path, Origin).
     * `NOTIFICATION`: Error notifications.
   - **BGP Path Selection Logic**: Evaluates Weight $\rightarrow$ LocalPref $\rightarrow$ SelfOriginated $\rightarrow$ Shortest AS-Path $\rightarrow$ Origin $\rightarrow$ Lowest MED $\rightarrow$ eBGP over iBGP (AD 20 vs 200).

2. **`app.py` (Flask Server & API)**:
   - REST API endpoints for triggering neighbor reset (`clear ip bgp`), simulating link failures, adding prefix updates, and retrieving `show ip bgp summary` and `show ip bgp` outputs.

3. **`templates/index.html` & `static/style.css` / `static/app.js`**:
   - **Visual Topology Graph**: Interactive SVG canvas rendering AS 100 (orange cloud), AS 200 (green cloud), AS 300 (pink cloud), animated packet pulses along connection links.
   - **Live Packet Sniffer Log**: Color-coded packet capture feed (OPEN = Blue, KEEPALIVE = Cyan, UPDATE = Gold, NOTIFICATION = Red).
   - **Router Console Inspector**: Clicking any router opens CLI tabs (`show ip bgp summary`, `show ip bgp`, `show ip route`).

---

## 📁 File Structure

All documentation and code will be cleanly organized:

```text
Ai-lab/
├── bgp_simulator_docs/             # Consolidated BGP Documentation & Diagrams
│   ├── implementation_plan.md
│   └── bgp_topology_diagram.md
├── app.py                          # Flask Server
├── bgp_engine.py                  # BGP FSM & Route Table Calculations
├── requirements.txt                # Dependencies (flask)
├── templates/
│   └── index.html                  # Visual BGP Dashboard & SVG Topology
└── static/
    ├── style.css                   # Dark Mode Neon Networking Theme
    └── app.js                      # SVG Animation & BGP Packet Stream Controller
```

---

## 🧪 Verification Plan

1. **FSM State Verification**: Verify R1-R2, R1-R3, and R2-R3 transition through `Idle` $\rightarrow$ `Established`.
2. **Route Convergence & AS-Path**: Verify R1 receives `2.2.2.2/32` via AS-Path `[200]` (Next-Hop `10.1.1.2`) and `3.3.3.3/32` via AS-Path `[300]` (Next-Hop `20.1.1.1`).
3. **Link Failure & Reconvergence**: Toggle link `10.1.1.0/24` down and verify R1 reroutes traffic to `2.2.2.2/32` via R3 (AS-Path `[300, 200]`).
4. **`gstack` Automation**: Verify UI rendering and packet animation using `.claude/skills/gstack/browse/dist/browse`.
