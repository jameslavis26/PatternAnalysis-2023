#Contains the data loader for loading and preprocessing your data
from torchvision import datasets
import torchvision.transforms as transforms
import random
from PIL import Image
from modules import *

# Define the custom dataset for the Triplet Siamese Network
class CustomTripletSiameseNetworkDataset(Dataset):
    def __init__(self, root_dir, transform=None):
        self.root_dir = root_dir # Root directory for the dataset
        self.transform = transform# Transformations to apply on images

        # Initialize empty lists to store image paths and labels
        self.image_paths = []
        self.labels = []

        # Loop through each folder in the root directory
        folders = os.listdir(root_dir)
        print("> Creating image paths")
        for i, folder1 in enumerate(folders):
            folder2 = folders[i ^ 1]
            c = 0
            print("Folder:", folder1, folder2)

            folder1_path = os.path.join(root_dir, folder1)
            folder2_path = os.path.join(root_dir, folder2)

            folder1_images = os.listdir(folder1_path)
            folder2_images = os.listdir(folder2_path)

            # Create anchor-positive-negative triples from images
            for anchor in folder1_images:
                c += 1
                if c % 1000 == 0:
                    print("Count:", c)

                # Choose positive and negative examples
                pos = random.choice(folder1_images)
                while anchor == pos:
                    print("FOUND SAME IMAGE - SHOULDN'T HAPPEN OFTEN")
                    pos = random.choice(folder1_images)
                neg = random.choice(folder2_images)

                # Store the paths of anchor, positive and negative images
                anchor_path = os.path.join(folder1_path, anchor)
                pos_path = os.path.join(folder1_path, pos)
                neg_path = os.path.join(folder2_path, neg)

                self.image_paths.append((anchor_path, pos_path, neg_path, i))

        print("< Finished creating image paths. #Images:", len(self.image_paths))

    def __len__(self):
        return len(self.image_paths) # Return the total number of images

    def __getitem__(self, index):
        # Return a single item (anchor, positive, negative, label) at the given index
        anchor_path, pos_path, neg_path, label = self.image_paths[index]
        anchor = Image.open(anchor_path).convert("RGB")
        pos = Image.open(pos_path).convert("RGB")
        neg = Image.open(neg_path).convert("RGB")

        if self.transform is not None:
            anchor = self.transform(anchor)
            pos = self.transform(pos)
            neg = self.transform(neg)

        return anchor, pos, neg, label
    
class CustomClassifcationDataset(Dataset):
    def __init__(self, train_subset, model, device):
        self.train_subset = train_subset
        # Create a list of image paths
        # self.image_embeddings = []
        print("> Creating image embedding")
        # c = 0
        # for anchor, _, _, label in train_subset:
        #     # print("Before shapes:", anchor.shape, pos.shape, neg.shape)
        #     anchor = anchor.unsqueeze(0)
        #     # pos = torch.zeros_like(anchor)
        #     # neg = neg.unsqueeze(0)
        #     # neg = torch.zeros_like(anchor)
        #     # print("After shapes:", anchor.shape, pos.shape, neg.shape, "\n")
        #     c += 1
        #     if c % 1000 == 0:
        #         print("Count:", c)
        #     # output_anchor = model.forward_once(anchor.to(device))
        #     self.image_embeddings.append((anchor, label))

        # print("< Finished creating image embeddings. #Images:", len(self.image_paths))

    def __len__(self):
        # return len(self.image_embeddings)
        return len(self.train_subset)

    def __getitem__(self, index):
        # return self.image_embeddings[index]
        anchor, _, _, label = self.train_subset[index]
        # anchor = anchor.unsqueeze(0)  # Do this operation here instead of in __init__
        return anchor, label

# Initialize transform for training images
transform_train = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.11550809, 0.11550809, 0.11550809), (0.22545652, 0.22545652, 0.22545652)),
])

print("> Getting triplet train set")
triplet_trainset = CustomTripletSiameseNetworkDataset(root_dir=Config.training_dir, transform=transform_train)

# Calculate the lengths of the splits for training and validation sets
total_len = len(triplet_trainset)
train_len = int(0.8 * total_len)
val_len = total_len - train_len

# Split the dataset into training and validation sets
triplet_train_subset, triplet_val_subset = utils.random_split(triplet_trainset, [train_len, val_len])

# Create DataLoaders for the training and validation subsets
triplet_train_loader = torch.utils.data.DataLoader(triplet_train_subset, batch_size=Config.siamese_train_batch_size, shuffle=True)
triplet_val_loader = torch.utils.data.DataLoader(triplet_val_subset, batch_size=Config.siamese_train_batch_size, shuffle=False)
print("< Finished getting triplet train set")

# print("> Getting train and validation set")
# trainset = datasets.ImageFolder(root=Config.training_dir, transform=transform_train)
# train_loader = torch.utils.data.DataLoader(trainset, batch_size=Config.train_batch_size, shuffle=True)
# # Calculate the lengths of the splits
# total_len = len(trainset)
# train_len = int(0.8 * total_len)
# val_len = total_len - train_len

# # Split the dataset
# train_subset, val_subset = utils.random_split(trainset, [train_len, val_len])

# trainset = CustomClassifcationDataset(triplet_train_subset, model, device)

# # Create DataLoaders for the subsets
# train_loader = torch.utils.data.DataLoader(train_subset, batch_size=Config.train_batch_size, shuffle=True)
# val_loader = torch.utils.data.DataLoader(val_subset, batch_size=Config.train_batch_size, shuffle=False)
# print("< Finished getting train set and validation set. With testing size:", len(train_subset), "and validation size:", len(val_subset))

# Create DataLoader for the test set
print("> Getting test set")
# testset = CustomSiameseNetworkDataset(root_dir=Config.testing_dir, transform=transform_train)
testset = datasets.ImageFolder(Config.testing_dir, transform=transform_train)
test_loader = torch.utils.data.DataLoader(testset, batch_size=Config.train_batch_size, shuffle=True)
print("< Finished getting test set")