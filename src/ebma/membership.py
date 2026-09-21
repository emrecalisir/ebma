"""Sole membership writer. LLM output is never assigned to bits."""
from __future__ import annotations

import numpy as np
import pandas as pd

from ebma import LLM_WROTE_MEMBERSHIP
from ebma.atoms import Atom, Audience


class SymbolicArbiter:
    def membership(self, audience: Audience, customers: pd.DataFrame) -> np.ndarray:
        assert LLM_WROTE_MEMBERSHIP is False
        n = len(customers)
        if audience.text_tag:
            col = "text_blob" if "text_blob" in customers.columns else "attr_blob"
            bits = (
                customers[col]
                .fillna("")
                .astype(str)
                .str.lower()
                .str.contains(audience.text_tag.lower(), regex=False)
                .to_numpy()
            )
            if audience.atoms:
                bits = np.logical_and(bits, self._all_numeric(audience, customers))
            return bits
        if not audience.atoms:
            return np.zeros(n, dtype=bool)
        masks = [self._eval_atom(atom, customers) for atom in audience.atoms]
        out = masks[0].copy()
        for m in masks[1:]:
            out = np.logical_and(out, m) if audience.combine == "and" else np.logical_or(out, m)
        return out

    def _all_numeric(self, audience: Audience, customers: pd.DataFrame) -> np.ndarray:
        out = np.ones(len(customers), dtype=bool)
        for atom in audience.atoms:
            out = np.logical_and(out, self._num(atom, customers))
        return out

    def _eval_atom(self, atom: Atom, customers: pd.DataFrame) -> np.ndarray:
        ev = customers["event_set"].fillna("").astype(str).str.contains(atom.event_key, regex=False).to_numpy()
        if atom.attr == "ANY":
            at = np.ones(len(customers), dtype=bool)
        else:
            at = (
                customers["attr_blob"]
                .fillna("")
                .astype(str)
                .str.contains("|" + atom.attr + "|", regex=False)
                .to_numpy()
            )
        return np.logical_and(np.logical_and(ev, at), self._num(atom, customers))

    def _num(self, atom: Atom, customers: pd.DataFrame) -> np.ndarray:
        if atom.numeric not in customers.columns:
            return np.zeros(len(customers), dtype=bool)
        x = customers[atom.numeric].to_numpy(dtype=float)
        ops = {">=": x >= atom.threshold, "<=": x <= atom.threshold, ">": x > atom.threshold, "<": x < atom.threshold}
        return ops.get(atom.op, np.zeros(len(customers), dtype=bool))
