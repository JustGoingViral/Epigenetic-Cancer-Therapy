import pandas as pd
import math
import numpy as np

# Read the input data from a CSV file, modify the file location to accommodate your environment 
df = pd.read_csv(r'/Desktop/SraRunTable.txt')

# Select specific columns from the DataFrame
df = df[['Run', 'Age', 'disease', 'AvgSpotLen', 'Bases', 'sex', 'disease_stage', 'Library Name']]

# Filter rows based on Library Name ending with 'PC'
df = df[df['Library Name'].str.endswith('PC')]

# Calculate the estimated number of reads
df['reads'] = ((df['Bases'] / (df['AvgSpotLen'] * 2))).apply(np.floor).astype(int)

# Separate data into cancer and control groups and save to separate files
df_cancer = df[df['disease'] == 'COLORECTAL CANCER']
df_cancer.to_csv(r'c:\users\jeremie\desktop\df_cancer.txt', index=None)
print(df_cancer.head())

df_control = df[df['disease'] == 'CONTROL']
df_control.to_csv(r'c:\users\jeremie\desktop\df_control.txt', index=None)
print(df_control.head())
