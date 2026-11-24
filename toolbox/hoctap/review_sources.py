import argparse
import csv
import json
import re
from pathlib import Path


def load_links(path):
    with path.open(encoding='utf-8', newline='') as f:
        return {row['code']: row['url'] for row in csv.DictReader(f)}


def render(md, records, links, body_lines):
    rows = ['| # | Dòng HCTH.md | Ý (70 ký tự) | Mã / ứng viên | Độ tin | Đối chiếu body.md |', '|---:|---:|---|---|---|---|']
    for i, record in enumerate(records, 1):
        text = re.sub(r'\s*(?:\[(?:[A-Z]+\d*:p\d+|\?)\]\s*)+$', '', record['text']).replace('|', r'\|')[:70]
        selected = record['codes']
        refs = []
        if selected:
            codes = [(code, next((c for c in record['candidates'] if c['code'] == code), None)) for code in selected]
        else:
            codes = [(c['code'], c) for c in record['candidates'][:2]]
        for code, candidate in codes:
            page = code.split(':p')[-1]
            key = re.match(r'[A-Z]+\d*', code).group()
            label = f'[{key}]({links[key]}) trang {page}' if key in links else f'{code} — chưa có link'
            excerpt = candidate['excerpt'].replace('|', r'\|') if candidate else ''
            refs.append(f'{label}: {excerpt}')
        if not refs: refs = ['[?]']
        matched_rows = []
        for n in record['matched_body_lines']:
            excerpt = body_lines[n-1][:80].replace('|', '\\|')
            matched_rows.append(f'dòng {n}: {excerpt}')
        matched = '; '.join(matched_rows)
        if not matched: matched = 'Ứng viên: ' + ' / '.join(refs)
        rows.append(f"| {i} | {record['line']} | {text} | {'; '.join(refs)} | {record['confidence']} | {matched} |")
    return '\n'.join(rows) + '\n'


def main():
    root = Path(__file__).parent
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=root/'content/HCTH.md')
    parser.add_argument('--sources', type=Path, default=root/'content/HCTH.sources.json')
    parser.add_argument('--body', type=Path, default=Path('C:/Users/Admin/orca/nhi-y4/toolbox/kho/lessons/G1-B13/body.md'))
    parser.add_argument('--links', type=Path, default=Path('C:/Users/Admin/orca/nhi-y4/toolbox/data/drive_links.csv'))
    parser.add_argument('--out', type=Path, default=root/'content/HCTH.review.md')
    a = parser.parse_args()
    a.out.write_text(render(a.input.read_text(encoding='utf-8'), json.loads(a.sources.read_text(encoding='utf-8')), load_links(a.links), a.body.read_text(encoding='utf-8').splitlines()), encoding='utf-8', newline='\n')


if __name__ == '__main__': main()
