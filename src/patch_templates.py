#!/usr/bin/env python3
"""SearXNG - Clean Mobile-Optimized UI + Zero-Config API."""
import os, re
base = "/usr/local/searxng/searx/templates/simple/base.html"
html = '''<style>
.searxng-ai-btn{position:fixed;bottom:20px;right:20px;z-index:9999}
.searxng-ai-btn button{background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;padding:12px 16px;border-radius:50px;cursor:pointer;font-size:12px;font-weight:600;box-shadow:0 4px 20px rgba(16,185,129,.4);font-family:system-ui}
.searxng-ai-panel{position:fixed;top:0;right:-100%;width:100%;max-width:400px;height:100vh;background:#fff;z-index:10000;box-shadow:-4px 0 40px rgba(0,0,0,.3);transition:right .3s;display:flex;flex-direction:column;font-family:system-ui}
.searxng-ai-panel.open{right:0}
.searxng-ai-header{display:flex;align-items:center;justify-content:space-between;padding:16px;background:linear-gradient(135deg,#10b981,#059669);color:#fff}
.searxng-ai-header h3{margin:0;font-size:16px}
.searxng-ai-close{background:rgba(255,255,255,.2);border:none;color:#fff;font-size:18px;cursor:pointer;padding:4px 10px;border-radius:4px}
.searxng-ai-body{flex:1;overflow-y:auto;padding:16px}
.searxng-summary-btn{width:100%;padding:12px;background:#10b981;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:13px;font-weight:600}
.searxng-summary{background:#ecfdf5;border-radius:8px;padding:12px;margin-bottom:12px;font-size:13px;border-left:3px solid #10b981}
.searxng-chat-msg{padding:10px;border-radius:8px;margin-bottom:8px;font-size:13px}
.searxng-chat-msg.user{background:#f3f4f6;text-align:right}
.searxng-chat-msg.ai{background:#ecfdf5}
.searxng-chat-msg.error{background:#fee2e2;color:#991b1b}
.searxng-ai-input{display:flex;gap:8px;padding:16px;border-top:1px solid #eee;background:#fafafa}
.searxng-ai-input input{flex:1;padding:10px;border:2px solid #e5e7eb;border-radius:8px;font-size:13px}
.searxng-ai-input button{background:#10b981;color:#fff;border:none;padding:10px 16px;border-radius:8px;cursor:pointer}
.searxng-ai-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:9999}
.searxng-ai-overlay.show{display:block}
@keyframes typing{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)}}
.searxng-typing span{width:6px;height:6px;background:#10b981;border-radius:50%;display:inline-block;animation:typing 1s infinite}
.searxng-typing span:nth-child(2){animation-delay:.2s}
.searxng-typing span:nth-child(3){animation-delay:.4s}
@media(max-width:480px){
.searxng-ai-btn{bottom:15px;right:15px}
.searxng-ai-btn button{padding:10px 14px;font-size:11px}
.searxng-ai-panel{max-width:100vw;box-shadow:none}
}</style>
<div class="searxng-ai-overlay" id="aiOverlay" onclick="closeAiPanel()"></div>
<div class="searxng-ai-panel" id="searxngAiPanel">
<div class="searxng-ai-header"><h3>AI Assistant</h3><button class="searxng-ai-close" onclick="closeAiPanel()">X</button></div>
<div class="searxng-ai-body">
<button class="searxng-summary-btn" onclick="getAISummary()">Get Summary</button>
<div id="aiSummary" class="searxng-summary" style="display:none"></div>
<div id="chatMessages"></div>
</div>
<div class="searxng-ai-input">
<input type="text" id="chatInput" placeholder="Ask AI..." onkeypress="if(event.keyCode==13)sendChat()">
<button onclick="sendChat()">Send</button>
</div>
</div>
<script>
(function(){
var h=[];
function openA(){document.getElementById("searxngAiPanel").classList.add("open");document.getElementById("aiOverlay").classList.add("show");document.body.style.overflow="hidden"}
function closeA(){document.getElementById("searxngAiPanel").classList.remove("open");document.getElementById("aiOverlay").classList.remove("show");document.body.style.overflow=""}
function typ(){var d=document.createElement("div");d.className="searxng-chat-msg ai";d.innerHTML='<span class="searxng-typing"><span></span><span></span><span></span></span>';document.getElementById("chatMessages").appendChild(d);return d}
function getS(){var q=document.querySelector("input[name=q]")?.value||"";var e=document.getElementById("aiSummary");e.innerHTML=q?"Loading...":"Search first!";e.style.display="block";if(q){fetch("/api/summary",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:q})}).then(r=>r.json()).then(function(d){e.innerHTML="Summary: "+(d.summary||"N/A")}).catch(function(){e.innerHTML="Error"})}}
function snd(){var i=document.getElementById("chatInput");var m=i.value.trim();if(!m)return;h.push({role:"user",content:m});i.value="";var t=typ();fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:m})}).then(r=>r.json()).then(function(d){t.innerHTML=d.response||"No response";h.push({role:"ai",content:d.response})}).catch(function(){t.innerHTML="Error";t.className="searxng-chat-msg error"})}
window.openAiPanel=openA;window.closeAiPanel=closeA;
})();
</script>'''
if os.path.exists(base):
    with open(base) as f: c=f.read()
    for p in ['atomic-privacy','atomic-ai-btn','atomic-ai-panel','searxng-ai-btn','searxng-ai-panel','atomic-ai-overlay','searxng-ai-overlay']:
        c=re.sub(r'<style[^>]*>.*?'+p+r'.*?</style>','',c,flags=re.DOTALL)
        c=re.sub(r'<div[^>]*class="[^"]*'+p+r'[^"]*"[^>]*>.*?</div>','',c,flags=re.DOTALL)
    c+=html
    with open(base,"w") as f: f.write(c)
    print("Patched!")
else: print("Not found")
