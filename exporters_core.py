
from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    import yaml  # optional
except Exception:
    yaml = None

_EXPORTERS: Dict[str, "BaseExporter"] = {}

def exporter(cls):
    inst = cls()
    _EXPORTERS[inst.name] = inst
    return cls

class Row:
    def __init__(self, data: Dict[str, Any]):
        self.data = data
    def get(self, key: str, default: str = "") -> str:
        v = self.data.get(key, default)
        return "" if v is None else str(v)

class BaseExporter:
    name: str = "base"
    def headers(self) -> List[str]:
        raise NotImplementedError
    def export_row(self, row: Row, cfg: Dict[str, Any]) -> List[Any]:
        raise NotImplementedError
    def export(self, rows: List[Row], out_path: Path, cfg: Dict[str, Any]) -> Path:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(self.headers())
            for r in rows:
                w.writerow(self.export_row(r, cfg))
        return out_path

def ensure_ai_keyword(keywords: str) -> str:
    toks = [t.strip() for t in (keywords or "").split(",") if t.strip()]
    has_ai = any(t.lower() == "_ai_generated" for t in toks)
    if not has_ai:
        toks.insert(0, "_ai_generated")
    return ", ".join(toks)

def load_yaml_config(path: Optional[Path]) -> Dict[str, Any]:
    if not path:
        return {}
    if not path.exists():
        return {}
    if yaml is None:
        return {}
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}

@exporter
class AdobeStockExporter(BaseExporter):
    name = "adobestock"
    def headers(self) -> List[str]:
        return ["Filename", "Title", "Keywords", "Category ID", "Releases"]
    def export_row(self, row: Row, cfg: Dict[str, Any]) -> List[Any]:
        return [
            row.get("Filename"),
            row.get("Title"),
            row.get("Keywords"),
            row.get("Category ID"),
            row.get("Releases")
        ]

@exporter
class FreepikExporter(BaseExporter):
    name = "freepik"
    def headers(self) -> List[str]:
        return ["filename", "title", "keywords"]
    def export_row(self, row: Row, cfg: Dict[str, Any]) -> List[Any]:
        mark_ai = bool(cfg.get("freepik", {}).get("mark_ai_keyword", True))
        filename = row.get("Filename")
        title    = row.get("Title")
        keywords = row.get("Keywords")
        if mark_ai:
            keywords = ensure_ai_keyword(keywords)
        return [filename, title, keywords]

@exporter
class DreamstimeExporter(BaseExporter):
    name = "dreamstime"
    def headers(self) -> List[str]:
        return [
            "Filename", "Image Name", "Description",
            "Category 1", "Category 2", "Category 3",
            "keywords", "Free", "W-EL", "P-EL", "SR-EL", "SR-Price", "Editorial",
            "MR doc Ids", "Pr Docs"
        ]
    def _infer_cat2_cat3(self, row: Row, cfg: Dict[str, Any]) -> (str, str):
        c2 = row.get("DT_Category2")
        c3 = row.get("DT_Category3")
        if c2 or c3:
            return c2, c3
        cat_map = cfg.get("dreamstime", {}).get("adobe_to_dt_map", {})
        adobe_cat_id = row.get("Category ID").strip()
        if adobe_cat_id and adobe_cat_id in cat_map:
            mapped = cat_map[adobe_cat_id]
            if isinstance(mapped, dict):
                return str(mapped.get("c2", "") or ""), str(mapped.get("c3", "") or "")
            if isinstance(mapped, (list, tuple)):
                m2 = str(mapped[0]) if len(mapped) > 0 and mapped[0] else ""
                m3 = str(mapped[1]) if len(mapped) > 1 and mapped[1] else ""
                return m2, m3
        return "", ""
    def export_row(self, row: Row, cfg: Dict[str, Any]) -> List[Any]:
        defaults = { "Free": 0, "W-EL": 0, "P-EL": 0, "SR-EL": 0, "SR-Price": 0, "Editorial": 0 }
        defaults.update(cfg.get("dreamstime", {}).get("defaults", {}))
        filename = row.get("Filename")
        title    = row.get("Title") or row.get("Image Name")
        desc     = row.get("Description")
        keywords = row.get("Keywords") or row.get("keywords")
        cat1 = "212"
        cat2, cat3 = self._infer_cat2_cat3(row, cfg)
        return [
            filename, title, desc,
            cat1, cat2, cat3,
            keywords,
            defaults.get("Free", 0),
            defaults.get("W-EL", 0),
            defaults.get("P-EL", 0),
            defaults.get("SR-EL", 0),
            defaults.get("SR-Price", 0),
            defaults.get("Editorial", 0),
            "", "",  # MR/PR Docs
        ]

def export_from_rows(rows: List[Dict[str, Any]], outdir: Optional[Path] = None,
                     targets: Optional[List[str]] = None, config_path: Optional[Path] = None,
                     master_stem: str = "metadata_api"):
    outdir = outdir or Path.cwd()
    cfg = load_yaml_config(config_path) if config_path else {}
    rows_wrapped = [Row(r) for r in rows]
    targets = targets or sorted(_EXPORTERS.keys())
    paths = []
    for t in targets:
        tname = t.strip().lower()
        exp = _EXPORTERS.get(tname)
        if not exp:
            raise ValueError(f"Exporter '{tname}' não encontrado. Disponíveis: {', '.join(sorted(_EXPORTERS))}")
        out_path = outdir / f"{tname}_metadata_{master_stem}.csv"
        exp.export(rows_wrapped, out_path, cfg)
        paths.append(out_path)
    return paths
