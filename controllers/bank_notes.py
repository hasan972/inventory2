import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
import datetime
from ..common import db, session, T, cache, auth,  flash
from ..common_cid import date_fixed



# create new note/coin
@action("bank_notes/new_note", method=["GET", "POST"])
@action.uses("bank_notes/new_note.html", auth, T, db)
def new_note():
    if not session.get('user_id'):
        redirect(URL('login'))  
    elif session['f_password']==1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']

        query = "SELECT * FROM ac_bank_note"
        
        # print(query)
        rows = db.executesql(query, as_dict=True)

        db.ac_bank_note.created_by.default = user
        db.ac_bank_note.created_on.default = date_fixed


        form = Form(db.ac_bank_note)
        if 'note_code' in form.custom.widgets:
            form.custom.widgets['note_code']['_class'] = 'form-control form-control-sm'
        if 'in_words' in form.custom.widgets:
            form.custom.widgets['in_words']['_class'] = 'form-control form-control-sm'
        if 'note_amount' in form.custom.widgets:
            form.custom.widgets['note_amount']['_class'] = 'form-control form-control-sm'            
        if 'status' in form.custom.widgets:
            form.custom.widgets['status']['_class'] = 'form-control form-control-sm select-custom'
        if form.accepted:
            flash.set('New note/coin added successfully', 'success')
            redirect(URL('bank_notes/new_note'))

    return dict(form=form, rows=rows, role=role, user=user, branch_name=branch_name)