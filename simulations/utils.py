import os
import shutil
import subprocess
import json

import pyorc
from smart_open import open as sopen


def get_samples(vcf_location):
    args = ["bcftools", "query", "--list-samples", vcf_location]
    samples_process = subprocess.Popen(
        args, stdout=subprocess.PIPE, cwd="/tmp", encoding="ascii"
    )
    sample_names = [line.strip() for line in samples_process.stdout]
    samples_process.stdout.close()

    return sample_names


def clear_tmp():
    for file_name in os.listdir("/tmp"):
        file_path = "/tmp/" + file_name
        if os.path.isfile(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)


def get_vcf_chromosomes(vcf):
    args = ["tabix", "--list-chroms", vcf]
    try:
        tabix_output = subprocess.check_output(args=args, cwd="/tmp", encoding="utf-8")
    except subprocess.CalledProcessError as e:
        print(e)
        tabix_output = ""
    try:
        clear_tmp()
    except:
        pass
    return tabix_output.split("\n")[:-1]


def upload_s3(args):
    cls, item, path = args
    header = (
        "struct<"
        + ",".join([f"{col.lower()}:string" for col in cls._table_columns])
        + ">"
    )
    bloom_filter_columns = list(map(lambda x: x.lower(), cls._table_columns))
    s3file = sopen(path, "wb")

    writer = pyorc.Writer(
        s3file,
        header,
        compression=pyorc.CompressionKind.SNAPPY,
        compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
        bloom_filter_columns=bloom_filter_columns,
    )

    row = tuple(
        item.__dict__[k]
        if type(item.__dict__[k]) == str
        else json.dumps(item.__dict__[k])
        for k in cls._table_columns
    )

    writer.write(row)
    writer.close()
    s3file.close()


def upload_batch_s3(args):
    cls, items, path = args
    header = (
        "struct<"
        + ",".join([f"{col.lower()}:string" for col in cls._table_columns])
        + ">"
    )
    bloom_filter_columns = list(map(lambda x: x.lower(), cls._table_columns))
    s3file = sopen(path, "wb")

    writer = pyorc.Writer(
        s3file,
        header,
        compression=pyorc.CompressionKind.SNAPPY,
        compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
        bloom_filter_columns=bloom_filter_columns,
    )

    for item in items:
        row = tuple(
            item.__dict__[k]
            if type(item.__dict__[k]) == str
            else json.dumps(item.__dict__[k])
            for k in cls._table_columns
        )
        writer.write(row)

    writer.close()
    s3file.close()


def get_writer(cls, path):
    header = (
        "struct<"
        + ",".join([f"{col.lower()}:{cls._table_column_types[col]}" for col in cls._table_columns])
        + ">"
    )
    bloom_filter_columns = list(map(lambda x: x.lower(), cls._table_columns))
    file = open(path, "wb+")
    writer = pyorc.Writer(
        file,
        header,
        compression=pyorc.CompressionKind.SNAPPY,
        compression_strategy=pyorc.CompressionStrategy.COMPRESSION,
        bloom_filter_columns=bloom_filter_columns,
    )

    return file, writer


def write_local(cls, item, writer):
    row = tuple(
        item.__dict__[k]
        if type(item.__dict__[k]) in (str, int)
        else json.dumps(item.__dict__[k])
        for k in cls._table_columns
    )
    writer.write(row)


def upload_local(local, s3):
    s3file = sopen(s3, "wb")

    with open(local, "rb") as fi:
        s3file.write(fi.read())
