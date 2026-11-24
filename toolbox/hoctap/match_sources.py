import json
import re
from pathlib import Path

SRC = re.compile(r'\[([A-Z]+\d*:p\d+)\]')
TAG = re.compile(r'<span class="([nkt])">(.*?)</span>', re.I)
HTML = re.compile(r'<[^>]+>')
STOP = {'hoặc','trong','khi','được','với','theo','một','các','cho','này','đến','sau','trước','là','của','và','hay','nếu','thì','từ','để','do','có','không','nên','phát','thường','tuổi','ngày','trẻ','bệnh','nhất','mắc','liên','tiếp','tháng','gặp','đáp','ứng','lần','đầu','thuốc','dùng','điều','trị','làm','sử','dụng','thận','đạm','niệu','tối','chuyển'}
NUMBER = re.compile(r'(?<![\w])(?:[<>≤≥]=?\s*)?\d+(?:[,.]\d+)*(?:\s*[–—−-]\s*\d+(?:[,.]\d+)*(?:\s*(?:%|‰|mg|g|kg|mm|mL|ml|L|dL|mmol|m²|m³|tuổi|tháng|tuần|ngày|giờ|năm))?)?(?::\d+(?::\d+)*)?(?:\s*(?:%|‰|mg|g|kg|mm|mL|ml|L|dL|mmol|m²|m³|tuổi|tháng|tuần|ngày|giờ|năm|/\w+|\.\w+))*(?!\s*[–—−-]\s*\d)', re.I)
UNIT = re.compile(r'[%‰:]|\b(?:mg|kg|mmol|tuổi|tháng|tuần|ngày|giờ|năm)\b|/|\.', re.I)


def norm(s):
    return re.sub(r'\s+', ' ', HTML.sub(' ', s).replace('**', '').lower().replace('≥', '>=').replace('≤', '<=').replace('–', '-').replace('—', '-').replace('−', '-')).strip()


def terms(s):
    words = re.findall(r'[^\W\d_]{3,}', norm(s), re.UNICODE)
    return set(w for w in words if w not in STOP)


def phrase_run(item, line):
    a = re.findall(r'[^\W\d_]+', norm(item), re.UNICODE)
    b = re.findall(r'[^\W\d_]+', norm(line), re.UNICODE)
    best, previous = 0, [(0, 0)] * (len(b) + 1)
    for word in a:
        current = [(0, 0)]
        for j, other in enumerate(b, 1):
            if word == other:
                length, count = previous[j - 1]
                count += len(word) >= 4 and word not in STOP
                current.append((length + 1, count))
                best = max(best, count)
            else:
                current.append((0, 0))
        previous = current
    return best


def numeric_evidence(item, line):
    a, b = norm(item), norm(line)
    found = []
    for m in NUMBER.finditer(a):
        token = re.sub(r'\s+', '', m.group()).replace(',', '.').replace('>=', '>=').replace('<=', '<=')
        short = not UNIT.search(m.group()) and re.fullmatch(r'\d{1,2}(?:-\d{1,2})?', token)
        if short:
            if len(terms(item) & terms(line)) < 2:
                continue
        elif len(re.sub(r'\D', '', token)) < 3 and not UNIT.search(m.group()):
            continue
        # Exact complete token only; punctuation around it is harmless.
        if re.search(r'(?<![\w.,\d–—−-])(?<!- )' + re.escape(m.group().strip()).replace(r'\ ', r'\s*') + r'(?![\w])', b):
            found.append(token)
    return list(dict.fromkeys(found))


def split_cells(line):
    return [x.strip() for x in line.strip().strip('|').split('|')]


def items(md):
    lines, found, in_self = md.splitlines(), [], False
    for i, line in enumerate(lines):
        if line.startswith('## '): in_self = 'tu-kiem-tra' in line.lower() or 'tự kiểm tra' in line.lower()
        if in_self: continue
        if re.match(r'^\s*- ', line):
            found.append({'line': i+1, 'raw': line, 'kind': 'li'})
        elif line.lstrip().startswith('|'):
            if re.fullmatch(r'\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?', line.strip()): continue
            found.append({'line': i+1, 'raw': line, 'kind': 'row'})
    return found


def match(md, body):
    body_lines, updated, records = body.splitlines(), md.splitlines(), []
    for item in items(md):
        raw = re.sub(r'\s*(?:\[(?:[A-Z]+\d*:p\d+|\?)\]\s*)+$', '', item['raw']).rstrip()
        kparts = [m.group(2) for m in TAG.finditer(raw) if m.group(1).lower() == 'k']
        plain = TAG.sub(lambda m: ' ' if m.group(1).lower() == 'k' else m.group(2), raw)
        pt, candidates = terms(plain), []
        first_number = next((re.sub(r'\s+', '', m.group()).replace(',', '.') for m in NUMBER.finditer(norm(plain))), None)
        for no, line in enumerate(body_lines, 1):
            trailing = re.search(r'((?:\s*\[[A-Z]+\d*:p\d+\])+\s*[.!?]?\s*)$', line)
            codes = SRC.findall(trailing.group(1)) if trailing else []
            if not codes: continue
            clean = SRC.sub('', line)
            if re.match(r'^\s*\d+\.\s', clean): continue
            overlap = pt & terms(clean)
            run = phrase_run(plain, clean)
            nums = numeric_evidence(plain, clean)
            if NUMBER.search(norm(plain)) and not nums: continue
            score = len(nums) * 10 + len(overlap)
            if score:
                strong_num = any('%' in n or '‰' in n or re.search(r'\d-\d', n) or re.search(r'/(?:kg|m²|mmol|100)', n) for n in nums)
                confidence = 'cao' if len(nums) >= 2 or run >= 3 else 'vua' if nums and (len(overlap) >= 2 or strong_num) else 'thap'
                if not overlap and run < 3: confidence = 'thap'
                candidates.append({'codes': codes, 'body_line': no, 'score': score, 'confidence': confidence, 'excerpt': line[:80], 'k': False, 'matched_terms': len(overlap), 'run': run, 'numbers': nums, 'first_number': bool(nums and nums[0] == first_number)})
            for part in kparts:
                knums, k_overlap = numeric_evidence(part, clean), len(terms(part) & terms(clean))
                krun = phrase_run(part, clean)
                if NUMBER.search(norm(part)) and not knums: continue
                if knums or krun >= 2:
                    kscore = len(knums) * 10 + k_overlap
                    kconfidence = 'cao' if len(knums) >= 2 or krun >= 3 else 'vua'
                    candidates.append({'codes': codes, 'body_line': no, 'score': kscore, 'confidence': kconfidence, 'excerpt': line[:80], 'k': True, 'matched_terms': k_overlap, 'run': krun, 'numbers': knums, 'first_number': bool(knums and knums[0] == first_number)})
        candidates.sort(key=lambda c: (c['first_number'], c['run'], c['score'], len(c['numbers']), c['matched_terms'], -c['body_line']), reverse=True)
        chosen, matched, best_conf = [], [], 'thap'
        best = next((c for c in candidates if not c['k'] and c['confidence'] != 'thap' and any(x.startswith('G1:') for x in c['codes'])), None)
        if best:
            chosen = [x for x in best['codes'] if x.startswith('G1:')][:3]
            matched, best_conf = [best['body_line']], best['confidence']
        kbest = next((c for c in candidates if c['k'] and c['confidence'] != 'thap' and any(not x.startswith('G1:') for x in c['codes'])), None)
        if kbest:
            external = next(x for x in kbest['codes'] if not x.startswith('G1:'))
            if external not in chosen and len(chosen) < 3: chosen.append(external)
            if kbest['body_line'] not in matched: matched.append(kbest['body_line'])
            if not best: best_conf = kbest['confidence']
        marker = ' '.join(f'[{c}]' for c in chosen) if chosen and best_conf != 'thap' else '[?]'
        if marker == '[?]': chosen, matched, best_conf = [], [], 'thap'
        if item['kind'] == 'li': updated[item['line']-1] = raw + ' ' + marker
        else:
            cells = split_cells(raw); cells[-1] = cells[-1].rstrip() + ' ' + marker
            updated[item['line']-1] = '| ' + ' | '.join(cells) + ' |'
        records.append({'line': item['line'], 'text': raw[:120], 'codes': chosen, 'confidence': best_conf, 'score': candidates[0]['score'] if candidates else 0, 'matched_body_lines': sorted(set(matched)), 'candidates': [{'code': code, 'body_line': c['body_line'], 'score': c['score'], 'confidence': c['confidence'], 'excerpt': c['excerpt']} for c in candidates[:2] for code in c['codes']]})
    return '\n'.join(updated) + '\n', records


def main():
    root = Path(__file__).parent
    source, backup = root/'content/HCTH.md', root/'content/HCTH.nosrc.md'
    body = Path('C:/Users/Admin/orca/nhi-y4/toolbox/kho/lessons/G1-B13/body.md')
    result, records = match(backup.read_text(encoding='utf-8'), body.read_text(encoding='utf-8'))
    source.write_text(result, encoding='utf-8', newline='\n')
    (root/'content/HCTH.sources.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


if __name__ == '__main__': main()
