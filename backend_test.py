#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Zyppy Food Delivery System
Tests all core functionalities including authentication, restaurants, orders, payments, and reviews.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://70c9841d-ded5-4ebe-9fe3-1d9baec2c430.preview.emergentagent.com/api"

class ZyppyBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = {
            "health_check": False,
            "user_auth": False,
            "restaurant_management": False,
            "food_menu": False,
            "order_management": False,
            "payment_integration": False,
            "reviews_system": False
        }
        self.test_data = {}
        
    def log(self, message, level="INFO"):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_health_check(self):
        """Test the root endpoint to ensure server is running"""
        self.log("Testing API Health Check...")
        try:
            response = self.session.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data and "Zyppy" in data["message"]:
                    self.log("✅ Health check passed - API is running")
                    self.test_results["health_check"] = True
                    return True
                else:
                    self.log("❌ Health check failed - Unexpected response format")
            else:
                self.log(f"❌ Health check failed - Status code: {response.status_code}")
        except Exception as e:
            self.log(f"❌ Health check failed - Error: {str(e)}")
        return False
        
    def test_user_authentication(self):
        """Test user registration and login endpoints"""
        self.log("Testing User Authentication System...")
        
        # Test user registration
        try:
            register_data = {
                "email": "sarah.johnson@foodie.com",
                "name": "Sarah Johnson",
                "phone": "+1-555-0123",
                "address": "123 Foodie Street, Culinary City, FC 12345"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code == 200:
                user_data = response.json()
                self.test_data["user_id"] = user_data["id"]
                self.test_data["user_email"] = user_data["email"]
                self.log("✅ User registration successful")
                
                # Test user login
                login_data = {"email": register_data["email"]}
                login_response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
                
                if login_response.status_code == 200:
                    login_user_data = login_response.json()
                    if login_user_data["id"] == user_data["id"]:
                        self.log("✅ User login successful")
                        self.test_results["user_auth"] = True
                        return True
                    else:
                        self.log("❌ Login failed - User ID mismatch")
                else:
                    self.log(f"❌ Login failed - Status code: {login_response.status_code}")
            else:
                self.log(f"❌ Registration failed - Status code: {response.status_code}")
                # Try login with existing user
                login_data = {"email": "sarah.johnson@foodie.com"}
                login_response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
                if login_response.status_code == 200:
                    user_data = login_response.json()
                    self.test_data["user_id"] = user_data["id"]
                    self.test_data["user_email"] = user_data["email"]
                    self.log("✅ User login with existing account successful")
                    self.test_results["user_auth"] = True
                    return True
                    
        except Exception as e:
            self.log(f"❌ Authentication test failed - Error: {str(e)}")
        return False
        
    def test_restaurant_management(self):
        """Test getting restaurants with search and cuisine filters"""
        self.log("Testing Restaurant Management System...")
        
        try:
            # Test getting all restaurants
            response = self.session.get(f"{BACKEND_URL}/restaurants")
            if response.status_code == 200:
                restaurants = response.json()
                if len(restaurants) > 0:
                    self.test_data["restaurant_id"] = restaurants[0]["id"]
                    self.test_data["restaurant_name"] = restaurants[0]["name"]
                    self.log(f"✅ Retrieved {len(restaurants)} restaurants")
                    
                    # Test cuisine filter
                    cuisine_response = self.session.get(f"{BACKEND_URL}/restaurants?cuisine=Italian")
                    if cuisine_response.status_code == 200:
                        italian_restaurants = cuisine_response.json()
                        self.log(f"✅ Cuisine filter working - Found {len(italian_restaurants)} Italian restaurants")
                        
                        # Test search functionality
                        search_response = self.session.get(f"{BACKEND_URL}/restaurants?search=Bella")
                        if search_response.status_code == 200:
                            search_results = search_response.json()
                            self.log(f"✅ Search functionality working - Found {len(search_results)} results")
                            
                            # Test individual restaurant retrieval
                            restaurant_response = self.session.get(f"{BACKEND_URL}/restaurants/{self.test_data['restaurant_id']}")
                            if restaurant_response.status_code == 200:
                                restaurant = restaurant_response.json()
                                self.log(f"✅ Individual restaurant retrieval successful - {restaurant['name']}")
                                self.test_results["restaurant_management"] = True
                                return True
                            else:
                                self.log(f"❌ Individual restaurant retrieval failed - Status: {restaurant_response.status_code}")
                        else:
                            self.log(f"❌ Search failed - Status code: {search_response.status_code}")
                    else:
                        self.log(f"❌ Cuisine filter failed - Status code: {cuisine_response.status_code}")
                else:
                    self.log("❌ No restaurants found")
            else:
                self.log(f"❌ Restaurant retrieval failed - Status code: {response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Restaurant management test failed - Error: {str(e)}")
        return False
        
    def test_food_menu_system(self):
        """Test restaurant menu retrieval and food item search"""
        self.log("Testing Food Menu System...")
        
        if "restaurant_id" not in self.test_data:
            self.log("❌ Cannot test menu - No restaurant ID available")
            return False
            
        try:
            # Test restaurant menu retrieval
            menu_response = self.session.get(f"{BACKEND_URL}/restaurants/{self.test_data['restaurant_id']}/menu")
            if menu_response.status_code == 200:
                menu_items = menu_response.json()
                if len(menu_items) > 0:
                    self.test_data["food_item_id"] = menu_items[0]["id"]
                    self.test_data["food_item_price"] = menu_items[0]["price"]
                    self.log(f"✅ Menu retrieval successful - Found {len(menu_items)} items")
                    
                    # Test category filter
                    category_response = self.session.get(f"{BACKEND_URL}/restaurants/{self.test_data['restaurant_id']}/menu?category=Pizza")
                    if category_response.status_code == 200:
                        category_items = category_response.json()
                        self.log(f"✅ Category filter working - Found {len(category_items)} pizza items")
                        
                        # Test food item search
                        search_response = self.session.get(f"{BACKEND_URL}/food-items/search?q=pizza")
                        if search_response.status_code == 200:
                            search_results = search_response.json()
                            self.log(f"✅ Food search working - Found {len(search_results)} results for 'pizza'")
                            self.test_results["food_menu"] = True
                            return True
                        else:
                            self.log(f"❌ Food search failed - Status code: {search_response.status_code}")
                    else:
                        self.log(f"❌ Category filter failed - Status code: {category_response.status_code}")
                else:
                    self.log("❌ No menu items found")
            else:
                self.log(f"❌ Menu retrieval failed - Status code: {menu_response.status_code}")
                
        except Exception as e:
            self.log(f"❌ Food menu test failed - Error: {str(e)}")
        return False
        
    def test_order_management(self):
        """Test order creation and retrieval"""
        self.log("Testing Order Management System...")
        
        if "user_id" not in self.test_data or "restaurant_id" not in self.test_data or "food_item_id" not in self.test_data:
            self.log("❌ Cannot test orders - Missing required test data")
            return False
            
        try:
            # Test order creation
            order_data = {
                "user_id": self.test_data["user_id"],
                "restaurant_id": self.test_data["restaurant_id"],
                "items": [
                    {
                        "food_item_id": self.test_data["food_item_id"],
                        "quantity": 2,
                        "special_instructions": "Extra cheese please"
                    }
                ],
                "delivery_address": "456 Delivery Lane, Food City, FC 54321"
            }
            
            response = self.session.post(f"{BACKEND_URL}/orders", json=order_data)
            if response.status_code == 200:
                order = response.json()
                self.test_data["order_id"] = order["id"]
                self.test_data["order_total"] = order["total_amount"]
                self.log(f"✅ Order creation successful - Order ID: {order['id']}, Total: ${order['total_amount']}")
                
                # Test individual order retrieval
                order_response = self.session.get(f"{BACKEND_URL}/orders/{order['id']}")
                if order_response.status_code == 200:
                    retrieved_order = order_response.json()
                    self.log("✅ Individual order retrieval successful")
                    
                    # Test user orders retrieval
                    user_orders_response = self.session.get(f"{BACKEND_URL}/users/{self.test_data['user_id']}/orders")
                    if user_orders_response.status_code == 200:
                        user_orders = user_orders_response.json()
                        self.log(f"✅ User orders retrieval successful - Found {len(user_orders)} orders")
                        
                        # Test order status update
                        status_response = self.session.put(f"{BACKEND_URL}/orders/{order['id']}/status?status=confirmed")
                        if status_response.status_code == 200:
                            self.log("✅ Order status update successful")
                            self.test_results["order_management"] = True
                            return True
                        else:
                            self.log(f"❌ Order status update failed - Status: {status_response.status_code}")
                    else:
                        self.log(f"❌ User orders retrieval failed - Status: {user_orders_response.status_code}")
                else:
                    self.log(f"❌ Individual order retrieval failed - Status: {order_response.status_code}")
            else:
                self.log(f"❌ Order creation failed - Status code: {response.status_code}")
                if response.text:
                    self.log(f"Error details: {response.text}")
                    
        except Exception as e:
            self.log(f"❌ Order management test failed - Error: {str(e)}")
        return False
        
    def test_payment_integration(self):
        """Test payment checkout session creation"""
        self.log("Testing Payment Integration (Stripe)...")
        
        if "order_id" not in self.test_data:
            self.log("❌ Cannot test payments - No order ID available")
            return False
            
        try:
            # Test checkout session creation
            checkout_data = {
                "order_id": self.test_data["order_id"],
                "origin_url": "https://70c9841d-ded5-4ebe-9fe3-1d9baec2c430.preview.emergentagent.com"
            }
            
            response = self.session.post(f"{BACKEND_URL}/payments/checkout", json=checkout_data)
            if response.status_code == 200:
                checkout_response = response.json()
                if "url" in checkout_response and "session_id" in checkout_response:
                    session_id = checkout_response["session_id"]
                    self.test_data["payment_session_id"] = session_id
                    self.log(f"✅ Checkout session creation successful - Session ID: {session_id}")
                    
                    # Test payment status retrieval
                    time.sleep(1)  # Brief delay for session to be processed
                    status_response = self.session.get(f"{BACKEND_URL}/payments/status/{session_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        self.log(f"✅ Payment status retrieval successful - Status: {status_data.get('payment_status', 'unknown')}")
                        self.test_results["payment_integration"] = True
                        return True
                    else:
                        self.log(f"❌ Payment status retrieval failed - Status: {status_response.status_code}")
                else:
                    self.log("❌ Checkout response missing required fields")
            else:
                self.log(f"❌ Checkout session creation failed - Status code: {response.status_code}")
                if response.text:
                    self.log(f"Error details: {response.text}")
                    
        except Exception as e:
            self.log(f"❌ Payment integration test failed - Error: {str(e)}")
        return False
        
    def test_reviews_system(self):
        """Test review creation and retrieval"""
        self.log("Testing Reviews and Ratings System...")
        
        if "user_id" not in self.test_data or "restaurant_id" not in self.test_data or "order_id" not in self.test_data:
            self.log("❌ Cannot test reviews - Missing required test data")
            return False
            
        try:
            # Test review creation
            review_data = {
                "user_id": self.test_data["user_id"],
                "restaurant_id": self.test_data["restaurant_id"],
                "order_id": self.test_data["order_id"],
                "rating": 5,
                "comment": "Absolutely delicious! The food was fresh, hot, and delivered quickly. Will definitely order again!"
            }
            
            response = self.session.post(f"{BACKEND_URL}/reviews", json=review_data)
            if response.status_code == 200:
                review = response.json()
                self.test_data["review_id"] = review["id"]
                self.log(f"✅ Review creation successful - Review ID: {review['id']}, Rating: {review['rating']}/5")
                
                # Test restaurant reviews retrieval
                reviews_response = self.session.get(f"{BACKEND_URL}/restaurants/{self.test_data['restaurant_id']}/reviews")
                if reviews_response.status_code == 200:
                    reviews = reviews_response.json()
                    self.log(f"✅ Restaurant reviews retrieval successful - Found {len(reviews)} reviews")
                    
                    # Verify our review is in the list
                    review_found = any(r["id"] == review["id"] for r in reviews)
                    if review_found:
                        self.log("✅ Created review found in restaurant reviews")
                        self.test_results["reviews_system"] = True
                        return True
                    else:
                        self.log("❌ Created review not found in restaurant reviews")
                else:
                    self.log(f"❌ Restaurant reviews retrieval failed - Status: {reviews_response.status_code}")
            else:
                self.log(f"❌ Review creation failed - Status code: {response.status_code}")
                if response.text:
                    self.log(f"Error details: {response.text}")
                    
        except Exception as e:
            self.log(f"❌ Reviews system test failed - Error: {str(e)}")
        return False
        
    def run_all_tests(self):
        """Run all backend tests in sequence"""
        self.log("=" * 60)
        self.log("STARTING ZYPPY BACKEND COMPREHENSIVE TESTING")
        self.log("=" * 60)
        
        # Run tests in logical order
        tests = [
            ("Health Check", self.test_health_check),
            ("User Authentication", self.test_user_authentication),
            ("Restaurant Management", self.test_restaurant_management),
            ("Food Menu System", self.test_food_menu_system),
            ("Order Management", self.test_order_management),
            ("Payment Integration", self.test_payment_integration),
            ("Reviews System", self.test_reviews_system)
        ]
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---")
            test_func()
            time.sleep(0.5)  # Brief pause between tests
            
        # Print final results
        self.print_test_summary()
        
    def print_test_summary(self):
        """Print comprehensive test results summary"""
        self.log("\n" + "=" * 60)
        self.log("ZYPPY BACKEND TEST RESULTS SUMMARY")
        self.log("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result)
        total = len(self.test_results)
        
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result else "❌ FAILED"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
            
        self.log(f"\nOVERALL RESULT: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 ALL TESTS PASSED! Zyppy backend is working correctly.")
        else:
            self.log(f"⚠️  {total - passed} test(s) failed. Please check the logs above for details.")
            
        # Print test data for reference
        if self.test_data:
            self.log("\nTest Data Generated:")
            for key, value in self.test_data.items():
                self.log(f"  {key}: {value}")

if __name__ == "__main__":
    tester = ZyppyBackendTester()
    tester.run_all_tests()