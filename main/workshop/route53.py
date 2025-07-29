import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def get_route53_client():
    return boto3.client(
        "route53",
        region_name=settings.AWS_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

def create_cname_record(zone_id, subdomain, target):
    """
    Creates a CNAME record that points *subdomain* → *target* using Route 53.
    """
    try:
        response = get_route53_client().change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "UPSERT",  # Changed to UPSERT to handle existing records
                        "ResourceRecordSet": {
                            "Name": subdomain,
                            "Type": "CNAME",
                            "TTL": 300,
                            "ResourceRecords": [{"Value": target}],
                        }
                    }
                ]
            }
        )
        logger.info(f"Created CNAME {subdomain} → {target}: {response['ChangeInfo']['Id']}")
        return response
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidChangeBatch":
            logger.warning(f"CNAME already exists for {subdomain}")
        else:
            logger.exception("Route53 create_cname_record failed")
        return None

def create_alias_record(zone_id, subdomain, target_zone_id, target):
    """
    Creates an ALIAS (A) record that points *subdomain* → *target* using Route 53.
    Only use this for AWS resources like ALB, CloudFront, etc.
    """
    try:
        response = get_route53_client().change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "UPSERT",
                        "ResourceRecordSet": {
                            "Name": subdomain,
                            "Type": "A",
                            "AliasTarget": {
                                "HostedZoneId": target_zone_id,
                                "DNSName": target,
                                "EvaluateTargetHealth": False,
                            },
                        }
                    }
                ]
            }
        )
        logger.info(f"Created alias {subdomain} → {target}: {response['ChangeInfo']['Id']}")
        return response
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidChangeBatch":
            logger.warning(f"Alias already exists for {subdomain}")
        else:
            logger.exception("Route53 create_alias_record failed")
        return None