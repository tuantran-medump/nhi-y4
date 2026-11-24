import argparse
from html.parser import HTMLParser
from pathlib import Path
import re

class Text(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.skips=[]; self.parts=[]
    def handle_starttag(self,tag,attrs):
        c=dict(attrs).get('class','').split()
        if tag in ('head','title','style','script') or 'kick' in c or 'src' in c or (tag=='div' and 'sub' in c): self.skips.append(tag)
        elif tag in ('p','li','tr','h1','h2','td','th'): self.parts.append(' ')
    def handle_endtag(self,tag):
        if self.skips and self.skips[-1]==tag: self.skips.pop()
        elif tag in ('p','li','tr','h1','h2','td','th'): self.parts.append(' ')
    def handle_data(self,data):
        if not self.skips: self.parts.append(data)
def plain_text(s):
    p=Text(); p.feed(s); return re.sub(r'\s+',' ',''.join(p.parts)).strip()
def main():
    p=argparse.ArgumentParser(); p.add_argument('original'); p.add_argument('built'); a=p.parse_args(); x=plain_text(Path(a.original).read_text(encoding='utf-8')); y=plain_text(Path(a.built).read_text(encoding='utf-8'))
    if x!=y:
        i=next((i for i,(c,d) in enumerate(zip(x,y)) if c!=d),min(len(x),len(y))); print(f'Different near: original={x[max(0,i-40):i+80]!r}; built={y[max(0,i-40):i+80]!r}'); raise SystemExit(1)
    print('Text matches')
if __name__=='__main__': main()
