import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY
import datetime

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# Create unit
@action("unit/new_unit", method=["GET", "POST"])
@action.uses("unit/new_unit.html", auth, T, db)
def new_unit():
    if not session.get('user_id'):
        redirect(URL('login'))  
    elif session['f_password'] == 1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
        search_term = request.query.get('search_term', '')
        search_by = request.query.get('search_by', 'unit_name')
        
        if search_term:
            if search_by == 'unit_name':
                query = "SELECT * FROM unit WHERE LOWER(unit_name) LIKE '%{}%'".format(search_term)            
        else:
            query = "SELECT * FROM unit"
        
        rows = db.executesql(query, as_dict=True)

        # db.unit.created_by.default = user
        form = Form(db.unit)        
        if 'unit_name' in form.custom.widgets:
            form.custom.widgets['unit_name']['_class'] = 'form-control form-control-sm'
        
        if form.accepted:
            flash.set('Unit added successfully', 'success')
            redirect(URL('unit/new_unit'))

    return dict(form=form, rows=rows, search_term=search_term, search_by=search_by, role=role, user=user, branch_name=branch_name)

# Edit unit
@action('unit/edit_unit/<unit_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash, 'unit/edit_unit.html')
def edit_unit(unit_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    
    assert unit_id is not None
    p = db.unit[unit_id]
    if p is None:
        redirect(URL('index'))
    
    form = Form(db.unit, record=p, deletable=False)
    if form.accepted:   
        flash.set('unit updated successfully', 'success')               
        redirect(URL('unit', 'new_unit'))        
    elif form.errors:
        print(form.errors)
    
    return dict(form=form, role=role, user=user, branch_name=branch_name)

# Delete unit
@action('unit/delete_unit/<unit_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash)
def delete_unit(unit_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    
    assert unit_id is not None
    # unit_exists = db.executesql("SELECT * FROM inventory_products WHERE unit_id = '%s'", placeholders=[unit_id])
    # if unit_exists:
    #     flash.set('Unable to delete! unit exists in products', 'error')
    #     redirect(URL('unit', 'new_unit'))
    # else:
    db.executesql("DELETE FROM unit where unit_code='%s'",placeholders=[unit_id])
    flash.set('unit deleted successfully', 'success')
    redirect(URL('unit', 'new_unit'))    
    
    return dict(role=role, user=user, branch_name=branch_name)
