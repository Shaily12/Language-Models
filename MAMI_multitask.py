# -*- coding: utf-8 -*-
"""SHAILYS Copy of MAMI-2022-Multimodal.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1GgHhtdyA69_YCxx6vgI9UPiKxBnmmRbh

# New Section
"""

!pip install transformers sentencepiece sacremoses
!pip install pytorch-lightning==1.2.3

from google.colab import drive
drive.mount('/content/drive')

import numpy as np
import os
import random
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import torch
import torchvision
import torchtext
from PIL import Image
from transformers import AutoTokenizer, AutoModel
import torchvision.models as models
import torch.nn as nn
import torch.nn.functional as F
from transformers import RobertaTokenizer, RobertaModel
import torch.optim as optim
import tqdm
import pytorch_lightning as pl

data = pd.read_csv('/content/preprocessed.csv')
data = data.drop(['Unnamed: 0','shaming','stereotype','objectification','violence'],axis=1)
data.head()

!unzip /content/drive/MyDrive/Misogyny_Detection/training.zip -d /content/

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# class MisogynyDataset(torch.utils.data.Dataset):
#     def __init__(self,data,img_dir,image_transform,tokenizer):
#         self.data = pd.read_csv(data)
#         self.image_transform = image_transform

#         self.tokenizer = tokenizer
#         self.data.file_name = self.data.apply(
#             lambda row: (os.path.join(img_dir,row.file_name)), axis=1)

#     def __len__(self):
#         return len(self.data)

#     def __getitem__(self,idx):
#         if torch.is_tensor(idx):
#             idx.tolist()

#         image = Image.open(self.data.loc[idx,'file_name']).convert('RGB')
#         image = self.image_transform(image)

#         text = self.data.loc[idx,'Text Transcription']
#         text = self.tokenizer.encode(text, max_length = 15, truncation=True, return_tensors="pt",padding='max_length')

#         label = torch.Tensor([self.data.loc[idx,'misogynous']]).long().squeeze()

#         item = {
#             'image' : image,
#             'text' : text,
#             'label' : label
#         }      

        return item

# dataset = MisogynyDataset('/content/preprocessed.csv','/content/TRAINING',image_transform,tokenizer)
# loader = torch.utils.data.DataLoader(dataset,batch_size=1)
# for i,data in enumerate(loader):
#     print(i,data['label'],type(data['label']))
#     if i ==5:
#         break

# tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
# text_module = RobertaModel.from_pretrained('roberta-base')
# text_module.to(device)

# dataset = MisogynyDataset('/content/preprocessed.csv','/content/TRAINING',image_transform,tokenizer)

# class Identity(nn.Module):
#     def __init__(self):
#         super(Identity, self).__init__()
        
#     def forward(self, x):
#         return x


# image_module = models.resnet18(pretrained=True)
# image_module.fc = Identity()
# image_module.to(device)
# print(image_module)

# class MultimodalModel(torch.nn.Module):
#     def __init__(self, text_module, image_module):
#         super(MultimodalModel, self).__init__()
#         self.text_module = text_module
#         self.image_module = image_module 
#         self.fc1 = nn.Linear(12032, 4096)
#         self.fc2 = nn.Linear(4096, 256)
#         self.fc3 = nn.Linear(256, 64)
#         self.fc4 = nn.Linear(64, 1)

#     def forward(self, image_batch, text_batch):
#         image_features = self.image_module(image_batch) 

#         text_features = self.text_module(torch.squeeze(text_batch)) 

#         reshaped_text_features = torch.reshape(text_features.last_hidden_state, (4, 15*768))
#         concat_features = torch.cat((reshaped_text_features, image_features), 1)
#         x = self.fc1(concat_features)
#         x = self.fc2(x) #relu
#         x = self.fc3(x) #relu
#         x = F.sigmoid(self.fc4(x))

#         return x

# loader = torch.utils.data.DataLoader(dataset,batch_size=4)
# multimodal_model = MultimodalModel(text_module, image_module)
# multimodal_model.to(device)
# criterion = nn.BCELoss()
# optimizer = optim.Adam(multimodal_model.parameters(), lr=0.003, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)

# def train(model, data_loader, epochs, optimizer, criterion):
#     for i in range(epochs):
#         running_loss = 0.0
#         for i, data in enumerate(data_loader,0):
#             labels = data["label"]
#             image_data = data["image"]
#             text_data = data["text"]

#             optimizer.zero_grad()
#             labels = labels.to(device)
#             image_data = image_data.to(device)
#             text_data = text_data.to(device)

#             outputs = model.forward(image_data, text_data)
#             labels = labels.unsqueeze(1).float()

#             outputs = outputs.to(device)

#             matches  = [torch.argmax(i)==torch.argmax(j) for i, j in zip(outputs, labels)]
#             in_sample_acc = matches.count(True)/len(matches)

#             loss = criterion(outputs, labels)

#             loss.backward()
#             optimizer.step()
#             running_loss += loss.item()
#             if i % 2000 == 1999:    # print every 2000 mini-batches
#                 print(f'[{i + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')
#                 running_loss = 0.0
#     print("Finished Training")

# train(multimodal_model, loader, 10, optimizer, criterion)

"""#Testing Code"""

# multimodal_model = MultimodalModel(text_module, image_module)
# sample_img = dataset[0]['image']
# sample_img = sample_img[None, :,:]
# sample_text = dataset[0]['text']



# x = multimodal_model.forward(sample_img, sample_text)

# x = torch.randn((4,1,15))
# print(torch.squeeze(x).shape)

"""Run RHis"""

class MisogynousDataset(torch.utils.data.Dataset):

    def __init__(self,data_path,img_dir,image_transform,tokenizer,balance=False,dev_limit=None,random_state=0):

        self.samples_frame = pd.read_csv(
            data_path)
        self.samples_frame = self.samples_frame.reset_index(drop=True)
        self.samples_frame.file_name = self.samples_frame.apply(
            lambda row: (os.path.join(img_dir,row.file_name)), axis=1)
        self.image_transform = image_transform
        self.tokenizer = tokenizer

    def __len__(self):
        return len(self.samples_frame)

    def __getitem__(self, idx):
        if torch.is_tensor(idx):
            idx = idx.tolist()

        image = Image.open(
            self.samples_frame.loc[idx, "file_name"]
        ).convert("RGB")
        image = self.image_transform(image)

        text = self.samples_frame.loc[idx,'Text Transcription']
        text = self.tokenizer.encode(text, max_length = 15, truncation=True, return_tensors="pt",padding='max_length')

        label = torch.Tensor(
                [self.samples_frame.loc[idx, "misogynous"]]
            ).long().squeeze()

        sample = {
                "label" : label, 
                "image": image, 
                "text": text}

        return sample

image_transform = torchvision.transforms.Compose([
                                                  torchvision.transforms.Resize(size=(350, 350)),
                                                  torchvision.transforms.ToTensor()]) 
tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
dataset = MisogynousDataset(data_path = '/content/preprocessed.csv',
                            img_dir = '/content/TRAINING',
                            image_transform = image_transform,
                            tokenizer=tokenizer)

loader = torch.utils.data.DataLoader(dataset,batch_size=4)
for i,data in enumerate(loader):
    print("LABEL FUCK", data['label'].shape)
    print("IMAGE FUCK", data['image'].shape)
    print("TEXT FUCK", data['text'].shape)
    if i==5:
        break

class MultimodalModel(torch.nn.Module):
    def __init__(self,language_module,vision_module,loss_fn):

        super(MultimodalModel, self).__init__()
        self.language_module = language_module
        self.vision_module = vision_module
                
        self.fc1 = nn.Linear(12032, 4096)
        self.fc2 = nn.Linear(4096, 256)
        self.fc3 = nn.Linear(256, 64)
        self.fc4 = nn.Linear(64, 1)
        self.loss_fn = loss_fn
        self.dropout = torch.nn.Dropout(0.5)
        
    def forward(self, text, image, label=None):
        text_features = self.language_module(torch.squeeze(text))
        reshaped_text_features = torch.flatten(text_features.last_hidden_state, start_dim=1)
        image_features = torch.nn.functional.relu(self.vision_module(image))

        combined = torch.cat(
            [reshaped_text_features, image_features], dim=1
        )
        fused = self.dropout(
            torch.nn.functional.relu(
            self.fc1(combined)
            )
        )
        out = self.fc2(fused)
        out = self.fc3(out)
        out = self.fc4(out)
        pred = torch.nn.functional.sigmoid(out)
        return pred

def train(model, data_loader, epochs, optimizer, criterion):
    for i in range(epochs):
        running_loss = 0.0
        for i, data in enumerate(data_loader,0):
            labels = data["label"]
            image_data = data["image"]
            text_data = data["text"]

            optimizer.zero_grad()
            labels = labels.to(device)
            image_data = image_data.to(device)
            text_data = text_data.to(device)

            outputs = model.forward(text_data, image_data)
            labels = labels.unsqueeze(1).float()

            outputs = outputs.to(device)

            matches  = [torch.argmax(i)==torch.argmax(j) for i, j in zip(outputs, labels)]
            in_sample_acc = matches.count(True)/len(matches)

            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            if i % 2000 == 1999:    # print every 2000 mini-batches
                print(f'[{i + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')
                print('ACCURACY OF THE FUCKINGMODEL IS', in_sample_acc)
                running_loss = 0.0
    print("Finished Training")

class Identity(nn.Module):
    def __init__(self):
        super(Identity, self).__init__()
        
    def forward(self, x):
        return x

vision_module = models.resnet18(pretrained=True)
vision_module.fc = Identity()

text_module = RobertaModel.from_pretrained('roberta-base')
misogyny_model = MultimodalModel(text_module, vision_module)
misogyny_model.to(device)
criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(misogyny_model.parameters(), lr=0.003, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
train(misogyny_model, loader, 10, optimizer, criterion)

# class MisogynousMemesModel(pl.LightningModule):
#     def __init__(self, hparams):
#         for data_key in ["img_dir"]:
#             # ok, there's one for-loop but it doesn't count
#             if data_key not in hparams.keys():
#                 raise KeyError(
#                     f"{data_key} is a required hparam in this model"
#                 )
        
#         super(MisogynousMemesModel, self).__init__()
#         self.hparams = hparams
#         self.output_path = Path(
#             self.hparams.get("output_path", "/content/model-outputs")
#         )
#         self.output_path.mkdir(exist_ok=True)
        
#         self.train_dataset = self.hparams['dataset']

#         self.model = self._build_model()
#         self.trainer_params = self._get_trainer_params()
    
#     ## Required LightningModule Methods (when validating) ##
    
#     def forward(self, text, image, label=None):
#         return self.model(text, image, label)

#     def training_step(self, batch, batch_nb):
#         preds, loss = self.forward(
#             text=batch["text"], 
#             image=batch["image"], 
#             label=batch["label"]
#         )
        
#         return {"loss": loss}

   
#     def configure_optimizers(self):
#         optimizers = torch.optim.AdamW(
#                 self.model.parameters(), 
#                 lr=self.hparams.get("lr", 0.003)
#             )
#         schedulers = torch.optim.lr_scheduler.CosineAnnealingLR(optimizers, T_max=10)
        
        
#         return [optimizers], [schedulers]
    
#     def train_dataloader(self):
#         return torch.utils.data.DataLoader(
#             self.train_dataset, 
#             shuffle=True, 
#             batch_size=self.hparams.get("batch_size", 4)
#             #num_workers=self.hparams.get("num_workers", 16)
#         )

#     ## Convenience Methods ##
    
#     def fit(self):
#         self._set_seed(self.hparams.get("random_state", 42))
#         self.trainer = pl.Trainer(**self.trainer_params)
#         self.trainer.fit(self)
        
#     def _set_seed(self, seed):
#         random.seed(seed)
#         np.random.seed(seed)
#         torch.manual_seed(seed)
#         if torch.cuda.is_available():
#             torch.cuda.manual_seed_all(seed)
    
#     def _build_model(self):
#         class Identity(nn.Module):
#             def __init__(self):
#                 super(Identity, self).__init__()
                
#             def forward(self, x):
#                 return x

#         vision_module = models.resnet18(pretrained=True)
#         vision_module.fc = Identity()

#         language_module = RobertaModel.from_pretrained('roberta-base')
       

#         return MultimodalModel(
#             #num_classes=self.hparams.get("num_classes", 2),
#             loss_fn=torch.nn.BCEWithLogitsLoss(),
#             language_module=language_module,
#             vision_module=vision_module,
#             #dropout_p=self.hparams.get("dropout_p", 0.1)
#         )
    
#     def _get_trainer_params(self):
#         checkpoint_callback = pl.callbacks.ModelCheckpoint(
#             dirpath=self.output_path,
#             mode=self.hparams.get(
#                 "checkpoint_monitor_mode", "min"
#             ),
#             verbose=self.hparams.get("verbose", True)
#         )

#         # early_stop_callback = pl.callbacks.EarlyStopping(
#         #     monitor=self.hparams.get(
#         #         "early_stop_monitor", "avg_val_loss"
#         #     ),
#         #     min_delta=self.hparams.get(
#         #         "early_stop_min_delta", 0.001
#         #     ),
#         #     patience=self.hparams.get(
#         #         "early_stop_patience", 3
#         #     ),
#         #     verbose=self.hparams.get("verbose", True),
#         # )

#         trainer_params = {
#             "checkpoint_callback": checkpoint_callback,
#             #"early_stop_callback": early_stop_callback,
#             #"default_save_path": self.output_path,
#             "accumulate_grad_batches": self.hparams.get(
#                 "accumulate_grad_batches", 1
#             ),
#             "gpus": self.hparams.get("n_gpu", 1),
#             "max_epochs": self.hparams.get("max_epochs", 10)
#             # "gradient_clip_val": self.hparams.get(
#             #     "gradient_clip_value", 1
#             # )
#         }
#         return trainer_params
            
#     def make_submission_frame(self, test_dataset):
#         submission_frame = pd.DataFrame(
#             columns=["proba", "label"]
#         )
#         test_dataloader = torch.utils.data.DataLoader(
#             test_dataset, 
#             shuffle=False, 
#             batch_size=self.hparams.get("batch_size", 4), 
#             num_workers=self.hparams.get("num_workers", 16))
#         for batch in tqdm(test_dataloader, total=len(test_dataloader)):
#             preds, _ = self.model.eval().to("cpu")(
#                 batch["text"], batch["image"]
#             )
#             submission_frame.loc[batch["id"], "proba"] = preds[:, 1]
#             submission_frame.loc[batch["id"], "label"] = preds.argmax(dim=1)
#         submission_frame.proba = submission_frame.proba.astype(float)
#         submission_frame.label = submission_frame.label.astype(int)
#         return submission_frame

# hparams = {
#     "img_dir": "/content/TRAINING",
    
#     "output_path": "/content/model-outputs",
#     "dev_limit": None,
#     "lr": 0.003,
#     "max_epochs": 10,
#     "n_gpu": 1,
#     "batch_size": 4,
#     # allows us to "simulate" having larger batches 
#     "accumulate_grad_batches": 16,
#     "early_stop_patience": 3,
#     "dataset" : dataset
# }

# hateful_memes_model = MisogynousMemesModel(hparams=hparams)
# hateful_memes_model.fit()



"""# Early Fusion"""

class TextModule(nn.Module):

    def __init__(self):
        super(TextModule, self).__init__()
        self.roberta = RobertaModel.from_pretrained('roberta-base')
        self.fc1 = nn.Linear(15*768, 1024)
        self.fc2 = nn.Linear(1024, 256)
        self.fc3 = nn.Linear(256, 64)

    def forward(self, text_batch):
        text_features = self.roberta(torch.squeeze(text_batch))
        reshaped_text_features = torch.reshape(text_features.last_hidden_state, (4, 15*768))
        x =  F.relu(self.fc1(reshaped_text_features))
        x =  F.relu(self.fc2(x))
        x =  F.relu(self.fc3(x))
        
        return x

class ImageModule(nn.Module):

    def __init__(self):
        super(ImageModule, self).__init__()

        class Identity(nn.Module):
            def _init_(self):
                super(Identity, self).__init__()
            
            def forward(self, x):
                return x  

        self.resnet = models.resnet18(pretrained=True)
        self.resnet.fc = Identity()
        self.fc1 = nn.Linear(512, 256)
        self.fc2 = nn.Linear(256, 64)


    def forward(self, image_batch):
        image_features = self.resnet(image_batch)
        x = F.relu(self.fc1(image_features))
        x = F.relu(self.fc2(x))

        return x 

class MultimodalModel(nn.Module):
    def __init__(self, text_module, image_module):
        super(MultimodalModel, self).__init__()
        self.text_module = text_module
        self.image_module = image_module
        self.fc1 = nn.Linear(128, 64)
        self.fc2 = nn.Linear(64, 32)
        self.fc3 = nn.Linear(32, 16)
        self.fc4 = nn.Linear(16, 1)


    def forward(self, text_batch, image_batch):
        text_features = self.text_module(text_batch)
        image_features = self.image_module(image_batch)
        concat_repr = torch.cat((text_features, image_features),dim=1)
        x = F.relu(self.fc1(concat_repr))
        x = F.relu(self.fc2(x))
        x = F.relu(self.fc3(x))
        x = torch.sigmoid(self.fc4(x))

        return x

a = torch.randn((4,64))
b = torch.cat((a,a),dim=1)
print(b.shape)

def train(model, data_loader, epochs, optimizer, criterion):
    for i in range(epochs):
        running_loss = 0.0
        for i, data in enumerate(data_loader,0):
            labels = data["label"]
            image_data = data["image"]
            text_data = data["text"]

            optimizer.zero_grad()
            labels = labels.to(device)
            image_data = image_data.to(device)
            text_data = text_data.to(device)

            outputs = model.forward(text_data, image_data)
            labels = labels.unsqueeze(1).float()

            outputs = outputs.to(device)

            matches  = [torch.argmax(i)==torch.argmax(j) for i, j in zip(outputs, labels)]
            in_sample_acc = matches.count(True)/len(matches)

            loss = criterion(outputs, labels)

            loss.backward()
            optimizer.step()
            running_loss += loss.item()
            if i % 2000 == 1999:    # print every 2000 mini-batches
                print(f'[{i + 1}, {i + 1:5d}] loss: {running_loss / 2000:.3f}')
                print('ACCURACY OF THE FUCKINGMODEL IS', in_sample_acc)
                running_loss = 0.0
    print("Finished Training")

image_module = ImageModule()
text_module = TextModule()
misogyny_model = MultimodalModel(text_module, image_module)
misogyny_model.to(device)
criterion = nn.BCEWithLogitsLoss()
optimizer = optim.Adam(misogyny_model.parameters(), lr=0.003, betas=(0.9, 0.999), eps=1e-08, weight_decay=0, amsgrad=False)
train(misogyny_model, loader, 10, optimizer, criterion)

