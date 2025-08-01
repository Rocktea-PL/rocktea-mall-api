from django.core.exceptions import ValidationError
from django.http import JsonResponse
import magic

class FileUploadMiddleware:
    """Validate file uploads before processing"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_size = 5 * 1024 * 1024  # 5MB
        self.allowed_types = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'text/plain'
        }

    def __call__(self, request):
        if request.method == 'POST' and request.FILES:
            for file_key, uploaded_file in request.FILES.items():
                # Size validation
                if uploaded_file.size > self.max_size:
                    return JsonResponse({
                        'error': f'File {uploaded_file.name} exceeds 5MB limit'
                    }, status=413)
                
                # MIME type validation
                try:
                    mime_type = magic.from_buffer(uploaded_file.read(1024), mime=True)
                    uploaded_file.seek(0)  # Reset file pointer
                    
                    if mime_type not in self.allowed_types:
                        return JsonResponse({
                            'error': f'File type {mime_type} not allowed'
                        }, status=415)
                except:
                    # Fallback to content type header
                    if uploaded_file.content_type not in self.allowed_types:
                        return JsonResponse({
                            'error': f'File type {uploaded_file.content_type} not allowed'
                        }, status=415)
        
        return self.get_response(request)

def validate_file_size(file):
    """Validator for file size"""
    max_size = 5 * 1024 * 1024  # 5MB
    if file.size > max_size:
        raise ValidationError(f'File size {file.size} exceeds maximum allowed size of 5MB')

def validate_image_file(file):
    """Validator for image files"""
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise ValidationError(f'File type {file.content_type} not allowed for images')