from typing import List


class QueryBuiler:
    def __init__(self) -> None:
        self.region = ""
        self.samples = []
        self.format = ""
        self.vcf = ""

    def set_region(self, region: str):
        self.region = region

        return self

    def set_samples(self, samples: List[str]):
        self.samples = samples

        return self

    def set_vcf(self, vcf: str):
        self.vcf = vcf

        return self

    def build(self):
        args = [
            "bcftools",
            "query",
            "--regions",
            self.region,
            "--format",
            "%POS\t%REF\t%ALT\t%INFO\t[%GT,]\t[%SAMPLE,]\n",
        ]

        if self.samples:
            args.extend(["--samples", ",".join(self.samples), self.vcf])
        else:
            args.append(self.vcf)
            
            # TODO if this is the case, must be piped for correct AC/AN
            # Use bcftools view for this
        print(f"Built query: {str(args)}") 
        return args
