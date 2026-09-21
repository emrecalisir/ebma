from __future__ import annotations

import random

from ebma.atoms import Atom, Audience


def edit_audience(aud: Audience, catalogue: dict, rng: random.Random, edit_type: str) -> Audience:
    atoms = [Atom.from_dict(a.to_dict()) for a in aud.atoms]
    tag = aud.text_tag
    pool = catalogue["atoms"]
    if edit_type == "drop":
        if len(atoms) >= 2:
            atoms.pop(rng.randrange(len(atoms)))
        elif atoms:
            a = atoms[0]
            cuts = [c for c in catalogue["V_bin"].get(a.numeric, []) if abs(c - a.threshold) > 1e-9]
            if cuts:
                a.threshold = cuts[rng.randrange(len(cuts))]
            else:
                a.threshold = a.threshold * 1.25
    elif edit_type == "add" and pool:
        atoms.append(pool[rng.randrange(len(pool))])
    elif edit_type == "threshold" and atoms:
        i = rng.randrange(len(atoms))
        a = atoms[i]
        cuts = [c for c in catalogue["V_bin"].get(a.numeric, []) if abs(c - a.threshold) > 1e-9]
        if cuts:
            a.threshold = cuts[rng.randrange(len(cuts))]
        else:
            a.threshold = a.threshold * (1.35 if rng.random() < 0.5 else 0.65)
    return Audience(aud.audience_id + f"_T{edit_type[:3]}", aud.arm, atoms, aud.combine, tag, dict(aud.notes), aud.code_path_id)
