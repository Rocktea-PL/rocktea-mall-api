"""
Test command for order completion email with the new modular service
"""
from django.core.management.base import BaseCommand
from order.models import StoreOrder
from setup.tasks import send_order_completion_email_task

class Command(BaseCommand):
    help = 'Test order completion email with improved service'

    def add_arguments(self, parser):
        parser.add_argument('--order-id', type=str, help='Order ID to test email for')
        parser.add_argument('--latest', action='store_true', help='Use latest order')

    def handle(self, *args, **options):
        order_id = options.get('order_id')
        
        if options.get('latest'):
            try:
                order = StoreOrder.objects.latest('created_at')
                order_id = order.id
                self.stdout.write(f"Using latest order: {order_id}")
            except StoreOrder.DoesNotExist:
                self.stdout.write(self.style.ERROR('No orders found'))
                return
        
        if not order_id:
            self.stdout.write(self.style.ERROR('Please provide --order-id or use --latest'))
            return
        
        try:
            # Debug order data first
            from order.debug_email import debug_order_email
            self.stdout.write("=== DEBUG ORDER DATA ===")
            context = debug_order_email(order_id)
            
            if context and context.get('has_items'):
                # Send email
                result = send_order_completion_email_task.delay(order_id)
                self.stdout.write(self.style.SUCCESS(f'Email task initiated: {result.id}'))
            else:
                self.stdout.write(self.style.WARNING('No items found in order - email may be incomplete'))
            
        except StoreOrder.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Order not found: {order_id}'))