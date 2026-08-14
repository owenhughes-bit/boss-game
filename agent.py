import torch
import torch.nn as nn #the neural network
import random
from collections import deque
import torch.optim as optim

from environment import STATE_SIZE, ACTION_SIZE #input and output size

LEARNING_RATE = 0.001
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY = 0.9995
GAMMA = 0.99
BATCH_SIZE = 64
TARGET_UPDATE = 1000


class DQN(nn.Module): #every pytorch network is a class that inherits from nn.Module (the base class)
    def __init__(self, state_size, action_size):
        super().__init__() #calls nn.Module's setup. Without it the weight-tracking machinery isn't initialized.
        self.net = nn.Sequential( #container that chains layers in order
            nn.Linear(state_size, 64),
            nn.ReLU(), #silences negative numbers
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, action_size),
        )

    def forward(self, x): #given the input x, run it through self.net and return the result
        return self.net(x)


class ReplayBuffer: #grabs a random handful from across all stored history to keep sample diverse and training stable.
    def __init__(self, capacity=10000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)

class Agent:
    def __init__(self, state_size, action_size):
        self.action_size = action_size

        #the two networks
        self.policy_net = DQN(state_size, action_size) #gets trained
        self.target_net = DQN(state_size, action_size) #provides stable targets to predict next_state's Q value
        self.target_net.load_state_dict(self.policy_net.state_dict()) #copies the policy_net's weights into the target net so they stay identical
        self.target_net.eval() #puts target_net into evaluation mode

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=LEARNING_RATE) #adjusts the weights using gradients autograd computes
        self.buffer = ReplayBuffer()

        #epsilon (exploration) schedule
        self.epsilon = EPSILON_START

    def choose_action(self, state):
        #explore: random action with probability epsilon
        if random.random() < self.epsilon:
            return random.randint(0, self.action_size - 1) #Does random moves early in trains to discover untried actions, decays over time.
        #exploit: best action according to the plicy network
        with torch.no_grad(): #prevents tracking during the deciding step that doesn't need to be tracked
            state_tensor = torch.tensor(state, dtype=torch.float32)
            q_values = self.policy_net(state_tensor)
            return torch.argmax(q_values).item()