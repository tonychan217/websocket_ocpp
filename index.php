<?php
// index.php — Live OCPP WS Log with Detail Panel
header('Content-Type: text/html; charset=UTF-8');
?>
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Live OCPP WS Log</title>
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
      max-width: 1000px;
      background: #fff;
      border-radius: 8px;
      box-shadow: 0 4px 16px rgba(0,0,0,0.1);
      display: flex;
      flex-direction: column;
      height: 95vh;
      overflow: hidden;
    }
    .header {
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
    /* DETAIL AREA */
    .jsonRaw {
      background: #f8f9fa;
      padding: 0.75rem;
      border-radius: 4px;
      font-family: monospace;
      white-space: pre;
      overflow-x: auto;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
      font-size: 0.95rem;
    }
    th, td {
      padding: 0.5rem;
      border: 1px solid #ddd;
      text-align: left;
      vertical-align: top;
    }
    th {
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
    <div class="header">OCPP WS Server → Live Log</div>
    <div class="content">
      <div id="log">
        <div class="entry status"><span class="ts">--:--:--</span>Connecting…</div>
      </div>
      <div id="detail">
        <div class="entry status"><span class="ts">--:--:--</span>No message selected</div>
      </div>
    </div>
  </div>

  <script>
  (function(){
    const host = location.hostname;
    const port = 2409;
    const url  = `ws://${host}:${port}`;
    const log  = document.getElementById('log');
    const detail = document.getElementById('detail');

    // Map array indices to OCPP fields
    const fieldNames = {
      0: "MessageTypeId",
      1: "UniqueId",
      2: "Action",
      3: "Payload"
    };

    function nowTs() {
      const d = new Date();
      const z = n => String(n).padStart(2,'0');
      return `${d.getFullYear()}-${z(d.getMonth()+1)}-${z(d.getDate())}`
           + ` ${z(d.getHours())}:${z(d.getMinutes())}:${z(d.getSeconds())}`;
    }

    function appendLog(msg, cls='') {
      const e = document.createElement('div');
      e.className = 'entry' + (cls ? ' ' + cls : '');
      const ts = document.createElement('span');
      ts.className = 'ts';
      ts.textContent = nowTs();
      e.appendChild(ts);
      e.appendChild(document.createTextNode(msg));
      log.appendChild(e);
      log.scrollTop = log.scrollHeight;
    }

    function showDetail(raw) {
      detail.innerHTML = ''; // clear
      // timestamp
      const hdr = document.createElement('div');
      hdr.className = 'entry status';
      const ts = document.createElement('span');
      ts.className = 'ts';
      ts.textContent = nowTs();
      hdr.appendChild(ts);
      hdr.appendChild(document.createTextNode('Detail view'));
      detail.appendChild(hdr);

      // raw JSON
      const pre = document.createElement('div');
      pre.className = 'jsonRaw';
      pre.textContent = raw;
      detail.appendChild(pre);

      // parse
      let obj;
      try { obj = JSON.parse(raw); }
      catch (e) {
        const err = document.createElement('div');
        err.className = 'entry status';
        err.textContent = 'Invalid JSON';
        detail.appendChild(err);
        return;
      }

      // If array: top-level fields
      if (Array.isArray(obj)) {
        const tbl = document.createElement('table');
        const thead = document.createElement('thead');
        thead.innerHTML = '<tr><th>Index</th><th>Field</th><th>Value</th></tr>';
        tbl.appendChild(thead);
        const tbody = document.createElement('tbody');
        obj.forEach((val,i) => {
          const tr = document.createElement('tr');
          const idx = document.createElement('td');
          idx.textContent = i;
          const fn = document.createElement('td');
          fn.textContent = fieldNames[i]||'';
          const vv = document.createElement('td');
          vv.textContent = (typeof val==='object')
            ? JSON.stringify(val)
            : String(val);
          tr.appendChild(idx);
          tr.appendChild(fn);
          tr.appendChild(vv);
          tbody.appendChild(tr);
        });
        tbl.appendChild(tbody);
        detail.appendChild(tbl);

        // If payload is object, show its key/values
        if (typeof obj[3] === 'object' && obj[3] !== null) {
          const subh = document.createElement('div');
          subh.className = 'entry status';
          subh.textContent = 'Payload fields';
          detail.appendChild(subh);

          const ptbl = document.createElement('table');
          const pthead = document.createElement('thead');
          pthead.innerHTML = '<tr><th>Key</th><th>Value</th></tr>';
          ptbl.appendChild(pthead);
          const ptbody = document.createElement('tbody');
          Object.entries(obj[3]).forEach(([k,v]) => {
            const pr = document.createElement('tr');
            const pk = document.createElement('td'); pk.textContent = k;
            const pv = document.createElement('td'); pv.textContent = String(v);
            pr.appendChild(pk); pr.appendChild(pv);
            ptbody.appendChild(pr);
          });
          ptbl.appendChild(ptbody);
          detail.appendChild(ptbl);
        }
      }
      // If object: generic key/value table
      else if (typeof obj === 'object' && obj !== null) {
        const tbl = document.createElement('table');
        const thead = document.createElement('thead');
        thead.innerHTML = '<tr><th>Key</th><th>Value</th></tr>';
        tbl.appendChild(thead);
        const tbody = document.createElement('tbody');
        Object.entries(obj).forEach(([k,v]) => {
          const tr = document.createElement('tr');
          const kd = document.createElement('td'); kd.textContent = k;
          const vd = document.createElement('td'); vd.textContent = String(v);
          tr.appendChild(kd); tr.appendChild(vd);
          tbody.appendChild(tr);
        });
        tbl.appendChild(tbody);
        detail.appendChild(tbl);
      }
    }

    // WebSocket
    let ws;
    function connect(){
      appendLog(`Connecting to ${url}`, 'status');
      ws = new WebSocket(url);

      ws.onopen = () => appendLog('Connected','status');
      ws.onmessage = ev => {
        appendLog(ev.data);
        showDetail(ev.data);
      };
      ws.onclose = () => {
        appendLog('Connection closed; retrying in 3s…','status');
        setTimeout(connect,3000);
      };
      ws.onerror = err => {
        console.error('WS error', err);
        appendLog('WebSocket error (see console)','status');
      };
    }
    connect();
  })();
  </script>
</body>
</html>
