"""
This file defines the database models
"""

from .common import db, Field,session
from py4web import action
from pydal.validators import *
import datetime
from py4web.utils.auth import Auth
from .common_cid import date_fixed

### Define your table below
#
# db.define_table('thing', Field('name'))
#
## always commit your models to avoid problems later 
#
# db.commit()
#
##############
# def get_current_date():
#     return datetime.datetime.now()

# @action.uses(db,session)
# def get_current_user():
#     return session['user_id'] 

signature=db.Table(db,'signature',
                Field('field1','string',length=100,default='',writable=False,readable=False), 
                Field('field2','integer',default=0,writable=False,readable=False),
                Field('note','string',length=100,writable=True,readable=False,default='_'),  
                Field('created_by','string',length=100,writable=False,readable=False),                
                Field('created_on','datetime',default=date_fixed,writable=False,readable=False),
                Field('updated_by','string',length=100,writable=False,readable=False),
                Field('updated_on','datetime',writable=False),
                )

db.define_table('ac_accounts_class',
                Field('id','integer',),
                Field('cid','string',length=10,default="TDCLPC",writable=False,readable=False),
                Field('class_code','integer', requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db,'ac_accounts_class.class_code','Code already exists'),IS_INT_IN_RANGE(10,99,error_message='Value must be number between 10 and 99')]),
                Field('class_name','string',length=100,requires=[IS_NOT_EMPTY('Enter Class Name'),IS_NOT_IN_DB(db,'ac_accounts_class.class_name','Class name already exists')]),
                Field('class_type','string',length=50,default="Asset",requires=IS_IN_SET(['Asset', 'Liability', 'Expense','Income'])),
                Field('active','string',length=10,default='T',writable=False,readable=False),
                Field('is_default','string',length=10,default='T',readable=False,writable=False),
                signature,
                migrate=False
                )


db.define_table('ac_accounts_group',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False,readable=False),
                Field('group_code','integer',requires=[IS_NOT_EMPTY('Enter a Value'), IS_NOT_IN_DB(db,'ac_accounts_group.group_code','Code already exists')]),
                Field('group_name','string',length=100,requires=IS_NOT_EMPTY('Enter Group Name')),
                Field('class_code','integer',requires=IS_NOT_EMPTY()),
                Field('class_name','string',length=100,requires=[IS_IN_DB(db, 'ac_accounts_class.class_name', '%(class_name)s'),IS_NOT_EMPTY('Select Class')]),
                Field('class_type','string',length=50,requires=IS_NOT_EMPTY()),
                Field('seq_in_trial_balance','string',length=50, default='0',writable=False,readable=False),
                Field('active','string',length=50,default="T",readable=False,writable=False),
                Field('is_default','string',length=50,default='T',readable=False,writable=False),
                signature,
                migrate=False
                )


db.define_table('ac_accounts',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False),                
                Field('account_code','string',length=50,requires=[IS_NOT_EMPTY('Enter Account Code'),IS_NOT_IN_DB(db,'ac_accounts.account_code','Code already exists')]),
                Field('account_name','string',length=100,requires=IS_NOT_EMPTY('Enter Account Name')),
                Field('group_code','integer'),
                Field('group_name','string',length=100,requires=IS_IN_DB(db, 'ac_accounts_group.group_name', '%(group_name)s',error_message='Select Accounts Group')),
                Field('class_code','integer'),
                Field('class_name','string',length=100,requires=IS_IN_DB(db, 'ac_accounts_class.class_name', '%(class_name)s',error_message='Select Accounts Class')),
                Field('class_type','string',length=100),                
                Field('active','string',length=10,default="T",writable=False,readable=False),
                Field('is_default','string',length=10,default='T',writable=False,readable=False),
                signature,
                migrate=False
                )

db.define_table('ac_ref_type',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False,readabale=False),
                Field('ref_type','string',length=100,requires=IS_NOT_EMPTY('Enter referance type')),
                signature,
                migrate=False
                )

db.define_table('ac_reference',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False),                
                Field('ref_code','string',length=100,requires=[IS_NOT_EMPTY('Enter referance Code'),IS_NOT_IN_DB(db,'ac_reference.ref_code','Code already exists')]),
                Field('ref_name','string',length=100,requires=IS_NOT_EMPTY('Enter referance name')),
                Field('des','string',length=100,default=''),
                Field('active','string',length=10,default='T',writable=False,readable=False),
                Field('ref_type','string',length=100,requires=IS_IN_DB(db, 'ac_ref_type.ref_type', '%(ref_type)s',error_message='Select ref. type')),
                signature,
                migrate=False
                )


from pydal.validators import Validator

class IS_IN_ACCOUNTS(Validator):
    def __init__(self, error_message='Account does not exist'):
        self.error_message = error_message

    def __call__(self, value, record_id=None, field=None):
        account = db(db.ac_accounts.account_code == value).select().first()
        if account:
            return (value, None)
        else:
            return (value, self.error_message)


db.define_table('ac_cash_bank',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False,readable=False),                
                Field('account_code','string',length=50,requires=[IS_NOT_IN_DB(db,'ac_cash_bank.account_code','Code already exists'),IS_IN_ACCOUNTS()]),
                Field('account_name','string',length=100,requires=IS_NOT_EMPTY('Enter Account')),
                Field('account_type','string',length=100,requires=[IS_IN_SET(['Cash','Bank','Corporate']),IS_NOT_EMPTY('Please select one')]),
                signature,
                migrate=False
                )


db.define_table('ac_voucher_head',
                Field('id','integer'),
                Field('sl','integer',requires=[IS_NOT_EMPTY('Sl Missing'),IS_NOT_IN_DB(db,'ac_voucher_head.sl','Sl already exists')]),
                Field('cid','string',length=10,default="TDCLPC",writable=False),
                Field('branch_code','integer'),
                Field('v_type','string',length=100,requires=IS_IN_SET(['Journal','Contra', 'Payment','Receive'])),
                Field('v_type_sl','integer',default=0),
                Field('v_date','datetime', default=datetime.datetime.now().date),                
                Field('narration','string',length=255),
                Field('status','string',length=100,default='DRAFT'),
                Field('total_amount','double',default=''),
                Field('post_by','string',length=100),
                Field('post_time','datetime'),  
                signature,              
                migrate=False
                )

db.define_table('ac_voucher_details',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False),
                Field('sl','integer'),
                Field('account_code','string',length=50,),
                Field('account_name','string',length=100,),
                Field('amount','double'),
                Field('class_code','integer'),
                Field('class_type','string',length=50),
                Field('group_code','integer'),
                Field('group_type','string',length=50,),
                Field('v_type','string',length=100,),
                Field('v_type_sl','integer'),                
                Field('v_date','datetime'),
                Field('status','string',length=100),
                Field('branch_code','integer'),
                Field('balance','double'),
                Field('post_time','timestamp without time zone'),
                signature,
                migrate=False
                )

db.define_table('ac_branch',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",readable=False,writable=False),                
                Field('branch_code','integer' ,requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db,'ac_branch.branch_code','Code already exists'),IS_INT_IN_RANGE(99,999,error_message='Value must be number between 100 and 999')]),              
                Field('branch_name','string',length=100,requires=IS_NOT_EMPTY('Please enter branch code')),                
                Field('address','string',length=255,default="_",requires= IS_NOT_EMPTY('Please enter branch code')),      
                signature,
                migrate=False
                )


db.define_table('ac_account_branch',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False),                              
                Field('account_code','string',length=50,requires= IS_NOT_EMPTY('Please enter account no.')),                
                Field('account_name','string',length=100,requires= IS_NOT_EMPTY('Please enter account name')),   
                Field('branch_code','integer', requires=IS_NOT_EMPTY('Please enter branch code')),                
                Field('branch_name','string',length=100,requires=[IS_IN_DB(db, 'ac_branch.branch_name', '%(branch_name)s'),IS_NOT_EMPTY('Select Class')]),   
                signature,  
                migrate=False
                )

def is_optional_email(value, error=None):
    if not value:
        return (value, None)  # Allow empty email
    is_email = IS_EMAIL()
    return is_email(value) 


db.define_table('ac_auth_user',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",readable=False,writable=False),           
                Field('username','string',length=100,requires=[IS_NOT_EMPTY('Enter user name'),IS_NOT_IN_DB(db,'ac_auth_user.username','User name already exists')]),
                Field('email','string',length=100,requires = is_optional_email),
                Field('password', 'string',length=50,requires=[IS_NOT_EMPTY('Enter password'),IS_LENGTH(minsize=8,error_message="Password must be of 8 charachters")]),
                Field('first_name','string',length=50,requires=IS_NOT_EMPTY('Enter first name')), 
                Field('last_name','string',length=50,requires=IS_NOT_EMPTY('Enter last name')),               
                Field('sso_id','string',length=50,readable=False,writable=False),
                Field('action_token','string',length=100,readable=False,writable=False),
                Field('last_password_change','datetime',readable=False,writable=False),
                Field('past_passwords_hash','string',length=100,readable=False,writable=False),
                Field('branch_code','integer',requires=IS_NOT_EMPTY('Branch code missing')),                
                Field('branch_name','string',length=100,requires=[IS_IN_DB(db, 'ac_branch.branch_name', '%(branch_name)s'),IS_NOT_EMPTY('Select Class')]), 
                Field('role','string',length=100,requires=[IS_NOT_EMPTY('Please select role'),IS_IN_SET(['ADMIN','VIEWER','EDITOR-1st','EDITOR-2nd'])],zero='Select'),                  
                Field('status','string',length=100,requires=[IS_NOT_EMPTY('Please select status'),IS_IN_SET(['ACTIVE', 'INACTIVE'])],default="ACTIVE"), 
                # Field('status',requires=IS_IN_SET(['ACTIVE','INACTIVE']),zero='Select'), 
                Field('contact','string',length=20, requires=[IS_MATCH('^01\d{9}$', error_message='Please enter a valid mobile number of 11 digits starting with 01'),IS_NOT_EMPTY('Please enter phone number'),IS_NOT_IN_DB(db,'ac_auth_user.contact','Mobile no. already exists')]),
                Field('f_password','integer',default='1',readable=False,writable=False),
                signature,
                migrate=False
                )

db.define_table('ac_voucher_reference',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False),
                Field('sl','integer'),
                Field('account_code','string',length=50,),
                Field('ref_code','string',length=100), 
                Field('ref_name','string',length=100),
                Field('amount','double'),                
                Field('v_type','string',length=100),                
                Field('v_date','datetime'),                               
                Field('status','string',length=100), 
                Field('branch_code','integer'),        
                Field('post_time','datetime'),   
                signature,           
                migrate=False
                )

db.define_table('ac_account_ref',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False),
                Field('account_code','string',length=50,requires=[IS_NOT_EMPTY('Please enter account code'),IS_NOT_IN_DB(db,'ac_account_ref.account_code','Code already exists')]),
                Field('account_name','string',length=100,requires=IS_NOT_EMPTY('Please enter account name')),                            
                Field('ref_type','string',length=100,requires=IS_IN_DB(db, 'ac_ref_type.ref_type', '%(ref_type)s')),    
                Field('ref_type_id','integer',readable=False,writable=False),           
                signature,
                migrate=False
            )

db.define_table('ac_bank_note',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False),
                Field('note_code','string',length=50,requires =IS_NOT_EMPTY('Please enter code')),
                Field('note_amount','double',requires=[IS_NOT_EMPTY('Please enter amount'),IS_FLOAT_IN_RANGE(0.01,100000)]),                            
                Field('in_words','string',length=100,requires=IS_NOT_EMPTY('Please enter amount in words')),                            
                Field('type','string',default="Note",length=100),                              
                Field('status','string',default="ACTIVE",length=100,requires=IS_IN_SET(['ACTIVE','INACTIVE'])),                              
                signature,
                migrate=False
            )

db.define_table('ac_denomination',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False),
                Field('note_code','string',length=50),
                Field('note_amount','double'),                            
                Field('in_words','string',length=100,),                            
                Field('type','string',length=100),                              
                Field('qty','integer'),    
                Field('total','double'),                                                   
                Field('account_code','string',length=50),                                                   
                Field('account_name','string',length=100),                                                   
                Field('branch_code','integer'),                                                   
                Field('branch_name','string',length=100),                                                   
                Field('trans_date','date'),                            
                Field('created_by','string',length=100),                            
                Field('created_on','datetime'),                            
                Field('updated_by','string',length=100),                            
                Field('updated_on','datetime'),                            
                Field('field1','string',length=100),                            
                Field('field2','integer'),                            
                Field('note','string',length=100),          
                migrate=False
            )

db.define_table('ac_denomination_head',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC",writable=False),
                Field('trans_id','string',length=20),
                Field('total_amount','double'),                                                   
                Field('account_code','string',length=50),                                                   
                Field('account_name','string',length=100),                                                   
                Field('branch_code','integer'),                                                   
                Field('branch_name','string',length=100),                                                   
                Field('trans_date','date'),                            
                signature,
                migrate=False
            )

db.define_table('ac_denomination_details',
                Field('id','integer'),
                Field('cid','string',length=10,default="TDCLPC"),
                Field('trans_id','string',length=20),
                Field('note_code','string',length=50),
                Field('note_amount','double'),                            
                Field('in_words','string',length=100,),                            
                Field('type','string',length=100),                              
                Field('qty','integer'),    
                Field('total','double'),                                                   
                Field('account_code','string',length=50),                                                   
                Field('account_name','string',length=100),                                                   
                Field('branch_code','integer'),                                                   
                Field('branch_name','string',length=100),                                                   
                Field('trans_date','date'),                            
                signature,      
                migrate=False
            )

#-----------This Is for Add Item Table------------------#

db.define_table('inventory_items',
                Field('id', 'integer'),
                Field('cid', 'string', length=10, default="TDCLPC", writable=False, readable=False),
                Field('item_code', 'string', length=20, requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'inventory_items.item_code', 'Item code already exists')]),
                Field('item_name', 'string', length=100, requires=[IS_NOT_EMPTY('Enter Item Name'), IS_NOT_IN_DB(db, 'inventory_items.item_name', 'Item name already exists')]),
                Field('category', 'string', length=50, requires=IS_NOT_EMPTY('Enter Category')),
                Field('unit', 'string', length=20, requires=IS_IN_SET(['Piece', 'Kg', 'Liter', 'Pack', 'Box', 'Dozen'])),
                # signature,
                migrate=False
            )
db.define_table('unit',
                Field('id', 'integer'),
                Field('cid', 'string', length=10, default="TDCLPC", writable=False, readable=False),
                Field('unit_code', 'string', length=20, requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'unit.unit_code', 'Unit code already exists')]),
                Field('unit_name', 'string', length=50, unique=True, requires=IS_NOT_EMPTY('Enter Unit Name')),
                migrate=False
            )
db.define_table('category',
                Field('id', 'integer'),
                Field('cid', 'string', length=10, default="TDCLPC", writable=False, readable=False),
                Field('category_code', 'string', length=20, requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'category.category_code', 'Category code already exists')]),
                Field('category_name', 'string', length=100, unique=True, requires=IS_NOT_EMPTY('Enter Category Name')),
                migrate=False
            )
db.define_table('brand',
                Field('id', 'integer'),
                Field('cid', 'string', length=10, default="TDCLPC", writable=False, readable=False),
                Field('brand_code', 'string', length=20, requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'brand.brand_code', 'Brand code already exists')]),
                Field('brand_name', 'string', length=100, unique=True, requires=IS_NOT_EMPTY('Enter Brand Name')),
                migrate=False
            )
db.define_table('product',
                Field('id', 'integer'),
                Field('cid', 'string', length=10, default="TDCLPC", writable=False, readable=False),
                Field('item_code', 'string', length=20,requires=[IS_NOT_EMPTY(), IS_NOT_IN_DB(db, 'inventory_items.item_code', 'Item code already exists')]),
                Field('item_name', 'string', length=100,requires=[IS_NOT_EMPTY('Enter Item Name'), IS_NOT_IN_DB(db, 'inventory_items.item_name', 'Item name already exists')]),
                Field('category', 'string', length=50, requires=[IS_IN_DB(db, 'category.category_name', '%(category_name)s'),IS_NOT_EMPTY('Select Category')]), 
                Field('unit', 'string', length=20, requires=IS_NOT_EMPTY('Enter Unit')),
                signature,
                migrate=True
            )







# db.commit()

