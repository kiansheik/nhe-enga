#!/usr/bin/env python3
"""Build the VLB viewer's small page files from pinned, local source snapshots.

Python standard library only. Run from any directory: python vlb/build_data.py
No network and no original 79 MB PDF are required. OCR transcription alignment
and proposed Navarro associations are separate evidence layers. The saved source
text is never normalized or rewritten. Generated gzip files use mtime=0.
"""
from pathlib import Path
import argparse, bisect, collections, difflib, gzip, hashlib, json, re, unicodedata

P=argparse.ArgumentParser(description=__doc__)
P.add_argument('--output',type=Path,help='Output folder; defaults to data beside this script.')
args=P.parse_args()
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source'
OUT=args.output or ROOT/'data'
(OUT/'pages').mkdir(parents=True,exist_ok=True)

def read(name):
    p=SOURCE/name
    if p.suffix=='.gz':
        with gzip.open(p,'rt',encoding='utf-8') as f:return json.load(f)
    return json.loads(p.read_text(encoding='utf-8'))
def write(name,obj,gz=False):
    data=json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    path=OUT/name
    temp=path.with_name(path.name+'.tmp')
    if gz:
        with temp.open('wb') as f:
            with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0) as g:g.write(data)
    else:temp.write_bytes(data+b'\n')
    temp.replace(path)
    return path.stat().st_size

def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')
def token_spans(s):
    return [(norm(m.group()),m.start(),m.end()) for m in re.finditer(r'[^\W_]+',s,re.UNICODE)]
def page_id(volume,page):return f'{volume}-{int(page):03d}'

text=(SOURCE/'emerson_vlb.txt').read_text(encoding='utf-8')
source_meta=read('source_metadata.json')
assert hashlib.sha256(text.encode()).hexdigest()==source_meta['text_sha256']
assert len(text.encode('utf-16-le'))//2==len(text)
alignment=read('page_alignment.json.gz')
page_map=read('page_map.json')
ocr={p['pdf_page1']:p for p in read('ocr_layout.json.gz')}
citations=read('citation_links.json.gz')
pdf_meta=read('pdf_source_metadata.json')
reviewed_path=SOURCE/'verified_citation_associations.json'
reviewed=read('verified_citation_associations.json') if reviewed_path.exists() else []
reviewed_by=collections.defaultdict(list)
for r in reviewed:reviewed_by[(r['citation_id'],r['page_id'])].append(r)
heading_re=re.compile(r'(?:[A-Z]\.?(?: ante .+)?|Deincipientibus a litera .+|De U Consoante)')
units=[];cursor=0
for number,raw in enumerate(text.split('\n'),1):
    kind='title' if number==1 else ('heading' if heading_re.fullmatch(raw) else 'entry')
    units.append({'id':f"vlb-emerson-r{source_meta['document_revision']}-p{number:05d}",'line':number,'start':cursor,'end':cursor+len(raw),'text':raw,'kind':kind})
    cursor+=len(raw)+1
assert '\n'.join(u['text'] for u in units)==text
units_by_id={u['id']:u for u in units}

# Per-page citations retain occurrence identity. Candidate associations are proposals.
citations_by_page=collections.defaultdict(list)
unresolved=[];citation_index=[]
for c in citations:
    linked=[]
    for p in c.get('page_links',[]):
        if p.get('link_status')!='page_range_linked':continue
        pid=page_id(p['volume'],p['printed_page']);linked.append(pid)
        associations=[]
        for a in p.get('paragraph_candidates',[]):
            reasons=[]
            for reason in a.get('reasons',[]):
                tokens=reason.get('tokens') or []
                if tokens:reasons.append({'type':reason.get('type'),'tokens':tokens})
                elif reason.get('type'):reasons.append({'type':reason['type']})
            associations.append({'source_id':a['source_id'],'source_line':a['source_line'],'status':'proposed','score':a.get('retrieval_score'), 'score_is_probability':False,'evidence':reasons})
        for a in reviewed_by.get((c['citation_id'],pid),[]):
            associations=[x for x in associations if x['source_id']!=a['source_id']]
            associations.insert(0,{'source_id':a['source_id'],'source_line':units_by_id[a['source_id']]['line'],'status':'reviewed','reviewer':a.get('reviewer','assistant'),'source_form':a.get('source_form'),'review_scope':a.get('review_scope','specific_citation_and_source_attestation'),'covers_entire_source_record':False,'evidence':a.get('evidence',[])})
        citations_by_page[pid].append({
            'id':c['citation_id'],'entry_index':c['entry_index'],'legacy_id':c.get('legacy_id'),
            'headword':c['headword'],'homonym':c.get('homonym',''),
            'raw_citation':c['raw_citation'],'context':c.get('local_context_text',''),
            'context_start':c.get('local_context_start'),'context_end':c.get('local_context_end_exclusive'),
            'citation_start':c.get('citation_start'),'citation_end':c.get('citation_end_exclusive'),
            'citation_type':c.get('citation_type'),'adapted':bool(c.get('adapted_citation')),
            'inherits_from':c.get('inherits_source_from_citation_id'),'associations':associations})
    if not linked:unresolved.append(c)
    citation_index.append({'id':c['citation_id'],'entry_index':c['entry_index'],'legacy_id':c.get('legacy_id'),'headword':c['headword'],'homonym':c.get('homonym',''),'pages':linked,'raw_citation':c['raw_citation']})
assert len({c['id'] for c in citation_index})==len(citations), 'Duplicate or omitted citation occurrence identity.'
assert len(unresolved)==2

# Monotonic within-page token alignment maps source fragments to OCR line boxes.
# It is orthographic transcription evidence, not a semantic Navarro judgment.
def align_layout(page,fragments):
    raw=ocr[page['pdf_page1']]
    w,h=raw['width_pt'],raw['height_pt']
    lines=[]
    for i,line in enumerate(raw['lines']):
        s=line['text'];n=norm(s).strip();box=line['bbox']
        if box[1]<h*.09 and (re.fullmatch(r'[\d\s]+',n) or re.fullmatch(r'(?:vocabulario|na|lingua|brasilica|\s)+',n)):continue
        if 'biblioteca digital curt' in n or 'etnolinguistica.org' in n:continue
        lines.append({'id':f"ocr-{page['pdf_page1']:03d}-{i:03d}",'text':s,'box':[round(max(0,min(1,v/(w if j%2==0 else h))),5) for j,v in enumerate(box)],'_y':box[1],'_x':box[0]})
    # OCR text spans at the same physical baseline are ordered left-to-right.
    rows=[]
    for line in sorted(lines,key=lambda x:(x['_y'],x['_x'])):
        if rows and abs(line['_y']-rows[-1][0]['_y'])<=2.5:rows[-1].append(line)
        else:rows.append([line])
    lines=[x for row in rows for x in sorted(row,key=lambda x:x['_x'])]
    owords=[];owners=[]
    for line in lines:
        ts=token_spans(line['text'])
        for t,_,_ in ts:owords.append(t);owners.append(line['id'])
    a,b=page['source_start'],page['source_end']
    st=token_spans(text[a:b]);swords=[t[0] for t in st]
    sm=difflib.SequenceMatcher(None,swords,owords,autojunk=False)
    matches={}
    for block in sm.get_matching_blocks():
        for j in range(block.size):matches[block.a+j]=owners[block.b+j]
    line_by_id={x['id']:x for x in lines}
    for f in fragments:
        tis=[i for i,(_,start,end) in enumerate(st) if a+start<f['source_end0'] and a+end>f['source_start0']]
        mids=[matches[i] for i in tis if i in matches]
        lids=list(dict.fromkeys(mids))
        ratio=len(mids)/max(1,len(tis))
        status='aligned' if len(mids)>=2 and ratio>=.55 else ('partial' if mids and ratio>=.25 else 'unmatched')
        if status=='unmatched':lids=[]
        f['ocr']={'status':status,'confidence':round(ratio,3),'confidence_is_probability':False,'line_ids':lids,'boxes':[line_by_id[i]['box'] for i in lids]}
    for line in lines:line.pop('_y');line.pop('_x')
    return lines,round(sum(b.size for b in sm.get_matching_blocks())/max(1,len(st)),3)

manifest_pages=[];source_pages=collections.defaultdict(list)
source_page_fragments=collections.defaultdict(list)
fragment_status=collections.Counter();total_fragments=0;total_associations=0;reviewed_count=0
for page in alignment['pages']:
    pid=page_id(page['printed_volume'],page['printed_page'])
    a,b=page['source_start'],page['source_end']
    fragments=[]
    for u in units:
        left=max(a,u['start']);right=min(b,u['end'])
        if left>=right:continue
        fragment={'id':u['id'],'source_line':u['line'],'kind':u['kind'],'text':text[left:right],
            'source_start0':left,'source_end0':right,
            'continues_from_previous':left>u['start'],'continues_on_next':right<u['end'],
            'boundary_uncertain':(left<page['start_boundary']['upper_char_offset0'] and u['start']<page['start_boundary']['upper_char_offset0']) or (right>page['end_boundary']['lower_char_offset0'] and u['end']>page['end_boundary']['lower_char_offset0'])}
        fragments.append(fragment);source_pages[u['id']].append(pid)
        source_page_fragments[u['id']].append({'page_id':pid,'text':fragment['text']})
    lines,layout_ratio=align_layout(page,fragments)
    available={f['id'] for f in fragments}
    page_citations=citations_by_page.get(pid,[])
    for c in page_citations:
        for link in c['associations']:
            link['fragment_available']=link['source_id'] in available
            total_associations+=1
            reviewed_count+=link['status']=='reviewed'
    boundary_data={}
    for name in ('start_boundary','end_boundary'):
        boundary_data[name]={k:page[name][k] for k in ['estimated_char_offset0','lower_char_offset0','upper_char_offset0','status']}
    record={'schema_version':1,'id':pid,'volume':page['printed_volume'],'page':page['printed_page'],
        'pdf_page':page['pdf_page1'],'image_index':page['pdf_page1'],'boundaries':boundary_data,
        'ocr_page_match':layout_ratio,'fragments':fragments,'ocr_lines':lines,'citations':page_citations}
    filename=f'pages/{pid}.json.gz'
    size=write(filename,record,True)
    manifest_pages.append({'id':pid,'volume':page['printed_volume'],'page':page['printed_page'],'pdf_page':page['pdf_page1'],'image_index':page['pdf_page1'],'data_file':filename,'first_source_line':fragments[0]['source_line'] if fragments else None,'last_source_line':fragments[-1]['source_line'] if fragments else None,'fragment_count':len(fragments),'citation_count':len(page_citations),'bytes':size})
    total_fragments+=len(fragments);fragment_status.update(f['ocr']['status'] for f in fragments)

assert all(source_pages[u['id']] for u in units if u['kind']=='entry')
source_index=[{'source_id':u['id'],'source_line':u['line'],'kind':u['kind'],'text':u['text'],'page_ids':source_pages[u['id']]} for u in units if source_pages[u['id']]]
for entry in source_index:
    if len(entry['page_ids']) > 1:
        entry['fragments']=source_page_fragments[entry['source_id']]
write('source-index.json.gz',source_index,True)
write('citation-index.json.gz',citation_index,True)
write('unresolved-citations.json',unresolved)
page_by_pdf={p['pdf_page']:p for p in manifest_pages}
scan_slots=[]
for m in page_map:
    p=page_by_pdf.get(m['pdf_page1'])
    scan_slots.append({'image_index':m['pdf_page1'],'kind':m['section'],'volume':m['volume'],'page':m.get('printed_page'),'page_id':p['id'] if p else None,'printed_page_status':m.get('printed_page_status')})
provenance={
 'title':'Vocabulário na Língua Brasílica',
 'digitizer':'Emerson José Silveira da Costa',
 'google_document':'https://docs.google.com/document/d/1oNYyk0gHjtP4Rm_Auemt-63DYMXLY9GgFtQ2OE2H6Ek/edit',
 'digitization_site':'https://sites.google.com/site/vocabularionalinguabrasilica/',
 'emerson_blog':'https://abanheenga.blogspot.com/p/como-aprender-tupi.html',
 'print_edition':'2ª edição revista por Carlos Drumond, 1952–1953',
 'document_revision':source_meta['document_revision'],'source_text_sha256':source_meta['text_sha256'],
 'source_retrieved_utc':source_meta.get('retrieved_utc'),
 'dictionary_repository_commit':'1d36bc8ebbb72806c6d6bd1773669481d5b910fd',
 'dictionary_snapshot_sha256':citations[0]['dictionary_snapshot_sha256'],
 'dictionary_path':'docs/dict-conjugated.json.gz',
 'dictionary_row_identity':'entry_index and legacy_id are snapshot row locators, not permanent lexical IDs.',
 'source_identity':'source_line identifies a paragraph in this saved transcription, not a printed line number.',
 'offset_convention':'source_start0/source_end0 are a half-open interval in the unchanged UTF-8 decoded source text; all characters are BMP, so 1-based UTF-16 offset equals char offset + 1.',
 'box_convention':'OCR boxes are normalized [left,top,right,bottom] relative to original PDF page extent.',
 'ocr_method':'Monotonic normalized token alignment of the page transcription to OCR lines; boxes are approximate. Score is matched source-token fraction, not probability.',
 'association_method':'Navarro-to-source paragraph links marked proposed are retrieval candidates. Page citations and OCR spelling alignment do not themselves confirm lexical equivalence.',
 'reviewed_association_scope':'Only explicitly reviewed specific citation associations can carry reviewed status; no source paragraph is marked fully covered by these links.',
 'pdf_source_metadata_file':'../source/pdf_source_metadata.json'
}
counts={'text_pages':len(manifest_pages),'scan_slots':len(scan_slots),'source_paragraphs':len(units),'lexicographic_records':sum(u['kind']=='entry' for u in units),'source_fragments':total_fragments,'citation_occurrences':len(citations),'unresolved_citations':len(unresolved),'page_citation_memberships':sum(len(v) for v in citations_by_page.values()),'proposed_associations':total_associations-reviewed_count,'reviewed_associations':reviewed_count,'ocr_fragment_status':dict(fragment_status)}
manifest={'schema_version':1,'provenance':provenance,'counts':counts,'page_order':[p['id'] for p in manifest_pages],'pages':manifest_pages,'scan_slots':scan_slots,'source_index_file':'source-index.json.gz','citation_index_file':'citation-index.json.gz','unresolved_citations_file':'unresolved-citations.json'}
write('manifest.json',manifest)
print(json.dumps({'counts':counts,'data_bytes':sum(p.stat().st_size for p in OUT.rglob('*') if p.is_file()),'source_bytes':sum(p.stat().st_size for p in SOURCE.rglob('*') if p.is_file())},ensure_ascii=False,indent=2))
