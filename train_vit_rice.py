from pathlib import Path
import json, random
import numpy as np, torch
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms
from transformers import AutoImageProcessor, ViTForImageClassification
MODEL='google/vit-base-patch16-224-in21k'
BASE=Path(__file__).resolve().parents[3]
DATA=BASE/'apps'/'ia'/'training'/'dataset'
OUT=BASE/'apps'/'ia'/'ai_model'/'model'/'riz_vit'
CLASSES=['riz__pyriculariose','riz__tache_brune','riz__bacteriose_feuilles','sain__riz']
SEED=42; BATCH=8; EPOCHS=15; BACKBONE_LR=1e-5; HEAD_LR=1e-4; WEIGHT_DECAY=.01; PATIENCE=4; SIZE=224
def seed():
    random.seed(SEED); np.random.seed(SEED); torch.manual_seed(SEED)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(SEED)
def evaluate(model,loader,device):
    model.eval(); crit=nn.CrossEntropyLoss(); ys=[]; ps=[]; total=0; loss_sum=0
    with torch.no_grad():
        for x,y in loader:
            x,y=x.to(device),y.to(device); o=model(pixel_values=x); loss=crit(o.logits,y); p=o.logits.argmax(-1)
            loss_sum+=loss.item()*y.size(0); total+=y.size(0); ys+=y.cpu().tolist(); ps+=p.cpu().tolist()
    return loss_sum/total, accuracy_score(ys,ps), ys, ps
def main():
    seed(); device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); print('Device:',device)
    if device.type=='cuda': print('GPU:',torch.cuda.get_device_name(0))
    OUT.mkdir(parents=True,exist_ok=True)
    proc=AutoImageProcessor.from_pretrained(MODEL); mean,std=proc.image_mean,proc.image_std
    tr=transforms.Compose([transforms.RandomResizedCrop(SIZE,scale=(.75,1),ratio=(.9,1.1)),transforms.RandomHorizontalFlip(),transforms.RandomRotation(10),transforms.ColorJitter(.15,.15,.1,.02),transforms.ToTensor(),transforms.Normalize(mean,std)])
    ev=transforms.Compose([transforms.Resize(256),transforms.CenterCrop(SIZE),transforms.ToTensor(),transforms.Normalize(mean,std)])
    train=datasets.ImageFolder(DATA/'train',transform=tr); val=datasets.ImageFolder(DATA/'validation',transform=ev); test=datasets.ImageFolder(DATA/'test',transform=ev)
    if train.classes!=CLASSES or val.classes!=CLASSES or test.classes!=CLASSES: raise ValueError(f'Classes detectees: train={train.classes}, val={val.classes}, test={test.classes}')
    print(f'Dataset: {len(train)} train / {len(val)} validation / {len(test)} test')
    tl=DataLoader(train,batch_size=BATCH,shuffle=True,num_workers=0,pin_memory=torch.cuda.is_available()); vl=DataLoader(val,batch_size=BATCH,num_workers=0,pin_memory=torch.cuda.is_available()); xl=DataLoader(test,batch_size=BATCH,num_workers=0,pin_memory=torch.cuda.is_available())
    id2label={i:c for i,c in enumerate(CLASSES)}; label2id={c:i for i,c in enumerate(CLASSES)}
    model=ViTForImageClassification.from_pretrained(MODEL,num_labels=4,id2label=id2label,label2id=label2id,ignore_mismatched_sizes=True).to(device)
    back=[]; head=[]
    for n,p in model.named_parameters(): (head if n.startswith('classifier') else back).append(p)
    opt=torch.optim.AdamW([{'params':back,'lr':BACKBONE_LR},{'params':head,'lr':HEAD_LR}],weight_decay=WEIGHT_DECAY); crit=nn.CrossEntropyLoss(); best=-1; bad=0; bestdir=OUT/'best_model'
    for ep in range(1,EPOCHS+1):
        model.train(); loss_sum=0; total=0
        for x,y in tl:
            x,y=x.to(device),y.to(device); opt.zero_grad(set_to_none=True); o=model(pixel_values=x); loss=crit(o.logits,y); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(),1.0); opt.step(); loss_sum+=loss.item()*y.size(0); total+=y.size(0)
        vlss,vacc,_,_=evaluate(model,vl,device); print(f'Epoch {ep:02d}/{EPOCHS} | train_loss={loss_sum/total:.4f} | val_loss={vlss:.4f} | val_accuracy={vacc:.4f}')
        if vacc>best:
            best=vacc; bad=0; model.save_pretrained(bestdir); proc.save_pretrained(bestdir); (bestdir/'classes.json').write_text(json.dumps({'classes':CLASSES,'id2label':id2label,'label2id':label2id},ensure_ascii=False,indent=2),encoding='utf-8'); print('  -> meilleur modele sauvegarde.')
        else:
            bad+=1
            if bad>=PATIENCE: print('Early stopping.'); break
    bestmodel=ViTForImageClassification.from_pretrained(bestdir).to(device); loss,acc,y,p=evaluate(bestmodel,xl,device)
    print('\nTEST FINAL'); print('test_loss:',round(loss,4)); print('test_accuracy:',round(acc,4)); print('\nRapport:\n',classification_report(y,p,labels=list(range(4)),target_names=CLASSES,zero_division=0)); print('Matrice:\n',confusion_matrix(y,p))
    (OUT/'metrics.json').write_text(json.dumps({'model':MODEL,'classes':CLASSES,'train_images':len(train),'validation_images':len(val),'test_images':len(test),'best_validation_accuracy':best,'test_loss':loss,'test_accuracy':acc,'seed':SEED},ensure_ascii=False,indent=2),encoding='utf-8')
    print('\nModele:',bestdir)
if __name__=='__main__': main()
