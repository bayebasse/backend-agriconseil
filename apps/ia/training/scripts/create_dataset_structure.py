import json
from pathlib import Path


# ---------------------------------------------------------
# Chemins
# ---------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent

# apps/ia/training/scripts
TRAINING_DIR = SCRIPT_DIR.parent

# apps/ia/training/dataset
DATASET_DIR = TRAINING_DIR / "dataset"

# apps/ia/ai_model/labels.json
AI_MODEL_DIR = TRAINING_DIR.parent / "ai_model"
LABELS_FILE = AI_MODEL_DIR / "labels.json"


# ---------------------------------------------------------
# Vérification de labels.json
# ---------------------------------------------------------

if not LABELS_FILE.exists():
    raise FileNotFoundError(
        f"Le fichier labels.json est introuvable : {LABELS_FILE}"
    )


with LABELS_FILE.open("r", encoding="utf-8") as file:
    labels = json.load(file)


if not isinstance(labels, dict):
    raise ValueError(
        "labels.json doit contenir un objet JSON avec les classes comme clés."
    )


# ---------------------------------------------------------
# Les trois ensembles du dataset
# ---------------------------------------------------------

splits = [
    "train",
    "validation",
    "test",
]


# ---------------------------------------------------------
# Création automatique
# ---------------------------------------------------------

created_count = 0

for split in splits:
    split_dir = DATASET_DIR / split
    split_dir.mkdir(parents=True, exist_ok=True)

    for class_name in labels.keys():
        class_dir = split_dir / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        created_count += 1


# ---------------------------------------------------------
# Résultat
# ---------------------------------------------------------

print()
print("=" * 60)
print("STRUCTURE DU DATASET CRÉÉE AVEC SUCCÈS")
print("=" * 60)
print()

print(f"Nombre de classes : {len(labels)}")
print(f"Nombre de parties : {len(splits)}")
print(f"Dossiers créés/vérifiés : {created_count}")
print()

print(f"Dataset : {DATASET_DIR}")
print()

for split in splits:
    print(f"{split}/")
    for class_name in labels.keys():
        print(f"  └── {class_name}/")

print()
print("=" * 60)
print("FIN")
print("=" * 60)