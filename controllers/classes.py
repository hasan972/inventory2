import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET
import datetime


from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# create class
@action("classes/new_class", method=["GET", "POST"])
@action.uses("classes/new_ac_class.html", auth, T, db)
def new_class():
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
            if search_by == 'class_name':
                query = "SELECT * FROM ac_accounts_class WHERE cid = 'TDCLPC' and LOWER(class_name) LIKE '%{}%'".format(search_term)
            elif search_by == 'class_code':
                query = "SELECT * FROM ac_accounts_class WHERE cid = 'TDCLPC' and class_code LIKE '%{}%'".format(search_term)
        else:
            query = "SELECT * FROM ac_accounts_class"
        
        # print(query)
        rows = db.executesql(query, as_dict=True)

        db.ac_accounts_class.created_by.default = user
        # db.ac_accounts_class.created_on.default = datetime.datetime.now()
        # db.ac_accounts_class.updated_by.default = ""
        # db.ac_accounts_class.updated_on.default = datetime.datetime.now()

        form = Form(db.ac_accounts_class)
        if 'class_code' in form.custom.widgets:
            form.custom.widgets['class_code']['_class'] = 'form-control form-control-sm'
        if 'class_name' in form.custom.widgets:
            form.custom.widgets['class_name']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'
        if 'class_type' in form.custom.widgets:
            form.custom.widgets['class_type']['_class'] = 'form-control form-control-sm select-custom'
        if form.accepted:
            flash.set('Accounts Class added successfully', 'success')
            redirect(URL('classes/new_class'))

    return dict(form=form, rows=rows, search_term=search_term, search_by=search_by, role=role, user=user, branch_name=branch_name)

# edit class
@action('classes/edit_class/<class_id:int>',method=["GET","POST"])
@action.uses(db,session,flash,'classes/edit_class.html')
def edit_class(class_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    assert class_id is not None
    p=db.ac_accounts_class[class_id]
    if p is None:
        redirect(URL('index'))
   
    form = Form(db.ac_accounts_class,record=p,deletable=False)
    if 'class_code' in form.custom.widgets:
            form.custom.widgets['class_code']['_class'] = 'form-control form-control-sm'
    if 'class_name' in form.custom.widgets:
        form.custom.widgets['class_name']['_class'] = 'form-control form-control-sm'
    if 'note' in form.custom.widgets:
        form.custom.widgets['note']['_class'] = 'form-control form-control-sm'
    if 'class_type' in form.custom.widgets:
        form.custom.widgets['class_type']['_class'] = 'form-control form-control-sm select-custom'
    if form.accepted:   
        flash.set('Class updated successfully','success')               
        redirect(URL('classes','new_class'))        
    elif form.errors:
        print(form.errors)
    return dict(form=form,role=role,user=user,branch_name=branch_name)

# delete class
@action('classes/delete_class/<class_id:int>',method=["GET","POST"])
@action.uses(db,session,flash)
def delete_class(class_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    assert class_id is not None
    class_exists = db.executesql("select * from ac_accounts_group where class_code = '%s'",placeholders=[class_id])
    if class_exists:
        flash.set('Unable to delete! Class exists in groups','error')
        redirect(URL('classes','new_class'))
    else:
        db.executesql("delete from ac_accounts_class where class_code='%s'",placeholders=[class_id])
        print(db._lastsql)
        flash.set('Class deleted successfully','success')
        redirect(URL('classes','new_class'))    
    
    return dict(role=role,user=user,branch_name=branch_name)