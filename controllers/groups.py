import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form,FormStyleBulma
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET
import datetime
"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# create new group
@action("groups/new_group", method=["GET", "POST"])
@action.uses("groups/new_ac_group.html", auth, T, db)
def new_group():
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
        search_by = request.query.get('search_by', 'class_name')

        if search_term:
            if search_by == 'group_name':
                query = "SELECT * FROM ac_accounts_group WHERE LOWER(group_name) LIKE '%{}%'".format(search_term.lower())
            elif search_by == 'group_code':
                query = "SELECT * FROM ac_accounts_group WHERE LOWER(group_code) LIKE '%{}%'".format(search_term)
            elif search_by == 'class_name':
                query = "SELECT * FROM ac_accounts_group WHERE LOWER(class_name) LIKE '%{}%'".format(search_term.lower())
        else:
            query = "SELECT * FROM ac_accounts_group"

        rows = db.executesql(query, as_dict=True)

        db.ac_accounts_group.created_by.default = user
        # db.ac_accounts_group.created_on.default = datetime.datetime.now()
        
        form = Form(db.ac_accounts_group)
        if 'class_name' in form.custom.widgets:
            form.custom.widgets['class_name']['_class'] = 'form-control form-control-sm select-custom'
        if 'group_code' in form.custom.widgets:
            form.custom.widgets['group_code']['_class'] = 'form-control form-control-sm'
        if 'group_code' in form.custom.widgets:
            form.custom.widgets['group_code']['_readonly'] = 'true'
        if 'group_name' in form.custom.widgets:
            form.custom.widgets['group_name']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'        

        if form.accepted:
            flash.set('Accounts group added successfully','success')
            redirect(URL('groups','new_group'))        
    return dict(form=form, rows=rows, search_term=search_term, search_by=search_by,role=role,user=user,branch_name=branch_name)



# edit group
@action('groups/edit_group/<group_id:int>',method=["GET","POST"])
@action.uses(db,session,'groups/edit_group.html',flash)
def edit_group(group_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']        
        branch_name = session['branch_name']
        assert group_id is not None
        p=db.ac_accounts_group[group_id]
        if p is None:
            redirect(URL('index'))
        form = Form(db.ac_accounts_group,record=p,deletable=False)
        if 'class_name' in form.custom.widgets:
            form.custom.widgets['class_name']['_class'] = 'form-control form-control-sm select-custom'
        if 'class_code' in form.custom.widgets:
            form.custom.widgets['class_code']['_class'] = 'form-control form-control-sm'
        if 'class_type' in form.custom.widgets:
            form.custom.widgets['class_type']['_class'] = 'form-control form-control-sm'
        if 'group_code' in form.custom.widgets:
            form.custom.widgets['group_code']['_class'] = 'form-control form-control-sm'
        if 'group_code' in form.custom.widgets:
            form.custom.widgets['group_code']['_readonly'] = 'true'
        if 'group_name' in form.custom.widgets:
            form.custom.widgets['group_name']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'       

        if 'group_code' in form.custom.widgets:
            form.custom.widgets['group_code']['_readonly'] = 'true'
        if 'class_code' in form.custom.widgets:
            form.custom.widgets['class_code']['_readonly'] = 'true'
        if form.accepted:
            flash.set("Group updated successfully","success")
            redirect(URL('groups','new_group'))
    return dict(form=form,role=role,branch_name=branch_name,user=user)

# delete group
@action('groups/delete_group/<group_id:int>',method=["GET","POST"])
@action.uses(db,session,flash)
def delete_group(group_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']

        print(group_id)
        
    assert group_id is not None    
    group_exists = db.executesql("select * from ac_accounts where group_code = '%s'",placeholders=[group_id])
    if group_exists:        
        flash.set('Unable to delete! Group exists in accounts','error')
        redirect(URL('new_group'))
    else:        
        db.executesql("delete from ac_accounts_group where group_code='%s'",placeholders=[group_id])
        
        flash.set('Group deleted successfully','success')
        redirect(URL('groups','new_group'))    
    
    return dict(role=role,user=user,branch_name=branch_name)

