import datetime
from py4web import action, redirect, URL, response,request
from py4web.utils.form import Form
import hashlib
from yatl.helpers import A
from ..common import db, session, T, cache, auth, flash
import hashlib

# create new user
@action("users/users", method=["GET", "POST"])
@action.uses("users/users.html", auth, T, db)
def users():
    if not session.get('user_id'):
        redirect(URL('login'))

    elif session.get('role') != 'ADMIN':
        flash.set('Access denied!', 'warning')
        redirect(URL('index'))

    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
        user_branch_code = session['branch_code']
        search_term = request.query.get('search_term', '')
        search_by = request.query.get('search_by', 'class_name')


        # Pagination parameters
        page = int(request.query.get('page', 1))
        items_per_page = 20
        offset = (page - 1) * items_per_page


        if user_branch_code != 99:
            branch_query = """and branch_code = {user_branch_code}""".format(user_branch_code=user_branch_code)
        else:
           branch_query = ""

        if search_term:
            if search_by == 'User':
                query = """select * from ac_auth_user where username like '%{userid}%' {branch_query} ORDER BY id DESC LIMIT {limit} OFFSET {offset}""".format(userid= search_term,branch_query=branch_query,limit=items_per_page, offset=offset)
            elif search_by == 'Role':
                query = """select * from ac_auth_user where role like '%{role}%' {branch_query}  ORDER BY id DESC LIMIT {limit} OFFSET {offset}""".format(role= search_term,branch_query=branch_query,limit=items_per_page, offset=offset)
            elif search_by == 'BranchCode':
                query = """select * from ac_auth_user where branch_code = '{branch_code}'  {branch_query} ORDER BY id DESC LIMIT {limit} OFFSET {offset} """.format(branch_code= search_term,branch_query=branch_query,limit=items_per_page, offset=offset)
            elif search_by == 'BranchName':
                query = """select * from ac_auth_user where branch_name like '%{branch_name}%' {branch_query} ORDER BY id DESC LIMIT {limit} OFFSET {offset} """.format(branch_name= search_term,branch_query=branch_query,limit=items_per_page, offset=offset)
            elif search_by == 'Mobile':
                query = """select * from ac_auth_user where contact like '%{contact}%' {branch_query} ORDER BY id DESC LIMIT {limit} OFFSET {offset}""".format(contact= search_term,branch_query=branch_query,limit=items_per_page, offset=offset)
        
        else:
            query = """select * from ac_auth_user where 1 {branch_query} ORDER BY id DESC LIMIT {limit} OFFSET {offset}""".format(branch_query=branch_query,limit=items_per_page, offset=offset) 

        user_rows = db.executesql(query, as_dict=True)       

        # Get total number of records for pagination
        total_records_query = "SELECT COUNT(*) FROM ac_auth_user where 1"
        if user_branch_code != 99:
            total_records_query += f" WHERE branch_code={user_branch_code}"
        
        if search_term:
            if search_by == 'User':
                total_records_query += f" and username like '%{search_term}%'"
            if search_by == 'Role':
                total_records_query += f" and role like '%{search_term}%'"
            if search_by == 'BranchCode':
                total_records_query += f" and branch_code = '{search_term}'"
            if search_by == 'BranchName':
                total_records_query += f" and branch_name like '%{search_term}%'"
            if search_by == 'Mobile':
                total_records_query += f" and contact like '%{search_term}%'"
        
        total_records = db.executesql(total_records_query)[0][0]
        total_pages = (total_records + items_per_page - 1) // items_per_page

        # Calculate the range of records being displayed
        start_record = offset + 1
        end_record = min(offset + items_per_page, total_records)

        db.ac_auth_user.created_by.default = user

        form = Form(db.ac_auth_user)        

        if 'username' in form.custom.widgets:
            form.custom.widgets['username']['_class'] = 'form-control form-control-sm'
        if 'first_name' in form.custom.widgets:
            form.custom.widgets['first_name']['_class'] = 'form-control form-control-sm'
        if 'last_name' in form.custom.widgets:
            form.custom.widgets['last_name']['_class'] = 'form-control form-control-sm'
        if 'status' in form.custom.widgets:
            form.custom.widgets['status']['_class'] = 'form-control form-control-sm select-custom'
        if 'email' in form.custom.widgets:
            form.custom.widgets['email']['_class'] = 'form-control form-control-sm'
        if 'password' in form.custom.widgets:
            form.custom.widgets['password']['_class'] = 'form-control form-control-sm'
        if 'branch_name' in form.custom.widgets:
            form.custom.widgets['branch_name']['_class'] = 'form-control form-control-sm select-custom'
        if 'role' in form.custom.widgets:
            form.custom.widgets['role']['_class'] = 'form-control form-control-sm select-custom'
        if 'contact' in form.custom.widgets:
            form.custom.widgets['contact']['_class'] = 'form-control form-control-sm'
        if 'password' in form.custom.widgets:
            form.custom.widgets['password']['_type'] = 'password'
        if 'branch_code' in form.custom.widgets:
            form.custom.widgets['branch_code']['_readonly'] = 'true'

        db.ac_auth_user.f_password.default = 1
        db.ac_auth_user.created_by.default = user

        if form.accepted:
            # Hash the password 
            password = form.vars['password']
            new_user = form.vars['username']        
            hashed_password = hashlib.sha256(password.encode()).hexdigest()            
            query = """update ac_auth_user set password = '{hash_password}' where username = '{user}'""".format(hash_password=hashed_password, user = new_user)
            db.executesql(query)
            flash.set('New user created successfully', 'success')
            redirect(URL('users', 'users'))

    return dict(form=form,role=role,user_rows=user_rows,user=user,branch_name=branch_name,search_term=search_term, search_by=search_by, page=page, total_pages=total_pages, start_record=start_record,
    end_record=end_record,
    total_records=total_records
)


# edit user
@action('users/edit_user/<user_id:int>',method=["GET","POST"])
@action.uses(db,session,flash,'users/edit_user.html')
def edit_user(user_id=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
    assert user_id is not None
    p=db.ac_auth_user[user_id]
    # print(p.status)
    current_pass = p.password
    if p is None:
        flash.set("User updated successfully","success")
        redirect(URL('users','index'))

    # setting updated by 
    db.ac_auth_user.updated_by.default = user
    form = Form(db.ac_auth_user,record=p,deletable=False)   
    
    
    if 'username' in form.custom.widgets:
            form.custom.widgets['username']['_class'] = 'form-control form-control-sm'
    if 'first_name' in form.custom.widgets:
        form.custom.widgets['first_name']['_class'] = 'form-control form-control-sm'
    if 'last_name' in form.custom.widgets:
        form.custom.widgets['last_name']['_class'] = 'form-control form-control-sm'
    if 'status' in form.custom.widgets:
        form.custom.widgets['status']['_class'] = 'form-control form-control-sm select-custom'
    if 'email' in form.custom.widgets:
        form.custom.widgets['email']['_class'] = 'form-control form-control-sm'
    if 'password' in form.custom.widgets:
        form.custom.widgets['password']['_class'] = 'form-control form-control-sm'
    if 'branch_name' in form.custom.widgets:
        form.custom.widgets['branch_name']['_class'] = 'form-control form-control-sm select-custom'
    if 'note' in form.custom.widgets:
        form.custom.widgets['note']['_class'] = 'form-control form-control-sm'
    if 'role' in form.custom.widgets:
        form.custom.widgets['role']['_class'] = 'form-control form-control-sm select-custom'    
    if 'contact' in form.custom.widgets:
        form.custom.widgets['contact']['_class'] = 'form-control form-control-sm'
    if 'branch_code' in form.custom.widgets:
        form.custom.widgets['branch_code']['_class'] = 'form-control form-control-sm'
    if 'branch_code' in form.custom.widgets:
            form.custom.widgets['branch_code']['_readonly'] = 'true'
 
    if 'password' in form.custom.widgets:
        form.custom.widgets['password']['_type'] = 'password'    
            
    if form.accepted:          
        new_pass = form.vars['password']
        _user = form.vars['username']              

        if current_pass!=new_pass:
            new_hashed_pass = hashlib.sha256(new_pass.encode()).hexdigest()      
            query = """update ac_auth_user set updated_by = '{logged_user}', updated_on='{updated_on}', password = '{password}' where username = '{user}'""".format(logged_user=user,updated_on= datetime.datetime.now() ,password=new_hashed_pass, user = _user)
            db.executesql(query)
        else:
            query = """update ac_auth_user set updated_by = '{logged_user}', updated_on='{updated_on}' where username = '{user}'""".format(logged_user=user,updated_on= datetime.datetime.now(), user = _user)
            db.executesql(query)
        flash.set('User updated successfully','success')          
        redirect(URL('users','users'))
    elif form.errors:
        print(form.errors)
    return dict(form=form,role=role,user=user,branch_name=branch_name)

# @action('users/edit_user/<user_id:int>', method=["GET", "POST"])
# @action.uses(db, session, flash, 'users/edit_user.html')
# def edit_user(user_id=None):
#     if not session.get('user_id'):
#         redirect(URL('login'))
#     else:
#         user = session['user_id']
#         role = session['role']
#         branch_name = session['branch_name']
    
#     assert user_id is not None
#     p = db.ac_auth_user[user_id]
#     if p is None:
#         flash.set("User not found", "warning")
#         redirect(URL('users', 'index'))
    
#     form = Form(db.ac_auth_user, record=p, deletable=False)
    
#     for field in ['username', 'first_name', 'last_name', 'status', 'email', 'password', 'branch_name', 'role', 'contact', 'branch_code']:
#         if field in form.custom.widgets:
#             form.custom.widgets[field]['_class'] = 'form-control form-control-sm'
    
#     if 'password' in form.custom.widgets:
#         form.custom.widgets['password']['_type'] = 'password'
#     if 'branch_code' in form.custom.widgets:
#         form.custom.widgets['branch_code']['_readonly'] = 'true'
    
#     if 'status' in form.custom.widgets:
#         form.custom.widgets['status']['_value'] = 'ACTIVE'
    
    
    
#     if form.accepted:
#         flash.set("User updated successfully", "success")
#         redirect(URL('users', 'users'))
#     elif form.errors:
#         print(form.errors)
    
#     return dict(form=form, role=role, user=user, branch_name=branch_name)


