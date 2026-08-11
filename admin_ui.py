ADMIN_HTML = r'''<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>uranai-app 管理画面</title>
  <style>
    :root{font-family:Inter,"Noto Sans JP",system-ui,sans-serif;color:#1f2937;background:#f5f3ef}
    *{box-sizing:border-box}body{margin:0}button,input,textarea,select{font:inherit}button{cursor:pointer}
    header{background:#16130f;color:#fff;padding:16px 22px;display:flex;justify-content:space-between;align-items:center;gap:12px}
    header h1{font-size:20px;margin:0}.sub{color:#bdb7ae;font-size:12px}.header-actions{display:flex;gap:8px;align-items:center}
    main{display:grid;grid-template-columns:320px 1fr;min-height:calc(100vh - 68px)}
    aside{border-right:1px solid #ddd6ca;background:#fff;padding:18px}.content{padding:22px;overflow:auto}
    .search{display:flex;gap:8px}.search input{flex:1}.field,input,textarea,select{width:100%;border:1px solid #d6d0c5;border-radius:9px;padding:10px;background:#fff}
    button{border:0;border-radius:9px;padding:10px 14px;background:#29231c;color:#fff}.secondary{background:#e9e4db;color:#29231c}.gold{background:#8b6b2f}.danger{background:#8c3131}.small{padding:6px 9px;font-size:12px}
    .clients{margin-top:14px;display:grid;gap:8px}.client{padding:12px;border:1px solid #e6e0d7;border-radius:10px;cursor:pointer;background:#faf9f7}.client:hover,.client.active{border-color:#8b6b2f;background:#f7f1e5}
    .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px}.card{background:#fff;border:1px solid #e2ddd4;border-radius:14px;padding:18px;box-shadow:0 2px 8px #00000008}.wide{grid-column:1/-1}
    h2{font-size:18px;margin:0}h3{font-size:14px;margin:14px 0 8px;color:#6b6258}.card-head{display:flex;justify-content:space-between;align-items:center;gap:10px;margin-bottom:12px}.muted{color:#777067}.kv{display:grid;grid-template-columns:130px 1fr;gap:6px 12px;font-size:14px}.kv b{color:#6b6258}.pill{display:inline-block;padding:3px 8px;border-radius:999px;background:#eee8dc;margin:2px;font-size:12px}
    .reading{border-top:1px solid #eee8df;padding:12px 0}.reading:first-child{border-top:0}.result{white-space:pre-wrap;line-height:1.75;background:#fbfaf8;border-radius:10px;padding:14px;min-height:90px}.row{display:flex;gap:8px;align-items:center}.row>*{flex:1}.status{font-size:12px;margin-top:8px}.ok{color:#22733b}.err{color:#a33}.empty{padding:30px;text-align:center;color:#81786e}
    .modal-bg{position:fixed;inset:0;background:#0007;display:none;align-items:center;justify-content:center;padding:20px;z-index:50}.modal{background:#fff;width:min(760px,100%);max-height:90vh;overflow:auto;border-radius:16px;padding:20px}.modal h2{margin-bottom:14px}.form-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.form-grid .full{grid-column:1/-1}.label{font-size:12px;color:#6b6258;margin-bottom:5px}.actions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}.chart-layout{display:grid;grid-template-columns:1fr 1fr 1fr;grid-template-areas:". north ." "west center east" ". south .";gap:8px;margin-top:10px}.starbox{border:1px solid #e4ddcf;border-radius:10px;padding:10px;text-align:center;background:#fbfaf7}.starbox b{display:block;font-size:11px;color:#7a6d5b;margin-bottom:3px}.center{grid-area:center}.north{grid-area:north}.east{grid-area:east}.south{grid-area:south}.west{grid-area:west}
    @media(max-width:900px){main{grid-template-columns:1fr}aside{border-right:0;border-bottom:1px solid #ddd6ca}.grid{grid-template-columns:1fr}.wide{grid-column:auto}.form-grid{grid-template-columns:1fr}.form-grid .full{grid-column:auto}}
  </style>
</head>
<body>
<header>
  <div><h1>uranai-app 鑑定士管理画面</h1><div class="sub">相談者カルテ・命式・鑑定履歴・AI鑑定補助</div></div>
  <div class="header-actions"><button class="gold" onclick="openClientModal(true)">＋ 新規相談者</button><a href="/docs" style="color:#ddd;text-decoration:none">API Docs</a></div>
</header>
<main>
  <aside>
    <div class="search"><input id="search" placeholder="氏名・LINE名など"><button onclick="loadClients()">検索</button></div>
    <div id="clients" class="clients"></div>
  </aside>
  <section class="content">
    <div id="empty" class="empty">左から相談者を選ぶか、「＋ 新規相談者」から登録してください。</div>
    <div id="dashboard" style="display:none" class="grid">
      <div class="card"><div class="card-head"><h2>相談者カルテ</h2><button class="secondary small" onclick="openClientModal(false)">編集</button></div><div id="clientCard" class="kv"></div></div>
      <div class="card"><div class="card-head"><h2>出生情報</h2><button class="secondary small" onclick="openBirthModal()">登録・編集</button></div><div id="birthCard" class="kv"></div></div>
      <div class="card"><div class="card-head"><h2>算命学命式</h2><button class="secondary small" onclick="openChartModal()">登録・編集</button></div><div id="chartCard"></div></div>
      <div class="card"><div class="card-head"><h2>AI鑑定補助</h2></div><textarea id="question" rows="5" placeholder="今回の相談内容・AIに整理してほしいことを入力"></textarea><div class="row" style="margin-top:10px"><button class="secondary" onclick="previewPrompt()">プロンプト確認</button><button class="gold" onclick="generateAI()">AI鑑定を生成</button></div><div id="aiStatus" class="status"></div></div>
      <div class="card wide"><div class="card-head"><h2>AI鑑定結果</h2><button class="gold small" onclick="saveAIAsReading()">この結果を鑑定履歴へ保存</button></div><div id="aiResult" class="result muted">まだ生成されていません。</div></div>
      <div class="card wide"><div class="card-head"><h2>鑑定履歴</h2><button class="gold small" onclick="openReadingModal()">＋ 新しい鑑定を保存</button></div><div id="readings"></div></div>
    </div>
  </section>
</main>

<div id="modalBg" class="modal-bg" onclick="if(event.target===this)closeModal()"><div class="modal"><div id="modalBody"></div></div></div>

<script>
let selectedId=null,currentContext=null,lastAIText='';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(url,opts){const r=await fetch(url,opts);let data=null;try{data=await r.json()}catch{}if(!r.ok)throw new Error(data?.detail||`HTTP ${r.status}`);return data}
function json(method,body){return{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}}
function val(id){return document.getElementById(id)?.value?.trim()||''}
function nullable(v){return v===''?null:v}
function openModal(html){document.getElementById('modalBody').innerHTML=html;document.getElementById('modalBg').style.display='flex'}
function closeModal(){document.getElementById('modalBg').style.display='none'}
async function loadClients(){const q=val('search');const rows=await api('/api/clients?limit=100'+(q?'&q='+encodeURIComponent(q):''));const el=document.getElementById('clients');el.innerHTML=rows.length?rows.map(c=>`<div class="client ${c.id===selectedId?'active':''}" onclick="selectClient(${c.id})"><b>${esc(c.name)}</b><div class="muted">${esc(c.name_kana||c.line_name||'')}</div></div>`).join(''):'<div class="muted">該当なし</div>'}
async function selectClient(id){selectedId=id;await loadClients();currentContext=await api(`/api/clients/${id}/context?reading_limit=50`);renderContext(currentContext);document.getElementById('empty').style.display='none';document.getElementById('dashboard').style.display='grid'}
function kv(obj,labels){return Object.entries(labels).map(([k,l])=>`<b>${l}</b><span>${esc(obj?.[k]||'—')}</span>`).join('')}
function renderContext(c){document.getElementById('clientCard').innerHTML=kv(c.client,{name:'氏名',name_kana:'ふりがな',phone:'電話',email:'メール',line_name:'LINE名',notes:'メモ'});document.getElementById('birthCard').innerHTML=kv(c.birth_profile,{birth_date:'生年月日',birth_time:'出生時間',birthplace_prefecture:'都道府県',birthplace_city:'市区町村',birthplace_detail:'詳細',timezone:'タイムゾーン'});const ch=c.sanmeigaku_chart;document.getElementById('chartCard').innerHTML=ch?`<div><span class="pill">年 ${esc(ch.year_pillar||'—')}</span><span class="pill">月 ${esc(ch.month_pillar||'—')}</span><span class="pill">日 ${esc(ch.day_pillar||'—')}</span><span class="pill">${esc(ch.tenchusatsu||'天中殺未登録')}</span></div><div class="chart-layout"><div class="starbox north"><b>北方</b>${esc(ch.north_star||'—')}</div><div class="starbox west"><b>西方</b>${esc(ch.west_star||'—')}</div><div class="starbox center"><b>中央</b>${esc(ch.center_star||'—')}</div><div class="starbox east"><b>東方</b>${esc(ch.east_star||'—')}</div><div class="starbox south"><b>南方</b>${esc(ch.south_star||'—')}</div></div><h3>十二大従星</h3><div><span class="pill">初年期 ${esc(ch.early_star||'—')}</span><span class="pill">中年期 ${esc(ch.middle_star||'—')}</span><span class="pill">晩年期 ${esc(ch.late_star||'—')}</span></div>`:'<span class="muted">未登録</span>';const rs=c.readings||[];document.getElementById('readings').innerHTML=rs.length?rs.map(r=>`<div class="reading"><b>${esc(r.theme||'テーマ未設定')}</b> <span class="muted">${esc((r.reading_at||'').replace('T',' ').slice(0,16))}</span><div>${esc(r.consultation||'')}</div>${r.methods?`<div class="muted">使用占術: ${esc(r.methods)}</div>`:''}${r.result?`<h3>鑑定結果</h3><div>${esc(r.result)}</div>`:''}${r.advice?`<h3>アドバイス</h3><div>${esc(r.advice)}</div>`:''}</div>`).join(''):'<span class="muted">鑑定履歴はまだありません。</span>'}

function field(id,label,value='',type='text',full=false){return`<div class="${full?'full':''}"><div class="label">${label}</div><input id="${id}" type="${type}" value="${esc(value||'')}"></div>`}
function area(id,label,value='',full=true){return`<div class="${full?'full':''}"><div class="label">${label}</div><textarea id="${id}" rows="4">${esc(value||'')}</textarea></div>`}
function openClientModal(isNew){const c=isNew?{}:(currentContext?.client||{});openModal(`<h2>${isNew?'新規相談者':'相談者カルテ編集'}</h2><div class="form-grid">${field('f_name','氏名',c.name)}${field('f_kana','ふりがな',c.name_kana)}${field('f_phone','電話番号',c.phone)}${field('f_email','メール',c.email,'email')}${field('f_line','LINE名',c.line_name)}${area('f_notes','メモ',c.notes)}</div><div class="actions"><button class="secondary" onclick="closeModal()">キャンセル</button><button class="gold" onclick="saveClient(${isNew})">保存</button></div>`)}
async function saveClient(isNew){try{const body={name:val('f_name'),name_kana:nullable(val('f_kana')),phone:nullable(val('f_phone')),email:nullable(val('f_email')),line_name:nullable(val('f_line')),notes:nullable(val('f_notes'))};if(!body.name)throw new Error('氏名は必須です');if(isNew){const c=await api('/api/clients',json('POST',body));closeModal();await loadClients();await selectClient(c.id)}else{await api(`/api/clients/${selectedId}`,json('PATCH',body));closeModal();await selectClient(selectedId)}}catch(e){alert(e.message)}}

function openBirthModal(){const b=currentContext?.birth_profile||{};openModal(`<h2>出生情報</h2><div class="form-grid">${field('b_date','生年月日',b.birth_date,'date')}${field('b_time','出生時間',b.birth_time?String(b.birth_time).slice(0,5):'','time')}<div><div class="label">出生時間</div><label><input id="b_unknown" type="checkbox" style="width:auto" ${b.birth_time_unknown?'checked':''}> 不明</label></div>${field('b_pref','都道府県',b.birthplace_prefecture)}${field('b_city','市区町村',b.birthplace_city)}${field('b_detail','出生地詳細',b.birthplace_detail)}${field('b_tz','タイムゾーン',b.timezone||'Asia/Tokyo')}</div><div class="actions"><button class="secondary" onclick="closeModal()">キャンセル</button><button class="gold" onclick="saveBirth()">保存</button></div>`)}
async function saveBirth(){try{const exists=!!currentContext?.birth_profile;const unknown=document.getElementById('b_unknown').checked;const body={birth_date:val('b_date'),birth_time:unknown?null:nullable(val('b_time')),birth_time_unknown:unknown,birthplace_prefecture:nullable(val('b_pref')),birthplace_city:nullable(val('b_city')),birthplace_detail:nullable(val('b_detail')),timezone:val('b_tz')||'Asia/Tokyo'};if(!body.birth_date)throw new Error('生年月日は必須です');await api(`/api/clients/${selectedId}/birth-profile`,json(exists?'PATCH':'POST',body));closeModal();await selectClient(selectedId)}catch(e){alert(e.message)}}

function openChartModal(){const c=currentContext?.sanmeigaku_chart||{};openModal(`<h2>算命学命式</h2><div class="form-grid">${field('c_year','年干支',c.year_pillar)}${field('c_month','月干支',c.month_pillar)}${field('c_day','日干支',c.day_pillar)}${field('c_tenchu','天中殺',c.tenchusatsu)}${field('c_center','中央',c.center_star)}${field('c_north','北方',c.north_star)}${field('c_east','東方',c.east_star)}${field('c_south','南方',c.south_star)}${field('c_west','西方',c.west_star)}${field('c_early','初年期',c.early_star)}${field('c_middle','中年期',c.middle_star)}${field('c_late','晩年期',c.late_star)}${field('c_source','計算元',c.calculation_source)}${field('c_version','計算バージョン',c.calculation_version)}${area('c_notes','補足メモ',c.notes)}</div><div class="actions"><button class="secondary" onclick="closeModal()">キャンセル</button><button class="gold" onclick="saveChart()">保存</button></div>`)}
async function saveChart(){try{const exists=!!currentContext?.sanmeigaku_chart;const body={year_pillar:nullable(val('c_year')),month_pillar:nullable(val('c_month')),day_pillar:nullable(val('c_day')),center_star:nullable(val('c_center')),north_star:nullable(val('c_north')),east_star:nullable(val('c_east')),south_star:nullable(val('c_south')),west_star:nullable(val('c_west')),early_star:nullable(val('c_early')),middle_star:nullable(val('c_middle')),late_star:nullable(val('c_late')),tenchusatsu:nullable(val('c_tenchu')),calculation_source:nullable(val('c_source')),calculation_version:nullable(val('c_version')),notes:nullable(val('c_notes'))};await api(`/api/clients/${selectedId}/sanmeigaku-chart`,json(exists?'PATCH':'POST',body));closeModal();await selectClient(selectedId)}catch(e){alert(e.message)}}

function openReadingModal(prefill={}){openModal(`<h2>新しい鑑定履歴</h2><div class="form-grid">${field('r_theme','相談テーマ',prefill.theme||'')}${field('r_methods','使用占術',prefill.methods||'算命学・AI補助')}${area('r_consultation','相談内容',prefill.consultation||'')}${area('r_result','鑑定結果',prefill.result||'')}${area('r_advice','アドバイス',prefill.advice||'')}${area('r_follow','フォロー内容',prefill.follow_up||'')}${area('r_private','非公開メモ',prefill.private_notes||'')}</div><div class="actions"><button class="secondary" onclick="closeModal()">キャンセル</button><button class="gold" onclick="saveReading()">保存</button></div>`)}
async function saveReading(){try{const body={theme:nullable(val('r_theme')),consultation:nullable(val('r_consultation')),methods:nullable(val('r_methods')),result:nullable(val('r_result')),advice:nullable(val('r_advice')),follow_up:nullable(val('r_follow')),private_notes:nullable(val('r_private'))};await api(`/api/clients/${selectedId}/readings`,json('POST',body));closeModal();await selectClient(selectedId)}catch(e){alert(e.message)}}

async function previewPrompt(){if(!selectedId)return;const q=val('question');if(!q)return setStatus('相談内容を入力してください','err');try{setStatus('プロンプトを作成中…','');const d=await api(`/api/clients/${selectedId}/ai/prompt`,json('POST',{question:q,reading_limit:10}));lastAIText=d.prompt;showAI(lastAIText);setStatus('AIへ送る内容を表示しました','ok')}catch(e){setStatus(e.message,'err')}}
async function generateAI(){if(!selectedId)return;const q=val('question');if(!q)return setStatus('相談内容を入力してください','err');try{setStatus('AI鑑定を生成しています…','');const d=await api(`/api/clients/${selectedId}/ai/generate`,json('POST',{question:q,reading_limit:10}));lastAIText=d.output_text||d.answer||d.message||JSON.stringify(d,null,2);showAI(lastAIText);setStatus(d.status==='not_configured'?'OPENAI_API_KEYが未設定です':'生成しました',d.status==='not_configured'?'err':'ok')}catch(e){setStatus(e.message,'err')}}
function showAI(text){const e=document.getElementById('aiResult');e.textContent=text;e.classList.remove('muted')}
function saveAIAsReading(){if(!selectedId)return;if(!lastAIText)return alert('先にAI鑑定結果を生成してください');openReadingModal({theme:'AI鑑定補助',consultation:val('question'),methods:'算命学・AI補助',result:lastAIText})}
function setStatus(msg,cls){const e=document.getElementById('aiStatus');e.textContent=msg;e.className='status '+cls}
document.getElementById('search').addEventListener('keydown',e=>{if(e.key==='Enter')loadClients()});loadClients().catch(e=>console.error(e));
</script>
</body></html>'''
