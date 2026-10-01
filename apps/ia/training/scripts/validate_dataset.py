import csv
import hashlib
import json
from pathlib import Path

from PIL import Image, UnidentifiedImageError


# ============================================================
# CHEMINS
# ============================================================

SCRIPT_DIR = Path(__file__).resolve().parent

# apps/ia/training/
TRAINING_DIR = SCRIPT_DIR.parent

# apps/ia/training/dataset/
DATASET_DIR = TRAINING_DIR / "dataset"

# apps/ia/ai_model/labels.json
LABELS_FILE = TRAINING_DIR.parent / "ai_model" / "labels.json"

# apps/ia/training/dataset/metadata.csv
METADATA_FILE = DATASET_DIR / "metadata.csv"


SPLITS = [
    "train",
    "validation",
    "test",
]

SUPPORTED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}

MIN_WIDTH = 224
MIN_HEIGHT = 224


# ============================================================
# OUTILS
# ============================================================

def print_section(title):
    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def load_labels():
    if not LABELS_FILE.exists():
        raise FileNotFoundError(
            f"labels.json introuvable : {LABELS_FILE}"
        )

    with LABELS_FILE.open("r", encoding="utf-8") as file:
        labels = json.load(file)

    if not isinstance(labels, dict):
        raise ValueError(
            "labels.json doit contenir un objet JSON."
        )

    return labels


def calculate_md5(file_path):
    hash_md5 = hashlib.md5()

    with file_path.open("rb") as file:
        for chunk in iter(lambda: file.read(8192), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


def get_images(directory):
    if not directory.exists():
        return []

    return sorted(
        file_path
        for file_path in directory.rglob("*")
        if file_path.is_file()
        and file_path.suffix.lower() in SUPPORTED_EXTENSIONS
    )


# ============================================================
# VALIDATION DES DOSSIERS
# ============================================================

def validate_structure(labels):
    print_section("1. VERIFICATION DE LA STRUCTURE")

    errors = 0

    for split in SPLITS:
        split_dir = DATASET_DIR / split

        if not split_dir.exists():
            print(f"[ERREUR] Dossier absent : {split_dir}")
            errors += 1
            continue

        print(f"[OK] {split}/")

        for class_name in labels:
            class_dir = split_dir / class_name

            if not class_dir.exists():
                print(
                    f"  [ERREUR] Classe absente : "
                    f"{split}/{class_name}"
                )
                errors += 1
            else:
                print(f"  [OK] {class_name}/")

    return errors


# ============================================================
# COMPTAGE DES IMAGES
# ============================================================

def count_images(labels):
    print_section("2. NOMBRE D'IMAGES PAR CLASSE")

    total_images = 0

    for split in SPLITS:
        print()
        print(f"--- {split.upper()} ---")

        split_total = 0

        for class_name in labels:
            class_dir = DATASET_DIR / split / class_name
            images = get_images(class_dir)

            count = len(images)
            split_total += count

            print(f"{class_name:<42} {count}")

        print(f"TOTAL {split:<35} {split_total}")

        total_images += split_total

    print()
    print(f"TOTAL GENERAL : {total_images}")

    return total_images


# ============================================================
# VERIFICATION DES IMAGES
# ============================================================

def validate_images(labels):
    print_section("3. VERIFICATION DES IMAGES")

    invalid_images = []
    small_images = []

    for split in SPLITS:
        for class_name in labels:
            class_dir = DATASET_DIR / split / class_name

            for image_path in get_images(class_dir):
                try:
                    with Image.open(image_path) as image:
                        image.verify()

                    # Re-ouverture nécessaire après verify()
                    with Image.open(image_path) as image:
                        width, height = image.size

                    if width < MIN_WIDTH or height < MIN_HEIGHT:
                        small_images.append(
                            (
                                split,
                                class_name,
                                image_path,
                                width,
                                height,
                            )
                        )

                except (UnidentifiedImageError, OSError, ValueError):
                    invalid_images.append(
                        (
                            split,
                            class_name,
                            image_path,
                        )
                    )

    if invalid_images:
        print()
        print("IMAGES INVALIDES / CORROMPUES :")

        for split, class_name, image_path in invalid_images:
            print(
                f"[ERREUR] {split}/{class_name}/"
                f"{image_path.name}"
            )
    else:
        print("[OK] Aucune image corrompue détectée.")

    if small_images:
        print()
        print(
            f"IMAGES PLUS PETITES QUE "
            f"{MIN_WIDTH}x{MIN_HEIGHT} :"
        )

        for split, class_name, image_path, width, height in small_images:
            print(
                f"[ATTENTION] {split}/{class_name}/"
                f"{image_path.name} "
                f"({width}x{height})"
            )
    else:
        print(
            f"[OK] Aucune image sous "
            f"{MIN_WIDTH}x{MIN_HEIGHT}."
        )

    return invalid_images, small_images


# ============================================================
# DETECTION DES DOUBLONS
# ============================================================

def detect_duplicates(labels):
    print_section("4. DETECTION DES DOUBLONS")

    hashes = {}

    for split in SPLITS:
        for class_name in labels:
            class_dir = DATASET_DIR / split / class_name

            for image_path in get_images(class_dir):
                try:
                    file_hash = calculate_md5(image_path)
                except OSError:
                    continue

                relative_path = image_path.relative_to(DATASET_DIR)

                if file_hash not in hashes:
                    hashes[file_hash] = []

                hashes[file_hash].append(relative_path)

    duplicates = [
        paths
        for paths in hashes.values()
        if len(paths) > 1
    ]

    if not duplicates:
        print("[OK] Aucun doublon exact détecté.")
        return duplicates

    print(f"[ATTENTION] {len(duplicates)} groupe(s) de doublons :")

    for group in duplicates:
        print()

        for path in group:
            print(f"  - {path}")

    return duplicates


# ============================================================
# VERIFICATION DES EXTENSIONS
# ============================================================

def validate_extensions(labels):
    print_section("5. VERIFICATION DES EXTENSIONS")

    unexpected_files = []

    for split in SPLITS:
        for class_name in labels:
            class_dir = DATASET_DIR / split / class_name

            if not class_dir.exists():
                continue

            for file_path in class_dir.iterdir():
                if not file_path.is_file():
                    continue

                if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                    unexpected_files.append(
                        file_path.relative_to(DATASET_DIR)
                    )

    if not unexpected_files:
        print("[OK] Toutes les images utilisent une extension supportée.")
    else:
        print("[ATTENTION] Fichiers avec extension non supportée :")

        for file_path in unexpected_files:
            print(f"  - {file_path}")

    return unexpected_files


# ============================================================
# VERIFICATION DE METADATA.CSV
# ============================================================

def validate_metadata():
    print_section("6. VERIFICATION DE METADATA.CSV")

    if not METADATA_FILE.exists():
        print(
            f"[ERREUR] metadata.csv introuvable : "
            f"{METADATA_FILE}"
        )
        return False

    required_columns = [
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

    try:
        with METADATA_FILE.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            reader = csv.DictReader(file)

            if reader.fieldnames is None:
                print("[ERREUR] metadata.csv est vide.")
                return False

            missing_columns = [
                column
                for column in required_columns
                if column not in reader.fieldnames
            ]

            if missing_columns:
                print(
                    "[ERREUR] Colonnes manquantes : "
                    + ", ".join(missing_columns)
                )
                return False

            rows = list(reader)

        print(
            f"[OK] metadata.csv est lisible "
            f"({len(rows)} ligne(s))."
        )

        return True

    except (OSError, csv.Error) as exc:
        print(
            f"[ERREUR] Impossible de lire metadata.csv : {exc}"
        )
        return False


# ============================================================
# RAPPORT FINAL
# ============================================================

def main():
    print()
    print("=" * 70)
    print("VALIDATION DU DATASET AGRI-CONSEIL")
    print("=" * 70)

    try:
        labels = load_labels()
    except Exception as exc:
        print()
        print(f"[ERREUR] {exc}")
        return 1

    print()
    print(f"Nombre de classes définies : {len(labels)}")

    structure_errors = validate_structure(labels)

    total_images = count_images(labels)

    invalid_images, small_images = validate_images(labels)

    duplicates = detect_duplicates(labels)

    unexpected_files = validate_extensions(labels)

    metadata_ok = validate_metadata()

    print_section("7. RAPPORT FINAL")

    print(
        f"Classes définies          : {len(labels)}"
    )

    print(
        f"Images détectées          : {total_images}"
    )

    print(
        f"Erreurs de structure      : {structure_errors}"
    )

    print(
        f"Images corrompues         : {len(invalid_images)}"
    )

    print(
        f"Images trop petites       : {len(small_images)}"
    )

    print(
        f"Groupes de doublons       : {len(duplicates)}"
    )

    print(
        f"Fichiers non supportés    : {len(unexpected_files)}"
    )

    print(
        f"metadata.csv valide       : "
        f"{'OUI' if metadata_ok else 'NON'}"
    )

    print()

    if total_images == 0:
        print(
            "[INFO] Le dataset ne contient encore aucune image."
        )

    if (
        structure_errors == 0
        and len(invalid_images) == 0
        and len(unexpected_files) == 0
        and metadata_ok
    ):
        print(
            "[OK] Structure du dataset valide."
        )
    else:
        print(
            "[ATTENTION] Le dataset nécessite des corrections."
        )

    print()
    print("=" * 70)
    print("FIN DE LA VALIDATION")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

