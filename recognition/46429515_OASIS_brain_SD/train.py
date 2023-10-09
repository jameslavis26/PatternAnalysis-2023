import os
import dataset
import module
import utils
import torch
import torchvision
import torchvision.transforms as transforms
import numpy as np
from torch import nn
from torch.optim import Adam


# Create a model instance from module.py
model = module.UNet()
model = model.to(utils.device)

# Adam Optimizer for training the model
optimizer = Adam(model.parameters(), lr=0.001)

best_loss = float('inf')  # Initialize with a high value
best_model_state_dict = None  # Variable to store the state_dict of the best model
validate_every_n_epochs = 5 # Variable to validate state of model every 5 epochs

for epoch in range(utils.epochs):
    
    # Training Loop
    model.train()
    for step, batch in enumerate(dataset.data_loader):
        optimizer.zero_grad()
        
        t = torch.randint(0, module.T, (utils.BATCH_SIZE,), device=utils.device).long()
        loss = utils.get_loss(model, batch[0], t)
        loss.backward()
        optimizer.step() 
        
        if epoch % 10 == 0 and step == 0:
            print(f"Epoch {epoch} | step {step:03d} Loss: {loss.item()}")
            utils.sample_save_image(model, epoch, utils.output_dir)
            
    # Validation loop (Written by ChatGPT3.5)
    if epoch % validate_every_n_epochs == 0:
        model.eval()  # Set the model to evaluation mode
        total_validation_loss = 0.0
        total_validation_samples = 0
        
        with torch.no_grad():
            for step, batch in enumerate(dataset.validate_loader):
                t = torch.randint(0, module.T, (utils.BATCH_SIZE,), device=utils.device).long()
                validation_loss = utils.get_loss(model, batch[0], t)
                total_validation_loss += validation_loss.item() * utils.BATCH_SIZE
                total_validation_samples += utils.BATCH_SIZE

        # Calculate average validation loss
        average_validation_loss = total_validation_loss / total_validation_samples

        # Check if the current model has a lower validation loss than the best so far
        if average_validation_loss < best_loss:
            best_loss = average_validation_loss  # Update the best loss
            best_model_state_dict = model.state_dict()  # Save the state_dict of the best model

            torch.save(best_model_state_dict, 'best_model.pth')
        
        # Print validation results
        print(f"Epoch {epoch} | Validation Loss: {average_validation_loss}")
