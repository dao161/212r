import os

html = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CPA Monitor</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f0f2f5;color:#1a1a2e;padding:16px;font-size:13px}
.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;background:#fff;padding:12px 16px;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.08)}
h1{font-size:17px;font-weight:700;color:#1a1a2e}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin-bottom:16px}
.card{background:#fff;border-radius:8px;padding:14px;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
.cl{font-size:11px;color:#6b7280;margin-bottom:4px;font-weight:500}
.cv{font-size:26px;font-weight:700;color:#111827}
.cv.g{color:#059669}.cv.r{color:#dc2626}.cv.y{color:#d97706}.cv.b{color:#2563eb}
.sec{background:#fff;border-radius:8px;padding:14px;margin-bottom:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06)}
.sec h2{font-size:13px;color:#6b7280;margin-bottom:10px;font-weight:600}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:6px 8px;font-size:12px}
th{color:#6b7280;border-bottom:2px solid #e5e7eb;font-weight:600;background:#f9fafb}
td{border-bottom:1px solid #f3f4f6}
tr:hover td{background:#f9fafb}
.bb{background:#e5e7eb;border-radius:4px;height:6px;flex:1}
.bf{background:#059669;border-radius:4px;height:6px;transition:width 0.3s}
.br{display:flex;align-items:center;gap:6px}
.bp{font-size:11px;color:#6b7280;min-width:36px;text-align:right;font-weight:600}
.st{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:5px}
.st.ok{background:#059669}.st.wn{background:#d97706}.st.er{background:#dc2626}
.ctl{display:flex;gap:6px;align-items:center;flex-wrap:wrap}
input[type=number],input[type=text]{background:#f9fafb;border:1px solid #d1d5db;color:#111827;padding:6px 10px;border-radius:6px;font-size:12px}
input[type=number]{width:80px}
button{background:#2563eb;color:#fff;border:none;padding:6px 14px;border-radius:6px;cursor:pointer;font-size:12px;font-weight:500;transition:background 0.2s}
button:hover{background:#1d4ed8}
button.dg{background:#dc2626}button.dg:hover{background:#b91c1c}
.ki{display:flex;gap:8px;margin-bottom:16px;max-width:380px}
.ki input{flex:1;background:#fff;border:1px solid #d1d5db;color:#111827;padding:8px 12px;border-radius:6px;font-size:13px}
#err{color:#dc2626;font-size:12px;margin-top:6px;display:none;background:#fef2f2;padding:8px 12px;border-radius:6px}
.lb{background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;padding:10px;max-height:350px;overflow-y:auto;font-family:'SF Mono',Monaco,monospace;font-size:10px;line-height:1.6;color:#6b7280;white-space:pre-wrap;word-break:break-all}
.lt{max-height:460px;overflow-y:auto}
.lt table{font-size:11px}.lt td{padding:4px 6px}.lt th{padding:5px 6px;position:sticky;top:0;background:#f9fafb}
.cd{color:#dc2626;font-weight:600}
.tabs{display:flex;gap:2px;margin-bottom:10px;background:#f3f4f6;border-radius:6px;padding:2px}
.tab{padding:6px 14px;border-radius:5px;cursor:pointer;font-size:12px;background:transparent;color:#6b7280;border:none;font-weight:500;transition:all 0.2s}
.tab.a{background:#fff;color:#111827;box-shadow:0 1px 2px rgba(0,0,0,0.06)}
.tc{display:none}.tc.a{display:block}
.pg{display:flex;gap:6px;align-items:center;margin-top:6px;font-size:11px;color:#6b7280}
.pg button{font-size:10px;padding:3px 8px}
.ul{color:#059669;font-weight:600}.lk{color:#dc2626;font-weight:600}
.info{font-size:10px;color:#9ca3af}
.tag{display:inline-block;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600}
.tag.g{background:#ecfdf5;color:#059669}.tag.r{background:#fef2f2;color:#dc2626}.tag.y{background:#fffbeb;color:#d97706}.tag.b{background:#eff6ff;color:#2563eb}
</style>
</head>
<body>
<div class="ki" id="auth"><input type="password" id="k" placeholder="Management Key" onkeydown="if(event.key==='Enter')doLogin()"/><button onclick="doLogin()">Login</button></div>
<div id="err"></div>
<div id="dash" style="display:none">
<div class="header"><h1>CPA Monitor</h1><div class="ctl"><span class="info" id="lr"></span><button onclick="G()">Refresh</button></div></div>

<div class="grid">
<div class="card"><div class="cl">Available</div><div class="cv g" id="c1">-</div></div>
<div class="card"><div class="cl">403 (moved)</div><div class="cv r" id="c2">-</div></div>
<div class="card"><div class="cl">Memory</div><div class="cv b" id="c3">-</div></div>
</div>

<div class="sec"><h2>Model Availability</h2>
<table><thead><tr><th>Model</th><th>Total</th><th>429 Lock</th><th>Available</th><th>503 Short</th><th>Avail%</th><th>Tomorrow+</th><th style="width:20%">Bar</th></tr></thead><tbody id="mt"></tbody></table></div>

<div class="sec"><h2>Rate Limit</h2><div class="ctl"><span>Limit: <b id="r1">-</b>/min</span><span style="margin-left:12px">OK: <b id="r2">-</b></span><input type="number" id="ri" placeholder="1000" min="1" style="margin-left:12px"/><button onclick="SRL()">Set</button></div></div>
<div class="sec"><h2>Memory Limit</h2><div class="ctl"><span>Current: <b id="m1">-</b></span><span style="margin-left:12px">Limit: <b id="m2">-</b></span><input type="number" id="mi" placeholder="GB" min="0" step="0.5" style="margin-left:12px"/><button onclick="SML()">Set</button></div></div>

<div class="sec">
<div class="tabs">
<div class="tab a" onclick="ST('logs')">Logs</div>
<div class="tab" onclick="ST('locks')">Locked JSON</div>
<div class="tab" onclick="ST('errlog')">Errors</div>
</div>
<div id="t-logs" class="tc a"><div class="ctl" style="margin-bottom:6px"><button onclick="LL()">Load</button><span class="info" id="lc"></span></div><div class="lb" id="lbox">Click Load...</div></div>
<div id="t-locks" class="tc"><div class="ctl" style="margin-bottom:6px"><button onclick="LK()">Load</button><span class="info" id="kc"></span></div><div class="lt" id="ktbl"></div><div class="pg" id="kpg" style="display:none"><button onclick="KP(-1)">Prev</button><span id="kpi"></span><button onclick="KP(1)">Next</button></div></div>
<div id="t-errlog" class="tc"><div class="ctl" style="margin-bottom:6px"><button onclick="LE()">Load</button></div><div class="lb" id="ebox">Click Load...</div></div>
</div>

</div>

<script>
var K="",B=location.origin,T=null,kD=[],kPg=0,kS=20;

function doLogin(){K=document.getElementById("k").value;if(!K)return;
fetch(B+"/v0/management/dashboard-stats",{headers:{"X-Management-Key":K}}).then(function(r){if(!r.ok)throw r;return r.json()}).then(function(d){
document.getElementById("auth").style.display="none";document.getElementById("err").style.display="none";
document.getElementById("dash").style.display="block";U(d);loadML();T=setInterval(G,15000);
}).catch(function(e){if(e.text)e.text().then(function(t){E(t)});else E(e.message)});}
function E(m){var e=document.getElementById("err");e.textContent=m;e.style.display="block";}
function G(){fetch(B+"/v0/management/dashboard-stats",{headers:{"X-Management-Key":K}}).then(function(r){return r.json()}).then(U).catch(function(){});}

function U(d){
document.getElementById("c1").textContent=d.available_accounts+"/"+d.total_accounts;
document.getElementById("c2").textContent=(d.forbidden_403_count||0);
if(d.memory){document.getElementById("c3").textContent=d.memory.alloc_mb+"MB";}
if(d.rate_limit){document.getElementById("r1").textContent=d.rate_limit.limit_per_minute;document.getElementById("r2").textContent=d.rate_limit.success_count;}
var t=document.getElementById("mt");t.innerHTML="";
if(d.model_stats){for(var i=0;i<d.model_stats.length;i++){var m=d.model_stats[i];
var p=m.available_pct||0;var c=p>80?"ok":p>30?"wn":"er";
t.innerHTML+="<tr><td><span class='st "+c+"'></span>"+m.model+"</td><td>"+m.total+"</td><td class='lk'>"+(m.precise_locked||0)+"</td><td class='ul'>"+m.available+"</td><td>"+(m.short_locked||0)+"</td><td><span class='tag "+(p>80?"g":p>30?"y":"r")+"'>"+p+"%</span></td><td>"+(m.tomorrow_recover||0)+"</td><td><div class='br'><div class='bb'><div class='bf' style='width:"+p+"%'></div></div><span class='bp'>"+p+"%</span></div></td></tr>";}}
if(d.locked_accounts){kD=d.locked_accounts;RK();}
document.getElementById("lr").textContent="Updated: "+new Date().toLocaleTimeString();}

function ST(n){var ts=document.querySelectorAll('.tab');for(var i=0;i<ts.length;i++)ts[i].className='tab';
var cs=document.querySelectorAll('.tc');for(var i=0;i<cs.length;i++)cs[i].className='tc';
if(n==='logs'){ts[0].className='tab a';document.getElementById('t-logs').className='tc a';}
else if(n==='locks'){ts[1].className='tab a';document.getElementById('t-locks').className='tc a';}
else{ts[2].className='tab a';document.getElementById('t-errlog').className='tc a';}}

function SRL(){var v=parseInt(document.getElementById("ri").value);if(!v)return;
fetch(B+"/v0/management/rate-limit",{method:"PUT",headers:{"X-Management-Key":K,"Content-Type":"application/json"},body:JSON.stringify({limit:v})}).then(G);}
function SML(){var v=parseFloat(document.getElementById("mi").value);if(isNaN(v))return;
fetch(B+"/v0/management/memory-limit",{method:"PUT",headers:{"X-Management-Key":K,"Content-Type":"application/json"},body:JSON.stringify({limit_gb:v})}).then(function(){loadML();});}
function loadML(){fetch(B+"/v0/management/memory-limit",{headers:{"X-Management-Key":K}}).then(function(r){return r.json()}).then(function(d){document.getElementById("m1").textContent=d.current_mb+"MB";document.getElementById("m2").textContent=d.limit_mb>0?d.limit_mb+"MB":"None";}).catch(function(){});}

function LL(){document.getElementById("lbox").textContent="Loading...";
fetch(B+"/v0/management/logs",{headers:{"X-Management-Key":K}}).then(function(r){return r.json()}).then(function(d){
var ls=d.lines||[];document.getElementById("lc").textContent=ls.length+" lines";
var box=document.getElementById("lbox");box.textContent="";
var sh=ls.slice(-200);
for(var i=0;i<sh.length;i++){var l=sh[i];var s=document.createElement("div");
if(l.indexOf("error")>-1||l.indexOf("ERROR")>-1)s.style.color="#dc2626";
else if(l.indexOf("warn")>-1)s.style.color="#d97706";
else if(l.indexOf("200 |")>-1)s.style.color="#059669";
s.textContent=l;box.appendChild(s);}box.scrollTop=box.scrollHeight;
}).catch(function(e){document.getElementById("lbox").textContent="Error: "+e.message;});}

function LK(){document.getElementById("ktbl").innerHTML="<div style='color:#6b7280'>Loading...</div>";
fetch(B+"/v0/management/dashboard-stats",{headers:{"X-Management-Key":K}}).then(function(r){return r.json()}).then(function(d){
kD=d.locked_accounts||[];kPg=0;document.getElementById("kc").textContent=kD.length+" locked";
RK();}).catch(function(e){document.getElementById("ktbl").innerHTML="Error";});}
function RK(){var pg=document.getElementById("kpg");var n=kD.length;
if(n===0){document.getElementById("ktbl").innerHTML="<div style='color:#059669;padding:16px;text-align:center'>No locks</div>";pg.style.display="none";return;}
pg.style.display="flex";var s=kPg*kS,e=Math.min(s+kS,n),tp=Math.ceil(n/kS);
document.getElementById("kpi").textContent=(kPg+1)+"/"+tp+" ("+n+")";
var h="<table><thead><tr><th>Account</th><th>Model</th><th>Reason</th><th>Status</th><th>Countdown</th></tr></thead><tbody>";
for(var i=s;i<e;i++){var ac=kD[i];var ms=ac.models||[];
for(var j=0;j<ms.length;j++){var m=ms[j];
var sc=m.locked?"lk":"ul",st=m.locked?"Locked":"OK";
var cd=m.locked&&m.remaining_seconds>0?FC(m.remaining_seconds):"-";
var reason=m.reason||"-";
h+="<tr><td>"+(j===0?ac.name:"")+"</td><td>"+m.model+"</td><td>"+reason+"</td><td class='"+sc+"'>"+st+"</td><td class='cd'>"+cd+"</td></tr>";}}
h+="</tbody></table>";document.getElementById("ktbl").innerHTML=h;}
function KP(d){var tp=Math.ceil(kD.length/kS);kPg+=d;if(kPg<0)kPg=0;if(kPg>=tp)kPg=tp-1;RK();}
function FC(s){if(s<=0)return"-";var m=Math.floor(s/60),r=s%60;return m>0?m+"m "+r+"s":r+"s";}
function LE(){document.getElementById("ebox").textContent="Loading...";
fetch(B+"/v0/management/request-error-logs",{headers:{"X-Management-Key":K}}).then(function(r){return r.json()}).then(function(d){
var fs=d.files||[];if(fs.length===0){document.getElementById("ebox").textContent="No error logs";return;}
var h="";for(var i=fs.length-1;i>=0;i--){var f=fs[i];h+=f.name+" ("+Math.round(f.size/1024)+"KB)\n";}
document.getElementById("ebox").textContent=h;
}).catch(function(e){document.getElementById("ebox").textContent="Error: "+e.message;});}

setInterval(function(){var rs=document.querySelectorAll('.cd');for(var i=0;i<rs.length;i++){
var t=rs[i].textContent;if(!t||t==='-')continue;
var p=t.match(/(\d+)m (\d+)s/);if(p){var tot=parseInt(p[1])*60+parseInt(p[2])-1;rs[i].textContent=tot>0?FC(tot):'-';}
else{var q=t.match(/(\d+)s/);if(q){var v=parseInt(q[1])-1;rs[i].textContent=v>0?v+'s':'-';}}}},1000);
</script>
</body></html>"""

import sys
out = "/opt/cliproxyapi/static/management.html"
if len(sys.argv) > 1:
    out = sys.argv[1]
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    f.write(html)
print("CPA Monitor dashboard written to " + out + ": " + str(len(html)) + " bytes")
