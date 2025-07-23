import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Context for user authentication
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in
    const savedUser = localStorage.getItem('zyppy_user');
    if (savedUser) {
      setUser(JSON.parse(savedUser));
    }
    setLoading(false);
  }, []);

  const login = async (email) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email });
      setUser(response.data);
      localStorage.setItem('zyppy_user', JSON.stringify(response.data));
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  };

  const logout = () => {
    setUser(null);
    localStorage.removeItem('zyppy_user');
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Context for cart management
const CartContext = createContext();

const CartProvider = ({ children }) => {
  const [cart, setCart] = useState([]);
  const [currentRestaurant, setCurrentRestaurant] = useState(null);

  const addToCart = (foodItem, quantity = 1) => {
    // If adding from different restaurant, clear cart
    if (currentRestaurant && currentRestaurant !== foodItem.restaurant_id) {
      setCart([]);
    }
    
    setCurrentRestaurant(foodItem.restaurant_id);
    
    setCart(prevCart => {
      const existingItem = prevCart.find(item => item.food_item_id === foodItem.id);
      if (existingItem) {
        return prevCart.map(item =>
          item.food_item_id === foodItem.id
            ? { ...item, quantity: item.quantity + quantity }
            : item
        );
      } else {
        return [...prevCart, {
          food_item_id: foodItem.id,
          quantity,
          name: foodItem.name,
          price: foodItem.price,
          restaurant_id: foodItem.restaurant_id
        }];
      }
    });
  };

  const removeFromCart = (foodItemId) => {
    setCart(prevCart => prevCart.filter(item => item.food_item_id !== foodItemId));
  };

  const updateQuantity = (foodItemId, quantity) => {
    if (quantity <= 0) {
      removeFromCart(foodItemId);
      return;
    }
    
    setCart(prevCart =>
      prevCart.map(item =>
        item.food_item_id === foodItemId
          ? { ...item, quantity }
          : item
      )
    );
  };

  const clearCart = () => {
    setCart([]);
    setCurrentRestaurant(null);
  };

  const getCartTotal = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0);
  };

  return (
    <CartContext.Provider value={{
      cart,
      addToCart,
      removeFromCart,
      updateQuantity,
      clearCart,
      getCartTotal,
      currentRestaurant
    }}>
      {children}
    </CartContext.Provider>
  );
};

// Hook to use auth context
const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// Hook to use cart context
const useCart = () => {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCart must be used within CartProvider');
  }
  return context;
};

// Login Component
const Login = ({ onLogin }) => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;
    
    setLoading(true);
    try {
      await login(email);
      onLogin();
    } catch (error) {
      alert('Login failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-400 to-red-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">Zyppy</h1>
          <p className="text-gray-600">Food delivered fast & fresh</p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Email Address
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent outline-none"
              placeholder="Enter your email"
              required
            />
          </div>
          
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-orange-500 text-white py-3 rounded-lg font-semibold hover:bg-orange-600 transition-colors disabled:opacity-50"
          >
            {loading ? 'Logging in...' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  );
};

// Home Component
const Home = () => {
  const [restaurants, setRestaurants] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCuisine, setSelectedCuisine] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRestaurants();
  }, [searchTerm, selectedCuisine]);

  const fetchRestaurants = async () => {
    try {
      const params = new URLSearchParams();
      if (searchTerm) params.append('search', searchTerm);
      if (selectedCuisine) params.append('cuisine', selectedCuisine);
      
      const response = await axios.get(`${API}/restaurants?${params}`);
      setRestaurants(response.data);
    } catch (error) {
      console.error('Error fetching restaurants:', error);
    } finally {
      setLoading(false);
    }
  };

  const cuisines = ['Italian', 'Indian', 'Seafood', 'Chinese', 'Mexican', 'Thai'];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero Section */}
      <div className="relative h-96 bg-gradient-to-r from-orange-500 to-red-600">
        <div className="absolute inset-0 bg-black bg-opacity-40"></div>
        <div className="relative z-10 container mx-auto px-4 h-full flex items-center">
          <div className="text-white max-w-2xl">
            <h1 className="text-5xl font-bold mb-4">Delicious Food Delivered</h1>
            <p className="text-xl mb-8">Order from your favorite restaurants and get it delivered fast</p>
            
            {/* Search Bar */}
            <div className="flex space-x-4">
              <input
                type="text"
                placeholder="Search restaurants or cuisines..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="flex-1 px-6 py-3 rounded-lg text-gray-800 focus:outline-none focus:ring-2 focus:ring-orange-300"
              />
              <select
                value={selectedCuisine}
                onChange={(e) => setSelectedCuisine(e.target.value)}
                className="px-6 py-3 rounded-lg text-gray-800 focus:outline-none focus:ring-2 focus:ring-orange-300"
              >
                <option value="">All Cuisines</option>
                {cuisines.map(cuisine => (
                  <option key={cuisine} value={cuisine}>{cuisine}</option>
                ))}
              </select>
            </div>
          </div>
        </div>
        <img 
          src="https://images.unsplash.com/photo-1679989260436-1038a839f434?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njl8MHwxfHNlYXJjaHwxfHxkZWxpY2lvdXMlMjBtZWFsc3xlbnwwfHx8fDE3NTMyNzI3NTR8MA&ixlib=rb-4.1.0&q=85"
          alt="Delicious Food"
          className="absolute inset-0 w-full h-full object-cover opacity-20"
        />
      </div>

      {/* Restaurants Section */}
      <div className="container mx-auto px-4 py-12">
        <h2 className="text-3xl font-bold text-gray-800 mb-8">
          {searchTerm || selectedCuisine ? 'Search Results' : 'Popular Restaurants'}
        </h2>
        
        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[1, 2, 3, 4, 5, 6].map(i => (
              <div key={i} className="bg-white rounded-xl shadow-lg animate-pulse">
                <div className="h-48 bg-gray-300 rounded-t-xl"></div>
                <div className="p-6">
                  <div className="h-6 bg-gray-300 rounded mb-2"></div>
                  <div className="h-4 bg-gray-300 rounded mb-4"></div>
                  <div className="flex justify-between">
                    <div className="h-4 bg-gray-300 rounded w-20"></div>
                    <div className="h-4 bg-gray-300 rounded w-16"></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {restaurants.map(restaurant => (
              <RestaurantCard key={restaurant.id} restaurant={restaurant} />
            ))}
          </div>
        )}
        
        {!loading && restaurants.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-600 text-lg">No restaurants found. Try a different search.</p>
          </div>
        )}
      </div>
    </div>
  );
};

// Restaurant Card Component
const RestaurantCard = ({ restaurant }) => {
  return (
    <div className="bg-white rounded-xl shadow-lg hover:shadow-xl transition-shadow cursor-pointer group">
      <div className="relative h-48 overflow-hidden rounded-t-xl">
        <img
          src={restaurant.image_url}
          alt={restaurant.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />
        <div className="absolute top-4 right-4 bg-white px-2 py-1 rounded-full text-sm font-semibold text-orange-600">
          ⭐ {restaurant.rating}
        </div>
      </div>
      
      <div className="p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-2">{restaurant.name}</h3>
        <p className="text-gray-600 mb-4">{restaurant.description}</p>
        
        <div className="flex justify-between items-center text-sm text-gray-500">
          <span>{restaurant.cuisine_type}</span>
          <span>{restaurant.delivery_time}</span>
          <span>${restaurant.delivery_fee} delivery</span>
        </div>
        
        <button
          onClick={() => window.location.href = `#restaurant/${restaurant.id}`}
          className="w-full mt-4 bg-orange-500 text-white py-2 rounded-lg font-semibold hover:bg-orange-600 transition-colors"
        >
          View Menu
        </button>
      </div>
    </div>
  );
};

// Restaurant Menu Component
const RestaurantMenu = ({ restaurantId }) => {
  const [restaurant, setRestaurant] = useState(null);
  const [menuItems, setMenuItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('');
  const { addToCart, cart } = useCart();

  useEffect(() => {
    fetchRestaurantData();
  }, [restaurantId]);

  const fetchRestaurantData = async () => {
    try {
      const [restaurantRes, menuRes] = await Promise.all([
        axios.get(`${API}/restaurants/${restaurantId}`),
        axios.get(`${API}/restaurants/${restaurantId}/menu`)
      ]);
      
      setRestaurant(restaurantRes.data);
      setMenuItems(menuRes.data);
    } catch (error) {
      console.error('Error fetching restaurant data:', error);
    } finally {
      setLoading(false);
    }
  };

  const categories = [...new Set(menuItems.map(item => item.category))];
  const filteredItems = selectedCategory 
    ? menuItems.filter(item => item.category === selectedCategory)
    : menuItems;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="container mx-auto">
          <div className="animate-pulse">
            <div className="h-48 bg-gray-300 rounded-xl mb-8"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="bg-white rounded-lg p-4">
                  <div className="h-32 bg-gray-300 rounded mb-4"></div>
                  <div className="h-6 bg-gray-300 rounded mb-2"></div>
                  <div className="h-4 bg-gray-300 rounded"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Restaurant Header */}
      {restaurant && (
        <div className="relative h-64 bg-gradient-to-r from-orange-500 to-red-600">
          <div className="absolute inset-0 bg-black bg-opacity-50"></div>
          <img
            src={restaurant.image_url}
            alt={restaurant.name}
            className="absolute inset-0 w-full h-full object-cover opacity-30"
          />
          <div className="relative z-10 container mx-auto px-4 h-full flex items-center">
            <div className="text-white">
              <button
                onClick={() => window.location.href = '#'}
                className="mb-4 text-white hover:text-orange-200 transition-colors"
              >
                ← Back to Restaurants
              </button>
              <h1 className="text-4xl font-bold mb-2">{restaurant.name}</h1>
              <p className="text-lg mb-4">{restaurant.description}</p>
              <div className="flex space-x-6 text-sm">
                <span>⭐ {restaurant.rating}</span>
                <span>🚗 {restaurant.delivery_time}</span>
                <span>💰 ${restaurant.delivery_fee} delivery</span>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Menu Section */}
          <div className="flex-1">
            {/* Category Filter */}
            <div className="mb-8">
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedCategory('')}
                  className={`px-4 py-2 rounded-full font-medium transition-colors ${
                    selectedCategory === '' 
                      ? 'bg-orange-500 text-white' 
                      : 'bg-white text-gray-700 hover:bg-orange-100'
                  }`}
                >
                  All Items
                </button>
                {categories.map(category => (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={`px-4 py-2 rounded-full font-medium transition-colors ${
                      selectedCategory === category 
                        ? 'bg-orange-500 text-white' 
                        : 'bg-white text-gray-700 hover:bg-orange-100'
                    }`}
                  >
                    {category}
                  </button>
                ))}
              </div>
            </div>

            {/* Menu Items */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {filteredItems.map(item => (
                <MenuItemCard key={item.id} item={item} onAddToCart={addToCart} />
              ))}
            </div>
          </div>

          {/* Cart Sidebar */}
          <div className="w-full lg:w-80">
            <CartSidebar />
          </div>
        </div>
      </div>
    </div>
  );
};

// Menu Item Card Component
const MenuItemCard = ({ item, onAddToCart }) => {
  return (
    <div className="bg-white rounded-lg shadow-md p-4 hover:shadow-lg transition-shadow">
      <div className="flex gap-4">
        <img
          src={item.image_url}
          alt={item.name}
          className="w-24 h-24 object-cover rounded-lg"
        />
        <div className="flex-1">
          <div className="flex items-start justify-between mb-2">
            <h3 className="font-bold text-gray-800">{item.name}</h3>
            {item.is_vegetarian && <span className="text-green-500 text-sm">🌱</span>}
          </div>
          <p className="text-gray-600 text-sm mb-3">{item.description}</p>
          <div className="flex items-center justify-between">
            <span className="text-lg font-bold text-orange-600">${item.price}</span>
            <button
              onClick={() => onAddToCart(item)}
              className="bg-orange-500 text-white px-4 py-2 rounded-lg hover:bg-orange-600 transition-colors"
            >
              Add to Cart
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

// Cart Sidebar Component
const CartSidebar = () => {
  const { cart, updateQuantity, removeFromCart, getCartTotal, clearCart } = useCart();
  const { user } = useAuth();
  const [showCheckout, setShowCheckout] = useState(false);

  if (cart.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
        <h3 className="text-lg font-bold text-gray-800 mb-4">Your Cart</h3>
        <p className="text-gray-500">Your cart is empty</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
      <h3 className="text-lg font-bold text-gray-800 mb-4">Your Cart</h3>
      
      <div className="space-y-4 mb-6">
        {cart.map(item => (
          <div key={item.food_item_id} className="flex items-center gap-3">
            <div className="flex-1">
              <h4 className="font-medium text-gray-800">{item.name}</h4>
              <p className="text-orange-600">${item.price}</p>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => updateQuantity(item.food_item_id, item.quantity - 1)}
                className="w-8 h-8 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center"
              >
                -
              </button>
              <span className="font-medium">{item.quantity}</span>
              <button
                onClick={() => updateQuantity(item.food_item_id, item.quantity + 1)}
                className="w-8 h-8 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center"
              >
                +
              </button>
            </div>
            <button
              onClick={() => removeFromCart(item.food_item_id)}
              className="text-red-500 hover:text-red-700 text-sm"
            >
              Remove
            </button>
          </div>
        ))}
      </div>
      
      <div className="border-t pt-4">
        <div className="flex justify-between items-center mb-4">
          <span className="font-bold text-lg">Total: ${getCartTotal().toFixed(2)}</span>
        </div>
        
        <button
          onClick={() => setShowCheckout(true)}
          className="w-full bg-orange-500 text-white py-3 rounded-lg font-semibold hover:bg-orange-600 transition-colors"
        >
          Proceed to Checkout
        </button>
        
        <button
          onClick={clearCart}
          className="w-full mt-2 text-gray-500 hover:text-gray-700 text-sm"
        >
          Clear Cart
        </button>
      </div>
      
      {showCheckout && (
        <CheckoutModal 
          onClose={() => setShowCheckout(false)}
          cart={cart}
          total={getCartTotal()}
        />
      )}
    </div>
  );
};

// Checkout Modal Component
const CheckoutModal = ({ onClose, cart, total }) => {
  const { user } = useAuth();
  const { currentRestaurant, clearCart } = useCart();
  const [address, setAddress] = useState(user?.address || '');
  const [loading, setLoading] = useState(false);

  const handleCheckout = async () => {
    if (!address.trim()) {
      alert('Please enter a delivery address');
      return;
    }

    setLoading(true);
    try {
      // Create order
      const orderData = {
        user_id: user.id,
        restaurant_id: currentRestaurant,
        items: cart.map(item => ({
          food_item_id: item.food_item_id,
          quantity: item.quantity
        })),
        delivery_address: address
      };

      const orderResponse = await axios.post(`${API}/orders`, orderData);
      const order = orderResponse.data;

      // Create checkout session
      const checkoutData = {
        order_id: order.id,
        origin_url: window.location.origin
      };

      const checkoutResponse = await axios.post(`${API}/payments/checkout`, checkoutData);
      
      // Redirect to Stripe checkout
      window.location.href = checkoutResponse.data.url;
      
    } catch (error) {
      console.error('Checkout error:', error);
      alert('Checkout failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full p-6">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-bold">Checkout</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700">✕</button>
        </div>
        
        <div className="space-y-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Delivery Address
            </label>
            <textarea
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-transparent"
              rows="3"
              placeholder="Enter your full address..."
              required
            />
          </div>
          
          <div className="border-t pt-4">
            <div className="flex justify-between items-center">
              <span className="font-bold text-lg">Total: ${(total + 2.99).toFixed(2)}</span>
              <span className="text-sm text-gray-500">(includes $2.99 delivery)</span>
            </div>
          </div>
        </div>
        
        <div className="flex gap-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-gray-600 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleCheckout}
            disabled={loading}
            className="flex-1 px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50"
          >
            {loading ? 'Processing...' : 'Pay Now'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Order Success Component
const OrderSuccess = () => {
  const [order, setOrder] = useState(null);
  const [paymentStatus, setPaymentStatus] = useState('checking');
  const { user } = useAuth();
  const { clearCart } = useCart();

  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('session_id');
    
    if (sessionId) {
      checkPaymentStatus(sessionId);
      clearCart();
    }
  }, []);

  const checkPaymentStatus = async (sessionId, attempts = 0) => {
    const maxAttempts = 5;
    
    if (attempts >= maxAttempts) {
      setPaymentStatus('timeout');
      return;
    }

    try {
      const response = await axios.get(`${API}/payments/status/${sessionId}`);
      
      if (response.data.payment_status === 'paid') {
        setPaymentStatus('success');
        return;
      } else if (response.data.status === 'expired') {
        setPaymentStatus('failed');
        return;
      }

      // Continue polling
      setTimeout(() => checkPaymentStatus(sessionId, attempts + 1), 2000);
    } catch (error) {
      console.error('Error checking payment status:', error);
      setPaymentStatus('error');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-lg p-8 max-w-md w-full text-center">
        {paymentStatus === 'checking' && (
          <>
            <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-orange-500 mx-auto mb-4"></div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Processing Payment</h2>
            <p className="text-gray-600">Please wait while we confirm your payment...</p>
          </>
        )}
        
        {paymentStatus === 'success' && (
          <>
            <div className="text-green-500 text-6xl mb-4">✓</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Order Confirmed!</h2>
            <p className="text-gray-600 mb-6">Thank you for your order. We'll prepare your food right away!</p>
            <div className="space-y-3">
              <button
                onClick={() => window.location.href = '#orders'}
                className="w-full bg-orange-500 text-white py-3 rounded-lg font-semibold hover:bg-orange-600 transition-colors"
              >
                Track Your Order
              </button>
              <button
                onClick={() => window.location.href = '#'}
                className="w-full text-gray-600 hover:text-gray-800"
              >
                Continue Shopping
              </button>
            </div>
          </>
        )}
        
        {(paymentStatus === 'failed' || paymentStatus === 'error' || paymentStatus === 'timeout') && (
          <>
            <div className="text-red-500 text-6xl mb-4">✗</div>
            <h2 className="text-2xl font-bold text-gray-800 mb-2">Payment Failed</h2>
            <p className="text-gray-600 mb-6">There was an issue processing your payment. Please try again.</p>
            <button
              onClick={() => window.location.href = '#'}
              className="w-full bg-orange-500 text-white py-3 rounded-lg font-semibold hover:bg-orange-600 transition-colors"
            >
              Back to Restaurants
            </button>
          </>
        )}
      </div>
    </div>
  );
};

// My Orders Component
const MyOrders = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();

  useEffect(() => {
    if (user) {
      fetchOrders();
    }
  }, [user]);

  const fetchOrders = async () => {
    try {
      const response = await axios.get(`${API}/users/${user.id}/orders`);
      setOrders(response.data);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      confirmed: 'bg-blue-100 text-blue-800',
      preparing: 'bg-purple-100 text-purple-800',
      on_way: 'bg-orange-100 text-orange-800',
      delivered: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 p-4">
        <div className="container mx-auto">
          <h1 className="text-3xl font-bold text-gray-800 mb-8">My Orders</h1>
          <div className="space-y-4">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-white rounded-lg shadow-md p-6 animate-pulse">
                <div className="h-6 bg-gray-300 rounded mb-4"></div>
                <div className="h-4 bg-gray-300 rounded mb-2"></div>
                <div className="h-4 bg-gray-300 rounded mb-4"></div>
                <div className="h-8 bg-gray-300 rounded"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="container mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold text-gray-800">My Orders</h1>
          <button
            onClick={() => window.location.href = '#'}
            className="text-orange-500 hover:text-orange-600"
          >
            ← Back to Restaurants
          </button>
        </div>
        
        {orders.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <p className="text-gray-600 text-lg mb-4">You haven't placed any orders yet</p>
            <button
              onClick={() => window.location.href = '#'}
              className="bg-orange-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-orange-600 transition-colors"
            >
              Start Ordering
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map(order => (
              <div key={order.id} className="bg-white rounded-lg shadow-md p-6">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-bold text-gray-800">Order #{order.id.slice(-8)}</h3>
                    <p className="text-gray-600">{new Date(order.created_at).toLocaleDateString()}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(order.status)}`}>
                    {order.status.replace('_', ' ').toUpperCase()}
                  </span>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div>
                    <p className="text-sm text-gray-500">Total Amount</p>
                    <p className="font-bold text-lg">${order.total_amount}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Delivery Address</p>
                    <p className="text-gray-800">{order.delivery_address}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Estimated Delivery</p>
                    <p className="text-gray-800">{new Date(order.estimated_delivery).toLocaleTimeString()}</p>
                  </div>
                </div>
                
                <div className="border-t pt-4">
                  <h4 className="font-medium text-gray-800 mb-2">Items Ordered:</h4>
                  <div className="space-y-2">
                    {order.items.map((item, index) => (
                      <div key={index} className="flex justify-between text-sm">
                        <span>Item ID: {item.food_item_id}</span>
                        <span>Qty: {item.quantity}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

// Navigation Component
const Navigation = () => {
  const { user, logout } = useAuth();
  const { cart } = useCart();

  return (
    <nav className="bg-white shadow-md p-4 sticky top-0 z-40">
      <div className="container mx-auto flex items-center justify-between">
        <button
          onClick={() => window.location.href = '#'}
          className="text-2xl font-bold text-orange-500"
        >
          Zyppy
        </button>
        
        <div className="flex items-center space-x-4">
          <button
            onClick={() => window.location.href = '#orders'}
            className="text-gray-600 hover:text-orange-500 transition-colors"
          >
            My Orders
          </button>
          
          <div className="relative">
            <span className="text-gray-600">🛒</span>
            {cart.length > 0 && (
              <span className="absolute -top-2 -right-2 bg-orange-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {cart.reduce((sum, item) => sum + item.quantity, 0)}
              </span>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="text-gray-600">👋 {user?.name}</span>
            <button
              onClick={logout}
              className="text-orange-500 hover:text-orange-600 transition-colors"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
};

// Main App Component
function App() {
  const { user, loading } = useAuth();
  const [currentView, setCurrentView] = useState('home');
  const [restaurantId, setRestaurantId] = useState(null);

  useEffect(() => {
    // Simple routing based on hash
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1);
      if (hash.startsWith('restaurant/')) {
        setRestaurantId(hash.split('/')[1]);
        setCurrentView('restaurant');
      } else if (hash === 'orders') {
        setCurrentView('orders');
      } else if (hash === 'order-success') {
        setCurrentView('order-success');
      } else {
        setCurrentView('home');
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    handleHashChange(); // Initial load

    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={() => setCurrentView('home')} />;
  }

  return (
    <div className="App">
      <Navigation />
      
      {currentView === 'home' && <Home />}
      {currentView === 'restaurant' && <RestaurantMenu restaurantId={restaurantId} />}
      {currentView === 'orders' && <MyOrders />}
      {currentView === 'order-success' && <OrderSuccess />}
    </div>
  );
}

// Wrapped App with Providers
export default function WrappedApp() {
  return (
    <AuthProvider>
      <CartProvider>
        <App />
      </CartProvider>
    </AuthProvider>
  );
}