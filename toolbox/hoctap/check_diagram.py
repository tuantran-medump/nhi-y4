import argparse
import csv
import re
import sys
from pathlib import Path


SOURCE_RE = re.compile(r"\[([A-Z]+\d*:p\d+)\]")
FIXED_LABELS = {
    "Các biểu hiện chính", "Phân biệt", "Nếu cận lâm sàng khó phân biệt thì làm gì",
    "Các thể", "Điều trị", "Biến chứng",
}


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def check(diagram, kb, kind=None):
    errors = []
    lines = diagram.read_text(encoding="utf-8").splitlines()
    entities = {row["ten"] for row in read_rows(kb / "entities.csv")}
    edges = read_rows(kb / "edges.csv")
    known_sources = {e["nguon"].strip("[]") for e in edges if SOURCE_RE.fullmatch(e["nguon"])}
    labels = []
    sources = set()
    root_label = None
    node_ids = {}
    if diagram.suffix.lower() == ".mmd":
        for n, line in enumerate(lines, 1):
            if line.strip() == "flowchart TD":
                continue
            node = re.search(r"\b\w+\s*\[\s*\"((?:\\.|[^\"])*)\"\s*\]", line)
            if node:
                value = node.group(1).replace(r'\"', '"')
                match = SOURCE_RE.search(value)
                label = SOURCE_RE.sub("", value).strip()
                labels.append((n, label, match.group(0) if match else ""))
                node_ids[(label, match.group(0) if match else "")] = re.search(r"\b(\w+)\s*\[", line).group(1)
                root_label = root_label or label
            edge = re.search(r"-->\|\s*\"?([^|\"]+)\"?\s*\|", line)
            if edge:
                match = SOURCE_RE.search(edge.group(1))
                if not match: errors.append(f"dòng {n}: cạnh thiếu mã nguồn")
                else: sources.add(match.group(1))
            elif "-->" in line:
                errors.append(f"dòng {n}: cạnh thiếu mã nguồn")
    else:
        for n, line in enumerate(lines, 1):
            content = line.strip().lstrip("#*- ").strip()
            if not content: continue
            match = SOURCE_RE.search(content)
            label = SOURCE_RE.sub("", content).strip()
            if label in FIXED_LABELS:
                continue
            labels.append((n, label, match.group(0) if match else ""))
            root_label = root_label or label
            if not match:
                errors.append(f"dòng {n}: thiếu mã nguồn")
            else:
                sources.add(match.group(1))
    for n, label, citation in labels:
        if not citation:
            errors.append(f"dòng {n}: nút thiếu mã nguồn")
        if label not in entities and label not in FIXED_LABELS:
            errors.append(f"dòng {n}: nhãn không có trong KB: {label}")
    for source in sorted(sources - known_sources):
        errors.append(f"mã nguồn [{source}] không thuộc cạnh nào trong KB")
    if kind == "approach" and root_label:
        root_ids = {row["id"] for row in read_rows(kb / "entities.csv") if row["ten"] == root_label}
        for root in root_ids:
            hard = [e for e in edges if e["tu"] == root and e["quan_he"] == "khi_cls_kho_phan_biet"]
            if diagram.suffix.lower() == ".mmd":
                root_node = next((node_id for (label, _), node_id in node_ids.items() if label == root_label), None)
                present = any(
                    (target := next((row["ten"] for row in read_rows(kb / "entities.csv") if row["id"] == e["den"]), None))
                    and (target_node := next((node_id for (label, _), node_id in node_ids.items() if label == target), None))
                    and f'{root_node} -->|"{e["nguon"]}"| {target_node}' in "\n".join(lines)
                    for e in hard
                )
            else:
                start = next((i for i, line in enumerate(lines) if line.strip() == "## Nếu cận lâm sàng khó phân biệt thì làm gì"), len(lines))
                end = next((i for i in range(start + 1, len(lines)) if lines[i].lstrip().startswith("## ")), len(lines))
                branch = "\n".join(lines[start:end])
                present = any(
                    any(row["id"] == e["den"] and f'{row["ten"]} {e["nguon"]}' in branch for row in read_rows(kb / "entities.csv"))
                    for e in hard
                )
            if hard and not present:
                errors.append("sơ đồ thiếu nhánh khó phân biệt")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("diagram", type=Path)
    parser.add_argument("--kb", required=True, type=Path)
    parser.add_argument("--kind", choices=("approach", "dxtx"))
    args = parser.parse_args()
    try:
        errors = check(args.diagram, args.kb, args.kind)
    except (OSError, csv.Error, KeyError) as exc:
        print(exc); return 1
    if errors:
        print("\n".join(errors)); return 1
    print("OK"); return 0


if __name__ == "__main__":
    raise SystemExit(main())
