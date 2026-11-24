import argparse
import re
from pathlib import Path
from boxes import parse_sections

SRC=re.compile(r'\[[A-Z]+\d*:p\d+\]')
def inspect(md):
    count=missing=0; lacks=0; misses=[]
    for no,line in enumerate(md.splitlines(),1):
        if '[?]' in line: misses.append((no,line))
    for section in parse_sections(md):
        for index,line in enumerate(section.lines):
            if line.lstrip().startswith('|') and index+1<len(section.lines) and section.lines[index+1].lstrip().startswith('|') and all(re.fullmatch(r':?-{3,}:?', c.strip()) for c in section.lines[index+1].strip().strip('|').split('|')):
                continue
            if line.lstrip().startswith('- ') or (line.lstrip().startswith('|') and not all(re.fullmatch(r':?-{3,}:?', c.strip()) for c in line.strip().strip('|').split('|'))):
                count+=1
                if SRC.search(line): missing+=1
                else: lacks+=1
    return {'with_source':count-lacks,'without_source':lacks,'missing':misses}
def main():
    p=argparse.ArgumentParser(); p.add_argument('input'); p.add_argument('--strict',action='store_true'); a=p.parse_args(); r=inspect(Path(a.input).read_text(encoding='utf-8'))
    print(f"Có nguồn: {r['with_source']}; không có nguồn: {r['without_source']}")
    for n,line in r['missing']: print(f'{n}: {line}')
    if a.strict and (r['missing'] or r['without_source']): raise SystemExit(1)
if __name__=='__main__': main()
