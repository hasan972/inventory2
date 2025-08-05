import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY
import datetime

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# Create supplier
@action("supplier/new_supplier", method=["GET", "POST"])
@action.uses("supplier/new_supplier.html", auth, T, db)
def new_supplier():
    if not session.get('user_id'):
        redirect(URL('login'))  
    elif session['f_password'] == 1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    else:
        user = session['user_id']
        role = session['role']

        # new id generate 
        last_sup = db.executesql("SELECT supplier_code FROM supplier ORDER BY supplier_code DESC LIMIT 1")
        new_sup_code = 10001 if not last_sup else int(last_sup[0][0]) + 1

        branch_name = session['branch_name']
        search_term = request.query.get('search_term', '')
        search_by = request.query.get('search_by', 'supplier_name')
        
        if search_term:
            if search_by == 'supplier_name':
                query = "SELECT * FROM supplier WHERE LOWER(supplier_name) LIKE '%{}%'".format(search_term)
            elif search_by == 'supplier_code':
                query = "SELECT * FROM supplier WHERE supplier_code LIKE '%{}%'".format(search_term)
        else:
            query = "SELECT * FROM supplier"
        
        rows = db.executesql(query, as_dict=True)

        # db.supplier.created_by.default = user
        form = Form(db.supplier)
        if 'supplier_code' in form.custom.widgets:
            form.custom.widgets['supplier_code']['_class'] = 'form-control form-control-sm'
        if 'supplier_code' in form.custom.widgets:
            form.custom.widgets['supplier_code']['_value'] = str(new_sup_code)
        if 'supplier_code' in form.custom.widgets:
            form.custom.widgets['supplier_code']['_readonly'] = 'true'
        if 'supplier_name' in form.custom.widgets:
            form.custom.widgets['supplier_name']['_class'] = 'form-control form-control-sm'
        
        if form.accepted:
            flash.set('supplier added successfully', 'success')
            redirect(URL('supplier/new_supplier'))

    return dict(form=form, rows=rows, search_term=search_term, search_by=search_by, role=role, user=user, branch_name=branch_name)

# Edit supplier
@action('supplier/edit_supplier/<supplier_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash, 'supplier/edit_supplier.html')
def edit_supplier(supplier_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    
    assert supplier_id is not None
    p = db.supplier[supplier_id]
    if p is None:
        redirect(URL('index'))
    
    form = Form(db.supplier, record=p, deletable=False)

    if 'supplier_code' in form.custom.widgets:
        form.custom.widgets['supplier_code']['_class'] = 'form-control form-control-sm'
    if 'supplier_code' in form.custom.widgets:
        form.custom.widgets['supplier_code']['_readonly'] = 'true'
    if 'supplier_name' in form.custom.widgets:
        form.custom.widgets['supplier_name']['_class'] = 'form-control form-control-sm'
    if 'supplier_name' in form.custom.widgets:
        form.custom.widgets['note']['_class'] = 'form-control form-control-sm'

    if form.accepted:   
        flash.set('supplier updated successfully', 'success')               
        redirect(URL('supplier', 'new_supplier'))        
    elif form.errors:
        print(form.errors)
    
    return dict(form=form, role=role, user=user, branch_name=branch_name)

# Delete supplier
@action('supplier/delete_supplier/<supplier_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash)
def delete_supplier(supplier_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    
    assert supplier_id is not None
    # supplier_exists = db.executesql("SELECT * FROM inventory_products WHERE supplier_id = '%s'", placeholders=[supplier_id])
    # if supplier_exists:
    #     flash.set('Unable to delete! supplier exists in products', 'error')
    #     redirect(URL('supplier', 'new_supplier'))
    # else:
    db.executesql("DELETE FROM supplier where supplier_code='%s'",placeholders=[supplier_id])
    flash.set('supplier deleted successfully', 'success')
    redirect(URL('supplier', 'new_supplier'))    
    
    return dict(role=role, user=user, branch_name=branch_name)
