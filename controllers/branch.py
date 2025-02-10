import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form,FormStyleBulma
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET
import datetime


from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# add new branch
@action("branch/new_branch", method=["GET", "POST"])
@action.uses("branch/new_branch.html", auth, T, db)
def new_branch():
    if not session.get('user_id'):
        redirect(URL('login'))
    elif session['f_password']==1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    else:
        user_name = session['user_id']
        role = session['role']
        branch_name = session['branch_name']

        # rows = db(db.ac_branch.id > 0).select()
        # rows = db(db.ac_branch.id > 0).select()
        rows = db.executesql("select id,branch_code, branch_name,left(address,100) as address from ac_branch",as_dict=True)
        
        db.ac_branch.created_by.default=user_name
        # db.ac_branch.created_on.default= datetime.datetime.now()
        
        form = Form(db.ac_branch)
        if 'branch_code' in form.custom.widgets:
            form.custom.widgets['branch_code']['_class'] = 'form-control form-control-sm'
        if 'branch_name' in form.custom.widgets:
            form.custom.widgets['branch_name']['_class'] = 'form-control form-control-sm'
        if 'address' in form.custom.widgets:
            form.custom.widgets['address']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'
        if form.accepted:  
            flash.set("Branch added successfully","success")      
            redirect(URL('branch','new_branch'))

    return dict(form=form, rows=rows,role=role,user=user_name,branch_name=branch_name)

# edit branch
@action('branch/edit_branch/<br_id:int>',method=["GET","POST"])
@action.uses(db,session,flash,'branch/edit_branch.html')
def edit_branch(br_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']        
        branch_name = session['branch_name']
        assert br_id is not None
        p=db.ac_branch[br_id]
        if p is None:
            redirect(URL('index'))
        form = Form(db.ac_branch,record=p,deletable=False)
        if 'branch_code' in form.custom.widgets:
            form.custom.widgets['branch_code']['_class'] = 'form-control form-control-sm'
        if 'branch_name' in form.custom.widgets:
            form.custom.widgets['branch_name']['_class'] = 'form-control form-control-sm'
        if 'address' in form.custom.widgets:
            form.custom.widgets['address']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'
        if form.accepted:
            flash.set("Branch updated successfully","success")
            redirect(URL('branch','new_branch'))
    return dict(form=form,role=role,branch_name=branch_name,user=user)

# delete branch
@action('branch/delete_branch/<br_id:int>', method=["GET", "POST"])
@action.uses(db, session, flash)
def delete_branch(br_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
       
        # print(acc_id)
    
    assert br_id is not None
    
    
    br_exists = db.executesql("SELECT * FROM ac_account_branch WHERE branch_code = %s LIMIT 5", placeholders=(br_id,))
    if br_exists:
        flash.set('Unable to delete! Branch type exists in Account-Branch', 'error')
        redirect(URL('branch','new_branch'))
    else:
        db.executesql("DELETE FROM ac_branch WHERE branch_code = %s", placeholders=(br_id,))
                
        flash.set('Branch deleted successfully', 'success')
        redirect(URL('branch','new_branch'))
    
    return dict(role=role, user=user, branch_name=branch_name)

