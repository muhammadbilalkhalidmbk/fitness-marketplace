from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from sqlalchemy import text

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='customer')  # admin, trainer, seller, customer
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    trainer_profile = db.relationship('Trainer', backref='user', uselist=False)
    seller_profile = db.relationship('Seller', backref='user', uselist=False)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)
    bookings = db.relationship('Booking', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_active_subscription(self):
        return any(sub.is_active() for sub in self.subscriptions)

class Gym(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    image_filename = db.Column(db.String(100))
    facilities = db.Column(db.Text)  # JSON string of facilities
    opening_hours = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    trainers = db.relationship('Trainer', backref='gym', lazy=True)

class Trainer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    gym_id = db.Column(db.Integer, db.ForeignKey('gym.id'), nullable=False)
    specialization = db.Column(db.String(100))
    experience_years = db.Column(db.Integer)
    bio = db.Column(db.Text)
    hourly_rate = db.Column(db.Float)
    availability = db.Column(db.String(50))  # online, in-person, both
    image_filename = db.Column(db.String(100))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bookings = db.relationship('Booking', backref='trainer', lazy=True)

class Seller(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    business_name = db.Column(db.String(100))
    business_address = db.Column(db.String(200))
    business_phone = db.Column(db.String(20))
    is_approved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    products = db.relationship('Product', backref='seller', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))  # supplement, accessory
    image_filename = db.Column(db.String(100))
    stock_quantity = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order_items = db.relationship('OrderItem', backref='product', lazy=True)

class SubscriptionPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    duration_months = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    
    # Relationships
    subscriptions = db.relationship('Subscription', backref='plan', lazy=True)

class Subscription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plan.id'), nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime)
    is_paid = db.Column(db.Boolean, default=False)
    payment_method = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    receipt_filename = db.Column(db.String(100))
    
    def is_active(self):
        return self.is_paid and self.end_date > datetime.utcnow()

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, shipped, delivered, cancelled
    shipping_address = db.Column(db.Text)
    payment_method = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy=True, cascade='all, delete-orphan')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    trainer_id = db.Column(db.Integer, db.ForeignKey('trainer.id'), nullable=False)
    session_date = db.Column(db.DateTime, nullable=False)
    duration_hours = db.Column(db.Integer, default=1)
    total_cost = db.Column(db.Float)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, completed, cancelled
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Coupon(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    discount_percentage = db.Column(db.Float, nullable=False)
    min_order_amount = db.Column(db.Float, default=0)
    max_discount_amount = db.Column(db.Float)
    usage_limit = db.Column(db.Integer)
    used_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    valid_from = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def is_valid(self, order_amount=0):
        now = datetime.utcnow()
        if not self.is_active:
            return False, "Coupon is not active"
        if self.valid_from and now < self.valid_from:
            return False, "Coupon is not yet valid"
        if self.valid_until and now > self.valid_until:
            return False, "Coupon has expired"
        if self.usage_limit and self.used_count >= self.usage_limit:
            return False, "Coupon usage limit reached"
        if order_amount < self.min_order_amount:
            return False, f"Minimum order amount is PKR {self.min_order_amount}"
        return True, "Valid"
    
    def calculate_discount(self, order_amount):
        discount = (order_amount * self.discount_percentage) / 100
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        return discount

def seed_data():
    """Seed the database with initial data"""
    
    # Check if data already exists
    if User.query.filter_by(username='admin').first():
        return
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@fithub.com',
        role='admin',
        full_name='System Administrator'
    )
    admin.set_password('admin123')
    db.session.add(admin)
    
    # Create gyms
    gyms_data = [
        {
            'name': 'PowerFit Gym',
            'description': 'Modern fitness facility with state-of-the-art equipment',
            'address': 'Main Street, Lahore',
            'phone': '+92-42-1234567',
            'email': 'info@powerfit.com',
            'facilities': 'Cardio, Weight Training, Group Classes',
            'opening_hours': '6:00 AM - 11:00 PM'
        },
        {
            'name': 'Elite Fitness Center',
            'description': 'Premium fitness center with personal training services',
            'address': 'Mall Road, Karachi',
            'phone': '+92-21-9876543',
            'email': 'contact@elitefitness.com',
            'facilities': 'Swimming Pool, Sauna, Yoga Studio',
            'opening_hours': '5:00 AM - 12:00 AM'
        },
        {
            'name': 'Flex Gym & Spa',
            'description': 'Complete wellness center with gym and spa services',
            'address': 'Blue Area, Islamabad',
            'phone': '+92-51-5555555',
            'email': 'hello@flexgym.com',
            'facilities': 'Spa, Massage, CrossFit Area',
            'opening_hours': '24/7'
        }
    ]
    
    for gym_data in gyms_data:
        gym = Gym(**gym_data)
        db.session.add(gym)
    
    db.session.commit()
    
    # Create trainers
    trainers_data = [
        {
            'username': 'ahmad_trainer',
            'email': 'ahmad@fithub.com',
            'full_name': 'Ahmad Khan',
            'phone': '+92-300-1234567',
            'specialization': 'Weight Training & Bodybuilding',
            'experience_years': 5,
            'bio': 'Certified personal trainer with expertise in strength training and muscle building.',
            'hourly_rate': 2000.0,
            'availability': 'both',
            'gym_id': 1
        },
        {
            'username': 'sara_trainer',
            'email': 'sara@fithub.com',
            'full_name': 'Sara Ahmed',
            'phone': '+92-301-9876543',
            'specialization': 'Yoga & Pilates',
            'experience_years': 3,
            'bio': 'Experienced yoga instructor specializing in Hatha and Vinyasa yoga.',
            'hourly_rate': 1500.0,
            'availability': 'online',
            'gym_id': 2
        },
        {
            'username': 'hassan_trainer',
            'email': 'hassan@fithub.com',
            'full_name': 'Hassan Ali',
            'phone': '+92-302-5555555',
            'specialization': 'CrossFit & HIIT',
            'experience_years': 4,
            'bio': 'High-intensity interval training specialist and CrossFit coach.',
            'hourly_rate': 2500.0,
            'availability': 'in-person',
            'gym_id': 3
        },
        {
            'username': 'fatima_trainer',
            'email': 'fatima@fithub.com',
            'full_name': 'Fatima Sheikh',
            'phone': '+92-303-7777777',
            'specialization': 'Cardio & Weight Loss',
            'experience_years': 6,
            'bio': 'Certified fitness trainer focused on cardiovascular health and weight management.',
            'hourly_rate': 1800.0,
            'availability': 'both',
            'gym_id': 1
        },
        {
            'username': 'ali_trainer',
            'email': 'ali@fithub.com',
            'full_name': 'Ali Raza',
            'phone': '+92-304-8888888',
            'specialization': 'Martial Arts & Self Defense',
            'experience_years': 8,
            'bio': 'Mixed martial arts instructor with black belt in multiple disciplines.',
            'hourly_rate': 3000.0,
            'availability': 'in-person',
            'gym_id': 2
        }
    ]
    
    for trainer_data in trainers_data:
        # Create user for trainer
        user = User(
            username=trainer_data['username'],
            email=trainer_data['email'],
            role='trainer',
            full_name=trainer_data['full_name'],
            phone=trainer_data['phone']
        )
        user.set_password('trainer123')
        db.session.add(user)
        db.session.commit()
        
        # Create trainer profile
        trainer = Trainer(
            user_id=user.id,
            gym_id=trainer_data['gym_id'],
            specialization=trainer_data['specialization'],
            experience_years=trainer_data['experience_years'],
            bio=trainer_data['bio'],
            hourly_rate=trainer_data['hourly_rate'],
            availability=trainer_data['availability'],
            is_approved=True
        )
        db.session.add(trainer)
    
    # Create a seller
    seller_user = User(
        username='fitstore_seller',
        email='seller@fitstore.com',
        role='seller',
        full_name='Fit Store Owner',
        phone='+92-300-9999999'
    )
    seller_user.set_password('seller123')
    db.session.add(seller_user)
    db.session.commit()
    
    seller = Seller(
        user_id=seller_user.id,
        business_name='Fit Store',
        business_address='Commercial Area, Lahore',
        business_phone='+92-300-9999999',
        is_approved=True
    )
    db.session.add(seller)
    db.session.commit()
    
    # Create products
    products_data = [
        {
            'name': 'Whey Protein Powder',
            'description': 'Premium whey protein for muscle building and recovery',
            'price': 8500.0,
            'category': 'supplement',
            'stock_quantity': 50
        },
        {
            'name': 'Pre-Workout Booster',
            'description': 'Energy boost supplement for intense workouts',
            'price': 4500.0,
            'category': 'supplement',
            'stock_quantity': 30
        },
        {
            'name': 'Adjustable Dumbbells',
            'description': 'Space-saving adjustable dumbbells for home workouts',
            'price': 15000.0,
            'category': 'accessory',
            'stock_quantity': 20
        },
        {
            'name': 'Yoga Mat Premium',
            'description': 'Non-slip premium yoga mat for all types of exercises',
            'price': 3500.0,
            'category': 'accessory',
            'stock_quantity': 100
        }
    ]
    
    for product_data in products_data:
        product = Product(
            seller_id=seller.id,
            **product_data
        )
        db.session.add(product)
    
    # Create subscription plans
    plans_data = [
        {
            'name': 'Monthly Plan',
            'duration_months': 1,
            'price': 5000.0,
            'description': 'Access to all gyms for 1 month'
        },
        {
            'name': '6-Month Plan',
            'duration_months': 6,
            'price': 25000.0,
            'description': 'Access to all gyms for 6 months - Save 17%'
        },
        {
            'name': 'Yearly Plan',
            'duration_months': 12,
            'price': 45000.0,
            'description': 'Access to all gyms for 1 year - Save 25%'
        }
    ]
    
    for plan_data in plans_data:
        plan = SubscriptionPlan(**plan_data)
        db.session.add(plan)
    
    # Create sample coupons
    from datetime import datetime, timedelta
    coupons_data = [
        {
            'code': 'WELCOME10',
            'discount_percentage': 10.0,
            'min_order_amount': 1000.0,
            'max_discount_amount': 500.0,
            'usage_limit': 100,
            'valid_until': datetime.utcnow() + timedelta(days=30),
            'is_active': True
        },
        {
            'code': 'SAVE20',
            'discount_percentage': 20.0,
            'min_order_amount': 2000.0,
            'max_discount_amount': 1000.0,
            'usage_limit': 50,
            'valid_until': datetime.utcnow() + timedelta(days=15),
            'is_active': True
        },
        {
            'code': 'FITCLUB25',
            'discount_percentage': 25.0,
            'min_order_amount': 3000.0,
            'max_discount_amount': 1500.0,
            'usage_limit': 25,
            'valid_until': datetime.utcnow() + timedelta(days=60),
            'is_active': True
        }
    ]
    
    for coupon_data in coupons_data:
        if not Coupon.query.filter_by(code=coupon_data['code']).first():
            coupon = Coupon(**coupon_data)
            db.session.add(coupon)
    
    db.session.commit()
    print("Seed data created successfully!")
