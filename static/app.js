/**
 * Enterprise BGP Simulator v2.0 Client Controller
 */

document.addEventListener("DOMContentLoaded", () => {
    let activeRouter = "R1";
    let activeCmd = "summary";
    let activeCodeTab = "ansible";
    let bgpData = null;
    let automationPayloads = null;

    // DOM Elements
    const cliPrompt = document.getElementById("cliPrompt");
    const cliOutput = document.getElementById("cliOutput");
    const streamList = document.getElementById("streamList");
    const trapList = document.getElementById("trapList");
    const btnResetBgp = document.getElementById("btnResetBgp");

    // Policy Control Selects
    const selectRouterPolicy = document.getElementById("selectRouterPolicy");
    const selectAddrFamily = document.getElementById("selectAddrFamily");
    const selectPrepend = document.getElementById("selectPrepend");
    const selectLocalPref = document.getElementById("selectLocalPref");
    const selectNextHopSelf = document.getElementById("selectNextHopSelf");

    // Fault & Automation Buttons
    const btnOpenAutomation = document.getElementById("btnOpenAutomation");
    const btnFaultAsMismatch = document.getElementById("btnFaultAsMismatch");
    const btnFaultMd5 = document.getElementById("btnFaultMd5");
    const btnClearFaults = document.getElementById("btnClearFaults");

    // Modals
    const modalTieBreaker = document.getElementById("modalTieBreaker");
    const btnOpenTieBreaker = document.getElementById("btnOpenTieBreaker");
    const btnCloseModal = document.getElementById("btnCloseModal");

    const modalAutomation = document.getElementById("modalAutomation");
    const btnCloseAutomation = document.getElementById("btnCloseAutomation");
    const btnTabAnsible = document.getElementById("btnTabAnsible");
    const btnTabRestconf = document.getElementById("btnTabRestconf");
    const codePayloadDisplay = document.getElementById("codePayloadDisplay");

    fetchBgpState();
    setInterval(fetchBgpState, 2000);

    // Event Listeners for Router & Command Tabs
    document.querySelectorAll(".router-selector .tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".router-selector .tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeRouter = btn.dataset.router;
            
            document.querySelectorAll(".router-node").forEach(n => n.classList.remove("active-router"));
            const node = document.getElementById(`node-${activeRouter}`);
            if (node) node.classList.add("active-router");

            renderCli();
        });
    });

    document.querySelectorAll(".cli-command-tabs .cmd-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".cli-command-tabs .cmd-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            activeCmd = btn.dataset.cmd;
            renderCli();
        });
    });

    // Policy Listener Handlers
    selectPrepend.addEventListener("change", () => {
        applyPolicy(selectRouterPolicy.value, "as_prepend", parseInt(selectPrepend.value));
    });

    selectLocalPref.addEventListener("change", () => {
        applyPolicy(selectRouterPolicy.value, "local_pref", parseInt(selectLocalPref.value));
    });

    selectNextHopSelf.addEventListener("change", () => {
        applyPolicy("R1", "next_hop_self", selectNextHopSelf.value === "true");
    });

    selectAddrFamily.addEventListener("change", () => {
        if (selectAddrFamily.value === "vpnv4") {
            activeCmd = "vpnv4";
            document.querySelectorAll(".cli-command-tabs .cmd-btn").forEach(b => b.classList.remove("active"));
            const vpnv4Btn = document.querySelector('.cli-command-tabs .cmd-btn[data-cmd="vpnv4"]');
            if (vpnv4Btn) vpnv4Btn.classList.add("active");
        } else {
            activeCmd = "bgp";
            document.querySelectorAll(".cli-command-tabs .cmd-btn").forEach(b => b.classList.remove("active"));
            const bgpBtn = document.querySelector('.cli-command-tabs .cmd-btn[data-cmd="bgp"]');
            if (bgpBtn) bgpBtn.classList.add("active");
        }
        renderCli();
    });

    // Fault Injection Handlers
    btnFaultAsMismatch.addEventListener("click", () => injectFault("R1-R2", "AS_MISMATCH"));
    btnFaultMd5.addEventListener("click", () => injectFault("R1-R3", "MD5_ERROR"));
    btnClearFaults.addEventListener("click", () => {
        injectFault("R1-R2", "NONE");
        injectFault("R1-R3", "NONE");
    });

    // Modal Tie-Breaker Listeners
    btnOpenTieBreaker.addEventListener("click", () => modalTieBreaker.classList.add("active"));
    btnCloseModal.addEventListener("click", () => modalTieBreaker.classList.remove("active"));
    modalTieBreaker.addEventListener("click", (e) => {
        if (e.target === modalTieBreaker) modalTieBreaker.classList.remove("active");
    });

    // Modal Automation Listeners
    btnOpenAutomation.addEventListener("click", () => {
        modalAutomation.classList.add("active");
        fetchAutomationPayload();
    });
    btnCloseAutomation.addEventListener("click", () => modalAutomation.classList.remove("active"));
    modalAutomation.addEventListener("click", (e) => {
        if (e.target === modalAutomation) modalAutomation.classList.remove("active");
    });

    btnTabAnsible.addEventListener("click", () => {
        btnTabAnsible.classList.add("active");
        btnTabRestconf.classList.remove("active");
        activeCodeTab = "ansible";
        renderCodePayload();
    });

    btnTabRestconf.addEventListener("click", () => {
        btnTabRestconf.classList.add("active");
        btnTabAnsible.classList.remove("active");
        activeCodeTab = "restconf";
        renderCodePayload();
    });

    selectRouterPolicy.addEventListener("change", () => {
        if (modalAutomation.classList.contains("active")) {
            fetchAutomationPayload();
        }
    });

    // Link Toggles
    document.getElementById("btnToggleR1R2").addEventListener("click", () => toggleLink("R1-R2"));
    document.getElementById("btnToggleR1R3").addEventListener("click", () => toggleLink("R1-R3"));
    document.getElementById("btnToggleR2R3").addEventListener("click", () => toggleLink("R2-R3"));

    btnResetBgp.addEventListener("click", () => {
        fetch("/api/bgp/reset", { method: "POST" }).then(() => fetchBgpState());
    });

    function applyPolicy(routerName, policyType, value) {
        fetch("/api/bgp/policy", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ router_name: routerName, policy_type: policyType, value: value })
        }).then(() => fetchBgpState());
    }

    function injectFault(linkName, faultType) {
        fetch("/api/bgp/fault", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ link_name: linkName, fault_type: faultType })
        }).then(() => fetchBgpState());
    }

    function toggleLink(linkName) {
        fetch("/api/bgp/link/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ link_name: linkName })
        }).then(() => fetchBgpState());
    }

    function fetchBgpState() {
        fetch("/api/bgp/state")
            .then(res => res.json())
            .then(data => {
                bgpData = data;
                updateLinkVisuals(data.links);
                renderCli();
                renderTraps(data.snmp_traps || []);
                updateTieBreakerValues();
            });
    }

    function fetchAutomationPayload() {
        const router = selectRouterPolicy.value || "R1";
        fetch(`/api/bgp/automation?router=${router}`)
            .then(res => res.json())
            .then(data => {
                automationPayloads = data;
                renderCodePayload();
            });
    }

    function renderCodePayload() {
        if (!automationPayloads) {
            codePayloadDisplay.textContent = "Loading automation payloads...";
            return;
        }
        if (activeCodeTab === "ansible") {
            codePayloadDisplay.textContent = automationPayloads.ansible;
        } else {
            codePayloadDisplay.textContent = automationPayloads.restconf;
        }
    }

    function updateLinkVisuals(links) {
        if (!links) return;
        for (const [key, info] of Object.entries(links)) {
            const line = document.getElementById(`link-${key}`);
            if (line) {
                if (info.status === "DOWN" || info.fault !== "NONE") {
                    line.classList.add("down");
                } else {
                    line.classList.remove("down");
                }
            }
        }
    }

    function updateTieBreakerValues() {
        if (!bgpData || !bgpData.routers || !bgpData.routers.R1) return;
        const r1 = bgpData.routers.R1;
        const locPref = r1.policies.local_pref || 100;
        const prepend = r1.policies.as_prepend || 0;

        document.getElementById("tbLocPref1").textContent = locPref;
        
        let path1 = "[200]";
        if (prepend > 0) path1 = `[200 ${'100 '.repeat(prepend).trim()}]`;
        document.getElementById("tbPath1").textContent = path1;

        if (locPref > 100) {
            document.getElementById("tbLocPrefWinner").textContent = "★ Path via R2 (LocPref 200)";
            document.getElementById("tbLocPrefWinner").className = "winner-cell";
        } else {
            document.getElementById("tbLocPrefWinner").textContent = "Tie";
        }
    }

    function renderCli() {
        if (!bgpData || !bgpData.routers || !bgpData.routers[activeRouter]) return;
        const router = bgpData.routers[activeRouter];

        if (activeCmd === "summary") {
            cliPrompt.textContent = `${router.hostname}# show ip bgp summary`;
            let text = `BGP router identifier ${router.loopback.split('/')[0]}, local AS number ${router.as}\n`;
            text += `BGP table version is 6, main routing table version 6\n\n`;
            text += `Neighbor        V    AS MsgRcvd MsgSent   TblVer  InQ OutQ Up/Down  State/PfxRcd BFD-State\n`;
            text += `--------------------------------------------------------------------------------------\n`;
            
            for (const [neighIp, n] of Object.entries(router.neighbors)) {
                const ipPad = neighIp.padEnd(15, ' ');
                const asPad = String(n.remote_as).padEnd(5, ' ');
                const upPad = n.up_time.padEnd(8, ' ');
                const bfdPad = (n.bfd || 'Up (50ms)').padEnd(10, ' ');
                const stateVal = n.state === "Established" ? String(n.prefix_count) : n.state;
                text += `${ipPad} 4    ${asPad}    184     192        6    0    0 ${upPad} ${stateVal.padEnd(12, ' ')} ${bfdPad}\n`;
            }
            cliOutput.textContent = text;
        } 
        else if (activeCmd === "bgp") {
            cliPrompt.textContent = `${router.hostname}# show ip bgp`;
            let text = `BGP table version is 6, local router ID is ${router.loopback.split('/')[0]}\n`;
            text += `Status codes: s suppressed, d damped, h history, * valid, > best, i - internal, r RIB-failure\n`;
            text += `Origin codes: i - IGP, e - EGP, ? - incomplete\n\n`;
            text += `   Network          Next Hop          Metric LocPrf Weight Path       Originator Cluster\n`;
            text += `------------------------------------------------------------------------------------------\n`;

            router.bgp_table.forEach(b => {
                const st = (b.status + " ").padEnd(3, ' ');
                const net = b.network.padEnd(16, ' ');
                const hop = b.next_hop.padEnd(16, ' ');
                const met = String(b.metric).padEnd(6, ' ');
                const loc = String(b.locpref).padEnd(6, ' ');
                const wt = String(b.weight).padEnd(6, ' ');
                const path = (b.as_path || '').padEnd(10, ' ');
                const orig = (b.originator_id || '-').padEnd(10, ' ');
                const clus = b.cluster_list || '-';
                text += `${st}${net}${hop}${met}${loc}${wt}${path}${orig}${clus}\n`;
            });
            cliOutput.textContent = text;
        } 
        else if (activeCmd === "route") {
            cliPrompt.textContent = `${router.hostname}# show ip route bgp`;
            let text = `Codes: C - connected, S - static, R - RIP, B - BGP\n`;
            text += `       AD: eBGP = 20, iBGP = 200\n\n`;

            if (router.routing_table.length === 0) {
                text += `% No BGP routes in routing table (Unreachable eBGP Next-Hop or Session Down)\n`;
            } else {
                router.routing_table.forEach(r => {
                    text += `${r.type} ${r.network} [${r.ad_metric}] via ${r.next_hop}, 02:15:00, ${r.interface}\n`;
                });
            }
            cliOutput.textContent = text;
        }
        else if (activeCmd === "vpnv4") {
            cliPrompt.textContent = `${router.hostname}# show ip bgp vpnv4 all`;
            let text = `BGP route identifier ${router.loopback.split('/')[0]}, local AS number ${router.as}\n`;
            text += `Route Distinguishers (RD) & Route Targets (RT) Multi-Tenancy Table:\n\n`;
            text += `VRF Name    RD        Route Target      Network          Next Hop   ExtCommunity\n`;
            text += `--------------------------------------------------------------------------------\n`;

            if (!router.vpnv4_table || router.vpnv4_table.length === 0) {
                text += `% No VPNv4 routes present in VRF table\n`;
            } else {
                router.vpnv4_table.forEach(v => {
                    const vrf = v.vrf.padEnd(11, ' ');
                    const rd = v.rd.padEnd(9, ' ');
                    const rt = v.route_target.padEnd(17, ' ');
                    const net = v.network.padEnd(16, ' ');
                    const hop = v.next_hop.padEnd(10, ' ');
                    text += `${vrf}${rd}${rt}${net}${hop}${v.extended_community}\n`;
                });
            }
            cliOutput.textContent = text;
        }
    }

    function renderTraps(traps) {
        if (!traps || traps.length === 0) {
            trapList.innerHTML = `<div style="color:var(--text-muted); text-align:center; padding:1rem; font-size:0.85rem;">No SNMP Traps fired yet. Toggle a link or inject a fault to generate SevOne telemetry.</div>`;
            return;
        }

        trapList.innerHTML = traps.map(t => `
            <div class="trap-item">
                <div class="trap-header">
                    <span class="trap-badge">🚨 SNMP TRAP</span>
                    <span class="trap-type">${t.trap_type}</span>
                    <span class="trap-time">${t.timestamp}</span>
                </div>
                <div class="trap-body">
                    <strong>Peer IP:</strong> ${t.peer_ip} &bull; <span>${t.sevone_alert}</span>
                </div>
            </div>
        `).join("");
    }
});
