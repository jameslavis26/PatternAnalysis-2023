import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision
from torchvision import transforms
from torchvision.utils import save_image
from tqdm import tqdm
from torch.utils.data import DataLoader, Dataset
import time
import numpy as np
from enum import Enum
from PIL import Image
from torch.utils.data.sampler import SubsetRandomSampler
import matplotlib.pyplot as plt
from platform import node

# IO Paths
match node():                                                    # root of data dir
    case 'Its-a-Macbook.modem':
        DATA_PATH = '/Users/samson/Documents/UQ/COMP3710/data/keras_png_slices_data/'
    case 'Its_a_PC':
        DATA_PATH = 'D:/Documents/UQ/COMP3710/data/keras_png_slices_data/'
    case _:
        if 'vgpu' in node():
            DATA_PATH = '/home/Student/s4667620/mac_mount/data/keras_png_slices_data/'
        else:
            raise Exception(f'Unknown hostname: {node()}. Please add your DATA_PATH in utils.py.')
TRAIN_INPUT_PATH = DATA_PATH + 'keras_png_slices_train/'         # train input
VALID_INPUT_PATH = DATA_PATH + 'keras_png_slices_validate/'      # valid input
TEST_INPUT_PATH = DATA_PATH + 'keras_png_slices_test/'           # test input
VALID_TARGET_PATH = DATA_PATH + 'keras_png_slices_seg_validate/' # train target
TRAIN_TARGET_PATH = DATA_PATH + 'keras_png_slices_seg_train/'    # valid target
TEST_TARGET_PATH = DATA_PATH + 'keras_png_slices_seg_test/'      # test target
MODEL_PATH = './vqvae2.pth'         # trained model
TRAIN_TXT = './oasis_train.txt'     # info of img for train
VALID_TXT = './oasis_valid.txt'     # info of img for valid
TEST_TXT = './oasis_test.txt'       # info of img for test
GENERATED_IMG_PATH = 'gened_imgs/'

# Configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
INPUT_DIM = 256*256 # dimension of Input
Z_DIM = 10          # dimension of Latent Space
H_DIM = 1600        # dimension of Hidden Layer
NUM_EPOCHS = 20     # number of epoch
LR_RATE = 3e-4      # learning rate
