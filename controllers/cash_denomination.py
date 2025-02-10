import json
from py4web import action, Field, redirect, URL, response,request
from py4web.utils.form import Form
import datetime
from pydal import DAL, Field
from ..common import db, session, T, cache, auth,  flash
from ..common_cid import date_fixed
import math


# voucher list/create 
@action("cash_denomination/cash_denomination_list", method=["GET", "POST"])
@action.uses("cash_denomination/cash_denomination_list.html", auth, T, db, session)
def cash_denomination_list():
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
        v_query = "SELECT trans_date,branch_code , branch_name , total_amount FROM ac_denomination_head WHERE cid='TDCLPC'"

        if user_branch_code != 99:
            v_query += f" AND branch_code={user_branch_code}"
        else:
            v_query=v_query
            
        # # Apply branch filter
        # if user_branch_code != 99:
        #     v_query += f" AND branch_code={user_branch_code}"
        # elif selected_branch:
        #     branch_code = selected_branch.split('-')[0]            
        #     if branch_code=='99':
        #         v_query=v_query
        #     else:
        #         v_query += f" AND branch_code={branch_code}"

        # # Apply status filter
        # if selected_status:
        #     v_query += f" AND status='{selected_status}'"

        # # Apply pagination
        # v_query += f" ORDER BY id DESC LIMIT {items_per_page} OFFSET {offset}"

        # # print(v_query)

        rows = db.executesql(v_query, as_dict=True)

        # for row in rows:
        #     row['total_amount'] = "{:,.2f}".format(row['total_amount'])

        # # Get total number of records for pagination
        # total_records_query = "SELECT COUNT(*) FROM ac_voucher_head WHERE cid='TDCLPC'"
        # if user_branch_code != 99:
        #     total_records_query += f" AND branch_code={user_branch_code}"
        # elif selected_branch:
        #     branch_code = selected_branch.split('-')[0]
        #     if branch_code =='99':
        #         total_records_query = total_records_query
        #     else:
        #         total_records_query += f" AND branch_code={branch_code}"


        # if selected_status:
        #     total_records_query += f" AND status='{selected_status}'"
        # total_records = db.executesql(total_records_query)[0][0]
        # total_pages = (total_records + items_per_page - 1) // items_per_page

        # # Calculate the range of vouchers being displayed
        # start_voucher = offset + 1
        # end_voucher = min(offset + items_per_page, total_records)
        
        # branch_disabled = str(user_branch_code) + '-' + user_branch_name
        # branch_names = db.executesql("SELECT concat(branch_code,'-',branch_name) FROM ac_branch order by branch_code asc")        


    return dict(rows=rows, user=username,  role=role, 
                # branch_names=branch_names,  end_voucher=end_voucher,  total_records=total_records,branch_disabled=branch_disabled, total_pages=total_pages,start_voucher=start_voucher
                user_branch_code=user_branch_code, 
                branch_name=user_branch_name,  today=today, page=page,
                selected_branch=selected_branch, selected_status=selected_status)


@action("cash_denomination/cash_denomination", method=["GET", "POST"])
@action.uses("cash_denomination/cash_denomination.html", auth, T, db)
def cash_denomination():
    if not session.get('user_id'):
        redirect(URL('login'))  
    elif session['f_password']==1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    elif session['role'] not in ['EDITOR-2nd','EDITOR-1st']:
        redirect(URL('index'))
    else:
        user = session['user_id']
        role = session['role']
        branch_name = session['branch_name']
        branch_code = session['branch_code']

        trx_branch_code=''
        trx_branch_name =''
        account_code =''
        account_name =''

        today = date_fixed
        today_date = today.strftime('%Y-%m-%d')


        account_query = """SELECT ab.account_code,ab.account_name FROM ac_account_branch AS ab 
                            LEFT JOIN ac_cash_bank AS cb ON ab.account_code = cb.account_code
                            WHERE ab.cid ='TDCLPC' and branch_code ={branch_code} AND cb.account_type = 'Cash'
                            """.format(branch_code = branch_code)
        
        account_info = db.executesql(account_query,as_dict=True)

        if branch_code==99:
            trx_branch_code=""
            trx_branch_name=""
            account_code = ""
            account_name = ""
        else:
            trx_branch_code=branch_code
            trx_branch_name=branch_name
            account_code = account_info[0]['account_code']
            account_name = account_info[0]['account_name']
        
        denom_data =  db((db.ac_denomination_details.trans_date == today) & (db.ac_denomination_details.branch_code == branch_code)).select(orderby=db.ac_denomination_details.note_amount)

        total_query = """SELECT SUM(total) as total_amount FROM ac_denomination_details WHERE  cid= 'TDCLPC' AND branch_code = {b_code} AND trans_date = '{trans_date}'""".format(b_code=branch_code, trans_date=today_date)
        total_amount = db.executesql(total_query, as_dict=True)[0]['total_amount']
          

        bank_notes = db(db.ac_bank_note.status == "ACTIVE").select(orderby=db.ac_bank_note.note_amount)     

    return dict(role=role, user=user, trx_branch_name=trx_branch_name,bank_notes=bank_notes,trx_branch_code=trx_branch_code,branch_name=branch_name,
                branch_code=branch_code,account_code=account_code,account_name=account_name,today=today,today_date=today_date,denom_data=denom_data,total_amount=total_amount)



# denomination add (save button)
@action("cash_denomination/save", method=["POST"])
@action.uses(db, session, auth)
def save_cash_denomination():
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
    
    data = request.json  # Get JSON data from the request
    time_now = date_fixed

    account_code = data.get("account_code")
    account_name = data.get("account_name")
    branch_code = data.get("branch_code")
    branch_name = data.get("branch_name")
    total = data.get("tot") 

    bank_notes = data.get("bank_notes",[])
    trans_date= data.get("trans_date")

    
    
    if not bank_notes:
        return dict(success=False, message="No bank notes data provided")
    
    # check multiple entry 
    check_entry = db.executesql("select * from ac_denomination_details where cid = 'TDCLPC' and branch_code = %s and trans_date = %s",(branch_code,trans_date))    
    if check_entry:
        return dict(success=False, message="Data alredy entered for this date")
    
    # checking balance 
    balance_query = db.executesql(
                        "SELECT balance FROM ac_voucher_details WHERE cid='TDCLPC' and account_code = %s and branch_code= %s AND status = 'POSTED' ORDER BY post_time DESC LIMIT 1",
                        (account_code,branch_code)
                )     

    # balance check 
    if balance_query:                    
        current_balance = math.floor(balance_query[0][0])   

        if current_balance != float(total):
            return dict(success=False, message="Balance does not match. Current Balance: "+str(current_balance))
    else:
        return dict(success=False, message="No balance found for this account.")

        
            
    trans_id = f"{branch_code}-{time_now.strftime('%Y%m%d')}"    
    

    try:
        db.ac_denomination_head.insert(
                cid='TDCLPC',               
                total_amount=total,
                trans_id= trans_id,
                account_code=account_code,
                account_name=account_name,
                branch_code=branch_code,
                branch_name=branch_name,
                # trans_date=time_now,
                trans_date=trans_date,
                created_by=user,
                created_on=time_now,                
            )

        for row in bank_notes:            
            db.ac_denomination_details.insert(
                cid='TDCLPC',
                trans_id= trans_id,
                note_code=row.get('note_code'),
                note_amount=row.get('note_amount'),
                qty=row.get('qty'),
                total=row.get('total'),
                branch_code=branch_code,
                branch_name=branch_name,
                # trans_date=time_now,
                trans_date=trans_date,
                created_by=user,
                created_on=time_now,
                account_code=account_code,
                account_name=account_name
            )
        db.commit()
        return dict(success=True, message="Data saved successfully")
    except Exception as e:
        db.rollback()
        return dict(success=False, message=str(e))
    

# denomination view 
@action("cash_denomination/view_denomination/<b_code:int>/<trans_date>", method=["GET", "POST"])
@action.uses("cash_denomination/view_denomination.html", auth, T, db)
def view_denomination(b_code=None, trans_date=None):
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

        if branch_code != 99 and branch_code != b_code:
            flash.set('Access Denied','error')
            redirect(URL('cash_denomination','cash_denomination_list'))

        assert b_code is not None
        assert trans_date is not None

        denom_data_query = """select * from ac_denomination_details where cid ='TDCLPC' and branch_code= {b_code} and trans_date ='{trans_date}'""".format(b_code=b_code, trans_date=trans_date)
        denom_data = db.executesql(denom_data_query, as_dict=True)

        head_info_query = """SELECT total_amount,account_code,account_name,branch_code,branch_name  FROM ac_denomination_head WHERE  cid= 'TDCLPC' AND branch_code = {b_code} AND trans_date = '{trans_date}'""".format(b_code=b_code, trans_date=trans_date)
        head_info = db.executesql(head_info_query, as_dict=True)

        # account_query = """SELECT ab.account_code,ab.account_name,ab.branch_name FROM ac_account_branch AS ab 
        #                     LEFT JOIN ac_cash_bank AS cb ON ab.account_code = cb.account_code
        #                     WHERE ab.cid ='TDCLPC' and branch_code ={branch_code} AND cb.account_type = 'Cash'
        #                     """.format(branch_code = b_code)        

        total_amount = head_info[0]['total_amount']
        account_code = head_info[0]['account_code']
        account_name = head_info[0]['account_name']
        b_name = head_info[0]['branch_name']
        

    return dict(role=role, user=user, branch_name=branch_name, branch_code=branch_code,denom_data=denom_data, trans_date=trans_date,b_code=b_code,
                account_code=account_code,account_name=account_name,b_name=b_name,total_amount=total_amount)

