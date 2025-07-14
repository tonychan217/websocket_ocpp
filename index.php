<?php
// index.php -- Live OCPP WS Log with “latest‐only” Categorized Detail Panel + JSON breakdown
header('Content-Type: text/html; charset=UTF-8');
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>OCPP Monitor</title>
  <style>
    /* RESET & BASE */
    *, *::before, *::after { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", Roboto, sans-serif;
      background: #f1f3f5;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    /* CONTAINER */
    .container {
      width: 95%;
      max-width: 1500px;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.1);
      display: flex;
      flex-direction: column;
      height: 95vh;
      overflow: hidden;
    }
    .header {
      border: 1px solid #ddd;
      background: #007bff;
      color: #fff;
      padding: 1rem;
      text-align: center;
      font-size: 1.25rem;
      flex-shrink: 0;
    }
    /* MAIN CONTENT: two columns */
    .content {
      flex: 1;
      display: flex;
      overflow: hidden;
    }
    #log, #detail {
      flex: 1;
      padding: 1rem;
      overflow-y: auto;
    }
    #detail {
      border-left: 1px solid #e0e0e0;
      background: #fafbfc;
    }
    /* LOG AREA */
    .entry {
      margin-bottom: 0.5rem;
      font-family: monospace;
      line-height: 1.4;
      word-wrap: break-word;
    }
    .entry .ts {
      color: #888;
      margin-right: 0.5rem;
      font-size: 0.85em;
    }
    .entry.status {
      font-style: italic;
      color: #555;
    }
    /* DETAIL AREA: three categories */
    #detail .subheader {
      padding: 0.5rem;
      font-weight: bold;
      margin-top: 1rem;
    }
    #detail table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 0.5rem;
      margin-bottom: 1rem;
      font-family: monospace;
      font-size: 0.9rem;
    }
    #detail th, #detail td {
      padding: 0.5rem;
      border: 1px solid #ddd;
      text-align: left;
      word-break: break-all;
    }
    #detail th {
      background: #f0f0f0;
    }
    /* RESPONSIVE */
    @media (max-width: 700px) {
      .content { flex-direction: column; }
      #detail { border-left: none; border-top: 1px solid #e0e0e0; }
    }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">OCPP Monitor</div>
    <div class="content">
      <div id="log">
        <div class="entry status"><span class="ts">--:--:--</span>Connecting…</div>
      </div>
      <div id="detail">
        <div id="detail-status" class="entry status"><span class="ts">--:--:--</span>No messages yet</div>
        <!-- Welcome -->
        <div class="subheader">Startup</div>
        <table id="welcome-table">
          <thead><tr><th>Timestamp</th><th>Raw JSON</th></tr></thead>
          <tbody></tbody>
        </table>
        <table id="welcome-desc">
          <thead><tr><th>Name</th><th>Value</th></tr></thead>
          <tbody></tbody>
        </table>
        <!-- Heartbeat -->
        <div class="subheader">Heartbeat</div>
        <table id="heartbeat-table">
          <thead><tr><th>Timestamp</th><th>Raw JSON</th></tr></thead>
          <tbody></tbody>
        </table>
        <table id="heartbeat-desc">
          <thead><tr><th>Name</th><th>Value</th></tr></thead>
          <tbody></tbody>
        </table>
        <!-- Other -->
        <div class="subheader">Messages</div>
        <table id="other-table">
          <thead><tr><th>Timestamp</th><th>Raw JSON</th></tr></thead>
          <tbody></tbody>
        </table>
        <table id="other-desc">
          <thead><tr><th>Name</th><th>Value</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>

  <script>
  (function(){
    const host = location.hostname, port = 2409, url = `ws://${host}:${port}`;
    const log     = document.getElementById('log'),
          status  = document.getElementById('detail-status'),
          tblWelcome   = document.querySelector('#welcome-table tbody'),
          descWelcome  = document.querySelector('#welcome-desc tbody'),
          tblHeartbeat = document.querySelector('#heartbeat-table tbody'),
          descHeartbeat= document.querySelector('#heartbeat-desc tbody'),
          tblOther     = document.querySelector('#other-table tbody'),
          descOther    = document.querySelector('#other-desc tbody');
    let firstMessage = true;

    function nowTs() {
      const d = new Date(), z = n=>String(n).padStart(2,'0');
      return `${d.getFullYear()}-${z(d.getMonth()+1)}-${z(d.getDate())}`
           + ` ${z(d.getHours())}:${z(d.getMinutes())}:${z(d.getSeconds())}`;
    }

    function appendLog(msg, cls='') {
      const e = document.createElement('div'), ts = document.createElement('span');
      e.className = 'entry' + (cls? ' '+cls:'');
      ts.className = 'ts'; ts.textContent = nowTs();
      e.appendChild(ts);
      e.appendChild(document.createTextNode(msg));
      log.appendChild(e);
      log.scrollTop = log.scrollHeight;
    }

    function setLatest(tbodyRaw, tbodyDesc, raw) {
      // raw JSON row
      tbodyRaw.innerHTML = '';
      const trRaw = document.createElement('tr'),
            tdTs = document.createElement('td'),
            tdRaw= document.createElement('td');
      tdTs.innerHTML = `<span class="ts">${nowTs()}</span>`;
      tdRaw.textContent = raw;
      trRaw.appendChild(tdTs);
      trRaw.appendChild(tdRaw);
      tbodyRaw.appendChild(trRaw);
      // description rows
      tbodyDesc.innerHTML = '';
      let obj;
      try { obj = JSON.parse(raw); }
      catch {
        const tr = document.createElement('tr'),
              tdN = document.createElement('td'),
              tdV = document.createElement('td');
        tdN.textContent = 'raw';
        tdV.textContent = raw;
        tr.appendChild(tdN); tr.appendChild(tdV);
        tbodyDesc.appendChild(tr);
        return;
      }
      if (Array.isArray(obj)) {
        obj.forEach((val,i)=> {
          const tr = document.createElement('tr'),
                tdN = document.createElement('td'),
                tdV = document.createElement('td');
          tdN.textContent = `Index ${i}`;
          tdV.textContent = (typeof val==='object')? JSON.stringify(val): String(val);
          tr.appendChild(tdN); tr.appendChild(tdV);
          tbodyDesc.appendChild(tr);
        });
      } else if (typeof obj==='object' && obj!==null) {
        Object.entries(obj).forEach(([k,v])=>{
          const tr = document.createElement('tr'),
                tdN = document.createElement('td'),
                tdV = document.createElement('td');
          tdN.textContent = k;
          tdV.textContent = (typeof v==='object')? JSON.stringify(v): String(v);
          tr.appendChild(tdN); tr.appendChild(tdV);
          tbodyDesc.appendChild(tr);
        });
      } else {
        const tr = document.createElement('tr'),
              tdN = document.createElement('td'),
              tdV = document.createElement('td');
        tdN.textContent = 'value';
        tdV.textContent = String(obj);
        tr.appendChild(tdN); tr.appendChild(tdV);
        tbodyDesc.appendChild(tr);
      }
    }

    function categorize(raw) {
      if (firstMessage) {
        status.remove();
        firstMessage = false;
      }
      let obj;
      try { obj = JSON.parse(raw); }
      catch {
        setLatest(tblOther, descOther, raw);
        return;
      }
      if (obj && obj.type==='welcome') {
        setLatest(tblWelcome, descWelcome, raw);
      } else if (obj && obj.type==='heartbeat') {
        setLatest(tblHeartbeat, descHeartbeat, raw);
      } else {
        setLatest(tblOther, descOther, raw);
      }
    }

    function connect(){
      appendLog(`Connecting to ${url}`,'status');
      const ws = new WebSocket(url);
      ws.onopen    = () => appendLog('Connected','status');
      ws.onmessage = ev => { appendLog(ev.data); categorize(ev.data); };
      ws.onclose   = () => {
        appendLog('Connection closed; retrying in 3s…','status');
        setTimeout(connect,3000);
      };
      ws.onerror   = err => {
        console.error('WS error',err);
        appendLog('WebSocket error','status');
      };
    }
    connect();
  })();
  </script>
</body>
</html>
