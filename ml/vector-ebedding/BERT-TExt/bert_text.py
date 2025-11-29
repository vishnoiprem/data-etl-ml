# Import everything we need
import torch
from transformers import BertTokenizer, BertModel
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity