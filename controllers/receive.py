import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET
import datetime


from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# # Create Product Receive Entry
# @action("receive/new_receive", method=["GET", "POST"])
# @action.uses("receive/new_receive.html", auth, T, db)
# def new_receive():
#     if not session.get('user_id'):
#         redirect(URL('login'))  
#     elif session['f_password']==1:
#         flash.set('Please change your password.', 'warning')
#         redirect(URL('change_password_force'))
#     else:
#         user = session['user_id']
#         role = session['role']
#         branch_name = session['branch_name']
#         search_term = request.query.get('search_term', '')
#         search_by = request.query.get('search_by', 'receive_code')
        
#         if search_term:
#             if search_by == 'receive_code':
#                 query = "SELECT * FROM product_receive_head WHERE cid = 'TDCLPC' and receive_code LIKE '%{}%'".format(search_term)
#             elif search_by == 'item_code':
#                 query = "SELECT * FROM product_receive_head WHERE cid = 'TDCLPC' and item_code LIKE '%{}%'".format(search_term)
#         else:
#             query = "SELECT * FROM product_receives"
        
#         print(query)
#         rows = db.executesql(query, as_dict=True)

#         # db.receive_code.created_by.default = user
    
#     # Define form
#     form = Form(db.product_receives)

#     # Apply custom styles to form fields
#     if 'receive_code' in form.custom.widgets:
#         form.custom.widgets['receive_code']['_class'] = 'form-control form-control-sm'
#     if 'item_code' in form.custom.widgets:
#         form.custom.widgets['item_code']['_class'] = 'form-control form-control-sm select-custom'
#     if 'supplier_code' in form.custom.widgets:
#         form.custom.widgets['supplier_code']['_class'] = 'form-control form-control-sm select-custom'
#     if 'unit_name' in form.custom.widgets:
#         form.custom.widgets['unit_name']['_class'] = 'form-control form-control-sm select-custom'
#     if 'quantity_received' in form.custom.widgets:
#         form.custom.widgets['quantity_received']['_class'] = 'form-control form-control-sm'
#     if 'receive_date' in form.custom.widgets:
#         form.custom.widgets['receive_date']['_class'] = 'form-control form-control-sm'
#     if 'remarks' in form.custom.widgets:
#         form.custom.widgets['remarks']['_class'] = 'form-control form-control-sm'
    
#     # Handle form submission
#     if form.accepted:
#         flash.set('Product receive entry added successfully', 'success')
#         redirect(URL('receive/new_receive'))
#         # print()

#     return dict(form=form, rows=rows,search_term=search_term, search_by=search_by, role=role, user=user, branch_name=branch_name)

# Edit Product Receive Entry
# @action('receive/edit_receive/<receive_id:int>', method=["GET", "POST"])
# @action.uses(db, session, flash, "receive/edit_receive.html")
# def edit_receive(receive_id=None):
#     if not session.get('user_id'):
#         redirect(URL('login'))
#     else:
#         user = session['user_id']
#         role = session['role']
#         branch_name = session['branch_name']

#     assert receive_id is not None
#     record = db.product_receives[receive_id]
    
#     if record is None:
#         redirect(URL('index'))
    
#     form = Form(db.product_receives, record=record, deletable=False)

#     # Apply custom styles to form fields
#     if 'receive_code' in form.custom.widgets:
#         form.custom.widgets['receive_code']['_class'] = 'form-control form-control-sm'
#     if 'item_code' in form.custom.widgets:
#         form.custom.widgets['item_code']['_class'] = 'form-control form-control-sm select-custom'
#     if 'supplier_code' in form.custom.widgets:
#         form.custom.widgets['supplier_code']['_class'] = 'form-control form-control-sm select-custom'
#     if 'unit_name' in form.custom.widgets:
#         form.custom.widgets['unit_name']['_class'] = 'form-control form-control-sm select-custom'
#     if 'quantity_received' in form.custom.widgets:
#         form.custom.widgets['quantity_received']['_class'] = 'form-control form-control-sm'
#     if 'receive_date' in form.custom.widgets:
#         form.custom.widgets['receive_date']['_class'] = 'form-control form-control-sm'
#     if 'remarks' in form.custom.widgets:
#         form.custom.widgets['remarks']['_class'] = 'form-control form-control-sm'
    
#     if form.accepted:
#         flash.set('Product receive entry updated successfully', 'success')
#         redirect(URL('receive/new_receive'))

#     return dict(form=form, role=role, user=user, branch_name=branch_name)

# # Delete Product Receive Entry
# @action('receive/delete_receive/<receive_id:int>', method=["GET", "POST"])
# @action.uses(db, session, flash)
# def delete_receive(receive_id=None):
#     if not session.get('user_id'):
#         redirect(URL('login'))

#     assert receive_id is not None
#     record = db.product_receives[receive_id]

#     if record:
#         db(db.product_receives.id == receive_id).delete()
#         flash.set('Product receive entry deleted successfully', 'success')
#     else:
#         flash.set('Error: Entry not found', 'error')

#     redirect(URL('receive/new_receive'))

#     return dict()

# voucher list/create 
@action("receive/receive", method=["GET", "POST"])
@action.uses("receive/receive.html", auth, T, db, session)
def receive():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')
        user_branch_name = session.get('branch_name')
        role = session['role']
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        today2 = datetime.datetime.now().strftime('%Y%m%d')

        # Pagination parameters
        # page = int(request.query.get('page', 1))
        # items_per_page = 25
        # offset = (page - 1) * items_per_page

        # Filter parameters
        selected_branch = request.query.get('branch_list', '')
        selected_status = request.query.get('search_status', '')

        # print(selected_branch)

        # Base query
        v_query = "SELECT * FROM product_receive_head  "

        # Apply branch filter
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

        # print(v_query)

        rows = db.executesql(v_query, as_dict=True)

        for row in rows:
            row['total_amount'] = "{:,.2f}".format(row['total_amount'])

        

        # Get total number of records for pagination
        total_records_query = "SELECT COUNT(*) FROM product_receive_head WHERE "
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

        # Calculate the range of vouchers being displayed
        # start_voucher = offset + 1
        # end_voucher = min(offset + items_per_page, total_records)
        
        branch_disabled = str(user_branch_code) + '-' + user_branch_name
        branch_names = db.executesql("SELECT concat(branch_code,'-',branch_name) FROM ac_branch order by branch_code asc")

        suppliers = db.executesql("SELECT concat(supplier_code,'|',supplier_name) FROM supplier ")

        # print(suppliers)

        if request.method == "POST":
            desc = str(request.forms.get('description')).strip()
            rcv_date = str(request.forms.get('rcv_date'))
            branch = str(request.forms.get('branch_name')).strip()
            supplier = str(request.forms.get('supplier')).strip()

            supplier_code = supplier.split('|')[0]
            supplier_name = supplier.split('|')[1]

            # print(supplier_code)
            # print(supplier_name)

            new_sl_value = '0'

            if desc == '':
                flash.set('Please enter description', 'error')
                redirect(URL('vouchers','voucher'))
            if branch == '':
                flash.set('Please select branch', 'error')
                redirect(URL('vouchers','voucher'))            
            if rcv_date == '':
                flash.set('Please select date', 'error')
                redirect(URL('vouchers','vouchers','voucher'))                

            branch_info = branch.split('-')
            voucher_branch_code = branch_info[0]
            voucher_branch_name = branch_info[1]

            result = db.executesql(f"SELECT MAX(receive_code)+1 FROM product_receive_head WHERE branch_code = "+voucher_branch_code)
            new_sl_value = result[0][0] if result[0][0] is not None else 1
            # if max_sl_value:
            #     new_sl_value = str(int(max_sl_value) + 1)
            # else:
            #     new_sl_value = f"{voucher_branch_code}00001"              

                        

            db.product_receive_head.insert(
                cid="TDCLPC",
                receive_code=new_sl_value,
                receive_date=rcv_date,
                status="DRAFT",
                desc=desc,
                supplier_code=supplier_code,
                supplier_name=supplier_name,                
                total_amount=0,
                branch_code=voucher_branch_code,
                created_by=username
                # created_on=datetime.datetime.now()
            )
            redirect(URL('receive','edit_receive', new_sl_value))
            # redirect(URL('receive','receive'))


    return dict(rows=rows, user=username,  role=role, branch_names=branch_names, user_branch_code=user_branch_code, 
                branch_name=user_branch_name, branch_disabled=branch_disabled, today=today,
                #   page=page, total_pages=total_pages, 
                # start_voucher=start_voucher, end_voucher=end_voucher, total_records=total_records,
                selected_branch=selected_branch, selected_status=selected_status,suppliers=suppliers
                )

@action('receive/edit_receive/<sl:int>',method=["GET","POST"])
@action.uses(db,'receive/edit_receive.html',session,flash)
def edit_receive(sl=None):
    
    if not session.get('user_id'):
        redirect(URL('login'))   
    else:
        user=session['user_id']
        role=session['role']
        branch_name=session['branch_name']
        branch_code=session['branch_code']
        assert sl is not None

        # print(sl)
        
        receive = db(db.product_receive_head.receive_code == sl).select().first()        

        status=receive.status
        receive_date=receive.receive_date 
        desctiption=receive.desc
        supplier_name=receive.supplier_name
        receive_branch_code=receive.branch_code
        receive_branch_name=receive.branch_name
        

        if branch_code != 99 and branch_code != receive_branch_code:
            flash.set('Access Denied','error')
            redirect(URL('receive','receive'))

        

        branch = db(db.ac_branch.branch_code ==receive_branch_code ).select().first()
        voucher_branch_name = branch.branch_name

        editable = not (status in ['POSTED', 'CANCEL'])

        ref_types = db(db.ac_ref_type).select(db.ac_ref_type.ref_type)

        # rows =  db(db.ac_voucher_details.sl == sl).select()   

        rows_query = """select * from product_receive_details where receive_code = {rcv_code} """.format(rcv_code=sl)
        
        rows = db.executesql(rows_query,as_dict=True)


     
        
    # return dict(sl=sl,status="status",v_date="v_date",v_type="v_type",narration="narration",role=role,user=user,branch_name=branch_name,editable=True,voucher_branch_name="voucher_branch_name",voucher_branch_code="voucher_branch_code")
    return dict(sl=sl,status=status,description=desctiption,rows=rows,role=role,user=user,
                branch_name=branch_name,editable=editable,receive_branch_name=receive_branch_name,
                ref_types=ref_types,supplier_name = supplier_name,
                receive_date=receive_date, receive_code = sl, receive_branch_code = receive_branch_code)

# auto suggest item 
@action('receive/fetch_item_code_name', method=['GET'])
@action.uses(db,session)
def fetch_item_code_name():
    term = request.params.get('term')  
    if term:
        if session.get('user_id'):
            username=session['user_id']
            branch_code= str(session['branch_code'])            
            
            query = """
                SELECT item_code, item_name from inventory_items where  (item_code like '%{term}%' or item_name like '%{term}%') limit 10
                """.format(term=term)
            # print(query)
            rows = db.executesql(query)
            suggestions = [f"{row[0]}|{row[1]}" for row in rows]
            return json.dumps(suggestions)
    return json.dumps([])


@action('receive/add_item', method=['GET', 'POST'])
@action.uses(db,session)
def add_item():
    sl = request.json.get('sl')
    item_code = request.json.get('item_code').strip()
    item_name = request.json.get('item_name').strip()
    receive_date = request.json.get('receive_date').strip()
    qty = request.json.get('qty')
    r_branch_code = request.json.get('v_branch_code')
    r_branch_name = request.json.get('v_branch_name')
     
    branch_code= session.get('branch_code')
    user= session.get('user_id')
    
    # checking account branchwise
    item_exists = db.executesql("SELECT item_code,trade_price FROM inventory_items WHERE item_code = %s ",placeholders=[item_code])    
    if not item_exists:        
        return json.dumps({'status': 'not_found'}) 
    else:
        trade_price = item_exists[0][1]
        total = trade_price* float(qty) 
        db.product_receive_details.insert(
                    cid='TDCLPC',
                    receive_code=sl,
                    item_code=item_code,
                    item_name=item_name,
                    quantity=qty,
                    receive_date=receive_date,  
                    trade_price=  trade_price,                
                    status='DRAFT',
                    total=total,
                    branch_code = r_branch_code,
                    created_by = user,

                )     
        return json.dumps({'status': 'valid','total':total,'trade_price':trade_price})
    # else:
    #     return json.dumps({'status': 'invalid'})
    

    # delete item head from receive details 
@action('receive/delete_receive_detail', method=['POST'])
@action.uses(db)
def delete_receive_detail():
    data = request.json
    item_code = data.get('item_code')
    sl = data.get('sl')
    # ref_code = data.get('ref_code')

    # print(ref_code)
    
    if item_code and sl:        
        delete_query = """delete from product_receive_details WHERE receive_code = {rcv_code} AND item_code = '{itm_code}'""".format(rcv_code=sl,itm_code=item_code)
        db.executesql(delete_query)
        return dict(status='success')
    else:
        return dict(status='error', message='No receive code provided')
    

    # endpoint to post receive 
@action('receive/post_receive', method=['POST'])
@action.uses(db,session)
def post_receive():
    data = request.json
    sl = data.get('sl')    
    branch_code = data.get('branch_code')    
    receive_date = data.get('receive_date')    
    description = data.get('description')    
    total = str(data.get('total'))
    user = session['user_id']
    # print(branch_code)
    
    date = datetime.datetime.now()
    # print(date)
    post_time = str(date)


    try:
        v_status = db.executesql("select status from product_receive_head where receive_code ="+sl)

        if v_status[0][0]=="POSTED":
            return dict(success=False, error=str('Receive already posted'))    
     

        # checking empty post
        items = db.executesql("SELECT item_code, quantity FROM product_receive_details WHERE receive_code = %s", (sl,))
        if not items:
            return dict(success=False, error=str('No items found'))

        else:
            # Check for insufficient balances 
            for item in items:
                item_code = item[0]
                qty = item[1]      

                db.product_stock.insert(
                    trx_code=sl,
                    trx_date=receive_date,
                    trx_type="Receive",
                    item_code=item_code,
                    quantity=qty,                
                    branch_code=branch_code,
                )  
                      
        db(db.product_receive_head.receive_code == sl).update(
                desc=description,
                total_amount=total,
                status='POSTED',
                post_by=user,                   
                updated_by=user,
                updated_on=date,
                post_time= post_time
            )
        
        db(db.product_receive_details.receive_code == sl).update(
                status='POSTED',
                updated_by=user,
                updated_on=date,
                post_time = post_time,
            )       
            
        db.commit()
        return dict(success=True)
    except Exception as e:
        db.rollback()
        return dict(success=False, error=str(e))
    
# endpoint to cancel receive
@action('receive/cancel_receive', method='POST')
@action.uses(db,session)
def cancel_receive():    
    user = session['user_id']
    data = request.json
    sl = data.get('sl')    

    # print(sl)
    
    if not sl:
        return json.dumps({'status': 'error', 'message': 'Sl missing'})
    try:        
        # db.executesql("UPDATE product_receive_head SET status='CANCEL' WHERE and receive_code = %s", (sl,))    
        # db.executesql("UPDATE product_receive_details SET status='CANCEL' WHERE receive_code = %s", (sl,))
        db(db.product_receive_head.receive_code == sl).update(
                status='CANCEL',
                updated_by=user,
                updated_on=datetime.datetime.now(),
            )       
        db(db.product_receive_details.receive_code == sl).update(
                status='CANCEL',
                updated_by=user,
                updated_on=datetime.datetime.now(),
            )       
        
        db.commit()
        return json.dumps({'status': 'success'})
    except Exception as e:
        db.rollback()
        return json.dumps({'status': 'error', 'message': str(e)})   

# print receive
@action("receive/print_receive/<sl:int>", method=["GET", "POST"])
@action.uses("receive/print_receive.html", auth, T, db, session)
def print_receive(sl=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:        
        user=session['user_id']
        role=session['role']
        branch_name=session['branch_name']
        assert sl is not None  
           
        time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        query = """select receive_code,receive_date ,total_amount,status,branch_code,`desc`, created_by,branch_name, post_by  from product_receive_head where receive_code = {sl} """.format(sl=sl)        
        # return query
        head= db.executesql(query, as_dict=True)
        
        v_date = head[0]['receive_date']
        # v_type = head[0]['v_type']
        total = head[0]['total_amount']
        status = head[0]['status']
        branch_code = head[0]['branch_code']
        narration = head[0]['desc']
        created_by = head[0]['created_by']
        post_by = head[0]['post_by']
        branch_name = head[0]['branch_name']

        # v_date = datetime.datetime.strptime(v_date_db, "%Y-%m-%d").strftime('%d-%b-%Y')   

        amt_words = num2word(total)
        # print(amt_words) 

        # fetching branch address
        # branch_query = """select branch_name,address from ac_branch where cid = 'TDCLPC' and branch_code = {branch_code}""".format(branch_code=branch_code)        
        # branch_row = db.executesql(branch_query,as_dict=True)
        # v_branch_name = branch_row[0]['branch_name']
        # v_branch_address = branch_row[0]['address']
        
        # transactio details 
        details_query = """select item_code, item_name,quantity, trade_price, total
                            from product_receive_details where receive_code= {sl};""".format(sl=sl)
        results = db.executesql(details_query,as_dict=True)

       

    return dict(v_date = v_date, total=total,time=time,status=status,branch_code=branch_code,branch_name=branch_name,results=results,sl=sl,
                 amt_words=amt_words,narration=narration,created_by=created_by, post_by=post_by)


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




