# -*- coding: utf-8 -*-
"""Multimodal.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1mVYW3ed8bITTaRTJ_D-0Z6OtzHl0gvPG
"""

!pip install transformers

from google.colab import drive
drive.mount('/content/drive')

import pandas as pd
import numpy as np
data = pd.read_csv('/content/preprocessed.csv')
data = data.drop(['Unnamed: 0','shaming','stereotype','objectification','violence'],axis=1)
data.head()

data['Text Transcription'][5]

total = []
for i,text in enumerate(data['Text Transcription']):
    total.append(len(text.split()))
    if i%200==0:
        print(i,total)

print(np.median(total))

import numpy as np
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import torch
import torchvision
import torchtext
from PIL import Image
from transformers import RobertaForSequenceClassification, RobertaTokenizer
from transformers import AutoTokenizer, AutoModel
import torchvision.models as models
import torch.nn as nn

data = pd.read_csv('/content/preprocessed.csv')
data = data.drop(['Unnamed: 0','shaming','stereotype','objectification','violence'],axis=1)
data.head()

len(data)

!unzip /content/drive/MyDrive/Misogyny_Detection/training.zip -d /content/

for i in range(20):
    img = mpimg.imread('/content/TRAINING/' + os.listdir('/content/TRAINING')[i])
    arr = np.asarray(img)
    print(arr.shape)

image_transform = torchvision.transforms.Compose([
                                                  torchvision.transforms.Resize(size=(350, 350)),
                                                  torchvision.transforms.ToTensor()])

class MisogynyDataset(torch.utils.data.Dataset):
    def __init__(self,data,img_dir,image_transform,tokenizer):
        self.data = pd.read_csv(data)
        self.image_transform = image_transform

        self.tokenizer = tokenizer
        self.data = self.data.reset_index(drop=True)
        self.data.file_name = self.data.apply(
            lambda row: (os.path.join(img_dir,row.file_name)), axis=1)

    def __len__(self):
        return len(self.data)

    def __getitem__(self,idx):
        if torch.is_tensor(idx):
            idx.tolist()

        image = Image.open(self.data.loc[idx,'file_name']).convert('RGB')
        image = self.image_transform(image)

        text = self.data.loc[idx,'Text Transcription']
        text = self.tokenizer.encode(text, max_length = 25, truncation=True, return_tensors="pt",padding='max_length')

        label = torch.Tensor([self.data.loc[idx,'misogynous']]).long().squeeze()

        item = {
            'image' : image,
            'text' : text,
            'label' : label
        }      

        return item

dataset = MisogynyDataset('/content/preprocessed.csv','/content/TRAINING',image_transform,tokenizer)

loader = torch.utils.data.DataLoader(dataset,batch_size=4)

for i,data in enumerate(loader):
    print(i,data['image'].shape)
    if i==10:
        break

class MultimodalModel(torch.nn.Module):
    def __init__(self, text_module, vision_module,):
        super(MultimodalModel, self).__init__()
        self.text_module = text_module
        self.vision_module = vision_module 

    def forward(self, image_batch, text_batch):
        image_features = self.vision_module(image_batch) #
        text_features = self.vision_module(text_batch) #(1, 8, 768)
        reshaped_text_features = torch.reshape(text_features, 1*8*758)
        inter_repr = torch.cat(#image_feature_shape, reshaped_text_feature)
        #fc1
        #fc2
        #output layer

#Text Module
from transformers import RobertaTokenizer, RobertaModel

tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
text_module = RobertaModel.from_pretrained('roberta-base')

import torchvision.models as models
import torch.nn as nn
import numpy as np

class Identity(nn.Module):
    def __init__(self):
        super(Identity, self).__init__()
        
    def forward(self, x):
        return x


image_module = models.resnet18(pretrained=True)
image_module.fc = Identity()
print(image_module)

#loader = torch.utils.data.DataLoader(dataset,batch_size=4)
#def train(model, data_loader, epochs):
    # for i in range(epochs):
    #     running_loss = 0.0
    #     for i, data in enumerate(data_loader, 0):
    #         labels = data["label"]
    #         image_data = data["image"]
    #         text_data = data["text"]

    #         optimizer.zero_grad()

    #         outputs = model.forward(image_data, text_data)
    #         loss = criterion(outputs, labels)

    #         loss.backward()
    #         optimizer.step()
    #         running_loss += loss.item()

for i,data in enumerate(loader):
    labels = data["label"]
    image_data = data["image"]
    text_data = data["text"]

    outputs = RobertaModel(**text_data)

