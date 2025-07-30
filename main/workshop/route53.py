import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_route53_client():
    """Get Route53 client with AWS credentials"""
    return boto3.client(
        "route53",
        region_name=getattr(settings, 'AWS_REGION_NAME', 'us-east-1'),
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def create_cname_record(zone_id, subdomain, target):
    """
    Creates a CNAME record that points subdomain → target using Route 53.
    """
    if not zone_id:
        logger.error("No hosted zone ID provided")
        return None
        
    try:
        client = get_route53_client()
        
        response = client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "UPSERT",
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
        
        logger.info(f"Successfully created CNAME record: {subdomain} → {target}")
        return response
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        logger.error(f"Route53 error ({error_code}): {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating DNS record: {e}")
        return None