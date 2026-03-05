let currentScenario = 'pin_update';
let lastLogId = 0;

// Poll for logs every 2 seconds
async function fetchLogs() {
    try {
        const response = await fetch('/api/logs?last_id=' + lastLogId);
        const data = await response.json();
        
        if (data.logs && data.logs.length > 0) {
            data.logs.forEach(log => {
                addLogEntry(log);
                lastLogId = Math.max(lastLogId, log.id);
            });
            updateMetrics(data.metrics);
            updateCallStatus(data.active_call);
        }
    } catch (err) {
        console.error('Failed to fetch logs:', err);
    }
}

function addLogEntry(log) {
    const container = document.getElementById('logContainer');
    const entry = document.createElement('div');
    entry.className = 'log-entry ' + (log.type === 'request' ? 'inbound' : 'outbound');
    
    entry.innerHTML = `
        <div class="log-meta">
            <span>${log.type.toUpperCase()}</span>
            <span>${new Date(log.timestamp * 1000).toLocaleTimeString()}</span>
        </div>
        <pre>${JSON.stringify(log.content, null, 2)}</pre>
    `;
    
    container.prepend(entry);
}

function updateMetrics(metrics) {
    if (metrics) {
        document.getElementById('totalCalls').innerText = metrics.total || 0;
        document.getElementById('activeCalls').innerText = metrics.active || 0;
    }
}

function updateCallStatus(call) {
    const orb = document.getElementById('callOrb');
    const statusText = document.getElementById('callStatusText');
    
    if (call && call.active) {
        orb.style.background = 'var(--neon-blue)';
        orb.style.boxShadow = '0 0 50px rgba(0, 210, 255, 0.5)';
        statusText.innerHTML = `
            <h2 style="color: var(--neon-blue)">CALL IN PROGRESS</h2>
            <p style="color: var(--text-main)">Caller: ${call.caller}</p>
            <p style="color: var(--text-dim)">Current State: ${call.state}</p>
        `;
    } else {
        orb.style.background = 'var(--primary)';
        orb.style.boxShadow = '0 0 50px rgba(88, 166, 255, 0.3)';
        statusText.innerHTML = `
            <h2 style="color: var(--primary)">WAITING FOR CALL...</h2>
            <p style="color: var(--text-dim)">Listening on /api/external/hipcall-ingress</p>
        `;
    }
}

// Scenario Selection
document.getElementById('scenarioList').addEventListener('click', async (e) => {
    const btn = e.target.closest('.scenario-btn');

    // UI Update
    document.querySelectorAll('.scenario-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    currentScenario = btn.dataset.id;
    
    // Notify Backend
    try {
        await fetch('/api/active-scenario', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ scenario: currentScenario })
        });
    } catch (err) {
        console.error('Failed to set scenario:', err);
    }
});

// Start polling
setInterval(fetchLogs, 2000);
fetchLogs();
