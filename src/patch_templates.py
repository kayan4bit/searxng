#!/usr/bin/env python3
"""Patch Atomic Search - Slide-out AI panel + Railway-ready."""

import os

base_html = "/usr/local/searxng/searx/templates/simple/base.html"

# Slide-out AI panel (like Kagi) with close button
ai_panel = """
<style>
.atomic-ai-panel{position:fixed;top:0;right:-420px;width:400px;height:100vh;background:#fff;z-index:9999999;box-shadow:-4px 0 30px rgba(0,0,0,.2);transition:right .3s ease;font-family:-apple-system,BlinkMacSystemFont,sans-serif;display:flex;flex-direction:column}
.atomic-ai-panel.open{right:0}
.atomic-ai-header{display:flex;align-items:center;justify-content:space-between;padding:16px;background:linear-gradient(135deg,#10b981,#059669);color:#fff}
.atomic-ai-header h3{margin:0;font-size:16px;display:flex;align-items:center;gap:8px}
.atomic-ai-close{background:rgba(255,255,255,.2);border:none;color:#fff;font-size:20px;cursor:pointer;padding:4px 10px;border-radius:4px}
.atomic-ai-close:hover{background:rgba(255,255,255,.3)}
.atomic-ai-body{flex:1;overflow-y:auto;padding:16px}
.atomic-summary-btn{width:100%;padding:12px;background:#10b981;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600;margin-bottom:12px}
.atomic-summary-btn:hover{background:#059669}
.atomic-summary{background:#f0fdf4;border-radius:8px;padding:12px;margin-bottom:12px;font-size:13px;line-height:1.5}
.atomic-chat-msg{padding:10px;border-radius:8px;margin-bottom:8px;font-size:13px}
.atomic-chat-msg.user{background:#f3f4f6;text-align:right}
.atomic-chat-msg.ai{background:#ecfdf5}
.atomic-chat-msg.loading{color:#666;font-style:italic}
.atomic-ai-input{display:flex;gap:8px;padding:16px;border-top:1px solid #eee}
.atomic-ai-input input{flex:1;padding:10px;border:2px solid #e5e7eb;border-radius:8px;font-size:13px}
.atomic-ai-input button{background:#10b981;color:#fff;border:none;padding:10px 16px;border-radius:8px;cursor:pointer;font-size:16px}
.atomic-ai-input button:hover{background:#059669}
.atomic-ai-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:9999998}
.atomic-ai-overlay.show{display:block}
@media(max-width:480px){
.atomic-ai-panel{width:100vw}
}
</style>
<div class="atomic-ai-overlay" id="aiOverlay" onclick="closeAiPanel()"></div>
<div class="atomic-ai-panel" id="atomicAiPanel">
<div class="atomic-ai-header">
<h3>&#129504; Atomic AI</h3>
<button class="atomic-ai-close" onclick="closeAiPanel()">&times;</button>
</div>
<div class="atomic-ai-body">
<button class="atomic-summary-btn" onclick="getAISummary()">&#128196; Get AI Summary</button>
<div id="aiSummary" class="atomic-summary" style="display:none"></div>
<div id="chatMessages"></div>
</div>
<div class="atomic-ai-input">
<input type="text" id="chatInput" placeholder="Ask AI anything..." onkeypress="if(event.key==='Enter')sendChat()">
<button onclick="sendChat()">&#10148;</button>
</div>
</div>
<script>
function openAiPanel(){document.getElementById("atomicAiPanel").classList.add("open");document.getElementById("aiOverlay").classList.add("show");document.body.style.overflow="hidden"}
function closeAiPanel(){document.getElementById("atomicAiPanel").classList.remove("open");document.getElementById("aiOverlay").classList.remove("show");document.body.style.overflow=""}
function getAISummary(){
  var q=document.querySelector('input[name="q"]')?.value||"";
  var el=document.getElementById("aiSummary");
  if(!q){el.innerHTML="Search something first!";el.style.display="block";return;}
  el.innerHTML="Loading summary...";el.style.display="block";
  fetch("/api/summary",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:q})})
  .then(r=>r.json()).then(function(d){el.innerHTML="<strong>Summary:</strong><br>"+d.summary;})
  .catch(function(){el.innerHTML="Error loading summary";});
}
function sendChat(){
  var inp=document.getElementById("chatInput");var msg=inp.value.trim();
  if(!msg)return;
  var msgs=document.getElementById("chatMessages");
  msgs.innerHTML+='<div class="atomic-chat-msg user">'+msg+'</div>';inp.value="";
  msgs.innerHTML+='<div class="atomic-chat-msg ai loading">Thinking...</div>';
  msgs.scrollTop=msgs.scrollHeight;
  fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg})})
  .then(r=>r.json()).then(function(d){
    var last=msgs.querySelector(".atomic-chat-msg.ai:last-child");
    if(last){last.classList.remove("loading");last.innerHTML=d.response;}
    msgs.scrollTop=msgs.scrollHeight;
  }).catch(function(){
    var last=msgs.querySelector(".atomic-chat-msg.ai:last-child");
    if(last){last.classList.remove("loading");last.innerHTML="Sorry, I couldn't respond.";}
  });
}
window.openAiPanel=openAiPanel;window.closeAiPanel=closeAiPanel;
</script>
"""

# Small floating AI button (mobile-optimized)
ai_btn = """
<style>
.atomic-ai-btn{position:fixed;bottom:15px;right:15px;z-index:9999999}
.atomic-ai-btn button{background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;padding:10px 14px;border-radius:50px;cursor:pointer;font-size:11px;font-weight:600;box-shadow:0 4px 15px rgba(16,185,129,.4);display:flex;align-items:center;gap:5px}
.atomic-ai-btn button:hover{transform:scale(1.05)}
@media(min-width:768px){
.atomic-ai-btn{position:fixed;bottom:20px;right:20px}
.atomic-ai-btn button{padding:12px 16px;font-size:12px}
}
</style>
<div class="atomic-ai-btn">
<button onclick="openAiPanel()">&#129504; AI</button>
</div>
"""

if os.path.exists(base_html):
    with open(base_html, "r") as f:
        content = f.read()
    content = content.replace('SearXNG', 'Atomic Search')
    # Remove old panels
    for old in ['atomic-ai-panel', 'atomic-ai-btn', 'atomic-ai-overlay']:
        if f'class="{old}"' in content or f'id="{old}"' in content:
            idx = content.find(f'id="{old}"' if f'id="{old}"' in content else f'class="{old}"')
            # Find start of style or div
            start = content.rfind('<style', 0, idx)
            if start == -1: start = content.rfind('<div', 0, idx)
            end = content.find('</script>', idx) + 9
            content = content[:start] + content[end:]
    # Remove old privacy
    if 'atomic-privacy' in content:
        idx = content.find('atomic-privacy')
        start = content.rfind('<style', 0, idx)
        if start == -1: start = content.rfind('<div', 0, idx)
        end = content.find('</script>', idx) + 9
        content = content[:start] + content[end:]
    content = content + ai_btn + ai_panel
    with open(base_html, "w") as f:
        f.write(content)
    print("Slide-out AI panel added!")
else:
    print("base.html not found")
print("Done!")
