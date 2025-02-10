from py4web import action, Field, redirect, URL, response,request
from py4web.utils.form import Form
import datetime
from io import StringIO 
from ..common import db, session, T, cache, auth, flash

# new account ref
@action("account_ref/account_ref", method=["GET", "POST"])
@action.uses("account_ref/account_ref.html", auth, T, db)
def account_ref():
    if not session.get('user_id'):
        redirect(URL('login'))  
    elif session['f_password']==1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))

    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
        branch_code = session['branch_code']

        search_term = request.query.get('search_term', '')
        search_by = request.query.get('search_by', 'class_name')

        # Pagination parameters
        page = int(request.query.get('page', 1))
        items_per_page = 20
        offset = (page - 1) * items_per_page

        # if branch_code == 99:
        #     branch_query = ''
        #     branch_query2 = ''
        # else:
        #     branch_query = "and branch_code = " + str(branch_code)
        #     branch_query2 = "where branch_code = " + str(branch_code)
        
        if search_term:
            if search_by == 'account_name':
                query = "SELECT * FROM ac_account_ref WHERE cid='TDCLPC' AND account_name LIKE '%{}%' ORDER BY id DESC LIMIT {limit} OFFSET {offset}".format(search_term.lower(), limit=items_per_page, offset=offset)
            elif search_by == 'account_code':
                query = "SELECT * FROM ac_account_ref WHERE cid='TDCLPC' AND account_code LIKE '%{}%' ORDER BY id DESC LIMIT {limit} OFFSET {offset}".format(search_term.lower(), limit=items_per_page, offset=offset)
        else:
            query = "SELECT * FROM ac_account_ref  ORDER BY id DESC LIMIT {limit} OFFSET {offset}".format(limit=items_per_page, offset=offset)

        rows = db.executesql(query, as_dict=True)

        # Get total number of records for pagination
        total_records_query = "SELECT COUNT(*) FROM ac_account_ref"        
        total_records = db.executesql(total_records_query)[0][0]
        total_pages = (total_records + items_per_page - 1) // items_per_page

        # Calculate the range of records being displayed
        start_record = offset + 1
        end_record = min(offset + items_per_page, total_records)

        db.ac_account_ref.created_by.default=user  
        # db.ac_account_ref.created_on.default= datetime.datetime.now() 
        
        form = Form(db.ac_account_ref, validation=on_validation)      
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_class'] = 'form-control form-control-sm'
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_class'] = 'form-control form-control-sm'
        if 'ref_type' in form.custom.widgets:
            form.custom.widgets['ref_type']['_class'] = 'form-control form-control-sm select-custom'
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_readonly'] = 'true'         
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_autocomplete'] = 'off'         
         
        if form.accepted:
            flash.set('Accounts-Reference added successfully', 'success')
            redirect(URL('account_ref','account_ref'))

    return dict(form=form, rows=rows, search_term=search_term, search_by=search_by, role=role, user=user, branch_name=branch_name, page=page, total_pages=total_pages, start_record=start_record, end_record=end_record, total_records=total_records)


def on_validation(form):    
    account_code = form.vars.get('account_code')    
    if db((db.ac_accounts.account_code == account_code)).count() == 0:
        form.errors['account_code'] = 'Account not found'
        

# edit account-ref
@action('account_ref/edit_account_ref/<acb_id:int>',method=["GET","POST"])
@action.uses(db,session,flash,'account_ref/edit_account_ref.html')
def edit_account_branch(acb_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']        
        branch_name = session['branch_name']
        assert acb_id is not None
        p=db.ac_account_ref[acb_id]
        if p is None:
            redirect(URL('index'))
        form = Form(db.ac_account_ref,record=p,deletable=False,validation=on_validation)
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_class'] = 'form-control form-control-sm'
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_class'] = 'form-control form-control-sm'
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_readonly'] = 'true' 
        if 'ref_type' in form.custom.widgets:
            form.custom.widgets['ref_type']['_class'] = 'form-control form-control-sm select-custom' 
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_readonly'] = 'true' 
        if form.accepted:
            flash.set('Account-Reference updated successfully','success')
            redirect(URL('account_ref','account_ref'))
    return dict(form=form,role=role,branch_name=branch_name,user=user)


# delete account-ref
@action('account_ref/delete_account_ref/<ar_code>',method=["GET","POST"])
@action.uses(db,session,flash)
def delete_account_branch(ar_code=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']

    assert ar_code is not None           
    ar_exists = db.executesql("select * from ac_voucher_reference where account_code = %s",placeholders=[ar_code])
    if ar_exists:        
        flash.set('Unable to delete! Account-Reference exists in voucher reference','error')
        redirect(URL('account_ref','account_ref'))
    else:        
        db.executesql("delete from ac_account_ref where account_code= %s",placeholders=[ar_code])
        
        flash.set('Account-Reference deleted successfully','success')
        redirect(URL('account_ref','account_ref'))    
    
    return dict(role=role,user=user,branch_name=branch_name)


# @action('account_ref/download_account_ref', method=['GET'])
# @action.uses(db)
# def download_account_branch():
#     # Use raw SQL to select specific columns
#     query = "SELECT CONCAT('''',account_code ),account_name,ref_type FROM ac_account_ref"  
#     rows = db.executesql(query)
    
#     # Create an in-memory text stream to hold the CSV data
#     csv_stream = StringIO()
    
#     # Write the header to the CSV
#     csv_stream.write("Account Code,Account_name,Reference Type\n")  # Replace with your actual column names
    
#     # Write the rows to the CSV stream
#     for row in rows:
#         csv_stream.write(','.join(map(str, row)) + "\n")
    
#     # Get the content of the CSV file
#     csv_content = csv_stream.getvalue()
#     csv_stream.close()
    
#     # Set the response headers to trigger a file download
#     response.headers['Content-Type'] = 'text/csv'
#     response.headers['Content-Disposition'] = 'attachment; filename="Account-Reference.csv"'
    
#     # Return the CSV content as a downloadable file
#     return csv_content


# account ref download 
from io import StringIO
import csv
@action('account_ref/download_account_ref', method=['GET'])
@action.uses(db, session)
def download_account_branch():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
               
        results = db.executesql("SELECT account_code,account_name,ref_type FROM ac_account_ref", as_dict=True)
        
        csv_stream = StringIO()       
        csv_writer = csv.writer(csv_stream,quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(["Account Code", "Account Name", "Reference Type"])
        
        for row in results:
            csv_writer.writerow([
                "'"+row['account_code'], 
                row['account_name'], 
                row['ref_type'] 
            ])
        
        csv_content = csv_stream.getvalue()
        csv_stream.close()
        
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename="Account-Reference.csv"'        
        
        return csv_content

