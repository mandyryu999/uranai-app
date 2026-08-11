ADMIN_HTML = r'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>uranai-app 管理画面</title>
  <style>
    :root{font-family:Inter,"Noto Sans JP",system-ui,sans-serif;color:#1f2937;background:#f5f3ef}
    *{box-sizing:border-box} body{margin:0} button,input,textarea{font:inherit}
    header{background:#16130f;color:#fff;padding:18px 24px;display:flex;justify-content:space-between;align-items:center}
    header h1{font-size:20px;margin:0}.sub{color:#bdb7ae;font-size:12px}
    main{display:grid;grid-template-columns:320px 1fr;min-height:calc(100vh - 70px)}
    aside{border-right:1px solid #ddd6ca;background:#fff;padding:18px}.content{padding:22px;overflow:auto}
    .search{display:flex;gap:8px}.search input{flex:1}.field,input,textarea{width:100%;border:1px solid #d6d0c5;border-radius:9px;padding:10px;background:#fff}
    button{border:0;border-radius:9px;padding:10px 14px;cursor:pointer;background:#29231c;color:#fff}.secondary{background:#e9e4db;color:#29231c}.gold{background:#8b6b2f}
    .clients{margin-top:14px;display:grid;gap:8px}.client{padding:12px;border:1px solid #e6e0d7;border-radius:10px;cursor:pointer;background:#faf9f7}.client:hover,.client.active{border-color:#8b6b2f;background:#f7f1e5}
    .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.card{background:white;border:1px solid #e2ddd4;border-radius:14px;padding:18px;box-shadow:0 2px 8px #00000008}.wide{grid-column:1/-1}
    h2{font-size:18px;margin:0 0 12px} h3{font-size:14px;margin:14px 0 8px;color:#6b6258}.muted{color:#777067}.kv{display:grid;grid-template-columns:130px 1fr;gap:6px 12px;font-size:14px}.kv b{color:#6b6258}.pill{display:inline-block;padding:3px 8px;border-radius:999px;background:#eee8dc;margin:2px;font-size:12px}
    .reading{border-top:1px solid #eee8df;padding:12px 0}.reading:first-child{border-top:0}.result{white-space:pre-wrap;line-height:1.75;background:#fbfaf8;border-radius:10px;padding:14px;min-height:90px}
    .row{display:flex;gap:8px;align-items:center}.row>*{flex:1}.status{font-size:12px;margin-top:8px}.ok{color:#22733b}.err{color:#a33}.empty{padding:30px;text-align:center;color:#81786e}
    @media(max-width:900px){main{grid-template-columns:1fr}aside{border-right:0;border-bottom:1px solid #ddd6ca}.grid{grid-template-columns:1fr}.wide{grid-column:auto}}
  </style>
</head>
<body>
<header><div><h1>uranai-app 鑑定士管理画面</h1><div class="sub">相談者カルテ・命式・鑑定履歴・AI鑑定補助</div></div><a href="/docs" style="color:#ddd;text-decoration:none">API Docs</a></header>
<main>
  <aside>
    <div class="search"><input id="search" placeholder="氏名・LINE名など"><button onclick="loadClients()">検索</button></div>
    <div id="clients" class="clients"></div>
  </aside>
  <section class="content">
    <div id="empty" class="empty">左から相談者を選んでください。</div>
    <div id="dashboard" style="display:none" class="grid">
      <div class="card"><h2>相談者カルテ</h2><div id="clientCard" class="kv"></div></div>
      <div class="card"><h2>出生情報</h2><div id="birthCard" class="kv"></div></div>
      <div class="card"><h2>算命学命式</h2><div id="chartCard"></div></div>
      <div class="card"><h2>AI鑑定補助</h2><textarea id="question" rows="5" placeholder="今回の相談内容・AIに整理してほしいことを入力"></textarea><div class="row" style="margin-top:10px"><button class="secondary" onclick="previewPrompt()">プロンプト確認</button><button class="gold" onclick="generateAI()">AI鑑定を生成</button></div><div id="aiStatus" class="status"></div></div>
      <div class="card wide"><h2>AI鑑定結果</h2><div id="aiResult" class="result muted">まだ生成されていません。</div></div>
      <div class="card wide"><h2>鑑定履歴</h2><div id="readings"></div></div>
    </div>
  </section>
</main>
<script>
let selectedId=null;
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(url,opts){const r=await fetch(url,opts);let data=null;try{data=await r.json()}catch{}if(!r.ok)throw new Error(data?.detail||`HTTP ${r.status}`);return data}
async function loadClients(){const q=document.getElementById('search').value.trim();const rows=await api('/api/clients?limit=100'+(q?'&q='+encodeURIComponent(q):''));const el=document.getElementById('clients');el.innerHTML=rows.length?rows.map(c=>`<div class="client ${c.id===selectedId?'active':''}" onclick="selectClient(${c.id})"><b>${esc(c.name)}</b><div class="muted">${esc(c.name_kana||c.line_name||'')}</div></div>`).join(''):'<div class="muted">該当なし</div>'}
async function selectClient(id){selectedId=id;await loadClients();const c=await api(`/api/clients/${id}/context?reading_limit=20`);renderContext(c);document.getElementById('empty').style.display='none';document.getElementById('dashboard').style.display='grid'}
function kv(obj,labels){return Object.entries(labels).map(([k,l])=>`<b>${l}</b><span>${esc(obj?.[k]||'—')}</span>`).join('')}
function renderContext(c){document.getElementById('clientCard').innerHTML=kv(c.client,{name:'氏名',name_kana:'ふりがな',phone:'電話',email:'メール',line_name:'LINE名',notes:'メモ'});document.getElementById('birthCard').innerHTML=kv(c.birth_profile,{birth_date:'生年月日',birth_time:'出生時間',birthplace_prefecture:'都道府県',birthplace_city:'市区町村',birthplace_detail:'詳細'});const ch=c.sanmeigaku_chart;document.getElementById('chartCard').innerHTML=ch?`<div><span class="pill">年 ${esc(ch.year_pillar||'—')}</span><span class="pill">月 ${esc(ch.month_pillar||'—')}</span><span class="pill">日 ${esc(ch.day_pillar||'—')}</span><span class="pill">${esc(ch.tenchusatsu||'天中殺未登録')}</span></div><h3>十大主星</h3><div class="kv">${kv(ch,{center_star:'中央',north_star:'北方',east_star:'東方',south_star:'南方',west_star:'西方'})}</div><h3>十二大従星</h3><div class="kv">${kv(ch,{early_star:'初年期',middle_star:'中年期',late_star:'晩年期'})}</div>`:'<span class="muted">未登録</span>';const rs=c.readings||[];document.getElementById('readings').innerHTML=rs.length?rs.map(r=>`<div class="reading"><b>${esc(r.theme||'テーマ未設定')}</b> <span class="muted">${esc((r.reading_at||'').replace('T',' ').slice(0,16))}</span><div>${esc(r.consultation||'')}</div>${r.result?`<h3>鑑定結果</h3><div>${esc(r.result)}</div>`:''}${r.advice?`<h3>アドバイス</h3><div>${esc(r.advice)}</div>`:''}</div>`).join(''):'<span class="muted">鑑定履歴はまだありません。</span>'}
async function previewPrompt(){if(!selectedId)return;const q=document.getElementById('question').value.trim();if(!q)return setStatus('相談内容を入力してください','err');try{setStatus('プロンプトを作成中…','');const d=await api(`/api/clients/${selectedId}/ai/prompt`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,reading_limit:10})});document.getElementById('aiResult').textContent=d.prompt;document.getElementById('aiResult').classList.remove('muted');setStatus('AIへ送る内容を表示しました','ok')}catch(e){setStatus(e.message,'err')}}
async function generateAI(){if(!selectedId)return;const q=document.getElementById('question').value.trim();if(!q)return setStatus('相談内容を入力してください','err');try{setStatus('AI鑑定を生成しています…','');const d=await api(`/api/clients/${selectedId}/ai/generate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({question:q,reading_limit:10})});const text=d.output_text||d.answer||d.message||JSON.stringify(d,null,2);document.getElementById('aiResult').textContent=text;document.getElementById('aiResult').classList.remove('muted');setStatus(d.status==='not_configured'?'OPENAI_API_KEYが未設定です':'生成しました',d.status==='not_configured'?'err':'ok')}catch(e){setStatus(e.message,'err')}}
function setStatus(msg,cls){const e=document.getElementById('aiStatus');e.textContent=msg;e.className='status '+cls}
document.getElementById('search').addEventListener('keydown',e=>{if(e.key==='Enter')loadClients()});loadClients().catch(e=>console.error(e));
</script>
</body></html>'''
