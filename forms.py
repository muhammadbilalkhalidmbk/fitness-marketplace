from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, PasswordField, BooleanField, SubmitField, SelectField, IntegerField, FloatField, DateTimeField
from wtforms.validators import DataRequired, Length, Email, NumberRange, Optional
from datetime import datetime

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class CustomerRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Register')

class TrainerRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    specialization = StringField('Specialization', validators=[DataRequired()])
    experience_years = IntegerField('Years of Experience', validators=[DataRequired(), NumberRange(min=0, max=50)])
    bio = TextAreaField('Bio', validators=[DataRequired(), Length(min=50, max=500)])
    hourly_rate = FloatField('Hourly Rate (PKR)', validators=[DataRequired(), NumberRange(min=500, max=10000)])
    availability = SelectField('Availability', choices=[
        ('online', 'Online Only'),
        ('in-person', 'In-Person Only'),
        ('both', 'Both Online & In-Person')
    ], validators=[DataRequired()])
    gym_name = StringField('Gym Name (if attached to specific gym)', validators=[Optional()])
    profile_image = FileField('Profile Picture', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Register as Trainer')

class SellerRegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    full_name = StringField('Full Name', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    business_name = StringField('Business Name', validators=[DataRequired()])
    business_address = TextAreaField('Business Address', validators=[DataRequired()])
    business_phone = StringField('Business Phone', validators=[DataRequired()])
    submit = SubmitField('Register as Seller')

class GymForm(FlaskForm):
    name = StringField('Gym Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    address = TextAreaField('Address', validators=[DataRequired()])
    phone = StringField('Phone Number', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    facilities = TextAreaField('Facilities')
    opening_hours = StringField('Opening Hours', validators=[DataRequired()])
    image = FileField('Gym Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Gym')

class ProductForm(FlaskForm):
    name = StringField('Product Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    price = FloatField('Price (PKR)', validators=[DataRequired(), NumberRange(min=0)])
    category = SelectField('Category', choices=[
        ('supplement', 'Supplement'),
        ('accessory', 'Accessory')
    ], validators=[DataRequired()])
    stock_quantity = IntegerField('Stock Quantity', validators=[DataRequired(), NumberRange(min=0)])
    image = FileField('Product Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'Images only!')])
    submit = SubmitField('Save Product')

class CheckoutForm(FlaskForm):
    shipping_address = TextAreaField('Shipping Address', validators=[DataRequired()])
    payment_method = SelectField('Payment Method', choices=[
        ('cod', 'Cash on Delivery')
    ], validators=[Optional()], default='cod')
    coupon_code = StringField('Coupon Code', validators=[Optional()])
    submit = SubmitField('Place Order')

class BookingForm(FlaskForm):
    session_date = StringField('Session Date & Time', validators=[DataRequired()])
    duration_hours = IntegerField('Duration (Hours)', validators=[DataRequired(), NumberRange(min=1, max=8)])
    notes = TextAreaField('Special Notes')
    submit = SubmitField('Book Session')

class CouponForm(FlaskForm):
    code = StringField('Coupon Code', validators=[DataRequired(), Length(min=3, max=50)])
    discount_percentage = FloatField('Discount Percentage', validators=[DataRequired(), NumberRange(min=1, max=100)])
    min_order_amount = FloatField('Minimum Order Amount (PKR)', validators=[Optional(), NumberRange(min=0)])
    max_discount_amount = FloatField('Maximum Discount Amount (PKR)', validators=[Optional(), NumberRange(min=0)])
    usage_limit = IntegerField('Usage Limit', validators=[Optional(), NumberRange(min=1)])
    valid_until = DateTimeField('Valid Until', validators=[Optional()], format='%Y-%m-%d %H:%M:%S')
    submit = SubmitField('Create Coupon')