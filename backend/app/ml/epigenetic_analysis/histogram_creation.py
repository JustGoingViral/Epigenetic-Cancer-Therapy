#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import numpy as np
import os
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re
import gzip
import io
from PIL import Image
import random


# In[2]:


def process_bed(directory, filename):
    # Print directory and filename for debugging
    print(directory)
    print(filename)
    
    # Construct the file path
    f = os.path.join(directory, filename)
    
    # Read the compressed file content and decode it to string
    with gzip.open(f, 'rb') as file:
        file_content = file.read().decode('utf-8')
    
    # Assuming the content is tab-delimited data, convert it to DataFrame
    df = pd.read_csv(io.BytesIO(file_content.encode()), delimiter='\t')
    
    # Chromosome position mapping
    chrom_pos ={'chr1': 0,
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
            'chrY': 3031042417}
    
    # Define column headers
    header = ['chrom', 'read_start', 'read_end', 'name', 'score', 'strand']
    df.columns = header[:len(df.columns)]

    # Calculate max value and modify 'name' and 'frag_length'
    max_value = df['read_end'].max()
    df['name'] = df['name'].str.rstrip('12') + '1'
    df['frag_length'] = df.groupby('name')['read_end'].transform('max') - df.groupby('name')['read_start'].transform('min')
    
    # Aggregate DataFrame to unique 'name' entries
    df = df.groupby('name', as_index=False).agg({
        'chrom': 'first',
        'read_start': 'min',
        'read_end': 'max',
        'name': 'first',
        'score': 'first',
        'strand': 'first',
        'frag_length': 'first'
    })

    # Remove extra information from 'chrom' values
    df["chrom"] = df["chrom"].str.split("_").str.get(0)
    
    # Mask for filtering "chrUn" chromosomes
    mask = df["chrom"].str.startswith("chrUn")
    
    # Exclude "chrUn" chromosomes and fragments longer than 1000
    df = df[~mask]
    df = df[df.frag_length <= 1000]

    # Adjust positions based on chromosome mapping
    for key, value in chrom_pos.items():
        mask = df['chrom'] == key
        df.loc[mask, 'read_start'] += value
        df.loc[mask, 'read_end'] += value
    
    # Convert specific columns to integers
    columns_to_convert = ['read_start', 'read_end', 'frag_length']
    df[columns_to_convert] = df[columns_to_convert].astype(int)
    
    # Sort DataFrame and drop duplicate rows
    df = df.sort_values('read_start')
    df = df.drop_duplicates(subset=['read_start', 'read_end'], keep='first')
    
    # Calculate histogram for read start and end positions
    num_bins = 2000000
    bin_edges = np.linspace(0, 3088269832, num_bins + 1)
    hist, bins = np.histogram(np.concatenate([df['read_start'].values, df['read_end'].values]), bins=bin_edges)
    
    return hist


# In[4]:


trying=process_bed('/home/sam/sra_files','cancer_SRR17006162.bed.gz')


# In[5]:


# Lists to store cancer and control filenames
cancer = []
control = []

# Set the directory where patient files are stored
directory = '/home/sam/sra_files'

# Get a list of all files in the directory
files = os.listdir(directory)

# Print the first 10 files in the directory for debugging
print(files[0:10])

# Iterate through each file in the directory
for k in files:
    # Check if the file contains 'cancer' and there are fewer than 400 cancer files collected
    if 'cancer' in k and len(cancer) < 400:
        cancer.append(k)
    # Check if the file contains 'control' and there are fewer than 400 control files collected
    elif 'control' in k and len(control) < 400:
        control.append(k)

# Print the number of collected cancer files
print(len(cancer))

# Combine the lists of cancer and control files
new_files = cancer + control

# Print the first 10 cancer filenames and the total number of new files
print(cancer[0:10])
print(len(new_files))


# In[6]:


# Write cancer filenames to a text file
with open(r'/home/sam/cancer_names.txt', 'w') as fp:
    for item in cancer:
        # Write each item on a new line
        fp.write("%s\n" % item)
    print('Done writing cancer filenames')

# Write control filenames to a text file
with open(r'/home/sam/control_names.txt', 'w') as fp:
    for item in control:
        # Write each item on a new line
        fp.write("%s\n" % item)
    print('Done writing control filenames')


# In[7]:


# Lists to store processed cancer and control data
cancer_full = []
control_full = []

l = 0  # Counter for tracking progress

# Iterate through each file in the combined list of cancer and control filenames
for k in new_files:
    if 'cancer' in k:
        # Process the bed file and append the patient data to cancer_full
        patient = process_bed(directory, k)
        cancer_full.append(patient)
    elif 'control' in k:
        # Process the bed file and append the patient data to control_full
        patient = process_bed(directory, k)
        control_full.append(patient)

    # Save data and reset lists when the respective batch size is reached
    if len(control_full) == 400:
        control_arr = np.array(control_full)
        with open('test_sort.npy', 'ab') as f:
            np.save(f, control_arr)
        control_arr = []
        control_full = []
    elif len(cancer_full) == 400:
        cancer_arr = np.array(cancer_full)
        with open('test_sort.npy', 'wb') as f:
            np.save(f, cancer_arr)
        cancer_arr = []
        cancer_full = []

    # Increment the counter and print progress every 10 iterations
    l += 1
    if l % 10 == 0:
        print(f'Processed {l} patients')


# In[ ]:




