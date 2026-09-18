# 🏛 Python SNMP Simulator Architecture Diagrams
## Project: `snmp-simulator` (Python replacement for `discovery-snmp-api`)

---

## 1. System Context Diagram (Level 1)

```mermaid
graph TD
    SevOne["SevOne NMS / Interrogation Service"]
    
    subgraph SimulatorBoundary ["Python Simulator System Boundary"]
        PythonSimulator["Python SNMP Discovery Simulator<br/>(app.py :5050)"]
    end

    MockHardware["Simulated Datacenter Hardware<br/>(Cisco, Arista, Ciena, DriveNets, Nokia, SONiC)"]
    Prometheus["Prometheus / Metrics Reader"]

    SevOne -->|POST /devices JSON| PythonSimulator
    Prometheus -->|GET /metrics| PythonSimulator
    PythonSimulator -->|Simulated OID Walk| MockHardware
    MockHardware -->> PythonSimulator : Return MIB PDUs
    PythonSimulator -->> SevOne : Return Standardized JSON
```

---

## 2. Sequence Execution Flow (Level 4)

```mermaid
sequenceDiagram
    autonumber
    actor SevOne as SevOne / Interrogation Client
    participant API as app.py (Flask API)
    participant Engine as snmp_engine.py
    participant Registry as vendor_drivers.py
    participant Parser as MIB Output Formatter

    SevOne->>API: POST /devices { fqdn, ipv4, snmpString }
    API->>API: Validate FQDN (.comcast.net, .ccp, .xcloud)
    API->>Engine: ProbeSysObjectID(ipv4)
    Engine-->>API: Return sysObjectID (.1.3.6.1.4.1.9 = Cisco)
    
    API->>Registry: GetDriver(".1.3.6.1.4.1.9.")
    Registry->>Engine: WalkVendorOIDs(IF-MIB, Chassis)
    Engine-->>Registry: Raw MIB Varbinds
    Registry->>Parser: ParseChassisAndInterfaces()
    Parser-->>API: Response Payload (Make: Cisco, Model: ASR-9904)
    API-->>SevOne: HTTP 200 OK JSON
```
