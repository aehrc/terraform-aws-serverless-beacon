import subprocess


def get_samples(vcf_location):
    args = [
        'bcftools', 'query',
        '--list-samples',
        vcf_location
    ]
    samples_process = subprocess.Popen(
        args, stdout=subprocess.PIPE, cwd='/tmp', encoding='ascii')
    sample_names = [line.strip() for line in samples_process.stdout]
    samples_process.stdout.close()

    return sample_names