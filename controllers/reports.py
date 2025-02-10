
from py4web import action, request,redirect, response, URL
from io import StringIO 
import csv
import datetime

from ..common import db, session, T, cache, auth,flash
from ..common_cid import date_fixed

# Report
@action("reports/reports", method=["GET", "POST"])
@action.uses("reports/reports.html", auth, T, db,session,flash)
def reports():
    if not session.get('user_id'):
        redirect(URL('login'))
    elif session['f_password']==1:
        flash.set('Please change your password.', 'warning')
        redirect(URL('change_password_force'))
    else:        
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']
        branch_diabled = str(user_branch_code)+'-'+user_branch_name            
        branch_names = db.executesql("SELECT concat(branch_code,'-',branch_name) FROM ac_branch where branch_code<>99 order by branch_code asc")  
        ref_type = db.executesql("SELECT ref_type FROM ac_ref_type")  


    return dict(role=role,branch_names=branch_names,user_branch_code=user_branch_code,branch_name=user_branch_name,branch_diabled=branch_diabled,user=username,ref_type=ref_type) 


# trial balance - details
@action("reports/trial_balance_1", method=["GET", "POST"])
@action.uses("reports/trial_balance_1.html", auth, T, db, session)
def trial_balance_1():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        branch = request.POST.get('branch')
        report_branch_code =str(branch).split('-')[0]
        report_branch_name =str(branch).split('-')[1]
        
        time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        address_query= """select address from ac_branch where branch_code = {branch_code}""".format(branch_code=report_branch_code)
        address_row = db.executesql(address_query,as_dict=True)   
        address = address_row[0]['address']  

        branch_query=''
        if report_branch_code =='99':
            branch_query=""
        else:
            branch_query="and branch_code ='"+report_branch_code+"'"

        results=[]
        

        if from_date and to_date and branch:


            # query to fetch accounts and their transaction amounts
            query = """
                        SELECT * FROM ( 
                        SELECT sl,account_code, account_name, amount AS debit, 0 AS credit,'' AS ref_code,'' AS ref_name, CAST(v_date AS DATE) AS v_date FROM ac_voucher_details WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
                                    AND amount > 0  {branch_code}
                                    UNION ALL
                        SELECT sl,account_code, account_name, 0 AS debit, abs(amount) AS credit,'' AS ref_code,'' AS ref_name,CAST(v_date AS DATE) AS v_date FROM ac_voucher_details WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
                        AND amount < 0  {branch_code}
                        ) AS t ORDER BY sl
            """.format(fromdate=from_date, todate=to_date,branch_code=branch_query )
               
            results = db.executesql(query,as_dict=True)

            # query to fetch reference and their transaction amounts
            query2 = """
            SELECT p.sl,p.account_code,ac.account_name, debit, credit,ref_code,ref_name,v_date FROM (
            SELECT sl,account_code, ref_code,ref_name, amount AS debit, 0 AS credit, CAST(v_date AS DATE) AS v_date FROM ac_voucher_reference WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
            AND amount > 0  {branch_code}
            UNION ALL           
            SELECT sl,account_code, ref_code,ref_name, 0 AS debit, abs(amount) AS credit, CAST(v_date AS DATE) AS v_date FROM ac_voucher_reference WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
            AND amount < 0  {branch_code}
            ) AS p 
            JOIN ac_accounts AS ac ON p.account_code = ac.account_code
            """.format(fromdate=from_date, todate=to_date,branch_code=branch_query )
            # return query2
               
            results2 = db.executesql(query2,as_dict=True)

            query3 = """
                        SELECT COALESCE(SUM(debit),0) AS tot_debit,COALESCE(SUM(credit),0) AS tot_credit FROM ( 
                        SELECT SUM(amount) AS debit, 0 AS credit FROM ac_voucher_details WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}'
                                AND amount > 0 {branch_code}
                                UNION ALL
                        SELECT 0 AS debit, ABS(SUM(amount)) AS credit FROM ac_voucher_details WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
                        AND amount < 0 {branch_code}
                        ) AS t 
            """.format(fromdate=from_date, todate=to_date,branch_code=branch_query )
            # return query3
               
            results3 = db.executesql(query3,as_dict=True)
            tot_debit = results3[0]['tot_debit']
            tot_credit = results3[0]['tot_credit']            

            merged_results = []

            for row in results:
                has_reference = False
                for ref in results2:
                    if ref['account_code'] == row['account_code'] and ref['sl'] == row['sl']:
                        merged_results.append(ref)
                        has_reference = True
                if not has_reference:
                    merged_results.append(row)            
            # print(merged_results)                        
                
        else:
            print("Form data is missing")

    return dict(user=username, address=address,branch_name=user_branch_name, role=role, merged_results=merged_results,results=results,
                results2=results2,from_date=from_date,to_date=to_date,report_branch_code=report_branch_code,time=time,
                report_branch_name=report_branch_name,tot_debit=tot_debit,tot_credit=tot_credit)


# download trial balance details 

from io import StringIO
# import csv

@action('reports/download_trial_balance_1', method=['GET'])
@action.uses(db, session)
def download_trial_balance_1():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.query.get('from_date')
        to_date = request.query.get('to_date')
        report_branch_code = request.query.get('branch_code')
        report_branch_name = request.query.get('branch_name')

        # print(report_branch_name)

        branch_query = ''
        if report_branch_code == '99':
            branch_query = ""
        else:
            branch_query = "and branch_code ='" + report_branch_code + "'"

        query = """
            SELECT * FROM ( 
            SELECT sl, CONCAT(' ',account_code) AS account_code, account_name, amount AS debit, 0 AS credit, '' AS ref_code, '' AS ref_name, DATE_FORMAT(v_date, "%Y%m%d") AS v_date  
            FROM ac_voucher_details 
            WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
            AND amount > 0 {branch_code}
            UNION ALL
            SELECT sl, account_code, account_name, 0 AS debit, amount AS credit, '' AS ref_code, '' AS ref_name, DATE_FORMAT(v_date, "%Y%m%d") AS v_date  
            FROM ac_voucher_details 
            WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
            AND amount < 0 {branch_code}
            ) AS t ORDER BY sl
        """.format(fromdate=from_date, todate=to_date, branch_code=branch_query)
               
        results = db.executesql(query, as_dict=True)

        query2 = """
            SELECT p.sl, CONCAT(' ',p.account_code) AS account_code, ac.account_name, debit, credit, ref_code, ref_name, DATE_FORMAT(v_date, "%Y%m%d") AS v_date 
            FROM (
            SELECT sl, account_code, ref_code, ref_name, amount AS debit, 0 AS credit, CAST(v_date AS DATE) AS v_date 
            FROM ac_voucher_reference 
            WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
            AND amount > 0 {branch_code}
            UNION ALL           
            SELECT sl, account_code, ref_code, ref_name, 0 AS debit, amount AS credit, CAST(v_date AS DATE) AS v_date 
            FROM ac_voucher_reference 
            WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
            AND amount < 0 {branch_code}
            ) AS p 
            JOIN ac_accounts AS ac ON p.account_code = ac.account_code
        """.format(fromdate=from_date, todate=to_date, branch_code=branch_query)
               
        results2 = db.executesql(query2, as_dict=True)

        print(report_branch_name)
            
        merged_results = []

        for row in results:
            has_reference = False
            for ref in results2:
                if ref['account_code'] == row['account_code'] and ref['sl'] == row['sl']:                    
                    merged_results.append(ref)
                    has_reference = True
            if not has_reference:                
                merged_results.append(row)   
        
        csv_stream = StringIO()       
        csv_writer = csv.writer(csv_stream,quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(["AccountID", "Description", "Debit", "Credit", "OPTValue", "OPTDescription", "TRANSDATE"])

        
        
        # for row in merged_results:
        #     account_id = str(row['account_code'])  
        #     ref_id = str(row['ref_code'])  
        #     csv_writer.writerow([
        #         f"\t{account_id}",  
        #         row['account_name'],
        #         row['debit'],
        #         row['credit'],
        #         f"\t{ref_id}",
        #         row['ref_name'],
        #         row['v_date'] 
        #     ])        
        
        for row in merged_results:
            csv_writer.writerow([
                " "+str(row['account_code']),
                row['account_name'],
                row['debit'],
                row['credit'],
                " "+str(row['ref_code']),
                row['ref_name'],
                row['v_date'] 
            ])        
        
        
        csv_content = csv_stream.getvalue()
        csv_stream.close()
        
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename="trial_balance_details.csv"'        
        
        return csv_content
    
    # excel 
@action('reports/download_trial_balance_xl', method=['GET','POST'])
@action.uses(db, session)
def download_trial_balance_xl():

    branch_code = request.query.get('branch_code')
    from_date = request.query.get('from_date')
    to_date = request.query.get('to_date')

    query = """
        SELECT * FROM ( 
        SELECT sl, account_code, account_name, amount AS debit, 0 AS credit, '' AS ref_code, '' AS ref_name, DATE_FORMAT(v_date, "%Y%m%d") AS v_date  
        FROM ac_voucher_details 
        WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
        AND amount > 0 and branch_code = {branch_code}
        UNION ALL
        SELECT sl, account_code, account_name, 0 AS debit, amount AS credit, '' AS ref_code, '' AS ref_name, DATE_FORMAT(v_date, "%Y%m%d") AS v_date  
        FROM ac_voucher_details 
        WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
        AND amount < 0 and branch_code = {branch_code}
        ) AS t ORDER BY sl
    """.format(fromdate=from_date, todate=to_date, branch_code=branch_code)
            
    results = db.executesql(query, as_dict=True)

    query2 = """
        SELECT p.sl, p.account_code, ac.account_name, debit, credit, ref_code, ref_name, DATE_FORMAT(v_date, "%Y%m%d") AS v_date 
        FROM (
        SELECT sl, account_code, ref_code, ref_name, amount AS debit, 0 AS credit, CAST(v_date AS DATE) AS v_date 
        FROM ac_voucher_reference 
        WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
        AND amount > 0 and branch_code = {branch_code}
        UNION ALL           
        SELECT sl, account_code, ref_code, ref_name, 0 AS debit, amount AS credit, CAST(v_date AS DATE) AS v_date 
        FROM ac_voucher_reference 
        WHERE cid='TDCLPC' AND STATUS='POSTED' AND v_date BETWEEN '{fromdate}' AND '{todate}' 
        AND amount < 0 and branch_code = {branch_code}
        ) AS p 
        JOIN ac_accounts AS ac ON p.account_code = ac.account_code
    """.format(fromdate=from_date, todate=to_date, branch_code=branch_code)
            
    results2 = db.executesql(query2, as_dict=True)

    merged_results = []

    for row in results:
        has_reference = False
        for ref in results2:
            if ref['account_code'] == row['account_code'] and ref['sl'] == row['sl']:                    
                merged_results.append(ref)
                has_reference = True
        if not has_reference:                
            merged_results.append(row)   
    
    renamed_results = [
    {
        "AccountID": row["account_code"],  
        "Description": row["account_name"],  
        "Debit": row["debit"],  
        "Credit": row["credit"],  
        "OPTValue": row["ref_code"], 
        "OPTDescription": row["ref_name"],
        "TRANSDATE": row["v_date"], 
    }
    for row in merged_results
]

    return dict(data=renamed_results) 
    
# trial balance summary
@action("reports/trial_balance_2", method=["GET", "POST"])
@action.uses("reports/trial_balance_2.html", auth, T, db, session)
def trial_balance_2():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        branch = request.POST.get('branch')
        report_branch_code =str(branch).split('-')[0]
        report_branch_name =str(branch).split('-')[1]
        # report_branch_name =str(branch).split('-')[1]
        time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        address_query= """select address from ac_branch where branch_code = {branch_code}""".format(branch_code=report_branch_code)
        address_row = db.executesql(address_query,as_dict=True)   
        address = address_row[0]['address']  

        branch_query=''
        if report_branch_code =='99':
            branch_query=""
        else:
            branch_query="and branch_code ='"+report_branch_code+"'"

        results=[]

        if from_date and to_date and branch:

            # all summation 
            query = """
                   SELECT account_code, account_name,
                    CASE WHEN amount > 0 THEN amount ELSE 0 END AS debit,
                    CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END AS credit
                    FROM (
                        SELECT account_code, account_name, SUM(amount) AS amount FROM ac_voucher_details WHERE
                            v_date BETWEEN '{fromdate}' AND '{todate}'  and status='POSTED' {branch_code} GROUP BY account_code, account_name
                    ) AS t;   
            """.format(fromdate=from_date, todate=to_date,branch_code=branch_query )
            # print(query)
            results = db.executesql(query,as_dict=True)

            # total debit 
            query2 = """
                        SELECT  coalesce(sum(amount),0) as tot_debit
                    FROM (
                        SELECT account_code, account_name, SUM(amount) AS amount FROM ac_voucher_details WHERE
                            v_date BETWEEN '{fromdate}' AND '{todate}'  and status='POSTED' {branch_code} GROUP BY account_code, account_name 
                    ) AS t1   where amount >0
                    """.format(fromdate=from_date, todate=to_date,branch_code=branch_query )
            results2 = db.executesql(query2,as_dict=True)
            tot_debit = results2[0]['tot_debit']

            # total credit 
            query2 = """
                        SELECT  abs(coalesce(sum(amount),0)) as tot_credit
                    FROM (
                        SELECT account_code, account_name, SUM(amount) AS amount FROM ac_voucher_details WHERE
                            v_date BETWEEN '{fromdate}' AND '{todate}'  and status='POSTED' {branch_code} GROUP BY account_code, account_name 
                    ) AS t1   where amount < 0
                    """.format(fromdate=from_date, todate=to_date,branch_code=branch_query )
            results3 = db.executesql(query2,as_dict=True)
            tot_credit = results3[0]['tot_credit']
              
            
            
            # results = db.executesql(query, as_dict=True)
        else:
            print("Form data is missing")

    return dict(user=username,address=address, branch_name=user_branch_name, role=role, results=results,tot_debit=tot_debit, tot_credit=tot_credit,from_date=from_date,to_date=to_date,report_branch_code=report_branch_code, time=time,report_branch_name=report_branch_name)

# download trial balance summary
@action('reports/download_trial_balance_2', method=['GET'])
@action.uses(db, session)
def download_trial_balance_2():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.query.get('from_date')
        to_date = request.query.get('to_date')
        report_branch_code = request.query.get('branch_code')

        branch_query=''
        if report_branch_code =='99':
            branch_query=""
        else:
            branch_query="and branch_code ='"+report_branch_code+"'"
       
        
        query = """
                    SELECT account_code, account_name,
                    CASE WHEN amount > 0 THEN amount ELSE 0 END AS debit,
                    CASE WHEN amount < 0 THEN ABS(amount) ELSE 0 END AS credit
                    FROM (
                        SELECT account_code, account_name, SUM(amount) AS amount FROM ac_voucher_details WHERE
                            v_date BETWEEN '{fromdate}' AND '{todate}'  and status='POSTED' {branch_code} GROUP BY account_code, account_name
                    ) AS t;                            

            """.format(fromdate=from_date, todate=to_date,branch_code=branch_query)
        
        rows = db.executesql(query)        

        # total debit 
        query2 = """
                    SELECT  coalesce(sum(amount),0) as tot_debit
                FROM (
                    SELECT account_code, account_name, SUM(amount) AS amount FROM ac_voucher_details WHERE
                        v_date BETWEEN '{fromdate}' AND '{todate}'  and status='POSTED' {branch_code} GROUP BY account_code, account_name 
                ) AS t1   where amount >0
                """.format(fromdate=from_date, todate=to_date,branch_code=branch_query )
        results2 = db.executesql(query2,as_dict=True)
        tot_debit = results2[0]['tot_debit']

        # total credit 
        query2 = """
                    SELECT  abs(coalesce(sum(amount),0)) as tot_credit
                FROM (
                    SELECT account_code, account_name, SUM(amount) AS amount FROM ac_voucher_details WHERE
                        v_date BETWEEN '{fromdate}' AND '{todate}'  and status='POSTED' {branch_code} GROUP BY account_code, account_name 
                ) AS t1   where amount < 0
                """.format(fromdate=from_date, todate=to_date,branch_code=branch_query )
        results3 = db.executesql(query2,as_dict=True)
        tot_credit = results3[0]['tot_credit']
            
        
        csv_stream = StringIO()       
        csv_stream.write("Account Code,Account_name,Debit,Credit\n")         
        
        for row in rows:
            csv_stream.write(','.join(map(str, row)) + "\n")
        
        csv_stream.write(",Total:,"+str(tot_debit)+","+str(tot_credit)+"\n")   
        
        
        csv_content = csv_stream.getvalue()
        csv_stream.close()
        
        
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename="tial_balance_summary.csv"'        
        
        return csv_content


# transactionlisting
@action("reports/transaction_listing", method=["GET", "POST"])
@action.uses("reports/transaction_listing.html", auth, T, db, session)
def transaction_listing():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        branch = request.POST.get('branch')
        account = request.POST.get('account')
        report_branch_code =str(branch).split('-')[0]
        report_branch_name =str(branch).split('-')[1]
        # report_branch_name =str(branch).split('-')[1]
        time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")       


        branch_query=''
        branch_query2=''
        if report_branch_code =='99':
            branch_query=""
            branch_query2=""
        else:
            branch_query="and branch_code ='"+report_branch_code+"'"
            branch_query2="and d.branch_code ='"+report_branch_code+"'"

        results=[]
        account_name=''
        account_group=''
        opening_balance= ''

        address_query= """select address from ac_branch where branch_code = {branch_code}""".format(branch_code=report_branch_code)
        address_row = db.executesql(address_query,as_dict=True)   
        address = address_row[0]['address']    


        if from_date and to_date and branch:


            # account_row = db.executesql("select * from ac_accounts where account_code= '%s'",placeholders=account,as_dict=True)
            account_row = db(db.ac_accounts.account_code == account).select().first()
            account_name = account_row.account_name
            account_class= account_row.class_name
            account_group= account_row.group_name

            # query1= """select coalesce(sum(amount),0) as opening_balance from ac_voucher_details where account_code = '{ac_code}' and v_date < '{fromdate}' 
            # and status='POSTED' {branch_code}
            # """.format(ac_code=account,fromdate=from_date, todate=to_date,branch_code=branch_query )
            
            query1 = """select sum(opening_balance) as opening_balance ,sum(rem_balance)+sum(opening_balance) as rem_balance from (
                        select sum(amount) as opening_balance,0 as rem_balance from ac_voucher_details where cid = 'TDCLPC' and account_code = '{ac_code}' and v_date < '{fromdate}' and status='POSTED'  {branch_code}
                        union all
                        select 0 as opening_balance, sum(amount) rem_balance from ac_voucher_details where cid = 'TDCLPC' and account_code = '{ac_code}' and v_date between '{fromdate}' and '{todate}'  and status='POSTED' {branch_code}
                        ) as q1
                    """.format(ac_code=account,fromdate=from_date, todate=to_date,branch_code=branch_query )
            
            result1 = db.executesql(query1,as_dict=True)
            opening_balance= result1[0]['opening_balance']
            rem_balance= result1[0]['rem_balance']
            
            
            query2 = """
                   SELECT d.sl, cast(d.v_date as date) as v_date,h.narration as narration,
                            CASE WHEN amount > 0 THEN amount ELSE 0 END AS debit,
                            CASE WHEN amount < 0 THEN -amount ELSE 0 END AS credit
                    FROM  ac_voucher_details as d 
                    join ac_voucher_head as h on d.sl=h.sl
                    where d.cid = 'TDCLPC' and account_code = '{ac_code}' and d.v_date between '{fromdate}' and '{todate}' and d.status= 'POSTED' {branch_code} order by d.id asc
            """.format(ac_code=account,fromdate=from_date, todate=to_date,branch_code=branch_query2 )
            
            results = db.executesql(query2,as_dict=True)

            query3="""
                    select sum(debit) as total_debit, sum(-credit) total_credit,sum(total) net_change from (
                    select sum(amount) as debit, 0 as credit, 0 as total from ac_voucher_details where cid = 'TDCLPC' and  account_code = '{ac_code}' and amount>0 and v_date between '{fromdate}' and '{todate}' and status='POSTED' {branch_code}
                    union all
                    select 0 as debit, sum(amount),0 as total from ac_voucher_details where cid = 'TDCLPC' and  account_code = '{ac_code}' and amount<0 and v_date between '{fromdate}' and '{todate}' and status='POSTED' {branch_code}
                    union all
                    select 0 as debit,0 as credit, sum(amount) as total from ac_voucher_details  where cid = 'TDCLPC' and account_code = '{ac_code}' and v_date between '{fromdate}' and '{todate}'  and status='POSTED' {branch_code}) as q3
                    """.format(ac_code=account,fromdate=from_date,todate=to_date,branch_code=branch_query)
            # print(query3)
            
            results2 = db.executesql(query3, as_dict=True)
            total_debit=results2[0]['total_debit']
            total_credit=results2[0]['total_credit']
            net_change = results2[0]['net_change']


        else:
            print("Form data is missing")

    return dict(user=username, branch_name=report_branch_name, role=role, results=results,from_date=from_date,to_date=to_date,report_branch_code=report_branch_code, time=time,
                account_no=account, account_name=account_name,account_group=account_group,opening_balance=opening_balance,total_debit=total_debit,total_credit=total_credit,
                net_change=net_change,rem_balance=rem_balance,address=address)


# download tr_listing
@action('reports/download_transactionlisting', method=['GET'])
@action.uses(db, session)
def download_transactionlisting():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.query.get('from_date')
        to_date = request.query.get('to_date')
        report_branch_code = request.query.get('branch_code')
        account = request.query.get('account')

        branch_query=''
        branch_query2=''
        if report_branch_code =='99':
            branch_query=""
            branch_query2=""
        else:
            branch_query="and branch_code ='"+report_branch_code+"'"
            branch_query2="and d.branch_code ='"+report_branch_code+"'"
       
        
        query1 = """select sum(opening_balance) as opening_balance ,sum(rem_balance)+sum(opening_balance) as rem_balance from (
                        select sum(amount) as opening_balance,0 as rem_balance from ac_voucher_details where cid = 'TDCLPC' and account_code = '{ac_code}' and v_date < '{fromdate}' and status='POSTED'  {branch_code}
                        union all
                        select 0 as opening_balance, sum(amount) rem_balance from ac_voucher_details where cid = 'TDCLPC' and account_code = '{ac_code}' and v_date between '{fromdate}' and '{todate}'  and status='POSTED' {branch_code}
                        ) as q1
                    """.format(ac_code=account,fromdate=from_date, todate=to_date,branch_code=branch_query )
            
        result1 = db.executesql(query1,as_dict=True)
        opening_balance= str(result1[0]['opening_balance'])
        # print(opening_balance)
        rem_balance= str(result1[0]['rem_balance'])

        query2 = """
                    SELECT d.sl, d.v_date,h.narration as narration,
                        CASE WHEN amount > 0 THEN amount ELSE 0 END AS debit,
                        CASE WHEN amount < 0 THEN -amount ELSE 0 END AS credit
                    FROM  ac_voucher_details as d
                    join ac_voucher_head as h on d.sl=h.sl
                where d.cid = 'TDCLPC' and account_code = '{ac_code}' and d.v_date between '{fromdate}' and '{todate}' and d.status= 'POSTED' {branch_code} 
        """.format(ac_code=account,fromdate=from_date, todate=to_date,branch_code=branch_query2 )
        
        result2 = db.executesql(query2)        


        query3 ="""
                    select sum(debit) as total_debit, sum(-credit) total_credit,sum(total) net_change from (
                    select sum(amount) as debit, 0 as credit, 0 as total from ac_voucher_details  where cid = 'TDCLPC' and account_code = '{ac_code}' and amount>0 and v_date between '{fromdate}' and '{todate}' and status='POSTED' {branch_code}
                    union all
                    select 0 as debit, sum(amount),0 as total from ac_voucher_details  where cid = 'TDCLPC' and account_code = '{ac_code}' and amount<0 and v_date between '{fromdate}' and '{todate}' and status='POSTED' {branch_code}
                    union all
                    select 0 as debit,0 as credit, sum(amount) as total from ac_voucher_details  where cid = 'TDCLPC' and account_code = '{ac_code}' and v_date between '{fromdate}' and '{todate}' and status='POSTED' {branch_code}) as q3
                    """.format(ac_code=account,fromdate=from_date,todate=to_date,branch_code=branch_query)
            # print(query3)
            
        results3 = db.executesql(query3, as_dict=True)
        total_debit=str(results3[0]['total_debit'])
        total_credit=str(results3[0]['total_credit'])
        net_change = str(results3[0]['net_change'])

        
        csv_stream = StringIO()      
        csv_stream.write(",,,,,Opening Balance:,"+opening_balance+"\n") 
        csv_stream.write("Voucher No.,Trans. Date,Narration,Debit,Credit,Net Change, Balance\n")        
            
        
        for row in result2:
            csv_stream.write(','.join(map(str, row)) + "\n")
        
        csv_stream.write(",,Total:,"+total_debit+","+total_credit+","+net_change+","+rem_balance+"\n")    
        
        
        csv_content = csv_stream.getvalue()
        csv_stream.close()
        
        
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename="transactionlising.csv"'        
        
        return csv_content
    

# receipt-payment - details
@action("reports/rcp_pay", method=["GET", "POST"])
@action.uses("reports/rcp_pay.html", auth, T, db, session)
def rcp_pay():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        branch = request.POST.get('branch')
        report_branch_code =str(branch).split('-')[0]
        report_branch_name =str(branch).split('-')[1]
        
        time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        address_query = """select address from ac_branch where cid = 'TDCLPC' and branch_code = {branch_code}""".format(branch_code=report_branch_code)        
        branch_row = db.executesql(address_query,as_dict=True)
        v_branch_address = branch_row[0]['address']

        
        if from_date and to_date and branch:


            # total cash and bank  balance upto from date
            query1 = """ select account_code, max(account_name) as account_name, coalesce(sum(amount),0)  as cash_bal from ac_voucher_details where branch_code= {branch_code} and v_date < '{fromdate}' and status = 'POSTED' and account_code in (
                        select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type in ('Cash','Bank') and account_code in (
                        select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code = {branch_code})) group by account_code            
            """.format(fromdate=from_date, branch_code=report_branch_code )  
            # return query1       
               
            result1 = db.executesql(query1,as_dict=True)

            # # total bank balance upto from date X X X
            # query2 = """ select account_code, max(account_name) as account_name, coalesce(sum(amount),0)  as bank_bal from ac_voucher_details where branch_code= {branch_code} and v_date < '{fromdate}' and status = 'POSTED' and account_code in (
            #             select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type= 'Bank' and account_code in (
            #             select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code = {branch_code})) group by account_code           
            # """.format(fromdate=from_date, branch_code=report_branch_code )       
            # # return query2

               
            # result2 = db.executesql(query2,as_dict=True)

            # total bank and cash upto from date
            query3 = """select coalesce(sum(amount),0)  as cash_bank_bal from ac_voucher_details where branch_code= {branch_code} and v_date < '{fromdate}' and status = 'POSTED' and account_code in (
				select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type in ('Bank','Cash') and account_code in (
				select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code = {branch_code}) )     
            """.format(fromdate=from_date, branch_code=report_branch_code )       
            # return query3  
               
            result3 = db.executesql(query3,as_dict=True)
            tot_cash_bank = result3[0]['cash_bank_bal']            

            # total received from from corporate 
            query4 = """select 	coalesce(sum(amount),0)*(-1)  as tot_corp from ac_voucher_details where branch_code={branch_code} and v_date between '{fromdate}' and '{todate}' and status = 'POSTED' and account_code in (
                        select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type = 'Corporate' and account_code in (
                        select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code = {branch_code}) )
            """.format(fromdate=from_date,todate=to_date, branch_code=report_branch_code )  
            # return query4       
               
            result4 = db.executesql(query4,as_dict=True)
            tot_corp = result4[0]['tot_corp']

            # cash, bank, corporate total 
            query5 = """select sum(total) as total from (
                        select coalesce(sum(amount),0)  as total from ac_voucher_details where branch_code= {branch_code} and v_date < '{fromdate}' and status = 'POSTED' and account_code in (
                        select account_code from ac_cash_bank where account_type in ('Cash','Bank') and account_code in (
                        select account_code from ac_account_branch where branch_code = {branch_code}) )				
                        union all	
                        select 		 coalesce(sum(amount),0)*(-1)  as total from ac_voucher_details where branch_code= {branch_code} and v_date between '{fromdate}' and '{todate}' and 
                        status = 'POSTED' and account_code in (
                                select account_code from ac_cash_bank where account_type ='Corporate' and account_code in (
                                select account_code from ac_account_branch where branch_code = {branch_code}) )

                        union all
                        select coalesce(sum(amount),0)*(-1) total from ac_voucher_details where branch_code= {branch_code} and  (v_date between '{fromdate}' and '{todate}') 
		                and status= 'POSTED' and account_code like '4%'                         
                                ) as t
            """.format(todate=to_date,fromdate=from_date, branch_code=report_branch_code )         
            # return query5
               
            result5 = db.executesql(query5,as_dict=True)
            total_receipt = result5[0]['total']

            # gl heads 
            query6 = """select account_code, max(account_name) as account_name, sum(amount)as amount from ac_voucher_details where  branch_code={branch_code} and STATUS='POSTED'
                        and (v_date between '{fromdate}' and '{todate}')  and account_code not like '4333%' and account_code not like '11666%' and account_code not in (
                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code} and account_code in (
                            select account_code from ac_cash_bank)
                        ) group by account_code order by account_code
            """.format(todate=to_date,fromdate=from_date, branch_code=report_branch_code )    
            # return query6     
               
            result6 = db.executesql(query6,as_dict=True)

            # reference 
            # query7 = """select account_code, max(account_name) as account_name,ref_code,max(ref_name) as ref_name, sum(amount) as amount from ac_voucher_details where branch_code={branch_code} and v_type='Payment' 
            #             and v_date between '{fromdate}' and '{todate}' and ref_code <> '' and status='POSTED' and account_code not in (
            #                 select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code} and account_code in (
            #                 select account_code from ac_cash_bank)
            #             )group by account_code,ref_code
            # """.format(todate=to_date,fromdate=from_date, branch_code=report_branch_code )    
            # reference   
            query7 = """select account_code, ref_code,max(ref_name) as ref_name, sum(amount) as amount from ac_voucher_reference where branch_code={branch_code} 
                        and v_date between '{fromdate}' and '{todate}' and status='POSTED' and account_code not like '4333%' and account_code not like '11666%' and account_code not in (
                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code = {branch_code} and account_code in (
                            select account_code from ac_cash_bank)
                        )group by account_code,ref_code
            """.format(todate=to_date,fromdate=from_date, branch_code=report_branch_code )     
            # return query7 
             
               
            result7 = db.executesql(query7,as_dict=True)   

            # total expense 
            query8 = """select coalesce(sum(amount),0) as tot_exp from ac_voucher_details where cid = 'TDCLPC' and branch_code={branch_code} and v_date between '{fromdate}' and '{todate}' and status='POSTED' 
                        and account_code not like '4333%' and account_code not like '11666%' and  account_code not in  (
                            select account_code from ac_cash_bank where account_type in ('Cash','Bank','Corporate') and account_code in (
                                    select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code})
                        )
                        """.format(todate=to_date,fromdate=from_date, branch_code=report_branch_code )  
            # return    query8             
               
            result8 = db.executesql(query8,as_dict=True)   
            tot_exp = result8[0]['tot_exp'] 

            # closing cash 
            query9 = """select account_code, max(account_name) as account_name, coalesce(sum(amount),0)  as closing_cash 
                        from ac_voucher_details where branch_code= {branch_code} and v_date <= '{todate}' and status = 'POSTED' and account_code in (
                            select account_code from ac_cash_bank where account_type= 'Cash' and account_code in (
                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code})) group by account_code                                         
                        """.format(todate=to_date, branch_code=report_branch_code )
            # return query9                           
               
            result9 = db.executesql(query9,as_dict=True)   

            # closing bank 
            query10 = """select account_code, max(account_name) as account_name, coalesce(sum(amount),0)  as closing_bank 
                        from ac_voucher_details where branch_code= {branch_code} and v_date <= '{todate}' and status = 'POSTED' and account_code in (
                            select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type= 'Bank' and account_code in (
                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code})) group by account_code                                         
                        """.format(todate=to_date, branch_code=report_branch_code )       
            # return   query10                  
               
            result10 = db.executesql(query10,as_dict=True)   

            # total cash and bank 
            query11 = """select coalesce(sum(amount),0)  as tot_closing
			            from ac_voucher_details where branch_code= {branch_code} and v_date <= '{todate}' and status = 'POSTED' and account_code in (
                            select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type in ('Cash','Bank') and account_code in (
                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code}))                                          
                        """.format(todate=to_date, branch_code=report_branch_code )    
            # return query11                       
               
            result11 = db.executesql(query11,as_dict=True) 
            tot_closing  =  result11[0]['tot_closing']

            # total cosing cash/bank + total expense 
            query12 = """select coalesce(sum(amount)) as amount from (
                            select sum(amount) as amount from ac_voucher_details where branch_code={branch_code} and v_date between '{fromdate}' and '{todate}' and status='POSTED' and
                            account_code NOT LIKE '4333%' AND account_code NOT LIKE '11666%' and account_code not in  (
                                            select account_code from ac_cash_bank where account_type in ('Cash','Bank','Corporate') and account_code in (
                                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code})
                                        )
                            union all			
                            select coalesce(sum(amount),0)  as amount from ac_voucher_details where branch_code= {branch_code} and 
                            v_date <= '{todate}' and status = 'POSTED' and account_code in (
                                            select account_code from ac_cash_bank where account_type in ('Cash','Bank') and account_code in (
                                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code}))    ) as q                                                      
                        """.format(fromdate=from_date,todate=to_date, branch_code=report_branch_code )  
            # return query12                         
               
            result12 = db.executesql(query12,as_dict=True) 
            total_pay  =  result12[0]['amount']

            # micellaneous receipt
            query13 = """select account_code,max(account_name) as account_name, coalesce(sum(amount),0)*(-1) as amount from ac_voucher_details where cid = 'TDCLPC' and branch_code= {branch_code} and  
                        (v_date between '{fromdate}' and '{todate}') and status= 'POSTED' and account_code like '4%' group by account_code                                            
                        """.format(fromdate=from_date,todate=to_date, branch_code=report_branch_code )                           
               
            result13 = db.executesql(query13,as_dict=True) 
            # return query13              
            
            
        else:
            print("Form data is missing")

    return dict(branch_name=user_branch_name,result1=result1,result6=result6,result7=result7,tot_exp=tot_exp,address=v_branch_address,
    tot_cash_bank=tot_cash_bank,tot_corp=tot_corp,total_receipt=total_receipt,from_date=from_date,to_date=to_date,result9=result9,
    tot_closing=tot_closing,result10=result10,result13=result13,total_pay=total_pay,report_branch_code=report_branch_code,time=time,report_branch_name=report_branch_name)


# receipt-payment summary
@action("reports/rcp_pay_sum", method=["GET", "POST"])
@action.uses("reports/rcp_pay_sum.html", auth, T, db, session)
def rcp_pay_sum():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        branch = request.POST.get('branch')
        report_branch_code =str(branch).split('-')[0]
        report_branch_name =str(branch).split('-')[1]
        
        time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        address_query = """select address from ac_branch where cid = 'TDCLPC' and branch_code = {branch_code}""".format(branch_code=report_branch_code)        
        branch_row = db.executesql(address_query,as_dict=True)
        v_branch_address = branch_row[0]['address']

        
        if from_date and to_date and branch:


            # total cash + bank balance
            query1 = """  select account_code, max(account_name) as account_name, coalesce(sum(amount),0)  as cash_bal from ac_voucher_details where branch_code= {branch_code} and v_date < '{fromdate}' and status = 'POSTED' and account_code in (
                        select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type in ('Cash','Bank') and account_code in (
                        select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code = {branch_code})) group by account_code   
            """.format(fromdate=from_date, branch_code=report_branch_code )         
               
            result1 = db.executesql(query1,as_dict=True)

            # total bank balance 
            # query2 = """ select account_code, max(account_name) as account_name, coalesce(sum(amount),0)  as bank_bal from ac_voucher_details where branch_code= {branch_code} and v_date < '{fromdate}' and status = 'POSTED' and account_code in (
            #             select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type= 'Bank' and account_code in (
            #             select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code = {branch_code})) group by account_code           
            # """.format(fromdate=from_date, branch_code=report_branch_code )         
               
            # result2 = db.executesql(query2,as_dict=True)

            # total bank and cash 
            query3 = """select coalesce(sum(amount),0)  as cash_bank_bal from ac_voucher_details where branch_code= {branch_code} and v_date < '{fromdate}' and status = 'POSTED' and account_code in (
				select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type in ('Bank','Cash') and account_code in (
				select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code = {branch_code}) )     
            """.format(fromdate=from_date, branch_code=report_branch_code )         
               
            result3 = db.executesql(query3,as_dict=True)
            tot_cash_bank = result3[0]['cash_bank_bal']            

            # total received from from corporate 
            query4 = """select 	coalesce(sum(amount),0)*(-1)  as tot_corp from ac_voucher_details where branch_code={branch_code} and v_date between '{fromdate}' and '{todate}' and status = 'POSTED' and account_code in (
                        select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type = 'Corporate' and account_code in (
                        select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code = {branch_code}) )
            """.format(fromdate=from_date,todate=to_date, branch_code=report_branch_code )         
               
            result4 = db.executesql(query4,as_dict=True)
            tot_corp = result4[0]['tot_corp']

            # cash, bank, corporate total 
            query5 = """select sum(total) as total from (
                        select coalesce(sum(amount),0)  as total from ac_voucher_details where branch_code= {branch_code} and v_date < '{fromdate}' and status = 'POSTED' and account_code in (
                        select account_code from ac_cash_bank where account_type in ('Cash','Bank') and account_code in (
                        select account_code from ac_account_branch where branch_code = {branch_code}) )				
                        union all	
                        select 		 coalesce(sum(amount),0)*(-1)  as total from ac_voucher_details where branch_code= {branch_code} and v_date between '{fromdate}' and '{todate}' and 
                        status = 'POSTED' and account_code in (
                                select account_code from ac_cash_bank where account_type ='Corporate' and account_code in (
                                select account_code from ac_account_branch where branch_code = {branch_code}) )

                        union all
                        select coalesce(sum(amount),0)*(-1) total from ac_voucher_details where branch_code= {branch_code} and  (v_date between '{fromdate}' and '{todate}') 
		                and status= 'POSTED' and account_code like '4%'                         
                                ) as t
            """.format(todate=to_date,fromdate=from_date, branch_code=report_branch_code )  
            # return query5      
               
            result5 = db.executesql(query5,as_dict=True)
            total_receipt = result5[0]['total']

            # gl heads 
            query6 = """select account_code, max(account_name) as account_name, sum(amount)as amount from ac_voucher_details where  branch_code={branch_code} and STATUS='POSTED'
                        and (v_date between '{fromdate}' and '{todate}')  and account_code not like '4333%' and account_code not like '11666%' and account_code not in (
                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code} and account_code in (
                            select account_code from ac_cash_bank)
                        ) group by account_code order by account_code
            """.format(todate=to_date,fromdate=from_date, branch_code=report_branch_code )         
               
            result6 = db.executesql(query6,as_dict=True)

            # total expense 
            query8 = """select coalesce(sum(amount),0) as tot_exp from ac_voucher_details where cid = 'TDCLPC' and branch_code={branch_code} and v_date between '{fromdate}' and '{todate}' and status='POSTED' 
                        and account_code not like '4333%' and account_code not like '11666%' and  account_code not in  (
                            select account_code from ac_cash_bank where account_type in ('Cash','Bank','Corporate') and account_code in (
                                    select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code})
                        )
                        """.format(todate=to_date,fromdate=from_date, branch_code=report_branch_code )                  
               
            result8 = db.executesql(query8,as_dict=True)   
            tot_exp = result8[0]['tot_exp'] 

            # closing cash 
            query9 = """select account_code, max(account_name) as account_name, coalesce(sum(amount),0)  as closing_cash 
                        from ac_voucher_details where branch_code= {branch_code} and v_date <= '{todate}' and status = 'POSTED' and account_code in (
                            select account_code from ac_cash_bank where account_type= 'Cash' and account_code in (
                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code})) group by account_code                                            
                        """.format(todate=to_date, branch_code=report_branch_code )                           
               
            result9 = db.executesql(query9,as_dict=True)   

            # closing bank 
            query10 = """select account_code, max(account_name) as account_name, coalesce(sum(amount),0)  as closing_bank 
                        from ac_voucher_details where branch_code= {branch_code} and v_date <= '{todate}' and status = 'POSTED' and account_code in (
                            select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type= 'Bank' and account_code in (
                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code})) group by account_code                             
                        """.format(todate=to_date, branch_code=report_branch_code )                           
               
            result10 = db.executesql(query10,as_dict=True)   

            # total cash and bank 
            query11 = """select coalesce(sum(amount),0)  as tot_closing
			            from ac_voucher_details where branch_code= {branch_code} and v_date <= '{todate}' and status = 'POSTED' and account_code in (
                            select account_code from ac_cash_bank where cid = 'TDCLPC' and account_type in ('Cash','Bank') and account_code in (
                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code}))                                            
                        """.format(todate=to_date, branch_code=report_branch_code )                           
               
            result11 = db.executesql(query11,as_dict=True) 
            tot_closing  =  result11[0]['tot_closing']

            # total cosing cash/bank + total expense 
            query12 = """select coalesce(sum(amount)) as amount from (
                            select sum(amount) as amount from ac_voucher_details where branch_code={branch_code} and v_date between '{fromdate}' and '{todate}' and status='POSTED' and
                            account_code NOT LIKE '4333%' AND account_code NOT LIKE '11666%' and account_code not in  (
                                            select account_code from ac_cash_bank where account_type in ('Cash','Bank','Corporate') and account_code in (
                                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code})
                                        )
                            union all			
                            select coalesce(sum(amount),0)  as amount from ac_voucher_details where branch_code= {branch_code} and 
                            v_date <= '{todate}' and status = 'POSTED' and account_code in (
                                            select account_code from ac_cash_bank where account_type in ('Cash','Bank') and account_code in (
                                            select account_code from ac_account_branch where cid = 'TDCLPC' and branch_code ={branch_code}))    ) as q                                                             
                        """.format(fromdate=from_date,todate=to_date, branch_code=report_branch_code )                           
               
            result12 = db.executesql(query12,as_dict=True) 
            total_pay  =  result12[0]['amount']

            # micellaneous receipt
            query13 = """select account_code,max(account_name) as account_name, coalesce(sum(amount),0)*(-1) as amount from ac_voucher_details where cid = 'TDCLPC' and branch_code= {branch_code} and  
                        (v_date between '{fromdate}' and '{todate}') and status= 'POSTED' and account_code like '4%' group by account_code                                     
                        """.format(fromdate=from_date,todate=to_date, branch_code=report_branch_code )                           
               
            result13 = db.executesql(query13,as_dict=True)               
            
            
        else:
            print("Form data is missing")

    return dict(branch_name=user_branch_name,result1=result1,result6=result6,tot_exp=tot_exp,address=v_branch_address,
    tot_cash_bank=tot_cash_bank,tot_corp=tot_corp,total_receipt=total_receipt,from_date=from_date,to_date=to_date,result9=result9,
    tot_closing=tot_closing,result10=result10,result13=result13,total_pay=total_pay,report_branch_code=report_branch_code,time=time,report_branch_name=report_branch_name)


# # ref details/
# @action("reports/ref_details", method=["GET", "POST"])
# @action.uses("reports/ref_details.html", auth, T, db, session)
# def ref_details():
#     if not session.get('user_id'):
#         redirect(URL('login'))
#     else:
#         username = session.get('user_id')
#         user_branch_code = session.get('branch_code')        
#         user_branch_name = session.get('branch_name')        
#         role = session['role']

#         from_date = request.POST.get('from_date')
#         to_date = request.POST.get('to_date')
#         branch = request.POST.get('branch')
#         # account = request.POST.get('account')
#         account = '66666270352110-240'
#         report_branch_code =str(branch).split('-')[0]
#         report_branch_name =str(branch).split('-')[1]
#         # report_branch_name =str(branch).split('-')[1]
#         time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")       


#         branch_query=''
#         branch_query2=''
#         if report_branch_code =='99':
#             branch_query=""
#             branch_query2=""
#         else:
#             branch_query="and branch_code ='"+report_branch_code+"'"
#             branch_query2="and d.branch_code ='"+report_branch_code+"'"

#         results=[]
#         account_name=''
#         account_group=''
#         opening_balance= ''

#         address_query= """select address from ac_branch where branch_code = {branch_code}""".format(branch_code=report_branch_code)
#         address_row = db.executesql(address_query,as_dict=True)   
#         address = address_row[0]['address']    


#         if from_date and to_date and branch:


#             # account_row = db.executesql("select * from ac_accounts where account_code= '%s'",placeholders=account,as_dict=True)
#             account_row = db(db.ac_accounts.account_code == account).select().first()
#             account_name = account_row.account_name
#             account_class= account_row.class_name
#             account_group= account_row.group_name

#             # query1= """select coalesce(sum(amount),0) as opening_balance from ac_voucher_details where account_code = '{ac_code}' and v_date < '{fromdate}' 
#             # and status='POSTED' {branch_code}
#             # """.format(ac_code=account,fromdate=from_date, todate=to_date,branch_code=branch_query )
            
#             query1 = """select sum(opening_balance) as opening_balance ,sum(rem_balance)+sum(opening_balance) as rem_balance from (
#                         select sum(amount) as opening_balance,0 as rem_balance from ac_voucher_details where cid = 'TDCLPC' and account_code = '{ac_code}' and v_date < '{fromdate}' and status='POSTED'  {branch_code}
#                         union all
#                         select 0 as opening_balance, sum(amount) rem_balance from ac_voucher_details where cid = 'TDCLPC' and account_code = '{ac_code}' and v_date between '{fromdate}' and '{todate}'  and status='POSTED' {branch_code}
#                         ) as q1
#                     """.format(ac_code=account,fromdate=from_date, todate=to_date,branch_code=branch_query )
            
#             result1 = db.executesql(query1,as_dict=True)
#             opening_balance= result1[0]['opening_balance']
#             rem_balance= result1[0]['rem_balance']
            
            
#             query2 = """
#                    SELECT d.sl, cast(d.v_date as date) as v_date,h.narration as narration,
#                             CASE WHEN amount > 0 THEN amount ELSE 0 END AS debit,
#                             CASE WHEN amount < 0 THEN -amount ELSE 0 END AS credit
#                     FROM  ac_voucher_details as d 
#                     join ac_voucher_head as h on d.sl=h.sl
#                     where d.cid = 'TDCLPC' and account_code = '{ac_code}' and d.v_date between '{fromdate}' and '{todate}' and d.status= 'POSTED' {branch_code} order by d.id asc
#             """.format(ac_code=account,fromdate=from_date, todate=to_date,branch_code=branch_query2 )
            
#             results = db.executesql(query2,as_dict=True)

#             query3="""
#                     select sum(debit) as total_debit, sum(-credit) total_credit,sum(total) net_change from (
#                     select sum(amount) as debit, 0 as credit, 0 as total from ac_voucher_details where cid = 'TDCLPC' and  account_code = '{ac_code}' and amount>0 and v_date between '{fromdate}' and '{todate}' and status='POSTED' {branch_code}
#                     union all
#                     select 0 as debit, sum(amount),0 as total from ac_voucher_details where cid = 'TDCLPC' and  account_code = '{ac_code}' and amount<0 and v_date between '{fromdate}' and '{todate}' and status='POSTED' {branch_code}
#                     union all
#                     select 0 as debit,0 as credit, sum(amount) as total from ac_voucher_details  where cid = 'TDCLPC' and account_code = '{ac_code}' and v_date between '{fromdate}' and '{todate}'  and status='POSTED' {branch_code}) as q3
#                     """.format(ac_code=account,fromdate=from_date,todate=to_date,branch_code=branch_query)
#             # print(query3)
            
#             results2 = db.executesql(query3, as_dict=True)
#             total_debit=results2[0]['total_debit']
#             total_credit=results2[0]['total_credit']
#             net_change = results2[0]['net_change']


#         else:
#             print("Form data is missing")

#     return dict(user=username, branch_name=report_branch_name, role=role, results=results,from_date=from_date,to_date=to_date,report_branch_code=report_branch_code, time=time,
#                 account_no=account, account_name=account_name,account_group=account_group,opening_balance=opening_balance,total_debit=total_debit,total_credit=total_credit,
#                 net_change=net_change,rem_balance=rem_balance,address=address)


# ref details
@action("reports/ref_details", method=["GET", "POST"])
@action.uses("reports/ref_details.html", auth, T, db, session)
def ref_details():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        branch = request.POST.get('branch')
        reference = request.POST.get('ref')
        ref_type = request.POST.get('ref_type')
        report_branch_code = str(branch).split('-')[0]
        report_branch_name = str(branch).split('-')[1]
        # print(reference)
        time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        ref_query=''

        if reference.strip()=='' or reference.strip() == None:
            ref_query=''
        else:
            ref_query = "and vr.ref_code = '"+reference+"'"
        
        # print(reference)

        address_query = """select address from ac_branch where cid = 'TDCLPC' and branch_code = {branch_code}""".format(branch_code=report_branch_code)        
        branch_row = db.executesql(address_query, as_dict=True)
        v_branch_address = branch_row[0]['address']
        
        if from_date and to_date and branch:
            # ref details
            query1 = """SELECT vr.ref_code, vr.ref_name, SUM(amount) AS tot_amount , ar.ref_type
                        FROM ac_voucher_reference AS vr 
                        LEFT JOIN ac_reference AS ar ON vr.ref_code = ar.ref_code
                        WHERE vr.cid ='TDCLPC' AND vr.v_date BETWEEN '{fromdate}' AND '{todate}' 
                        AND vr.status = 'POSTED' and vr.branch_code =  {branch_code} AND ar.ref_type = '{ref_type}' {ref_query}
                        GROUP BY vr.ref_code, vr.ref_name""".format(fromdate=from_date, todate=to_date, branch_code=report_branch_code,ref_query=ref_query,ref_type=ref_type)
            # return query1
            result1 = db.executesql(query1, as_dict=True)


            query2 = """SELECT ref_code, ref_name, CONCAT(vr.account_code,' - ',aa.account_name) AS account,vr.account_code,SUM(amount) AS tot  FROM ac_voucher_reference AS vr
                        LEFT JOIN ac_accounts AS aa ON vr.account_code = aa.account_code
                        WHERE vr.cid = 'TDCLPC' AND aa.cid='TDCLPC' AND branch_code= {branch_code} AND v_date BETWEEN '{fromdate}' AND '{todate}'  AND STATUS ='POSTED' GROUP BY ref_code, ref_name,vr.account_code 
                        """.format(fromdate=from_date, todate=to_date, branch_code=report_branch_code,ref_query=ref_query,ref_type=ref_type)
            # return query2
            result2 = db.executesql(query2, as_dict=True)
           

            # ref_details
            query3 = """SELECT vr.sl, vr.ref_code, vr.ref_name, vr.amount, vr.v_type, CAST(vr.v_date AS DATE) AS v_date, vr.status, vr.account_code, aa.account_name, vh.narration, ar.des 
                        FROM ac_voucher_reference AS vr
                        LEFT JOIN ac_accounts AS aa ON vr.account_code = aa.account_code 
                        LEFT JOIN ac_voucher_head AS vh ON vr.sl = vh.sl
                        LEFT JOIN ac_reference AS ar ON vr.ref_code = ar.ref_code
                        WHERE vr.cid ='TDCLPC' AND vr.v_date BETWEEN '{fromdate}' AND '{todate}' 
                        AND vr.branch_code = {branch_code}  AND vr.status = 'POSTED' AND ar.ref_type = '{ref_type}' {ref_query}""".format(fromdate=from_date, todate=to_date, branch_code=report_branch_code,ref_type=ref_type,ref_query=ref_query)
        
            # return query3
            result3 = db.executesql(query3, as_dict=True)

        else:
            print("Form data is missing")

    return dict(branch_name=user_branch_name, address=v_branch_address, from_date=from_date, to_date=to_date, report_branch_code=report_branch_code, time=time, report_branch_name=report_branch_name, result1=result1, result2=result2,result3=result3, ref_type=ref_type, reference=reference)


@action('reports/download_ref_details', method=['GET'])
@action.uses(db, session)
def download_ref_details():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.query.get('from_date')
        to_date = request.query.get('to_date')
        report_branch_code = request.query.get('branch_code')
        ref_type= request.query.get('ref_type')
        reference= request.query.get('reference')

        ref_query=''

        if reference.strip()=='' or reference.strip() == None:
            ref_query=''
        else:
            ref_query = "and vr.ref_code = '"+reference+"'"


        query1 = """SELECT vr.ref_code, vr.ref_name, SUM(amount) AS tot_amount , ar.ref_type
                        FROM ac_voucher_reference AS vr 
                        LEFT JOIN ac_reference AS ar ON vr.ref_code = ar.ref_code
                        WHERE vr.cid ='TDCLPC' AND vr.v_date BETWEEN '{fromdate}' AND '{todate}' 
                        AND vr.status = 'POSTED' and vr.branch_code =  {branch_code} AND ar.ref_type = '{ref_type}' {ref_query}
                        GROUP BY vr.ref_code, vr.ref_name""".format(fromdate=from_date, todate=to_date, branch_code=report_branch_code,ref_query=ref_query,ref_type=ref_type)
            # return query1
        result1 = db.executesql(query1, as_dict=True)


        query2 = """SELECT ref_code, ref_name, vr.account_code,aa.account_name,SUM(amount) AS tot  FROM ac_voucher_reference AS vr
                    LEFT JOIN ac_accounts AS aa ON vr.account_code = aa.account_code
                    WHERE vr.cid = 'TDCLPC' AND aa.cid='TDCLPC' AND branch_code= {branch_code} AND v_date BETWEEN '{fromdate}' AND '{todate}'  AND STATUS ='POSTED' GROUP BY ref_code, ref_name,vr.account_code 
                    """.format(fromdate=from_date, todate=to_date, branch_code=report_branch_code,ref_query=ref_query,ref_type=ref_type)
        
        # return query2
        result2 = db.executesql(query2, as_dict=True)
        

        # ref_details
        query3 = """SELECT vr.sl, vr.ref_code, vr.ref_name, vr.amount, vr.v_type, CAST(vr.v_date AS DATE) AS v_date, vr.status, vr.account_code, aa.account_name, vh.narration, ar.des 
                    FROM ac_voucher_reference AS vr
                    LEFT JOIN ac_accounts AS aa ON vr.account_code = aa.account_code 
                    LEFT JOIN ac_voucher_head AS vh ON vr.sl = vh.sl
                    LEFT JOIN ac_reference AS ar ON vr.ref_code = ar.ref_code
                    WHERE vr.cid ='TDCLPC' AND vr.v_date BETWEEN '{fromdate}' AND '{todate}' 
                    AND vr.branch_code = {branch_code}  AND vr.status = 'POSTED' AND ar.ref_type = '{ref_type}' {ref_query}""".format(fromdate=from_date, todate=to_date, branch_code=report_branch_code,ref_type=ref_type,ref_query=ref_query)
    
        # return query
        result3 = db.executesql(query3, as_dict=True)            

        
        csv_stream = StringIO()       
        csv_writer = csv.writer(csv_stream,quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(["Trans. Date", "Voucher Type", "Voucher No.", "Narration", "Description", "Total Expense", "Total Expense", "Total Expense"])
        
        for ref in result1:
            csv_writer.writerow([
                "'"+ref['ref_code'], 
                ref['ref_name'],
                '',
                '',
                '',  
                '',
                '',              
                ref['tot_amount'],                 
            ])
            for ref2 in result2:
                if ref2['ref_code'] == ref['ref_code'] and ref2['ref_name'] == ref['ref_name']:
                    csv_writer.writerow([
                    "'"+ref2['account_code'], 
                        ref2['account_name'],   
                        '',
                        '',
                        '',
                        '',
                        ref2['tot'],
                        ''              
                ])
                    for ref3 in result3:
                        if ref3['ref_code'] == ref2['ref_code']  and  ref3['account_code'] == ref2['account_code']  :
                            csv_writer.writerow([
                                str(ref3['v_date']), 
                                    ref3['v_type'],   
                                    ref3['sl'],   
                                    ref3['narration'],              
                                    ref3['des'],                                                  
                                    ref3['amount'],                                                  
                            ])

                    
        
        csv_content = csv_stream.getvalue()
        csv_stream.close()
        
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename="ref_details.csv"'        
        
        return csv_content


# imprest cash
@action("reports/imprest_cash", method=["GET", "POST"])
@action.uses("reports/imprest_cash.html", auth, T, db, session)
def imprest_cash():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.POST.get('from_date')
        to_date = request.POST.get('to_date')
        branch = request.POST.get('branch')
        report_branch_code =str(branch).split('-')[0]
        report_branch_name =str(branch).split('-')[1]
        # report_branch_name =str(branch).split('-')[1]
        time = date_fixed.strftime("%d/%m/%Y %H:%M:%S")

        address_query= """select address from ac_branch where branch_code = {branch_code}""".format(branch_code=report_branch_code)
        address_row = db.executesql(address_query,as_dict=True)   
        address = address_row[0]['address']  

        

        if from_date and to_date and branch:
            
            query1 = """ SELECT trans_date,note_amount,qty,total FROM ac_denomination_details WHERE cid = 'TDCLPC' AND branch_code = {branch_code} AND trans_date = '{todate}'
                        """.format(fromdate=from_date, todate=to_date,branch_code=report_branch_code )
            
            result1 = db.executesql(query1,as_dict=True)
            
            query2 = """SELECT COALESCE(total_amount,0) as total_amount, account_code,account_name,branch_code,branch_name FROM ac_denomination_head WHERE 
                        cid = 'TDCLPC' AND branch_code = {branch_code} AND trans_date = '{todate}'""".format(fromdate=from_date, todate=to_date,branch_code=report_branch_code )
            result2 = db.executesql(query2,as_dict=True)

            if result2:
                total_amount = result2[0]['total_amount']
                account_code = result2[0]['account_code']
                account_name= result2[0]['account_name']
            else:
                total_amount = 0
                account_code = ""
                account_name= ""

            # print(total_amount)          
            
        else:
            print("Form data is missing")

    return dict(user=username,address=address, branch_name=user_branch_name, role=role, result1=result1,total_amount=total_amount,from_date=from_date,to_date=to_date,report_branch_code=report_branch_code, time=time,report_branch_name=report_branch_name,
                account_code=account_code,account_name=account_name)

# download imprest cash
@action('reports/download_imprest_cash', method=['GET'])
@action.uses(db, session)
def download_imprest_cash():
    if not session.get('user_id'):
        redirect(URL('login'))
    else:
        username = session.get('user_id')
        user_branch_code = session.get('branch_code')        
        user_branch_name = session.get('branch_name')        
        role = session['role']

        from_date = request.query.get('from_date')
        to_date = request.query.get('to_date')
        report_branch_code = request.query.get('branch_code')       
        report_branch_name = request.query.get('branch_name')      

        d = datetime.datetime.strptime(to_date, "%Y-%m-%d") 

        trans_date = d.strftime("%d-%B-%YY")
        print(trans_date)
        
        
        query1 = """ SELECT trans_date,note_amount,qty,total FROM ac_denomination_details WHERE cid = 'TDCLPC' AND branch_code = {branch_code} AND trans_date = '{todate}'
                        """.format(fromdate=from_date, todate=to_date,branch_code=report_branch_code )
        # return query1
            
        result1 = db.executesql(query1,as_dict=True)
            
        query2 = """SELECT total_amount, account_code,account_name,branch_code,branch_name FROM ac_denomination_head WHERE 
                        cid = 'TDCLPC' AND branch_code = {branch_code} AND trans_date = '{todate}'""".format(fromdate=from_date, todate=to_date,branch_code=report_branch_code )
        result2 = db.executesql(query2,as_dict=True)

        total_amount = result2[0]['total_amount']
        account_code = result2[0]['account_code']
        account_name= result2[0]['account_name']

        csv_stream = StringIO()       
        csv_writer = csv.writer(csv_stream,quoting=csv.QUOTE_MINIMAL)
        csv_writer.writerow(["Daily Imprest Cash Closing Statement"])
        csv_writer.writerow(["Date : ",trans_date])
        csv_writer.writerow(["Branch : ",report_branch_name])

        csv_writer.writerow([])

        csv_writer.writerow(["Trans. Date", "Note Details","Quantity","Total"])

        for row in result1:
            csv_writer.writerow([
                str(row['trans_date']), 
                int(row['note_amount']), 
                row['qty'] ,
                row['total'] 
            ])

        csv_writer.writerow([])

        csv_writer.writerow(["", "","Total Amount:",total_amount])

        
        
        csv_content = csv_stream.getvalue()
        csv_stream.close()
        
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = 'attachment; filename="ImprestCash.csv"'        
        
        return csv_content

