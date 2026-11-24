import argparse
import json
from html.parser import HTMLParser
from pathlib import Path
import re


class Node:
    def __init__(self, tag='', attrs=()): self.tag, self.attrs, self.children = tag, dict(attrs), []
    def text(self): return ''.join(x.text() if isinstance(x, Node) else x for x in self.children)


class Tree(HTMLParser):
    def __init__(self): super().__init__(convert_charrefs=True); self.root = Node('root'); self.stack = [self.root]
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs); self.stack[-1].children.append(n)
        if tag not in {'br','hr','img','meta','link','input'}: self.stack.append(n)
    def handle_startendtag(self, tag, attrs): self.stack[-1].children.append(Node(tag, attrs))
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, 0, -1):
            if self.stack[i].tag == tag: del self.stack[i:]; break
    def handle_data(self, data): self.stack[-1].children.append(data)


def inline(n):
    if isinstance(n, str): return n
    tag = n.tag
    body = ''.join(inline(c) for c in n.children)
    if tag in ('b','strong'): return '**' + body + '**'
    if tag == 'span' and n.attrs.get('class') in ('n','k','t'): return f'<span class="{n.attrs["class"]}">{body}</span>'
    return body


def convert(source, box_map=None):
    p = Tree(); p.feed(source); root = p.root
    def find(n, tag=None, cls=None):
        for x in n.children:
            if isinstance(x, Node):
                if (tag is None or x.tag == tag) and (cls is None or cls in x.attrs.get('class','').split()): yield x
                yield from find(x, tag, cls)
    out=[]; h1=next(find(root,'h1'),None)
    if h1: out.append('# '+inline(h1).strip())
    sub=next(find(root,'div','sub'),None)
    if sub: out.extend(['',inline(sub).strip()])
    cols=next(find(root,'div','cols'),root)
    mapping = box_map or {}
    if isinstance(box_map, (str,Path)): mapping=json.loads(Path(box_map).read_text(encoding='utf-8'))
    for sec in (x for x in cols.children if isinstance(x,Node) and x.tag=='section'):
        heading=next((x for x in sec.children if isinstance(x,Node) and x.tag=='h2'),None)
        if not heading:
            if 'ans' in sec.attrs.get('class','').split(): out.extend(['',inline(sec).strip()])
            continue
        title=heading.text().strip(); out.extend(['','## '+inline(heading).strip()])
        if title in mapping: out.append('{hop: '+mapping[title]+'}')
        for el in sec.children:
            if not isinstance(el,Node) or el is heading: continue
            if el.tag=='ul':
                def emit_ul(ul, depth):
                    for li in (c for c in ul.children if isinstance(c,Node) and c.tag=='li'):
                        nested=next((c for c in li.children if isinstance(c,Node) and c.tag=='ul'),None)
                        parts=''.join(inline(c) for c in li.children if c is not nested).strip()
                        trap='trap' in li.attrs.get('class','').split() or (len(li.children)==1 and isinstance(li.children[0],Node) and li.children[0].tag=='span' and li.children[0].attrs.get('class')=='t')
                        parts=re.sub(r'^<span class="t">(.*?)</span>$',r'\1',parts)
                        out.append('  '*depth+'- '+('!bay ' if trap else '')+parts)
                        if nested: emit_ul(nested,depth+1)
                emit_ul(el,0)
            elif el.tag=='table':
                rows=list(find(el,'tr')); has_th=any(list(find(r,'th')) for r in rows)
                for i,row in enumerate(rows):
                    cells=[c for c in row.children if isinstance(c,Node) and c.tag in ('th','td')]
                    out.append('| '+' | '.join(inline(c).strip() for c in cells)+' |')
                    if has_th and i==0: out.append('|'+'|'.join('---' for _ in cells)+'|')
            elif el.tag=='p': out.append(inline(el).strip())
        loose=''.join(inline(c) for c in sec.children if c is not heading and not (isinstance(c,Node) and c.tag in ('ul','table','p'))).strip()
        if loose: out.append(loose)
    return '\n'.join(out).strip()+'\n'


def main():
    a=argparse.ArgumentParser(); a.add_argument('input'); a.add_argument('output'); a.add_argument('--box-map'); x=a.parse_args()
    Path(x.output).parent.mkdir(parents=True,exist_ok=True)
    Path(x.output).write_text(convert(Path(x.input).read_text(encoding='utf-8'),x.box_map),encoding='utf-8',newline='\n')
if __name__=='__main__': main()
