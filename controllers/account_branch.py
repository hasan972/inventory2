from py4web import action, Field, redirect, URL, response,request
from py4web.utils.form import Form
import datetime
from io import StringIO 
from ..common import db, session, T, cache, auth, flash

# new account branch
@action("account_branch/account_branch", method=["GET", "POST"])
@action.uses("account_branch/account_branch.html", auth, T, db)
def account_branch():
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
        items_per_page = 50
        offset = (page - 1) * items_per_page

        if branch_code == 99:
            branch_query = ''
            branch_query2 = ''
        else:
            branch_query = "and branch_code = " + str(branch_code)
            branch_query2 = "where cid='TDCLPC' and branch_code = " + str(branch_code)
        
        if search_term:
            if search_by == 'account_name':
                query = "SELECT * FROM ac_account_branch WHERE cid= 'TDCLPC' and account_name LIKE '%{}%' {bc} ORDER BY id DESC LIMIT {limit} OFFSET {offset}".format(search_term.lower(), bc=branch_query, limit=items_per_page, offset=offset)
                # print(query)
            elif search_by == 'account_code':
                query = "SELECT * FROM ac_account_branch WHERE cid= 'TDCLPC' and account_code LIKE '%{}%' {bc} ORDER BY id DESC LIMIT {limit} OFFSET {offset}".format(search_term.lower(), bc=branch_query, limit=items_per_page, offset=offset)
                # print(query)
            elif search_by == 'branch_name':
                query = "SELECT * FROM ac_account_branch WHERE cid= 'TDCLPC' and branch_name LIKE '%{}%' {bc} ORDER BY id DESC LIMIT {limit} OFFSET {offset}".format(search_term.lower(), bc=branch_query, limit=items_per_page, offset=offset)
                # print(query)
            elif search_by == 'branch_code':
                query = "SELECT * FROM ac_account_branch WHERE cid= 'TDCLPC' and branch_code = '{}' {bc} ORDER BY id DESC LIMIT {limit} OFFSET {offset}".format(search_term.lower(), bc=branch_query, limit=items_per_page, offset=offset)
                # print(query)
        else:
            query = "SELECT * FROM ac_account_branch {bc} ORDER BY id DESC LIMIT {limit} OFFSET {offset}".format(bc=branch_query2, limit=items_per_page, offset=offset)
            # print(query)

        rows = db.executesql(query, as_dict=True)

        # Get total number of records for pagination
        total_records_query = "SELECT COUNT(*) FROM ac_account_branch"
        if branch_code != 99:
            total_records_query += f" WHERE branch_code={branch_code}"
        total_records = db.executesql(total_records_query)[0][0]
        total_pages = (total_records + items_per_page - 1) // items_per_page

        # Calculate the range of records being displayed
        start_record = offset + 1
        end_record = min(offset + items_per_page, total_records)

        db.ac_account_branch.created_by.default=user  
        # db.ac_account_branch.created_on.default= datetime.datetime.now() 
        
        form = Form(db.ac_account_branch, validation=on_validation)
        if 'branch_code' in form.custom.widgets:
            form.custom.widgets['branch_code']['_class'] = 'form-control form-control-sm'
        if 'branch_name' in form.custom.widgets:
            form.custom.widgets['branch_name']['_class'] = 'form-control form-control-sm select-custom'
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_class'] = 'form-control form-control-sm'
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_class'] = 'form-control form-control-sm'
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_autocomplete'] = 'off' 
        if 'branch_code' in form.custom.widgets:
            form.custom.widgets['branch_code']['_readonly'] = 'true' 
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_readonly'] = 'true' 

        if request.method == "POST":        
            account_code = str(request.forms.get('account_code')).strip()      
            branch_code = str(request.forms.get('branch_code')).strip() 
            branch_name = str(request.forms.get('branch_name')).strip() 
              
            # # Check for duplicate entry
            # duplicate = db(db.ac_account_branch.account_code == account_code and db.ac_account_branch.branch_code == branch_code).select().first()
            # if duplicate:
            #     form.errors['account_code'] = 'This account code with the specified branch code already exists.' 

            if branch_name == "All":
                db.executesql("DELETE FROM ac_account_branch WHERE account_code = %s and branch_name <> 'All'", (account_code,))
            else:
                db.executesql("DELETE FROM ac_account_branch WHERE account_code = %s AND branch_name = 'All'", (account_code,))   
            if form.accepted:
                flash.set('Accounts-Branch added successfully', 'success')
                redirect(URL('account_branch','account_branch'))

    return dict(form=form, rows=rows, search_term=search_term, search_by=search_by, role=role, user=user, branch_name=branch_name, page=page, total_pages=total_pages, start_record=start_record, end_record=end_record, total_records=total_records)



def on_validation(form):
    # print('Hellllo')
    account_code = form.vars.get('account_code')
    branch_code = form.vars.get('branch_code')
    if db((db.ac_account_branch.account_code == account_code) & (db.ac_account_branch.branch_code == branch_code)).count() > 0:
        form.errors['account_code'] = 'This account code already exists for the selected branch code.'
        

# edit account-branch
@action('account_branch/edit_account_branch/<acb_id:int>',method=["GET","POST"])
@action.uses(db,session,flash,'account_branch/edit_account_branch.html')
def edit_account_branch(acb_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']        
        branch_name = session['branch_name']
        assert acb_id is not None
        p=db.ac_account_branch[acb_id]
        if p is None:
            redirect(URL('index'))
        form = Form(db.ac_account_branch,record=p,deletable=False,validation=on_validation)
        if 'branch_code' in form.custom.widgets:
            form.custom.widgets['branch_code']['_class'] = 'form-control form-control-sm'
        if 'branch_name' in form.custom.widgets:
            form.custom.widgets['branch_name']['_class'] = 'form-control form-control-sm select-custom'
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_class'] = 'form-control form-control-sm'
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_class'] = 'form-control form-control-sm'
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_autocomplete'] = 'off' 
        if 'account_code' in form.custom.widgets:
            form.custom.widgets['account_code']['_readonly'] = 'true' 
        if 'branch_code' in form.custom.widgets:
            form.custom.widgets['branch_code']['_readonly'] = 'true' 
        if 'account_name' in form.custom.widgets:
            form.custom.widgets['account_name']['_readonly'] = 'true' 
        if form.accepted:
            flash.set('Account-Branch updated successflly','success')
            redirect(URL('account_branch','account_branch'))
    return dict(form=form,role=role,branch_name=branch_name,user=user)


# delete account-branch
@action('account_branch/delete_account_branch/<ac_code>/<br_code>',method=["GET","POST"])
@action.uses(db,session,flash)
def delete_account_branch(ac_code=None,br_code=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']

    assert ac_code is not None    
    assert br_code is not None    
    acb_exists = db.executesql("select * from ac_voucher_details where account_code = %s and branch_code= %s",placeholders=[ac_code,br_code])
    if acb_exists:        
        flash.set('Unable to delete! Account-Branch exists in vouchers','error')
        redirect(URL('account_branch','account_branch'))
    else:        
        db.executesql("delete from ac_account_branch where account_code= %s and branch_code=%s",placeholders=[ac_code,br_code])
        
        flash.set('Account-Branch deleted successfully','success')
        redirect(URL('account_branch','account_branch'))    
    
    return dict(role=role,user=user,branch_name=branch_name)

# account branch download 
# @action('account_branch/download_account_branch', method=['GET'])
# @action.uses(db)
# def download_account_branch():
#     # Use raw SQL to select specific columns
#     query = "SELECT CONCAT('''',account_code ),id,account_name,branch_code,branch_name FROM ac_account_branch"  
#     rows = db.executesql(query)
    
#     # Create an in-memory text stream to hold the CSV data
#     csv_stream = StringIO()
    
#     # Write the header to the CSV
#     csv_stream.write("Account Code,id,Account_name,Branch Code,Branch Name\n")  # Replace with your actual column names
    
#     # Write the rows to the CSV stream
#     for row in rows:
#         csv_stream.write(','.join(map(str, row)) + "\n")
    
#     # Get the content of the CSV file
#     csv_content = csv_stream.getvalue()
#     csv_stream.close()
    
#     # Set the response headers to trigger a file download
#     response.headers['Content-Type'] = 'text/csv'
#     response.headers['Content-Disposition'] = 'attachment; filename="Account-Branch.csv"'
    
#     # Return the CSV content as a downloadable file
#     return csv_content

from io import StringIO
import csv

@action('account_branch/download_account_branch', method=['GET'])
@action.uses(db, session)
def download_account_branch():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
               
        results = db.executesql("SELECT account_code,account_name,branch_code,branch_name FROM ac_account_branch", as_dict=True)
        
        csv_stream = StringIO()       
        csv_writer = csv.writer(csv_stream,quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(["Account Code", "Account Name", "Branch Code", "Branch Name"])
        
        for row in results:
            csv_writer.writerow([
                "'"+row['account_code'], 
                row['account_name'], 
                row['branch_code'], 
                row['branch_name'], 
            ])
        
        csv_content = csv_stream.getvalue()
        csv_stream.close()
        
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename="Account-Branch.csv"'        
        
        return csv_content
