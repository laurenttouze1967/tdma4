"""Consignes de mise en page par récit : un fichier JSON par récit dans specs/ (liste d'opérations, voir layout.py)."""
import json, glob, os
SPECS = {}
for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'specs', '*.json'))):
    SPECS[os.path.splitext(os.path.basename(f))[0]] = json.load(open(f))
