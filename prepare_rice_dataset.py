from pathlib import Path
import csv, random, shutil
SEED=42
BASE_DIR=Path(__file__).resolve().parent
RAW_DIR=BASE_DIR/'apps'/'ia'/'training'/'dataset'/'raw'
SPLITS={'train':BASE_DIR/'apps'/'ia'/'training'/'dataset'/'train','validation':BASE_DIR/'apps'/'ia'/'training'/'dataset'/'validation','test':BASE_DIR/'apps'/'ia'/'training'/'dataset'/'test'}
METADATA_FILE=BASE_DIR/'apps'/'ia'/'training'/'dataset'/'metadata.csv'
CLASSES=['riz__pyriculariose','riz__tache_brune','riz__bacteriose_feuilles','sain__riz']
EXT={'.jpg','.jpeg','.png','.webp','.bmp'}
def main():
    random.seed(SEED); split_map={}
    for d in SPLITS.values(): d.mkdir(parents=True,exist_ok=True)
    for c in CLASSES:
        src=RAW_DIR/c; imgs=sorted(p for p in src.iterdir() if p.is_file() and p.suffix.lower() in EXT)
        if len(imgs)!=20: raise ValueError(f'{c}: {len(imgs)} images trouvees, 20 attendues.')
        random.shuffle(imgs); parts={'train':imgs[:12],'validation':imgs[12:16],'test':imgs[16:]}
        for s,files in parts.items():
            dst=SPLITS[s]/c
            if dst.exists(): shutil.rmtree(dst)
            dst.mkdir(parents=True)
            for p in files:
                shutil.copy2(p,dst/p.name); split_map[(c,p.name)]=s
        print(f'{c}: 12 train / 4 validation / 4 test')
    with METADATA_FILE.open(encoding='utf-8-sig',newline='') as f: rows=list(csv.DictReader(f))
    for r in rows: r['split']=split_map.get((r['class'],r['filename']),r['split'])
    fields=['filename','class','culture','maladie','split','source','source_url','license','verified']
    with METADATA_FILE.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print('\n80 images preparees. Les fichiers de raw/ n\'ont pas ete deplaces.')
if __name__=='__main__': main()
