#!/usr/bin/env python3
"""Patch Atomic Search templates."""

import os

base_html = "/usr/local/searxng/searx/templates/simple/base.html"

privacy_html = """
<style>
.atomic-privacy,.atomic-ai-btn{position:fixed;z-index:999999;font-family:-apple-system,BlinkMacSystemFont,sans-serif}
.atomic-btn,.atomic-ai-btn button{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;padding:10px 14px;border-radius:50px;cursor:pointer;font-size:11px;font-weight:600;box-shadow:0 2px 10px rgba(102,126,234,.4)}
.atomic-ai-btn button{background:linear-gradient(135deg,#10b981 0%,#059669 100%)}
.atomic-popup,.atomic-ai-popup{display:none;position:fixed;z-index:1000000;background:#fff;border-radius:12px;box-shadow:0 8px 30px rgba(0,0,0,.25);padding:16px;width:calc(100vw - 30px);max-width:320px;max-height:60vh;overflow-y:auto;left:50%;transform:translateX(-50%);bottom:70px}
.atomic-popup.show,.atomic-ai-popup.show{display:block}
.atomic-popup{left:auto;right:10px;transform:none;bottom:60px;width:280px}
.atomic-popup h3{color:#667eea;font-size:14px;margin:0 0 8px}
.atomic-item{display:flex;align-items:center;gap:8px;padding:6px 0;border-bottom:1px solid #eee;font-size:11px}
.atomic-check{color:#10b981;font-size:14px}
.atomic-text strong{display:block}
.atomic-text span{font-size:9px;color:#666}
.atomic-modes{display:flex;gap:4px;margin-top:10px}
.mode-btn{flex:1;padding:6px 2px;border:2px solid #667eea;background:#fff;border-radius:4px;cursor:pointer;font-size:9px;font-weight:600}
.mode-btn:hover,.mode-btn.active{background:#667eea;color:#fff}
.atomic-chat-input{display:flex;gap:4px;margin-top:8px}
.atomic-chat-input input{flex:1;padding:6px;border:1px solid #e5e7eb;border-radius:4px;font-size:11px}
.atomic-chat-input button{background:#10b981;color:#fff;border:none;padding:6px 10px;border-radius:4px;cursor:pointer}
.atomic-chat-messages{max-height:150px;overflow-y:auto;margin:6px 0}
.atomic-msg{padding:6px;border-radius:4px;margin-bottom:4px;font-size:11px}
.atomic-msg.user{background:#f3f4f6;text-align:right}
.atomic-msg.ai{background:#ecfdf5}
.atomic-summary-box{background:#f0fdf4;border-radius:4px;padding:8px;margin:6px 0;font-size:11px}
.atomic-close{position:absolute;top:6px;right:8px;background:none;border:none;font-size:14px;cursor:pointer;color:#999}
@media(min-width:768px){
.atomic-privacy{position:fixed;bottom:20px;right:20px}
.atomic-ai-btn{position:fixed;bottom:80px;right:20px}
.atomic-btn,.atomic-ai-btn button{padding:12px 18px;font-size:13px}
.atomic-popup{right:20px;bottom:65px;width:320px}
.atomic-popup h3{font-size:15px}
.atomic-item{font-size:12px}
}
</style>
<div class="atomic-privacy">
<button class="atomic-btn" onclick="togglePopup()"><span>&#128274;</span><span id="atomicStatus">Protected</span></button>
</div>
<div class="atomic-ai-btn">
<button onclick="toggleAiPopup()">&#129504; AI</button>
</div>
<div class="atomic-popup" id="atomicPopup">
<button class="atomic-close" onclick="togglePopup()">&times;</button>
<h3>&#128274; Atomic Privacy</h3>
<div class="atomic-item"><span class="atomic-check">&#10003;</span><div class="atomic-text"><strong>40+ Trackers Blocked</strong><span>Google, Facebook</span></div></div>
<div class="atomic-item"><span class="atomic-check">&#10003;</span><div class="atomic-text"><strong>E2EE + Zero Logs</strong><span>Privacy protected</span></div></div>
<div class="atomic-modes">
<button class="mode-btn speed" onclick="setMode('speed',this)">&#9889;</button>
<button class="mode-btn balanced active" onclick="setMode('balanced',this)">&#9878;</button>
<button class="mode-btn max" onclick="setMode('max',this)">&#128274;</button>
</div>
</div>
<div class="atomic-ai-popup" id="atomicAiPopup">
<button class="atomic-close" onclick="toggleAiPopup()">&times;</button>
<h3>&#129504; Atomic AI</h3>
<button onclick="getAISummary()" style="width:100%;padding:8px;background:#10b981;color:#fff;border:none;border-radius:6px;cursor:pointer;margin-bottom:6px;font-size:11px">&#128196; Summary</button>
<div id="aiSummary" style="display:none" class="atomic-summary-box"></div>
<div class="atomic-chat-messages" id="chatMessages"></div>
<div class="atomic-chat-input">
<input type="text" id="chatInput" placeholder="Ask..." onkeypress="if(event.key==='Enter')sendChat()">
<button onclick="sendChat()">&#10148;</button>
</div>
</div>
<script>
(function(){
  var mode=document.cookie.match(/atomic_mode=([^;]+)/)?.[1]||"balanced";
  function togglePopup(){document.getElementById("atomicPopup").classList.toggle("show")}
  function toggleAiPopup(){document.getElementById("atomicAiPopup").classList.toggle("show")}
  function setMode(m,btn){
    document.cookie="atomic_mode="+m+";path=/;max-age="+(30*24*60*60);
    document.querySelectorAll(".mode-btn").forEach(function(b){b.classList.remove("active")});
    btn.classList.add("active");
    document.getElementById("atomicStatus").textContent=m==="speed"?"Speed":m==="max"?"Max":"Protected";
    fetch("/api/privacy/mode",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mode:m})});
  }
  function getAISummary(){
    var q=document.querySelector('input[name="q"]')?.value||"";
    if(!q){document.getElementById("aiSummary").innerHTML="Search first!";document.getElementById("aiSummary").style.display="block";return;}
    document.getElementById("aiSummary").innerHTML="Loading...";document.getElementById("aiSummary").style.display="block";
    fetch("/api/summary",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:q})})
    .then(r=>r.json()).then(function(d){document.getElementById("aiSummary").innerHTML="Summary: "+d.summary;})
    .catch(function(){document.getElementById("aiSummary").innerHTML="Error";});
  }
  function sendChat(){
    var inp=document.getElementById("chatInput");var msg=inp.value.trim();
    if(!msg)return;
    var msgs=document.getElementById("chatMessages");
    msgs.innerHTML+='<div class="atomic-msg user">'+msg+'</div>';inp.value="";
    msgs.innerHTML+='<div class="atomic-msg ai">Thinking...</div>';
    fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg})})
    .then(r=>r.json()).then(function(d){var last=msgs.querySelector(".atomic-msg.ai:last-child");if(last)last.innerHTML=d.response;})
    .catch(function(){var last=msgs.querySelector(".atomic-msg.ai:last-child");if(last)last.innerHTML="Error";});
  }
  window.togglePopup=togglePopup;window.setMode=setMode;window.toggleAiPopup=toggleAiPopup;
  window.getAISummary=getAISummary;window.sendChat=sendChat;
})();
</script>
"""

if os.path.exists(base_html):
    with open(base_html, "r") as f:
        content = f.read()
    content = content.replace('SearXNG', 'Atomic Search')
    # Remove old buttons first
    if '<div class="atomic-privacy">' in content:
        idx = content.find('<div class="atomic-privacy">')
        content = content[:idx]
    if '<div class="atomic-ai-btn">' in content:
        idx = content.find('<div class="atomic-ai-btn">')
        if '<div class="atomic-privacy">' in content:
            content = content[:content.find('<div class="atomic-privacy">')]
        else:
            content = content[:idx]
    content = content + privacy_html
    with open(base_html, "w") as f:
        f.write(content)
    print("Mobile-optimized UI patched!")
else:
    print("base.html not found")

# Force nord-frost theme in settings
settings_yml = "/usr/local/searxng/searx/settings.yml"
if os.path.exists(settings_yml):
    with open(settings_yml, "r") as f:
        s = f.read()
    if "nord-frost" not in s:
        s = s.replace("simple_style: auto", "simple_style: nord-frost")
        with open(settings_yml, "w") as f:
            f.write(s)
        print("Theme forced to nord-frost!")

print("Done!")
