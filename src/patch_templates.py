#!/usr/bin/env python3
"""Patch Atomic Search templates."""

import os

base_html = "/usr/local/searxng/searx/templates/simple/base.html"

privacy_html = """
<style>
.atomic-privacy{position:fixed;bottom:20px;right:20px;z-index:999999;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.atomic-btn{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:#fff;border:none;padding:14px 22px;border-radius:50px;cursor:pointer;font-size:14px;font-weight:600;box-shadow:0 4px 20px rgba(102,126,234,.4);display:flex;align-items:center;gap:8px}
.atomic-btn:hover{transform:translateY(-2px)}
.atomic-popup{display:none;position:absolute;bottom:65px;right:0;background:#fff;border-radius:16px;box-shadow:0 10px 50px rgba(0,0,0,.2);padding:24px;width:340px}
.atomic-popup.show{display:block}
.atomic-popup h3{color:#667eea;font-size:17px;margin:0 0 14px}
.atomic-item{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid #eee}
.atomic-check{color:#10b981;font-size:18px}
.atomic-text{flex:1}
.atomic-text strong{display:block;font-size:13px}
.atomic-text span{font-size:11px;color:#666}
.atomic-modes{display:flex;gap:6px;margin-top:16px}
.mode-btn{flex:1;padding:10px;border:2px solid #667eea;background:#fff;border-radius:8px;cursor:pointer;font-size:11px;font-weight:600}
.mode-btn:hover,.mode-btn.active{background:#667eea;color:#fff}
.close-btn{position:absolute;top:10px;right:12px;background:none;border:none;font-size:20px;cursor:pointer;color:#999}
</style>
<div class="atomic-privacy">
<button class="atomic-btn" onclick="togglePopup()"><span>&#128274;</span><span id="atomicStatus">Protected</span></button>
<div class="atomic-popup" id="atomicPopup">
<button class="close-btn" onclick="togglePopup()">&times;</button>
<h3>&#128274; Atomic Privacy</h3>
<div class="atomic-item"><span class="atomic-check">&#10003;</span><div class="atomic-text"><strong>40+ Trackers Blocked</strong><span>Google, Facebook, Cloudflare</span></div></div>
<div class="atomic-item"><span class="atomic-check">&#10003;</span><div class="atomic-text"><strong>E2EE Encryption</strong><span>End-to-end encrypted</span></div></div>
<div class="atomic-item"><span class="atomic-check">&#10003;</span><div class="atomic-text"><strong>Zero Logs Policy</strong><span>No search history</span></div></div>
<div class="atomic-item"><span class="atomic-check">&#10003;</span><div class="atomic-text"><strong>Security Headers</strong><span>CSP, HSTS, X-Frame-Options</span></div></div>
<div class="atomic-modes">
<button class="mode-btn speed" onclick="setMode('speed',this)">&#9889; Speed</button>
<button class="mode-btn balanced active" onclick="setMode('balanced',this)">&#9878; Balanced</button>
<button class="mode-btn max" onclick="setMode('max',this)">&#128274; Max</button>
</div>
</div>
</div>
<script>
(function(){
  var mode=document.cookie.match(/atomic_mode=([^;]+)/)?.[1]||"balanced";
  function togglePopup(){document.getElementById("atomicPopup").classList.toggle("show")}
  function setMode(m,btn){
    document.cookie="atomic_mode="+m+";path=/;max-age="+(30*24*60*60);
    document.querySelectorAll(".mode-btn").forEach(function(b){b.classList.remove("active")});
    btn.classList.add("active");
    document.getElementById("atomicStatus").textContent=m==="speed"?"Speed":m==="max"?"Maximum":"Protected";
    fetch("/api/privacy/mode",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({mode:m})});
  }
  window.togglePopup=togglePopup;window.setMode=setMode;
})();
</script>
"""

ai_html = """
<style>
.atomic-ai-btn{position:fixed;bottom:80px;right:20px;z-index:999998;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}
.atomic-ai-btn button{background:linear-gradient(135deg,#10b981 0%,#059669 100%);color:#fff;border:none;padding:12px 18px;border-radius:50px;cursor:pointer;font-size:13px;font-weight:600;box-shadow:0 4px 15px rgba(16,185,129,.4);display:flex;align-items:center;gap:6px}
.atomic-ai-popup{display:none;position:fixed;bottom:150px;right:20px;z-index:999999;background:#fff;border-radius:16px;box-shadow:0 10px 50px rgba(0,0,0,.25);padding:20px;width:380px;max-height:500px;overflow-y:auto}
.atomic-ai-popup.show{display:block}
.atomic-ai-popup h3{color:#10b981;font-size:16px;margin:0 0 12px}
.atomic-chat-input{display:flex;gap:8px;margin-top:12px}
.atomic-chat-input input{flex:1;padding:10px;border:2px solid #e5e7eb;border-radius:8px;font-size:13px}
.atomic-chat-input button{background:#10b981;color:#fff;border:none;padding:10px 16px;border-radius:8px;cursor:pointer;font-weight:600}
.atomic-chat-messages{max-height:250px;overflow-y:auto;margin:10px 0}
.atomic-msg{padding:10px;border-radius:8px;margin-bottom:8px;font-size:13px}
.atomic-msg.user{background:#f3f4f6;text-align:right}
.atomic-msg.ai{background:#ecfdf5;text-align:left}
.atomic-summary-box{background:#f0fdf4;border-radius:8px;padding:12px;margin:10px 0;font-size:13px;color:#166534}
.atomic-close{position:absolute;top:8px;right:12px;background:none;border:none;font-size:18px;cursor:pointer;color:#999}
</style>
<div class="atomic-ai-btn">
<button onclick="toggleAiPopup()">&#129504; AI Chat</button>
</div>
<div class="atomic-ai-popup" id="atomicAiPopup">
<button class="atomic-close" onclick="toggleAiPopup()">&times;</button>
<h3>&#129504; Atomic AI</h3>
<button onclick="getAISummary()" style="width:100%;padding:10px;background:#10b981;color:#fff;border:none;border-radius:8px;cursor:pointer;margin-bottom:10px;font-weight:600">&#128196; Get AI Summary</button>
<div id="aiSummary" style="display:none" class="atomic-summary-box"></div>
<div class="atomic-chat-messages" id="chatMessages"></div>
<div class="atomic-chat-input">
<input type="text" id="chatInput" placeholder="Ask AI..." onkeypress="if(event.key==='Enter')sendChat()">
<button onclick="sendChat()">Send</button>
</div>
</div>
<script>
(function(){
  function toggleAiPopup(){document.getElementById("atomicAiPopup").classList.toggle("show")}
  function getAISummary(){
    var q=document.querySelector('input[name="q"]')?.value||"";
    if(!q){document.getElementById("aiSummary").innerHTML="Search something first!";document.getElementById("aiSummary").style.display="block";return;}
    document.getElementById("aiSummary").innerHTML="Loading...";document.getElementById("aiSummary").style.display="block";
    fetch("/api/summary",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:q})})
    .then(r=>r.json()).then(function(d){document.getElementById("aiSummary").innerHTML="AI Summary: "+d.summary;})
    .catch(function(){document.getElementById("aiSummary").innerHTML="Error loading summary";});
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
  window.toggleAiPopup=toggleAiPopup;window.getAISummary=getAISummary;window.sendChat=sendChat;
})();
</script>
"""

if os.path.exists(base_html):
    with open(base_html, "r") as f:
        content = f.read()
    content = content.replace('SearXNG', 'Atomic Search')
    if '<div class="atomic-privacy">' not in content:
        content = content + privacy_html
    if '<div class="atomic-ai-btn">' not in content:
        content = content + ai_html
    with open(base_html, "w") as f:
        f.write(content)
    print("base.html patched with AI buttons!")
else:
    print("base.html not found")
print("Done!")
