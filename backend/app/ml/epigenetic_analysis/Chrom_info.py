from pyfaidx import Fasta

# Path to the reference genome FASTA file
fasta_file = "/home/sam/hg38.fa"

# Create a Fasta object with the reference genome FASTA file
genome = Fasta(fasta_file)
chromosomes = []
# List of chromosome names in the reference genome
for n in range(1,23):
    chromosomes.append(f'chr{n}')
chromosomes.append('chrX')
chromosomes.append('chrY')
#find the maximal value:
chroms_max=[]
chrom_pos=0
chrom_posit=[]
# Iterate over the chromosomes and retrieve the maximum base pair position
for chromosome in chromosomes:
    chrom_posit.append(chrom_pos)
    chrom_length = len(genome[chromosome])
    print(f"'{chromosome}': {chrom_pos},")
    chrom_pos=chrom_length+chrom_pos
    chroms_max.append(chrom_length)
    
print(f"final length: {chrom_pos}")
    
print(f'The maximal value is: {max(chroms_max)}')