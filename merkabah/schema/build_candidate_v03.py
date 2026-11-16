"""Build the explicitly provisional two-scene graph. No network or mutation of v0.1."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCES = {
    "AELF_EZ1": {"edition": "AELF", "url": "https://www.aelf.org/bible/Ez/1"},
    "AELF_EZ10": {"edition": "AELF", "url": "https://www.aelf.org/bible/Ez/10"},
    "USCCB_EZ1": {"edition": "NABRE / USCCB", "url": "https://bible.usccb.org/bible/ezekiel/1"},
    "USCCB_EZ10": {"edition": "NABRE / USCCB", "url": "https://bible.usccb.org/bible/ezekiel/10"},
}


def build():
    nodes, edges = [], []
    scenes = ("ez1", "ez10")
    def ref(scene, verse, edition="AELF"):
        return {"source": f"{edition}_{scene.upper()}", "verse": verse}
    def node(identifier, scene, kind, verse, **extra):
        nodes.append({"id": identifier, "scene": scene, "type": kind,
                      "status": "TEXTUEL", "references": [ref(scene, verse)], **extra})
    def edge(source, target, scene, relation, verse, status="TEXTUEL"):
        edges.append({"from": source, "to": target, "scene": scene, "type": relation,
                      "status": status, "references": [ref(scene, verse)]})

    for scene in scenes:
        is_first = scene == "ez1"
        v = lambda a, b: a if is_first else b
        forms = ("human", "lion", "ox", "eagle") if is_first else ("cherub", "human", "lion", "eagle")
        node(f"{scene}_expanse", scene, "expanse", v("1:22", "10:1"))
        node(f"{scene}_throne", scene, "throne", v("1:26", "10:1"))
        node(f"{scene}_spirit", scene, "spirit", v("1:12,20-21", "10:17"),
             uncertainty="Nature et identité du souffle non déterminées par ce modèle.")
        edge(f"{scene}_throne", f"{scene}_expanse", scene, "above", v("1:26", "10:1"))
        for i in range(1, 5):
            being, wheel = f"{scene}_being_{i}", f"{scene}_wheel_{i}"
            node(being, scene, "living_being", v("1:5-6", "10:15,20-21"),
                 identity_note="Numérotation de scène choisie; aucune identité individuelle inter-scènes établie.")
            node(wheel, scene, "wheel", v("1:15-16", "10:9-10"),
                 wheel_inside_wheel=True,
                 rim_appearance="eyes (NABRE 1:18)" if is_first else "eyes (10:12)",
                 rim_reference=ref(scene, "1:18", "USCCB") if is_first else ref(scene, "10:12", "USCCB"))
            edge(being, wheel, scene, "beside", v("1:15", "10:9"), "DEDUIT" if is_first else "TEXTUEL")
            edge(wheel, being, scene, "moves_with", v("1:19-21", "10:16-17"))
            if is_first:
                edge(being, f"{scene}_spirit", scene, "directed_by", "1:12")
            edge(wheel, f"{scene}_spirit", scene, "contains_spirit", v("1:20", "10:17"))
            edge(being, f"{scene}_expanse", scene, "beneath", v("1:22", "10:1"))
            for form in forms:
                face = f"{being}_face_{form}"
                node(face, scene, "face", v("1:10", "10:14"), form=form,
                     orientation="INCONNUE" if scene == "ez10" or form in {"human", "eagle"} else
                                 ("right" if form == "lion" else "left"))
                edge(being, face, scene, "has_face", v("1:10", "10:14"))
            for n in range(1, 5):
                wing = f"{being}_wing_{n}"
                node(wing, scene, "wing", v("1:6,11", "10:21"),
                     function=("spread" if n <= 2 else "covering") if is_first else "INCONNUE")
                edge(being, wing, scene, "has_wing", v("1:6,11", "10:21"))
            hand = f"{being}_human_hands"
            node(hand, scene, "hands_presence", v("1:8", "10:8"),
                 uncertainty="Nombre et géométrie des mains non imposés.")
            edge(being, hand, scene, "has_hands_under_wings", v("1:8", "10:8"))
            if is_first:
                legs = f"{being}_legs_and_feet"
                node(legs, scene, "legs_and_feet", "1:7", uncertainty="Forme exacte et taille non spécifiées.")
                edge(being, legs, scene, "has_legs_and_feet", "1:7")
        if is_first:
            node("ez1_kebar", scene, "location", "1:1-3")
        else:
            node("ez10_temple", scene, "location", "10:3-4,19")
            node("ez10_linen_man", scene, "person", "10:2,7")
            node("ez10_coals", scene, "coals", "10:2,7")
            edge("ez10_linen_man", "ez10_coals", scene, "receives", "10:7")

    return {"project": "MERKABAH", "version": "0.3.0-experimental",
            "status": "PROPOSED_NOT_VALIDATED", "scenes": list(scenes), "sources": SOURCES,
            "notes": ["Vues de chapitres distinctes : numérotation individuelle non historique.",
                      "Éz 1:10 et 10:14 sont conservés séparément; aucune équivalence bœuf/chérubin affirmée.",
                      "Éz 1:18 : AELF parle de scintillements, NABRE d'yeux; référence de traduction explicite.",
                      "Placements, géométrie et animation sont des choix d'interprétation, non représentés ici."],
            "nodes": nodes, "edges": edges}


if __name__ == "__main__":
    path = ROOT / "merkabah_candidate_v0.3.json"
    path.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(path)
