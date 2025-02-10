import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form,FormStyleBulma
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET
import datetime
import hashlib
"""
This file defines actions, i.e. functions the URLs are mapped into
The @action(path) decorator exposed the function at URL:

    http://127.0.0.1:8000/{app_name}/{path}

If app_name == '_default' then simply

    http://127.0.0.1:8000/{path}

If path == 'index' it can be omitted:

    http://127.0.0.1:8000/

The path follows the bottlepy syntax.

@action.uses('generic.html')  indicates that the action uses the generic.html template
@action.uses(session)         indicates that the action uses the session
@action.uses(db)              indicates that the action uses the db
@action.uses(T)               indicates that the action uses the i18n & pluralization
@action.uses(auth.user)       indicates that the action requires a logged in user
@action.uses(auth)            indicates that the action requires the auth object

session, db, T, auth, and tempates are examples of Fixtures.
Warning: Fixtures MUST be declared with @action.uses({fixtures}) else your app will result in undefined behavior
"""

from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash



@action("index")
@action.uses("index.html", auth, T,session)
def index():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
        
        return dict(username=user,branch_name=branch_name,role=role,user=user)

# login controller
@action("login", method=["GET", "POST"])
@action.uses("login.html", auth, T)
def login():
    if request.method == "POST":
        cid = str(request.forms.get('cid')).strip().upper()      
        username = str(request.forms.get('username')).strip().upper()      
        password = str(request.forms.get('password')).strip()     
        
        # print('cid: '+cid)
        # print('Username: '+username)
        # print('Password: '+password)

        

        if(cid == '' or username == '' or password == ''):
            flash.set('User ID and Password required !', 'warning') 
            redirect(URL('login'))        

        else:
            # sqlQuery = """
            # SELECT * from ac_auth_user where cid='{cid}' and username ='{username}' and password='{password}'  limit 1
            # """.format(username=username,password=password,cid=cid)  
            # print(sqlQuery)         
            # useRecords = db.executesql(sqlQuery, as_dict=True)
            # print(useRecords[0]['branch_code'])            # return sqlQuery
            hashed_password = hashlib.sha256(password.encode()).hexdigest()

            useRecords =  db((db.ac_auth_user.cid == cid) & 
                      (db.ac_auth_user.username == username) & 
                      (db.ac_auth_user.password == hashed_password)).select().first()
            # print(hashed_password)
            
            if not useRecords:
                flash.set('Wrong username or password!', 'error')      
            
            elif useRecords.status=='INACTIVE':
                flash.set('Inactive User', 'error') 
            
            else:                
                session['cid'] = useRecords.cid
                session['user_id'] = useRecords.username                
                
                session['branch_code'] = useRecords.branch_code
                session['branch_name'] = useRecords.branch_name
                session['password'] = useRecords.password 
                session['first_name'] = useRecords.first_name 
                session['role'] = useRecords.role 
                session['f_password'] = useRecords.f_password 

                if useRecords.f_password ==1:
                    flash.set('Please change your password.', 'warning')
                    redirect(URL('change_password_force'))

                else:
                    # session['last_pass_change'] = useRecords[0]['last_password_change'] 
                    flash.set('Hello'+' '+session['first_name'], 'success')

                    # if not useRecords[0]['last_password_change']:
                    #     flash.set('Please change your password.', 'warning')
                    #     redirect(URL('change_password'))

                    redirect(URL("index"))            
                
    
    return locals()


# logout controller
@action("logout")
@action.uses(session)
def logout():
    session.clear()  # Clears all session data
    redirect(URL('login'))  # Redirects to the login page


# endpoint fetch groups by class
@action("get_groups/<class_name>", method=["GET"])
@action.uses(db)
def get_groups(class_name):
    groups = db(db.ac_accounts_group.class_name == class_name).select()
    group_options = [(g.group_name, g.group_name) for g in groups]
    
    return dict(group_options=group_options)  


# End-point to get group code for cash bank
@action("get_group_code", method=["GET"])
@action.uses(db)
def get_group_code():   
    group_name = request.query.get("q")    
    
    group_row = db(db.ac_accounts_group.group_name == group_name).select().first()      
    
    return dict(group_code=group_row.group_code)

# End-point to populate with groups by class in new accounts
@action('get_groups',method=["GET"])
@action.uses(db)
def get_groups():
    selected_class =request.query.get("q")

    groups = db(db.ac_accounts_group.class_name == selected_class).select(db.ac_accounts_group.group_name)
    # print(groups)
    return dict(groups=groups)


# End-point to get class info and generate new group code
@action('get_class_info',method=["GET"])
@action.uses(db)
def get_class_info():   
    class_name = request.query.get("q")    
    
    class_row = db(db.ac_accounts_class.class_name == class_name).select().first()  
    
    max_group_code_row = db(db.ac_accounts_group.class_code == class_row.class_code).select(db.ac_accounts_group.group_code.max()).first()
    max_group_code = max_group_code_row[db.ac_accounts_group.group_code.max()] if max_group_code_row else None

    if max_group_code:
        new_group_code = int(max_group_code) + 1
    else:
        new_group_code = f"{class_row.class_code}001"    
    
    return dict(class_code=class_row.class_code,class_type=class_row.class_type,new_group_code=new_group_code)



# endpoint to fetch account code and name
@action("get_account_info", method=["GET"])
@action.uses(db)
def get_account_names():    
    query = request.params.get('query', '')
    
    suggestions = []
    if query:
        accounts = db(db.ac_accounts.account_name.contains(query)).select()
        for account in accounts:
            suggestions.append({
                'account_name': account.account_name,
                'account_code': account.account_code
            })
    # return json.dumps(suggestions)


# endpoint to save voucher 
@action('save_voucher', method=['POST'])
@action.uses(db,session)
def save_voucher():
    data = request.json
    sl = str(data.get('sl'))
    narration = data.get('narration')    
    total = str(data.get('total'))
    user = session['user_id']
    time = datetime.datetime.now().strftime("%H:%M:%S")
    date = datetime.datetime.now()
    # print(time)


    try:
  
        db.executesql("UPDATE ac_voucher_head SET narration = %s, updated_by=%s,updated_on=%s WHERE sl = %s",(narration,user,date, sl)) 
        
        # if post:
            
        #     # db.executesql("UPDATE ac_voucher_head SET total_amount = %s, status= 'POSTED',post_time=%s, post_by=%s, updated_by=%s, upated_on=%s  WHERE sl = %s",(total,user,time,user,date)) 
        #     db(db.ac_voucher_head.sl == sl).update(
        #             total_amount=total,
        #             status='POSTED',
        #             post_by=user,                   
        #             updated_by=user,
        #             updated_on=date,
        #             post_time= time
        #         )
            
        #     # db.executesql("UPDATE ac_voucher_details SET status = 'POSTED', updated_by = %s, updated_on = %s WHERE sl = %s",(user, date,sl)) 
        #     db(db.ac_voucher_details.sl == sl).update(
        #             status='POSTED',
        #             updated_by=user,
        #             updated_on=date
        #         )
            
        db.commit()
        return dict(success=True)
    except Exception as e:
        db.rollback()
        return dict(success=False, error=str(e))
    

# # endpoint to post voucher 
# @action('post_voucher', method=['POST'])
# @action.uses(db,session)
# def post_voucher():
#     data = request.json
#     sl = data.get('sl')
#     post = data.get('post')
#     narration = data.get('narration')    
#     total = str(data.get('total'))
#     user = session['user_id']
#     time = datetime.datetime.now().strftime("%H:%M:%S")
#     date = datetime.datetime.now()
#     # print(time)


#     try:
#         dr = db.executesql("select coalesce(sum(amount),0) as debit from ac_voucher_details where sl = "+sl+" and amount>0")
#         debit = dr[0][0]
#         print(debit)

#         cr = db.executesql("select abs(coalesce(sum(amount),0)) as credit from ac_voucher_details where sl = "+sl+" and amount<0")
#         credit = cr[0][0]
#         print(credit)

#         if debit!=credit:
#             return dict(success=False, error=str('Debit amount not equal to credit amount'))

  
#         db.executesql("UPDATE ac_voucher_head SET narration = %s, updated_by=%s,updated_on=%s WHERE sl = %s",(narration,user,date, sl)) 

#         # print(debit)
#         # print(credit)
        
#         if post:
            
#             # db.executesql("UPDATE ac_voucher_head SET total_amount = %s, status= 'POSTED',post_time=%s, post_by=%s, updated_by=%s, upated_on=%s  WHERE sl = %s",(total,user,time,user,date)) 
#             db(db.ac_voucher_head.sl == sl).update(
#                     total_amount=total,
#                     status='POSTED',
#                     post_by=user,                   
#                     updated_by=user,
#                     updated_on=date,
#                     post_time= time
#                 )
            
#             # db.executesql("UPDATE ac_voucher_details SET status = 'POSTED', updated_by = %s, updated_on = %s WHERE sl = %s",(user, date,sl)) 
#             db(db.ac_voucher_details.sl == sl).update(
#                     status='POSTED',
#                     updated_by=user,
#                     updated_on=date
#                 )
            
#         db.commit()
#         return dict(success=True)
#     except Exception as e:
#         db.rollback()
#         return dict(success=False, error=str(e))




# # endpoint to cancel voucher
# @action('cancel_voucher', method='POST')
# def cancel_voucher():
    
#     data = request.json
#     sl = data.get('sl')    
    
#     if not sl:
#         return json.dumps({'status': 'error', 'message': 'Sl missing'})
#     try:
        
#         db.executesql("UPDATE ac_voucher_head SET status='CANCEL' WHERE sl = %s", (sl,))
#         # print(f"Updated ac_voucher_head to cancel for sl={sl}")
        
#         db.executesql("UPDATE ac_voucher_details SET status='CANCEL' WHERE sl = %s", (sl,))
#         # print(f"Updated ac_voucher_details to cancel for sl={sl}")

#         db.commit()
#         return json.dumps({'status': 'success'})
#     except Exception as e:
#         db.rollback()
#         return json.dumps({'status': 'error', 'message': str(e)})    


# # endpoint to post voucher  
# @action('post_voucher', method='POST')
# @action.uses(db)
# def post_voucher():
#     data = request.json
#     serial = data.get('sl')
#     tableData = data.get('tableData', [])     
#     vtype=  data.get('v_type')
#     total = str(data.get('totalDebit'))   
    
    
#     if not serial:
#         return json.dumps({'status': 'error', 'message': 'Sl missing'})
    
#     try:
#         # Check if data with the given sl value exists in ac_voucher_head
#         existing_voucher_head = db(db.ac_voucher_head.sl == serial).select().first()

#         if existing_voucher_head:
#             # Delete existing data in ac_voucher_details
#             db(db.ac_voucher_details.sl == serial).delete()
            
        
#         # Insert new data in ac_voucher_details        

#         for row in tableData:
#             account_code = row.get('account_code')
#             account_name = row.get('account_name')
#             debit = row.get('debit', 0)
#             credit = row.get('credit', 0)
#             amount = debit if debit != 0 else credit

#             ref_code=  row.get('ref_code')
#             ref_name=  row.get('ref_name')

#             db.ac_voucher_details.insert(
#                 sl=serial,
#                 account_code=account_code,
#                 account_name=account_name,
#                 amount=amount,
#                 v_type=vtype,
#                 cid="TDCLPC",
#                 status="POSTED",
#                 ref_code = ref_code,
#                 ref_name=ref_name
#             )
            
        
#         # db.executesql("UPDATE ac_voucher_head SET tota_amount='%s',status='POSTED' WHERE sl = %s", (total,serial,))
#         # print(f"Updated ac_voucher_head for sl={serial}")       
#         db.executesql("UPDATE ac_voucher_head SET total_amount = %s, status = 'POSTED' WHERE sl = %s",(total, serial)) 
        

#         db.commit()
#         return json.dumps({'status': 'success'})
#     except Exception as e:
#         db.rollback()
#         return json.dumps({'status': 'error', 'message': str(e)})


# endpoint to check account validity for voucher type for adding account to table in voucher_detail
# @action('check_account_code', method=['GET', 'POST'])
# @action.uses(db,session)
# def check_account_code():
#     sl = request.json.get('sl')
#     account_code = request.json.get('acno').strip()
#     account_name = request.json.get('acname').strip()
#     v_type = request.json.get('vt').strip()
#     v_date = request.json.get('vd').strip()
#     drcr = request.json.get('type').strip()
#     amount = request.json.get('amount')
#     v_branch_code = request.json.get('v_branch_code')
#     ref_code = str(request.json.get('ref_code')).strip()
#     ref_name = str(request.json.get('ref_name')).strip()        
#     branch_code= session.get('branch_code')
#     user= session.get('user_id')
#     datetime_now = datetime.datetime.now()
    
    
#     account_exists = db.executesql("SELECT * FROM ac_account_branch WHERE account_code = %s AND branch_code in(%s,99)",placeholders=[account_code,v_branch_code])
#     # print(db._lastsql)
#     if not account_exists:        
#         return json.dumps({'status': 'not_found'})     
  
#     if ref_name != '':        
#         q = """ select * from ac_reference where ref_code ='{ref}' """.format(ref=ref_code)
#         ref_exists= db.executesql(q)  
#         # print(q) 
#         if not ref_exists:        
#             return json.dumps({'status': 'rf_not_found'})    
    
#     # fetch account's class name,class code,class type, group code, groupname here
#     account = db(db.ac_accounts.account_code == account_code).select().first()
#     if account:
#         class_code = account.class_code
#         class_name = account.class_name
#         class_type = account.class_type
#         group_code = account.group_code
#         group_name = account.group_name
#     else:
#         return json.dumps({'status': 'ac_not_found'})
    
#     if v_type == "Contra":        
#         account = db(db.ac_cash_bank.account_code == account_code).select().first()              
#         # account = db.executesql("select * from ac_cash_bank where account_code=%s",placeholders=account_code)
#         if account: 
#             # insert into ac_voucher_detail here
#             db.ac_voucher_details.insert(
#                 cid='TDCLPC',
#                 sl=sl,
#                 account_code=account_code,
#                 account_name=account_name,
#                 amount=amount,
#                 v_type=v_type,
#                 v_date=v_date,
#                 class_code=class_code,
#                 class_name=class_name,
#                 class_type=class_type,
#                 group_code=group_code,
#                 group_type=group_name,
#                 ref_code=ref_code,
#                 ref_name=ref_name,
#                 status='DRAFT',
#                 branch_code = v_branch_code,
#                 created_by = user,
#                 ceated_on=datetime.datetime.now()
#             )                      
#             return json.dumps({'status': 'valid'})
#         else:           
#             return json.dumps({'status': 'invalid'})
        
#     elif v_type == "Journal":
#         account = db(db.ac_cash_bank.account_code == account_code).select().first()        
#         if account:
#             return json.dumps({'status': 'invalid'})
#         else:
#             # insert into ac_voucher_detail here
#             db.ac_voucher_details.insert(
#                 cid='TDCLPC',
#                 sl=sl,
#                 account_code=account_code,
#                 account_name=account_name,
#                 amount=amount,
#                 v_type=v_type,
#                 v_date=v_date,
#                 class_code=class_code,
#                 class_name=class_name,
#                 class_type=class_type,
#                 group_code=group_code,
#                 group_type=group_name,
#                 ref_code=ref_code,
#                 ref_name=ref_name,
#                 status='DRAFT',
#                 branch_code = v_branch_code,
#                 created_by = user,
#                 created_on=datetime.datetime.now(),
#                 trans_time = datetime_now
#             )                      
#             return json.dumps({'status': 'valid'})
                
#     elif v_type == "Receive":
#         if drcr=='debit':
#             account = db(db.ac_cash_bank.account_code == account_code).select().first()
#             if account:
#                 # insert into ac_voucher_detail here
#                 db.ac_voucher_details.insert(
#                 cid='TDCLPC',
#                 sl=sl,
#                 account_code=account_code,
#                 account_name=account_name,
#                 amount=amount,
#                 v_type=v_type,
#                 v_date=v_date,
#                 class_code=class_code,
#                 class_name=class_name,
#                 class_type=class_type,
#                 group_code=group_code,
#                 group_type=group_name,
#                 ref_code=ref_code,
#                 ref_name=ref_name,
#                 status='DRAFT',
#                 branch_code = v_branch_code,
#                 created_by = user,
#                 ceated_on=datetime.datetime.now()
#             )                      
#                 return json.dumps({'status': 'valid'})
#             else:
#                 return json.dumps({'status': 'invalid'})
#         elif drcr=='credit':
#             account = db(db.ac_accounts.account_code == account_code).select().first()
#             if account:
#                 # insert into ac_voucher_detail here
#                 db.ac_voucher_details.insert(
#                 cid='TDCLPC',
#                 sl=sl,
#                 account_code=account_code,
#                 account_name=account_name,
#                 amount=amount,
#                 v_type=v_type,
#                 v_date=v_date,
#                 class_code=class_code,
#                 class_name=class_name,
#                 class_type=class_type,
#                 group_code=group_code,
#                 group_type=group_name,
#                 ref_code=ref_code,
#                 ref_name=ref_name,
#                 status='DRAFT',
#                 branch_code = v_branch_code,
#                 created_by = user,
#                 ceated_on=datetime.datetime.now()
#             )                      
#                 return json.dumps({'status': 'valid'})
#             else:
                
#                 return json.dumps({'status': 'error'})
#         else:
#             return json.dumps({'status': 'error'})        
#     elif v_type == "Payment":        
#         if drcr=='credit':
#             account = db(db.ac_cash_bank.account_code == account_code).select().first()            
#             if account:
#                 # insert into ac_voucher_detail here  
#                 db.ac_voucher_details.insert(
#                 cid='TDCLPC',
#                 sl=sl,
#                 account_code=account_code,
#                 account_name=account_name,
#                 amount=amount,
#                 v_type=v_type,
#                 v_date=v_date,
#                 class_code=class_code,
#                 class_name=class_name,
#                 class_type=class_type,
#                 group_code=group_code,
#                 group_type=group_name,
#                 ref_code=ref_code,
#                 ref_name=ref_name,
#                 status='DRAFT',
#                 branch_code = v_branch_code,
#                 created_by = user,
#                 ceated_on=datetime.datetime.now()
#             )                                    
#                 return json.dumps({'status': 'valid'})
#             else:                
#                 return json.dumps({'status': 'invalid'})
#         elif drcr=='debit':
            
#             account = db(db.ac_accounts.account_code == account_code).select().first()
#             if account: 
#                 # insert into ac_voucher_detail here
#                 db.ac_voucher_details.insert(
#                 cid='TDCLPC',
#                 sl=sl,
#                 account_code=account_code,
#                 account_name=account_name,
#                 amount=amount,
#                 v_type=v_type,
#                 v_date=v_date,
#                 class_code=class_code,
#                 class_name=class_name,
#                 class_type=class_type,
#                 group_code=group_code,
#                 group_type=group_name,
#                 ref_code=ref_code,
#                 ref_name=ref_name,
#                 status='DRAFT',
#                 branch_code = v_branch_code,
#                 created_by = user,
#                 ceated_on=datetime.datetime.now()
#             )                                     
#                 return json.dumps({'status': 'valid'})
#             else: 
#                 return json.dumps({'status': 'error'})
#         else:            
#             return json.dumps({'status': 'error'})
#     else:             
#          return json.dumps({'status': 'error'})


#edit voucher
@action('edit_voucher/<sl:int>',method=["GET","POST"])
@action.uses(db,'edit_voucher.html',session)
def edit_voucher(sl=None):
    
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        user=session['user_id']
        role=session['role']
        branch_name=session['branch_name']
        assert sl is not None
        
        voucher = db(db.ac_voucher_head.sl == sl).select().first()        

        status=voucher.status
        v_date=voucher.v_date 
        v_type=voucher.v_type
        narration=voucher.narration
        voucher_branch_code=voucher.branch_code

        branch = db(db.ac_branch.branch_code ==voucher_branch_code ).select().first()
        voucher_branch_name = branch.branch_name
        


        editable = not (status in ['POSTED', 'CANCEL'] or role in ['VIEWER','ADMIN'])

        ref_types = db(db.ac_ref_type).select(db.ac_ref_type.ref_type)

        rows =  db(db.ac_voucher_details.sl == sl).select()

        
        
    
    return dict(sl=sl,status=status,v_date=v_date,v_type=v_type,narration=narration,rows=rows,role=role,user=user,branch_name=branch_name,editable=editable,voucher_branch_name=voucher_branch_name,voucher_branch_code=voucher_branch_code,ref_types=ref_types)

# @action("edit_voucher_details_", method=["POST"])
# @action.uses(db)
# def edit_voucher_details_():
#     data = request.json
#     if data:

#         # serial = str(data.get('sl'))
#         serial = data.get('sl')
#         tableData = data.get('tableData', [])     
#         vtype=  data.get('v_type')        

#         # Here first check status
        
#         existing_voucher_head = db(db.ac_voucher_head.sl == serial).select().first()
#         if existing_voucher_head:
            
#             v_status= existing_voucher_head.status
#             if v_status=="POSTED" or v_status=="CANCEL":
#                 return dict(status=v_status)
#             else:

#                 #here update table ac_voucher_head 
#                 db(db.ac_voucher_head.sl == serial).update(v_type=vtype)
#                 # print(f"Updated v_type in ac_voucher_head for sl={serial}")

#                 db(db.ac_voucher_details.sl == serial).delete()
#                 # print(f"Deleted existing records in ac_voucher_details for sl={serial}")     

#                 for row in tableData:                    

#                     account_code = row.get('account_code')
#                     debit = row.get('debit', 0)
#                     credit = row.get('credit', 0)
#                     amount = debit if debit != 0 else credit
                    
#                     db.ac_voucher_details.insert(
#                         sl=serial,
#                         account_code=account_code,
#                         amount=amount,
#                         v_type=vtype,
#                         cid="TDCLPC",
#                         status="DRAFT"
#                     )
                    
#                     # flash.set('Error', 'warning')
#                 return dict(status="success")
            
# @action('cedit_voucher_post', method='POST')
# def edit_voucher_post():    
#     data = request.json
#     sl = data.get('sl')    
    
#     if not sl:
#         return json.dumps({'status': 'error', 'message': 'Sl missing'})
#     try:
        
#         db.executesql("UPDATE ac_voucher_head SET status='POSTED' WHERE sl = %s", (sl,))
#         # print(f"Updated ac_voucher_head to cancel for sl={sl}")
        
#         db.executesql("UPDATE ac_voucher_details SET status='POSTED' WHERE sl = %s", (sl,))
#         # print(f"Updated ac_voucher_details to cancel for sl={sl}")

#         db.commit()
#         return json.dumps({'status': 'success'})
#     except Exception as e:
#         db.rollback()
#         return json.dumps({'status': 'error', 'message': str(e)})
    

# End-point to get class info and generate new group code
@action('get_branch_code',method=["GET"])
@action.uses(db)
def get_branch_code():   
    branch_name = request.query.get("q")        
    branch_row = db(db.ac_branch.branch_name == branch_name).select().first()  
    branch_code=branch_row.branch_code    
    
    return dict(branch_code=branch_code)

@action('fetch_account_info', method=['GET'])
@action.uses(db)
def fetch_account_info():
    term = request.params.get('term')
    if term:
        # rows = db(db.ac_accounts.account_name.like(f'%{term}%')).select(db.ac_accounts.account_name)
        # suggestions = [row.account_name for row in rows]
        ###################
        # rows = db(db.ac_accounts.account_name.like(f'%{term}%')).select(db.ac_accounts.account_code, db.ac_accounts.account_name)
        # suggestions = [f"{row.account_code}|{row.account_name}" for row in rows]
        query = """
            SELECT account_code, account_name from ac_accounts where lower(account_code) like lower('%{term}%') or lower(account_name) like lower('%{term}%') limit 20
            """.format(term=term)
        rows = db.executesql(query)
        suggestions = [f"{row[0]}|{row[1]}" for row in rows]
        return json.dumps(suggestions)
    return json.dumps([])


# fetch account name info for autofill suggestion
@action('fetch_account_voucher_detail', method=['GET'])
@action.uses(db,session)
def account_name_autocomplete_vd():
    term = request.params.get('term')  
    
    if term:
        if session.get('user_id'):
            username=session['user_id']
            branch_code= session['branch_code']
            
            query = """
                SELECT account_code, account_name from ac_account_branch where lower(account_name) like lower('%{term}%') and branch_code in (99,{branch_code}) limit 10
                """.format(term=term, branch_code=branch_code)
            rows = db.executesql(query)
            suggestions = [f"{row[0]}|{row[1]}" for row in rows]
            return json.dumps(suggestions)
    return json.dumps([])


@action('fetch_account_code_voucher_detail', method=['GET'])
@action.uses(db,session)
def account_code_autocomplete_vd():
    term = request.params.get('term')  
    v_branch_code = request.params.get('v_branch_code')      
    if term:
        if session.get('user_id'):
            username=session['user_id']
            branch_code= str(session['branch_code'])            
            
            query = """
                SELECT account_code, account_name from ac_account_branch where cid='TDCLPC' and branch_code in (99,{v_branch_code}) and (account_code like '%{term}%' or account_name like '%{term}%') limit 10
                """.format(term=term, v_branch_code=v_branch_code)
            # print(query)
            rows = db.executesql(query)
            suggestions = [f"{row[0]}|{row[1]}" for row in rows]
            return json.dumps(suggestions)
    return json.dumps([])


# fetch reference for autofill suggestion
@action('fetch_reference', method=['GET'])
@action.uses(db)
def reference_autocomplete():
    term = request.params.get('term')
    r_type = request.params.get('r_type')    
    if term:                    
        query = """
            SELECT ref_code,ref_name from ac_reference where cid= 'TDCLPC' and ref_type = '{rtype}' and  (lower(ref_name) like lower('%{term}%') or lower(ref_code) like lower('%{term}%')) limit 10
            """.format(term=term, rtype=r_type)           
        # print(query)
            
        rows = db.executesql(query)
        suggestions = [f"{row[0]}|{row[1]}" for row in rows]
        return json.dumps(suggestions)
    return json.dumps([])

# fetch reference for autofill suggestion
@action('fetch_reference2', method=['GET'])
@action.uses(db)
def reference_autocomplete2():
    term = request.params.get('term')
    print(term)   
    if term:                    
        query = """
            SELECT ref_code,ref_name from ac_reference where  ref_name like '%{term}%' or ref_code like '%{term}%' limit 10
            """.format(term=term)   
        print(query)
    
        rows = db.executesql(query)
        suggestions = [f"{row[0]}|{row[1]}" for row in rows]
        return json.dumps(suggestions)
    return json.dumps([])



# from io import StringIO
# from py4web import response

# @action('download_accounts', method=['GET'])
# @action.uses(db, session)
# def download_accounts():
#     # Use raw SQL to select specific columns
#     query = "SELECT CONCAT('''',account_code ),account_name,group_code,group_name,class_code,class_name,class_type,created_on FROM ac_accounts"  
#     rows = db.executesql(query)
    
#     # Create an in-memory text stream to hold the CSV data
#     csv_stream = StringIO()
    
#     # Write the header to the CSV
#     csv_stream.write("Account Code,account_name,group_code,group_name,class_code,class_name,class_type,created_on\n")  # Replace with your actual column names
    
#     # Write the rows to the CSV stream
#     for row in rows:
#         csv_stream.write(','.join(map(str, row)) + "\n")
    
#     # Get the content of the CSV file
#     csv_content = csv_stream.getvalue()
#     csv_stream.close()
    
#     # Set the response headers to trigger a file download
#     response.headers['Content-Type'] = 'text/csv'
#     response.headers['Content-Disposition'] = 'attachment; filename="accounts.csv"'
    
#     # Return the CSV content as a downloadable file
#     return csv_content



# @action('delete_voucher_detail', method=['POST'])
# @action.uses(db)
# def delete_voucher_detail():
#     data = request.json
#     account_code = data.get('account_code')
#     sl = data.get('sl')
#     ref_code = data.get('ref_code')

#     # print(ref_code)
    
#     if account_code and sl:
#         # db.executesql('DELETE FROM ac_voucher_details WHERE  sl = %s and account_code = %s', (account_code, sl))
#         # db((db.ac_voucher_details.sl == sl) & (db.ac_voucher_details.account_code == account_code)).delete()
#         db.executesql('delete from ac_voucher_details where sl= %s and account_code = %s and ref_code = %s', placeholders=[sl,account_code,ref_code])
#         return dict(status='success')
#     else:
#         return dict(status='error', message='No sl provided')
    
# endpoint to generate new sl - voucher head
@action('get_sl',method=["GET"])
@action.uses(db)
def get_sl():   
    branch_code = request.query.get("q")    
    
    sql = "SELECT MAX(sl) FROM ac_voucher_head WHERE cast(sl as varchar) LIKE '"+branch_code+"%'"
    
    max_sl_row = db.executesql(sql)   

    max_sl = max_sl_row[0][0] if max_sl_row[0][0] else None

    if max_sl:        
        new_sl = int(max_sl) + 1        
    else:        
        new_sl = f"{branch_code}00001"    
    return dict(newsl=new_sl)


# change password
@action("change_password", method=["GET", "POST"])
@action.uses("change_pass.html", T, db,session,flash)
def change_pass():   
    if not session.get('user_id'):
        redirect(URL('login'))       

    else:
        user=session['user_id']
        role=session['role']
        branch_name=session['branch_name']
        # password=session['password']
        query = """select password from ac_auth_user where username = '{user}'""".format(user=user)
        password = db.executesql(query)[0][0]
        
        if request.method == "POST":
            old_pass = str(request.forms.get('old_pass')).strip()      
            new_pass = str(request.forms.get('new_pass')).strip()    
            new_pass_con = str(request.forms.get('new_pass_con')).strip()  

            hashed_new_pass = hashlib.sha256(new_pass.encode()).hexdigest()
            hashed_old_pass = hashlib.sha256(old_pass.encode()).hexdigest()

            if len(new_pass) < 8:
                flash.set('Password must be at least 8 charachters','error')
                redirect(URL('change_password'))
            
            elif old_pass=='' or new_pass=='' or new_pass_con=='':
                flash.set('Please fill all fields','error')
                redirect(URL('change_password'))
            
            elif hashed_old_pass!=password:
                flash.set('Incorrect password','error')
                redirect(URL('change_password'))

            elif hashed_new_pass==password:
                flash.set('New password cannot be same as old password','error')
                redirect(URL('change_password'))            
            
            elif new_pass!=new_pass_con:
                flash.set('Passwords do not match','error')
                redirect(URL('change_password'))
            else:
                # hashed_new_pass = hashlib.sha256(new_pass.encode()).hexdigest()
                # print(hashed_new_pass)
                db(db.ac_auth_user.username == user).update(
                    password=hashed_new_pass,
                    last_password_change=datetime.datetime.now(),     
                    f_password=0               
                )
                flash.set('Password changed successfully, please login again','success')
                redirect(URL('logout'))  
    return dict(role=role,user=user,branch_name=branch_name)



# change password
@action("change_password_force", method=["GET", "POST"])
@action.uses("change_pass_force.html", T, db,session,flash)
def change_pass_force():   
    if not session.get('user_id'):
        redirect(URL('login'))       

    else:
        user=session['user_id']
        role=session['role']
        branch_name=session['branch_name']
        password=session['password']
        
        if request.method == "POST":
            old_pass = str(request.forms.get('old_pass')).strip()      
            new_pass = str(request.forms.get('new_pass')).strip()    
            new_pass_con = str(request.forms.get('new_pass_con')).strip()  

            hashed_new_pass = hashlib.sha256(new_pass.encode()).hexdigest()
            hashed_old_pass = hashlib.sha256(old_pass.encode()).hexdigest()

            if len(new_pass) < 8:
                flash.set('Password must be at least 8 charachters','error')
                redirect(URL('change_password'))
            
            elif old_pass=='' or new_pass=='' or new_pass_con=='':
                flash.set('Please fill all fields','error')
                redirect(URL('change_password'))
            
            elif hashed_old_pass!=password:
                flash.set('Incorrect password','error')
                redirect(URL('change_password'))

            elif hashed_new_pass==password:
                flash.set('New password cannot be same as old password','error')
                redirect(URL('change_password'))
            
            elif new_pass!=new_pass_con:
                flash.set('Passwords do not match','error')
                redirect(URL('change_password'))
            else:                  
                db(db.ac_auth_user.username == user).update(
                    password=hashed_new_pass,
                    last_password_change=datetime.datetime.now(),     
                    f_password=0               
                )
                flash.set('Password changed successfully, please login again', 'success')
                redirect(URL('logout'))  
    return dict(role=role,user=user,branch_name=branch_name)


    

    
 








    
    
    
    






    










    








        





