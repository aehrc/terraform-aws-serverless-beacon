import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


def generate_presigned_url(
    bucket_name: str, object_key: str, expiration: int = 3600
) -> str:
    """
    Generate a presigned URL to download an S3 object

    :param bucket_name: string, name of the S3 bucket
    :param object_key: string, key of the object in the S3 bucket
    :param expiration: Time in seconds for the presigned URL to remain valid, default is 3600 seconds (1 hour)
    :return: Presigned URL as string, if successful. None if error occurs.
    """
    s3_client = boto3.client("s3")

    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_key},
            ExpiresIn=expiration,
        )
    except (NoCredentialsError, PartialCredentialsError) as e:
        print(f"Error generating presigned URL: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None

    return response
