import json
from py4web import action, Field, redirect, URL, response
from py4web.utils.form import Form
from pydal.validators import IS_NOT_EMPTY, IS_IN_SET
import datetime
import socket


from py4web import action, request, abort, redirect, URL
from yatl.helpers import A
from ..common import db, session, T, cache, auth, logger, authenticated, unauthenticated, flash

# voucher list/create 
@action("sales/sales", method=["GET", "POST"])
@action.uses("sales/sales.html", auth, T, db, session)
def sales():
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
            v_query = "SELECT * FROM product_receive_head where trans_type='Sales' "

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


            # print(suppliers)

            if request.method == "POST":
                desc = str(request.forms.get('description')).strip()
                rcv_date = str(request.forms.get('rcv_date')).strip()
                branch = str(request.forms.get('branch_name')).strip()



                # print(supplier_code)
                # print(supplier_name)

                new_sl_value = '0'

                
                if branch == '':
                    flash.set('Please select branch', 'error')
                    redirect(URL('vouchers','voucher'))            
                if rcv_date == '':
                    flash.set('Please select date', 'error')
                    redirect(URL('vouchers','vouchers','voucher'))                

                branch_info = branch.split('-')
                voucher_branch_code = branch_info[0]
                voucher_branch_name = branch_info[1]

                # result = db.executesql(f"SELECT MAX(receive_code)+1 FROM product_receive_head WHERE branch_code = "+voucher_branch_code)
                result = db.executesql(f"SELECT MAX(receive_code)+1 FROM product_receive_head")
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
                    supplier_code="",
                    supplier_name="",                
                    total_amount=0,
                    vat=0,
                    grand_total=0,
                    branch_code=voucher_branch_code,
                    branch_name=voucher_branch_name,
                    created_by=username,
                    trans_type="Sales",
                    # created_on=datetime.datetime.now()
                )
                redirect(URL('sales','edit_sales', new_sl_value))
                # redirect(URL('receive','receive'))

        return dict(rows=rows, user=username,  role=role, branch_names=branch_names, user_branch_code=user_branch_code, 
                    branch_name=user_branch_name, branch_disabled=branch_disabled, today=today,
                    #   page=page, total_pages=total_pages, 
                    # start_voucher=start_voucher, end_voucher=end_voucher, total_records=total_records,
                    selected_branch=selected_branch, selected_status=selected_status,
                    )
    except Exception as e:
        import traceback
        err_msg=traceback.format_exc()
        return str(err_msg)
    
# new sales
@action("sales/new_sales/<b_code:int>/<b_name>", method=["GET", "POST"])
@action.uses(auth, T, db, session)
def new_sales(b_code=None, b_name=None):
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code') 
        user_branch_name = session.get('branch_name')
        role = session['role']
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        today2 = datetime.datetime.now().strftime('%Y%m%d')

        assert b_code and b_name is not None 

        sales_branch_code = b_code
        sales_branch_name = b_name

        sales_date = today

        # print(sales_branch_code)
        # print(sales_branch_name)
        # print(sales_date)
        new_sl_value = '0'


        # result = db.executesql(f"SELECT MAX(receive_code)+1 FROM product_receive_head WHERE branch_code = "+voucher_branch_code)
        result = db.executesql(f"SELECT MAX(receive_code)+1 FROM product_receive_head")
        new_sl_value = result[0][0] if result[0][0] is not None else 1
            # if max_sl_value:
            #     new_sl_value = str(int(max_sl_value) + 1)
            # else:
            #     new_sl_value = f"{voucher_branch_code}00001"             

                        

        db.product_receive_head.insert(
            cid="TDCLPC",
            receive_code=new_sl_value,
            receive_date=sales_date,
            status="DRAFT",
            desc="",
            supplier_code="",
            supplier_name="",                
            total_amount=0,
            vat=0,
            grand_total=0,
            branch_code=sales_branch_code,
            branch_name=sales_branch_name,
            created_by=username,
            trans_type="Sales",
            # created_on=datetime.datetime.now()
    )
    redirect(URL('sales','edit_sales', new_sl_value))
            # redirect(URL('receive','receive'))



# edit sales 
@action('sales/edit_sales/<sl:int>',method=["GET","POST"])
@action.uses(db,'sales/edit_sales.html',session,flash)
def edit_sales(sl=None):
    
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
            redirect(URL('sales','sales'))
    

        editable = not (status in ['POSTED', 'CANCEL'])

        rows_query = """select item_code, item_name, ((-1)*quantity) as quantity, trade_price, total from product_receive_details where receive_code = {rcv_code} """.format(rcv_code=sl)
        
        rows = db.executesql(rows_query,as_dict=True)     
        
    # return dict(sl=sl,status="status",v_date="v_date",v_type="v_type",narration="narration",role=role,user=user,branch_name=branch_name,editable=True,voucher_branch_name="voucher_branch_name",voucher_branch_code="voucher_branch_code")
    return dict(sl=sl,status=status,description=desctiption,rows=rows,role=role,user=user,
                branch_name=branch_name,editable=editable,receive_branch_name=receive_branch_name,
                supplier_name = supplier_name,
                receive_date=receive_date, receive_code = sl, receive_branch_code = receive_branch_code,trans_type=trans_type)

@action('sales/add_item', method=['GET', 'POST'])
@action.uses(db,session)
def add_item():
    try:
        sl = request.json.get('sl')
        item_code = request.json.get('item_code').strip()
        item_name = request.json.get('item_name').strip()
        receive_date = request.json.get('receive_date').strip()
        qty = float(request.json.get('qty'))
        r_branch_code = request.json.get('v_branch_code')
        r_branch_name = request.json.get('v_branch_name')        
        barcode = request.json.get('barcode') 

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
            total = round((retail_price* qty),2 )

            duplicate_query= """SELECT item_code FROM product_receive_details  WHERE receive_code= '{sl}' and item_code = '{itm_code}' LIMIT 1 """.format(sl=sl,itm_code=itm_code)
            duplicate= db.executesql(duplicate_query)
            # print(duplicate_query)
            if duplicate:
                return json.dumps({'status': 'duplicate'}) 
            else:  
                db.product_receive_details.insert(
                            cid='TDCLPC',
                            receive_code=sl,
                            item_code=itm_code,
                            item_name=itm_name,
                            quantity=-qty,
                            receive_date=receive_date,
                            retail_price=retail_price,  
                            trade_price=  trade_price,                
                            status='DRAFT',
                            total=total,
                            trans_type="Sales",
                            branch_code = r_branch_code,
                            created_by = user,
                        )     
                return json.dumps({'status': 'valid','total':total,'retail_price':retail_price,'itm_code':itm_code,'itm_name':itm_name})
    except Exception as e:
        import traceback
        return json.dumps({
            'status': 'exception',
            'message':str(traceback.format_exc()) ,
            'trace': traceback.format_exc()  # Optional: for detailed trace in dev
        })
        
#  post sales        
@action('sales/post_sales', method=['POST'])
@action.uses(db,session)
def post_sales():
    data = request.json
    sl = data.get('sl')    
    branch_code = data.get('branch_code')    
    receive_date = data.get('receive_date')    
    description = data.get('description')    
    sub_total = data.get('sub_total')
    vat = data.get('vat')
    grand_total= data.get('grand_total')
    user = session['user_id']
    # print(branch_code)
    
    date = datetime.datetime.now()
    # print(date)
    post_time = str(date)

    # print(grand_total)


    try:
        v_status = db.executesql("select status from product_receive_head where receive_code ="+sl)

        if (v_status[0][0]=="POSTED" or v_status[0][0]=="CANCEL"):
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
                    return dict(success=False, error='Insufficient stock for item: {} - {} Current stock quantity: {}'.format(item_code,item_name,current_balance))                    
                
        for item in items:
                item_code = item[0]
                qty = item[1]
                current_balance = item[2]
                new_balance2=0


                new_balance2 = current_balance + qty  
                # print("--Update start--")
                # print(item_name+' '+str(current_balance)+" "+str(new_balance))

                db((db.stock.item_code == item_code) & (db.stock.branch_code == branch_code)).update(
                quantity = new_balance2
            )
        # print(db._lastsql)


        # update had table status                      
        db(db.product_receive_head.receive_code == sl).update(
                desc=description,
                total_amount=sub_total,
                vat=vat,
                grand_total=grand_total,
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
    
@action('sales/print_receiptttt', method=['POST'])
@action.uses(db,session)
def print_receiptttt():
        try:
            # Start timing
            # start_time = time.time()
            order_number = '1111'
            printer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            printer.settimeout(3)  # Set shorter timeout
            printer.connect(("10.168.122.179", 9100))
            
            # print("Connected to printer in", time.time() - start_time, "seconds")

            # ESC/POS Commands
            center_text = b'\x1B\x61\x01'
            right_text = b'\x1B\x61\x02'
            left_text = b'\x1B\x61\x00'
            bold_on = b'\x1B\x45\x01'
            bold_off = b'\x1B\x45\x00'
            double_on = b'\x1D\x21\x11'
            double_off = b'\x1D\x21\x00'
            small_font = b'\x1B\x4D\x01'
            normal_font = b'\x1B\x4D\x00'
            cut_paper = b'\x1D\x56\x41\x03'
            double_height_on = b'\x1b\x21\x10'
            double_width_on = b'\x1b\x21\x20'
            normal_text = b'\x1b\x21\x00'
            # double_height = b'\x1b\x21\x10'
            

            # Construct the receipt text
            receipt_text = (
                center_text + bold_on + double_on +normal_text+ b"KFC\n" + double_off + bold_off +
                center_text + bold_on  +double_on +double_height_on+double_width_on+ b"Order Number: " +  bold_on  + double_on + str(order_number).encode()+ double_off +bold_off  + b"\n\n" + double_off +bold_off +
                center_text + normal_font + normal_text+ b"Thank you!\nPlease check your order status\non the display screen.\n\n" + normal_font +
                right_text + small_font + b"Powered by: Transcom Technology\n" + normal_font +
                left_text + b"\n" +  # Form feed
                cut_paper
            )

            printer.sendall(receipt_text)
            printer.sendall(b'\x0C')  # Form feed to force immediate printing
            # printer.shutdown(socket.SHUT_WR)  # Ensure complete transmission
            print('Print successful')
        except Exception as e:
            print("Error:", e)
        finally:
            printer.close()  # Close immediately
            # print("Socket closed in", time.time() - start_time, "seconds")
        return "Hello"  
    
# # # print_receipt(1111)
# @action("sales/print_receipt", method=["GET", "POST"])
# @action.uses(auth, T, db, session)
# def print_receipt():
#     if not session.get('user_id'):
#         redirect(URL('login'))
#     else:
#         try:
#             printer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#             printer.settimeout(3)  
#             printer.connect(("10.168.122.179", 9100))
#             printer.sendall(b"Helloooo")
#             printer.sendall(b'\x0C')            
#         except Exception as e:
#             print("Error:", e)
#         finally:
#             printer.close() 
@action("sales/print_receipt", method=["GET", "POST"])
@action.uses(auth, T, db, session)
def print_receipt():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        try:
            printer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            printer.settimeout(3)
            printer.connect(("10.168.122.179", 9100))

            # ESC/POS Commands
            center_text = b'\x1B\x61\x01'
            right_text = b'\x1B\x61\x02'
            left_text = b'\x1B\x61\x00'
            bold_on = b'\x1B\x45\x01'
            bold_off = b'\x1B\x45\x00'
            double_on = b'\x1D\x21\x11'
            double_off = b'\x1D\x21\x00'
            small_font = b'\x1B\x4D\x01'
            normal_font = b'\x1B\x4D\x00'
            cut_paper = b'\x1D\x56\x41\x03'
            double_height_on = b'\x1b\x21\x10'
            double_width_on = b'\x1b\x21\x20'
            normal_text = b'\x1b\x21\x00'

            product_details_query = """SELECT * FROM product_receive_details WHERE receive_code = {trx_code}""".format(trx_code=6)
            product_details = db.executesql(product_details_query,as_dict=True)

            order_number = 1111  # You can change this dynamically

            # Construct receipt
            # receipt_text = (
            #     center_text + bold_on + double_on + normal_text + b"KFC\n" + double_off + bold_off +
            #     center_text +   b"Order Number: " +  str(order_number).encode() +  b"\n\n" + 
            #     left_text + small_font+   b"Crispy Fired Chicken " +  str(1).encode() +   str(12.50).encode() +  b"\n" + 
            #     left_text + small_font+  b"Large Coleslaw  " +  str(1).encode() +   str(6.00).encode() +  b"\n" + 
            #     left_text +  small_font+ b"Pepsi Large Fountain  " +  str(1).encode() +   str(5.00).encode() +  b"\n" +                 
            #     center_text + normal_font +  b"Thank you!\nPlease check your order status\non the display screen.\n\n" + normal_font +
            #     right_text + small_font + b"Powered by: Transcom Technology\n" + normal_font +
            #     left_text + b"\n" +
            #     cut_paper
            # )
            receipt_text = (
                center_text + bold_on + double_on + normal_text + b"KFC\n" + double_off + bold_off +
                center_text +   b"Order Number: " +  str(order_number).encode() +  b"\n\n" ) 
            #     left_text + small_font+   b"Crispy Fired Chicken " +  str(1).encode() +   str(12.50).encode() +  b"\n" + 
            #     left_text + small_font+  b"Large Coleslaw  " +  str(1).encode() +   str(6.00).encode() +  b"\n" + 
            #     left_text +  small_font+ b"Pepsi Large Fountain  " +  str(1).encode() +   str(5.00).encode() +  b"\n" +                 
            #     center_text + normal_font +  b"Thank you!\nPlease check your order status\non the display screen.\n\n" + normal_font +
            #     right_text + small_font + b"Powered by: Transcom Technology\n" + normal_font +
            #     left_text + b"\n" +
            #     cut_paper
            # )

            for product in product_details:
                item_name = str(product['item_name']).encode()
                qty = str(product['quantity']).encode()
                total = str(product['total']).encode()                

                receipt_text+= left_text + small_font+   item_name + b"  "+ qty +  b"  "+total  +  b"\n"
            
            receipt_text  += cut_paper



            # Send to printer
            printer.sendall(receipt_text)
            printer.sendall(b'\x0C')  # Form feed

            # return receipt_text

            print('Print successful')
        except Exception as e:
            print("Error:", e)
        finally:
            printer.close()