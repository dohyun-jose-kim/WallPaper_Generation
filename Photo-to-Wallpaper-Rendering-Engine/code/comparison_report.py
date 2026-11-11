"""Generate an offline report. Images stay outside Git in the local results tree."""
import json
import os
from pathlib import Path


TEMPLATE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Build and Compare 0.0.1</title><style>
:root{color-scheme:dark;font:15px/1.5 system-ui,sans-serif;background:#11151c;color:#e8edf5}*{box-sizing:border-box}body{margin:0}header{padding:28px 32px 18px;border-bottom:1px solid #354050}h1{font-size:28px;margin:0 0 5px}p{color:#aeb9ca;margin:5px 0}main{padding:20px 32px}button,select{font:inherit;color:inherit;background:#202a39;border:1px solid #45546c;border-radius:7px;padding:7px 12px;cursor:pointer}button.active{background:#275789;border-color:#91beef}nav,.filters{display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-bottom:18px}.filters label{display:flex;gap:8px;align-items:center}.comparison{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:24px}.view{min-width:0}.view select{width:100%;margin-bottom:10px}.imagebox{overflow:auto;max-height:75vh;background:#080b10;border:1px solid #354050;min-height:120px}.imagebox img{display:block;width:100%;height:auto}.zoom .imagebox img{width:1920px;height:1080px;max-width:none}.empty{padding:30px;color:#f0b4a9}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(330px,1fr));gap:18px}.card{background:#1a2230;border:1px solid #354050;border-radius:10px;overflow:hidden}.card img{display:block;width:100%;aspect-ratio:16/9;object-fit:contain;background:#080b10}.card .body{padding:14px}.card h3{font-size:16px;margin:0 0 8px}.actions{display:flex;gap:8px;margin:10px 0}.status{padding:2px 7px;border-radius:4px;font-size:12px}.passed{background:#1b503c}.failed,.blocked{background:#72372f}.warning{background:#69521f}.planned{background:#45546c}details{margin:8px 0}summary{cursor:pointer;color:#bcd0eb}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:12px/1.45 ui-monospace,monospace;color:#bdc9d9;max-height:420px;overflow:auto}a{color:#9dcdff}.source{max-height:180px;max-width:260px;display:block;margin-top:10px}.note{padding:12px;border-left:3px solid #74abd6;background:#192434;margin-bottom:18px}footer{padding:24px 32px;color:#aeb9ca}@media(max-width:800px){main,header{padding:16px}.comparison{grid-template-columns:1fr}.grid{grid-template-columns:1fr}}
</style></head><body><header><h1>Build and Compare <span style="color:#81b4ea">0.0.1</span></h1>
<p>Complete photos. Nine treatments. Five tools. 1920 × 1080 PNG.</p><p id="summary"></p>
<details><summary>Run settings and verification</summary><pre id="run"></pre></details></header><main>
<nav><button class="active" data-input="portrait-01">Portrait</button><button data-input="landscape-01">Landscape</button></nav>
<div class="filters"><label>Method <select id="method"></select></label><label>Tool <select id="tool"></select></label><label>Preset <select id="preset"></select></label><label><input id="zoom" type="checkbox">100% zoom</label><span id="count"></span></div>
<div class="note">Select two results to compare. Use 100% zoom to inspect seams and edges. Native glass settings use different units. Failed cases stay visible.</div>
<details><summary>Prepared source preview</summary><img id="source" class="source" alt="Prepared source photo"></details>
<section class="comparison" id="comparison"><div class="view"><select id="left"></select><div class="imagebox" id="leftImage"></div></div><div class="view"><select id="right"></select><div class="imagebox" id="rightImage"></div></div></section>
<section class="grid" id="grid"></section></main><footer>Process memory is not a full GPU-memory measurement. Selected: S1 Blur, S1 Gallery, D3 Frosted, S2 Gradient. This report uses local files only.</footer>
<script id="data" type="application/json">__DATA__</script><script>
const data=JSON.parse(document.getElementById('data').textContent), rows=data.cases;
let input='portrait-01'; const byId=id=>document.getElementById(id);
const label=r=>`${r.method} · ${r.tool} · ${r.preset} · ${r.status}`;
byId('summary').textContent=`${rows.length} cases · ${rows.filter(r=>r.status==='passed').length} passed · ${rows.filter(r=>r.status==='warning').length} warnings · ${rows.filter(r=>['failed','blocked'].includes(r.status)).length} failed or blocked`;
byId('run').textContent=JSON.stringify(data.run,null,2);
for(const key of ['method','tool','preset']){const s=byId(key);s.add(new Option('All',''));[...new Set(rows.map(r=>r[key]))].forEach(v=>s.add(new Option(v,v)));s.onchange=refresh;}
function show(side){const r=rows.find(r=>r.case_id===byId(side).value),box=byId(side+'Image');box.replaceChildren();if(!r)return;
 if(r.image){const im=new Image();im.src=r.image;im.alt=label(r);box.append(im);}else{const p=document.createElement('p');p.className='empty';p.textContent=`${r.status}: ${r.error||'No image available'}`;box.append(p);}}
function refresh(){const visible=rows.filter(r=>r.input_id===input&&['method','tool','preset'].every(k=>!byId(k).value||byId(k).value===r[k]));byId('count').textContent=`${visible.length} results`;
 byId('source').src=data.previews[input];
 for(const [idx,side] of ['left','right'].entries()){const s=byId(side),previous=s.value;s.replaceChildren();visible.forEach(r=>s.add(new Option(label(r),r.case_id)));if(visible.some(r=>r.case_id===previous))s.value=previous;else if(visible.length)s.selectedIndex=Math.min(idx,visible.length-1);show(side);}
 const grid=byId('grid');grid.replaceChildren();visible.forEach(r=>{const card=document.createElement('article');card.className='card';
 if(r.thumbnail){const im=new Image();im.src=r.thumbnail;im.alt=label(r);im.loading='lazy';card.append(im);}else{const empty=document.createElement('div');empty.className='empty';empty.textContent='No result image';card.append(empty);}
 const body=document.createElement('div');body.className='body';const h=document.createElement('h3');h.textContent=`${r.method} · ${r.tool} · ${r.preset}`;body.append(h);
 const status=document.createElement('span');status.className='status '+r.status;status.textContent=r.status;body.append(status);
 const actions=document.createElement('div');actions.className='actions';for(const side of ['left','right']){const b=document.createElement('button');b.textContent=side==='left'?'Compare left':'Compare right';b.onclick=()=>{byId(side).value=r.case_id;show(side);};actions.append(b);}body.append(actions);
 if(r.image){const a=document.createElement('a');a.href=r.image;a.textContent='Open full PNG';a.target='_blank';body.append(a);}
 const d=document.createElement('details'),s=document.createElement('summary'),pre=document.createElement('pre');s.textContent='Settings, checks and measurements';pre.textContent=JSON.stringify(r,null,2);d.append(s,pre);body.append(d);card.append(body);grid.append(card);});}
document.querySelectorAll('[data-input]').forEach(b=>b.onclick=()=>{input=b.dataset.input;document.querySelectorAll('[data-input]').forEach(x=>x.classList.toggle('active',x===b));refresh();});
byId('left').onchange=()=>show('left');byId('right').onchange=()=>show('right');byId('zoom').onchange=()=>byId('comparison').classList.toggle('zoom',byId('zoom').checked);refresh();
</script></body></html>'''


def resolve_rated_image(path):
    """Resolve a positive-rating rename without changing evidence or filenames."""
    path = Path(path)
    rated = path.with_name(path.stem + 'a' + path.suffix)
    return path if path.exists() or not rated.exists() else rated


def write_report(run, cases, destination, prepared_dir):
    rows = []
    for original in cases:
        row = dict(original)
        for key in ('image', 'thumbnail'):
            if row.get(key):
                resolved = resolve_rated_image(row[key])
                if key == 'image' and resolved != Path(row[key]):
                    row['user_rating'] = 'a'
                row[key] = Path(os.path.relpath(resolved, destination.parent)).as_posix()
        rows.append(row)
    data = {'run': run, 'cases': rows,
            'previews': {name: Path(os.path.relpath(prepared_dir / f'{name}.png', destination.parent)).as_posix()
                         for name in ('portrait-01', 'landscape-01')}}
    destination.write_text(TEMPLATE.replace('__DATA__', json.dumps(data).replace('</', '<\\/')))
