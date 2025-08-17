from celery import shared_task
import logging
import base64
from mall.models import CustomUser
from mall.cloudinary_utils import CloudinaryOptimizer

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, retry_backoff=60, name='tenants.tasks.upload_profile_image')
def upload_profile_image(self, user_id, file_content, file_name):
    """Background task to upload and optimize profile image"""
    try:
        logger.info(f"Task started for user {user_id}")
        
        user = CustomUser.objects.get(id=user_id)
        decoded_content = base64.b64decode(file_content)
        
        result = CloudinaryOptimizer.upload_optimized(
            decoded_content,
            folder='profiles',
            transformation_type='medium'
        )
        
        user.profile_image = result.get('secure_url')
        user.save(update_fields=['profile_image'])
        
        logger.info(f"Task completed for user {user_id}")
        return f"Success: {user_id}"
        
    except Exception as e:
        logger.error(f"Task failed for user {user_id}: {e}")
        return f"Failed: {e}"