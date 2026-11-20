"""Build XML and an offline gallery from sourced bibliographic records."""
from pathlib import Path
import json, re, hashlib, html, collections
import xml.etree.ElementTree as E
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
PUBLIC=ROOT/'public'
PUBLIC.mkdir(exist_ok=True)
records=json.loads((ROOT/'research/records.json').read_text())
user_additions=json.loads((ROOT/'research/user-additions-2026-11-17.json').read_text())
user_addition_ids={record['isbnNormalized'] for record in user_additions}
user_override_ids={'5318007481','9785496005449','5020249858'}
records+=user_additions
imagekit_manifest=ROOT/'research/imagekit-manifest.json'
imagekit_covers=json.loads(imagekit_manifest.read_text()).get('covers',{}) if imagekit_manifest.exists() else {}
DATE='2026-11-04'
decisions=json.loads((ROOT/'research/decisions.json').read_text())
rules={'hibernate':r'hibernate','postgres':r'postgres(?:ql)?|postgis|постгрес','kafka':r'kafka|ksqldb','java':r'java|swing|j2ee|spring|hibernate','kotlin':r'kotlin|jetpack','clojure':r'clojure','scala':r'scala','groovy':r'groovy|grails','jvm':r'jvm|java|spring|kotlin|scala|clojure|groovy|grails','spring':r'spring','compilers':r'компилятор','ddd':r'ddd|предметно-ориентированное|предметно-ориентированного','dsl':r'предметно-ориентированные языки','android':r'android','algorithms':r'алгоритм|структур.*данных','tools':r'eclipse|netbeans|intellij'}
blocked_works=json.loads((ROOT/'research/excluded-works.json').read_text())['works']
seen=set()
for r in records:
    isbn=r['isbnNormalized']; assert isbn not in seen; seen.add(isbn)
    assert (sum(int(c)*(1 if i%2==0 else 3) for i,c in enumerate(isbn))%10==0) if len(isbn)==13 else (sum((10-i)*(10 if c=='X' else int(c)) for i,c in enumerate(isbn))%11==0)
    p=ROOT/r['coverPath']; assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256']
    with Image.open(p) as im: im.verify()
    assert r['title'] and r['authors'] and r['url'].startswith('https://')
    notes=list(r.get('notes',[]))
    if isbn.startswith('978601'): notes.append('Регистрационная группа ISBN Казахстана: принадлежность конкретного издания издательству РФ требует проверки по выходным данным.')
    if int(r['year'])>2026: notes.append('Год в карточке позднее даты исследования: факт выхода не подтверждён.')
    verified_cover_types={'russian-cover-and-isbn-matched','publisher-cover-and-isbn-matched'}
    if r['coverSourceType']!='publisher' and r.get('coverVerification') not in verified_cover_types and not r.get('archiveVerification'): notes.append('Обложка получена не с сайта издательства; требуется сверка с первичным источником.')
    if isbn=='9785937000552': notes.append('На обложке указано второе издание; соответствие ISBN и года этому изданию не подтверждено.')
    r['reviewNotes']=list(dict.fromkeys(notes))
    r['status']='needs-review' if notes else ('archive-sourced' if r.get('archiveVerification') else ('cross-checked' if r.get('coverVerification') else 'publisher-sourced'))
    if isbn in decisions:
        r['status']='user-approved' if decisions[isbn]['decision']=='include' else 'excluded'
    if (set(r.get('topicCodes',[])) & {'postgres','clojure'} or any(isbn in b['isbns'] or re.search(b['pattern'],r['title'],re.I) for b in blocked_works)) and isbn not in user_addition_ids | user_override_ids:
        r['status']='excluded'
    if isbn in user_override_ids:
        r['status']='cross-checked'
    r['topics']=list(dict.fromkeys(r.get('topicCodes',[])+[k for k,v in rules.items() if re.search(v,r['title'],re.I)])) or ['related']

work_groups=json.loads((ROOT/'research/work-groups.json').read_text())
work_by_isbn={}
for group in work_groups:
    for isbn in group['isbns']:
        assert isbn in seen and isbn not in work_by_isbn
        work_by_isbn[isbn]=group
for r in records:
    group=work_by_isbn.get(r['isbnNormalized'])
    r['workId']=group['id'] if group else 'isbn-'+r['isbnNormalized']
    r['workTitle']=group['title'] if group else r['title']

def xml(name, selected):
    root=E.Element('catalog',{'version':'1','researchedAt':DATE,'completeness':'partial','count':str(len(selected))})
    E.SubElement(root,'scope').text='Русскоязычные издания по JVM, языкам JVM, Kafka, компиляторам и DDD. Одна запись на ISBN; полнота рынка не подтверждена.'
    books=E.SubElement(root,'books')
    for r in selected:
        b=E.SubElement(books,'book',{'id':'isbn-'+r['isbnNormalized'],'status':r['status'],'workId':r['workId']})
        if r['isbnNormalized'] in decisions:
            E.SubElement(b,'selection',decisions[r['isbnNormalized']])
        E.SubElement(b,'title',{'lang':'ru'}).text=r['title']
        if r.get('edition'): E.SubElement(b,'edition').text=r['edition']
        a=E.SubElement(b,'authors')
        for author in r['authors']: E.SubElement(a,'author').text=author
        for k in ['publisher','isbn','pages']: E.SubElement(b,k).text=str(r[k])
        E.SubElement(b,'year',{'kind':r['yearKind']}).text=r['year']
        topics=E.SubElement(b,'topics')
        for t in r['topics']: E.SubElement(topics,'topic',{'code':t})
        c=E.SubElement(b,'cover',{'sourceType':r['coverSourceType'],'kind':'photo' if r['coverSourceType']=='author-photo' else 'cover','visualVerification':r.get('visualVerification','not-complete')})
        for k,v in [('url',r['cover']),('localPath',r['coverPath']),('sourceUrl',r['coverSource']),('width',r['width']),('height',r['height']),('sha256',r['sha256'])]: E.SubElement(c,k).text=str(v)
        E.SubElement(b,'source',{'checkedAt':DATE,'access':r.get('sourceAccess', 'search-index' if r['publisher']=='ДМК Пресс' else 'publisher-page')}).text=r['url']
        if r.get('metadataSource'): E.SubElement(b,'metadataSource').text=r['metadataSource']
        verification=E.SubElement(b,'verificationNotes')
        for n in r.get('verificationNotes',[]): E.SubElement(verification,'note').text=n
        notes=E.SubElement(b,'notes')
        for n in r['reviewNotes']: E.SubElement(notes,'note').text=n
    E.indent(root); E.ElementTree(root).write(ROOT/name,encoding='utf-8',xml_declaration=True)
    E.ElementTree(root).write(PUBLIC/name,encoding='utf-8',xml_declaration=True)
    assert len(E.parse(ROOT/name).findall('./books/book'))==len(selected)
xml('books.xml',[r for r in records if r['status'] in ('publisher-sourced','user-approved','cross-checked','archive-sourced')])
xml('review.xml',[r for r in records if r['status']=='needs-review'])
xml('catalog-all.xml',records)
xml('excluded.xml',[r for r in records if r['status']=='excluded'])
esc=lambda s:html.escape(str(s),quote=True)
labels={'misc':'Разное','hibernate':'Hibernate','kafka':'Kafka','groovy':'Groovy / Grails','java':'Java','kotlin':'Kotlin','scala':'Scala','jvm':'JVM','architecture':'Архитектура','spring':'Spring','compilers':'Компиляторы','ddd':'DDD','dsl':'DSL','android':'Android','algorithms':'Алгоритмы','tools':'Инструменты','related':'Другое'}
counts=collections.Counter(r['status'] for r in records)
active=sum(r['status'] not in ('excluded','needs-review') for r in records)
publisher_options=''.join('<option value="'+esc(v)+'">'+esc(v)+'</option>' for v in sorted({r['publisher'] for r in records if r['status'] not in ('excluded','needs-review')}))
quick_topics=['java','spring','kotlin','scala','jvm','architecture','algorithms','ddd','hibernate','compilers','kafka','misc']
topic_buttons='<button type="button" data-topic="" aria-pressed="true">Все книги</button>'+''.join('<button type="button" data-topic="'+k+'" aria-pressed="false">'+labels[k]+'</button>' for k in quick_topics)
new_ids={r['isbnNormalized'] for r in json.loads((ROOT/'research/additions-verified.json').read_text())}
cards=[]
gallery_groups=collections.OrderedDict()
for r in records:
    if r['status'] in ('excluded','needs-review'): continue
    edition=(' · '+r['edition']) if r.get('edition') else ''
    cover_url=imagekit_covers.get(r['isbnNormalized'],{}).get('url',r['coverPath'])
    cards.append(f'''<article data-search="{esc(' '.join([r['title'],r['publisher'],*r['authors'],r['isbnNormalized'],r['isbn'],r['year'],r.get('edition',''),*r['topics']]).lower())}" data-status="{r['status']}" data-publisher="{esc(r['publisher'])}" data-topics="{esc(' '.join(r['topics']))}" data-new="{str(r['isbnNormalized'] in new_ids).lower()}"><img loading="lazy" src="{esc(cover_url)}" alt="{esc(r['title'])}"><div><small>{esc(r['publisher'])} · {esc(r['year'])}</small><h2>{esc(r['title'])}</h2><p>{esc(', '.join(r['authors']))}</p><label class="owned-control"><input type="checkbox" data-owned-isbn="{r['isbnNormalized']}"> У меня есть</label><p>ISBN {esc(r['isbn'])}{esc(edition)}</p><a href="{esc(r['url'])}">Страница издания</a></div></article>''')

    gallery_groups.setdefault(r['workId'],[]).append((r,cards[-1]))
group_cards=[]
for key, members in gallery_groups.items():
    members.sort(key=lambda pair:(int(pair[0]['year']),pair[0]['isbnNormalized']),reverse=True)
    representative=members[0][0]
    representative_cover=imagekit_covers.get(representative['isbnNormalized'],{}).get('url',representative['coverPath'])
    years=sorted({r['year'] for r,_ in members})
    year_range=years[0] if len(years)==1 else years[0]+'–'+years[-1]
    ownership_control=(f'<label class="owned-control"><input type="checkbox" data-owned-isbn="{representative["isbnNormalized"]}"> У меня есть</label>' if len(members)==1 else '<p class="note">Отметьте своё издание в разделе ниже.</p>')
    group_cards.append(f'''<div class="book-group" data-work="{esc(key)}"><img class="group-cover" loading="lazy" src="{esc(representative_cover)}" alt="{esc(representative['title'])}"><h2>{esc(representative['workTitle'])}</h2><p class="group-meta">{len(members)} изд. · {year_range}</p><p class="owned-summary" aria-live="polite"></p>{ownership_control}<details><summary>Издания и сведения · <span class="match-count">{len(members)}</span></summary><div class="editions">{''.join(card for _,card in members)}</div></details></div>''')

# The web application consumes this concise, public-safe representation.  The
# full research records remain in research/ and keep the audit trail intact.
catalog_data={
    'researchedAt': DATE,
    'books': [{
        'id': r['isbnNormalized'],
        'isbn': r['isbn'],
        'title': r['title'],
        'workId': r['workId'],
        'workTitle': r['workTitle'],
        'authors': r['authors'],
        'publisher': r['publisher'],
        'year': r['year'],
        'edition': r.get('edition',''),
        'topics': r['topics'],
        'coverUrl': imagekit_covers.get(r['isbnNormalized'],{}).get('url',r['coverPath']),
        'sourceUrl': r['url'],
    } for r in records if r['status'] not in ('excluded','needs-review')]
}
(ROOT/'src').mkdir(exist_ok=True)
(ROOT/'src/catalog-data.json').write_text(json.dumps(catalog_data,ensure_ascii=False,indent=2)+'\n')
page=('''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Каталог книг JVM и DDD</title><style>html{scroll-behavior:smooth}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}.catalog-footer{display:flex;justify-content:flex-end;margin-top:32px;padding-bottom:8px}.back-to-top{display:inline-flex;align-items:center;gap:8px;min-height:48px;padding:0 20px;border-radius:10px;background:#f4d85b;color:#141719;font-weight:700;text-decoration:none}.back-to-top:hover{background:#ffe873}.back-to-top:focus-visible{outline:2px solid #fff;outline-offset:4px}.back-to-top span{font-size:26px}body{font:16px/1.5 system-ui;background:#141719;color:#eee;margin:0;padding:32px}main{max-width:1300px;margin:auto}h1{font-size:32px}input,button,select{font:inherit;padding:12px;background:#252b30;color:white;border:1px solid #666;border-radius:6px;margin:8px 8px 16px 0}input[type="search"]{width:min(90%,480px)}input[type="checkbox"]{width:20px;height:20px;margin:0;accent-color:#f4d85b}.owned-control{display:flex;align-items:center;gap:10px;cursor:pointer;margin:12px 0}.owned-summary{color:#f4d85b;font-weight:600}.library-controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap}section{align-items:start;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px}article{padding:20px 0;border-top:1px solid #41474b}.book-group{padding:20px;background:#20262a;border-radius:10px;min-width:0}.group-meta{color:#b7bec4}summary{cursor:pointer;color:#f4d85b;padding:12px 0}summary:focus-visible{outline:2px solid #f4d85b;outline-offset:4px}.editions img{height:160px}.editions h2{font-size:17px}.editions p{overflow-wrap:anywhere}@media(max-width:600px){body{padding:16px}h1{font-size:26px}}img{height:240px;width:100%;object-fit:contain}h2{font-size:19px}a{color:#f4d85b}small,.note{color:#b7bec4}.note{font-size:13px}.topic-buttons{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 20px}.topic-buttons button{margin:0;padding:9px 14px}button:focus-visible{outline:2px solid #f4d85b;outline-offset:3px}.filters{display:flex;flex-wrap:wrap;gap:8px}button{cursor:pointer}button[aria-pressed="true"]{background:#f4d85b;color:#141719;border-color:#f4d85b}[hidden]{display:none}</style><main id="top"><h1>Книги JVM, Kafka, компиляторы и DDD</h1><p>125 изданий в подборке · Исследовано 04.11.2026</p><p>Рабочий каталог, не полная библиография. Источники: издательства и архивные карточки магазинов. Происхождение данных указано у каждой книги; полная сверка выходных данных всех изданий не выполнена. Издания одной книги объединены в группы: раскройте карточку, чтобы сравнить годы, версии, обложки и ISBN. При поиске показываются только подходящие издания.</p><p><a href="books.xml">Скачать каталог XML</a></p><input id="q" type="search" aria-label="Поиск" placeholder="Название, автор, ISBN, Java, Kotlin, DDD…"><div class="filters"><label>Издательство<br><select id="publisher"><option value="">Все издательства</option>'''+publisher_options+'''</select></label></div><div class="topic-buttons" role="group" aria-label="Быстрый выбор тематики">'''+topic_buttons+'''</div><div class="library-controls"><button type="button" id="owned-only" aria-pressed="false">Мои книги</button><span id="owned-total" aria-live="polite"></span></div><p class="note" id="storage-notice">Отметки сохраняются в этом браузере. Для разных изданий выбор хранится отдельно.</p><p id="count" aria-live="polite"></p><section>'''+''.join(group_cards)+'''</section><footer class="catalog-footer"><a class="back-to-top" href="#top" aria-label="Вернуться к началу каталога"><span aria-hidden="true">↑</span> Наверх</a></footer></main><script>
const q=document.querySelector('#q'),publisher=document.querySelector('#publisher'),topic={value:''},cards=[...document.querySelectorAll('article')],groups=[...document.querySelectorAll('.book-group')],shelf=document.querySelector('section');
const initialGroupOrder=new Map(groups.map((group,index)=>[group,index]));
const firebaseConfig={apiKey:'AIzaSyC73CklHmDbbFNhuunTJ9afTZWr1mYVhSM',authDomain:'read-in-60-seconds.firebaseapp.com',projectId:'read-in-60-seconds',storageBucket:'read-in-60-seconds.firebasestorage.app',messagingSenderId:'157768008666',appId:'1:157768008666:web:64bc6c7f87fbe9aa4f36e3'};
firebase.initializeApp(firebaseConfig);
const firebaseAuth=firebase.auth(),firestore=firebase.firestore();
let currentUser=null;
const ownershipKey='read-in-60-seconds.catalog.owned.v1';
let owned=new Set(),onlyOwned=false;
const ownershipInputs=[...document.querySelectorAll('[data-owned-isbn]')],ownedOnly=document.querySelector('#owned-only');
try{
 const raw=localStorage.getItem(ownershipKey);
 if(raw!==null){const saved=JSON.parse(raw);if(!Array.isArray(saved)||!saved.every(i=>typeof i==='string'&&/^(?:[0-9]{13}|[0-9]{9}[0-9X])$/.test(i)))throw new Error('Invalid ownership data');owned=new Set(saved);}
}catch(error){document.querySelector('#storage-notice').textContent='Не удалось прочитать сохранённые отметки. Новые отметки пока доступны в этой вкладке.';}
function updateOwnership(){
 for(const input of ownershipInputs)input.checked=owned.has(input.dataset.ownedIsbn);
 const visibleIds=new Set(ownershipInputs.map(input=>input.dataset.ownedIsbn));
 document.querySelector('#owned-total').textContent='У меня есть: '+[...owned].filter(i=>visibleIds.has(i)).length;
 ownedOnly.setAttribute('aria-pressed',String(onlyOwned));
 document.querySelector('#auth-open').textContent=currentUser?'Аккаунт':'Войти';
 const authStatus=document.querySelector('#auth-status'),authEmail=document.querySelector('#auth-email');
 authStatus.textContent=currentUser?'':'Гостевой режим';authStatus.dataset.state=currentUser?'synced':'guest';
 authEmail.textContent=currentUser?currentUser.email:'';authEmail.hidden=!currentUser;
 document.querySelector('#auth-logout').hidden=!currentUser;
 document.querySelector('#auth-dialog').classList.toggle('is-authenticated',Boolean(currentUser));
 document.querySelector('#auth-title').textContent=currentUser?'Аккаунт':'Личная библиотека';
 document.querySelector('#auth-lead').textContent=currentUser?'Ваши книги синхронизируются между устройствами.':'Сохраняйте отметки «У меня есть» и открывайте их на любом устройстве.';
 document.querySelector('#auth-current-email').textContent=currentUser?currentUser.email:'';
 for(const group of groups){const ids=new Set([...group.querySelectorAll('[data-owned-isbn]')].map(input=>input.dataset.ownedIsbn));const n=[...ids].filter(i=>owned.has(i)).length;group.querySelector('.owned-summary').textContent=n?'В моей библиотеке: '+n+' изд.':'';}
}
function hasOwnedEdition(group){return [...group.querySelectorAll('article [data-owned-isbn]')].some(input=>owned.has(input.dataset.ownedIsbn));}
function orderOwnedGroupsLast(){
 for(const group of [...groups].sort((a,b)=>Number(hasOwnedEdition(a))-Number(hasOwnedEdition(b))||initialGroupOrder.get(a)-initialGroupOrder.get(b)))shelf.append(group);
}
function localSave(){try{localStorage.setItem(ownershipKey,JSON.stringify([...owned].sort()));return true;}catch(error){document.querySelector('#storage-notice').textContent='Браузер не разрешил сохранение. Отметки останутся только до закрытия или обновления страницы.';return false;}}
function cloudBooks(user){return firestore.collection('users').doc(user.uid).collection('catalogOwnership');}
function firebaseError(error){const messages={'auth/email-already-in-use':'Этот email уже зарегистрирован. Войди с паролем.','auth/invalid-credential':'Неверный email или пароль.','auth/wrong-password':'Неверный email или пароль.','auth/user-not-found':'Неверный email или пароль.','auth/too-many-requests':'Слишком много попыток. Подожди немного и повтори.','auth/weak-password':'Пароль слишком простой. Используй не менее 12 символов.','auth/operation-not-allowed':'В Firebase Console нужно включить вход по email и паролю.','permission-denied':'Нет доступа к личной библиотеке. Проверь правила Firestore.'};return Error(messages[error.code]||error.message||'Не удалось сохранить изменения.');}
async function loadCloudOwnership(user,mergeLocal){
 const ref=cloudBooks(user),snapshot=await ref.get(),remote=new Set(snapshot.docs.map(doc=>doc.id));
 const merged=new Set(mergeLocal?[...owned,...remote]:remote),batch=firestore.batch();
 for(const isbn of merged)if(!remote.has(isbn))batch.set(ref.doc(isbn),{owned:true,updatedAt:firebase.firestore.FieldValue.serverTimestamp()});
 if(mergeLocal&&merged.size!==remote.size)await batch.commit();
 owned=merged;localSave();document.querySelector('#storage-notice').hidden=true;filter();
}
for(const input of ownershipInputs)input.addEventListener('change',async()=>{
 const isbn=input.dataset.ownedIsbn,wasOwned=owned.has(isbn),willOwn=input.checked;
 if(willOwn)owned.add(isbn);else owned.delete(isbn);filter();
 try{
  if(currentUser){const ref=cloudBooks(currentUser).doc(isbn);if(willOwn)await ref.set({owned:true,updatedAt:firebase.firestore.FieldValue.serverTimestamp()});else await ref.delete();document.querySelector('#storage-notice').hidden=true;}
  else if(localSave())document.querySelector('#storage-notice').textContent='Отметки сохранены в этом браузере.';
 }catch(error){if(wasOwned)owned.add(isbn);else owned.delete(isbn);document.querySelector('#storage-notice').textContent=firebaseError(error).message;filter();}
});
const authDialog=document.querySelector('#auth-dialog'),authForm=document.querySelector('#auth-form');
document.querySelector('#auth-open').addEventListener('click',()=>{document.querySelector('#auth-error').textContent='';authDialog.showModal();});
document.querySelector('#auth-close').addEventListener('click',()=>authDialog.close());
document.querySelector('#auth-logout').addEventListener('click',async()=>{try{await firebaseAuth.signOut();authDialog.close();}catch(error){document.querySelector('#auth-error').textContent=firebaseError(error).message;}});
authForm.addEventListener('submit',async event=>{
 event.preventDefault();const action=event.submitter.value,email=authForm.elements.email.value.trim().toLowerCase(),password=authForm.elements.password.value,buttons=[...authForm.querySelectorAll('button')];
 buttons.forEach(button=>button.disabled=true);document.querySelector('#auth-error').textContent='';
 try{if(action==='register'){if(password.length<12)throw Error('Пароль должен содержать минимум 12 символов.');await firebaseAuth.createUserWithEmailAndPassword(email,password);}else await firebaseAuth.signInWithEmailAndPassword(email,password);authForm.reset();authDialog.close();}
 catch(error){document.querySelector('#auth-error').textContent=firebaseError(error).message;}finally{buttons.forEach(button=>button.disabled=false);}
});
firebaseAuth.onAuthStateChanged(async user=>{currentUser=user;try{if(user)await loadCloudOwnership(user,true);else{const notice=document.querySelector('#storage-notice');notice.hidden=false;notice.textContent='Отметки сохраняются в этом браузере.';filter();}}catch(error){const notice=document.querySelector('#storage-notice');notice.hidden=false;notice.textContent=firebaseError(error).message;filter();}});
ownedOnly.addEventListener('click',()=>{onlyOwned=!onlyOwned;filter()});
const topicButtons=[...document.querySelectorAll('[data-topic]')];
function filter(){
 updateOwnership();
 orderOwnedGroupsLast();
 for(const button of topicButtons)button.setAttribute('aria-pressed',String(button.dataset.topic===topic.value));
 const term=q.value.toLowerCase().trim().replaceAll('ё','е');let n=0,works=0;
 for(const c of cards){
  const text=c.dataset.search.replaceAll('ё','е');
  c.hidden=!( (!onlyOwned||owned.has(c.querySelector('[data-owned-isbn]').dataset.ownedIsbn))&&text.includes(term)&&(!publisher.value||c.dataset.publisher===publisher.value)&&(!topic.value||c.dataset.topics.split(' ').includes(topic.value)));
  if(!c.hidden)n++;
 }
 for(const group of groups){
  const matches=[...group.querySelectorAll('article')].filter(c=>!c.hidden);
  group.hidden=!matches.length;
  if(!matches.length)continue;
  works++;
  const cover=matches[0].querySelector('img'),hero=group.querySelector('.group-cover');
  hero.src=cover.getAttribute('src');hero.alt=cover.alt;
  group.querySelector('.match-count').textContent=matches.length;
 }
 document.querySelector('#count').textContent=n?'Показано групп: '+works+' из '+groups.length+' · Изданий: '+n+' из '+cards.length:'По выбранным фильтрам ничего не найдено.';
}
for(const button of topicButtons)button.addEventListener('click',()=>{topic.value=button.dataset.topic;filter()});
q.addEventListener('input',filter);publisher.addEventListener('change',filter);filter();
</script></html>''').replace('125 изданий',str(active)+' изданий · '+str(len(gallery_groups))+' групп').replace('Подборка · 125','Подборка · '+str(active)).replace('Из карточек издателей · 119','Из карточек издателей · '+str(counts['publisher-sourced'])).replace('Одобрены вами · 6','Одобрены вами · '+str(counts['user-approved'])).replace('Требуют проверки · 0','Требуют проверки · '+str(counts['needs-review']))
page=page.replace('</style><main','.catalog-heading{display:flex;justify-content:space-between;align-items:flex-start;gap:24px}.catalog-heading h1{margin-top:0}.catalog-heading button{margin:0;white-space:nowrap}.account-controls{display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin:0}.account-info{display:flex;gap:8px;align-items:center}.account-info span{color:#b7bec4;font-size:14px}.account-info #auth-status{color:#e7ecef;font-weight:650}.account-info #auth-status[data-state="synced"]::before{content:"";display:block;width:9px;height:9px;border-radius:50%;background:#74d99a}.auth-form{width:min(100%,430px);padding:8px}.auth-form-header{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;margin-bottom:20px}.auth-form h2{margin:0;font-size:25px}.auth-lead{margin:7px 0 0;color:#b7bec4}.auth-form label{display:block;margin:16px 0 0;font-size:14px;font-weight:650}.auth-form input{box-sizing:border-box;display:block;width:100%;margin:7px 0 0;padding:13px 14px;border-radius:9px;border-color:#586269;background:#252b30;color:#fff}.auth-form input:focus{outline:2px solid #f4d85b;outline-offset:2px;border-color:#f4d85b}.auth-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:22px}.auth-actions button{margin:0;min-height:46px;border-radius:9px}.auth-actions button[value="login"]{background:#f4d85b;color:#141719;border-color:#f4d85b;font-weight:750}.auth-actions button[value="register"]{background:transparent;border-color:#667078}.auth-actions #auth-logout{grid-column:span 2;background:transparent;border-color:#ff8b8b;color:#ffb4b4}.auth-signed-in{display:none;margin:28px 0 6px;padding:16px;border:1px solid #3d5a49;border-radius:12px;background:#202a25}.auth-signed-in strong{display:block;color:#94e3af;margin-bottom:4px}.auth-signed-in span{color:#c6d0c9;font-size:14px}.is-authenticated .auth-credentials,.is-authenticated .auth-hint,.is-authenticated .auth-guest-actions{display:none}.is-authenticated .auth-signed-in{display:block}.auth-close{display:grid;place-items:center;width:36px;height:36px;padding:0;border-radius:50%;font-size:23px;line-height:1;color:#b7bec4;background:transparent;border-color:#4c555c}.auth-error{color:#ff9d9d;min-height:22px;margin:14px 0 0}.auth-hint{margin:10px 0 0;font-size:13px;color:#9da7ae}dialog#auth-dialog{width:min(92vw,500px);padding:0;border:1px solid #3d474e;border-radius:16px;background:#1b2024;color:#f5f6f7;box-shadow:0 28px 80px rgba(0,0,0,.6)}dialog#auth-dialog::backdrop{background:rgba(0,0,0,.72);backdrop-filter:blur(4px)}@media(max-width:600px){.catalog-heading{align-items:stretch;flex-direction:column;gap:0}.catalog-heading button{align-self:flex-start}.auth-actions{grid-template-columns:1fr}.auth-actions #auth-logout{grid-column:auto}}</style><main')
page=page.replace('.auth-actions{display:grid;','.auth-guest-actions{display:contents}.auth-actions{display:grid;')
page=page.replace('.auth-actions{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:22px}', '.auth-actions{display:flex;flex-direction:column;gap:10px;margin-top:18px}')
page=page.replace('<main id="top"><h1>','<main id="top"><div class="catalog-heading"><h1>').replace('</h1><p>','</h1><div class="account-controls"><div class="account-info"><span id="auth-status" aria-live="polite">Гостевой режим</span><span id="auth-email" hidden></span></div><button type="button" id="auth-open">Войти</button></div></div><p>',1)
page=page.replace('<p id="count" aria-live="polite"></p>','''<dialog id="auth-dialog"><form class="auth-form" id="auth-form"><div class="auth-form-header"><div><h2 id="auth-title">Личная библиотека</h2><p class="auth-lead" id="auth-lead">Сохраняйте отметки «У меня есть» и открывайте их на любом устройстве.</p></div><button class="auth-close" type="button" id="auth-close" aria-label="Закрыть">×</button></div><div class="auth-credentials"><label>Email<input name="email" type="email" autocomplete="email" maxlength="254" placeholder="you@example.com" required></label><label>Пароль<input name="password" type="password" autocomplete="current-password" minlength="12" maxlength="128" placeholder="Не менее 12 символов" required></label></div><p class="auth-hint">Если аккаунта ещё нет, регистрация займёт один шаг.</p><div class="auth-signed-in"><strong>Синхронизация включена</strong><span id="auth-current-email"></span></div><p id="auth-error" class="auth-error" role="status"></p><div class="auth-actions"><div class="auth-guest-actions"><button type="submit" value="login">Войти</button><button type="submit" value="register">Создать аккаунт</button></div><button type="button" id="auth-logout">Выйти из аккаунта</button></div></form></dialog><p id="count" aria-live="polite"></p>''')
page=page.replace('<script>\nconst q=','''<script src="https://www.gstatic.com/firebasejs/11.7.3/firebase-app-compat.js"></script><script src="https://www.gstatic.com/firebasejs/11.7.3/firebase-auth-compat.js"></script><script src="https://www.gstatic.com/firebasejs/11.7.3/firebase-firestore-compat.js"></script><script>
const q=''')
(ROOT/'legacy-index.html').write_text(page)
print(collections.Counter(r['status'] for r in records));print(collections.Counter(t for r in records for t in r['topics']))
