import mimetypes
import os

import boto3
from botocore.exceptions import ClientError
from decouple import config
from supabase import Client, create_client

from utils import data_utils

SUPABASE_URL = config("SUPABASE_URL")
SUPABASE_KEY = config("SERVICE_ROLE_KEY")
SUPABASE_CARRY_TABLE = config("SUPABASE_CARRY_TABLE")
SUPABASE_RATING_TABLE = config("SUPABASE_RATING_TABLE")

AWS_ACCESS_KEY_ID = config("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = config("AWS_SECRET_ACCESS_KEY")
AWS_REGION = config("AWS_REGION")
S3_BUCKET = config("AWS_S3_BUCKET_NAME")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

COLUMNS = ["name", "longtitle", "position", "size", "mmposition", "difficulty"]
# Initialize S3 client
s3_client = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


def upload_png_files(file_paths):
    for file_path in file_paths:
        file_name = os.path.basename(file_path)

        # Check if file already exists
        try:
            s3_client.head_object(Bucket=S3_BUCKET, Key=file_name)
            print(f"Skipped {file_name} (already exists)")
            continue
        except s3_client.exceptions.ClientError as e:
            if e.response["Error"]["Code"] != "404":
                print(f"Error checking {file_name}: {e}")
                continue  # real error, not just missing file

        # Upload file
        with open(file_path, "rb") as f:
            try:
                print(f"Uploading {file_name}...")
                s3_client.upload_fileobj(
                    f,
                    Bucket=S3_BUCKET,
                    Key=file_name,
                    ExtraArgs={"ContentType": "image/png"},
                )
                print(f"Uploaded {file_name}")
            except Exception as e:
                print(f"Failed to upload {file_name}: {e}")


def update_value_in_table(carryname):
    try:
        # Perform the update on the table
        response = (
            supabase.table(SUPABASE_CARRY_TABLE)
            .update({"tutorial": True})  # Column to update and its new value
            .eq("name", carryname)
            .execute()
        )

        # Check if the update was successful
        if response is not None:
            print("Successfully updated tutorial to True")
        else:
            print("Failed to update:", response.error_message)
    except Exception as e:
        print(f"Error updating value: {e}")


def get_carries():
    try:
        response = (
            supabase.table(SUPABASE_CARRY_TABLE)
            .select(
                f"""
                name, 
                longtitle, 
                position, 
                size, 
                mmposition,
                {SUPABASE_RATING_TABLE}(difficulty)
            """
            )
            .eq("tutorial", True)
            .execute()
        )

        carries = [
            data_utils.Carry(
                r["name"],
                r["longtitle"],
                r["mmposition"],
                r["position"],
                r["size"],
                r["wrappinggallery_rating"]["difficulty"],
            )
            for r in response.data
        ]

        return carries

    except Exception as e:
        return {"data": None, "error": str(e)}


def get_carry_by_name(carryname):
    response = (
        supabase.table(SUPABASE_CARRY_TABLE)
        .select(
            f"""
            name, 
            longtitle, 
            position, 
            size, 
            mmposition,
            {SUPABASE_RATING_TABLE}(difficulty)
        """
        )
        .eq("tutorial", True)
        .eq("name", carryname)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None  # or raise an exception if preferred

    r = response.data[0]
    return data_utils.Carry(
        r["name"],
        r["longtitle"],
        r["mmposition"],
        r["position"],
        r["size"],
        r["wrappinggallery_rating"]["difficulty"],
    )


def count_steps(carryname):
    count = 0

    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=S3_BUCKET)

        for page in page_iterator:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                file_name = obj["Key"]

                mime_type, _ = mimetypes.guess_type(file_name)
                if (
                    mime_type
                    and mime_type.startswith("image/")
                    and file_name.startswith(carryname.name + "_step")
                ):
                    count += 1

        return count

    except ClientError as e:
        print(f"Error accessing S3 bucket: {e}")
        return 0
    except Exception as e:
        print(str(e))
        return 0


def get_tutorial_steps_by_carry(name_filter):
    """
    Gets images from an AWS S3 bucket where filename contains a specific string

    Args:
        name_filter (str): String to filter filenames by (will match if filename contains this string)

    Returns:
        dict: Dictionary containing list of images with their data and URLs, or error message
    """
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        page_iterator = paginator.paginate(Bucket=S3_BUCKET)

        image_files = []

        for page in page_iterator:
            if "Contents" not in page:
                continue

            for obj in page["Contents"]:
                file_name = obj["Key"]

                # Filter filenames
                mime_type, _ = mimetypes.guess_type(file_name)
                if (
                    mime_type
                    and mime_type.startswith("image/")
                    and file_name.startswith(name_filter + "_step")
                ):
                    try:
                        signed_url = s3_client.generate_presigned_url(
                            ClientMethod="get_object",
                            Params={"Bucket": S3_BUCKET, "Key": file_name},
                            ExpiresIn=3600,
                        )
                        image_files.append({"name": file_name, "url": signed_url})
                    except ClientError as e:
                        print(f"Failed to generate URL for {file_name}: {e}")

        if not image_files:
            return {"data": None, "error": "No matching image files found"}

        return {"data": image_files, "error": None}

    except Exception as e:
        return {"data": None, "error": str(e)}
