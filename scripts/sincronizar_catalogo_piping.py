"""Extrae las dimensiones existentes del visor de intercambiadores para piping."""
import ast
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'visor_3d' / 'index.html').read_text()

def constante(nombre):
    match = re.search(r'const\s+' + re.escape(nombre) + r'\s*=\s*([\[{])', source)
    start = match.start(1)
    end = source.index(';', start)
    return ast.literal_eval(source[start:end].strip())

labels = constante('DIAMETERS')
nps = constante('DIAMETER_INCHES')
ods = constante('PIPE_OUTSIDE_DIAMETER_MM')
rf = constante('RAISED_FACE_DIAMETER_INCHES')
rows = constante('FLANGE_DIMENSIONS')
fields = ('diameterMM', 'thicknessMM', 'hubDiameterMM', 'legacyOD', 'lengthMM', 'pitchMM', 'holeMM')
items = []
for i in sorted(range(len(rf)), key=lambda k: nps[k]):
    flanges = {}
    for rating, table in rows.items():
        row = table[i]
        dims = {field: round(value * 25.4, 5) for field, value in zip(fields, row[:7]) if field != 'legacyOD'}
        dims.update(boltCount=row[7], odMM=ods[i], raisedFaceMM=round(rf[i] * 25.4, 5))
        flanges[rating] = dims
    items.append(dict(nps=nps[i], label=labels[i], odMM=ods[i], flanges=flanges))
output = dict(version=1, source='Dimensiones del visor de intercambiadores: bridas WN ASME B16.5 y diámetro exterior ASME B36.10M. Unidades: mm.', items=items)
(ROOT / 'visor_piping' / 'catalogo.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
print(f'Catálogo sincronizado: {len(items)} medidas y {len(rows)} clases.')
