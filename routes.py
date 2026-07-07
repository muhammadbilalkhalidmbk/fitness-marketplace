import os
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, flash, request, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import *
from forms import *
from flask_wtf.csrf import generate_csrf

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

def save_uploaded_file(file):
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

@app.route('/')
def index():
    gyms = Gym.query.filter_by(is_active=True).all()
    trainers = Trainer.query.filter_by(is_approved=True).join(User).all()
    products = Product.query.filter_by(is_active=True).limit(8).all()
    return render_template('index.html', gyms=gyms, trainers=trainers, products=products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_active:
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html', form=form)

@app.route('/register')
def register_choice():
    return render_template('register.html')

@app.route('/register/customer', methods=['GET', 'POST'])
def register_customer():
    form = CustomerRegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists')
            return render_template('register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists')
            return render_template('register.html', form=form)
        
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            role='customer'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form, user_type='customer')

@app.route('/register/trainer', methods=['GET', 'POST'])
def register_trainer():
    form = TrainerRegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists')
            return render_template('trainer_register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists')
            return render_template('trainer_register.html', form=form)
        
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            role='trainer'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Find gym by name or assign to first gym
        gym = Gym.query.filter_by(name=form.gym_name.data).first() if form.gym_name.data else Gym.query.first()
        if not gym:
            gym = Gym.query.first()
        
        # Save profile image
        image_filename = None
        if form.profile_image.data:
            image_filename = save_uploaded_file(form.profile_image.data)
        
        # Create trainer profile
        trainer = Trainer(
            user_id=user.id,
            gym_id=gym.id if gym else 1,
            specialization=form.specialization.data,
            experience_years=form.experience_years.data,
            bio=form.bio.data,
            hourly_rate=form.hourly_rate.data,
            availability=form.availability.data,
            image_filename=image_filename,
            is_approved=False  # Needs admin approval
        )
        db.session.add(trainer)
        db.session.commit()
        
        flash('Trainer registration successful! Please wait for admin approval.')
        return redirect(url_for('login'))
    return render_template('trainer_register.html', form=form)

@app.route('/register/seller', methods=['GET', 'POST'])
def register_seller():
    form = SellerRegistrationForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists')
            return render_template('seller_register.html', form=form)
        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists')
            return render_template('seller_register.html', form=form)
        
        # Create user
        user = User(
            username=form.username.data,
            email=form.email.data,
            full_name=form.full_name.data,
            phone=form.phone.data,
            role='seller'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        # Create seller profile
        seller = Seller(
            user_id=user.id,
            business_name=form.business_name.data,
            business_address=form.business_address.data,
            business_phone=form.business_phone.data,
            is_approved=False  # Needs admin approval
        )
        db.session.add(seller)
        db.session.commit()
        
        flash('Seller registration successful! Please wait for admin approval.')
        return redirect(url_for('login'))
    return render_template('seller_register.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif current_user.role == 'trainer':
        return redirect(url_for('trainer_dashboard'))
    elif current_user.role == 'seller':
        return redirect(url_for('seller_dashboard'))
    else:
        return redirect(url_for('customer_dashboard'))

# Admin routes
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    # Analytics data
    total_users = User.query.count()
    total_gyms = Gym.query.count()
    total_trainers = Trainer.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    active_subscriptions = Subscription.query.filter_by(is_paid=True).count()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_gyms=total_gyms,
                         total_trainers=total_trainers,
                         total_products=total_products,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         active_subscriptions=active_subscriptions)

@app.route('/admin/gyms')
@login_required
def admin_gyms():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    gyms = Gym.query.all()
    return render_template('admin/gyms.html', gyms=gyms)

@app.route('/admin/gym/add', methods=['GET', 'POST'])
@login_required
def admin_add_gym():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    form = GymForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_filename = save_uploaded_file(form.image.data)
        
        gym = Gym(
            name=form.name.data,
            description=form.description.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data,
            facilities=form.facilities.data,
            opening_hours=form.opening_hours.data,
            image_filename=image_filename
        )
        db.session.add(gym)
        db.session.commit()
        flash('Gym added successfully!')
        return redirect(url_for('admin_gyms'))
    
    return render_template('admin/gyms.html', form=form, action='add')

@app.route('/admin/gym/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def admin_edit_gym(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    gym = Gym.query.get_or_404(id)
    form = GymForm(obj=gym)
    
    if form.validate_on_submit():
        gym.name = form.name.data
        gym.description = form.description.data
        gym.address = form.address.data
        gym.phone = form.phone.data
        gym.email = form.email.data
        gym.facilities = form.facilities.data
        gym.opening_hours = form.opening_hours.data
        
        if form.image.data:
            gym.image_filename = save_uploaded_file(form.image.data)
        
        db.session.commit()
        flash('Gym updated successfully!')
        return redirect(url_for('admin_gyms'))
    
    return render_template('admin/gyms.html', form=form, gym=gym, action='edit')

@app.route('/admin/gym/delete/<int:id>')
@login_required
def admin_delete_gym(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    gym = Gym.query.get_or_404(id)
    db.session.delete(gym)
    db.session.commit()
    flash('Gym deleted successfully!')
    return redirect(url_for('admin_gyms'))

@app.route('/admin/trainers')
@login_required
def admin_trainers():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    trainers = Trainer.query.join(User).all()
    return render_template('admin/trainers.html', trainers=trainers)

@app.route('/admin/trainer/approve/<int:id>')
@login_required
def admin_approve_trainer(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    trainer = Trainer.query.get_or_404(id)
    trainer.is_approved = True
    db.session.commit()
    flash('Trainer approved successfully!')
    return redirect(url_for('admin_trainers'))

@app.route('/admin/trainer/delete/<int:id>')
@login_required
def admin_delete_trainer(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    trainer = Trainer.query.get_or_404(id)
    user = trainer.user
    db.session.delete(trainer)
    db.session.delete(user)
    db.session.commit()
    flash('Trainer deleted successfully!')
    return redirect(url_for('admin_trainers'))

@app.route('/admin/sellers')
@login_required
def admin_sellers():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    sellers = Seller.query.join(User).all()
    return render_template('admin/sellers.html', sellers=sellers)

@app.route('/admin/seller/approve/<int:id>')
@login_required
def admin_approve_seller(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    seller = Seller.query.get_or_404(id)
    seller.is_approved = True
    db.session.commit()
    flash('Seller approved successfully!')
    return redirect(url_for('admin_sellers'))

@app.route('/admin/products')
@login_required
def admin_products():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    products = Product.query.join(Seller).join(User).all()
    return render_template('admin/products.html', products=products)

from datetime import datetime

@app.route('/admin/customers')
@login_required
def admin_customers():
    if current_user.role != 'admin':
        flash("Access denied")
        return redirect(url_for('index'))
    
    customers = User.query.filter_by(role='customer').all()
    return render_template("admin/customers.html", customers=customers, now=datetime.utcnow())


@app.route('/admin/coupons')
@login_required
def admin_coupons():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    coupons = Coupon.query.all()
    return render_template('admin/coupons.html', coupons=coupons)

@app.route('/admin/coupon/add', methods=['GET', 'POST'])
@login_required
def admin_add_coupon():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    form = CouponForm()
    if form.validate_on_submit():
        coupon = Coupon(
            code=form.code.data.upper(),
            discount_percentage=form.discount_percentage.data,
            min_order_amount=form.min_order_amount.data or 0,
            max_discount_amount=form.max_discount_amount.data,
            usage_limit=form.usage_limit.data,
            valid_until=form.valid_until.data
        )
        db.session.add(coupon)
        db.session.commit()
        flash('Coupon created successfully!')
        return redirect(url_for('admin_coupons'))
    
    return render_template('admin/coupon_form.html', form=form, action='add')

@app.route('/admin/coupon/delete/<int:id>')
@login_required
def admin_delete_coupon(id):
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('index'))
    
    coupon = Coupon.query.get_or_404(id)
    db.session.delete(coupon)
    db.session.commit()
    flash('Coupon deleted successfully!')
    return redirect(url_for('admin_coupons'))

# Trainer routes
@app.route('/trainer/dashboard')
@login_required
def trainer_dashboard():
    if current_user.role != 'trainer':
        flash('Access denied')
        return redirect(url_for('index'))
    
    trainer = Trainer.query.filter_by(user_id=current_user.id).first()
    if not trainer:
        flash('Trainer profile not found')
        return redirect(url_for('index'))
    
    bookings = Booking.query.filter_by(trainer_id=trainer.id).order_by(Booking.session_date.desc()).all()
    return render_template('trainer/dashboard.html', trainer=trainer, bookings=bookings)

# Seller routes
@app.route('/seller/dashboard')
@login_required
def seller_dashboard():
    if current_user.role != 'seller':
        flash('Access denied')
        return redirect(url_for('index'))
    
    seller = Seller.query.filter_by(user_id=current_user.id).first()
    if not seller:
        flash('Seller profile not found')
        return redirect(url_for('index'))
    
    products = Product.query.filter_by(seller_id=seller.id).all()
    orders = Order.query.join(OrderItem).join(Product).filter(Product.seller_id == seller.id).distinct().all()
    
    return render_template('seller/dashboard.html', seller=seller, products=products, orders=orders)

@app.route('/seller/product/add', methods=['GET', 'POST'])
@login_required
def seller_add_product():
    if current_user.role != 'seller':
        flash('Access denied')
        return redirect(url_for('index'))
    
    seller = Seller.query.filter_by(user_id=current_user.id).first()
    if not seller or not seller.is_approved:
        flash('Seller not approved')
        return redirect(url_for('index'))
    
    form = ProductForm()
    if form.validate_on_submit():
        image_filename = None
        if form.image.data:
            image_filename = save_uploaded_file(form.image.data)
        
        product = Product(
            seller_id=seller.id,
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            category=form.category.data,
            stock_quantity=form.stock_quantity.data,
            image_filename=image_filename
        )
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully!')
        return redirect(url_for('seller_dashboard'))
    
    seller = Seller.query.filter_by(user_id=current_user.id).first()
    return render_template('seller/dashboard.html', form=form, action='add', seller=seller)

@app.route('/seller/order/update/<int:id>/<status>')
@login_required
def seller_update_order(id, status):
    if current_user.role != 'seller':
        flash('Access denied')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(id)
    # Verify this order belongs to seller's products
    seller = Seller.query.filter_by(user_id=current_user.id).first()
    if not any(item.product.seller_id == seller.id for item in order.items):
        flash('Access denied')
        return redirect(url_for('seller_dashboard'))
    
    if status in ['shipped', 'delivered', 'cancelled']:
        order.status = status
        db.session.commit()
        flash(f'Order status updated to {status}!')
    else:
        flash('Invalid status')
    
    return redirect(url_for('seller_dashboard'))

# Customer routes
@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    if current_user.role != 'customer':
        flash('Access denied')
        return redirect(url_for('index'))
    
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).all()
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.session_date.desc()).all()

    # ✅ Active subscription logic
    active_sub = next(
        (sub for sub in subscriptions if sub.is_paid and sub.end_date > datetime.utcnow()),
        None
    )

    # ✅ Upcoming bookings logic
    upcoming_bookings = [
        b for b in bookings if b.session_date > datetime.utcnow()
    ]

    return render_template(
        'customer/dashboard.html',
        subscriptions=subscriptions,
        orders=orders,
        bookings=bookings,
        active_sub=active_sub,
        upcoming_bookings=upcoming_bookings
    )

@app.route('/customer/gyms')
def customer_gyms():
    gyms = Gym.query.filter_by(is_active=True).all()
    return render_template('customer/gyms.html', gyms=gyms)

@app.route('/customer/trainers')
def customer_trainers():
    trainers = Trainer.query.filter_by(is_approved=True).join(User).all()
    csrf_token = generate_csrf()  # 🔐 Generate token
    return render_template('customer/trainers.html', trainers=trainers)

@app.route('/customer/products')
def customer_products():
    products = Product.query.filter_by(is_active=True).all()
    return render_template('customer/products.html', products=products)

@app.route('/customer/subscriptions')
def customer_subscriptions():
    plans = SubscriptionPlan.query.filter_by(is_active=True).all()
    return render_template('customer/subscriptions.html', plans=plans)

@app.route('/customer/subscribe/<int:plan_id>', methods=['GET', 'POST'])
@login_required
def customer_subscribe(plan_id):
    plan = SubscriptionPlan.query.get_or_404(plan_id)

    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        receipt_file = request.files.get('receipt')

        if not payment_method or not receipt_file:
            flash('All fields are required!', 'danger')
            return redirect(request.url)

        # Save the uploaded file
        filename = secure_filename(receipt_file.filename)
        receipt_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        receipt_file.save(receipt_path)

        subscription = Subscription(
            user_id=current_user.id,
            plan_id=plan.id,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=30 * plan.duration_months),
            is_paid=False,  # Admin will verify
            payment_method=payment_method,
            receipt_filename=filename
        )
        db.session.add(subscription)
        db.session.commit()

        flash('Subscription request submitted. Admin will verify your payment.', 'info')
        return redirect(url_for('customer_dashboard'))

    return render_template('customer/subscribe_confirm.html', plan=plan)



@app.route('/customer/book_trainer/<int:trainer_id>', methods=['GET', 'POST'])
@login_required
def customer_book_trainer(trainer_id):
    if current_user.role != 'customer':
        flash('Access denied')
        return redirect(url_for('index'))

    if not current_user.has_active_subscription():
        flash('You need an active subscription to book trainers.')
        return redirect(url_for('customer_subscriptions'))

    trainer = Trainer.query.get_or_404(trainer_id)
    form = BookingForm(request.form)

    if request.method == 'POST' and form.validate():
        try:
            session_date = datetime.strptime(request.form['session_date'], '%Y-%m-%d %H:%M')

        except ValueError:
            flash('Invalid session date. Please check your input.')
            return redirect(url_for('customer_trainers'))

        total_cost = trainer.hourly_rate * int(form.duration_hours.data)

        booking = Booking(
            user_id=current_user.id,
            trainer_id=trainer.id,
            session_date=session_date,
            duration_hours=int(form.duration_hours.data),
            total_cost=total_cost,
            notes=form.notes.data,
            status='confirmed'
        )
        db.session.add(booking)
        db.session.commit()

        flash(f'Session booked with {trainer.user.full_name}. Total: PKR {total_cost:,.2f}')
        return redirect(url_for('customer_dashboard'))

    return redirect(url_for('customer_trainers'))

# Shopping cart functionality
@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    if current_user.role != 'customer':
        flash('Access denied')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    # Initialize cart in session if not exists
    if 'cart' not in session:
        session['cart'] = {}
    
    # Add product to cart
    cart = session['cart']
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    
    session['cart'] = cart
    flash(f'{product.name} added to cart!')
    return redirect(url_for('customer_products'))

@app.route('/customer/cart')
@login_required
def customer_cart():
    if current_user.role != 'customer':
        flash('Access denied')
        return redirect(url_for('index'))
    
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            subtotal = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal
    
    return render_template('customer/cart.html', cart_items=cart_items, total=total)

@app.route('/customer/checkout', methods=['GET', 'POST'])
@login_required
def customer_checkout():
    if current_user.role != 'customer':
        flash('Access denied')
        return redirect(url_for('index'))
    
    cart = session.get('cart', {})
    if not cart:
        flash('Your cart is empty!')
        return redirect(url_for('customer_products'))
    
    # Calculate cart items and subtotal
    cart_items = []
    subtotal = 0
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            item_subtotal = product.price * quantity
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': item_subtotal
            })
            subtotal += item_subtotal
    
    form = CheckoutForm()
    discount = 0
    coupon = None
    total = subtotal
    
    if form.validate_on_submit():
        # Check coupon if provided
        if form.coupon_code.data:
            coupon = Coupon.query.filter_by(code=form.coupon_code.data.upper()).first()
            if coupon:
                is_valid, message = coupon.is_valid(subtotal)
                if is_valid:
                    discount = coupon.calculate_discount(subtotal)
                    total = subtotal - discount
                else:
                    flash(f'Coupon error: {message}')
                    return render_template('customer/checkout.html', form=form, cart_items=cart_items, 
                                         subtotal=subtotal, discount=discount, total=total)
            else:
                flash('Invalid coupon code')
                return render_template('customer/checkout.html', form=form, cart_items=cart_items, 
                                     subtotal=subtotal, discount=discount, total=total)
        
        # Create order
        order = Order(
            user_id=current_user.id,
            total_amount=total,
            shipping_address=form.shipping_address.data,
            payment_method=form.payment_method.data,
            status='pending'
        )
        db.session.add(order)
        db.session.commit()
        
        # Create order items
        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
            if product:
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price
                )
                db.session.add(order_item)
                
                # Update stock
                product.stock_quantity -= quantity
        
        # Update coupon usage if applied
        if coupon and discount > 0:
            coupon.used_count += 1
        
        db.session.commit()
        
        # Clear cart
        session['cart'] = {}
        flash(f'Order placed successfully! Total: PKR {total:.2f}')
        return redirect(url_for('customer_dashboard'))
    
    return render_template('customer/checkout.html', form=form, cart_items=cart_items, 
                         subtotal=subtotal, discount=discount, total=total)

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    if current_user.role != 'customer':
        flash('Access denied')
        return redirect(url_for('index'))
    
    cart = session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        session['cart'] = cart
        flash('Item removed from cart!')
    
    return redirect(url_for('customer_cart'))

# Template filter for currency formatting
@app.template_filter('currency')
def currency_filter(amount):
    return f"PKR {amount:,.2f}"
@app.route('/admin/subscriptions')
@login_required
def admin_subscriptions():
    if current_user.role != 'admin':
        abort(403)

    all_subs = Subscription.query.order_by(Subscription.created_at.desc()).all()
    return render_template('admin/subscriptions.html', subscriptions=all_subs)


