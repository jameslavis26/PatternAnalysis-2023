import torch
import torch.utils.data
import torchvision.datasets as dset
import torchvision.transforms.v2 as transforms
import numpy as np
import matplotlib.pyplot as plt
import random
import os.path

import CONSTANTS

# global variables
batch_size = 32
workers = 0

# alias for testing on different machines
LOCAL = -1
GLOBAL = 1

machine = GLOBAL
if machine == GLOBAL:
    # get filepaths from CONSTANTS.py
    train_path = CONSTANTS.TRAIN_PATH
    test_path = CONSTANTS.TEST_PATH
    savepath = CONSTANTS.RESULTS_PATH
else: 
    # configureable filepaths for local testing
    train_path = '/Users/minhaosun/Documents/COMP3710_local/data/AD_NC/train'
    test_path = '/Users/minhaosun/Documents/COMP3710_local/data/AD_NC/test'
    savepath = '/Users/minhaosun/Documents/COMP3710_local/project_results'

# transforms
Siamese_train_transforms = transforms.Compose([
    transforms.ToTensor(),
    transforms.RandomCrop(240, 20, padding_mode='constant'),
])

classifier_train_transforms = transforms.Compose([
    transforms.ToTensor(),
    transforms.RandomCrop(240, 20, padding_mode='constant'),
])

test_transforms = transforms.Compose([
    transforms.ToTensor(),
    transforms.CenterCrop(240),
])


class PairedDataset(torch.utils.data.Dataset):
    def __init__(self, 
                dataset:torch.utils.data.Dataset, 
                show_debug_info:bool, 
                random_seed=None) -> None:
        super().__init__()
        self.dataset = dataset
        self.dataset_size = len(self.dataset)
        self.debug_mode = show_debug_info
        self.imagefolder = self.dataset.dataset

        # for reproducibility
        if random_seed is not None:
            random.seed(random_seed)
            torch.random.manual_seed(random_seed)

    def __len__(self) -> int:
        return self.dataset_size

    def __getitem__(self, index: int):
        """
        returns [img1, img2, similarity] or [img1, img2, similarity, filepath1, filepath2]
        where:
            img1 and img2 are tensor representations of images
            similarity is 1 if the two images are of the same class and 0 otherwise
            filepath1 and filepath2 are strings representing the last 15 characters
                of the images' filepaths excluding the .jpeg extension
        """
        img1, label1 = self.dataset[index]
        similarity = random.randint(0, 1)

        match_found = False
        while not match_found:
            choice = random.randint(0, self.dataset_size - 1)
            # make sure we do not pair the same image against itself
            if choice == index:
                continue

            filepath1 = self.imagefolder.imgs[self.dataset.indices[index]][0]
            filepath2 = self.imagefolder.imgs[self.dataset.indices[choice]][0]

            img2, label2 = self.dataset[choice]
            if similarity == 1:
                match_found = label1 == label2
            else:
                match_found = label1 != label2

        # only include the filepaths in the dataset if specifically requested
        if self.debug_mode:
            return img1, img2, similarity, filepath1[-20:-5], filepath2[-20:-5]
        # otherwise save some memory
        return img1, img2, similarity
    
    def showing_debug_info(self) -> bool:
        return self.debug_mode


def load_data(training:bool, Siamese:bool, random_seed=None, train_proportion=0.8) -> torch.utils.data.DataLoader:
    
    path = train_path
    if training:
        if Siamese:
            transforms = Siamese_train_transforms
        else:
            transforms = classifier_train_transforms
    else:
        # validation set uses the same transforms as the test set
        transforms = test_transforms

    if random_seed is not None:
        random.seed(random_seed)
        torch.random.manual_seed(random_seed)

    source = dset.ImageFolder(root=path, transform=transforms)
    patient_ids = set()
    
    for i in range(len(source)):
        filepath = source.imgs[i][0]
        start, end = filepath.rfind(os.path.sep) + 1, filepath.rfind('_')
        patient_id = filepath[start:end]
        patient_ids.add(patient_id)
    
    patient_ids = list(patient_ids)
    split_point = int(train_proportion*len(patient_ids))

    if training:
        patients = patient_ids[:split_point]
    else: 
        patients = patient_ids[split_point:]

    indices_to_be_included = []

    for i in range(len(source)):
        filepath = source.imgs[i][0]
        start, end = filepath.rfind(os.path.sep) + 1, filepath.rfind('_')
        patient_id = filepath[start:end]

        if patient_id in patients:
            indices_to_be_included.append(i)
    
    source = torch.utils.data.Subset(source, indices_to_be_included)

    images = source.dataset.imgs
    image_paths = [images[i][0] for i in indices_to_be_included]

    print(f'loading {"training" if training else "validation"} data with a training split of {train_proportion}')
    print(f'dataset has classes {source.dataset.class_to_idx} and {len(source)} images')

    img_AD = [index for (index, item) in enumerate(image_paths) if item.find('AD' + os.path.sep) != -1]
    print(f'AD images count: {len(img_AD)}')
    img_NC = [index for (index, item) in enumerate(image_paths) if item.find(os.path.sep + 'NC') != -1]
    print(f'NC images count: {len(img_NC)}')

    if Siamese:
        # loading paired data for the Siamese neural net
        # each data point is of format [img1, img2, similarity]
        # where similarity is 1 if the two images are of the same class and 0 otherwise
        dataset = PairedDataset(source, False, random_seed=random_seed)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size,
                                            shuffle=True, num_workers=workers)
    else:
        # loading unitary training data for the MLP
        # each data point is of format [img, label]
        # where label is 1 if the image is of class AD and 0 otherwise
        loader = torch.utils.data.DataLoader(source, batch_size=2*batch_size,
                                            shuffle=True, num_workers=workers)
    
    return loader

def load_test_data(Siamese:bool, random_seed=None) -> torch.utils.data.DataLoader:

    if random_seed is not None:
        random.seed(random_seed)
        torch.random.manual_seed(random_seed)

    source = dset.ImageFolder(root=test_path, transform=test_transforms)
    print('Loading testing data')
    print(f'dataset has classes {source.class_to_idx} and {len(source)} images')

    if Siamese:
        # loading paired data for the Siamese neural net
        # each data point is of format [img1, img2, similarity]
        # where similarity is 1 if the two images are of the same class and 0 otherwise
        source = torch.utils.data.Subset(source, range(len(source))) # wrapper class for compatiability with PairedDataset
        dataset = PairedDataset(source, False, random_seed=random_seed)
        loader = torch.utils.data.DataLoader(dataset, batch_size=batch_size,
                                            shuffle=True, num_workers=workers)
    else:
        # loading unitary training data for the MLP
        # each data point is of format [img, label]
        # where label is 1 if the image is of class AD and 0 otherwise
        loader = torch.utils.data.DataLoader(source, batch_size=2*batch_size,
                                            shuffle=True, num_workers=workers)
    
    return loader

#
# basic tests
#
def test_visualise_data_MLP():
    # Plot some training images
    dataloader = load_data(training=False, Siamese=False, train_proportion=0.99)
    next_batch = next(iter(dataloader))
    print(next_batch[0][0].shape)

    # the following data visualisation code is modified based on code at
    # https://github.com/pytorch/tutorials/blob/main/beginner_source/basics/data_tutorial.py
    # published under the BSD 3-Clause "New" or "Revised" License
    # full text of the license can be found in this project at BSD_new.txt
    figure = plt.figure(figsize=(12, 9))
    cols, rows = 5, 3

    labels_map = {0: 'AD', 1: 'NC'}

    for i in range(1, cols * rows + 1):
        figure.add_subplot(rows, cols, i)
        plt.title(labels_map[next_batch[1][i].tolist()])
        plt.axis("off")
        plt.imshow(np.transpose(next_batch[0][i].squeeze(), (1,2,0)), cmap="gray")
    
    if machine == GLOBAL:
        print("saving figure for mlp")
        plt.savefig(f"{savepath}/data_for_mlp.png", dpi=300)
        print("figure saved for mlp")
    else: 
        plt.show()

def test_visualise_data_Siamese():
    # Plot some training images
    dataloader = load_data(training=True, Siamese=True)
    dataloader.dataset.debug_mode = True

    next_batch = next(iter(dataloader))
    print(next_batch[0][0].shape)
    print(next_batch[0][1].shape)

    cols, rows = 3, 3
    fig, axs = plt.subplots(rows, cols * 2, figsize=(16,12))
    labels_map = {0: 'diff', 1: 'same'}

    for i in range(rows):
        for j in range(cols):
            axs[i,j*2].imshow(np.transpose(next_batch[0][i*rows+j].squeeze(), (1,2,0)), cmap="gray")
            axs[i,j*2+1].imshow(np.transpose(next_batch[1][i*rows+j].squeeze(), (1,2,0)), cmap="gray")
            axs[i,j*2].set_title(f"""{labels_map[next_batch[2][i*rows+j].tolist()]}, {next_batch[3][i*rows+j]}""")
            axs[i,j*2+1].set_title(next_batch[4][i*rows+j])
            axs[i,j*2].axis("off")
            axs[i,j*2+1].axis("off")
    
    if machine == GLOBAL:
        print("saving figure for Siamese")
        plt.savefig(f"{savepath}/data_for_siamese.png", dpi=300)
        print("figure saved for Siamese")
    else: 
        plt.show()

def test_data_leakage():
    trainloader = load_data(training=True, Siamese=True, random_seed=89, train_proportion=0.8)
    testloader  = load_data(training=False, Siamese=True, random_seed=89, train_proportion=0.8)

    train_subset = trainloader.dataset.dataset
    test_subset = testloader.dataset.dataset

    training_images = train_subset.dataset.imgs
    testing_images = test_subset.dataset.imgs

    training_paths = [training_images[i][0] for i in train_subset.indices]
    testing_paths = [testing_images[i][0] for i in test_subset.indices]

    training_paths = set(training_paths)
    testing_paths = set(testing_paths)

    print(len(training_paths))
    print(len(testing_paths))

    overlap = training_paths.intersection(testing_paths)
    print(f'number of intersecting files: {len(overlap)}')
    # print(overlap)


if __name__ == "__main__":
    # Decide which device we want to run on
    device = torch.device("cuda:0" if torch.cuda.is_available() else "mps")
    print("Device: ", device)

    test_visualise_data_MLP()
    test_visualise_data_Siamese()
    test_data_leakage()
