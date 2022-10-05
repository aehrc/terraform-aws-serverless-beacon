## VCF files

Create a file named `vcf.txt` and put VCF files in each line for the simulation of datasets in the following format. These must be VCF files in gzipped format with an index file (tbi or csi). If there are multiple vcfs, separate them using spaces.

```txt
MULTIPLIER VCF1 VCF2 VCF3 ...
```

An example would be;

```txt
1000 s3://mybucket/vcf.1000.samples.chr-1.gz s3://mybucket/vcf.1000.samples.chr-2.gz
```

The above will simulate 1000 datasets from the vcf collection. This yields a synthetic population of 1 Million people.

## Simulation

Prepare the environment as follows.

```bash
$ export AWS_REGION=<REGION>
$ export AWS_DEFAULT_REGION=<REGION>
```

Now run `python simulate.py`.

## Indexing

At the end, run the indexer lambda function to build the onto index.