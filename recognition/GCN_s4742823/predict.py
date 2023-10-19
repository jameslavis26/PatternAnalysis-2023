import torch
from dataset import load_data
from utils import device
from dataset import load_data
from train import test_model, TEST_SIZE, VAL_SIZE

if __name__ == "__main__":
    data = load_data(test_size=TEST_SIZE, val_size=VAL_SIZE)
    data = data.to(device)

    model = torch.load("Facebook_GCN.pth")
    model = model.to(device)

    test_model(model, data)