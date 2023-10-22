""" Contains the source code for training, validating, testing and saving your model. The model
should be imported from “modules.py” and the data loader should be imported from “dataset.py”. Make
sure to plot the losses and metrics during training """
import os
import torch
import torch.nn as nn
import time
from modules import *
from dataset import *
from predict import *

# Device configuration
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
if not torch.cuda.is_available():
    print("Warning CUDA not Found. Using CPU")
else:
    print("Using CUDA.")

# model = SiameseNetwork()
model = ResNet18()
model = model.to(device)

print("Model No. of Parameters:", sum([param.nelement() for param in model.parameters()]))

# Decalre Loss Function
criterion = ContrastiveLoss()
criterion_triplet = TripletLoss()
learning_rate = 1e-4
# optimizer = optim.RMSprop(model.parameters(), lr=1e-4, alpha=0.99, eps=1e-8, weight_decay=0.0005, momentum=0.9)
optimizer = torch.optim.SGD(model.parameters(), lr=learning_rate, momentum=0.9, weight_decay=5e-4)
# scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=learning_rate, steps_per_epoch=len(train_loader), epochs=Config.siamese_number_epochs)
scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=learning_rate, steps_per_epoch=len(triplet_train_loader), epochs=Config.siamese_number_epochs)

# --------------
# Train the model
model.train()
print("> Training")
start = time.time() #time generation
def siameseTripletTraining(): #Maybe add validation loss, track both losses and then plot
    counter = []
    loss_history = []
    iteration_number = 0
    for epoch in range(0,Config.siamese_number_epochs):
        for i, data in enumerate(triplet_train_loader,0):
            #Produce two sets of images with the label as 0 if they're from the same file or 1 if they're different
            anchor_img, pos_img, neg_img = data
            anchor_img, pos_img, neg_img = anchor_img.to(device), pos_img.to(device), neg_img.to(device)

            # Forward pass
            anchor_output, pos_output, neg_output = model(anchor_img, pos_img, neg_img)
            loss_triplet = criterion_triplet(anchor_output, pos_output, neg_output)

            # Backward and optimize
            optimizer.zero_grad()
            loss_triplet.backward()
            optimizer.step()
            if i % 50 == 0:
                print("i:", i, "/", int(len(train_subset) / Config.train_batch_size))
                print("Epoch number {}\n Current loss {}\n".format(epoch,loss_triplet.item()))
            if i % 50 == 0:
                iteration_number += 50
                counter.append(iteration_number)
                loss_history.append(loss_triplet.item())
            scheduler.step()
    save_plot(counter, loss_history, 'siameseTripletTraining_whole', "Triplet Network loss over iterations.")

siameseTripletTraining()
end = time.time()
elapsed = end - start
print("Siamese Triplet Training took " + str(elapsed) + " secs or " + str(elapsed/60) + " mins in total")

model.eval()

# torch.save(model.state_dict(), "siamese_model.pt")
# print("Model Saved Successfully")
os.environ['KMP_DUPLICATE_LIB_OK']='TRUE'
print("\n> Loading from parameter file")
#/home/Student/s4533021/siamese_model.pt
# C:\\Users\\david\\OneDrive\\Documents\\0NIVERSITY\\2023\\SEM2\\COMP3710\\Project\\PatternAnalysis-2023\\recognition\\Siamese_45330212\\siamese_model.pt
# model.load_state_dict(torch.load("/home/Student/s4533021/siamese_model.pt", map_location=torch.device('cpu')))
# print("> Loaded from parameter file")
# --------------------------
# Train classification model
# print("> Getting classification train set")
# classification_trainset = CustomClassifcationDataset(train_subset=train_subset, model=model, device=device)
# classification_train_loader = torch.utils.data.DataLoader(classification_trainset, batch_size=Config.train_batch_size, shuffle=True)
# classification_valset = CustomClassifcationDataset(train_subset=val_subset, model=model, device=device)
# classification_val_loader = torch.utils.data.DataLoader(classification_valset, batch_size=Config.train_batch_size, shuffle=False)
# print("< Finished getting classification train set\n")

classification_model = BinaryClassifier()
classification_model = classification_model.to(device)

print("Model No. of Parameters:", sum([param.nelement() for param in classification_model.parameters()]))
# learning_rate = 0.001
# Decalre Loss Function
class_criterion = nn.CrossEntropyLoss()
# optimizer = optim.RMSprop(model.parameters(), lr=1e-4, alpha=0.99, eps=1e-8, weight_decay=0.0005, momentum=0.9)
class_optimizer = torch.optim.SGD(classification_model.parameters(), lr=learning_rate, momentum=0.9, weight_decay=5e-4)
# scheduler = torch.optim.lr_scheduler.OneCycleLR(optimizer, max_lr=learning_rate, steps_per_epoch=len(train_loader), epochs=Config.train_number_epochs)
class_scheduler = torch.optim.lr_scheduler.OneCycleLR(class_optimizer, max_lr=learning_rate, steps_per_epoch=len(train_loader), epochs=Config.train_number_epochs)

# print(sum(p.numel() for p in model.parameters() if p.requires_grad))
def classificationModelTraining():
    iteration_number = 0
    counter = []
    loss_history = []
    epochs = []
    val_accuracy = []
    for epoch in range(0,Config.train_number_epochs):
        for i, (image, labels) in enumerate(train_loader,0):
            #Produce two sets of images with the label as 0 if they're from the same file or 1 if they're different
            image = image.to(device)
            embeddings = model.forward_once(image)
            embeddings, labels = embeddings.to(device), labels.to(device)

            # Forward pass
            output = classification_model(embeddings)
            # print("Out1len", output1.size(), "Out2len", output1.size(), "labelssize", labels.size())
            CEloss = class_criterion(output, labels)

            # Backward and optimize
            class_optimizer.zero_grad()
            CEloss.backward()
            class_optimizer.step()
            if i % 50 == 0:
                print("ic:", i, "/", int(17216 / Config.train_batch_size))
                print("Epoch number {} / {}\n Current loss {}\n".format(epoch, Config.train_number_epochs,CEloss.item()))
            if i % 50 == 0:
                iteration_number += 50
                counter.append(iteration_number)
                loss_history.append(CEloss.item())
            class_scheduler.step()

        #test the network after finish each epoch, to have a brief training result.
        correct_val = 0
        total_val = 0
        with torch.no_grad():
            for image, label in val_loader:
                image = image.to(device)
                embeddings = model.forward_once(image)
                embeddings, label = embeddings.to(device), label.to(device)
                output = classification_model(embeddings)
                _, predicted = torch.max(output.data, 1)
                total_val += label.size(0)
                correct_val += (predicted == label).sum().item()

        epochs.append(epoch)
        val_accuracy.append((100 * correct_val / total_val))
        print('Accuracy of the classifier network: %d %%' % (100 * correct_val / total_val))
        save_plot(counter, loss_history, epoch, "Loss over iterations for Classifier Network")
    save_plot_acc(epochs, val_accuracy, "classificationModelTraining_Accuracy", "Validation accuracy over epochs for Classifier Network", "Epoch", "Accuracy")

classification_model.train()
start = time.time()
classificationModelTraining()
end = time.time()
elapsed = end - start
print("Classification Model Training took " + str(elapsed) + " secs or " + str(elapsed/60) + " mins in total")

# torch.save(classification_model.state_dict(), "classifaction_model.pt")
# print("Classification model Saved Successfully")
# --------------
# Test the model
print("> Testing")
start = time.time() #time generation
classification_model.eval()
with torch.no_grad():
    correct = 0
    total = 0
    for img, label in test_loader:
        img, label = img.to(device) , label.to(device)
        embeddings = model.forward_once(img)
        output = classification_model(embeddings)
        _, predicted = torch.max(output.data, 1)
        total += label.size(0)
        correct += (predicted == label).sum().item()
    if total != 0:
        print('Test Accuracy: {} %'.format(100 * correct / total))
    else:
        print('Total is 0', correct, total)
end = time.time()
elapsed = end - start
print("Testing took " + str(elapsed) + " secs or " + str(elapsed/60) + " mins in total")

print('END')