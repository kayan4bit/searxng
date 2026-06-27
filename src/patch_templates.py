#!/usr/bin/env python3
"""SearXNG - Clean UI + AI Panel."""
import os, re
base = "/usr/local/searxng/searx/templates/simple/base.html"
html = '''<style>
.sxng-ai-wrap{position:fixed;bottom:20px;right:20px;z-index:99999}
.sxng-ai-btn{background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;padding:14px 18px;border-radius:50px;cursor:pointer;font-size:13px;font-weight:600;box-shadow:0 4px 25px rgba(16,185,129,.5);display:flex;align-items:center;gap:8px;font-family:system-ui}
.sxng-ai-btn:hover{transform:scale(1.05);box-shadow:0 6px 30px rgba(16,185,129,.6)}
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
@media(max-width:480px){
.sxng-ai-wrap{bottom:15px;right:15px}
.sxng-ai-btn{padding:12px 14px;font-size:12px}
.sxng-panel{width:100vw;right:-100%}
.sxng-panel.open{right:0}
}</style>
<div class="sxng-ov" id="sxngOv" onclick="sxngClose()"></div>
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
<script>
(function(){
var h=[];
function sxngOpen(){document.getElementById("sxngPanel").classList.add("open");document.getElementById("sxngOv").classList.add("show");document.body.style.overflow="hidden";document.getElementById("sxngInp").focus()}
function sxngClose(){document.getElementById("sxngPanel").classList.remove("open");document.getElementById("sxngOv").classList.remove("show");document.body.style.overflow=""}
function sxngTyp(){var d=document.createElement("div");d.className="sxng-msg ai ld";d.innerHTML='<span class="sxng-typing"><span></span><span></span><span></span></span>';document.getElementById("sxngMsgs").appendChild(d);return d}
function sxngSum(){var q=document.querySelector("input[name=q]")?.value||"";var e=document.getElementById("sxngSum");if(!q){e.innerHTML="Search something first!";e.classList.add("show");return}e.innerHTML="Loading...";e.classList.add("show");fetch("/api/summary",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:q})}).then(r=>r.json()).then(function(d){e.innerHTML=(d.summary||"No summary").replace(/\\n/g,"<br>")}).catch(function(){e.innerHTML="Error loading summary"})}
function sxngSend(){var i=document.getElementById("sxngInp");var m=i.value.trim();if(!m)return;h.push({role:"user",content:m});i.value="";var t=sxngTyp();fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:m})}).then(r=>r.json()).then(function(d){t.classList.remove("ld");t.classList.add("ai");t.innerHTML=(d.response||"No response").replace(/\\n/g,"<br>");h.push({role:"ai",content:d.response})}).catch(function(){t.classList.remove("ld");t.classList.add("err");t.innerHTML="Error"})}
window.sxngOpen=sxngOpen;window.sxngClose=sxngClose;
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
