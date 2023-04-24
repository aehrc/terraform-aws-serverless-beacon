# Getting started with test data

Please ensure you first upload the `chr1.vcf.gz` and `chr1.vcf.gz.tbi` files to an S3 bucket that is accessible from the sBeacon deployment account. Obtain the S3 URI for the `chr1.vcf.gz` from the uploaded desitation. Note that, both `vcf.gz` and `vcf.gz.tbi` files must have the same prefix in S3 for this to work.

Now edit the `submission.json` file such that they match the S3 URI of the `vcf.gz` file.

```json
...
    "vcfLocations": [
        "s3://<bucket>/<prefix>/chr1.vcf.gz"
    ]
...
```

You can submit the data in two ways.

### Submission as request body

You can simply copy the edited JSON content in to the API gateway `/submit` POST endpoint. If you're using a REST client make sure you add authorization headers before you make the request. For example, Postman supports Authorization type AWS Signature and there you can enter AWS Keys.

### Submission as an S3 payload

Alternatively, you can upload edited `submission.json` file to an S3 location accessible from deployment. Then you can use the file's S3 URI as follows in the API Gateway or in your REST client.

```json
{
    "s3Payload": "s3://<bucket>/<prefix>/submission.json"
}
```

This approach is recommended for larger submissions with thousands of metadata entries.