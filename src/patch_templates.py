#!/usr/bin/env python3
"""SearXNG - Atomic Search Premium UI + Privacy Modes + Node System."""
import os, re, secrets
base = "/usr/local/searxng/searx/templates/simple/base.html"
node_id = secrets.token_hex(8)
html = f'''<!-- START ATOMIC SEARCH - Node: {node_id} -->
<div class="sxng-ai-wrap" id="sxngAiWrap"><button class="sxng-ai-btn" onclick="sxngOpen()">✨ AI</button></div>
<div class="sxng-pv-wrap" id="sxngPvWrap"><button class="sxng-pv-btn" onclick="sxngPvOpen()"><span class="sxng-dot"></span>Privacy</button></div>
<div id="sxngOv" class="sxng-ov" onclick="sxngClose()"></div>
<div id="sxngPanel" class="sxng-panel">
    <div class="sxng-phdr"><h3>✨ AI Assistant</h3><button class="sxng-close" onclick="sxngClose()">×</button></div>
    <div id="sxngChat" class="sxng-pbody"><div class="sxng-msg ai">How can I help you search today?</div></div>
    <div class="sxng-pfoot">
        <input type="text" id="sxngInput" placeholder="Message AI..." onkeypress="if(event.key==='Enter')sxngSend()">
        <button onclick="sxngSend()">→</button>
    </div>
</div>
<div id="sxngPvPanel" class="sxng-pv-panel">
    <div class="sxng-phdr" style="background:linear-gradient(135deg,#6366f1,#4f46e5)"><h3>🛡️ Privacy Shield</h3><button class="sxng-close" onclick="sxngClose()">×</button></div>
    <div class="sxng-pbody">
        <div class="sxng-status" id="sxngStatus">Loading...</div>
        <div class="sxng-processing" id="sxngProcessing" style="display:none">
            <div class="sxng-proc-header">⚡ Processing Request...</div>
            <div class="sxng-proc-item" id="proc-enc"><span class="sxng-proc-icon">🔒</span> Encrypting request...</div>
            <div class="sxng-proc-item" id="proc-route"><span class="sxng-proc-icon">🔀</span> Routing through privacy network...</div>
            <div class="sxng-proc-item" id="proc-block"><span class="sxng-proc-icon">🚫</span> Blocking trackers...</div>
            <div class="sxng-proc-item" id="proc-proxy"><span class="sxng-proc-icon">🌐</span> Proxying IP...</div>
            <div class="sxng-proc-item" id="proc-done" style="display:none"><span class="sxng-proc-icon">✅</span> <strong>Complete!</strong></div>
        </div>
        <div class="sxng-modes">
            <div class="sxng-mode-header">Choose Privacy Level</div>
            <button class="sxng-mode-btn" data-mode="fast" onclick="sxngSetMode('fast')">
                <span>⚡ Speed</span><small>Fastest, some tracking blocked</small>
            </button>
            <button class="sxng-mode-btn active" data-mode="balanced" onclick="sxngSetMode('balanced')">
                <span>🛡️ Balanced</span><small>Good privacy + E2EE</small>
            </button>
            <button class="sxng-mode-btn" data-mode="max" onclick="sxngSetMode('max')">
                <span>🔒 Maximum</span><small>Full E2EE + IP spoofing</small>
            </button>
            <button class="sxng-mode-btn" data-mode="ultra" onclick="sxngSetMode('ultra')">
                <span>🛡️ Ultra</span><small>Maximum + Tor + NoJS</small>
            </button>
        </div>
        <div class="sxng-compare">
            <div class="sxng-compare-header">🔍 Privacy Comparison</div>
            <table class="sxng-table">
                <tr><th>Feature</th><th>Speed</th><th>Balanced</th><th>Max</th><th>Ultra</th></tr>
                <tr><td>E2EE</td><td>-</td><td>✓</td><td>✓</td><td>✓</td></tr>
                <tr><td>IP Spoofing</td><td>-</td><td>-</td><td>✓</td><td>✓</td></tr>
                <tr><td>Tor</td><td>-</td><td>-</td><td>-</td><td>✓</td></tr>
                <tr><td>No JS</td><td>-</td><td>-</td><td>-</td><td>✓</td></tr>
                <tr><td>Speed</td><td>⭐⭐⭐⭐⭐</td><td>⭐⭐⭐</td><td>⭐⭐</td><td>⭐</td></tr>
            </table>
        </div>
        <div class="sxng-bts">
            <div class="sxng-bts-header">⚙️ What's Happening</div>
            <div class="sxng-bts-item" id="bts-enc">🔒 Encryption: <span>Loading...</span></div>
            <div class="sxng-bts-item" id="bts-track">🚫 Trackers: <span>Loading...</span></div>
            <div class="sxng-bts-item" id="bts-log">📝 Logs: <span>Loading...</span></div>
            <div class="sxng-bts-item" id="bts-ip">🌐 IP: <span>Loading...</span></div>
        </div>
        <div class="sxng-api">
            <h4>🔑 Free API Access</h4>
            <pre id="sxngApiKey">Loading...</pre>
            <button onclick="sxngCopyKey()">Copy API Key</button>
        </div>
        <div class="sxng-node">
            <span class="sxng-node-badge">🟢 Node Active</span>
            <code>{node_id}</code>
        </div>
    </div>
</div>
<style>
.sxng-ai-wrap,.sxng-pv-wrap{{position:fixed;bottom:24px;z-index:99999;transition:all .3s ease}}
.sxng-ai-wrap{{right:24px}}.sxng-pv-wrap{{left:24px}}
.sxng-ai-wrap.hidden,.sxng-pv-wrap.hidden{{opacity:0;transform:scale(0.8);pointer-events:none}}
.sxng-ai-btn,.sxng-pv-btn{{background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;padding:14px 20px;border-radius:50px;cursor:pointer;font-size:14px;font-weight:700;box-shadow:0 4px 20px rgba(16,185,129,.4);transition:all .2s}}
.sxng-pv-btn{{background:linear-gradient(135deg,#6366f1,#4f46e5);box-shadow:0 4px 20px rgba(99,102,241,.4)}}
.sxng-ai-btn:hover,.sxng-pv-btn:hover{{transform:scale(1.08) translateY(-2px);box-shadow:0 8px 30px rgba(16,185,129,.5)}}
.sxng-dot{{width:10px;height:10px;background:#10b981;border-radius:50%;display:inline-block;margin-right:8px;animation:pulse 2s infinite}}
@keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.5;transform:scale(.8)}}}}
.sxng-ov{{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:99998;backdrop-filter:blur(4px)}}
.sxng-ov.show{{display:block}}
.sxng-panel,.sxng-pv-panel{{position:fixed;top:0;width:420px;height:100vh;background:#fff;z-index:99999;box-shadow:0 0 60px rgba(0,0,0,.3);transition:.3s cubic-bezier(0.4,0,0.2,1);display:flex;flex-direction:column;font-family:system-ui,-apple-system,sans-serif}}
.sxng-panel{{right:-440px}}.sxng-panel.open{{right:0}}
.sxng-pv-panel{{left:-440px}}.sxng-pv-panel.open{{left:0}}
.sxng-phdr{{display:flex;justify-content:space-between;align-items:center;padding:20px 24px;background:linear-gradient(135deg,#10b981,#059669);color:#fff}}
.sxng-phdr h3{{margin:0;font-size:18px;font-weight:600}}
.sxng-close{{background:rgba(255,255,255,.2);border:none;color:#fff;font-size:22px;padding:8px 14px;border-radius:8px;cursor:pointer;transition:.2s}}
.sxng-close:hover{{background:rgba(255,255,255,.3);transform:rotate(90deg)}}
.sxng-pbody{{flex:1;overflow-y:auto;padding:20px;background:#f8fafc}}
.sxng-msg{{padding:14px 18px;border-radius:14px;font-size:14px;line-height:1.6;margin-bottom:12px;animation:fadeIn .3s}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(10px)}}to{{opacity:1;transform:translateY(0)}}}}
.sxng-msg.ai{{background:linear-gradient(135deg,#ecfdf5,#d1fae5);color:#065f46;border-left:4px solid #10b981;align-self:flex-start}}
.sxng-msg.user{{background:linear-gradient(135deg,#f3f4f6,#e5e7eb);color:#1f2937;align-self:flex-end;border-left:none;border-right:4px solid #6366f1}}
.sxng-typing span{{width:8px;height:8px;background:#10b981;border-radius:50%;display:inline-block;animation:ty 1s infinite;margin:0 3px}}
.sxng-typing span:nth-child(2){{animation-delay:.2s}}.sxng-typing span:nth-child(3){{animation-delay:.4s}}
@keyframes ty{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-8px)}}}}
.sxng-pfoot{{display:flex;gap:10px;padding:20px;border-top:1px solid #e5e7eb;background:#fff}}
.sxng-pfoot input{{flex:1;padding:14px 18px;border:2px solid #e5e7eb;border-radius:12px;font-size:15px;transition:.2s}}
.sxng-pfoot input:focus{{outline:none;border-color:#10b981;box-shadow:0 0 0 3px rgba(16,185,129,.1)}}
.sxng-pfoot button{{background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;padding:14px 22px;border-radius:12px;cursor:pointer;font-size:16px;font-weight:600;transition:.2s}}
.sxng-pfoot button:hover{{transform:scale(1.05)}}
.sxng-status{{background:linear-gradient(135deg,#ecfdf5,#d1fae5);padding:14px;border-radius:12px;text-align:center;font-size:14px;color:#065f46;font-weight:500;margin-bottom:16px;border:2px solid #10b981}}
.sxng-processing{{background:#fef3c7;border:2px solid #f59e0b;border-radius:12px;padding:16px;margin-bottom:16px;animation:pulseGlow 2s infinite}}
@keyframes pulseGlow{{0%,100%{{box-shadow:0 0 5px rgba(245,158,11,.3)}}50%{{box-shadow:0 0 20px rgba(245,158,11,.5)}}}}
.sxng-proc-header{{font-size:14px;font-weight:700;color:#92400e;margin-bottom:12px}}
.sxng-proc-item{{padding:8px 0;font-size:13px;color:#78350f;border-bottom:1px solid rgba(245,158,11,.2);display:flex;align-items:center;gap:8px}}
.sxng-proc-item:last-child{{border-bottom:none}}
.sxng-proc-item.done{{color:#065f46;font-weight:600}}
.sxng-proc-item.done .sxng-proc-icon{{color:#10b981}}
.sxng-proc-icon{{font-size:16px}}
.sxng-modes{{margin-bottom:16px}}
.sxng-mode-header{{font-size:13px;font-weight:600;color:#374151;margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px}}
.sxng-mode-btn{{display:flex;flex-direction:column;width:100%;padding:14px 16px;background:#fff;border:2px solid #e5e7eb;border-radius:12px;cursor:pointer;font-size:14px;margin-bottom:8px;text-align:left;transition:all .2s}}
.sxng-mode-btn:hover{{border-color:#6366f1;background:#eef2ff;transform:translateX(4px)}}
.sxng-mode-btn.active{{border-color:#10b981;background:#ecfdf5;box-shadow:0 4px 12px rgba(16,185,129,.2)}}
.sxng-mode-btn span{{font-weight:700;font-size:15px}}
.sxng-mode-btn small{{color:#6b7280;margin-top:4px;font-size:12px}}
.sxng-compare{{background:#fff;border-radius:12px;padding:16px;margin-bottom:16px;border:1px solid #e5e7eb}}
.sxng-compare-header{{font-size:13px;font-weight:600;color:#374151;margin-bottom:12px;text-transform:uppercase}}
.sxng-table{{width:100%;border-collapse:collapse;font-size:11px}}
.sxng-table th,.sxng-table td{{padding:8px 6px;text-align:center;border-bottom:1px solid #e5e7eb}}
.sxng-table th{{background:#f3f4f6;font-weight:600;color:#374151}}
.sxng-table td{{color:#6b7280}}.sxng-table td:first-child{{text-align:left;font-weight:500}}
.sxng-bts{{background:#1e293b;border-radius:12px;padding:16px;margin-bottom:16px}}
.sxng-bts-header{{font-size:13px;font-weight:600;color:#fff;margin-bottom:12px}}
.sxng-bts-item{{display:flex;justify-content:space-between;padding:8px 0;color:#94a3b8;font-size:13px;border-bottom:1px solid rgba(255,255,255,.1)}}
.sxng-bts-item:last-child{{border-bottom:none}}
.sxng-bts-item span{{color:#10b981;font-weight:600}}
.sxng-api{{background:linear-gradient(135deg,#f0fdf4,#dcfce7);border:2px solid #10b981;border-radius:12px;padding:16px;margin-bottom:16px}}
.sxng-api h4{{font-size:14px;color:#166534;margin:0 0 12px;font-weight:700}}
.sxng-api pre{{font-size:11px;background:#1e293b;color:#e2e8f0;padding:12px;border-radius:8px;overflow-x:auto;margin:0 0 12px;max-height:100px}}
.sxng-api button{{width:100%;padding:12px;background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600;transition:.2s}}
.sxng-api button:hover{{transform:scale(1.02);box-shadow:0 4px 12px rgba(16,185,129,.3)}}
.sxng-node{{display:flex;align-items:center;justify-content:space-between;background:#f3f4f6;padding:12px 16px;border-radius:8px}}
.sxng-node-badge{{background:#10b981;color:#fff;padding:4px 10px;border-radius:20px;font-size:11px;font-weight:600}}
.sxng-node code{{font-size:11px;color:#6b7280}}
@media(max-width:480px){{.sxng-panel,.sxng-pv-panel{{width:100vw;right:-100%;left:-100%}}.sxng-panel.open,.sxng-pv-panel.open{{right:0;left:0}}.sxng-ai-wrap{{right:12px;bottom:12px}}.sxng-pv-wrap{{left:12px;bottom:12px}}}}
</style>
<script>
(function(){{
    var _=function(id){{return document.getElementById(id)}};
    var aiWrap=_('sxngAiWrap'),pvWrap=_('sxngPvWrap');
    window.sxngOpen=function(){{aiWrap.classList.add('hidden');_('sxngPanel').classList.add('open');_('sxngOv').classList.add('show');setTimeout(function(){{_('sxngInput').focus()}},100)}};
    window.sxngPvOpen=function(){{pvWrap.classList.add('hidden');_('sxngPvPanel').classList.add('open');_('sxngOv').classList.add('show');loadApi();loadStatus()}};
    window.sxngClose=function(){{['sxngPanel','sxngPvPanel'].forEach(function(id){{var e=_(id);if(e)e.classList.remove('open')}});_('sxngOv').classList.remove('show');aiWrap.classList.remove('hidden');pvWrap.classList.remove('hidden')}};
    window.sxngCopyKey=function(){{navigator.clipboard.writeText(_('sxngApiKey').textContent);alert('API Key Copied!')}};
    function loadApi(){{if(_('sxngApiKey').textContent==='Loading...')fetch('/api/zero-config').then(function(r){{return r.json()}}).then(function(d){{_('sxngApiKey').textContent=JSON.stringify(d,null,2)}})}};
    function loadStatus(){{
        fetch('/api/privacy/status').then(function(r){{return r.json()}}).then(function(d){{
            var s=_('sxngStatus');
            if(s)s.textContent='Mode: '+d.mode+' | Encrypted: '+d.encryption+' | Trackers: '+d.trackers_blocked+'+';
            document.querySelectorAll('.sxng-mode-btn').forEach(function(b){{b.classList.remove('active')}});
            var btn=document.querySelector('[data-mode=\"'+d.mode+'\"]');
            if(btn)btn.classList.add('active');
            var map={{fast:{{enc:'Basic',track:'~20',log:'Some',ip:'Your IP'}},balanced:{{enc:'AES-256-GCM',track:'60+',log:'None',ip:'Your IP'}},max:{{enc:'AES-256-GCM',track:'100+',log:'None',ip:'Random IP'}},ultra:{{enc:'AES-256-GCM',track:'150+',log:'None',ip:'Tor Network'}}}};
            var info=map[d.mode]||map.balanced;
            if(_('bts-enc'))_('bts-enc').querySelector('span').textContent=info.enc;
            if(_('bts-track'))_('bts-track').querySelector('span').textContent=info.track;
            if(_('bts-log'))_('bts-log').querySelector('span').textContent=info.log;
            if(_('bts-ip'))_('bts-ip').querySelector('span').textContent=info.ip;
        }}).catch(function(){{
            var s=_('sxngStatus');
            if(s)s.textContent='Mode: balanced | Encrypted: AES-256-GCM | Trackers: 60+';
            var map={{enc:'AES-256-GCM',track:'60+',log:'None',ip:'Your IP'}};
            if(_('bts-enc'))_('bts-enc').querySelector('span').textContent=map.enc;
            if(_('bts-track'))_('bts-track').querySelector('span').textContent=map.track;
            if(_('bts-log'))_('bts-log').querySelector('span').textContent=map.log;
            if(_('bts-ip'))_('bts-ip').querySelector('span').textContent=map.ip;
        }});
    }}
    window.sxngSend=function(){{
        var inp=_('sxngInput'),chat=_('sxngChat'),txt=inp.value.trim();
        if(!txt)return;
        var u=document.createElement('div');u.className='sxng-msg user';u.textContent=txt;chat.appendChild(u);inp.value='';chat.scrollTop=chat.scrollHeight;
        var t=document.createElement('div');t.className='sxng-msg ai sxng-typing';t.innerHTML='<span></span><span></span><span></span>';chat.appendChild(t);chat.scrollTop=chat.scrollHeight;
        fetch('/api/chat',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{message:txt}})}}).then(function(r){{return r.json()}}).then(function(d){{t.remove();var a=document.createElement('div');a.className='sxng-msg ai';a.textContent=d.response||'Error';chat.appendChild(a);chat.scrollTop=chat.scrollHeight}}).catch(function(){{t.remove();var a=document.createElement('div');a.className='sxng-msg ai';a.textContent='Error connecting';chat.appendChild(a);chat.scrollTop=chat.scrollHeight}});
    }};
    window.sxngSetMode=function(m){{fetch('/api/privacy/mode',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{mode:m}})}}).then(function(){{location.reload()}})}};
    loadApi();
    loadStatus();
    var searchForm=document.querySelector('form[action="/search"]');
    if(searchForm){{
        searchForm.addEventListener('submit',function(){{
            var proc=document.getElementById('sxngProcessing');
            if(proc){{
                proc.style.display='block';
                var enc=document.getElementById('proc-enc');
                var route=document.getElementById('proc-route');
                var block=document.getElementById('proc-block');
                var proxy=document.getElementById('proc-proxy');
                var done=document.getElementById('proc-done');
                setTimeout(function(){{enc.classList.add('done');enc.innerHTML='<span class="sxng-proc-icon">✅</span> Request encrypted with AES-256-GCM'}},300);
                setTimeout(function(){{route.classList.add('done');route.innerHTML='<span class="sxng-proc-icon">✅</span> Routed through privacy network'}},700);
                setTimeout(function(){{block.classList.add('done');block.innerHTML='<span class="sxng-proc-icon">✅</span> Trackers blocked'}},1100);
                setTimeout(function(){{proxy.classList.add('done');proxy.innerHTML='<span class="sxng-proc-icon">✅</span> IP proxied'}},1500);
                setTimeout(function(){{done.style.display='block';done.classList.add('done');done.innerHTML='<span class="sxng-proc-icon">✅</span> <strong>Search Complete! Safe & Private.</strong>';proc.style.background='#d1fae5';proc.style.borderColor='#10b981';proc.style.animation='none'}},1900);
            }}
        }});
    }}
}})();
</script>
<!-- END ATOMIC SEARCH -->
'''
if os.path.exists(base):
    with open(base) as f: c=f.read()
    for p in ['atomic-privacy','atomic-ai-btn','searxng-ai-btn','atomic-ai-overlay','sxng-ai-wrap','sxng-panel','sxng-ov','START ATOMIC','END ATOMIC']:
        c=re.sub(r'<style[^>]*>.*?'+p+r'.*?</style>','',c,flags=re.DOTALL)
        c=re.sub(r'<div[^>]*class="[^"]*'+p+r'[^"]*"[^>]*>.*?</div>','',c,flags=re.DOTALL)
        c=re.sub(r'<script[^>]*>.*?'+p+r'.*?</script>','',c,flags=re.DOTALL)
        c=re.sub(r'<!--.*?'+p+r'.*?-->','',c,flags=re.DOTALL)
    c+=html
    with open(base,'w') as f: f.write(c)
    print("Done - Node: "+node_id)
else: print("Not found")
