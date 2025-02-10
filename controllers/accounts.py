import json
from py4web import action, request,Field, abort,redirect, URL, response
from py4web.utils.form import Form
import datetime
from yatl.helpers import A
from ..common import db, session, T, cache, auth,  flash
from ..common_cid import date_fixed

# create account
@action("accounts/new_account", method=["GET", "POST"])
@action.uses("accounts/new_account.html", auth, T, db, flash)
def new_account():
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

        page = int(request.query.get('page', 1))
        items_per_page = 50
        offset = (page - 1) * items_per_page

        if search_term:
            if search_by == 'account_name':
                query = "SELECT * FROM ac_accounts WHERE LOWER(account_name) LIKE '%{}%' order by id desc LIMIT {limit} OFFSET {offset}".format(search_term,limit=items_per_page, offset=offset)
            elif search_by == 'account_code':
                query = "SELECT * FROM ac_accounts WHERE LOWER(account_code) LIKE '%{}%' order by id desc LIMIT {limit} OFFSET {offset}".format(search_term,limit=items_per_page, offset=offset)
            elif search_by == 'group_name':
                query = "SELECT * FROM ac_accounts WHERE LOWER(group_name) LIKE '%{}%' order by id desc LIMIT {limit} OFFSET {offset}".format(search_term,limit=items_per_page, offset=offset)
            else:
                query = "SELECT * FROM ac_accounts order by id desc limit 50"
        else:
            query = "SELECT * FROM ac_accounts order by id desc limit 50"


        rows = db.executesql(query, as_dict=True)

        total_records_query = "SELECT COUNT(*) FROM ac_accounts"        
        total_records = db.executesql(total_records_query)[0][0]
        total_pages = (total_records + items_per_page - 1) // items_per_page

        # Calculate the range of records being displayed
        start_record = offset + 1
        end_record = min(offset + items_per_page, total_records)

        db.ac_accounts.created_by.default = user_name
        db.ac_accounts.created_on.default = date_fixed
        
        form = Form(db.ac_accounts)
        
        # Customize form widgets
        if 'class_name' in form.custom.widgets:
            form.custom.widgets['class_name']['_class'] = 'form-control form-control-sm select-custom'
        if 'group_name' in form.custom.widgets:
            form.custom.widgets['group_name']['_class'] = 'form-control form-control-sm select-custom'
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_class'] = 'form-control form-control-sm'
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'
        if 'class_type' in form.custom.widgets:
            form.custom.widgets['class_type']['_class'] = 'form-control form-control-sm select-custom'
        
        if form.accepted:
            # Handle successful form submission here
            group_name = request.forms.get('group_name')
            account_code = request.forms.get('account_code')
            account_name = request.forms.get('account_name').replace("'","")
            
            # Fetch class_code, class_type, and group_code from ac_accounts_group table
            group = db(db.ac_accounts_group.group_name == group_name).select().first()
            
            if group:
                # Update the ac_accounts table with the fetched values
                db(db.ac_accounts.account_code == account_code).update(
                    class_code=group.class_code,
                    class_type=group.class_type,
                    group_code=group.group_code
                )

                sql= """
                    insert into ac_account_branch (branch_code,branch_name,account_code,account_name,field2,created_by, created_on,cid) values 
                    ('99','All','{ac_code}','{ac_name}',0,'{username}','{dt}','TDCLPC')
                    """.format(ac_code=account_code,ac_name=account_name,username=user_name, dt=datetime.datetime.now())           
                db.executesql(sql)
                flash.set("Account added successfully", "success")
                redirect(URL('accounts','new_account'))
            else:
                flash.set("Failed to update account information", "warning")

            flash.set("Account created successfully", "success")
            redirect(URL('accounts','new_account'))
        elif form.errors:
            # Display error messages using flash
            for error in form.errors.values():
                flash.set(error, "danger")

    return dict(form=form, search_term=search_term, search_by=search_by, rows=rows, role=role, user=user_name, branch_name=branch_name,page=page, total_pages=total_pages, start_record=start_record, end_record=end_record, total_records=total_records)

# edit account
@action('accounts/edit_account/<ac_id:int>',method=["GET","POST"])
@action.uses(db,session,flash,'accounts/edit_account.html')
def edit_account(ac_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        role=session['role']
        branch_name=session['branch_name']
        user=session['user_id']
        db.ac_accounts.updated_by.default = user
        assert ac_id is not None
        p=db.ac_accounts[ac_id]

        current_ac_name = p.account_name
        current_ac_code = p.account_code

        if p is None:
            redirect(URL('index'))
        
        # db.ac_accounts.updated_by.default = user
        # db.ac_accounts.updated_on.default = datetime.datetime.now()
        form=Form(db.ac_accounts,record=p,deletable=False)
        
        
        if 'group_code' in form.custom.widgets:
            form.custom.widgets['group_code']['_class'] = 'form-control form-control-sm'
        if 'class_code' in form.custom.widgets:
            form.custom.widgets['class_code']['_class'] = 'form-control form-control-sm'
        if 'class_name' in form.custom.widgets:
            form.custom.widgets['class_name']['_class'] = 'form-control form-control-sm select-custom'
        if 'group_name' in form.custom.widgets:
            form.custom.widgets['group_name']['_class'] = 'form-control form-control-sm select-custom'
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_class'] = 'form-control form-control-sm'
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'
        if 'class_type' in form.custom.widgets:
            form.custom.widgets['class_type']['_class'] = 'form-control form-control-sm select-custom'
        if form.accepted:
            new_ac_name = form.vars['account_name']
            if current_ac_name!= new_ac_name:
                db(db.ac_cash_bank.account_code == current_ac_code).update(
                account_name = new_ac_name,
                updated_by=user,
                updated_on=date_fixed,                
            )

                db(db.ac_account_branch.account_code == current_ac_code).update(
                account_name = new_ac_name,
                updated_by=user,
                updated_on=date_fixed,                
                )
            

            db(db.ac_accounts.id == ac_id).update(
                updated_by=user,
                updated_on=date_fixed,                
            )
            flash.set('Account updated successfully','success')
            redirect(URL('accounts','new_account'))
            
        elif form.errors:
            print(form.errors)
    return dict(form=form,role=role,branch_name=branch_name,user=user)


# delete account
@action('accounts/delete_account/<ac_id>', method=["GET", "POST"])
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
        redirect(URL('accounts','new_account'))
    else:
        db.executesql("DELETE FROM ac_accounts WHERE account_code = %s", placeholders=(acc_id,))
        # print(db._lastsql)
        db.executesql("DELETE FROM ac_account_branch WHERE account_code = %s", placeholders=(acc_id,))
        # print(db._lastsql)
        db.executesql("DELETE FROM ac_cash_bank WHERE account_code = %s", placeholders=(acc_id,))
        # print(db._lastsql)
        flash.set('Account deleted successfully', 'success')
        redirect(URL('accounts','new_account'))
    
    return dict(role=role, user=user, branch_name=branch_name)


from io import StringIO
import csv

@action('accounts/download_accounts', method=['GET'])
@action.uses(db, session)
def download_accounts():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
               
        results = db.executesql("SELECT account_code,account_name,group_code,group_name,class_code,class_name,class_type,created_on FROM ac_accounts", as_dict=True)
        
        csv_stream = StringIO()       
        csv_writer = csv.writer(csv_stream,quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(["Account Code", "Account Name", "Group Code", "Group Name", "Class Code", "Class Name", "Class Type","Created On"])
        
        for row in results:
            csv_writer.writerow([
                "'"+row['account_code'], 
                row['account_name'], 
                row['group_code'], 
                row['group_name'], 
                row['class_code'], 
                row['class_name'], 
                row['class_type'], 
                row['created_on']
            ])
        
        csv_content = csv_stream.getvalue()
        csv_stream.close()
        
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename="COA.csv"'        
        
        return csv_content