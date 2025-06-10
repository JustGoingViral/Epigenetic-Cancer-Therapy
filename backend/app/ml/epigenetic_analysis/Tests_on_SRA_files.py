#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re
import gzip
import io
import argparse
import time


# In[2]:


# Path to the control data file
f = '/home/sam/sra_files/control_SRR17006224.bed.gz'

# Open and read the compressed file content
with gzip.open(f, 'rb') as file:
    file_content = file.read().decode('utf-8')  # Decode the bytes to string
    
    # Process the file content and convert it into a DataFrame
    # Assuming the file content is in a specific format, modify the code accordingly
    # For example, if the content is a CSV file, you can use pd.read_csv()
    # If it's in JSON format, you can use pd.read_json(), etc.
df = pd.read_csv(io.BytesIO(file_content.encode()), delimiter='\t')  # Use BytesIO to read from bytes

# Define the header for the DataFrame
header = ['chrom', 'read_start', 'read_end', 'name', 'score', 'strand']

# Set DataFrame columns using the defined header
df.columns = header[:len(df.columns)]

# Sort the DataFrame by 'name' column
df = df.sort_values('name')

# Print the first few rows of the DataFrame
print(df.head())


# In[3]:


# Modify 'name' column by removing trailing '1' or '2' and appending '1'
df['name'] = df['name'].str.rstrip('12') + '1'

# Calculate 'frag_length' for each group of rows with the same 'name'
frag_length = df.groupby('name')['read_end'].transform('max') - df.groupby('name')['read_start'].transform('min')
df['frag_length'] = frag_length

# Print the first few rows of the modified DataFrame
print(df.head())


# In[4]:


# Group the DataFrame by 'name' and aggregate values for each group
df_unique = df.groupby('name', as_index=False).agg({
    'chrom': 'first',
    'read_start': 'min',
    'read_end': 'max',
    'name': 'first',
    'score': 'first',
    'strand': 'first',
    'frag_length': 'first'
})

# Sort the unique DataFrame by 'read_start'
df_unique = df_unique.sort_values('read_start')

# Remove extra information from 'chrom' values
df_unique["chrom"] = df_unique["chrom"].str.split("_").str.get(0)

# Create a mask for filtering out "chrUn" chromosomes
mask = df_unique["chrom"].str.startswith("chrUn")

# Exclude rows with "chrUn" chromosomes
df_unique = df_unique[~mask]

# Print the first few rows of the modified unique DataFrame
print(df_unique.head())


# In[5]:


# Filter the unique DataFrame to include only rows with 'frag_length' less than or equal to 1000
df_unique = df_unique[df_unique.frag_length <= 1000]

# Print the maximum value of 'frag_length'
print("Maximum frag_length:", df_unique['frag_length'].max())

# Sort the unique DataFrame by 'chrom'
df_unique = df_unique.sort_values('chrom')

# Print the first few rows of the modified DataFrame
print(df_unique.head())


# In[6]:


# Create a dictionary with chromosome positions
chrom_pos = {
    'chr1': 0,
    'chr2': 248956422,
    'chr3': 491149951,
    'chr4': 689445510,
    'chr5': 879660065,
    'chr6': 1061198324,
    'chr7': 1232004303,
    'chr8': 1391350276,
    'chr9': 1536488912,
    'chr10': 1674883629,
    'chr11': 1808681051,
    'chr12': 1943767673,
    'chr13': 2077042982,
    'chr14': 2191407310,
    'chr15': 2298451028,
    'chr16': 2400442217,
    'chr17': 2490780562,
    'chr18': 2574038003,
    'chr19': 2654411288,
    'chr20': 2713028904,
    'chr21': 2777473071,
    'chr22': 2824183054,
    'chrX': 2875001522,
    'chrY': 3031042417
}

# Print the dictionary of chromosome positions
print(chrom_pos)

# Adjust read start and end positions based on chromosome positions
for key, value in chrom_pos.items():
    mask = df_unique['chrom'] == key
    df_unique.loc[mask, 'read_start'] += value
    df_unique.loc[mask, 'read_end'] += value

# Print the first few rows of the modified DataFrame with adjusted positions
print(df_unique.head())


# In[7]:


# Print rows in df_unique where 'chrom' column is 'chr3'
print(df_unique[df_unique['chrom'] == 'chr3'])

# Import necessary library for plotting
import matplotlib.pyplot as plt

# Create a histogram of 'frag_length' with specified settings
df_unique['frag_length'].hist(bins=65, color='#BDE0BD', edgecolor='black', grid=False)

# Set labels and title for the plot
plt.xlabel('Fragment Length')
plt.ylabel('Frequency')
plt.title('Histogram of Fragment Length Per Patient')

# Show the plot
plt.show()


# In[8]:


# Get unique values from the 'chrom' column
chromed = df_unique['chrom'].unique()

# Define maximum indices for adjusting read positions
max_index = 3088269832
max_index_adj = 3088358329

# Create an array of zeros to represent reads
zero_reads = np.zeros(max_index_adj, dtype='uint8')

# Convert read start and end positions to numpy arrays
read_tonump1 = df_unique['read_start'].tolist()
read_tonump2 = df_unique['read_end'].tolist()

# Set appropriate positions to 1 in the zero_reads array
zero_reads[read_tonump1] = 1
zero_reads[read_tonump2] = 1

# Assign df_unique to df and sort it by 'read_start'
df = df_unique
df = df.sort_values('read_start')

# Print the first few rows of the sorted DataFrame
print(df.head())


# In[9]:


# Instead of assigning to a new variable, modify the original dataframe
df = df_unique

# Specify the number of bins
num_bins = 20000

# Calculate the bin edges
bin_edges = np.linspace(0, 3088269832, num_bins + 1)

# Calculate the histogram
hist, bins = np.histogram(
    np.concatenate([df['read_start'].values, df['read_end'].values]),
    bins=bin_edges
)

# Calculate the bin indices for the 'read_start' column
bin_indices = np.searchsorted(bin_edges, df['read_start'], side='right') - 1

# Calculate the counts of fragment lengths in different ranges for each bin
condition1 = (df['frag_length'] <= 220) & (df['frag_length'] >= 100)
condition2 = (df['frag_length'] <= 400) & (df['frag_length'] >= 300)
condition3 = (df['frag_length'] <= 590) & (df['frag_length'] >= 470)

# Combine the conditions using logical OR (|)
combined_condition = condition1 | condition2 | condition3

# Calculate small_counts using the combined condition
small_counts = np.bincount(bin_indices, weights=combined_condition, minlength=num_bins)
medium_counts = np.bincount(bin_indices, weights=(df['frag_length'] <= 160), minlength=num_bins)

# Calculate large_counts using the condition for large fragments
large_counts = np.bincount(bin_indices, weights=(df['frag_length'] > 160), minlength=num_bins)

# Calculate the ratio for each bin, avoiding division by zero
ratio = np.where(small_counts == 0, 0, np.where(large_counts == 0, 1, small_counts / large_counts))

# Calculate the logarithm of hist values, avoiding -inf values
new_counts = np.log(hist)
new_counts[new_counts == -np.inf] = 0

# Create a DataFrame with bin indices, counts, ratios, and other information
df_result = pd.DataFrame({
    'Bin Indices': np.arange(num_bins),
    'new_counts': new_counts,
    'Counts': hist,
    'true_counts': small_counts,
    'Small Counts': medium_counts,
    'Large Counts': large_counts,
    'Ratio': np.round(ratio * 10)
})

# Calculate the sum of small and large counts
total_counts = small_counts + large_counts

# Expand dimensions for new_counts
arr = np.expand_dims(new_counts, axis=1)
arr = np.expand_dims(arr, axis=0)

# Print the resulting DataFrame
print(df_result)


# In[10]:


# Create a 1D histogram with 100,000,000 bins using values from both columns
hist, bins = np.histogram(
    np.concatenate([df_unique['read_start'].values, df_unique['read_end'].values]),
    bins=100000000
)
print(hist.shape)

# Take the logarithm of the histogram values
hist = np.log(hist)

# Plot the histogram as a 1D heatmap using a logarithmic scale
plt.plot(bins[:-1], hist, color='#BDE0BD')

# Set labels and title for the plot
plt.xlabel('Human Genome (bp)')
plt.ylabel('Frequency (Log)')

# Show the plot
plt.show()


# In[ ]:




