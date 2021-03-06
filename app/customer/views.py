from flask import flash, redirect, render_template, url_for, session
from flask_login import login_required, login_user, logout_user, current_user
from paypalrestsdk import Payment
from paypalrestsdk.exceptions import ServerError, ResourceNotFound
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash


from ..helpers import redirect_url
from . import customer
from ..admin.orders.forms import StatusForm
from .forms import LoginForm, RegistrationForm, AccountForm

from .. import db
from ..models import User, Order, OrderStatus, Activity

from datetime import datetime

@customer.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handle requests to the /register route
    Add a registered customer to the database through the registration form
    """
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    password=form.password.data,
                    user_role='customer',
                    is_registered=True,
                    created_at=datetime.now())
        
        # add user to the database
        db.session.add(user)
        db.session.commit()
        flash('You have successfully registered! You may now login.', 'info')

        # redirect to the login page
        return redirect(url_for('customer.login'))

    # load registration template
    return render_template('customer/register.html', form=form, title='Register')

@customer.route('/register/guest', methods=['GET', 'POST'])
def register_guest():
    """
    Handle requests to the /register_guest route
    registers a guest account after an order has been made
    """

    if session['guest']:
        user = User.query.filter_by(id=session['guest']).first()
        if user:
            user.is_registered=True
            form = RegistrationForm()
            if form.validate_on_submit():
                user.email = form.email.data
                user.username = form.username.data
                user.first_name = form.first_name.data
                user.last_name = form.last_name.data
                user.password = form.password.data
                user.user_role = 'customer'
                user.is_registered=True
                try:
                    db.session.merge(user)
                    db.session.commit()
                except:
                    flash('Sorry, you can\'t register right now. Please contact support', 'warning')
                    return redirect(url_for('shop.index'))
                flash('You have registered successfully. You may now login', 'info')
                return redirect(url_for('customer.login'))
            
            form.username.data = user.username
            return render_template('customer/register.html', form=form, title='Guest Register')
 
    flash('Something went wrong!', 'danger')
    return redirect(url_for('shop.index'))


@customer.route('/account', methods=['GET','POST'])
@login_required
def account():
    """
    Handles requests to the customer account page
    """
    form = AccountForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=current_user.id).first()
        if user is not None and user.verify_password(
                form.password.data):
            user.username = form.username.data
            user.email = form.email.data
            if form.new_password.data:
                user.password=form.new_password.data
            try:
                db.session.merge(user)
                db.session.commit()
                flash('You have succesfully updated your details.', 'info')
            except:
                raise
                flash('There was a problem with our database. Please, try again later.', 'warning')
        else:
            flash('Invalid password', 'warning')
            return redirect(redirect_url())
        if not user:
            flash('Could not find this user', 'danger')
            return redirect(redirect_url())
          
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    
    return render_template('customer/account.html', form=form, title='Account')

@customer.route('/orders')
@login_required
def orders():
    """
    List all orders
    """
    
    orders = Order.query.filter_by(user_id=current_user.id).all()

    return render_template('customer/orders.html', orders=orders, title="Orders")

@customer.route('/orders/detail/<int:id>', defaults={'u_id': None}, methods=['GET', 'POST'])
@customer.route('/orders/detail/<int:id>/<int:u_id>', methods=['GET', 'POST'])
def order_detail(id, u_id):
    """
    List all details for order by id
    """
    if not u_id and current_user.is_authenticated:
        u_id = current_user.id

    order = Order.query.filter_by(id=id, user_id=u_id).first()

    # - guest orders are publically visible
    # - user orders are visible only to them
    if not order \
        or (current_user.is_authenticated and order.user.id != current_user.id\
        and not current_user.user_role == 'admin')\
        or (not current_user.is_authenticated and order.user.is_registered):
        flash('Order not found.', 'warning')
        if current_user.is_authenticated:
            return redirect(url_for('customer.orders'))
        else:
            return redirect(url_for('shop.index'))
    payment = None
    payment_state = None
    shipping_address = None
    try:
        # Retrieve the payment object by calling the
        # `find` method
        # on the Payment class by passing Payment ID
        payment = Payment.find(order.payment_id)
        print("Got Payment Details for Payment[%s]" % (payment.id))
        #items = payment.transactions[0].item_list.items
        print(payment)
    except ResourceNotFound as error:
        # It will through ResourceNotFound exception if the payment not found
        # Hm?
        flash("Payment Not Found", 'danger')
    except ConnectionError as error:
        flash('There was a problem with contacting PayPal. Please try again later', 'warning')
        return redirect(url_for('shop.index'))


    if payment:
        shipping_address = payment.transactions[0].item_list.shipping_address or None
        if shipping_address: shipping_address.phone = payment.payer.payer_info.phone
    
        try:
            payment_state = payment.transactions[0].related_resources[0].sale.state
        except IndexError:
            payment_state = payment.state
    
    form = None
    if current_user.is_authenticated and current_user.user_role == 'admin':
        form = StatusForm()
        if form.validate_on_submit():
            order.status = form.status.data
            order.updated_at = datetime.now()
            try:
                db.session.merge(order)
                activity = Activity(verb='update', object=order)
                db.session.add(activity)
                db.session.commit()
            except:
                flash('You can\'t do this right now.', 'warning')
            
            return render_template('customer/order.html', order=order, payment_state=payment_state,shipping_address=shipping_address, form=form, title="Order Details")

        form.status.data = order.status 

    return render_template('customer/order.html', order=order, payment_state=payment_state, shipping_address=shipping_address, form=form, title="Order Details")

@customer.route('/orders/cancel/<int:id>', methods=['GET', 'POST'])
@login_required
def cancel_order(id):
    """
    Issues a cancel on order
    """
    order = Order.query.filter_by(id=id, user_id=current_user.id).first()
    if not order:
        flash('Order not found.', 'warning')
        return redirect(url_for('shop.index'))
    order.cancelled = True
    order.updated = datetime.now()
    try:
        db.session.merge(order)
        db.session.flush()
        activity = Activity(verb='update', object=order)
        db.session.add(activity)
        db.session.commit()
        flash("Your request was successful.", 'info')
    except:
        flash("You can't do this right now.", 'warning')
    
    return redirect(url_for('shop.index'))


@customer.route('/login', methods=['GET', 'POST'])
def login():
    """Handle requests to the /login route
    Log an employee in through the login form
    """
    form = LoginForm()
    if form.validate_on_submit():
        # check weather user exists in the database and wherther
        # the password entered matches the password in the database
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(
                form.password.data):
            login_user(user)
            if current_user.user_role == 'admin':
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('shop.index')) 
        # when login details are incorrect
        else:
            flash('Invalid email or password.', 'warning')
    # load login template
    return render_template('customer/login.html', form=form, titile='Login')

@customer.route('/logout')
@login_required
def logout():
    """Handle request to the /logout route
    Log a user out thorugh the logout link
    """
    logout_user()
    flash('You have successfully been logged out.', 'info')

    # redirect to the login page
    return redirect(url_for('customer.login'))
