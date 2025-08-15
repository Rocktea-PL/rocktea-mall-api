from celery import shared_task
from .models import StoreOrder, WithdrawalRecord
from .shipbubble_service import ShipbubbleService
from mall.payments.verify_payment import verify_transfer_paystack
import logging

logger = logging.getLogger(__name__)

@shared_task
def update_shipment_status():
    """Check and update shipment status for orders with tracking IDs"""
    shipbubble_service = ShipbubbleService()
    
    # Get orders with tracking IDs that are not delivered
    orders = StoreOrder.objects.filter(
        tracking_id__isnull=False,
        tracking_status__in=['pending', 'cancelled']
    ).exclude(tracking_id='')
    
    updated_count = 0
    
    for order in orders:
        try:
            # Get tracking status from Shipbubble
            response = shipbubble_service.track_shipping_status(order.tracking_id)
            
            if response.get('status') == 'success':
                data = response.get('data', {})
                new_status = data.get('status', '').lower()
                
                # Map Shipbubble status to our order status
                status_mapping = {
                    'pending': 'Pending',
                    'in_transit': 'Enroute',
                    'delivered': 'Delivered',
                    'cancelled': 'Returned'
                }
                
                mapped_status = status_mapping.get(new_status)
                
                if mapped_status and order.status != mapped_status:
                    order.tracking_status = new_status
                    order.save(update_fields=['tracking_status', 'tracking_status'])
                    updated_count += 1
                    logger.info(f"Updated order {order.id} status to {mapped_status}")
                    
        except Exception as e:
            logger.error(f"Error updating order {order.id}: {e}")
    
    logger.info(f"Updated {updated_count} orders")
    return f"Updated {updated_count} orders"

@shared_task
def check_withdrawal_status():
    """Check and update withdrawal status from Paystack"""
    # Get pending withdrawals that are older than 5 minutes
    from django.utils import timezone
    from datetime import timedelta
    
    five_minutes_ago = timezone.now() - timedelta(minutes=5)
    pending_withdrawals = WithdrawalRecord.objects.filter(
        status='pending',
        created_at__lte=five_minutes_ago
    )
    
    updated_count = 0
    
    for withdrawal in pending_withdrawals:
        try:
            if not withdrawal.transfer_code:
                continue
                
            # Check transfer status from Paystack
            response = verify_transfer_paystack(withdrawal.transfer_code)
            
            if response.get('status'):
                transfer_data = response.get('data', {})
                paystack_status = transfer_data.get('status', '').lower()
                
                # Map Paystack status to our status
                if paystack_status in ['success', 'successful']:
                    withdrawal.status = 'success'
                    withdrawal.processed_at = timezone.now()
                elif paystack_status in ['failed', 'reversed']:
                    withdrawal.status = 'failed'
                    withdrawal.processed_at = timezone.now()
                    
                    # Refund wallet if failed
                    wallet = withdrawal.wallet
                    wallet.balance = str(float(wallet.balance) + float(withdrawal.amount))
                    wallet.save()
                    
                    logger.info(f"Refunded {withdrawal.amount} to wallet {wallet.id}")
                
                # Update paystack response
                withdrawal.paystack_response = response
                withdrawal.save()
                updated_count += 1
                
                logger.info(f"Updated withdrawal {withdrawal.id} status to {withdrawal.status}")
                
        except Exception as e:
            logger.error(f"Error checking withdrawal {withdrawal.id}: {e}")
    
    logger.info(f"Checked {updated_count} withdrawals")
    return f"Checked {updated_count} withdrawals"