import json
from py4web import action, Field, redirect, URL, response,request
from py4web.utils.form import Form
import datetime

from yatl.helpers import A
from ..common import db, session, T, cache, auth, flash
from ..common_cid import date_fixed

# voucher list/create 
@action("vouchers/voucher", method=["GET", "POST"])
@action.uses("vouchers/voucher.html", auth, T, db, session)
def voucher():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')
        user_branch_name = session.get('branch_name')
        role = session['role']
        today = datetime.datetime.now().strftime('%Y-%m-%d')

        # Pagination parameters
        page = int(request.query.get('page', 1))
        items_per_page = 25
        offset = (page - 1) * items_per_page

        # Filter parameters
        selected_branch = request.query.get('branch_list', '')
        selected_status = request.query.get('search_status', '')

        # print(selected_branch)

        # Base query
        v_query = "SELECT * FROM ac_voucher_head WHERE cid='TDCLPC'"

        # Apply branch filter
        if user_branch_code != 99:
            v_query += f" AND branch_code={user_branch_code}"
        elif selected_branch:
            branch_code = selected_branch.split('-')[0]            
            if branch_code=='99':
                v_query=v_query
            else:
                v_query += f" AND branch_code={branch_code}"

        # Apply status filter
        if selected_status:
            v_query += f" AND status='{selected_status}'"

        # Apply pagination
        v_query += f" ORDER BY id DESC LIMIT {items_per_page} OFFSET {offset}"

        # print(v_query)

        rows = db.executesql(v_query, as_dict=True)

        for row in rows:
            row['total_amount'] = "{:,.2f}".format(row['total_amount'])

        # Get total number of records for pagination
        total_records_query = "SELECT COUNT(*) FROM ac_voucher_head WHERE cid='TDCLPC'"
        if user_branch_code != 99:
            total_records_query += f" AND branch_code={user_branch_code}"
        elif selected_branch:
            branch_code = selected_branch.split('-')[0]
            if branch_code =='99':
                total_records_query = total_records_query
            else:
                total_records_query += f" AND branch_code={branch_code}"


        if selected_status:
            total_records_query += f" AND status='{selected_status}'"
        total_records = db.executesql(total_records_query)[0][0]
        total_pages = (total_records + items_per_page - 1) // items_per_page

        # Calculate the range of vouchers being displayed
        start_voucher = offset + 1
        end_voucher = min(offset + items_per_page, total_records)
        
        branch_disabled = str(user_branch_code) + '-' + user_branch_name
        branch_names = db.executesql("SELECT concat(branch_code,'-',branch_name) FROM ac_branch order by branch_code asc")

        if request.method == "POST":
            narration = str(request.forms.get('narration')).strip()
            v_date = str(request.forms.get('v_date'))
            v_type = str(request.forms.get('v_type')).strip()
            branch = str(request.forms.get('branch_name')).strip()
            new_sl_value = '0'

            if narration == '':
                flash.set('Please enter narration', 'error')
                redirect(URL('vouchers','voucher'))
            if branch == '':
                flash.set('Please select branch', 'error')
                redirect(URL('vouchers','voucher'))
            if v_type == '':
                flash.set('Please select voucher type', 'error')
                redirect(URL('vouchers','voucher'))
            if v_date == '':
                flash.set('Please select date', 'error')
                redirect(URL('vouchers','vouchers','voucher'))                

            branch_info = branch.split('-')
            voucher_branch_code = branch_info[0]
            voucher_branch_name = branch_info[1]

            result = db.executesql(f"SELECT MAX(sl) FROM ac_voucher_head WHERE sl LIKE '{voucher_branch_code}%'")
            max_sl_value = result[0][0] if result[0][0] is not None else None
            if max_sl_value:
                new_sl_value = str(int(max_sl_value) + 1)
            else:
                new_sl_value = f"{voucher_branch_code}00001"  

                        

            db.ac_voucher_head.insert(
                cid="TDCLPC",
                sl=new_sl_value,
                status="DRAFT",
                narration=narration,
                v_date=v_date,
                v_type=v_type,
                total_amount=0,
                branch_code=voucher_branch_code,
                created_by=username
                # created_on=datetime.datetime.now()
            )
            redirect(URL('vouchers','edit_voucher', new_sl_value))


    return dict(rows=rows, user=username,  role=role, branch_names=branch_names, user_branch_code=user_branch_code, 
                branch_name=user_branch_name, branch_disabled=branch_disabled, today=today, page=page, total_pages=total_pages, 
                start_voucher=start_voucher, end_voucher=end_voucher, total_records=total_records,selected_branch=selected_branch, selected_status=selected_status)


@action('vouchers/edit_voucher/<sl:int>',method=["GET","POST"])
@action.uses(db,'vouchers/edit_voucher.html',session,flash)
def edit_voucher(sl=None):
    
    if not session.get('user_id'):
        redirect(URL('login'))   
    else:
        user=session['user_id']
        role=session['role']
        branch_name=session['branch_name']
        branch_code=session['branch_code']
        assert sl is not None

        # print(sl)
        
        voucher = db(db.ac_voucher_head.sl == sl).select().first()        

        status=voucher.status
        v_date=voucher.v_date 
        v_type=voucher.v_type
        narration=voucher.narration
        voucher_branch_code=voucher.branch_code

        if branch_code != 99 and branch_code != voucher_branch_code:
            flash.set('Access Denied','error')
            redirect(URL('vouchers','voucher'))

        

        branch = db(db.ac_branch.branch_code ==voucher_branch_code ).select().first()
        voucher_branch_name = branch.branch_name

        editable = not (status in ['POSTED', 'CANCEL'] or role in ['VIEWER','ADMIN'])
        can_post = editable and role == 'EDITOR-2nd'

        ref_types = db(db.ac_ref_type).select(db.ac_ref_type.ref_type)

        # rows =  db(db.ac_voucher_details.sl == sl).select()   

        rows_query = """SELECT d.*, r.account_code AS ref_must 
            FROM ac_voucher_details d
            LEFT JOIN ac_account_ref r ON d.account_code = r.account_code
            WHERE d.cid ='TDCLPC' AND d.sl = {sl}
       """.format(sl=sl)
        
        rows = db.executesql(rows_query,as_dict=True)


     
        
    # return dict(sl=sl,status="status",v_date="v_date",v_type="v_type",narration="narration",role=role,user=user,branch_name=branch_name,editable=True,voucher_branch_name="voucher_branch_name",voucher_branch_code="voucher_branch_code")
    return dict(sl=sl,status=status,v_date=v_date,v_type=v_type,narration=narration,rows=rows,role=role,user=user,
                branch_name=branch_name,editable=editable,voucher_branch_name=voucher_branch_name,
                voucher_branch_code=voucher_branch_code,ref_types=ref_types,can_post=can_post)

# check account and add to voucher 
@action('vouchers/check_account_code', method=['GET', 'POST'])
@action.uses(db,session)
def check_account_code():
    sl = request.json.get('sl')
    account_code = request.json.get('acno').strip()
    # account_name = request.json.get('acname').strip()
    v_type = request.json.get('vt').strip()
    v_date = request.json.get('vd').strip()
    drcr = request.json.get('type').strip()
    amount = request.json.get('amount')
    v_branch_code = request.json.get('v_branch_code')
     
    branch_code= session.get('branch_code')
    user= session.get('user_id')
    
    # checking account branchwise
    account_exists = db.executesql("SELECT * FROM ac_account_branch WHERE cid= 'TDCLPC' and account_code = %s AND branch_code in(%s,99)",placeholders=[account_code,v_branch_code])    
    if not account_exists:        
        return json.dumps({'status': 'not_found'}) 
    
    ref_mandatory = bool(db.executesql("select account_code from ac_account_ref where cid = 'TDCLPC' and account_code = %s", placeholders=[account_code]))
        
    # checking cash/bank/corporate type account and calculate balance
    cash_bank = db(db.ac_cash_bank.account_code == account_code).select().first()    

    # fetch account's class name,class code,class type, group code, groupname here
    account = db((db.ac_accounts.account_code == account_code) & (db.ac_accounts.cid == 'TDCLPC')).select().first()
    if account:
        class_code = account.class_code
        class_name = account.class_name
        class_type = account.class_type
        group_code = account.group_code
        group_name = account.group_name
        account_name = account.account_name
    else:
        return json.dumps({'status': 'ac_not_found'})
    
    if v_type == "Contra":        
        if cash_bank:
            # insert into ac_voucher_detail here
            db.ac_voucher_details.insert(
                cid='TDCLPC',
                sl=sl,
                account_code=account_code,
                account_name=account_name,
                amount=amount,
                v_type=v_type,
                v_date=v_date,
                class_code=class_code,
                class_name=class_name,
                class_type=class_type,
                group_code=group_code,
                group_type=group_name,
                # ref_code=ref_code,
                # ref_name=ref_name,
                status='DRAFT',
                branch_code = v_branch_code,
                created_by = user,
                # created_on=datetime.datetime.now(),                
            )                      
            return json.dumps({'status': 'valid', 'ref_mandatory':ref_mandatory})
        else:           
            return json.dumps({'status': 'invalid'})
        
    elif v_type == "Journal":
        # account = db(db.ac_cash_bank.account_code == account_code).select().first()        
        if cash_bank:
            return json.dumps({'status': 'invalid'})
        else:
            # insert into ac_voucher_detail here
            db.ac_voucher_details.insert(
                cid='TDCLPC',
                sl=sl,
                account_code=account_code,
                account_name=account_name,
                amount=amount,
                v_type=v_type,
                v_date=v_date,
                class_code=class_code,
                class_name=class_name,
                class_type=class_type,
                group_code=group_code,
                group_type=group_name,
                # ref_code=ref_code,
                # ref_name=ref_name,
                status='DRAFT',
                branch_code = v_branch_code,
                created_by = user,
                # created_on=datetime.datetime.now(),           
            )                      
            return json.dumps({'status': 'valid', 'ref_mandatory':ref_mandatory})
                
    elif v_type == "Receive":
        if drcr=='debit':
            # account = db(db.ac_cash_bank.account_code == account_code).select().first()
            if cash_bank:                
                # insert into ac_voucher_detail here
                db.ac_voucher_details.insert(
                cid='TDCLPC',
                sl=sl,
                account_code=account_code,
                account_name=account_name,
                amount=amount,
                v_type=v_type,
                v_date=v_date,
                class_code=class_code,
                class_name=class_name,
                class_type=class_type,
                group_code=group_code,
                group_type=group_name,
                # ref_code=ref_code,
                # ref_name=ref_name,
                status='DRAFT',
                branch_code = v_branch_code,
                created_by = user,
                # created_on=datetime.datetime.now(),

            )                      
                return json.dumps({'status': 'valid', 'ref_mandatory':ref_mandatory})
            else:
                return json.dumps({'status': 'invalid'})
        elif drcr=='credit':
            # insert into ac_voucher_detail here
            db.ac_voucher_details.insert(
            cid='TDCLPC',
            sl=sl,
            account_code=account_code,
            account_name=account_name,
            amount=amount,
            v_type=v_type,
            v_date=v_date,
            class_code=class_code,
            class_name=class_name,
            class_type=class_type,
            group_code=group_code,
            group_type=group_name,
            # ref_code=ref_code,
            # ref_name=ref_name,
            status='DRAFT',
            branch_code = v_branch_code,
            created_by = user,
            # created_on=datetime.datetime.now(),
            )                      
            return json.dumps({'status': 'valid', 'ref_mandatory':ref_mandatory})            
        else:
            return json.dumps({'status': 'error'})        
    elif v_type == "Payment":        
        if drcr=='credit':
            # account = db(db.ac_cash_bank.account_code == account_code).select().first()            
            if cash_bank:               
                # insert into ac_voucher_detail here  
                db.ac_voucher_details.insert(
                cid='TDCLPC',
                sl=sl,
                account_code=account_code,
                account_name=account_name,
                amount=amount,
                v_type=v_type,
                v_date=v_date,
                class_code=class_code,
                class_name=class_name,
                class_type=class_type,
                group_code=group_code,
                group_type=group_name,
                # ref_code=ref_code,
                # ref_name=ref_name,
                status='DRAFT',
                branch_code = v_branch_code,
                created_by = user,
                # created_on=datetime.datetime.now(),
            )                                    
                return json.dumps({'status': 'valid', 'ref_mandatory':ref_mandatory})
            else:                
                return json.dumps({'status': 'invalid'})
        elif drcr=='debit':       
            # insert into ac_voucher_detail here
            db.ac_voucher_details.insert(
            cid='TDCLPC',
            sl=sl,
            account_code=account_code,
            account_name=account_name,
            amount=amount,
            v_type=v_type,
            v_date=v_date,
            class_code=class_code,
            class_name=class_name,
            class_type=class_type,
            group_code=group_code,
            group_type=group_name,
            # ref_code=ref_code,
            # ref_name=ref_name,
            status='DRAFT',
            branch_code = v_branch_code,
            created_by = user,
            # created_on=datetime.datetime.now(),
        )                                     
            return json.dumps({'status': 'valid', 'ref_mandatory':ref_mandatory})
    else: 
        return json.dumps({'status': 'error'})
    


# endpoint to post voucher 
@action('vouchers/post_voucher', method=['POST'])
@action.uses(db,session)
def post_voucher():
    data = request.json
    sl = data.get('sl')    
    branch_code = data.get('branch_code')    
    narration = data.get('narration')    
    total = str(data.get('total'))
    user = session['user_id']
    # print(branch_code)
    
    date = datetime.datetime.now()+datetime.timedelta(hours=6)
    # print(date)
    post_time = str(date)
    # print(post_time)

    try:
        v_status = db.executesql("select status from ac_voucher_head where cid ='TDCLPC' and sl ="+sl)

        if v_status[0][0]=="POSTED":
            return dict(success=False, error=str('Voucher already posted'))


        dr = db.executesql("select coalesce(sum(amount),0) as debit from ac_voucher_details where  cid='TDCLPC' and sl = "+sl+" and amount>0")
        debit = dr[0][0]        

        cr = db.executesql("select abs(coalesce(sum(amount),0)) as credit from ac_voucher_details where cid='TDCLPC' and sl = "+sl+" and amount<0")
        credit = cr[0][0]        

        if debit!=credit:
            return dict(success=False, error=str('Debit amount not equal to credit amount'))
  
     

        # checking empty post
        accounts = db.executesql("SELECT account_code, amount FROM ac_voucher_details WHERE cid='TDCLPC' and sl = %s", (sl,))
        if not accounts:
            return dict(success=False, error=str('No accounts found to post'))


        else:
            # Check for insufficient balances 
            for account in accounts:
                account_code = account[0]
                amount = account[1]                
                new_balance=0

                ref_mandatory = db.executesql("select account_code from ac_account_ref where cid = 'TDCLPC' and account_code = %s",placeholders=[account_code])
                if ref_mandatory:
                    # account_total = db.executesql("select amount from ac_voucher_details where cid='TDCLPC' and sl = %s and account_code = %s ", placeholders=[sl,account_code])[0][0]
                    # print("Query amount - "+str(amount))
                    ref_total = db.executesql("select coalesce(sum(amount),0) from ac_voucher_reference where cid='TDCLPC' and sl = %s and account_code = %s ", placeholders=[sl,account_code])[0][0]
                    # print(db._lastsql)
                    # print("acc amt-> "+str(amount))
                    # print("ref amt-> "+str(ref_total))
                    if amount!=ref_total:
                        return dict(success=False, error=str('Reference amount mismatch for account: '+account_code))

                # check cash_bank
                # cash_bank = db(db.ac_cash_bank.account_code == account_code).select().first()
                cash_bank = db.executesql("select account_code from ac_cash_bank where cid='TDCLPC' and account_type <> 'Corporate' and account_code = %s",placeholders=[account_code])

                if cash_bank:   
                    # Fetch the latest balance for the account_code
                    balance_query = db.executesql(
                        "SELECT balance FROM ac_voucher_details WHERE cid='TDCLPC' and account_code = %s and branch_code= %s AND status = 'POSTED' ORDER BY post_time DESC LIMIT 1",
                        (account_code,branch_code)
                    )
                    # print(db._lastsql)
                    
                    if balance_query:
                        current_balance = balance_query[0][0]
                    else:
                        current_balance = 0

                    # Calculate new balance
                    new_balance = current_balance + amount
                    
                    # print(str(account_code)+' Current '+str(current_balance))                    
                    # print(str(account_code)+' New '+str(new_balance))

                    # Check if the new balance is less than zero
                    if new_balance < 0:
                        return dict(success=False, error='Insufficient balance for account: {} Current Balance: {}'.format(account_code,current_balance))                    
                    
            
            # check ref total 
            for account in accounts:
                account_code = account[0]
                amount = account[1]
                
                ref_mandatory = db.executesql("select * from ac_account_ref where cid = 'TDCLPC' and account_code = %s",placeholders=[account_code])
                if ref_mandatory:
                    account_total = db.executesql("select amount from ac_voucher_details where cid='TDCLPC' and sl = %s and account_code = %s ", placeholders=[sl,account_code])[0][0]
                    # print(account_total)
                    ref_total = db.executesql("select coalesce(sum(amount),0) from ac_voucher_reference where cid='TDCLPC' and sl = %s and account_code = %s ", placeholders=[sl,account_code])[0][0]
                    # print(ref_total)
                    if account_total!=ref_total:
                        return dict(success=False, error=str('Reference amount mismatch for account: '+account_code))
            


            # update voucher details with balance 
            for account in accounts:
                account_code = account[0]
                amount = account[1]
                new_balance=0

                # Fetch the current balance for the account_code
                balance_query = db.executesql(
                    "SELECT balance FROM ac_voucher_details WHERE cid ='TDCLPC' and account_code = %s AND branch_code=%s AND status = 'POSTED' ORDER BY post_time DESC LIMIT 1",
                    (account_code,branch_code)
                )
                
                if balance_query:
                    current_balance = balance_query[0][0]
                else:
                    current_balance = 0

                # Calculate new balance                
                new_balance = current_balance + amount
                # print(str(account_code)+' Current '+str(current_balance))
                # print("----------")
                # print(str(account_code)+' Current '+str(new_balance))


                # Update the balance in ac_voucher_details for the given SL and account_code
                update_balance_query = """UPDATE ac_voucher_details SET balance = {bal} WHERE cid='TDCLPC' and sl = {sl} AND account_code = '{account_code}' AND branch_code={branch_code}""".format(bal=new_balance,sl=sl,account_code=account_code,branch_code=branch_code)
                # print(update_balance_query)
                db.executesql(update_balance_query)
                # db.executesql(
                #     "UPDATE ac_voucher_details SET balance = %s WHERE cid='TDCLPC' and sl = %s AND account_code = %s AND branch_code=%s",
                #     (new_balance, sl, account_code,branch_code)
                # )

        
        # db.executesql("UPDATE ac_voucher_head SET total_amount = %s, status= 'POSTED',post_time=%s, post_by=%s, updated_by=%s, upated_on=%s  WHERE sl = %s",(total,user,time,user,date)) 
        db(db.ac_voucher_head.sl == sl).update(
                narration=narration,
                total_amount=debit,
                status='POSTED',
                post_by=user,                   
                updated_by=user,
                updated_on=date,
                post_time= post_time
            )
        
        db.executesql("UPDATE ac_voucher_details SET status = 'POSTED', updated_by = %s, updated_on = %s WHERE sl = %s",(user, date,sl)) 
        db(db.ac_voucher_details.sl == sl).update(
                status='POSTED',
                updated_by=user,
                updated_on=date,
                post_time = post_time
            )
        
        db(db.ac_voucher_reference.sl == sl).update(
                status='POSTED',                
                post_time = post_time
            )
            
        db.commit()
        return dict(success=True)
    except Exception as e:
        db.rollback()
        return dict(success=False, error=str(e))
        
# delete account head from voucher details 
@action('vouchers/delete_voucher_detail', method=['POST'])
@action.uses(db)
def delete_voucher_detail():
    data = request.json
    account_code = data.get('account_code')
    sl = data.get('sl')
    # ref_code = data.get('ref_code')

    # print(ref_code)
    
    if account_code and sl:
        # db.executesql('DELETE FROM ac_voucher_details WHERE  sl = %s and account_code = %s', (account_code, sl))
        # db((db.ac_voucher_details.sl == sl) & (db.ac_voucher_details.account_code == account_code)).delete()
        db.executesql("delete from ac_voucher_details where cid='TDCLPC' and sl= %s and account_code = %s", placeholders=[sl,account_code])
        db.executesql("delete from ac_voucher_reference where cid='TDCLPC' and sl= %s and account_code = %s", placeholders=[sl,account_code])
        return dict(status='success')
    else:
        return dict(status='error', message='No sl provided')
    
    
# endpoint to cancel voucher
@action('vouchers/cancel_voucher', method='POST')
def cancel_voucher():    
    data = request.json
    sl = data.get('sl')    
    
    if not sl:
        return json.dumps({'status': 'error', 'message': 'Sl missing'})
    try:
        
        db.executesql("UPDATE ac_voucher_head SET status='CANCEL' WHERE cid='TDCLPC' and sl = %s", (sl,))
        # print(f"Updated ac_voucher_head to cancel for sl={sl}")
        
        db.executesql("UPDATE ac_voucher_details SET status='CANCEL' WHERE cid='TDCLPC' and sl = %s", (sl,))
        # print(f"Updated ac_voucher_details to cancel for sl={sl}")

        db.executesql("UPDATE ac_voucher_reference SET status='CANCEL' WHERE cid='TDCLPC' and sl = %s", (sl,))

        db.commit()
        return json.dumps({'status': 'success'})
    except Exception as e:
        db.rollback()
        return json.dumps({'status': 'error', 'message': str(e)})    


# endpoint to load reference form modal 
@action('vouchers/load_reference_data', method=['GET'])
@action.uses(db,session)
def load_reference_data():
    sl = request.params.get('sl')
    account_code = request.params.get('account_code')
    role = session['role']
    # print(role)
    
    # checking reference eligible 
    ref_mandatory = db.executesql("select * from ac_account_ref where cid = 'TDCLPC' and account_code = %s",placeholders=[account_code])
    if not ref_mandatory:
        return dict(error="Account is not eligible for reference")   
    
    if not sl or not account_code:
        return dict(error="Missing parameters")
    
    status_row=db.executesql("select status from ac_voucher_head where cid = 'TDCLPC' and sl =%s", placeholders=[sl])
    status = status_row[0][0]
    # print(status)

    is_editable = not (status in ['POSTED', 'CANCEL'] or role in ['VIEWER','ADMIN'])

    ref_row=db.executesql("select ref_type from ac_account_ref where cid = 'TDCLPC' and account_code =%s", placeholders=[account_code])
    ref_type = ref_row[0][0]
    # print(ref_type)
    

    
    query = """select ref_code, ref_name, abs(amount) as amount from ac_voucher_reference where cid = 'TDCLPC' and sl = {sl} and account_code = '{ac_code}'""".format(sl=sl,ac_code=account_code)
    rows = db.executesql(query,as_dict=True)
    # print(query)
    # rows = db(db.ac_voucher_reference.sl == sl and db.ac_voucher_reference.account_code == account_code).select().as_list()
    # print(db._lastsql)
    
    return dict(data=rows, is_editable=is_editable, ref_type=ref_type)
        

# add reference 
@action('vouchers/add_reference', method=['GET', 'POST'])
@action.uses(db,session)
def add_reference():
    user=session['user_id']
    sl = request.json.get('sl')
    account_code = request.json.get('account_code').strip()
    amount = request.json.get('amount')
    
    ref_code = str(request.json.get('ref_code')).strip()
    ref_name = str(request.json.get('ref_name')).strip()      
    
    # checking ref_code
    ref_exists = db.executesql("SELECT * FROM ac_reference WHERE ref_code = %s",placeholders=[ref_code])    
    if not ref_exists:        
        return json.dumps({'status': 'not_found'})     
    
    ref_duplicate = db.executesql("SELECT * FROM ac_voucher_reference WHERE cid='TDCLPC' and sl = %s and account_code=%s and ref_code = %s",placeholders=[sl,account_code,ref_code])    
    if ref_duplicate:        
        return json.dumps({'status': 'ref_duplicate'})     

    # fetch account's v_date, v_type here
    account = db.executesql("select v_date, v_type, account_name,branch_code from ac_voucher_details where sl = %s and account_code = %s",placeholders=[sl,account_code])
    if account:
        v_date =  account[0][0]
        v_type= account[0][1]
        account_name= account[0][2]     
        branch_code= account[0][3]    

    db.ac_voucher_reference.insert(
                cid='TDCLPC',
                sl=sl,
                account_code=account_code,
                account_name=account_name,
                amount=amount,
                v_type=v_type,
                v_date=v_date,                
                ref_code=ref_code,
                ref_name=ref_name,
                branch_code= branch_code,
                status='DRAFT', 
                created_by=user,
                created_on=date_fixed            
            )           
    total_amount = db.executesql("SELECT SUM(amount) FROM ac_voucher_reference WHERE cid='TDCLPC' and account_code = %s AND sl = %s", placeholders=[account_code, sl])[0][0]

    if total_amount is not None:
        # Update the ac_voucher_details table with the calculated sum
        db.executesql("UPDATE ac_voucher_details SET amount = %s WHERE cid='TDCLPC' and sl = %s AND account_code = %s", placeholders=[total_amount, sl, account_code])
        return json.dumps({'status': 'valid'})
    
    return json.dumps({'status': 'error'})           
    

# delete reference 
@action('vouchers/delete_reference', method=['POST'])
@action.uses(db)
def delete_reference():
    data = request.json
    account_code = data.get('account_code')
    sl = data.get('sl')
    ref_code = data.get('ref_code')

    # print(account_code)
    # print(sl)
    # print(ref_code)
    
    if account_code and sl and ref_code:        
        db.executesql("delete from ac_voucher_reference where cid='TDCLPC' and sl= %s and account_code = %s and ref_code = %s", placeholders=[sl,account_code,ref_code])

        total_amount = db.executesql("SELECT coalesce(SUM(amount),0) FROM ac_voucher_reference WHERE cid='TDCLPC' and account_code = %s AND sl = %s", placeholders=[account_code, sl])[0][0]
        if total_amount is not None:
        # Update the ac_voucher_details table with the calculated sum
            db.executesql("UPDATE ac_voucher_details SET amount = %s WHERE cid='TDCLPC' and sl = %s AND account_code = %s", placeholders=[total_amount, sl, account_code])
            return dict(status='success')
    else:
        return dict(status='error', message='Missing Info')
    

# # fetch amount 
# @action('vouchers/fetch_amount', method=['GET'])
# @action.uses(db)
# def fetch_amount():
#     data = request.json
#     account_code = data.get('account_code')
#     sl = data.get('sl')
#     # ref_code = data.get('ref_code')

#     print(account_code)
#     print(sl)
#     # print(ref_code)
    
#     if account_code and sl:        
#         amount_row = db.executesql("select abs(amount) from ac_voucher_detils where cid='TDCLPC' and sl= %s and account_code= %s", placeholders=[sl,account_code])
#         if not amount_row:
#             return dict(status='error', message='Amount not found')
#         else:
#             amount = amount_row[0][0]
#             return dict(status='success', amount=amount)       
#     else:
#         return dict(status='error', message='Missing Info')

# fetch amount from voucher details account 
@action('vouchers/fetch_amount', method=['GET'])
@action.uses(db)
def fetch_amount():
    sl = request.params.get('sl')
    account_code = request.params.get('account_code')
    
    if not sl or not account_code:
        return dict(error='Missing parameters')
    
    row = db((db.ac_voucher_details.sl == sl) & (db.ac_voucher_details.account_code == account_code)).select().first()
    
    if not row:
        return dict(error='No data found')
    
    amount = abs(row.amount)
    return dict(amount=amount)

# print voucher
@action("vouchers/print_voucher/<sl:int>", method=["GET", "POST"])
@action.uses("vouchers/voucher_print.html", auth, T, db, session)
def print_voucher(sl=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:        
        user=session['user_id']
        role=session['role']
        branch_name=session['branch_name']
        assert sl is not None  
           
        time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        query = """select sl,cast(v_date as date) as v_date,v_type,total_amount,status,branch_code,narration, created_by, post_by  from ac_voucher_head where cid='TDCLPC' and sl = {sl} """.format(sl=sl)        
        head= db.executesql(query, as_dict=True)
        
        v_date = head[0]['v_date']
        v_type = head[0]['v_type']
        total = head[0]['total_amount']
        status = head[0]['status']
        branch_code = head[0]['branch_code']
        narration = head[0]['narration']
        created_by = head[0]['created_by']
        post_by = head[0]['post_by']
        # branch_name = head[0]['branch_name']

        # v_date = datetime.datetime.strptime(v_date_db, "%Y-%m-%d").strftime('%d-%b-%Y')   

        amt_words = num2word(total)
        # print(amt_words) 

        # fetching branch address
        branch_query = """select branch_name,address from ac_branch where cid = 'TDCLPC' and branch_code = {branch_code}""".format(branch_code=branch_code)        
        branch_row = db.executesql(branch_query,as_dict=True)
        v_branch_name = branch_row[0]['branch_name']
        v_branch_address = branch_row[0]['address']
        
        # transactio details 
        details_query = """select account_code, account_name,
                            CASE WHEN amount > 0 THEN amount ELSE 0 END AS debit,
                            CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END AS credit
                            from ac_voucher_details where sl= {sl};""".format(sl=sl)
        results = db.executesql(details_query,as_dict=True)

        # totals
        total_query="""select sum(debit)as total_debit, sum(credit) as total_credit from(
                        select COALESCE(sum(amount),0) as debit, 0 as credit from ac_voucher_details where cid='TDCLPC' and sl={sl} and amount>0
                        union all
                        select 0 as debit, abs(COALESCE(sum(amount),0)) as credit from ac_voucher_details where cid='TDCLPC' and sl={sl} and amount<0) as t""".format(sl=sl)
        total_row= db.executesql(total_query,as_dict=True)
        total_debit=total_row[0]['total_debit']
        total_credit=total_row[0]['total_credit']

    return dict(v_date = v_date, v_type=v_type,total=total,time=time,status=status,branch_code=branch_code,branch_name=v_branch_name,results=results,sl=sl,
                address=v_branch_address, amt_words=amt_words,narration=narration,total_debit=total_debit,total_credit=total_credit
                ,created_by=created_by, post_by=post_by)


# preview voucher
@action("vouchers/preview_voucher/<sl:int>", method=["GET", "POST"])
@action.uses("vouchers/preview_voucher.html", auth, T, db, session)
def preview_voucher(sl=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:        
        user=session['user_id']
        role=session['role']
        branch_name=session['branch_name']
        assert sl is not None  
        # print(sl)   
        time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        query = """select sl,cast(v_date as date) as v_date,v_type,total_amount,status,branch_code,narration, created_by, post_by  from ac_voucher_head where cid='TDCLPC'  and sl = {sl} """.format(sl=sl)  
        # print(query)
        head= db.executesql(query, as_dict=True)
        v_date_db = str(head[0]['v_date'])
        v_type = head[0]['v_type']
        total = head[0]['total_amount']
        status = head[0]['status']
        branch_code = head[0]['branch_code']
        narration = head[0]['narration']
        created_by = head[0]['created_by']
        post_by = head[0]['post_by']
        # branch_name = head[0]['branch_name']

        v_date = datetime.datetime.strptime(v_date_db, "%Y-%m-%d").strftime('%d-%b-%Y')    
        amt_words = num2word(total)    

        branch_query = """select branch_name, address from ac_branch where cid = 'TDCLPC' and branch_code = {branch_code}""".format(branch_code=branch_code)
        # print(branch_query)
        branch_row = db.executesql(branch_query,as_dict=True)
        v_branch_name = branch_row[0]['branch_name']
        v_branch_address = branch_row[0]['address']
        # print(branch_name)

        details_query = """select account_code, account_name,
                            CASE WHEN amount > 0 THEN amount ELSE 0 END AS debit,
                            CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END AS credit
                            from ac_voucher_details where cid= 'TDCLPC' and sl= {sl};""".format(sl=sl)
        results = db.executesql(details_query,as_dict=True)

        ref_query = """select  rf.account_code,ac.account_name,rf.ref_code,rf.ref_name, 
                        CASE WHEN amount > 0 THEN amount ELSE 0 END AS debit,
                        CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END AS credit                        
                        from ac_voucher_reference as rf 
                        left join ac_accounts as ac on rf.account_code= ac.account_code
                        where rf.cid= 'TDCLPC' and rf.sl = {sl}""".format(sl=sl)
        results2 = db.executesql(ref_query,as_dict=True)



        # totals
        total_query="""select sum(debit)as total_debit, sum(credit) as total_credit from(
                        select COALESCE(sum(amount),0) as debit, 0 as credit from ac_voucher_details where cid='TDCLPC' and sl={sl} and amount>0
                        union all
                        select 0 as debit, abs(COALESCE(sum(amount),0)) as credit from ac_voucher_details where cid='TDCLPC' and sl={sl} and amount<0) as t""".format(sl=sl)
        total_row= db.executesql(total_query,as_dict=True)
        total_debit=total_row[0]['total_debit']
        total_credit=total_row[0]['total_credit']        

        # merged_results = []
        # for row in results:
        #     has_reference = False
        #     for ref in results2:
        #         if ref['account_code'] == row['account_code']:
        #             ref['account_name'] = f"{ref['account_name']} - {ref['ref_name']}"
        #             merged_results.append(ref)
        #             has_reference = True
        #     if not has_reference:
        #         merged_results.append(row)        
        merged_results = []

        for row in results:
            has_reference = False
            for ref in results2:
                if ref['account_code'] == row['account_code']:
                    merged_results.append(ref)
                    has_reference = True
            if not has_reference:
                row['ref_name']=''
                merged_results.append(row)  
        # return merged_results


    return dict(v_date = v_date, v_type=v_type,total=total,time=time,status=status,branch_code=branch_code,branch_name=v_branch_name,results=results,sl=sl,
                results2=results2,address=v_branch_address,narration=narration,total_debit=total_debit,total_credit=total_credit,
                amt_words=amt_words,merged_results=merged_results, created_by=created_by, post_by=post_by)



# amount in words functions 
#================================= Number To word conversion
def handel_upto_99(number):
    predef = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
              9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
              16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty", 30: "thirty", 40: "forty",
              50: "fifty", 60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety", 100: "hundred", 100000: "lakh",
              10000000: "crore"}
    if number in predef.keys():
        return predef[int(number)]
    else:
        res=''
        if int((int(int(number) / 10)) * 10)>0:
            res += predef[int((int(int(number) / 10)) * 10)]

        if int(int(number) % 10)>0:
            res += ' ' + predef[int(int(number) % 10) ]

        return res


def return_bigdigit(number, devideby):
    predef = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight",
              9: "nine", 10: "ten", 11: "eleven", 12: "twelve", 13: "thirteen", 14: "fourteen", 15: "fifteen",
              16: "sixteen", 17: "seventeen", 18: "eighteen", 19: "nineteen", 20: "twenty", 30: "thirty", 40: "forty",
              50: "fifty", 60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety", 100: "hundred", 1000: "thousand",
              100000: "lakh", 10000000: "crore"}
    if devideby in predef.keys():
        return predef[int(int(number) / devideby)] + " " + predef[int(devideby)]
    else:
        devideby = int(devideby / 10)
        return handel_upto_99(int(int(number) / devideby)) + " " + predef[int(devideby)]


def mainfunction(number):
    dev = {100: "hundred", 1000: "thousand", 100000: "lakh", 10000000: "crore"}
    if int(number) == 0:
        return "Zero"
    if int(number) < 100:
        result = handel_upto_99(number)

    else:
        result = ""
        while int(number) >= 100:
            devideby = 1
            length = len(str(number))

            for i in range(length - 1):
                devideby *= 10

            #            if number%devideby==0:
            #                if devideby in dev:
            #                    return handel_upto_99(number/devideby)+" "+ dev[devideby]
            #                else:
            #                    return handel_upto_99(number/(devideby/10))+" "+ dev[devideby/10]

            res = return_bigdigit(number, devideby)
            result = result + ' ' + res

            if devideby not in dev:
                number = int(number) - (int(devideby / 10) * int((int(number) / int((devideby / 10)))))

            number = int(number) - devideby * int((int(number) / devideby))


        if 0 < int(number) < 100:
            result = result + ' ' + handel_upto_99(number)

    return result


def num2word(num_amount):
    temp_amount = str('{:.2f}'.format(float(num_amount)))

    if '.' in temp_amount:
        amount = temp_amount.split('.')
        taka = amount[0]
        paisa = str(amount[1])[:2]
    else:
        taka = temp_amount
        paisa = '0'


    amtWord = mainfunction(taka)
    paisaWord = mainfunction(paisa)

    if paisaWord == 'Zero':
        total = 'Taka ' + str(amtWord) + ' only'
    else:
        total = 'Taka ' + str(amtWord) + ' and paisa ' + str(paisaWord) + ' only'

    return total

#=================== two digit after decimal point
def easy_format(amount,temp):
    return '{0:.2f}'.format(amount)

def easy_format(num):    
    return '{0:20,.2f}'.format(num)
