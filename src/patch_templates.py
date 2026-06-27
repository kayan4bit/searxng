#!/usr/bin/env python3
"""Patch Atomic Search templates."""

import os

base_html = "/usr/local/searxng/searx/templates/simple/base.html"

badge_html = """
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
.mode-btn.speed{border-color:#f59e0b;color:#f59e0b}
.mode-btn.speed.active{background:#f59e0b;color:#fff}
.close-btn{position:absolute;top:10px;right:12px;background:none;border:none;font-size:20px;cursor:pointer;color:#999}
</style>
<div class="atomic-privacy">
<button class="atomic-btn" id="atomicBtn" onclick="togglePopup()"><span>&#128274;</span><span id="atomicStatus">Protected</span></button>
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
  window.togglePopup=togglePopup;
  window.setMode=setMode;
})();
</script>
"""

if os.path.exists(base_html):
    with open(base_html, "r") as f:
        content = f.read()
    
    # Replace SearXNG text with Atomic Search
    content = content.replace('SearXNG', 'Atomic Search')
    
    # Add privacy badge before </body> if not already there
    if '<div class="atomic-privacy">' not in content:
        content = content + badge_html
    
    with open(base_html, "w") as f:
        f.write(content)
    print("base.html patched successfully")
else:
    print("base.html not found, skipping")

print("Atomic Search patch complete!")
