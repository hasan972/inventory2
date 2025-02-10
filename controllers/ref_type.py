from py4web import action, Field, redirect, URL, response,request,abort
from py4web.utils.form import Form
import datetime

from yatl.helpers import A
from ..common import db, session, T, cache, auth, flash


# create reference type
@action("ref_type/ref_type",method=["GET","POST"])
@action.uses("ref_type/ref_type.html", auth, T)
def ref_type():
    
    if not session.get('user_id'):
        redirect(URL('login'))
    elif session['f_password']==1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    else:
        user_name = session['user_id']
        branch_name = session['branch_name']
        role = session['role']

        rows=db(db.ac_ref_type.id>0).select()

        db.ac_ref_type.created_by.default = user_name
        # db.ac_ref_type.created_on.default = datetime.datetime.now()        
        form = Form(db.ac_ref_type)    
        if 'ref_type' in form.custom.widgets:
            form.custom.widgets['ref_type']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'
        
        if form.accepted:
            flash.set('Reference Type created successfully','success')
            redirect(URL('ref_type','ref_type'))

    return dict(form=form,rows=rows,role=role,user=user_name,branch_name=branch_name)

# edit ref_type
@action('ref_type/edit_ref_type/<rftp_id:int>',method=["GET","POST"])
@action.uses(db,session,flash,'ref_type/edit_ref_type.html')
def edit_ref_type(rftp_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']        
        branch_name = session['branch_name']
        assert rftp_id is not None
        p=db.ac_ref_type[rftp_id]
        if p is None:
            redirect(URL('index'))
        form = Form(db.ac_ref_type,record=p,deletable=False)

        if 'ref_type' in form.custom.widgets:
            form.custom.widgets['ref_type']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'

        if form.accepted:
            flash.set("Reference Type updated successfully","success")
            redirect(URL('ref_type','ref_type'))
    return dict(form=form,role=role,branch_name=branch_name,user=user)

# delete ref type
@action('ref_type/delete_ref_type/<rf_name>', method=["GET", "POST"])
@action.uses(db, session, flash)
def delete_ref_type(rf_name=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
        ref_type = str(rf_name)
        # print(acc_id)
    
    assert ref_type is not None
    
    ref_exists = db.executesql("SELECT * FROM ac_reference WHERE ref_type = %s LIMIT 5", placeholders=(ref_type,))
    if ref_exists:
        flash.set('Unable to delete! Reference type exists in Reference', 'error')
        redirect(URL('ref_type','ref_type'))
    else:
        db.executesql("DELETE FROM ac_ref_type WHERE ref_type = %s", placeholders=(ref_type,))
               
        flash.set('Ref. type deleted successfully', 'success')
        redirect(URL('ref_type','ref_type'))
    
    return dict(role=role, user=user, branch_name=branch_name)