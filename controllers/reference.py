
from py4web import action, redirect, URL, response,request
from py4web.utils.form import Form
import datetime
from io import StringIO 
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash


# create new reference
@action("reference/new_ref",method=["GET","POST"])
@action.uses("reference/referance.html", auth, T)
def new_ref():

    if not session.get('user_id'):
        redirect(URL('login'))
    elif session['f_password']==1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    else:
        user_name = session['user_id']
        branch_name = session['branch_name']
        role = session['role']

        search_term = request.query.get('search_term', '')
        search_by = request.query.get('search_by', 'ref_name')

        page = int(request.query.get('page', 1))
        items_per_page = 30
        offset = (page - 1) * items_per_page

        
        if search_term:
            if search_by == 'ref_name':
                query = "SELECT * FROM ac_reference WHERE LOWER(ref_name) LIKE '%{}%' order by id desc limit {limit} offset {offset} ".format(search_term.lower(),limit=items_per_page,offset=offset)
            elif search_by == 'ref_code':
                query = "SELECT * FROM ac_reference WHERE LOWER(ref_code) LIKE '%{}%' order by id desc limit {limit} offset {offset}".format(search_term.lower(),limit=items_per_page,offset=offset)
            
        else:
            query = "SELECT * FROM ac_reference order by id desc limit {limit} offset {offset}".format(limit=items_per_page,offset=offset)

        rows = db.executesql(query, as_dict=True)    

        # Get total number of records for pagination
        total_records_query = "SELECT COUNT(*) FROM ac_reference"        
        total_records = db.executesql(total_records_query)[0][0]
        total_pages = (total_records + items_per_page - 1) // items_per_page

        # Calculate the range of records being displayed
        start_record = offset + 1
        end_record = min(offset + items_per_page, total_records)

        db.ac_reference.created_by.default=user_name  
        # db.ac_reference.created_on.default= datetime.datetime.now() 

        form = Form(db.ac_reference)    
        if 'ref_code' in form.custom.widgets:
            form.custom.widgets['ref_code']['_class'] = 'form-control form-control-sm'
        if 'ref_name' in form.custom.widgets:
            form.custom.widgets['ref_name']['_class'] = 'form-control form-control-sm'
        if 'des' in form.custom.widgets:
            form.custom.widgets['des']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'    
        if 'ref_type' in form.custom.widgets:
            form.custom.widgets['ref_type']['_class'] = 'form-control form-control-sm select-custom'    
        
        
        if form.accepted:
            # Do something with form.vars['product_name'] and form.vars['product_quantity']
            flash.set("New reference created succesfully","success")
            redirect(URL('reference','new_ref'))

    return dict(form=form,rows=rows,role=role,user=user_name,branch_name=branch_name,search_term=search_term, search_by=search_by,page=page, total_pages=total_pages, start_record=start_record, end_record=end_record, total_records=total_records)

# edit ref
@action('reference/edit_ref/<ref_id:int>',method=["GET","POST"])
@action.uses(db,session,flash,'reference/edit_ref.html')
def edit_ref(ref_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']        
        branch_name = session['branch_name']
        assert ref_id is not None
        p=db.ac_reference[ref_id]
        if p is None:
            redirect(URL('index'))
        
        p.updated_by = user
        
        # db.ac_reference.updated_by.default = user
        # print(db.ac_reference.updated_by.default)
        form = Form(db.ac_reference,record=p,deletable=False)

        

        if 'ref_code' in form.custom.widgets:
            form.custom.widgets['ref_code']['_class'] = 'form-control form-control-sm'
        if 'ref_name' in form.custom.widgets:
            form.custom.widgets['ref_name']['_class'] = 'form-control form-control-sm'
        if 'des' in form.custom.widgets:
            form.custom.widgets['des']['_class'] = 'form-control form-control-sm'
        if 'note' in form.custom.widgets:
            form.custom.widgets['note']['_class'] = 'form-control form-control-sm'    
        if 'ref_type' in form.custom.widgets:
            form.custom.widgets['ref_type']['_class'] = 'form-control form-control-sm select-custom'            
        
        if form.accepted:
            ref_code = p.ref_code
            update_query = """update ac_reference set updated_by ='{user}', updated_on = '{update_date}' where ref_code = '{ref_code}'""".format(user= user,update_date=datetime.datetime.now(),ref_code=ref_code)
            db.executesql(update_query)
            # print(update_query)
            flash.set("Reference updated successfully","success")
            redirect(URL('reference','new_ref'))
    return dict(form=form,role=role,branch_name=branch_name,user=user)

# delete ref
@action('reference/delete_ref/<ref_id>', method=["GET", "POST"])
@action.uses(db, session, flash)
def delete_account(ref_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
        acc_id = str(ref_id)       
    
    assert ref_id is not None
    
    ref_exists = db.executesql("SELECT * FROM ac_voucher_reference WHERE ref_code = %s and status <> 'CANCEL' LIMIT 5", placeholders=(acc_id,))
    if ref_exists:
        flash.set('Unable to delete! Voucher already created with this reference', 'error')
        redirect(URL('reference','new_ref'))
    else:
        db.executesql("DELETE FROM ac_reference WHERE ref_code = %s", placeholders=(acc_id,))
              
        flash.set('Reference deleted successfully', 'success')
        redirect(URL('reference','new_ref'))
    
    return dict(role=role, user=user, branch_name=branch_name)

# @action('reference/download_reference', method=['GET'])
# @action.uses(db)
# def download_ref():
#     # Use raw SQL to select specific columns
#     query = "SELECT ref_code,ref_name,des,ref_type FROM ac_reference"  
#     rows = db.executesql(query)
    
#     # Create an in-memory text stream to hold the CSV data
#     csv_stream = StringIO()
    
#     # Write the header to the CSV
#     csv_stream.write("Ref. Code,Ref. Name,Description,Ref. Type\n")  # Replace with your actual column names
    
#     # Write the rows to the CSV stream
#     for row in rows:
#         csv_stream.write(','.join(map(str, row)) + "\n")
    
#     # Get the content of the CSV file
#     csv_content = csv_stream.getvalue()
#     csv_stream.close()
    
#     # Set the response headers to trigger a file download
#     response.headers['Content-Type'] = 'text/csv'
#     response.headers['Content-Disposition'] = 'attachment; filename="Reference.csv"'
    
#     # Return the CSV content as a downloadable file
#     return csv_content



from io import StringIO
import csv

@action('reference/download_reference', method=['GET'])
@action.uses(db, session)
def download_ref():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
               
        results = db.executesql("SELECT ref_code,ref_name,des,ref_type FROM ac_reference", as_dict=True)
        
        csv_stream = StringIO()       
        csv_writer = csv.writer(csv_stream,quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(["Ref. Code", "Ref. Name", "Description", "Ref. Type"])
        
        for row in results:
            ref_id = str(row['ref_code'])  
            csv_writer.writerow([
                f"\t{ref_id}",  
                row['ref_name'], 
                row['des'], 
                row['ref_type']
            ])

        csv_content = csv_stream.getvalue()
        csv_stream.close()
        
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename="Reference.csv"'        
        
        return csv_content

