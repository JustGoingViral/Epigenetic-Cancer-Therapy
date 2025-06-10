#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import os
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import matplotlib.pyplot as plt
import os
import re
import gzip
import io
import random
from scipy.stats import ranksums
from multiprocessing import Pool, cpu_count


# In[2]:


# Set the number of control arrays and cancer arrays
num_control_arrays = 400
num_cancer_arrays = 400

# Define the number of bins for data analysis
num_bins = 2000000

# Open the binary file 'test_sort.npy' for reading
with open('test_sort.npy', 'rb') as f:
    # Load the data for cancer arrays from the binary file
    cancer_arr = np.load(f)
    
    # Load the data for control arrays from the binary file
    control_arr = np.load(f)
    
# Print the shapes of the loaded arrays for control and cancer data
print("Shape of control array:", control_arr.shape)
print("Shape of cancer array:", cancer_arr.shape)


# In[3]:


# Open the file 'cancer_names.txt' for reading and load cancer names
with open('cancer_names.txt', 'r') as f:
    # Create a list of cancer names by stripping each line
    cancer_names = [line.strip() for line in f]

# Open the file 'control_names.txt' for reading and load control names
with open('control_names.txt', 'r') as f:
    # Create a list of control names by stripping each line
    control_names = [line.strip() for line in f]

# Print the lists of cancer and control names
print("Cancer names:", cancer_names)
print("Control names:", control_names)


# In[4]:


# Select a subset of control and cancer arrays for training and testing
training_con = control_arr[30:400]
training_can = cancer_arr[30:400]
testing_con = control_arr[:30]
testing_can = cancer_arr[:30]

# Select a subset of control and cancer names for testing
test_con_names = control_names[:30]
test_can_names = cancer_names[:30]

# Function to perform Wilcoxon rank-sum test for a single bin
def ranksums_parallel(bin_index):
    return ranksums(training_con[:, bin_index], training_can[:, bin_index]).pvalue

# Number of processes for parallel processing (adjust based on your CPU cores)
num_processes = cpu_count()

# Perform Wilcoxon rank-sum test for each bin using parallel processing
with Pool(num_processes) as pool:
    p_values = pool.map(ranksums_parallel, range(num_bins))

# Convert p_values to a NumPy array for efficient vectorized operations
p_values = np.array(p_values)

# Adjust p-values for multiple comparisons (Bonferroni correction)
adjusted_alpha = 0.05  # 0.05 significance level divided by the number of bins
is_significant = p_values < adjusted_alpha

# Get the indices of significant bins
significant_bins_indices = np.where(is_significant)[0]

# Sort the p_values array in ascending order
sorted_p_values = np.sort(p_values)

# Find the indices of p_values that are below the adjusted_alpha (0.05)
significant_indices = np.where(sorted_p_values < adjusted_alpha)[0]

# Get the actual p-values for the significant bins
significant_p_values = sorted_p_values[significant_indices]

# Get the indices of the top x smallest significant p-values
top_x_indices = significant_indices[np.argsort(significant_p_values)[:10000]]

# Get the corresponding bin indices for the top 100 significant p-values
top_x_bin_indices = np.argsort(p_values)[top_x_indices]

# Print the indices and p-values of the top 10 significant bins
print("Top 10 significant bin indices:", top_x_bin_indices[0:10])
print("Corresponding p-values:", significant_p_values[np.argsort(significant_p_values)[:10000]])

# Print the first 100 p-values
print("First 100 p-values:", p_values[0:100])


# In[5]:


print(list(top_x_bin_indices[0:100]))


# In[6]:


# Plot a histogram of p-values
plt.hist(p_values, bins=20, color='#BDE0BD')
plt.xlabel('p-value')
plt.ylabel('Frequency')
plt.title('Histogram of p-values')
plt.show()


# In[7]:


# Select a subset of top significant bin indices for graphs
test_can = training_can[:, top_x_bin_indices[:3]]
test_con = training_con[:, top_x_bin_indices[:3]]

# Select full training data for top significant bin indices
train_full_ca = training_can[:, top_x_bin_indices]
train_full_co = training_con[:, top_x_bin_indices]

# Select full testing data for top significant bin indices
test_full_ca = testing_can[:, top_x_bin_indices]
test_full_co = testing_con[:, top_x_bin_indices]


# In[8]:


# This code generates boxplots to visualize the distribution of log-transformed data
# for important bins in both the 'Cancer' and 'Control' groups.

# Define the number of columns for the subplots (one for each column)
num_cols = 3

# Create a figure and subplots
fig, axes = plt.subplots(1, num_cols, figsize=(15, 5))

# Sample data (replace this with your actual data)
col1_can = np.log(test_can[:, [0]])
col2_can = np.log(test_can[:, [1]])
col3_can = np.log(test_can[:, [2]])
col1_con = np.log(test_con[:, [0]])
col2_con = np.log(test_con[:, [1]])
col3_con = np.log(test_con[:, [2]])

# Create boxplots for each column (combine "can" and "con" data)
positions = [0, 1]
labels = ['Cancer', 'Control']
colors = ['#BDE0BD', '#B285BC']

for i in range(num_cols):
    bp = axes[i].boxplot([eval(f'col{i+1}_can').flatten(), eval(f'col{i+1}_con').flatten()],
                         positions=positions, vert=True, patch_artist=True, labels=labels)

    # Set box colors
    for box, color in zip(bp['boxes'], colors):
        box.set(facecolor=color)

    # Set flier color (outliers)
    for flier in bp['fliers']:
        flier.set(marker='o', color='black', alpha=0.5)

    axes[i].set_title(f'Important Bin {i+1}')
    axes[i].set_xticks(positions)
    axes[i].set_ylabel('Values (Log)')

# Adjust spacing between subplots
plt.tight_layout()

# Show the plot
plt.show()


# In[9]:


from sklearn.decomposition import PCA
all_data = np.vstack((train_full_ca, train_full_co))

# Perform PCA with desired number of components
n_components = 2
pca = PCA(n_components=n_components)
pca_result = pca.fit_transform(all_data)

# Separate the results back into "can" and "con" datasets
can_pca = pca_result[:len(train_full_co)]
con_pca = pca_result[len(train_full_co):]

# Plot the PCA results
plt.scatter(can_pca[:, 0], can_pca[:, 1], color='#BDE0BD', label='Cancer')
plt.scatter(con_pca[:, 0], con_pca[:, 1], color='#B285BC', label='Control')
plt.xlabel('Principal Component 1')
plt.ylabel('Principal Component 2')
plt.legend()
plt.title('PCA Plot')
plt.show()

# Print the explained variance ratio for each component
print('Explained Variance Ratio:', pca.explained_variance_ratio_)


# In[23]:


from tensorflow.keras import regularizers
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Import necessary libraries and modules
from tensorflow.keras.layers import BatchNormalization, Dense, Flatten, Dropout, ZeroPadding2D
from collections import defaultdict
import visualkeras
from tensorflow.keras.metrics import AUC

#Building our neural net

# Create binary labels (0 for control, 1 for cancer)
control_labels_train = np.zeros(train_full_co.shape[0])
cancer_labels_train = np.ones(train_full_ca.shape[0])
control_labels_test = np.zeros(test_full_co.shape[0])
cancer_labels_test = np.ones(test_full_ca.shape[0])

# Combine the datasets and labels
X_train = np.concatenate((train_full_co, train_full_ca), axis=0)
y_train = np.concatenate((control_labels_train, cancer_labels_train))
X_test = np.concatenate((test_full_co, test_full_ca), axis=0)
y_test = np.concatenate((control_labels_test, cancer_labels_test))

train_indices = np.random.permutation(len(X_train))
X_train_shuffled = X_train[train_indices]
y_train_shuffled = y_train[train_indices]

# Standardize the data (optional but can help with training)
scaler = StandardScaler()
X_train_shuffled = scaler.fit_transform(X_train_shuffled)
X_test = scaler.transform(X_test)

# Build the neural network model
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation='relu', kernel_regularizer=regularizers.l2(0.01), input_shape=(X_train.shape[1],)),
    tf.keras.layers.Dropout(0.5),
    BatchNormalization(),
    tf.keras.layers.Dense(32, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(16, activation='relu', kernel_regularizer=regularizers.l2(0.01)),
    tf.keras.layers.Dropout(0.5),
    tf.keras.layers.Dense(1, activation='sigmoid')
])
model.summary()

# Set custom colors for visualization
color_map = defaultdict(dict)
color_map[tf.keras.layers.Dense]['fill'] = '#BDE0BD'
color_map[tf.keras.layers.Dropout]['fill'] = '#B285BC'

# Visualize the model architecture
visualkeras.layered_view(model, color_map=color_map, legend=True, to_file='output.png').show()

# Implement learning rate schedule
optimizer = tf.keras.optimizers.RMSprop(learning_rate=0.00005)

# Compile the model
model.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['accuracy', AUC()])

# Train the model
history = model.fit(X_train_shuffled, y_train_shuffled, epochs=250, batch_size=16, validation_split=0.1)

# Evaluate the model
loss, accuracy, auc = model.evaluate(X_test, y_test)
print(f'Test Loss: {loss:.4f}, Test Accuracy: {accuracy:.4f}, Test AUC: {auc:.4f}')


# In[21]:


# Retrieve training history metrics
training_accuracy = history.history['accuracy']
validation_accuracy = history.history['val_accuracy']
training_loss = history.history['loss']
validation_loss = history.history['val_loss']

# Create a list of epochs for x-axis
epochs = range(1, len(training_accuracy) + 1)

# Plot training and validation accuracy
plt.figure(figsize=(10, 5))
plt.subplot(1, 2, 1)
plt.plot(epochs, training_accuracy, label='Training Accuracy')
plt.plot(epochs, validation_accuracy, label='Validation Accuracy', color='#BDE0BD')
plt.title('Training and Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.legend()

# Plot training and validation loss
plt.subplot(1, 2, 2)
plt.plot(epochs, training_loss, label='Training Loss')
plt.plot(epochs, validation_loss, label='Validation Loss', color='#BDE0BD')
plt.title('Training and Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()

# Adjust layout and display the plots
plt.tight_layout()
plt.show()


# In[12]:


from sklearn.metrics import roc_auc_score

# Assuming you have already trained your model and obtained predictions on the testing set
y_pred = model.predict(X_test)

# Calculate AUC
auc_score = roc_auc_score(y_test, y_pred)  # Replace y_true with the true labels of the testing set

print(f"AUC on testing set: {auc_score}")


# In[25]:


# Predict on the test data
y_pred = model.predict(X_test)

# Extract SRR numbers from test_can_names using regular expressions
srr_numbers = [re.search(r'SRR(\d+)', item).group() for item in test_can_names if re.search(r'SRR\d+', item)]

# Extract predicted cancer results for visualization
cancer_results = y_pred.flatten()[30:]

# Print the extracted cancer results
print("Extracted cancer results:", cancer_results)

# Print the entire y_pred array
print("Predicted probabilities:", y_pred.flatten())

# Print the true labels from y_test
print("True labels:", y_test)


# In[26]:


y = 0

wrong_canc, wrong_cont = 0, 0

# Iterate through predicted values and true labels to identify misclassifications
for pred in y_pred:
    if pred[0] >= 0.5 and y_test[y] != 1:
        wrong_cont += 1
        print(f'This is the actual: {y_test[y]} and the prediction: {pred[0]} and index {y}')
    elif pred[0] < 0.5 and y_test[y] != 0:
        wrong_canc += 1
        print(f'This is the actual: {y_test[y]} and the prediction: {pred[0]} and index {y}')
    y += 1

# Print the number of wrongly classified cancer and control samples, as well as the total number of samples
print(f"Number of wrongly classified cancer samples: {wrong_canc}")
print(f"Number of wrongly classified control samples: {wrong_cont}")
print(f"Total number of samples: {len(y_test)}")
        


# In[27]:


# Read data from a CSV file into a DataFrame
df = pd.read_csv(r'df_cancer.txt')

# Display the first few rows of the DataFrame
print(df.head())

# List of SRR numbers

# Filter rows where SRR numbers match
filtered_df = df[df['Run'].isin(srr_numbers)]
print("Shape of filtered DataFrame:", filtered_df.shape)

# Specify the column from which you want to extract values
column_to_extract = 'disease_stage'

# Extract values at the specified column for the filtered rows
extracted_values = filtered_df[column_to_extract].tolist()

# Find missing SRR numbers
missing_srr_numbers = [srr for srr in srr_numbers if srr not in df['Run'].values]

# Print missing SRR numbers
for missing_srr in missing_srr_numbers:
    print("Missing SRR:", missing_srr)

# Print extracted disease stage values
print("Extracted Disease Stage Values:", extracted_values)

# Print missing SRR numbers and extracted values
print("Missing SRR Numbers:", missing_srr_numbers)





# Sample data
numbers = list(cancer_results * 100)
characters = extracted_values

# Create a dictionary to store values for each unique character
data_dict = {}
for char, num in zip(characters, numbers):
    if char not in data_dict:
        data_dict[char] = []
    data_dict[char].append(num)

# Create a list of lists for box plot
data_lists = [data_dict[char] for char in sorted(data_dict.keys())]

# Create a box plot
plt.boxplot(data_lists, labels=sorted(data_dict.keys()))
plt.xlabel('Cancer Stage')
plt.ylabel('Accuracy (%)')
plt.title('Testing Accuracy by Cancer Stage')
plt.show()


