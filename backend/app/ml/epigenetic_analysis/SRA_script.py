
#!/usr/bin/python3.10
import os
import subprocess
import random
import pandas as pd

# Load the cancer data file as a DataFrame
df_cancer = pd.read_csv(r"/home/sam/df_cancer.txt")

# Extract SRA names and read counts from the DataFrame
sra_names = df_cancer['Run'].tolist()
sra_reads = df_cancer['reads'].tolist()

# Set paths and parameters
sra_file = r"/home/sam/df_cancer.txt"
genome_dir = 'human_ge'  # Replace with your genome directory

# Fastq-dump parameters
n_reads = 1000000  # Number of reads to download per SRA file
output_dir = '/home/sam/fastq'  # Replace with your desired output directory

# Bowtie2 parameters
num_threads = 8 

# Combine BAM files using samtools
bam_files = []
bam_file = '/home/sam/all_samples.bam'  # Replace with your desired output BAM file

bedgraph_file = '/home/sam/all_samples.bedGraph'  # Replace with your desired output bedGraph file

# Download SRA files, convert to Fastq, align reads, and create BAM and bedGraph files

# Loop through a subset of SRA names
for n in range(0, 400):
    sra_name = sra_names[n]
    read = sra_reads[n]
    
    # Generate a random start position within the read range
    max_num = read
    num_samples = 1000000
    start = random.randint(0, max_num - num_samples)
    end = start + 999999

    # Download n_reads from the SRA file and output as paired-end Fastq files
    output_file_1 = f'{output_dir}/{sra_name}_1.fastq.gz'
    output_file_2 = f'{output_dir}/{sra_name}_2.fastq.gz'
    bed = f'/desktop/sra_files/cancer_{sra_name}.bed.gz' #must be changed if control dataset is downloaded
    cmd = f'fastq-dump --gzip --split-files -N {start} -X {end} {sra_name} --outdir {output_dir} '
    subprocess.run(cmd, shell=True)

    # Align paired-end reads to the reference genome using Bowtie2
    input_file_1 = f'{output_dir}/{sra_name}_1.fastq.gz'
    input_file_2 = f'{output_dir}/{sra_name}_2.fastq.gz'
    output_file = f'{output_dir}/{sra_name}.bam'
    cmd = f'bowtie2 -p {num_threads} -x {genome_dir} -1 {input_file_1} -2 {input_file_2} | samtools view -bS - > {output_file}'
    subprocess.run(cmd, shell=True)

    # Remove unnecessary Fastq files
    os.remove(input_file_1)
    os.remove(input_file_2)

    # Add the resulting BAM file to the list of BAM files
    bam_files.append(output_file)

    # Sort and index the BAM file, then convert to bedGraph format
    cmd = f'samtools sort -@ {num_threads} -o {output_file} {output_file}; samtools index {output_file}; bedtools bamtobed -i {output_file} | gzip > {bed}'
    subprocess.run(cmd, shell=True)
    os.remove(output_file)
      
