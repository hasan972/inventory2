import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET
import datetime


from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# Create Product Receive Entry
@action("receive/new_receive", method=["GET", "POST"])
@action.uses("receive/new_receive.html", auth, T, db)
def new_receive():
    if not session.get('user_id'):
        redirect(URL('login'))  
    elif session['f_password']==1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
        search_term = request.query.get('search_term', '')
        search_by = request.query.get('search_by', 'receive_code')
        
        if search_term:
            if search_by == 'receive_code':
                query = "SELECT * FROM product_receives WHERE cid = 'TDCLPC' and receive_code LIKE '%{}%'".format(search_term)
            elif search_by == 'item_code':
                query = "SELECT * FROM product_receives WHERE cid = 'TDCLPC' and item_code LIKE '%{}%'".format(search_term)
        else:
            query = "SELECT * FROM product_receives"
        
        print(query)
        rows = db.executesql(query, as_dict=True)

        # db.receive_code.created_by.default = user
    
    # Define form
    form = Form(db.product_receives)

    # Apply custom styles to form fields
    if 'receive_code' in form.custom.widgets:
        form.custom.widgets['receive_code']['_class'] = 'form-control form-control-sm'
    if 'item_code' in form.custom.widgets:
        form.custom.widgets['item_code']['_class'] = 'form-control form-control-sm select-custom'
    if 'supplier_code' in form.custom.widgets:
        form.custom.widgets['supplier_code']['_class'] = 'form-control form-control-sm select-custom'
    if 'unit_name' in form.custom.widgets:
        form.custom.widgets['unit_name']['_class'] = 'form-control form-control-sm select-custom'
    if 'quantity_received' in form.custom.widgets:
        form.custom.widgets['quantity_received']['_class'] = 'form-control form-control-sm'
    if 'receive_date' in form.custom.widgets:
        form.custom.widgets['receive_date']['_class'] = 'form-control form-control-sm'
    if 'remarks' in form.custom.widgets:
        form.custom.widgets['remarks']['_class'] = 'form-control form-control-sm'
    
    # Handle form submission
    if form.accepted:
        flash.set('Product receive entry added successfully', 'success')
        redirect(URL('receive/new_receive'))
        # print()

    return dict(form=form, rows=rows,search_term=search_term, search_by=search_by, role=role, user=user, branch_name=branch_name)

# Edit Product Receive Entry
@action('receive/edit_receive/<receive_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash, "receive/edit_receive.html")
def edit_receive(receive_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']

    assert receive_id is not None
    record = db.product_receives[receive_id]
    
    if record is None:
        redirect(URL('index'))
    
    form = Form(db.product_receives, record=record, deletable=False)

    # Apply custom styles to form fields
    if 'receive_code' in form.custom.widgets:
        form.custom.widgets['receive_code']['_class'] = 'form-control form-control-sm'
    if 'item_code' in form.custom.widgets:
        form.custom.widgets['item_code']['_class'] = 'form-control form-control-sm select-custom'
    if 'supplier_code' in form.custom.widgets:
        form.custom.widgets['supplier_code']['_class'] = 'form-control form-control-sm select-custom'
    if 'unit_name' in form.custom.widgets:
        form.custom.widgets['unit_name']['_class'] = 'form-control form-control-sm select-custom'
    if 'quantity_received' in form.custom.widgets:
        form.custom.widgets['quantity_received']['_class'] = 'form-control form-control-sm'
    if 'receive_date' in form.custom.widgets:
        form.custom.widgets['receive_date']['_class'] = 'form-control form-control-sm'
    if 'remarks' in form.custom.widgets:
        form.custom.widgets['remarks']['_class'] = 'form-control form-control-sm'
    
    if form.accepted:
        flash.set('Product receive entry updated successfully', 'success')
        redirect(URL('receive/new_receive'))

    return dict(form=form, role=role, user=user, branch_name=branch_name)

# Delete Product Receive Entry
@action('receive/delete_receive/<receive_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash)
def delete_receive(receive_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))

    assert receive_id is not None
    record = db.product_receives[receive_id]

    if record:
        db(db.product_receives.id == receive_id).delete()
        flash.set('Product receive entry deleted successfully', 'success')
    else:
        flash.set('Error: Entry not found', 'error')

    redirect(URL('receive/new_receive'))

    return dict()
