# -*- coding: utf-8 -*-
"""CNN-Daily Mail summarization(T5).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_FADaKJjcxfCwO21yt4acrEo6QM4nPmQ

# Imports
"""

!pip install datasets

!pip install transformers
!pip install wandb
!pip install sentencepiece
!pip install pytorch-lightning
!pip install sentencepiece

from torch import cuda
device = 'cuda' if cuda.is_available() else 'cpu'
print(device)

from datasets import load_dataset
import matplotlib.pyplot as plt
import torch
from torch.utils.data import Dataset, DataLoader 
import numpy as np
import pandas as pd
from transformers import (
    T5ForConditionalGeneration,
    T5Tokenizer
)
import wandb
#import pytorch_lightning as pl

!wandb login

"""# EDA"""

dataset = load_dataset("cnn_dailymail", '3.0.0')

print(dataset.keys())
print(dataset['train'][1].keys())

print(dataset['train']['article'][112])

text = dataset['train']['article'][34]
print("1.", text)
_, text = text.split('--', 1)
print("2.", text)

print("Train data size:\t", len(dataset['train']))
print("Val data size:\t", len(dataset['validation']))
print("Test data size:\t", len(dataset['validation']))
print("Sample input\t:", dataset['train'][0]['article'])
print("Sample output\t:", dataset['train'][0]['highlights'])

est_dataset = dataset['train'].select(list(range(0,200)))
article_len = []
highlight_len = []

for example in est_dataset:
    article_example = example['article']
    article_example = article_example.replace('\n', '')
    article_words = article_example.split()
    article_len.append(len(article_words))
    highlight_example = example['highlights']
    highlight_example = highlight_example.replace('\n', '')
    highlight_words = highlight_example.split()
    highlight_len.append(len(highlight_words))

plt.hist(article_len)
plt.show()

plt.hist(highlight_len)
plt.show()

print('Average length of article:\t', sum(article_len)/len(article_len))
print('Average length of highlights:\t', sum(highlight_len)/len(highlight_len))

"""# Dataset"""

class CnnDailyMail(Dataset):
    def __init__(self, split_type, tokenizer, input_len, output_len, num_samples=None):
        self.dataset = load_dataset('cnn_dailymail', '3.0.0', 'all', split=split_type)
        if num_samples:
            self.dataset = self.dataset.select(list(range(0, num_samples)))
        self.input_len = input_len
        self.output_len = output_len
        self.tokenizer = tokenizer

    def __len__(self):
        return self.dataset.shape[0]
    
    def clean_text(self, text):
        text = text.replace("NEW:", '')
        if '--' in text[:10]:
            _,text = text.split('--', 1)
        text = text.replace('\n', '')
        text = text.replace('"', '')
        #text = text.lower()
        return text

    def convert_to_features(self, batch):
        input = self.clean_text(batch['article'])      
        target = self.clean_text(batch['highlights'])
        source = self.tokenizer.batch_encode_plus([input], 
                                                  max_length = self.input_len,
                                                  padding='max_length', truncation=True, return_tensors='pt')
        
        targets = self.tokenizer.batch_encode_plus([target], 
                                                  max_length = self.input_len,
                                                  padding='max_length', truncation=True, return_tensors='pt')
        
        return source, targets

    def __getitem__(self, idx):
        source, targets = self.convert_to_features(self.dataset[idx])
        source_ids = source['input_ids'].squeeze()
        target_ids = targets['input_ids'].squeeze()

        source_mask = source['attention_mask'].squeeze()
        target_mask = targets['attention_mask'].squeeze()

        return {'source_ids': source_ids, 'source_mask': source_mask, 
               'target_ids': target_ids, 'target_mask': target_mask}

tokenizer = T5Tokenizer.from_pretrained('t5-small')
demo_data = CnnDailyMail('validation', tokenizer, 600, 40, num_samples=5000)

len(demo_data)

eg_data = demo_data[4999]
print("Shape of Tokenized Text: ", eg_data['source_ids'].shape)
print("Decode Text: ", tokenizer.decode(eg_data['source_ids']))
print("Decode Summary: ", tokenizer.decode(eg_data['target_ids']))
del demo_data, tokenizer

"""# Training and validation"""

def lmap(f, x):
    return list(map(f, x))


def ids_to_clean_text(ids, tokenizer):
    text = tokenizer.batch_decode(ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
    return lmap(str.strip, text)

def train(epoch, tokenizer, model, device, loader, optim):
    model.train()
    for i, data in enumerate(loader, 0):
        y = data['target_ids'].to(device, dtype=torch.long)
        y_ids = y[:,:-1].contiguous()
        lm_labels = y[:,1:].clone().detach()
        lm_labels[y[:, 1:] == tokenizer.pad_token_id] = -100
        ids = data['source_ids'].to(device, dtype=torch.long)
        mask = data['source_mask'].to(device, dtype=torch.long)

        outputs = model(input_ids=ids, attention_mask = mask, decoder_input_ids=y_ids, labels = lm_labels)
        loss = outputs[0]
        
        if i%10==0:
            wandb.log({"Training loss":loss.item()})
        if i%100==0:
            print(f"Epoch:\t{epoch+1} \t Loss :\t{loss.item()}")
            
        optim.zero_grad()
        loss.backward()
        optim.step()

def validate(epoch, tokenizer, model, device, loader):
    model.eval()
    preds = []
    truths = []
    with torch.no_grad():
        for i, data in enumerate(loader, 0):
            y = data['target_ids'].to(device, dtype=torch.long)
            ids = data['source_ids'].to(device, dtype=torch.long)
            mask = data['source_mask'].to(device, dtype=torch.long)

            generated_ids = model.generate(input_ids = ids,
                                           attention_mask = mask,
                                           max_length = 45,
                                           num_beams = 2,
                                           length_penalty = 1.0,
                                           early_stopping=True)

            pred = [tokenizer.decode(g, skip_special_tokens=True, clean_up_tokenization_spaces=True) for g in generated_ids]
            truth = [tokenizer.decode(t, skip_special_tokens=True, clean_up_tokenization_spaces=True) for t in y]
            if i%100==0:
                print(f"{i} Completed")
            preds.extend(pred)
            truths.extend(truth)
        return preds, truths

"""## T5 small"""

model = None
def main():
    wandb.init(project='cnn-dailymail-summarization')
    config = wandb.config
    config.TRAIN_BATCH_SIZE = 4
    config.VALID_BATCH_SIZE = 4
    config.TRAIN_EPOCHS = 2
    #config.VAL_EPOCHS = 1
    config.LEARNING_RATE = 0.001
    config.SEED = 42
    config.MAX_LEN = 680
    config.SUMMARY_LEN = 45

    torch.manual_seed(config.SEED)
    
    tokenizer = T5Tokenizer.from_pretrained('t5-small')

    train_dataset = CnnDailyMail('train', tokenizer, config.MAX_LEN, config.SUMMARY_LEN, num_samples=60000)
    print(f"Size of train_dataset:\t{len(train_dataset)}")
    val_dataset = CnnDailyMail('validation', tokenizer, config.MAX_LEN, config.SUMMARY_LEN, num_samples=5000)
    print(f"Size of val_dataset:\tP{len(val_dataset)}")

    train_params = {
        'batch_size':config.TRAIN_BATCH_SIZE,
        'shuffle':True,
        'num_workers':0
    }
    val_params = {
        'batch_size':config.VALID_BATCH_SIZE,
        'shuffle':False,
        'num_workers':0
    }

    train_loader = DataLoader(train_dataset, **train_params)
    val_loader = DataLoader(val_dataset, **val_params)
    val_loader = DataLoader(val_dataset, **val_params)

    model = T5ForConditionalGeneration.from_pretrained('t5-small')
    model = model.to(device)

    optim = torch.optim.Adam(params=model.parameters(), lr=config.LEARNING_RATE)
    wandb.watch(model, log='all')

    #Train
    for itr in range(config.TRAIN_EPOCHS):
        train(itr, tokenizer, model, device, train_loader, optim)

    if itr:
        print(f"itr:\t{itr}")
    #Validate
    preds, truths = validate(1, tokenizer, model, device, val_loader)
    output_file = pd.DataFrame({'Generated Summary': preds, 'Ground Truth': truths})
    output_file.to_csv('/content/summarizartion_report.csv')

    torch.save(model.state_dict(), '/content/T5-small-summary.pt')

if __name__=='__main__':
    main()

cuda.empty_cache()

"""## T5 Base"""

model = None
def main():
    wandb.init(project='cnn-dailymail-summarization')
    config = wandb.config
    config.TRAIN_BATCH_SIZE = 2
    config.VALID_BATCH_SIZE = 2
    config.TRAIN_EPOCHS = 2
    #config.VAL_EPOCHS = 1
    config.LEARNING_RATE = 0.0015
    config.SEED = 42
    config.MAX_LEN = 680
    config.SUMMARY_LEN = 45

    torch.manual_seed(config.SEED)
    
    tokenizer = T5Tokenizer.from_pretrained('t5-base')

    train_dataset = CnnDailyMail('train', tokenizer, config.MAX_LEN, config.SUMMARY_LEN, num_samples=60000)
    print(f"Size of train_dataset:\t{len(train_dataset)}")
    val_dataset = CnnDailyMail('validation', tokenizer, config.MAX_LEN, config.SUMMARY_LEN, num_samples=5000)
    print(f"Size of val_dataset:\tP{len(val_dataset)}")

    train_params = {
        'batch_size':config.TRAIN_BATCH_SIZE,
        'shuffle':True,
        'num_workers':0
    }
    val_params = {
        'batch_size':config.VALID_BATCH_SIZE,
        'shuffle':False,
        'num_workers':0
    }

    train_loader = DataLoader(train_dataset, **train_params)
    val_loader = DataLoader(val_dataset, **val_params)
    
    model = T5ForConditionalGeneration.from_pretrained('t5-base')
    model = model.to(device)

    optim = torch.optim.Adam(params=model.parameters(), lr=config.LEARNING_RATE)
    wandb.watch(model, log='all')

    #Train
    for itr in range(config.TRAIN_EPOCHS):
        train(itr, tokenizer, model, device, train_loader, optim)

    if itr:
        print(f"itr:\t{itr}")
    #Validate
    preds, truths = validate(1, tokenizer, model, device, val_loader)
    preds, truths = validate(1, tokenizer, model, device, val_loader
                )
    output_file = pd.DataFrame({'Generated Summary': preds, 'Ground Truth': truths})
    output_file.to_csv('/content/summarizartion_report_t5base.csv')

    torch.save(model.state_dict(), '/content/T5-base-summary.pt')

if __name__=='__main__':
    main()

cuda.clear_cache()

