import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY
import datetime

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# Create brand
@action("brand/new_brand", method=["GET", "POST"])
@action.uses("brand/new_brand.html", auth, T, db)
def new_brand():
    if not session.get('user_id'):
        redirect(URL('login'))  
    elif session['f_password'] == 1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']

        # new id generate 
        last_brand = db.executesql("SELECT brand_code FROM brand ORDER BY brand_code DESC LIMIT 1")
        new_brand_code = 1001 if not last_brand else int(last_brand[0][0]) + 1

        search_term = request.query.get('search_term', '')
        search_by = request.query.get('search_by', 'brand_name')
        
        if search_term:
            if search_by == 'brand_name':
                query = "SELECT * FROM brand WHERE LOWER(brand_name) LIKE '%{}%'".format(search_term)
            elif search_by == 'brand_code':
                query = "SELECT * FROM brand WHERE brand_code LIKE '%{}%'".format(search_term)
        else:
            query = "SELECT * FROM brand"
        
        rows = db.executesql(query, as_dict=True)

        # db.brand.created_by.default = user
        form = Form(db.brand)
        if 'brand_code' in form.custom.widgets:
            form.custom.widgets['brand_code']['_class'] = 'form-control form-control-sm'
        if 'brand_code' in form.custom.widgets:
            form.custom.widgets['brand_code']['_readonly'] = 'true'
        if 'brand_code' in form.custom.widgets:
            form.custom.widgets['brand_code']['_value'] = str(new_brand_code)

        if 'brand_name' in form.custom.widgets:
            form.custom.widgets['brand_name']['_class'] = 'form-control form-control-sm'
        if 'supplier_name' in form.custom.widgets:
            form.custom.widgets['supplier_name']['_class'] = 'form-control form-control-sm'
        if 'supplier_code' in form.custom.widgets:
            form.custom.widgets['supplier_code']['_class'] = 'form-control form-control-sm'
        if 'supplier_code' in form.custom.widgets:
            form.custom.widgets['supplier_code']['_readonly'] = 'true'
        
        if form.accepted:
            flash.set('Brand added successfully', 'success')
            redirect(URL('brand/new_brand'))

    return dict(form=form, rows=rows, search_term=search_term, search_by=search_by, role=role, user=user, branch_name=branch_name)

# Edit brand
@action('brand/edit_brand/<brand_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash, 'brand/edit_brand.html')
def edit_brand(brand_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    
    assert brand_id is not None
    p = db.brand[brand_id]
    if p is None:
        redirect(URL('index'))    
    
    form = Form(db.brand, record=p, deletable=False)

    if 'brand_code' in form.custom.widgets:
        form.custom.widgets['brand_code']['_class'] = 'form-control form-control-sm'
    if 'brand_code' in form.custom.widgets:
        form.custom.widgets['brand_code']['_readonly'] = 'true'
    if 'brand_name' in form.custom.widgets:
        form.custom.widgets['brand_name']['_class'] = 'form-control form-control-sm'
    if 'supplier_name' in form.custom.widgets:
        form.custom.widgets['supplier_name']['_class'] = 'form-control form-control-sm'
    if 'supplier_code' in form.custom.widgets:
        form.custom.widgets['supplier_code']['_class'] = 'form-control form-control-sm'
    if 'supplier_code' in form.custom.widgets:
        form.custom.widgets['supplier_code']['_readonly'] = 'true'
    if 'note' in form.custom.widgets:
        form.custom.widgets['note']['_class'] = 'form-control form-control-sm'

    if form.accepted:   
        flash.set('brand updated successfully', 'success')               
        redirect(URL('brand', 'new_brand'))        
    elif form.errors:
        print(form.errors)
    
    return dict(form=form, role=role, user=user, branch_name=branch_name)

# Delete brand
@action('brand/delete_brand/<brand_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash)
def delete_brand(brand_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    
    assert brand_id is not None
    # brand_exists = db.executesql("SELECT * FROM inventory_products WHERE brand_id = '%s'", placeholders=[brand_id])
    # if brand_exists:
    #     flash.set('Unable to delete! brand exists in products', 'error')
    #     redirect(URL('brand', 'new_brand'))
    # else:
    db.executesql("DELETE FROM brand where brand_code='%s'",placeholders=[brand_id])
    flash.set('brand deleted successfully', 'success')
    redirect(URL('brand', 'new_brand'))    
    
    return dict(role=role, user=user, branch_name=branch_name)

# End-point to fetch supplier code
@action('brand/get_sup_code',method=["GET"])
@action.uses(db)
def get_sup_code():   
    sup_name = request.query.get("q")        
    sup_row = db(db.supplier.supplier_name == sup_name).select().first()  
    sup_code=sup_row.supplier_code   
    # print(db._lastsql)

    return dict(supplier_code=sup_code)

