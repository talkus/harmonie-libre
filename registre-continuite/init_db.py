#!/usr/bin/env python3
"""init_db.py — Initialise la base DuckDB avec tous les schemas.

Execute les fichiers SQL dans l'ordre, puis insere les donnees du
premier cas reel (transcription du 12 septembre 2026).

Usage:
    python3 init_db.py --db registre.duckdb
    python3 init_db.py --db registre.duckdb --seed
"""

import argparse
import os
import sys

import duckdb

SQL_DIR = os.path.join(os.path.dirname(__file__), "sql")
SQL_FILES = [
    "001_documents.sql",
    "002_entities.sql",
    "003_relations.sql",
    "004_contradictions.sql",
    "005_status_history.sql",
    "006_signing_keys.sql",
    "007_key_lifecycle.sql",
    "008_chain_integrity.sql",
]


def init_database(db_path: str, seed: bool = False):
    """Cree ou reinitialise la base DuckDB."""
    if os.path.exists(db_path):
        os.remove(db_path)

    con = duckdb.connect(db_path)
    print(f"Base creee : {db_path}")

    for sql_file in SQL_FILES:
        path = os.path.join(SQL_DIR, sql_file)
        if not os.path.exists(path):
            print(f"  ATTENTION : {sql_file} absent — saute")
            continue
        print(f"  Execution : {sql_file}")
        with open(path, "r", encoding="utf-8") as fh:
            con.execute(fh.read())

    if seed:
        _seed_first_case(con)

    con.close()
    print("Initialisation terminee.")


def _seed_first_case(con):
    """Insere le premier cas reel : transcription du 12 septembre 2026."""
    print("  Seed : transcription du 12 septembre 2026")

    con.execute(
        """INSERT INTO documents VALUES (
            'doc_notion_transcription_2026-09-12',
            'Transcription du 12 septembre 2026',
            'notion',
            'https://app.notion.com/p/3d98d1e3591e816980dfd61d4d4e3044',
            '94f838644a7b7af5df72759a7fafca5a3d3d2f30ddde9341ae14a67b92c95d17',
            '2026-09-12', 'vibe', '2026-09-12T23:30Z'
        )"""
    )

    entities = [
        ('ent_001', 'Person', 'Mikael', 'doc_notion_transcription_2026-09-12', '2026-09-12T23:35Z', 'candidate', 'Extrait par IA'),
        ('ent_002', 'Project', 'Forteresse', 'doc_notion_transcription_2026-09-12', '2026-09-12T23:35Z', 'candidate', 'Extrait par IA'),
        ('ent_003', 'Document', 'Passation', 'doc_notion_transcription_2026-09-12', '2026-09-12T23:35Z', 'candidate', 'Extrait par IA'),
        ('ent_004', 'Concept', 'Double memoire', 'doc_notion_transcription_2026-09-12', '2026-09-12T23:35Z', 'candidate', 'Extrait par IA'),
        ('ent_005', 'Concept', 'Architecture de cloture', 'doc_notion_transcription_2026-09-12', '2026-09-12T23:35Z', 'candidate', 'Extrait par IA'),
        ('ent_006', 'Tool', 'DuckDB', 'doc_notion_transcription_2026-09-12', '2026-09-12T23:35Z', 'candidate', 'Extrait par IA'),
        ('ent_007', 'Concept', 'Amour choisi', 'doc_notion_transcription_2026-09-12', '2026-09-12T23:35Z', 'candidate', 'Extrait par IA'),
    ]
    for ent in entities:
        con.execute("INSERT INTO entities VALUES (?, ?, ?, ?, ?, ?, ?, ?)", list(ent))

    relations = [
        ('rel_001', 'ent_001', 'WORKS_ON', 'ent_002', 0.95, 'candidate', 'ia_extract', 'vibe', '2026-09-12T23:40Z', 'doc_notion_transcription_2026-09-12'),
        ('rel_002', 'ent_002', 'REFERENCES', 'ent_005', 0.90, 'candidate', 'ia_extract', 'vibe', '2026-09-12T23:40Z', 'doc_notion_transcription_2026-09-12'),
        ('rel_003', 'ent_003', 'DESCRIBES', 'ent_002', 0.95, 'candidate', 'ia_extract', 'vibe', '2026-09-12T23:40Z', 'doc_notion_transcription_2026-09-12'),
        ('rel_004', 'ent_002', 'IMPLEMENTS', 'ent_004', 0.85, 'candidate', 'ia_extract', 'vibe', '2026-09-12T23:40Z', 'doc_notion_transcription_2026-09-12'),
        ('rel_005', 'ent_002', 'INSPIRED_BY', 'ent_007', 0.90, 'candidate', 'ia_extract', 'vibe', '2026-09-12T23:40Z', 'doc_notion_transcription_2026-09-12'),
    ]
    for rel in relations:
        con.execute("INSERT INTO relations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", list(rel))

    print("    1 document, 7 entites, 5 relations candidates")


def main():
    parser = argparse.ArgumentParser(
        description="Initialise la base DuckDB du registre de continuite"
    )
    parser.add_argument("--db", default="registre.duckdb",
                        help="Chemin vers le fichier DuckDB")
    parser.add_argument("--seed", action="store_true",
                        help="Inserer le premier cas reel")
    args = parser.parse_args()

    init_database(args.db, seed=args.seed)


if __name__ == "__main__":
    main()
