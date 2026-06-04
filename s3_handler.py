import boto3
import os
from datetime import datetime
from utils import get_env_variable


class S3Handler:

    def __init__(self, config, logger):

        self.logger = logger
        self.config = config

        self.bucket_name = get_env_variable("AWS_BUCKET_NAME")

        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=get_env_variable("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=get_env_variable("AWS_SECRET_ACCESS_KEY"),
            region_name=get_env_variable("AWS_REGION")
        )

        # S3 Layer Configuration
        self.layers = config["s3"]["layers"]

    # ══════════════════════════════════════════════════════
    # GENERATE ENTERPRISE FILE NAME
    # ══════════════════════════════════════════════════════

    def generate_s3_filename(self, local_file_path):

        original_filename = os.path.basename(local_file_path)

        # Remove extension
        base_name, extension = os.path.splitext(original_filename)

        # Clean filename
        base_name = (
            base_name
            .replace(" ", "_")
            .replace("-", "_")
            .lower()
        )

        # Timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Final enterprise-style filename
        final_name = f"{timestamp}_{base_name}{extension}"

        return final_name

    # ══════════════════════════════════════════════════════
    # UPLOAD FILE TO SPECIFIC LAYER
    # ══════════════════════════════════════════════════════

    def upload_file(self, local_file_path, layer):

        if layer not in self.layers:
            raise ValueError(
                f"Invalid S3 layer: {layer}"
            )

        if not os.path.exists(local_file_path):
            raise FileNotFoundError(
                f"File not found: {local_file_path}"
            )

        # Generate clean filename
        filename = self.generate_s3_filename(
            local_file_path
        )

        # Final S3 key
        s3_key = f"{self.layers[layer]}{filename}"

        self.logger.info(
            f"Uploading file to S3 layer: {layer}"
        )

        self.logger.info(
            f"S3 Key: {s3_key}"
        )

        self.s3_client.upload_file(
            local_file_path,
            self.bucket_name,
            s3_key
        )

        self.logger.info(
            f"Upload successful: {s3_key}"
        )

        return f"s3://{self.bucket_name}/{s3_key}"

    # ══════════════════════════════════════════════════════
    # LIST ALL BUCKET FILES
    # ══════════════════════════════════════════════════════

    def list_bucket_files(self):

        self.logger.info(
            "Fetching bucket file list..."
        )

        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name
        )

        files = []

        if "Contents" in response:

            files = [
                obj["Key"]
                for obj in response["Contents"]
            ]

        self.logger.info(
            f"Total files found: {len(files)}"
        )

        return files

    # ══════════════════════════════════════════════════════
    # LIST FILES BY LAYER
    # ══════════════════════════════════════════════════════

    def list_files_by_layer(self, layer):

        if layer not in self.layers:
            raise ValueError(
                f"Invalid S3 layer: {layer}"
            )

        prefix = self.layers[layer]

        response = self.s3_client.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=prefix
        )

        files = []

        if "Contents" in response:

            files = [
                obj["Key"]
                for obj in response["Contents"]
            ]

        return files

    # ══════════════════════════════════════════════════════
    # ARCHIVE FILE
    # ══════════════════════════════════════════════════════

    def archive_file(self, s3_key):

        archive_key = (
            f"{self.layers['archive']}"
            f"{os.path.basename(s3_key)}"
        )

        self.logger.info(
            f"Archiving file: {s3_key}"
        )

        copy_source = {
            "Bucket": self.bucket_name,
            "Key": s3_key
        }

        # Copy to archive
        self.s3_client.copy_object(
            CopySource=copy_source,
            Bucket=self.bucket_name,
            Key=archive_key
        )

        # Delete original
        self.s3_client.delete_object(
            Bucket=self.bucket_name,
            Key=s3_key
        )

        self.logger.info(
            f"Archived successfully: {archive_key}"
        )

        return archive_key

    # ══════════════════════════════════════════════════════
    # DELETE FILE
    # ══════════════════════════════════════════════════════

    def delete_file(self, s3_key):

        self.logger.info(
            f"Deleting file: {s3_key}"
        )

        self.s3_client.delete_object(
            Bucket=self.bucket_name,
            Key=s3_key
        )

        self.logger.info(
            f"Deleted successfully: {s3_key}"
        )

    # ══════════════════════════════════════════════════════
    # RAW LAYER UPLOAD
    # ══════════════════════════════════════════════════════

    def upload_raw_file(self, local_file_path):

        return self.upload_file(
            local_file_path,
            "raw"
        )

    # ══════════════════════════════════════════════════════
    # STAGING LAYER UPLOAD
    # ══════════════════════════════════════════════════════

    def upload_staging_file(self, local_file_path):

        return self.upload_file(
            local_file_path,
            "staging"
        )

    # ══════════════════════════════════════════════════════
    # PROCESSED LAYER UPLOAD
    # ══════════════════════════════════════════════════════

    def upload_processed_file(self, local_file_path):

        return self.upload_file(
            local_file_path,
            "processed"
        )