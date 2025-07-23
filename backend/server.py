from fastapi import FastAPI, APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timedelta
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Stripe configuration
stripe_api_key = os.environ.get('STRIPE_API_KEY')

# Data Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserCreate(BaseModel):
    email: str
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None

class UserLogin(BaseModel):
    email: str

class Restaurant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    cuisine_type: str
    rating: float = 4.5
    delivery_time: str = "30-45 min"
    delivery_fee: float = 2.99
    image_url: str
    description: str

class FoodItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    restaurant_id: str
    name: str
    description: str
    price: float
    category: str
    image_url: str
    is_vegetarian: bool = False
    is_available: bool = True

class CartItem(BaseModel):
    food_item_id: str
    quantity: int = 1
    special_instructions: Optional[str] = None

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    restaurant_id: str
    items: List[CartItem]
    total_amount: float
    delivery_address: str
    status: str = "pending"  # pending, confirmed, preparing, on_way, delivered, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_delivery: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(minutes=40))
    payment_session_id: Optional[str] = None

class OrderCreate(BaseModel):
    user_id: str
    restaurant_id: str
    items: List[CartItem]
    delivery_address: str

class Review(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    restaurant_id: str
    order_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ReviewCreate(BaseModel):
    user_id: str
    restaurant_id: str
    order_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None

class PaymentTransaction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    payment_id: Optional[str] = None
    user_id: Optional[str] = None
    order_id: str
    amount: float
    currency: str = "usd"
    payment_status: str = "pending"  # pending, paid, failed, cancelled
    status: str = "initiated"  # initiated, completed, expired
    metadata: Optional[Dict[str, str]] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CheckoutRequest(BaseModel):
    order_id: str 
    origin_url: str

# Initialize sample data
async def init_sample_data():
    # Check if data already exists
    existing_restaurants = await db.restaurants.find_one()
    if existing_restaurants:
        return
    
    # Sample restaurants
    restaurants = [
        {
            "id": str(uuid.uuid4()),
            "name": "Bella Italia",
            "cuisine_type": "Italian",
            "rating": 4.8,
            "delivery_time": "25-35 min",
            "delivery_fee": 2.99,
            "image_url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwyfHxyZXN0YXVyYW50fGVufDB8fHx8MTc1MzI3Mjc2MHww&ixlib=rb-4.1.0&q=85",
            "description": "Authentic Italian cuisine with fresh ingredients"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Spice Garden",
            "cuisine_type": "Indian",
            "rating": 4.6,
            "delivery_time": "30-45 min", 
            "delivery_fee": 3.49,
            "image_url": "https://images.unsplash.com/photo-1737141499779-5e228d601f98?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwzfHxkZWxpY2lvdXMlMjBtZWFsc3xlbnwwfHx8fDE3NTMyNzI3NTR8MA&ixlib=rb-4.1.0&q=85",
            "description": "Flavorful Indian dishes with authentic spices"
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Ocean Breeze",
            "cuisine_type": "Seafood",
            "rating": 4.7,
            "delivery_time": "35-45 min",
            "delivery_fee": 4.99,
            "image_url": "https://images.unsplash.com/photo-1414235077428-338989a2e8c0?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzF8MHwxfHNlYXJjaHwzfHxyZXN0YXVyYW50fGVufDB8fHx8MTc1MzI3Mjc2MHww&ixlib=rb-4.1.0&q=85",
            "description": "Fresh seafood and coastal flavors"
        }
    ]
    
    await db.restaurants.insert_many(restaurants)
    
    # Sample food items
    food_items = []
    for restaurant in restaurants:
        if restaurant["cuisine_type"] == "Italian":
            items = [
                {"name": "Margherita Pizza", "description": "Classic pizza with fresh mozzarella and basil", "price": 12.99, "category": "Pizza", "is_vegetarian": True},
                {"name": "Spaghetti Carbonara", "description": "Creamy pasta with bacon and parmesan", "price": 14.99, "category": "Pasta", "is_vegetarian": False},
                {"name": "Caesar Salad", "description": "Fresh romaine with caesar dressing", "price": 8.99, "category": "Salad", "is_vegetarian": True},
                {"name": "Tiramisu", "description": "Classic Italian dessert", "price": 6.99, "category": "Dessert", "is_vegetarian": True}
            ]
        elif restaurant["cuisine_type"] == "Indian":
            items = [
                {"name": "Butter Chicken", "description": "Creamy tomato-based chicken curry", "price": 15.99, "category": "Main Course", "is_vegetarian": False},
                {"name": "Palak Paneer", "description": "Spinach curry with cottage cheese", "price": 13.99, "category": "Main Course", "is_vegetarian": True},
                {"name": "Garlic Naan", "description": "Fresh baked bread with garlic", "price": 3.99, "category": "Bread", "is_vegetarian": True},
                {"name": "Mango Lassi", "description": "Sweet yogurt drink with mango", "price": 4.99, "category": "Beverage", "is_vegetarian": True}
            ]
        else:  # Seafood
            items = [
                {"name": "Grilled Salmon", "description": "Fresh Atlantic salmon with herbs", "price": 18.99, "category": "Main Course", "is_vegetarian": False},
                {"name": "Fish & Chips", "description": "Beer battered fish with crispy fries", "price": 14.99, "category": "Main Course", "is_vegetarian": False},
                {"name": "Seafood Pasta", "description": "Mixed seafood with linguine", "price": 19.99, "category": "Pasta", "is_vegetarian": False},
                {"name": "Clam Chowder", "description": "Creamy New England style soup", "price": 7.99, "category": "Soup", "is_vegetarian": False}
            ]
        
        for item in items:
            food_item = {
                "id": str(uuid.uuid4()),
                "restaurant_id": restaurant["id"],
                "image_url": "https://images.unsplash.com/photo-1679989260436-1038a839f434?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxkZWxpY2lvdXMlMjBtZWFsc3xlbnwwfHx8fDE3NTMyNzI3NTR8MA&ixlib=rb-4.1.0&q=85",
                "is_available": True,
                **item
            }
            food_items.append(food_item)
    
    await db.food_items.insert_many(food_items)

# Auth endpoints
@api_router.post("/auth/login", response_model=User)
async def login_user(user_data: UserLogin):
    # Simple auth - check if user exists, create if not
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        return User(**existing_user)
    
    # Create new user
    new_user = User(email=user_data.email, name=user_data.email.split('@')[0])
    await db.users.insert_one(new_user.dict())
    return new_user

@api_router.post("/auth/register", response_model=User)
async def register_user(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    new_user = User(**user_data.dict())
    await db.users.insert_one(new_user.dict())
    return new_user

# Restaurant endpoints
@api_router.get("/restaurants", response_model=List[Restaurant])
async def get_restaurants(cuisine: Optional[str] = None, search: Optional[str] = None):
    query = {}
    if cuisine:
        query["cuisine_type"] = {"$regex": cuisine, "$options": "i"}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"cuisine_type": {"$regex": search, "$options": "i"}}
        ]
    
    restaurants = await db.restaurants.find(query).to_list(100)
    return [Restaurant(**restaurant) for restaurant in restaurants]

@api_router.get("/restaurants/{restaurant_id}", response_model=Restaurant)
async def get_restaurant(restaurant_id: str):
    restaurant = await db.restaurants.find_one({"id": restaurant_id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return Restaurant(**restaurant)

# Food items endpoints
@api_router.get("/restaurants/{restaurant_id}/menu", response_model=List[FoodItem])
async def get_restaurant_menu(restaurant_id: str, category: Optional[str] = None):
    query = {"restaurant_id": restaurant_id, "is_available": True}
    if category:
        query["category"] = {"$regex": category, "$options": "i"}
    
    food_items = await db.food_items.find(query).to_list(100)
    return [FoodItem(**item) for item in food_items]

@api_router.get("/food-items/search")
async def search_food_items(q: str):
    query = {
        "$and": [
            {"is_available": True},
            {"$or": [
                {"name": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
                {"category": {"$regex": q, "$options": "i"}}
            ]}
        ]
    }
    
    food_items = await db.food_items.find(query).to_list(50)
    return [FoodItem(**item) for item in food_items]

# Order endpoints
@api_router.post("/orders", response_model=Order)
async def create_order(order_data: OrderCreate):
    # Calculate total amount
    total_amount = 0.0
    for item in order_data.items:
        food_item = await db.food_items.find_one({"id": item.food_item_id})
        if food_item:
            total_amount += food_item["price"] * item.quantity
    
    # Add delivery fee
    restaurant = await db.restaurants.find_one({"id": order_data.restaurant_id})
    if restaurant:
        total_amount += restaurant["delivery_fee"]
    
    new_order = Order(
        **order_data.dict(),
        total_amount=round(total_amount, 2)
    )
    
    await db.orders.insert_one(new_order.dict())
    return new_order

@api_router.get("/orders/{order_id}", response_model=Order)
async def get_order(order_id: str):
    order = await db.orders.find_one({"id": order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return Order(**order)

@api_router.get("/users/{user_id}/orders", response_model=List[Order])
async def get_user_orders(user_id: str):
    orders = await db.orders.find({"user_id": user_id}).sort("created_at", -1).to_list(100)
    return [Order(**order) for order in orders]

@api_router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    valid_statuses = ["pending", "confirmed", "preparing", "on_way", "delivered", "cancelled"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    result = await db.orders.update_one(
        {"id": order_id},
        {"$set": {"status": status}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order status updated successfully"}

# Payment endpoints
@api_router.post("/payments/checkout")
async def create_checkout_session(checkout_data: CheckoutRequest):
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
    
    # Get order details
    order = await db.orders.find_one({"id": checkout_data.order_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    try:
        # Initialize Stripe checkout
        host_url = checkout_data.origin_url
        webhook_url = f"{host_url}/api/webhook/stripe"
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url=webhook_url)
        
        # Create success and cancel URLs
        success_url = f"{host_url}/order-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{host_url}/checkout"
        
        # Create checkout session
        checkout_request = CheckoutSessionRequest(
            amount=order["total_amount"],
            currency="usd",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "order_id": checkout_data.order_id,
                "user_id": order.get("user_id", ""),
                "source": "zyppy_food_delivery"
            }
        )
        
        session = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        payment_transaction = PaymentTransaction(
            session_id=session.session_id,
            order_id=checkout_data.order_id,
            user_id=order.get("user_id"),
            amount=order["total_amount"],
            currency="usd",
            payment_status="pending",
            status="initiated",
            metadata=checkout_request.metadata
        )
        
        await db.payment_transactions.insert_one(payment_transaction.dict())
        
        # Update order with payment session ID
        await db.orders.update_one(
            {"id": checkout_data.order_id},
            {"$set": {"payment_session_id": session.session_id}}
        )
        
        return {"url": session.url, "session_id": session.session_id}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create checkout session: {str(e)}")

@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str):
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
    
    try:
        # Initialize Stripe checkout
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        
        # Get checkout status from Stripe
        checkout_status = await stripe_checkout.get_checkout_status(session_id)
        
        # Update payment transaction in database
        payment_transaction = await db.payment_transactions.find_one({"session_id": session_id})
        if payment_transaction:
            await db.payment_transactions.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "payment_status": checkout_status.payment_status,
                        "status": checkout_status.status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Update order status if payment is successful
            if checkout_status.payment_status == "paid" and payment_transaction["payment_status"] != "paid":
                await db.orders.update_one(
                    {"id": payment_transaction["order_id"]},
                    {"$set": {"status": "confirmed"}}
                )
        
        return {
            "status": checkout_status.status,
            "payment_status": checkout_status.payment_status,
            "amount_total": checkout_status.amount_total,
            "currency": checkout_status.currency
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get payment status: {str(e)}")

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    if not stripe_api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
    
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        stripe_checkout = StripeCheckout(api_key=stripe_api_key, webhook_url="")
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Update payment transaction based on webhook
        if webhook_response.session_id:
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {
                    "$set": {
                        "payment_status": webhook_response.payment_status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Update order status if payment is successful
            if webhook_response.payment_status == "paid":
                payment_transaction = await db.payment_transactions.find_one({"session_id": webhook_response.session_id})
                if payment_transaction:
                    await db.orders.update_one(
                        {"id": payment_transaction["order_id"]},
                        {"$set": {"status": "confirmed"}}
                    )
        
        return {"received": True}
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook error: {str(e)}")

# Reviews endpoints
@api_router.post("/reviews", response_model=Review)
async def create_review(review_data: ReviewCreate):
    # Check if user already reviewed this order
    existing_review = await db.reviews.find_one({
        "user_id": review_data.user_id,
        "order_id": review_data.order_id
    })
    
    if existing_review:
        raise HTTPException(status_code=400, detail="Review already exists for this order")
    
    new_review = Review(**review_data.dict())
    await db.reviews.insert_one(new_review.dict())
    return new_review

@api_router.get("/restaurants/{restaurant_id}/reviews", response_model=List[Review])
async def get_restaurant_reviews(restaurant_id: str):
    reviews = await db.reviews.find({"restaurant_id": restaurant_id}).sort("created_at", -1).to_list(100)
    return [Review(**review) for review in reviews]

# Root endpoint
@api_router.get("/")
async def root():
    return {"message": "Zyppy Food Delivery API", "status": "running"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    await init_sample_data()
    logger.info("Zyppy Food Delivery API started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()