import subprocess

from lambda_utils import clear_tmp


CHROMOSOME_ALIASES = {
    'M': 'MT',
    'x': 'X',
    'y': 'Y',
}

CHROMOSOME_LENGTHS_MBP = {
    '1': 248.956422,
    '2': 242.193529,
    '3': 198.295559,
    '4': 190.214555,
    '5': 181.538259,
    '6': 170.805979,
    '7': 159.345973,
    '8': 145.138636,
    '9': 138.394717,
    '10': 133.797422,
    '11': 135.086622,
    '12': 133.275309,
    '13': 114.364328,
    '14': 107.043718,
    '15': 101.991189,
    '16': 90.338345,
    '17': 83.257441,
    '18': 80.373285,
    '19': 58.617616,
    '20': 64.444167,
    '21': 46.709983,
    '22': 50.818468,
    'X': 156.040895,
    'Y': 57.227415,
    'MT': 0.016569,
}

CHROMOSOMES = CHROMOSOME_LENGTHS_MBP.keys()


def get_vcf_chromosomes(vcf):
    args = [
        'tabix',
        '--list-chroms',
        vcf
    ]
    try:
        tabix_output = subprocess.check_output(args=args, cwd='/tmp', encoding='utf-8')
    except subprocess.CalledProcessError as e:
        print(e)
        tabix_output = ''
    clear_tmp()
    return tabix_output.split('\n')[:-1]


def get_matching_chromosome(vcf_chromosomes, target_chromosome):
    for vcf_chrom in vcf_chromosomes:
        if _match_chromosome_name(vcf_chrom) == target_chromosome:
            return vcf_chrom
    return None


def _match_chromosome_name(chromosome_name):
    for i in range(len(chromosome_name)):
        chrom = chromosome_name[i:]  # progressively remove prefix
        if chrom in CHROMOSOMES:
            return chrom
        elif chrom in CHROMOSOME_ALIASES:
            return CHROMOSOME_ALIASES[chrom]
    print('WARNING: Could not find chromosome to match "{}"'.format(chromosome_name))
    return None

