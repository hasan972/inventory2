import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY
import datetime

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# Create category
@action("categories/new_category", method=["GET", "POST"])
@action.uses("categories/new_category.html", auth, T, db)
def new_category():
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
        last_cat = db.executesql("SELECT category_code FROM category ORDER BY category_code DESC LIMIT 1")
        new_cat_code = 101 if not last_cat else int(last_cat[0][0]) + 1

        search_term = request.query.get('search_term', '')
        search_by = request.query.get('search_by', 'category_name')
        
        if search_term:
            if search_by == 'category_name':
                query = "SELECT * FROM category WHERE LOWER(category_name) LIKE '%{}%'".format(search_term)
            elif search_by == 'category_code':
                query = "SELECT * FROM category WHERE category_code LIKE '%{}%'".format(search_term)
        else:
            query = "SELECT * FROM category"
        
        rows = db.executesql(query, as_dict=True)

        # db.category.created_by.default = user
        form = Form(db.category)
        if 'category_code' in form.custom.widgets:
            form.custom.widgets['category_code']['_class'] = 'form-control form-control-sm'
        if 'category_code' in form.custom.widgets:
            form.custom.widgets['category_code']['_value'] = str(new_cat_code)
        if 'category_code' in form.custom.widgets:
            form.custom.widgets['category_code']['_readonly'] = "true"
        if 'category_name' in form.custom.widgets:
            form.custom.widgets['category_name']['_class'] = 'form-control form-control-sm'
        
        if form.accepted:
            flash.set('Category added successfully', 'success')
            redirect(URL('categories/new_category'))

    return dict(form=form, rows=rows, search_term=search_term, search_by=search_by, role=role, user=user, branch_name=branch_name)

# Edit category
@action('categories/edit_category/<category_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash, 'categories/edit_category.html')
def edit_category(category_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    
    assert category_id is not None
    p = db.category[category_id]
    if p is None:
        redirect(URL('index'))
    
    form = Form(db.category, record=p, deletable=False)

    if 'category_code' in form.custom.widgets:
        form.custom.widgets['category_code']['_class'] = 'form-control form-control-sm'
    if 'category_code' in form.custom.widgets:
        form.custom.widgets['category_code']['_readonly'] = "true"
    if 'category_name' in form.custom.widgets:
        form.custom.widgets['category_name']['_class'] = 'form-control form-control-sm'
    if 'note' in form.custom.widgets:
        form.custom.widgets['category_name']['_class'] = 'form-control form-control-sm'

    if form.accepted:   
        flash.set('Category updated successfully', 'success')               
        redirect(URL('categories', 'new_category'))        
    elif form.errors:
        print(form.errors)
    
    return dict(form=form, role=role, user=user, branch_name=branch_name)

# Delete category
@action('categories/delete_category/<category_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash)
def delete_category(category_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    
    assert category_id is not None
    # category_exists = db.executesql("SELECT * FROM inventory_products WHERE category_id = '%s'", placeholders=[category_id])
    # if category_exists:
    #     flash.set('Unable to delete! Category exists in products', 'error')
    #     redirect(URL('categories', 'new_category'))
    # else:
    db.executesql("DELETE FROM category where category_code='%s'",placeholders=[category_id])
    flash.set('Category deleted successfully', 'success')
    redirect(URL('categories', 'new_category'))    
    
    return dict(role=role, user=user, branch_name=branch_name)
