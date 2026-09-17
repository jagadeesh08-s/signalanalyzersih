"""
SIH26147 Signal Analyzer — PyTorch CNN Training Script

This script demonstrates how to train the VT-CNN2 architecture on a 
RadioML-style dataset of raw I/Q signals.

Usage:
1. Ensure PyTorch is installed: pip install torch torchvision
2. Prepare your dataset (I/Q arrays of shape [N, 2, 1024] and labels)
3. Run this script: python train_model.py
"""

import os
import logging
import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader, TensorDataset
    from app.modulation.cnn_model import IQ_CNN, TORCH_AVAILABLE
except ImportError:
    TORCH_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_dummy_dataset(num_samples=1000, seq_len=1024):
    """Generates random noise to simulate an I/Q dataset for demonstration."""
    logger.info("Generating synthetic I/Q dataset...")
    # Shape: (Batch, Channels, I/Q, SeqLen)
    X = np.random.randn(num_samples, 1, 2, seq_len).astype(np.float32)
    # 11 Classes
    y = np.random.randint(0, 11, size=(num_samples,)).astype(np.int64)
    return X, y

def train():
    if not TORCH_AVAILABLE:
        logger.error("PyTorch is not installed. Please install it to train the model.")
        return
        
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Using device: {device}")
    
    # 1. Load Data
    X_train, y_train = generate_dummy_dataset()
    
    dataset = TensorDataset(torch.tensor(X_train), torch.tensor(y_train))
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    # 2. Initialize Model
    model = IQ_CNN(num_classes=11, num_samples=1024).to(device)
    
    # 3. Loss and Optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # 4. Training Loop
    epochs = 5
    logger.info("Starting training loop...")
    for epoch in range(epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            
            # Zero gradients
            optimizer.zero_grad()
            
            # Forward pass
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            
            # Backward pass and optimize
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item()
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
            
        epoch_loss = running_loss / len(dataloader)
        epoch_acc = 100 * correct / total
        logger.info(f"Epoch [{epoch+1}/{epochs}] | Loss: {epoch_loss:.4f} | Accuracy: {epoch_acc:.2f}%")
        
    # 5. Save Model
    os.makedirs("models", exist_ok=True)
    torch.save(model.state_dict(), "models/iq_cnn_weights.pt")
    logger.info("Training complete! Model saved to models/iq_cnn_weights.pt")

if __name__ == "__main__":
    train()
