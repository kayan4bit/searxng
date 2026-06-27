#!/usr/bin/env python3
"""SearXNG - Clean UI + AI Panel + Privacy Button."""
import os, re
base = "/usr/local/searxng/searx/templates/simple/base.html"
html = '''<style>
.sxng-ai-wrap{position:fixed;bottom:24px;right:24px;z-index:1000001!important}
.sxng-ai-btn{background:linear-gradient(135deg,#10b981,#059669)!important;color:#fff!important;border:none!important;padding:16px 20px!important;border-radius:50px!important;cursor:pointer!important;font-size:14px!important;font-weight:700!important;box-shadow:0 4px 25px rgba(16,185,129,.5)!important;display:flex!important;align-items:center!important;gap:8px!important;font-family:system-ui!important;z-index:99999!important;pointer-events:auto!important}
.sxng-ai-btn:hover{transform:scale(1.08)!important;box-shadow:0 6px 30px rgba(16,185,129,.6)!important}
.sxng-pv-wrap{position:fixed;bottom:24px;left:24px;z-index:1000001!important}
.sxng-pv-btn{background:linear-gradient(135deg,#6366f1,#4f46e5)!important;color:#fff!important;border:none!important;padding:14px 18px!important;border-radius:50px!important;cursor:pointer!important;font-size:13px!important;font-weight:700!important;box-shadow:0 4px 20px rgba(99,102,241,.4)!important;font-family:system-ui!important;display:flex!important;align-items:center!important;gap:6px!important;z-index:1000001!important;pointer-events:auto!important}
.sxng-pv-btn:hover{transform:scale(1.08)!important;box-shadow:0 6px 25px rgba(99,102,241,.5)!important}
.sxng-pv-dot{width:10px;height:10px;background:#10b981;border-radius:50%;animation:sxngPulse 2s infinite;flex-shrink:0}
@keyframes sxngPulse{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.5;transform:scale(.8)}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.sxng-panel{position:fixed;top:0;right:-420px;width:400px;height:100vh;background:#fff;z-index:100000;box-shadow:-4px 0 50px rgba(0,0,0,.3);transition:right .3s ease;display:flex;flex-direction:column;font-family:system-ui}
.sxng-panel.open{right:0}
.sxng-phdr{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;background:linear-gradient(135deg,#10b981,#059669);color:#fff}
.sxng-phdr h3{margin:0;font-size:15px;font-weight:600}
.sxng-close{background:rgba(255,255,255,.2);border:none;color:#fff;font-size:20px;cursor:pointer;padding:6px 12px;border-radius:6px}
.sxng-close:hover{background:rgba(255,255,255,.3)}
.sxng-pbody{flex:1;overflow-y:auto;padding:16px 20px}
.sxng-sbtn{width:100%;padding:14px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;border-radius:10px;cursor:pointer;font-size:13px;font-weight:600;margin-bottom:16px;box-shadow:0 2px 10px rgba(16,185,129,.3)}
.sxng-sbtn:hover{transform:translateY(-1px);box-shadow:0 4px 15px rgba(16,185,129,.4)}
.sxng-sum{background:linear-gradient(135deg,#ecfdf5,#d1fae5);border-radius:10px;padding:14px;margin-bottom:16px;font-size:13px;line-height:1.6;border-left:4px solid #10b981;display:none}
.sxng-sum.show{display:block}
.sxng-msg{padding:12px 14px;border-radius:10px;margin-bottom:10px;font-size:13px;max-width:90%;line-height:1.5}
.sxng-msg.user{background:#f3f4f6;margin-left:auto;text-align:right}
.sxng-msg.ai{background:#ecfdf5}
.sxng-msg.err{background:#fee2e2;color:#991b1b}
.sxng-msg.ld{color:#666;font-style:italic;background:none}
.sxng-typing span{width:8px;height:8px;background:#10b981;border-radius:50%;display:inline-block;animation:ty 1s infinite}
.sxng-typing span:nth-child(2){animation-delay:.2s}
.sxng-typing span:nth-child(3){animation-delay:.4s}
@keyframes ty{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}
.sxng-pfoot{display:flex;gap:10px;padding:16px 20px;border-top:1px solid #e5e7eb;background:#fafafa}
.sxng-pfoot input{flex:1;padding:12px 14px;border:2px solid #e5e7eb;border-radius:10px;font-size:13px}
.sxng-pfoot input:focus{outline:none;border-color:#10b981}
.sxng-pfoot button{background:#10b981;color:#fff;border:none;padding:12px 18px;border-radius:10px;cursor:pointer;font-size:16px}
.sxng-pfoot button:hover{background:#059669}
.sxng-ov{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:99999}
.sxng-ov.show{display:block}
.sxng-pv-panel{position:fixed;top:0;left:-350px;width:340px;height:100vh;background:#fff;z-index:100000;box-shadow:4px 0 50px rgba(0,0,0,.3);transition:left .3s ease;display:flex;flex-direction:column;font-family:system-ui}
.sxng-pv-panel.open{left:0}
.sxng-pv-hdr{display:flex;align-items:center;justify-content:space-between;padding:16px 20px;background:linear-gradient(135deg,#6366f1,#4f46e5);color:#fff}
.sxng-pv-hdr h3{margin:0;font-size:15px;font-weight:600}
.sxng-pv-body{padding:20px;flex:1;overflow-y:auto}
.sxng-pv-stat{margin-bottom:20px}
.sxng-pv-stat h4{margin:0 0 12px;font-size:14px;color:#374151}
.sxng-pv-item{display:flex;align-items:center;justify-content:space-between;padding:10px 12px;background:#f3f4f6;border-radius:8px;margin-bottom:8px;font-size:13px}
.sxng-pv-item span{color:#059669;font-weight:600}
.sxng-pv-api{background:#f0fdf4;border:2px solid #10b981;border-radius:10px;padding:16px;margin-top:20px}
.sxng-pv-api h4{margin:0 0 10px;font-size:14px;color:#166534}
.sxng-pv-api pre{background:#fff;padding:10px;border-radius:6px;font-size:11px;overflow-x:auto;margin:0;word-break:break-all}
.sxng-pv-copy{background:#10b981;color:#fff;border:none;padding:8px 16px;border-radius:6px;cursor:pointer;font-size:12px;margin-top:10px;width:100%}
.sxng-pv-copy:hover{background:#059669}
.sxng-node-reg{background:linear-gradient(135deg,#fef3c7,#fde68a);border:2px solid #f59e0b;border-radius:12px;padding:16px;margin-top:20px}
.sxng-node-reg h4{margin:0 0 12px;font-size:14px;color:#92400e;font-weight:600}
.sxng-node-reg input{width:100%;padding:10px;border:2px solid #f59e0b;border-radius:8px;font-size:13px;margin-bottom:8px;box-sizing:border-box}
.sxng-node-reg input:focus{outline:none;border-color:#d97706}
.sxng-node-reg button{width:100%;padding:12px;background:linear-gradient(135deg,#f59e0b,#d97706);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600;margin-top:8px}
.sxng-node-reg button:hover{transform:scale(1.02)}
.sxng-node-reg .perks{font-size:11px;color:#78350f;margin-top:10px;padding:8px;background:#fff;border-radius:6px}
.sxng-node-status{font-size:12px;color:#065f46;padding:8px;background:#d1fae5;border-radius:6px;margin-top:8px;display:none}
.sxng-node-logged{background:#d1fae5;border:2px solid #10b981;border-radius:12px;padding:16px;margin-top:20px}
.sxng-node-logged h4{margin:0 0 8px;font-size:14px;color:#065f46}
.sxng-node-logged .key{display:flex;align-items:center;gap:8px;padding:8px;background:#fff;border-radius:6px;margin-bottom:8px}
.sxng-node-logged .key code{flex:1;font-size:11px;word-break:break-all;color:#6b7280}
.sxng-node-logged .heartbeat{font-size:11px;color:#059669;padding:6px;background:#ecfdf5;border-radius:4px;text-align:center}
@media(max-width:480px){
.sxng-ai-wrap,.sxng-pv-wrap{bottom:15px}
.sxng-ai-wrap{right:15px}
.sxng-pv-wrap{left:15px}
.sxng-ai-btn,.sxng-pv-btn{padding:10px 14px;font-size:11px}
.sxng-panel,.sxng-pv-panel{width:100vw;right:-100%;left:-100%}
.sxng-panel.open,.sxng-pv-panel.open{right:0;left:0}
}</style>
<div class="sxng-ov" id="sxngOv" onclick="sxngClose()"></div>
<div class="sxng-pv-panel" id="sxngPvPanel">
<div class="sxng-pv-hdr"><h3>Privacy & Security</h3><button class="sxng-close" onclick="sxngPvClose()">X</button></div>
<div class="sxng-pv-body">
<div class="sxng-pv-stat">
<h4>Privacy Mode</h4>
<div class="sxng-mode">
<button class="sxng-mode-btn fast" id="mode-fast" onclick="sxngSetMode('fast')"><div><strong>Speed</strong><small>Fast, some tracking blocked</small></div><span>⚡ Fast</span></button>
<button class="sxng-mode-btn" id="mode-balanced" onclick="sxngSetMode('balanced')"><div><strong>Balanced</strong><small>Good privacy + E2EE</small></div><span>🛡 Good</span></button>
<button class="sxng-mode-btn max" id="mode-max" onclick="sxngSetMode('max')"><div><strong>Maximum</strong><small>Full E2EE + IP spoofing</small></div><span>🔒 Max</span></button>
</div>
</div>
<div class="sxng-pv-stat">
<h4>Security Status</h4>
<div class="sxng-pv-item">E2EE <span id="sxngE2ee">AES-256-GCM</span></div>
<div class="sxng-pv-item">CSP Nonce <span>Per Request</span></div>
<div class="sxng-pv-item">Trackers Blocked <span>60+</span></div>
<div class="sxng-pv-item">Zero Logs <span>Enabled</span></div>
<div class="sxng-pv-item">IP Spoofing <span id="sxngIp">Off</span></div>
</div>
<div class="sxng-pv-api" id="sxngPvApi">
<h4>Zero-Config API</h4>
<pre id="sxngPvKey">Loading...</pre>
<button class="sxng-pv-copy" onclick="sxngPvCopy()">Copy API Key</button>
</div>
<div class="sxng-node-reg" id="sxngNodeReg">
<h4>🖥️ Become a Node Operator</h4>
<input type="text" id="sxngNodeEmail" placeholder="Your email">
<input type="text" id="sxngNodeName" placeholder="Node name">
<button onclick="sxngRegisterNode()">Register as Node</button>
<div class="perks">🎁 Perks: Faster searches, Beta features, Privacy dashboard</div>
<div class="sxng-node-status" id="sxngNodeStatus"></div>
</div>
<div class="sxng-node-logged" id="sxngNodeLogged" style="display:none">
<h4>🟢 Node Registered</h4>
<div class="key"><code id="sxngNodeKey">---</code></div>
<div class="heartbeat" id="sxngHeartbeat">❤️ Sending heartbeat...</div>
</div>
</div>
</div>
<div class="sxng-panel" id="sxngPanel">
<div class="sxng-phdr"><h3>AI Assistant</h3><button class="sxng-close" onclick="sxngClose()">X</button></div>
<div class="sxng-pbody">
<button class="sxng-sbtn" onclick="sxngSum()">Summary</button>
<div class="sxng-sum" id="sxngSum"></div>
<div id="sxngMsgs"></div>
</div>
<div class="sxng-pfoot">
<input type="text" id="sxngInp" placeholder="Ask AI..." onkeypress="if(event.key===13)sxngSend()">
<button onclick="sxngSend()">></button>
</div>
</div>
<div class="sxng-ai-wrap">
<button class="sxng-ai-btn" onclick="sxngOpen()">AI</button>
</div>
<div class="sxng-pv-wrap">
<button class="sxng-pv-btn" onclick="sxngPvOpen()"><span class="sxng-pv-dot"></span>Privacy</button>
</div>
<script>
(function(){
var h=[];
function sxngOpen(){document.getElementById("sxngPanel").classList.add("open");document.getElementById("sxngOv").classList.add("show");document.body.style.overflow="hidden";document.getElementById("sxngInp").focus()}
function sxngClose(){document.getElementById("sxngPanel").classList.remove("open");document.getElementById("sxngOv").classList.remove("show");document.body.style.overflow=""}
function sxngPvOpen(){document.getElementById("sxngPvPanel").classList.add("open");document.getElementById("sxngOv").classList.add("show");document.body.style.overflow="hidden";if(document.getElementById("sxngPvKey").textContent==="Loading..."){fetch("/api/zero-config").then(r=>r.json()).then(function(d){document.getElementById("sxngPvKey").textContent=JSON.stringify(d,null,2)})}}
function sxngPvClose(){document.getElementById("sxngPvPanel").classList.remove("open");document.getElementById("sxngOv").classList.remove("show");document.body.style.overflow=""}
function sxngPvCopy(){navigator.clipboard.writeText(document.getElementById("sxngPvKey").textContent);alert("Copied!")}
function sxngTyp(){var d=document.createElement("div");d.className="sxng-msg ai ld";d.innerHTML='<span class="sxng-typing"><span></span><span></span><span></span></span>';document.getElementById("sxngMsgs").appendChild(d);return d}
function sxngSum(){var q=document.querySelector("input[name=q]")?.value||"";var e=document.getElementById("sxngSum");if(!q){e.innerHTML="Search something first!";e.classList.add("show");return}e.innerHTML="Loading...";e.classList.add("show");fetch("/api/summary",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:q})}).then(r=>r.json()).then(function(d){e.innerHTML=(d.summary||"No summary").replace(/\\n/g,"<br>")}).catch(function(){e.innerHTML="Error loading summary"})}
function sxngSend(){var i=document.getElementById("sxngInp");var m=i.value.trim();if(!m)return;h.push({role:"user",content:m});i.value="";var t=sxngTyp();fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:m})}).then(r=>r.json()).then(function(d){t.classList.remove("ld");t.classList.add("ai");t.innerHTML=(d.response||"No response").replace(/\\n/g,"<br>");h.push({role:"ai",content:d.response})}).catch(function(){t.classList.remove("ld");t.classList.add("err");t.innerHTML="Error"})}
window.sxngOpen=sxngOpen;window.sxngClose=sxngClose;window.sxngPvOpen=sxngPvOpen;window.sxngPvClose=sxngPvClose;
window.sxngRegisterNode=function(){var e=document.getElementById("sxngNodeEmail").value;var n=document.getElementById("sxngNodeName").value;var s=document.getElementById("sxngNodeStatus");if(!e||!n){if(s)s.style.display="block",s.textContent="Fill all fields";return}if(s)s.style.display="block",s.textContent="Registering...";fetch("/api/node/register",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({email:e,name:n})}).then(function(r){return r.json()}).then(function(d){if(d.node_id){localStorage.setItem("node_key",d.node_id);document.getElementById("sxngNodeReg").style.display="none";var l=document.getElementById("sxngNodeLogged");l.style.display="block";document.getElementById("sxngNodeKey").textContent=d.node_id;startHeartbeat(d.node_id)}else{if(s)s.textContent=d.error||"Error"}}).catch(function(){if(s)s.textContent="Connection error"})};
function startHeartbeat(key){setInterval(function(){fetch("/api/node/heartbeat",{method:"POST",headers:{"X-Session-Token":key}}).then(function(r){return r.json()}).then(function(d){var h=document.getElementById("sxngHeartbeat");if(h)h.textContent="❤️ Heartbeat: "+(d.alive?"Active":"Inactive")}).catch(function(){var h=document.getElementById("sxngHeartbeat");if(h)h.textContent="❤️ Offline"})},30000)}
var savedKey=localStorage.getItem("node_key");if(savedKey){document.getElementById("sxngNodeReg").style.display="none";var l=document.getElementById("sxngNodeLogged");l.style.display="block";document.getElementById("sxngNodeKey").textContent=savedKey;startHeartbeat(savedKey)}
})();
</script>'''
if os.path.exists(base):
    with open(base) as f: c=f.read()
    for p in ['atomic-privacy','atomic-ai-btn','atomic-ai-panel','searxng-ai-btn','searxng-ai-panel','atomic-ai-overlay','searxng-ai-overlay','sxng-ai-wrap','sxng-panel','sxng-ov']:
        c=re.sub(r'<style[^>]*>.*?'+p+r'.*?</style>','',c,flags=re.DOTALL)
        c=re.sub(r'<div[^>]*class="[^"]*'+p+r'[^"]*"[^>]*>.*?</div>','',c,flags=re.DOTALL)
        c=re.sub(r'<script[^>]*>.*?'+p+r'.*?</script>','',c,flags=re.DOTALL)
    c+=html
    with open(base,"w") as f: f.write(c)
    print("UI Patched!")
else: print("Not found")
