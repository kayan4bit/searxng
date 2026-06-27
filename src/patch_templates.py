#!/usr/bin/env python3
"""Patch Atomic Search - Slide-out AI panel + Railway-ready."""

import os

base_html = "/usr/local/searxng/searx/templates/simple/base.html"

# Slide-out AI panel (mobile-optimized)
ai_panel = """
<style>
.searxng-ai-panel{position:fixed;top:0;right:-100%;width:100%;max-width:400px;height:100vh;background:#fff;z-index:9999999;box-shadow:-4px 0 30px rgba(0,0,0,.2);transition:right .3s ease;font-family:-apple-system,BlinkMacSystemFont,sans-serif;display:flex;flex-direction:column}
.searxng-ai-panel.open{right:0}
.searxng-ai-header{display:flex;align-items:center;justify-content:space-between;padding:14px;background:#10b981;color:#fff}
.searxng-ai-header h3{margin:0;font-size:15px}
.searxng-ai-close{background:rgba(255,255,255,.2);border:none;color:#fff;font-size:18px;cursor:pointer;padding:4px 10px;border-radius:4px}
.searxng-ai-close:hover{background:rgba(255,255,255,.3)}
.searxng-ai-body{flex:1;overflow-y:auto;padding:14px}
.searxng-summary-btn{width:100%;padding:10px;background:#10b981;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:13px;font-weight:600;margin-bottom:10px}
.searxng-summary-btn:hover{background:#059669}
.searxng-summary{background:#f0fdf4;border-radius:6px;padding:10px;margin-bottom:10px;font-size:12px}
.searxng-chat-msg{padding:8px;border-radius:6px;margin-bottom:6px;font-size:12px}
.searxng-chat-msg.user{background:#f3f4f6;text-align:right}
.searxng-chat-msg.ai{background:#ecfdf5}
.searxng-chat-msg.loading{color:#666;font-style:italic}
.searxng-ai-input{display:flex;gap:6px;padding:14px;border-top:1px solid #eee}
.searxng-ai-input input{flex:1;padding:8px;border:1px solid #e5e7eb;border-radius:6px;font-size:12px}
.searxng-ai-input button{background:#10b981;color:#fff;border:none;padding:8px 14px;border-radius:6px;cursor:pointer;font-size:14px}
.searxng-ai-overlay{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.5);z-index:9999998}
.searxng-ai-overlay.show{display:block}
@media(max-width:480px){
.searxng-ai-panel{max-width:100vw}
.searxng-ai-btn{position:fixed;bottom:70px;right:10px}
.searxng-ai-btn button{padding:10px 14px;font-size:11px}
}
</style>
<div class="searxng-ai-overlay" id="aiOverlay" onclick="closeAiPanel()"></div>
<div class="searxng-ai-panel" id="searxngAiPanel">
<div class="searxng-ai-header">
<h3>&#129504; AI Assistant</h3>
<button class="searxng-ai-close" onclick="closeAiPanel()">&times;</button>
</div>
<div class="searxng-ai-body">
<button class="searxng-summary-btn" onclick="getAISummary()">&#128196; Get Summary</button>
<div id="aiSummary" class="searxng-summary" style="display:none"></div>
<div id="chatMessages"></div>
</div>
<div class="searxng-ai-input">
<input type="text" id="chatInput" placeholder="Ask AI..." onkeypress="if(event.key==='Enter')sendChat()">
<button onclick="sendChat()">&#10148;</button>
</div>
</div>
<script>
function openAiPanel(){document.getElementById("searxngAiPanel").classList.add("open");document.getElementById("aiOverlay").classList.add("show");document.body.style.overflow="hidden"}
function closeAiPanel(){document.getElementById("searxngAiPanel").classList.remove("open");document.getElementById("aiOverlay").classList.remove("show");document.body.style.overflow=""}
function getAISummary(){
  var q=document.querySelector('input[name="q"]')?.value||"";
  var el=document.getElementById("aiSummary");
  if(!q){el.innerHTML="Search first!";el.style.display="block";return;}
  el.innerHTML="Loading...";el.style.display="block";
  fetch("/api/summary",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:q})})
  .then(r=>r.json()).then(function(d){el.innerHTML="<strong>Summary:</strong><br>"+d.summary;}).catch(function(){el.innerHTML="Error";});
}
function sendChat(){
  var inp=document.getElementById("chatInput");var msg=inp.value.trim();
  if(!msg)return;
  var msgs=document.getElementById("chatMessages");
  msgs.innerHTML+='<div class="searxng-chat-msg user">'+msg+'</div>';inp.value="";
  msgs.innerHTML+='<div class="searxng-chat-msg ai loading">Thinking...</div>';
  msgs.scrollTop=msgs.scrollHeight;
  fetch("/api/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg})})
  .then(r=>r.json()).then(function(d){var last=msgs.querySelector(".searxng-chat-msg.ai:last-child");if(last){last.classList.remove("loading");last.innerHTML=d.response;}}).catch(function(){var last=msgs.querySelector(".searxng-chat-msg.ai:last-child");if(last){last.classList.remove("loading");last.innerHTML="Error";}});
}
window.openAiPanel=openAiPanel;window.closeAiPanel=closeAiPanel;
</script>
"""

# Small floating AI button (mobile-optimized)
ai_btn = """
<style>
.searxng-ai-btn{position:fixed;bottom:15px;right:15px;z-index:9999999}
.searxng-ai-btn button{background:linear-gradient(135deg,#10b981,#059669);color:#fff;border:none;padding:10px 14px;border-radius:50px;cursor:pointer;font-size:11px;font-weight:600;box-shadow:0 4px 15px rgba(16,185,129,.4)}
.searxng-ai-btn button:hover{transform:scale(1.05)}
@media(min-width:768px){
.searxng-ai-btn{position:fixed;bottom:20px;right:20px}
.searxng-ai-btn button{padding:12px 16px;font-size:12px}
}
</style>
<div class="searxng-ai-btn">
<button onclick="openAiPanel()">&#129504; AI</button>
</div>
"""

if os.path.exists(base_html):
    with open(base_html, "r") as f:
        content = f.read()
    # Keep SearXNG branding
    # Remove old panels
    for old in ['atomic-ai-panel', 'searxng-ai-panel', 'atomic-ai-btn', 'searxng-ai-btn', 'atomic-ai-overlay', 'searxng-ai-overlay', 'atomic-privacy']:
        if f'class="{old}"' in content or f'id="{old}"' in content:
            idx = content.find(f'id="{old}"' if f'id="{old}"' in content else f'class="{old}"')
            start = content.rfind('<style', 0, idx)
            if start == -1: start = content.rfind('<div', 0, idx)
            end = content.find('</script>', idx) + 9
            if end > start: content = content[:start] + content[end:]
    content = content + ai_btn + ai_panel
    with open(base_html, "w") as f:
        f.write(content)
    print("Mobile-optimized AI panel added!")
else:
    print("base.html not found")

# Update opensearch for default search
opensearch_xml = "/usr/local/searxng/searx/templates/simple/opensearch.xml"
if os.path.exists(opensearch_xml):
    with open(opensearch_xml, "r") as f:
        c = f.read()
    # Keep SearXNG name
    with open(opensearch_xml, "w") as f:
        f.write(c)
    print("OpenSearch ready!")

print("Done!")
