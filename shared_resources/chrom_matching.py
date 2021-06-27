import subprocess

from lambda_utils import clear_tmp


CHROMOSOME_ALIASES = {
    'M': 'MT',
    'x': 'X',
    'y': 'Y',
}

CHROMOSOME_LENGTHS = {
    '1': 248956422,
    '2': 242193529,
    '3': 198295559,
    '4': 190214555,
    '5': 181538259,
    '6': 170805979,
    '7': 159345973,
    '8': 145138636,
    '9': 138394717,
    '10': 133797422,
    '11': 135086622,
    '12': 133275309,
    '13': 114364328,
    '14': 107043718,
    '15': 101991189,
    '16': 90338345,
    '17': 83257441,
    '18': 80373285,
    '19': 58617616,
    '20': 64444167,
    '21': 46709983,
    '22': 50818468,
    'X': 156040895,
    'Y': 57227415,
    'MT': 16569,
}

CHROMOSOMES = CHROMOSOME_LENGTHS.keys()


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

