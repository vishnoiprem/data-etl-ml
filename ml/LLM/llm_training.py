
# Import required libraries
import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader
from transformers import GPT2Tokenizer, GPT2LMHeadModel, AdamW, get_linear_schedule_with_warmup
import torch.nn.functional as F
import os

# Load the tokenizer pretrained on the GPT-2 model
tokenizer = GPT2Tokenizer.from_pretrained('gpt2')

# Load the pretrained weights of the GPT-2 model
model = GPT2LMHeadModel.from_pretrained('gpt2')
def get_logits_for_next_token(model, sequence, temp_setting):
    # Generate model outputs for the given sequence
    model_outputs = model(sequence, labels=sequence)

    # Extract logits for the last token in the sequence, scale by temperature
    logits = model_outputs[1][:, -1, :] / max(temp_setting, 1.0)

    return logits

def training(dataset, model, tokenizer, batch_size=8, epochs=10, learning_rate=1e-3):

    # Initialization of training parameters and setting the device
    compute_device = torch.device("cpu")
    model.to(compute_device)
    model.train()

    # Preparing the data loader for batch processing
    batch_loader = DataLoader(dataset, batch_size=1, shuffle=True)
    current_loss, batch_accumulator = 0, 0
    processing_tensor = None

    # Setting up the optimizer and scheduler for training
    model_optimizer = AdamW(model.parameters(), lr=learning_rate)
    training_scheduler = get_linear_schedule_with_warmup(
        model_optimizer, num_warmup_steps=10, num_training_steps=-1
    )

    # Looping through each training epoch
    for current_epoch in range(epochs):
        print(f"Current training epoch: {current_epoch}")
        print(current_loss)

        # Initializing the index for a while loop
        index = 0
        batch_iterator = iter(batch_loader)

        # Processing each batch in the dataset using a while loop
        while index < len(batch_loader):
            data_batch = next(batch_iterator)

            # Handling tensor packing for batch processing
            if processing_tensor is None or processing_tensor.size()[1] + data_batch.size()[1] > 500: # Max sequence limit for batches
                processing_tensor, continue_batch = (data_batch, True) if processing_tensor is None else (processing_tensor, False)
            else:
                processing_tensor = torch.cat([data_batch, processing_tensor[:, 1:]], dim=1)
                continue_batch = True

            # Skipping to next iteration if current batch should not be processed now
            if continue_batch and index != len(batch_loader) - 1:
                index += 1
                continue

            # Training model on the current batch
            processing_tensor = processing_tensor.to(compute_device)
            model_output = model(processing_tensor, labels=processing_tensor)
            current_loss = model_output[0]
            current_loss.backward()

            # Optimizer and scheduler steps
            if (batch_accumulator % batch_size) == 0:
                model_optimizer.step()
                training_scheduler.step()
                model_optimizer.zero_grad()
                model.zero_grad()

            batch_accumulator += 1
            processing_tensor = None
            index += 1

    # Saving the model state after training is complete
    torch.save(
        model.state_dict(),
        os.path.join(".", "model-final.pt"),
    )

    return model

# Training the model on the specific data we have
model = training(train_subset, model, tokenizer)
def filter_low_probability_tokens(logits, probability_threshold, filter_threshold):
    # Sort logits to find the most probable tokens and their indices
    sorted_logits, sorted_indices = torch.sort(logits, descending=True)

    # Calculate the cumulative probabilities of the sorted logits
    cumul_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)

    # Identify indices where cumulative probability exceeds the threshold
    indices_to_filter = cumul_probs > probability_threshold

    # Adjust indices to filter, ensuring the first token is not filtered out
    indices_to_filter[..., 1:] = indices_to_filter[..., :-1].clone()
    indices_to_filter[..., 0] = 0

    # Set logits of tokens to be filtered to the filter threshold
    logits[:, sorted_indices[indices_to_filter]] = filter_threshold

    return logits

def generate_text_for_entry(model, tokenizer, prompt, probability_threshold, temp_setting):
    # Encode the prompt into a tensor and add a batch dimension
    generated_sequence = torch.tensor(tokenizer.encode(prompt)).unsqueeze(0)

    # Set a very low threshold for filtering tokens
    filter_threshold = -float("Inf")

    # Loop to generate up to 20 tokens
    for _ in range(20):
        # Obtain the logits for the next token in the sequence, scaled by temperature
        logits = get_logits_for_next_token(model, generated_sequence, temp_setting)

        # Filter out tokens with low probability to maintain text quality
        logits = filter_low_probability_tokens(logits, probability_threshold, filter_threshold)

        # Randomly select the next token based on the adjusted probabilities
        next_token = torch.multinomial(F.softmax(logits, dim=-1), num_samples=1)

        # Concatenate the next token to the generated sequence
        generated_sequence = torch.cat((generated_sequence, next_token), dim=1)

        # Check if the next token is the end-of-sequence token; if so, break the loop
        if next_token in tokenizer.encode(""):
            break

    # Convert the generated sequence tensor into a list of integers (token IDs)
    output_sequence = list(generated_sequence.squeeze().numpy())

    # Decode the token IDs back into text and return the generated text
    return tokenizer.decode(output_sequence)


generated_lyrics = []

# Loop directly through the test data DataFrame
for song in range(len(test_subset)):

    # Get the prompt from the 'Lyric' column
    lyric_prompt = test_subset['Lyric'][song]

    if not lyric_prompt.strip():
        continue

    # Set the model to evaluation mode and disable gradient calculations
    model.eval()
    with torch.no_grad():
        generated_lyric = generate_text_for_entry(model.to('cpu'), tokenizer, lyric_prompt, 0.80, 1.0)

    print(generated_lyric)

    # Append the generated lyric to the list
    generated_lyrics.append(generated_lyric)