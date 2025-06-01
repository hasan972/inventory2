import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET
import datetime


from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash


# voucher list/create 
@action("receive/receive", method=["GET", "POST"])
@action.uses("receive/receive.html", auth, T, db, session)
def receive():
    try:
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
            v_query = "SELECT * FROM product_receive_head where trans_type='Receive' "
            # print("v_query- "+v_query)

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

                branch = branch.split('-')
                voucher_branch_code = branch[0]
                voucher_branch_name = branch[1]

                result = db.executesql(f"SELECT MAX(receive_code)+1 FROM product_receive_head")
                print("mx_sl")
                print(db._lastsql)
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
                    vat=0,
                    grand_total=0,
                    branch_code=voucher_branch_code,
                    branch_name=voucher_branch_name,
                    created_by=username,
                    trans_type='Receive'
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
    except Exception as e:
        import traceback
        err_msg=traceback.format_exc()
        return str(err_msg)

# edit receive 
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
        trans_type=receive.trans_type
        

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
                receive_date=receive_date, receive_code = sl, receive_branch_code = receive_branch_code,trans_type=trans_type)

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

# add item to receive 
@action('receive/add_item', method=['GET', 'POST'])
@action.uses(db,session)
def add_item():
    try:
        sl = request.json.get('sl')
        item_code = request.json.get('item_code').strip()
        item_name = request.json.get('item_name').strip()
        receive_date = request.json.get('receive_date').strip()
        qty = request.json.get('qty')
        r_branch_code = request.json.get('v_branch_code')
        r_branch_name = request.json.get('v_branch_name')
        barcode = request.json.get('barcode')  

        # print(barcode)

        searched_item='' 
        
        branch_code= session.get('branch_code')
        user= session.get('user_id')

        if barcode and barcode.strip():
            searched_item = barcode.strip()
        else:
            searched_item = item_code.strip()
        
        # checking item exists
        if barcode and barcode.strip():
            item_exists = db.executesql("SELECT item_code,item_name, trade_price,retail_price FROM inventory_items WHERE barcode = %s LIMIT 1", placeholders=[barcode.strip()])
        else:
            item_exists = db.executesql("SELECT item_code,item_name, trade_price,retail_price FROM inventory_items WHERE item_code = %s LIMIT 1", placeholders=[item_code.strip()])
        
        # print(db._lastsql)
        if not item_exists:        
            return json.dumps({'status': 'not_found'}) 
        else:
            itm_code = item_exists[0][0]
            itm_name = item_exists[0][1]
            trade_price = item_exists[0][2]
            retail_price = item_exists[0][3]
            total = round(trade_price* float(qty),2 )

            duplicate = db.executesql("SELECT item_code FROM product_receive_details  WHERE receive_code= %s and item_code = %s LIMIT 1", placeholders=[sl,itm_code.strip()])

            if duplicate:
                return json.dumps({'status': 'duplicate'}) 
            else:
                db.product_receive_details.insert(
                            cid='TDCLPC',
                            receive_code=sl,
                            item_code=itm_code,
                            item_name=itm_name,
                            quantity=qty,
                            receive_date=receive_date,  
                            retail_price= retail_price, 
                            trade_price= trade_price,                
                            status='DRAFT',
                            total=total,
                            trans_type="Receive",
                            branch_code = r_branch_code,
                            created_by = user,

                        )     
                return json.dumps({'status': 'valid','total':total,'trade_price':trade_price,'itm_code':itm_code,'itm_name':itm_name})
    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'exception',
            'message':str(traceback.format_exc()) ,
            'trace': traceback.format_exc()  # Optional: for detailed trace in dev
        })

    

# delete item head from receive details 
@action('receive/delete_receive_detail', method=['POST'])
@action.uses(db)
def delete_receive_detail():
    try:
        data = request.json
        item_code = data.get('item_code')
        sl = data.get('sl')
        # ref_code = data.get('ref_code')

        # print(ref_code)
        
        if item_code and sl:        
            delete_query = """delete from product_receive_details WHERE receive_code = {rcv_code} AND item_code = '{itm_code}'""".format(rcv_code=sl,itm_code=item_code)
            # print(delete_query)
            db.executesql(delete_query)
            return dict(status='success')
        else:
            return dict(status='error', message='No receive code provided')
    except Exception as e:
        import traceback
        return dict(status='exception', message=str(traceback.format_exc()))
        
    
    

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
        # items = db.executesql("SELECT item_code, quantity FROM product_receive_details WHERE receive_code = %s", (sl,))
        balance_query = """SELECT prd.item_code, prd.quantity, s.quantity AS balance,prd.item_name FROM product_receive_details AS prd
                        LEFT JOIN stock AS s ON prd.item_code=s.item_code AND prd.branch_code=s.branch_code 
                        WHERE prd.receive_code ='{receive_code}'""".format(receive_code=sl)
        
        # print(balance_query)
        
        items=db.executesql(balance_query)
        if not items:
            return dict(success=False, error=str('No items found'))

        else:
            # Check for insufficient balances 
            for item in items:
                item_code = item[0]
                qty = item[1]
                current_balance = item[2]
                item_name = item[3]
                # print("--Checking start--")
                # print(item_name+' '+str(current_balance))
                new_balance=0

                new_balance = current_balance + qty         
                # print("new bal: "+str(new_balance))   
                # print("--Checking end--")
        

                if new_balance < 0:
                    return dict(success=False, error='Insufficient balance for item: {} Current Balance: {}'.format(item_code,current_balance))                    
                
        for item in items:
                item_code = item[0]
                qty = item[1]
                current_balance = item[2]
                new_balance=0


                new_balance = current_balance + qty  
                # print("--Update start--")
                # print(item_name+' '+str(current_balance)+" "+str(new_balance))


                db((db.stock.item_code == item_code) & (db.stock.branch_code == branch_code)).update(
                quantity = new_balance
            )
        # print(db._lastsql)


        # update head table status                      
        db(db.product_receive_head.receive_code == sl).update(
                desc=description,
                total_amount=total,
                status='POSTED',
                post_by=user,                   
                updated_by=user,
                updated_on=date,
                post_time= post_time
            )
        # update details table status 
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
        check_status_query = """select status from product_receive_head where receive_code = '{rcv_code}'""".format(rcv_code=sl)
        # print(check_status_query)
        check_status=db.executesql(check_status_query)
        rcv_status=check_status[0][0]
        print(rcv_status)

        if(rcv_status == 'POSTED' or rcv_status=='CANCEL'):
            return json.dumps({'status': 'error', 'message': 'Already posted or cancelled'})


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




