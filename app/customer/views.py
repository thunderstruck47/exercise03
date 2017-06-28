from flask import flash, redirect, render_template, url_for
from flask_login import login_required, login_user, logout_user, current_user

from . import customer
from .forms import LoginForm, RegistrationForm, AccountForm

from .. import db
from ..models import User, Order

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
                    first_name=form.first_name.data,
                    last_name=form.last_name.data,
                    password=form.password.data,
                    user_role='customer',
                    is_registered=True,
                    created_at=datetime.utcnow())
        
        # add user to the database
        db.session.add(user)
        db.session.commit()
        flash('You have successfully registered! You may now login.')

        # redirect to the login page
        return redirect(url_for('customer.login'))

    # load registration template
    return render_template('customer/register.html', form=form, title='Register')

@customer.route('/account', methods=['GET','POST'])
@login_required
def account():
    """
    Handles requests to the customer account page
    """
    form = AccountForm()
    if form.validate_on_submit():
        user = User.query.filter_by(id=current_user.id).first()
        if not custommer:
            # Unexpected error
            pass 
        user.email = form.email.data
        try:
            db.session.merge(user)
            db.session.commit()
            flash('You have succesfully updated your details.')
        except:
            raise
            flash('There was a problem with our database. Please, try again later.')
    
    form.email.data = current_user.email
    form.first_name.data = current_user.first_name
    form.last_name.data = current_user.last_name
    
    return render_template('customer/account.html', form=form, title='Account')

@customer.route('/orders')
@login_required
def orders():
    """
    List all departments
    """

    orders = Order.query.all()

    return render_template('customer/orders.html', orders=orders, title="Orders")


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
            return redirect(url_for('shop.index')) 
        # when login details are incorrect
        else:
            flash('Invalid email or password.')
    # load login template
    return render_template('customer/login.html', form=form, titile='Login')

@customer.route('/logout')
@login_required
def logout():
    """Handle request to the /logout route
    Log a user out thorugh the logout link
    """
    logout_user()
    flash('You have successfully been logged out.')

    # redirect to the login page
    return redirect(url_for('customer.login'))