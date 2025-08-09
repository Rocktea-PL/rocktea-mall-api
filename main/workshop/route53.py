import boto3
from botocore.exceptions import ClientError
from django.conf import settings
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def get_route53_client():
    """Get Route53 client with AWS credentials (cached for performance)"""
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
                            "TTL": 60,  # Reduced TTL for faster propagation
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


def delete_cname_record(zone_id, subdomain, target):
    """
    Deletes a CNAME record from Route 53.
    """
    if not zone_id:
        logger.error("No hosted zone ID provided for deletion")
        return None
        
    try:
        client = get_route53_client()
        
        response = client.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch={
                "Changes": [
                    {
                        "Action": "DELETE",
                        "ResourceRecordSet": {
                            "Name": subdomain,
                            "Type": "CNAME",
                            "TTL": 60,
                            "ResourceRecords": [{"Value": target}],
                        }
                    }
                ]
            }
        )
        
        logger.info(f"Successfully deleted CNAME record: {subdomain}")
        return response
        
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "InvalidChangeBatch":
            logger.warning(f"DNS record {subdomain} may not exist or already deleted")
        else:
            logger.error(f"Route53 deletion error ({error_code}): {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error deleting DNS record: {e}")
        return None


def get_existing_record(zone_id, subdomain):
    """
    Check if a DNS record exists and get its details.
    """
    if not zone_id:
        return None
        
    try:
        client = get_route53_client()
        
        response = client.list_resource_record_sets(
            HostedZoneId=zone_id,
            StartRecordName=subdomain,
            StartRecordType='CNAME',
            MaxItems='1'
        )
        
        for record in response.get('ResourceRecordSets', []):
            if record['Name'].rstrip('.') == subdomain.rstrip('.'):
                return record
                
        return None
        
    except ClientError as e:
        logger.error(f"Error checking existing record: {e}")
        return None


def delete_store_dns_record(domain_identifier, environment='dev'):
    """
    Delete DNS record for a store when dropshipper is deleted.
    domain_identifier can be either a store slug or a full domain name.
    """
    from mall.utils import determine_environment_config, generate_store_domain
    
    try:
        # Get environment configuration
        env_config = determine_environment_config()
        
        # Skip deletion for local environment
        if env_config['environment'] == 'local':
            logger.info(f"Local environment - skipping DNS deletion for: {domain_identifier}")
            return True
        
        # Determine if domain_identifier is a full domain or just a slug
        if '.' in domain_identifier and not domain_identifier.startswith('http'):
            # It's already a full domain
            full_domain = domain_identifier
            logger.info(f"Using provided domain: {full_domain}")
        else:
            # It's a slug, generate the full domain
            full_domain = generate_store_domain(domain_identifier, env_config['environment'])
            logger.info(f"Generated domain from slug: {full_domain}")
        
        if not full_domain:
            logger.warning(f"No domain to delete for identifier: {domain_identifier}")
            return False
        
        # Check if record exists first
        existing_record = get_existing_record(env_config['hosted_zone_id'], full_domain)
        
        if not existing_record:
            logger.info(f"DNS record {full_domain} does not exist or already deleted")
            return True
        
        # Get the target from existing record
        target = existing_record['ResourceRecords'][0]['Value']
        
        # Delete the DNS record
        response = delete_cname_record(
            zone_id=env_config['hosted_zone_id'],
            subdomain=full_domain,
            target=target
        )
        
        if response:
            logger.info(f"Successfully deleted DNS record: {full_domain}")
            return True
        else:
            logger.error(f"Failed to delete DNS record: {full_domain}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting DNS record for {domain_identifier}: {e}")
        return False
