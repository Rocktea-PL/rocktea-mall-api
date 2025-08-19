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
            order = StoreOrder.objects.get(id=order_id)
            self.stdout.write(f"Testing email for order: {order.order_sn}")
            self.stdout.write(f"Customer: {order.buyer.email}")
            self.stdout.write(f"Store: {order.store.name}")
            self.stdout.write(f"Items count: {order.items.count()}")
            
            # Send email
            result = send_order_completion_email_task.delay(order_id)
            self.stdout.write(self.style.SUCCESS(f'Email task initiated: {result.id}'))
            
        except StoreOrder.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Order not found: {order_id}'))