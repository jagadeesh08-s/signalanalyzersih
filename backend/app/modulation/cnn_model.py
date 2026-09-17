import logging

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not installed. CNN classifier will run in mock mode.")
    # Mock classes so the file doesn't crash on import
    class nn:
        Module = object
    class F:
        pass


class IQ_CNN(nn.Module):
    """
    Convolutional Neural Network for Automatic Modulation Classification (AMC).
    Inspired by VT-CNN2 architecture designed for raw I/Q signal data.
    
    Input shape: (Batch, 1, 2, N_samples) where 2 represents I and Q channels.
    """
    def __init__(self, num_classes=11, num_samples=1024):
        super(IQ_CNN, self).__init__()
        if not TORCH_AVAILABLE:
            return
            
        self.num_classes = num_classes
        self.num_samples = num_samples
        
        # 1st Convolutional Layer
        # Filters: 256, Kernel: (1, 3), padding 'same' over time dimension
        self.conv1 = torch.nn.Conv2d(in_channels=1, out_channels=256, kernel_size=(1, 3), padding=(0, 1))
        self.dropout1 = torch.nn.Dropout(0.5)
        
        # 2nd Convolutional Layer
        # Filters: 80, Kernel: (2, 3), valid padding (reduces the channel dimension from 2 to 1)
        self.conv2 = torch.nn.Conv2d(in_channels=256, out_channels=80, kernel_size=(2, 3))
        self.dropout2 = torch.nn.Dropout(0.5)
        
        # Calculate flattened size
        # After conv2, H goes from 2 -> 1, W goes from 1024 -> 1022
        flattened_size = 80 * 1 * (num_samples - 2)
        
        # Fully Connected Layers
        self.fc1 = torch.nn.Linear(flattened_size, 256)
        self.dropout3 = torch.nn.Dropout(0.5)
        
        self.fc2 = torch.nn.Linear(256, num_classes)
        
    def forward(self, x):
        if not TORCH_AVAILABLE:
            return None
            
        # x expected shape: (Batch, 1, 2, L)
        
        # Conv block 1
        x = F.relu(self.conv1(x))
        x = self.dropout1(x)
        
        # Conv block 2
        x = F.relu(self.conv2(x))
        x = self.dropout2(x)
        
        # Flatten
        x = x.view(x.size(0), -1)
        
        # Dense block 1
        x = F.relu(self.fc1(x))
        x = self.dropout3(x)
        
        # Dense block 2 (Output)
        x = self.fc2(x)
        
        return x


def get_mock_prediction(iq_data):
    """
    Provides a mock prediction when PyTorch weights aren't loaded, 
    but still returns data formatted like the real model.
    """
    classes = ['8PSK', 'AM-DSB', 'AM-SSB', 'BPSK', 'CPFSK', 'GFSK', 'PAM4', 'QAM16', 'QAM64', 'QPSK', 'WBFM']
    import numpy as np
    
    # Simple heuristic to make the mock somewhat dynamic based on input power
    power = np.mean(np.abs(iq_data)**2)
    idx = int(power * 1000) % len(classes)
    
    probs = np.random.dirichlet(np.ones(len(classes)))
    probs[idx] += 1.5  # Boost one class
    probs = probs / np.sum(probs)
    
    predicted = classes[np.argmax(probs)]
    confidence = np.max(probs)
    prob_dict = {classes[i]: float(probs[i]) for i in range(len(classes))}
    
    return predicted, float(confidence), prob_dict
