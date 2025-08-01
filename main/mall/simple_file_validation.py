from django.http import JsonResponse
from django.conf import settings
import os

class SimpleFileUploadMiddleware:
    """Simple file upload validation without python-magic dependency"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_file_size = getattr(settings, 'FILE_UPLOAD_MAX_MEMORY_SIZE', 5 * 1024 * 1024)  # 5MB
        self.allowed_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp',  # Images
            '.pdf', '.doc', '.docx', '.txt',  # Documents
        }
        self.allowed_image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}

    def __call__(self, request):
        # Only validate file uploads, skip other requests
        if request.method == 'POST' and request.FILES and self.should_validate(request):
            try:
                validation_error = self.validate_files(request.FILES)
                if validation_error:
                    return JsonResponse({
                        'error': validation_error,
                        'status': 'validation_failed'
                    }, status=400)
            except Exception:
                # Don't block requests if validation fails
                pass
        
        response = self.get_response(request)
        return response
    
    def should_validate(self, request):
        """Only validate specific endpoints to avoid blocking admin"""
        skip_paths = ['/admin/', '/dropshippers/admin/']
        return not any(request.path.startswith(path) for path in skip_paths)

    def validate_files(self, files):
        """Validate uploaded files efficiently"""
        for field_name, file_list in files.lists():
            for uploaded_file in file_list:
                # Quick size check first
                if hasattr(uploaded_file, 'size') and uploaded_file.size > self.max_file_size:
                    return f"File exceeds {self.max_file_size // (1024*1024)}MB limit"
                
                # Quick extension check
                if hasattr(uploaded_file, 'name') and uploaded_file.name:
                    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
                    if file_ext and file_ext not in self.allowed_extensions:
                        return f"File type '{file_ext}' not allowed"
        
        return None

    def is_image_field(self, field_name):
        """Check if field should only accept images"""
        image_field_keywords = ['image', 'photo', 'picture', 'avatar', 'logo', 'cover']
        return any(keyword in field_name.lower() for keyword in image_field_keywords)