import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path


SOURCE_RE = re.compile(r"^\[[A-Z]+\d*:p\d+\]$")
RELATIONS = {"approach": {"bieu_hien", "phan_biet_voi", "xu_tri_phan_biet", "khi_cls_kho_phan_biet"},
             "dxtx": {"la_the_cua", "dieu_tri", "bien_chung"}}


def read_rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


REL_LABEL = {"bieu_hien": "biểu hiện", "phan_biet_voi": "cần phân biệt", "xu_tri_phan_biet": "cách phân biệt",
             "khi_cls_kho_phan_biet": "nếu CLS khó phân biệt", "la_the_cua": "thể", "dieu_tri": "điều trị",
             "bien_chung": "biến chứng", "la_nguyen_nhan_cua": "nguyên nhân", "la_benh_nen_cua": "bệnh nền",
             "yeu_to_khoi_phat": "khởi phát"}


def mermaid_quote(value):
    return '"' + value.replace('"', r'\"').replace("\n", " ") + '"'


def generate(kb, root, kind, out):
    entities = {r["id"]: r for r in read_rows(kb / "entities.csv")}
    edges = read_rows(kb / "edges.csv")
    names = {key: row["ten"] for key, row in entities.items()}
    relevant = [e for e in edges if e["quan_he"] in RELATIONS[kind] and (e["tu"] == root or e["den"] == root)]
    if kind == "approach":
        peers = {e["den"] if e["tu"] == root else e["tu"] for e in edges if e["quan_he"] == "phan_biet_voi" and root in (e["tu"], e["den"])}
        relevant += [e for e in edges if e["quan_he"] in {"xu_tri_phan_biet", "khi_cls_kho_phan_biet"} and (e["tu"] == root or e["tu"] in peers)]
    else:
        variants = {e["tu"] for e in edges if e["quan_he"] == "la_the_cua" and e["den"] == root}
        complications = {e["den"] for e in edges if e["quan_he"] == "bien_chung" and e["tu"] == root}
        relevant += [e for e in edges if e["quan_he"] == "dieu_tri" and e["tu"] in variants | complications | {root}]
    seen = set()
    relevant = [e for e in relevant if not ((e["tu"], e["quan_he"], e["den"], e["nguon"]) in seen or seen.add((e["tu"], e["quan_he"], e["den"], e["nguon"]))) ]
    valid, gaps = [], []
    for edge in relevant:
        if not SOURCE_RE.fullmatch(edge["nguon"]):
            gaps.append({"tu": edge["tu"], "quan_he": edge["quan_he"], "den": edge["den"], "ly_do": "nguon rỗng" if not edge["nguon"] else f"nguon sai định dạng: {edge['nguon']}"})
        elif edge["tu"] in entities and edge["den"] in entities:
            valid.append(edge)
    if root not in entities:
        raise ValueError(f"Không tìm thấy thực thể gốc: {root}")
    if kind == "approach" and any(e["quan_he"] == "khi_cls_kho_phan_biet" and e["tu"] == root for e in edges) and not any(e["quan_he"] == "khi_cls_kho_phan_biet" and e["tu"] == root for e in valid):
        raise ValueError("Thiếu nhánh khi cận lâm sàng khó phân biệt: cạnh KB có nguồn không hợp lệ hoặc đích không tồn tại")

    node_sources = defaultdict(list)
    for e in valid:
        node_sources[e["tu"]].append(e["nguon"])
        node_sources[e["den"]].append(e["nguon"])
    node_sources[root]  # force initialization
    labels = {i: f"{names[i]} {node_sources[i][0]}" for i in node_sources if i in names and node_sources[i]}
    # Root-only KBs still get a source from an eligible edge if available.
    if root not in labels:
        raise ValueError("Thực thể gốc không có cạnh có nguồn hợp lệ để gắn mã")

    out.mkdir(parents=True, exist_ok=True)
    safe_name = re.sub(r'[<>:"/\\|?*]', "_", names[root]).rstrip(" .") or root.replace(":", "_")
    stem = f"{safe_name}-{kind}"
    ids = {key: f"n{i}" for i, key in enumerate(labels)}
    lines = ["flowchart TD"]
    for key, label in labels.items():
        lines.append(f"  {ids[key]}[{mermaid_quote(label)}]")
    for edge in valid:
        if edge["tu"] not in ids or edge["den"] not in ids:
            continue
        source, target = ((edge["den"], edge["tu"]) if kind == "dxtx" and edge["quan_he"] == "la_the_cua" else (edge["tu"], edge["den"]))
        lines.append(f"  {ids[source]} -->|{mermaid_quote(REL_LABEL.get(edge['quan_he'], edge['quan_he']) + ' ' + edge['nguon'])}| {ids[target]}")
    (out / f"{stem}.mmd").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    children = defaultdict(list)
    for edge in valid:
        if kind == "dxtx" and edge["quan_he"] == "la_the_cua" and edge["den"] == root and edge["tu"] in labels:
            children[root].append((edge["tu"], edge["nguon"], edge["quan_he"]))
        elif edge["tu"] in labels and edge["den"] in labels:
            children[edge["tu"]].append((edge["den"], edge["nguon"], edge["quan_he"]))
    md = [f"# {labels[root]}"]
    if kind == "approach":
        md.append("## Các biểu hiện chính")
        for target, source, rel in children[root]:
            if rel == "bieu_hien": md.append(f"- {names[target]} {source}")
        md.append("## Phân biệt")
        for peer, source, rel in children[root]:
            if rel != "phan_biet_voi": continue
            md.append(f"- {names[peer]} {source}")
            for target, action_source, action_rel in children[peer]:
                if action_rel == "xu_tri_phan_biet": md.append(f"  - {names[target]} {action_source}")
        for target, source, rel in children[root]:
            if rel == "xu_tri_phan_biet": md.append(f"- {names[target]} {source}")
        md.append("## Nếu cận lâm sàng khó phân biệt thì làm gì")
        for target, source, rel in children[root]:
            if rel == "khi_cls_kho_phan_biet": md.append(f"- {names[target]} {source}")
    else:
        for rel_title, relation in (("Các thể", "la_the_cua"), ("Điều trị", "dieu_tri"), ("Biến chứng", "bien_chung")):
            md.append(f"## {rel_title}")
            if relation == "la_the_cua":
                for variant, source, rel in children[root]:
                    if rel == relation:
                        md.append(f"- {names[variant]} {source}")
                        for target, treatment_source, treatment_rel in children[variant]:
                            if treatment_rel == "dieu_tri": md.append(f"  - {names[target]} {treatment_source}")
            elif relation == "dieu_tri":
                for target, source, rel in children[root]:
                    if rel == relation: md.append(f"- {names[target]} {source}")
            else:
                for comp, source, rel in children[root]:
                    if rel == relation:
                        md.append(f"- {names[comp]} {source}")
                        for target, treatment_source, treatment_rel in children[comp]:
                            if treatment_rel == "dieu_tri": md.append(f"  - {names[target]} {treatment_source}")
    (out / f"{stem}.md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    with (out / f"{stem}-gaps.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("tu", "quan_he", "den", "ly_do"), lineterminator="\n")
        writer.writeheader(); writer.writerows(gaps)
    return len(labels), len([e for e in valid if e["tu"] in ids and e["den"] in ids]), len(gaps), gaps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("kb", type=Path)
    parser.add_argument("--root", required=True)
    parser.add_argument("--kind", choices=("approach", "dxtx"), required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        nodes, edges, gaps, reasons = generate(args.kb, args.root, args.kind, args.out)
    except (OSError, csv.Error, KeyError, ValueError) as exc:
        print(exc, file=sys.stderr); return 1
    print(f"Nút: {nodes}; cạnh: {edges}; gaps: {gaps}")
    for reason in sorted({g["ly_do"] for g in reasons}): print(f"  {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
