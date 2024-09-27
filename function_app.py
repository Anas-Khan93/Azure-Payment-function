import azure.functions as func
import logging
import json
import stripe
from django.shortcuts import get_object_or_404
from django.conf import settings
from .ai_interviewer.ai_appinterviewer.models import CartItems, User, UserProfile, Cart, Order


app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="StripeWebhookView", methods= ['POST'])
def StripeWebhookView(req: func.HttpRequest) -> func.HttpResponse:
    
    logging.info('Stripe Webhook received !')

    payload = req.get.body()
    sig_header = req.headers.get('sig_header')
    
    # Stripe endpoint secret
    endpoint_secret = settings.STRIPE_WEBHOOK
    
    
    try:
        event = stripe.Webhook.construct_event(
            
            payload, sig_header, endpoint_secret
        
        )
    except ValueError as e:
        return func.HttpResponse("Invalid Payload", status_code= 400)
    except stripe.error.SignatureVerificationError as e:
        return func.HttpResponse("Invalid Signature", status_code= 400)
    
    # Handle the Checkout event:
    print("ITS THE EVENT: ", event)
    
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        
        cart_id = session['metadata'].get('cart_id')
        user_id = session['metadata'].get('user_id')
        total_amount = session['metadata'].get('total_amount')
        
        cart_items= CartItems.objects.get(cart_id=cart_id)
        
        # Fetch the cart items and update the quantities of the products 
        for item in cart_items:
            product = item.product
            
            if item.quantity > product.prod:
                return ValueError("Not enough stock")
            
            product.prod_quantity -= item.quantity
            product.save()
            
        self.create_order(user_id, cart_id, total_amount )
        
        return HttpResponse("PAYMENT SUCCESSFUL", status=200)
    
    elif even['type'] == 'payment_intent.payment_failed':
        session = event['data']['object']
        
        return HttpResponse("PAYMENT FAILED", status= 200)
    return HttpResponse("Unhandled event type", status= 400)


def create_order(self, user_id, cart_id, total_amount):
    
    user = get_object_or_404(User, id=user_id)
    
    userprofile = get_object_or_404(UserProfile, user_id=user_id) 
    
    cart = get_object_or_404(Cart, pk=cart_id, user= userprofile)
    
    if not cart.items.exists():
        return {'error': 'cart is empty'}
    
    # Create an OBJECT INSTANCE:
    order = Order.objects.create(
        
        user= cart.user,
        cart= cart,
        customer_email= user.email,
        order_total_amount = total_amount,
        post_code = "M24 6PL", 
        deliv_add = "122 B Baker Street",

    )
    
    return order
        