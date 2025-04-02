import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET
import datetime

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# Add a new item
@action("items/new_item", method=["GET", "POST"])
@action.uses("items/new_item.html", auth, T, db)
def new_item():
    if not session.get('user_id'):
        redirect(URL('login'))

    user = session['user_id']
    role = session['role']
    branch_name = session['branch_name']
    
    search_term = request.query.get('search_term', '')
    search_by = request.query.get('search_by', 'item_name')

    if search_term:
        if search_by == 'item_name':
            query = "SELECT * FROM inventory_items WHERE  LOWER(item_name) LIKE '%{}%'".format(search_term)
        elif search_by == 'item_code':
            query = "SELECT * FROM inventory_items WHERE item_code LIKE '%{}%'".format(search_term)
    else:
        query = "SELECT * FROM inventory_items  "

    # print(query)
    rows = db.executesql(query, as_dict=True)

    # db.inventory_items.created_by.default = user
    

    form = Form(db.inventory_items)

    # for field in ['item_code', 'item_name', 'category', 'unit']:
    #     if field in form.custom.widgets:
    #         form.custom.widgets[field]['_class'] = 'form-control form-control-sm'
    if 'item_code' in form.custom.widgets:
            form.custom.widgets['item_code']['_class'] = 'form-control form-control-sm'
    if 'item_name' in form.custom.widgets:
            form.custom.widgets['item_name']['_class'] = 'form-control form-control-sm'
    if 'category_code' in form.custom.widgets:
            form.custom.widgets['category_code']['_class'] = 'form-control form-control-sm'
    if 'category_name' in form.custom.widgets:
            form.custom.widgets['category_name']['_class'] = 'form-control form-control-sm'
    if 'unit' in form.custom.widgets:
            form.custom.widgets['brand_name']['_class'] = 'form-control form-control-sm'
    if 'brand_name' in form.custom.widgets:
            form.custom.widgets['unit']['_class'] = 'form-control form-control-sm'
    if 'brand_code' in form.custom.widgets:
            form.custom.widgets['brand_code']['_class'] = 'form-control form-control-sm'
    if 'supplier_name' in form.custom.widgets:
            form.custom.widgets['supplier_name']['_class'] = 'form-control form-control-sm'
    if 'supplier_code' in form.custom.widgets:
            form.custom.widgets['supplier_code']['_class'] = 'form-control form-control-sm'
    if 'trade_price' in form.custom.widgets:
            form.custom.widgets['trade_price']['_class'] = 'form-control form-control-sm'
    if 'retail_price' in form.custom.widgets:
            form.custom.widgets['retail_price']['_class'] = 'form-control form-control-sm'

    

    if form.accepted:
        flash.set('Item added successfully', 'success')
        redirect(URL('items/new_item'))

    return dict(form=form, rows=rows, search_term=search_term, search_by=search_by, role=role, user=user, branch_name=branch_name)

# Edit an item
@action('items/edit_item/<item_id:int>', method=["GET", "POST"])
@action.uses("items/edit_item.html", db, session, flash)
def edit_item(item_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))

    user = session['user_id']
    role = session['role']
    branch_name = session['branch_name']
    
    assert item_id is not None
    item = db.inventory_items[item_id]
    if item is None:
        redirect(URL('items/new_item'))

    form = Form(db.inventory_items, record=item, deletable=False)

    if 'item_code' in form.custom.widgets:
            form.custom.widgets['item_code']['_class'] = 'form-control form-control-sm'
    if 'item_name' in form.custom.widgets:
            form.custom.widgets['item_name']['_class'] = 'form-control form-control-sm'
    if 'category' in form.custom.widgets:
            form.custom.widgets['category']['_class'] = 'form-control form-control-sm select-custom'
    if 'unit' in form.custom.widgets:
            form.custom.widgets['unit']['_class'] = 'form-control form-control-sm'

    if form.accepted:
        flash.set('Item updated successfully', 'success')
        redirect(URL('items/new_item'))

    elif form.errors:
        print('form.errors')

    return dict(form=form, role=role, user=user, branch_name=branch_name)

# Delete an item
@action('items/delete_item/<item_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash)
def delete_item(item_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))

    user = session['user_id']
    role = session['role']
    branch_name = session['branch_name']

    assert item_id is not None
    item_exists = db.executesql("SELECT * FROM inventory_items WHERE item_code = '%s'",placeholders=[item_id])

    if not item_exists:
        flash.set('Item not found', 'error')
        redirect(URL('items/new_item'))
    else:
        db.executesql("DELETE FROM inventory_items WHERE item_code = '%s'",placeholders=[item_id])
        flash.set('Item deleted successfully', 'success')
        redirect(URL('items/new_item'))

    return dict(role=role, user=user, branch_name=branch_name)

# End-point to fetch branch code
@action('items/get_brand_code',method=["GET"])
@action.uses(db)
def get_brand_code():   
    brand_name = request.query.get("q")        
    brand_row = db(db.brand.brand_name == brand_name).select().first()  
    brand_code=brand_row.brand_code    
    supplier_code=brand_row.supplier_code    
    supplier_name=brand_row.supplier_name    
    
    return dict(brand_code=brand_code,supplier_code=supplier_code,supplier_name=supplier_name)

# End-point to fetch category code
@action('items/get_cat_code',method=["GET"])
@action.uses(db)
def get_cat_code():   
    category_name = request.query.get("q")        
    cat_row = db(db.category.category_name == category_name).select().first()  
    category_code=cat_row.category_code   
    # print(cat_row.category_code)
    # print("Hello"+category_code)
    
    return dict(category_code=category_code)
# End-point to fetch branch code
# @action('items/test',method=["GET"])
# @action.uses(db)
# def test():   
#     # brand_name = request.query.get("q")        
#     # brand_row = db(db.brand.brand_name == brand_name).select().first()  
#     # brand_code=brand_row.brand_code    
    
#     return "Hello"

