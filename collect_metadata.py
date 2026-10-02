from pathlib import Path
import csv
import json

# ============================================================
# Agri-Conseil - Collecte automatique de metadata.csv
# Phase actuelle : RIZ uniquement
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "apps" / "ia" / "training" / "dataset" / "raw"
METADATA_FILE = BASE_DIR / "apps" / "ia" / "training" / "dataset" / "metadata.csv"
LABELS_FILE = BASE_DIR / "apps" / "ia" / "ai_model" / "labels.json"

# Les sources sont associées aux classes déjà collectées.
# On ne touche PAS aux fichiers image.
SOURCE_INFO = {
    "riz__pyriculariose": {
        "source": "Mendeley Data - Rice Leaf Disease Dataset V2",
        "source_url": "https://data.mendeley.com/datasets/z4hx2v3ywc/2",
        "license": "CC BY 4.0",
    },
    "riz__tache_brune": {
        "source": "Mendeley Data - Rice Leaf Bacterial and Fungal Disease Dataset V2",
        "source_url": "https://data.mendeley.com/datasets/hx6f852hw4/2",
        "license": "CC BY 4.0",
    },
    "riz__bacteriose_feuilles": {
        "source": "Mendeley Data - Rice Leaf Bacterial and Fungal Disease Dataset V2",
        "source_url": "https://data.mendeley.com/datasets/hx6f852hw4/2",
        "license": "CC BY 4.0",
    },
    "sain__riz": {
        "source": "Mendeley Data - Rice Leaf Bacterial and Fungal Disease Dataset V2",
        "source_url": "https://data.mendeley.com/datasets/hx6f852hw4/2",
        "license": "CC BY 4.0",
    },
}

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

def load_labels():
    with LABELS_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def main():
    labels = load_labels()

    rows = []

    for class_name, info in SOURCE_INFO.items():
        class_dir = RAW_DIR / class_name

        if not class_dir.exists():
            print(f"[ATTENTION] Dossier absent : {class_dir}")
            continue

        label_info = labels.get(class_name, {})
        culture = label_info.get("culture", "")
        maladie = label_info.get("maladie")

        images = sorted(
            p for p in class_dir.iterdir()
            if p.is_file() and p.suffix.lower() in ALLOWED_EXTENSIONS
        )

        for image_path in images:
            rows.append({
                "filename": image_path.name,
                "class": class_name,
                "culture": culture,
                "maladie": maladie or "",
                "split": "",
                "source": info["source"],
                "source_url": info["source_url"],
                "license": info["license"],
                "verified": "non",
            })

    fieldnames = [
        "filename",
        "class",
        "culture",
        "maladie",
        "split",
        "source",
        "source_url",
        "license",
        "verified",
    ]

    METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    with METADATA_FILE.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print()
    print("==============================================")
    print("metadata.csv généré avec succès")
    print("==============================================")
    print(f"Fichier : {METADATA_FILE}")
    print(f"Nombre total d'images : {len(rows)}")
    print()

    counts = {}
    for row in rows:
        counts[row["class"]] = counts.get(row["class"], 0) + 1

    for class_name, count in counts.items():
        print(f"{class_name:<32} {count:>3} image(s)")

    print()
    print("IMPORTANT :")
    print("- split reste vide : il sera attribué après validation.")
    print("- verified = non : aucune validation manuelle n'est inventée.")
    print("- aucun fichier image n'est déplacé ou renommé.")

if __name__ == "__main__":
    main()
