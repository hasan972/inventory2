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
            query = "SELECT * FROM inventory_items WHERE cid = 'TDCLPC' AND LOWER(item_name) LIKE '%{}%'".format(search_term)
        elif search_by == 'item_code':
            query = "SELECT * FROM inventory_items WHERE cid = 'TDCLPC' AND item_code LIKE '%{}%'".format(search_term)
    else:
        query = "SELECT * FROM inventory_items WHERE cid = 'TDCLPC'"

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
    if 'category' in form.custom.widgets:
            form.custom.widgets['category']['_class'] = 'form-control form-control-sm'
    if 'unit' in form.custom.widgets:
            form.custom.widgets['unit']['_class'] = 'form-control form-control-sm'
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

