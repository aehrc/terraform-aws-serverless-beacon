import subprocess


CHROMOSOME_ALIASES = {
    "M": "MT",
    "x": "X",
    "y": "Y",
}

CHROMOSOME_LENGTHS = {
    "1": 248956422,
    "2": 242193529,
    "3": 198295559,
    "4": 190214555,
    "5": 181538259,
    "6": 170805979,
    "7": 159345973,
    "8": 145138636,
    "9": 138394717,
    "10": 133797422,
    "11": 135086622,
    "12": 133275309,
    "13": 114364328,
    "14": 107043718,
    "15": 101991189,
    "16": 90338345,
    "17": 83257441,
    "18": 80373285,
    "19": 58617616,
    "20": 64444167,
    "21": 46709983,
    "22": 50818468,
    "X": 156040895,
    "Y": 57227415,
    "MT": 16569,
}

CHROMOSOMES = CHROMOSOME_LENGTHS.keys()


def get_vcf_chromosomes(vcf):
    args = ["tabix", "--list-chroms", vcf]
    errored = False
    error = ""
    chromosomes = []

    try:
        tabix_output = subprocess.check_output(args=args, cwd="/tmp", encoding="utf-8")
        chromosomes = tabix_output.strip().split("\n")
        print(f"vcf - {vcf} has chromosomes - {chromosomes}")
    except subprocess.CalledProcessError as e:
        error_message = e.stderr
        print(
            "cmd {} returned non-zero error code {}. stderr:\n{}".format(
                e.cmd, e.returncode, error_message
            )
        )
        if error_message.startswith("[E::hts_open_format] Failed to open"):
            error = "Could not access {}.".format(vcf)
        elif error_message.startswith("[E::hts_hopen] Failed to open"):
            error = "{} is not a gzipped vcf file.".format(vcf)
        elif error_message.startswith("Could not load .tbi index"):
            error = "Could not open index file for {}.".format(vcf)
        else:
            error = str(e)
        errored = True
        tabix_output = ""
    
    return errored, error, chromosomes


def get_matching_chromosome(vcf_chromosomes, target_chromosome):
    for vcf_chrom in vcf_chromosomes:
        if vcf_chrom == target_chromosome:
            return vcf_chrom
        elif _match_chromosome_name(vcf_chrom) == target_chromosome:
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
