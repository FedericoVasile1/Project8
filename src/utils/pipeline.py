import random
import os

import numpy as np
import torch
from torchvision import transforms, datasets

from src.datasets.BiologicalDataset import BiologicalDataset
from src.models.mc_dropout import M_3Conv3FC, M_AlexNet
from src.models.var_inf import V_3Conv3FC, V_AlexNet


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True

def load_dataset(dataset_name, val_split, batch_size, num_workers=4, mode='train'):
    if mode == 'train':
        train = True
        dataset = {phase: None for phase in ['train', 'val']}
    elif mode == 'test':
        train = False
        dataset = {'test': None}
    else:
        raise Exception('Wrong mode parameter; ' + mode + ' is not supported.'
                        ' Supported modes: [train|test]')

    if dataset_name == 'MNIST':
        transform = transforms.Compose([
            #transforms.Resize(32),  # in order to have the same size as MNIST and CRC
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,)),
        ])
        dataset[mode] = datasets.MNIST(root=os.path.join(os.getcwd(), 'data'),
                                       train=train,
                                       download=True,
                                       transform=transform)
    elif dataset_name == 'CIFAR10':
        transform = transforms.Compose([
            transforms.ToTensor(),
            # values taken from: https://github.com/kuangliu/pytorch-cifar/issues/19
            transforms.Normalize(mean=(0.4914, 0.4822, 0.4465), std=(0.247, 0.243, 0.261)),
        ])
        dataset[mode] = datasets.CIFAR10(root=os.path.join(os.getcwd(), 'data'),
                                         train=train,
                                         download=True,
                                         transform=transform)
    elif dataset_name == 'CRC':
        dataset[mode] = BiologicalDataset(train)
    else:
        raise Exception('Wrong --dataset option; ' + dataset_name + ' is not supported.'
                        ' Supported datasets: [CRC|MNIST|CIFAR10]')

    dataloader = {}
    if train:
        n_val_samples = int(len(dataset['train']) * val_split)
        n_train_samples = len(dataset['train']) - n_val_samples
        dataset['train'], dataset['val'] = torch.utils.data.random_split(dataset['train'],
                                                                         [n_train_samples, n_val_samples])
        dataloader['train'] = torch.utils.data.DataLoader(dataset['train'],
                                                          batch_size,
                                                          True,
                                                          num_workers=num_workers)
        dataloader['val'] = torch.utils.data.DataLoader(dataset['val'],
                                                        batch_size,
                                                        False,
                                                        num_workers=num_workers)
    else:
        dataloader['test'] = torch.utils.data.DataLoader(dataset['test'],
                                                         batch_size,
                                                         False,
                                                         num_workers=num_workers)

    return dataloader

def load_model(model, input_channels, num_classes, activation_function, dropout, priors, layer_type):
    if model == 'MCDROP3CONV3FC':
        model = M_3Conv3FC.M3Conv3FC(num_classes, input_channels, dropout, activation_function)
    elif model == 'VARINF3CONV3FC':
        model = V_3Conv3FC.V3Conv3FC(num_classes, input_channels, priors, layer_type, activation_function)
    elif model == 'MCDROPALEXNET':
        model = M_AlexNet.MAlexNet(num_classes, input_channels, dropout, activation_function)
    elif model == 'VARINFALEXNET':
        model = V_AlexNet.VAlexNet(num_classes, input_channels, priors, layer_type, activation_function)
    else:
        raise Exception('Wrong --model option; ' + model + ' is not supported.'
                        ' Supported models: [MCDROP3CONV3FC|VARINF3CONV3FC|MCDROPALEXNET|VARINFALEXNET]')
    return model