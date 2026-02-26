import csv
import json
import math
from collections import defaultdict

import numpy as np


class GaitAnalysisService:
    """Procesamiento simple de marcha para fuerza vertical (Fz).

    Entrada esperada (CSV):
    - Opción A: columnas `foot`, `step_id`, `fz`
    - Opción B: columnas `t`, `foot`, `fz` (segmenta pasos por umbral)
    """

    @staticmethod
    def _norm_foot(v):
        txt = (v or "").strip().lower()
        if txt in ("izq", "left", "l", "i"):
            return "IZQ"
        if txt in ("der", "right", "r", "d"):
            return "DER"
        return ""

    @staticmethod
    def _normalize_step(step_values, n=101):
        arr = np.array(step_values, dtype=float)
        if arr.size < 3:
            return None
        x_old = np.linspace(0.0, 1.0, arr.size)
        x_new = np.linspace(0.0, 1.0, n)
        return np.interp(x_new, x_old, arr)

    @staticmethod
    def _segment_steps(raw_points, threshold_n=80.0):
        """raw_points: list[(t, fz)] ordenado por t."""
        steps = []
        current = []
        on_step = False
        for _t, fz in raw_points:
            if fz >= threshold_n:
                current.append(float(fz))
                on_step = True
            else:
                if on_step and len(current) >= 5:
                    steps.append(current)
                current = []
                on_step = False
        if on_step and len(current) >= 5:
            steps.append(current)
        return steps

    @staticmethod
    def analizar_csv(path_csv):
        with open(path_csv, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if not rows:
            return {"error": "CSV vacío"}

        cols = {c.strip().lower() for c in (reader.fieldnames or [])}
        by_foot_steps = {"IZQ": [], "DER": []}

        if {"foot", "step_id", "fz"}.issubset(cols):
            grouped = defaultdict(list)
            for r in rows:
                foot = GaitAnalysisService._norm_foot(r.get("foot"))
                if foot not in ("IZQ", "DER"):
                    continue
                sid = str(r.get("step_id", "")).strip()
                try:
                    fz = float(r.get("fz", 0.0))
                except Exception:
                    continue
                grouped[(foot, sid)].append(fz)
            for (foot, _sid), seq in grouped.items():
                if len(seq) >= 5:
                    by_foot_steps[foot].append(seq)

        elif {"t", "foot", "fz"}.issubset(cols):
            raw = {"IZQ": [], "DER": []}
            for r in rows:
                foot = GaitAnalysisService._norm_foot(r.get("foot"))
                if foot not in ("IZQ", "DER"):
                    continue
                try:
                    t = float(r.get("t", 0.0))
                    fz = float(r.get("fz", 0.0))
                except Exception:
                    continue
                raw[foot].append((t, fz))
            for foot in ("IZQ", "DER"):
                raw[foot].sort(key=lambda x: x[0])
                by_foot_steps[foot] = GaitAnalysisService._segment_steps(raw[foot])
        else:
            return {"error": "Formato CSV no compatible. Use columnas: foot,step_id,fz o t,foot,fz"}

        out = {"IZQ": {}, "DER": {}, "ok": True}
        for foot in ("IZQ", "DER"):
            normalized = []
            for s in by_foot_steps[foot]:
                ns = GaitAnalysisService._normalize_step(s, n=101)
                if ns is not None:
                    normalized.append(ns)
            if not normalized:
                out[foot] = {
                    "n_steps": 0,
                    "curve": [],
                    "peak_n": 0.0,
                    "impulse": 0.0,
                }
                continue
            mat = np.vstack(normalized)
            mean_curve = mat.mean(axis=0)
            peak = float(np.max(mean_curve))
            impulse = float(np.trapezoid(mean_curve, dx=1.0 / 100.0))
            out[foot] = {
                "n_steps": int(mat.shape[0]),
                "curve": [float(v) for v in mean_curve],
                "peak_n": peak,
                "impulse": impulse,
            }

        return out

    @staticmethod
    def resumen_texto(res):
        if res.get("error"):
            return f"Error: {res['error']}"
        izq = res.get("IZQ", {})
        der = res.get("DER", {})
        lines = ["Análisis Fz normalizado (0-100% apoyo)", ""]
        for foot, d in (("IZQ", izq), ("DER", der)):
            lines.append(f"{foot}: pasos válidos={d.get('n_steps', 0)}")
            lines.append(f"  - Pico Fz: {d.get('peak_n', 0.0):.1f} N")
            lines.append(f"  - Impulso: {d.get('impulse', 0.0):.3f} N·s (normalizado)")
            lines.append("")
        return "\n".join(lines)
