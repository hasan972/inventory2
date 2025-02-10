
from py4web import action, Field, redirect, URL, response,request
from py4web.utils.form import Form
import datetime
from yatl.helpers import A
from ..common import db, session, T, cache, auth, flash

# create cash/bank
@action("cash_bank/cash_bank", method=["GET", "POST"])
@action.uses("cash_bank/cash_bank.html", auth, T, db)
def cash_bank():
    if not session.get('user_id'):
        redirect(URL('login'))
    elif session['f_password']==1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    else:
        user_name = session['user_id']
        role = session['role']
        branch_name = session['branch_name']

        search_term = request.query.get('search_term', '')
        search_by = request.query.get('search_by', 'account_name')

        if search_term:
            if search_by == 'account_code':
                query = "SELECT * FROM ac_cash_bank WHERE LOWER(account_code) LIKE '%{}%' limit 50".format(search_term.lower())
            elif search_by == 'account_name':
                query = "SELECT * FROM ac_cash_bank WHERE  LOWER(account_name) LIKE '%{}%'".format(search_term.lower())
            elif search_by == 'cash':
                query = "SELECT * FROM ac_cash_bank WHERE  account_type = 'Cash' limit 50"
            elif search_by == 'bank':
                query = "SELECT * FROM ac_cash_bank WHERE  account_type = 'Bank' limit 50"
        else:
            query = "SELECT * FROM ac_cash_bank"

        rows = db.executesql(query, as_dict=True)

        db.ac_cash_bank.created_by.default=user_name  
        # db.ac_cash_bank.created_on.default= datetime.datetime.now()        
        form = Form(db.ac_cash_bank)
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_class'] = 'form-control form-control-sm'
        if 'account_type' in form.custom.widgets:
            form.custom.widgets['account_type']['_class'] = 'form-control form-control-sm select-custom'
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'

        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_autocomplete'] = 'off'
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_readonly'] = 'true'
        
        if form.accepted: 
            flash.set('Cash/Bank Account added successfully','success')
            redirect(URL('cash_bank','cash_bank'))
        elif form.errors:
            # Display error messages using flash
            for error in form.errors.values():
                flash.set(error, "error")

    return dict(form=form, rows=rows, search_term=search_term, search_by=search_by,role=role,user=user_name,branch_name=branch_name)

# edit cach bank
@action('cash_bank/edit_cash_bank/<cb_id:int>',method=["GET","POST"])
@action.uses(db,session,flash,'cash_bank/edit_cash_bank.html')
def edit_cash_bank(cb_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']        
        branch_name = session['branch_name']
        assert cb_id is not None
        p=db.ac_cash_bank[cb_id]
        if p is None:
            redirect(URL('index'))
        form = Form(db.ac_cash_bank,record=p,deletable=False)

        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_class'] = 'form-control form-control-sm'
        if 'account_type' in form.custom.widgets:
            form.custom.widgets['account_type']['_class'] = 'form-control form-control-sm select-custom'
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'

        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_readonly'] = 'true'
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_readonly'] = 'true'
        if form.accepted:
            flash.set("Cash-Bank account updated successfully","success")
            redirect(URL('cash_bank','cash_bank'))
    return dict(form=form,role=role,branch_name=branch_name,user=user)

# delete cash_bank
@action('cash_bank/delete_cash_bank/<ac_id>', method=["GET", "POST"])
@action.uses(db, session, flash)
def delete_account(ac_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
        acc_id = str(ac_id)
        
    
    assert ac_id is not None
    
    ac_exists = db.executesql("SELECT * FROM ac_voucher_details WHERE account_code = %s LIMIT 5", placeholders=(acc_id,))
    if ac_exists:
        flash.set('Unable to delete! Account exists in vouchers', 'error')
        redirect(URL('cash_bank','cash_bank'))
    else:        
        db.executesql("DELETE FROM ac_cash_bank WHERE account_code = %s", placeholders=(acc_id,))
        
        flash.set('Account deleted successfully', 'success')
        redirect(URL('cash_bank','cash_bank'))
    
    return dict(role=role, user=user, branch_name=branch_name)

