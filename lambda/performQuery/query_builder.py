from typing import List


class QueryBuiler:
    def __init__(self) -> None:
        self.region = ""
        self.samples = []
        self.format = "%POS\t%REF\t%ALT\t%INFO\t[%GT,]"
        self.vcf = ""
        self.parser_attrs = []

    def set_region(self, region: str):
        self.region = region

        return self

    def set_samples(self, samples: List[str]):
        self.samples = samples

        return self

    def set_vcf(self, vcf: str):
        self.vcf = vcf

        return self

    def set_return_samples(self, flag=True):
        if flag:
            self.format += "\t[%SAMPLE,]"
        return self

    def build(self):
        args = [
            "bcftools",
            "query",
            "--regions",
            self.region,
            "--format",
            f"{self.format}\n",
        ]

        if self.samples:
            args.extend(["--samples", ",".join(self.samples), self.vcf])
        else:
            args.append(self.vcf)

            # TODO if this is the case, must be piped for correct AC/AN
            # Use bcftools view for this
        print(f"Built query: {str(args)}")
        self.parser_attrs = len(self.format.split("\t"))
        return args

    def parse_line(self, line):
        if self.parser_attrs == 5:
            return line.split("\t") + [""]
        elif self.parser_attrs == 6:
            return line.split("\t")
