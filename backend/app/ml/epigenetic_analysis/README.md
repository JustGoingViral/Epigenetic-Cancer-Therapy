# Epigenetic Cancer Analysis Pipeline

This module contains a comprehensive pipeline for analyzing cancer and control patient datasets using next-generation sequencing data. The pipeline involves several functions that perform various tasks, from data preprocessing to neural network-based analysis.

## Function Descriptions

### 1. `metadata_treat.py`
This function utilizes data from the `SraRunTable.txt` metadata file, which can be obtained through the NCBI SRA Run Selector. It creates a dataset containing information about control and cancer patients, along with their SRA run names.

### 2. `sra_script.py`
Using the SRA run names from the dataset generated by `metadata_treat.py`, this function downloads SRA run data, aligns it to the human hg38 genome, and generates BED files. Replace "cancer" with "control" if using the `df_control` dataset.

### 3. `Tests_on_SRA_files.py`
This function conducts tests on the BED files to enable thorough analysis of the dataset. Various tests and quality checks are performed to ensure the reliability of the data.

### 4. `Chrom_info.py`
Extracts chromosome positioning information from the BED files, which is essential for generating histograms containing fragment distribution data.

### 5. `histogram_creation.py`
Uses the chromosome positioning information to create histograms that provide insights into fragment distribution patterns within the dataset.

### 6. `AI_simple_NN_WRST.py`
Implements a neural network using the `histogram_creation` data. This neural network aids in data analysis and cancer detection with high accuracy.

## System Requirements

Please be aware that due to the complexity of the analysis and the large amount of data involved, your system should have sufficient memory and processing capabilities.

## Usage

1. Ensure you are using a Linux-based system, as the pipeline is designed to work best on this platform.

2. Install the required dependencies using Conda and Bioconda, including:
   - FASTQC
   - Bedtools
   - Samtools

   ```bash
   conda install -c bioconda fastqc bedtools samtools
   ```

3. Run the functions in the order specified above, ensuring that you provide the necessary inputs and configurations.

4. Monitor memory usage during execution and consider utilizing a system with higher memory capacity if memory-related errors occur.

## Dependencies

- FASTQC
- Bedtools
- Samtools
- TensorFlow
- scikit-learn
- pandas
- numpy
- matplotlib

## Integration with MTET Platform

This module is fully integrated with the Multi-Targeted Epigenetic Cancer Therapy Platform, providing advanced genomic analysis capabilities for precision cancer medicine.
