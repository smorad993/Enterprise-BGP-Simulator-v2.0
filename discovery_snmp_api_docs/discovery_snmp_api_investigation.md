# 🔍 gstack `/investigate` Technical Walkthrough
## Target: `discovery-snmp-api`
**Location**: `/Volumes/mobile/sevone/github/disc/discovery-snmp-api`

---

## 1. Executive Summary & Codebase Purpose

`discovery-snmp-api` is a Go microservice built to perform **automated SNMP discovery** on network infrastructure (Cisco, Arista, Ciena, DriveNets, Nokia, NVIDIA, SONiC, Dell). 

It accepts HTTP REST requests from network automation platforms (like SevOne), queries network devices over UDP via SNMP v2c/v3, parses MIB varbind responses, and returns standardized JSON telemetry (chassis serial numbers, interface tables, optical power metrics).

---

## 2. Deep Line-by-Line Code Investigation

### A. HTTP Transport & FQDN Validation (`api/api.go`)

```go
func fetchDeviceDetailsByFqdn(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("content-type", "application/json")
    var req web.Request
    err := helpers.DecodeJSONBody(w, r, &req)
    ...
    if strings.HasSuffix(req.Fqdn, helpers.ComcastNet) || strings.HasSuffix(req.Fqdn, helpers.ComcastCom) || strings.Contains(req.Fqdn, helpers.CCPDevices) {
        res, err := service.DeviceAttrService.LoadDeviceDetailsByFqdn(req)
        ...
        res.Send(w)
    } else {
        http.Error(w, "Not compatible device...", http.StatusBadRequest)
    }
}
```

1. **JSON Decoding**: Decodes the incoming JSON payload into `web.Request` struct.
2. **Domain Scope Gate**: Validates that the FQDN matches expected domain suffixes (`comcast.net`, `comcast.com`, or `CCPDevices`).
3. **Rejection Handling**: If FQDN validation fails, returns `HTTP 400 Bad Request` without wasting SNMP UDP socket connections.

---

### B. Asynchronous SNMP Stream Processing (`snmp/client.go`)

```go
func (s *snmpService) WalkAndFind(handler *ConnectionHandler, oid string, targetValue int) (res string, err error) {
    chassis := make(chan gosnmp.SnmpPDU)
    done := make(chan error)
    start := time.Now()
    
    go func() {
        defer helpers.RecoverWithErrorNotify(done)
        done <- handler.Connection.BulkWalk(oid, func(pdu gosnmp.SnmpPDU) error {
            switch pdu.Type {
            case gosnmp.Integer:
                if pdu.Value.(int) == targetValue {
                    chassis <- pdu
                    return fmt.Errorf("Result found. stop watching")
                }
            case gosnmp.EndOfMibView, gosnmp.EndOfContents:
                chassis <- pdu
                return fmt.Errorf("Result not found. stop watching")
            }
            return nil
        })
    }()

    select {
    case pdu := <-chassis:
        return pdu.Name, nil
    case err := <-done:
        return "", err
    case <-time.After(time.Duration(viper.GetInt(TimeoutProperty)) * time.Second):
        return "", fmt.Errorf("SNMP walk timeout exceeded")
    }
}
```

1. **Goroutine Execution**: Spawns a lightweight Go routine (`go func()`) to execute `BulkWalk` on the target OID tree asynchronously.
2. **Panic Safety**: Uses `defer helpers.RecoverWithErrorNotify(done)` to catch runtime panics (e.g. nil pointer in PDU parsing) without crashing the HTTP server.
3. **Channel Select Pattern**: Uses Go `select` to race between:
   * Successfully finding the target MIB value (`<-chassis`).
   * Reaching end of MIB view (`<-done`).
   * Hitting configured timeout (`<-time.After(...)`).

---

### C. Device Orchestration & Vendor Classification (`service/device_details.go`)

```go
func (s *deviceAttrService) LoadDeviceDetailsByIp(r web.Request) (*web.Response, error) {
    // 1. Fetch sysObjectID (.1.3.6.1.2.1.1.2.0)
    sysObjectID, err := s.api.GetOne(handler, ".1.3.6.1.2.1.1.2.0")
    if err != nil {
        return nil, fmt.Errorf("Failed to retrieve sysObjectID: %w", err)
    }

    // 2. Dispatch to specific vendor handler based on enterprise OID prefix
    switch {
    case strings.HasPrefix(sysObjectID, ".1.3.6.1.4.1.9."):
        return s.parseCiscoDevice(handler, r)
    case strings.HasPrefix(sysObjectID, ".1.3.6.1.4.1.30065."):
        return s.parseAristaDevice(handler, r)
    case strings.HasPrefix(sysObjectID, ".1.3.6.1.4.1.1271."):
        return s.parseCienaDevice(handler, r)
    case strings.HasPrefix(sysObjectID, ".1.3.6.1.4.1.6527."):
        return s.parseNokiaDevice(handler, r)
    default:
        return s.parseGenericDevice(handler, r)
    }
}
```

1. **Vendor Classification**: Queries `.1.3.6.1.2.1.1.2.0` (`sysObjectID`) to identify the hardware vendor.
2. **Enterprise OID Prefixes**:
   * `.1.3.6.1.4.1.9.` $\rightarrow$ **Cisco Systems**
   * `.1.3.6.1.4.1.30065.` $\rightarrow$ **Arista Networks**
   * `.1.3.6.1.4.1.1271.` $\rightarrow$ **Ciena**
   * `.1.3.6.1.4.1.6527.` $\rightarrow$ **Nokia**
3. **Targeted SNMP Walks**: Once vendor is identified, executes vendor-specific walks for chassis serial numbers, line cards, and optical telemetry.

---

## 3. Investigation Summary & Strengths

| Component | Assessment | Key Implementation Detail |
| :--- | :--- | :--- |
| **Resilience & Stability** | **High** | Panic recovery wrappers prevent unexpected SNMP malformed PDUs from taking down the microservice. |
| **Concurrency Model** | **High** | Uses non-blocking Go channels (`select`) with configurable `viper` timeouts for non-blocking I/O. |
| **Security Support** | **High** | Full support for SNMP v2c (community strings) and SNMP v3 (USM SHA/AES encryption). |
| **Extensibility** | **Medium-High** | New hardware vendors can be added by adding an Enterprise OID `case` in `service/device_details.go`. |
