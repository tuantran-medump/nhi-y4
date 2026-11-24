import argparse
import html
from pathlib import Path
import re
import subprocess
import tempfile
from boxes import LABELS, parse_sections


def esc(s): return html.escape(s, quote=False)
def inline(s):
    s=re.sub(r'\[([A-Z]+\d*:p\d+)\]',r'<span class="src">[\1]</span>',s)
    s=s.replace('[?]','<span class="src miss">[?]</span>')
    s=re.sub(r'<span class="([nkt])">(.*?)</span>',lambda m:'<span class="'+m.group(1)+'">'+esc(m.group(2))+'</span>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',s)
    return re.sub(r'(<span class="(?:src(?: miss)?|n|k|t)">.*?</span>|<b>.*?</b>)|([&<>])',lambda m:m.group(1) or {'&':'&amp;','<':'&lt;','>':'&gt;'}[m.group(2)],s)

def render(md, style):
    if style not in ('warm','clean','screen'): raise SystemExit('style must be warm, clean, or screen')
    sections=parse_sections(md); lines=md.splitlines(); title=next((x[2:].strip() for x in lines if x.startswith('# ')),'')
    first=next((i for i,x in enumerate(lines) if x.startswith('## ')),len(lines)); sub=' '.join(x.strip() for x in lines[1:first] if x.strip())
    out=['<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>'+inline(title)+'</title><link rel="stylesheet" href="../styles/'+style+'.css"></head><body class="style-'+style+'"><header><h1>'+inline(title)+'</h1><div class="sub">'+inline(sub)+'</div></header><div class="cols">']
    for sec in sections:
        if sec.level == 0: continue
        out.append('<section class="bx '+sec.box+'"><h2>'+inline(sec.title)+'<span class="kick">'+esc(LABELS[sec.box])+'</span></h2>')
        i=0
        while i<len(sec.lines):
            line=sec.lines[i]
            if not line.strip(): i+=1; continue
            if line.lstrip().startswith('|'):
                rows=[]
                while i<len(sec.lines) and sec.lines[i].lstrip().startswith('|'):
                    cells=[x.strip() for x in sec.lines[i].strip().strip('|').split('|')]; rows.append(cells); i+=1
                head=len(rows)>1 and all(re.fullmatch(r':?-{3,}:?',c) for c in rows[1])
                out.append('<table>')
                for ri,row in enumerate(rows):
                    if ri==1 and head: continue
                    tag='th' if head and ri==0 else 'td'; out.append('<tr>'+''.join('<'+tag+'>'+inline(c)+'</'+tag+'>' for c in row)+'</tr>')
                out.append('</table>'); continue
            if re.match(r'^\s*- ',line):
                items=[]
                while i<len(sec.lines) and re.match(r'^\s*- ',sec.lines[i]):
                    l=sec.lines[i]; d=len(l)-len(l.lstrip()); items.append((d,l.strip()[2:])); i+=1
                def list_html(start, depth):
                    result=['<ul>']; j=start
                    while j<len(items) and items[j][0]==depth:
                        text=items[j][1]; trap=text.startswith('!bay '); result.append('<li'+(' class="trap"' if trap else '')+'>'+inline(text[5:] if trap else text)); j+=1
                        if j<len(items) and items[j][0]>depth:
                            nested,j=list_html(j,items[j][0]); result.extend([nested,'</li>'])
                        else: result.append('</li>')
                    result.append('</ul>'); return ''.join(result),j
                out.append(list_html(0,items[0][0])[0]); continue
            out.append('<p>'+inline(line.strip())+'</p>'); i+=1
        out.append('</section>')
    return '\n'.join(out+['</div></body></html>'])

def main():
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--style',choices=['warm','clean','screen'],required=True); p.add_argument('--out',required=True); p.add_argument('--pdf',action='store_true'); a=p.parse_args()
    src=Path(a.input); dest=Path(a.out); dest.mkdir(parents=True,exist_ok=True); stem=src.stem+'-'+a.style
    target=dest/(stem+'.html'); target.write_text(render(src.read_text(encoding='utf-8'),a.style),encoding='utf-8',newline='\n')
    if a.pdf:
        edge=Path(r'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
        if not edge.is_file(): raise SystemExit(f'Edge executable not found: {edge}')
        with tempfile.TemporaryDirectory(prefix='cheatsheet-edge-') as profile:
            r=subprocess.run([str(edge),'--headless','--print-to-pdf='+str((dest/(stem+'.pdf')).resolve()),'--no-pdf-header-footer','--no-first-run','--disable-gpu','--user-data-dir='+profile,'--allow-file-access-from-files',target.resolve().as_uri()],capture_output=True,text=True)
            if r.returncode or not (dest/(stem+'.pdf')).is_file(): raise SystemExit('Edge PDF generation failed: '+r.stderr)
if __name__=='__main__': main()
