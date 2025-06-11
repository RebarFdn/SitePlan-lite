
from typing import Coroutine, List, Any
from asyncio import sleep
from starlette.requests import Request
from starlette.responses import HTMLResponse, JSONResponse
from ezchart import ezChart
from database import Recouch, local_db
from logger import logger
from modules.supplier import supplier_name_index, get_supplier, update_supplier, get_supplier_key_index
from modules.utils import tally, timestamp, load_metadata, set_metadata, generate_id
from models import (Project, project_phases, project_template ,DepositModel, WithdrawalModel, 
ExpenceModel, BillFees , PaybillModel, Supplier, InvoiceItem, InvoiceModel, UnpaidTaskModel, SupplierInvoiceRecord)
from modules.site_db import SiteDb
from config import TEMPLATES

import time
from plyer import notification
#from tabulate import tabulate

_databases:dict = { # Project Databases
            "local":"lite-projects", 
            "local_partitioned": False,
            "slave":"lite-projects", 
            "slave_partitioned": False ,
            "invoice_db": "temp_invoice"           
            }
# connection to site-projects database 
db_connection:Coroutine = local_db(db_name=_databases.get('local'))   

# CRUD OPERATIONS

async def all_projects( conn:Coroutine=db_connection )->list:
    try:
        projects:dict = await conn.get(_directive="_design/project-index/_view/name-view") 
        return projects.get('rows')          
    except Exception as e:
        logger().error( str(e))
    finally: del(projects)


async def get_project(id:str=None, conn:Coroutine=db_connection)->dict:
    """Retreive a single Project Object from storage

    Args:
        id (str, optional): The project _id . Defaults to None.
        conn (Coroutine, optional): connection to a couchdb  database. Defaults to db_connection.

    Returns:
        dict: The Project Object
    """
    r:dict = await conn.get(_directive=id)
    try:       
        return r
    except Exception as e:
        logger().error(str(e))        
    finally: del(r)  


async def save_project(data:dict=None, user:str=None, conn:Coroutine=db_connection )->dict:   
    try:
        data['_id'] = generate_id(name=data.get('name')) 
        new_project = project_template() | data
        new_project['meta_data'] = load_metadata(property='properties', value=list(new_project.keys()), db=_databases)
        new_project['meta_data'] = set_metadata(property='created', value=timestamp(),  metadata=new_project.get('meta_data'))
        new_project['meta_data'] = set_metadata(property='created_by', value=user, metadata=new_project.get('meta_data'))
        await conn.post( json=new_project )  
        return new_project  
    except Exception as e:
        print(e)  
        

async def update_project(data:dict=None, conn:Coroutine=db_connection):
        try:            
            return await conn.put( json=data)            
        except Exception as e:
            logger().exception(e)
            

async def delete_project( id:str=None, conn:Coroutine=db_connection ):    
    try:            
        await conn.delete(_id=id)
    except Exception as e:
        logger().exception(e)
    
# Utility Methods 
async def projects_index()->list:
    """   

    Returns:
        list: _description_
    """
    return [{"_id": project.get('id'), "name": project.get('key')} for project in await all_projects()]


async def get_project_ids()->list:
    return [project.get('id') for project in await all_projects()]


def log_activity(title:str=None, message:str=None, project:dict=None)->None:
    project['activity_logs'].append(
        {
            "id": timestamp(),
            "title": title,
            "description": message 
        }
    )  


# Project specific utilities
async def reset_invoice_db()->None:
    db = SiteDb(db_name=_databases.get('invoice_db'))
    await db.reset_repo()
    
def doc_count()->int:
    db = SiteDb(db_name=_databases.get('invoice_db'))
    return db.doc_count() 

def set_prop( prop:str=None ):
    if prop[len(prop)-1: ] == 's':
        return prop[ :-1]
    else:
        return prop

def notice(title:str=None, message:str=None)->None:
    notification.notify(
        title=title, 
        message=message, 
        app_name='SiteLite',        
        timeout=20 
        )
     
async def piechart(request:Request, project:dict=None):
    account:dict = {
        "current_balance": 0,
        "deposits": tally(project['account']['transactions']['deposit']),
        "withdrawals": tally(project['account']['transactions']['withdraw']),
        "expences": tally(project['account']['expences']),
        "paybills": tally(project['account']['records']['paybills']),
        "invoices": tally(project['account']['records']['invoices'])
    }
    account['current_balance'] = account["deposits"] - sum([account["withdrawals"], account["expences"]])
    labels = []
    series = []
    for key, val in account.items():
        if key in ['deposits', 'withdrawals']:
            pass  
        else:
            labels.append(key)
            series.append(val)
    options = {
        "chart": {
                "width": '380',
                "height": '280',
                "type": 'pie',
            },
        "series": series,
        "labels": labels,
        "responsive": [
            {
            "breakpoint": 1000,
            "options": {
                "plotOptions": {
                    "bar": {
                        "horizontal": False
                    },                
                    "pie": {
                        "expandOnClick": False
                    },
                    "legend": {
                        "position": "bottom"
                    }
                }
            }
            }
        ]

    }
    chart = ezChart(options=options )
    return HTMLResponse(chart.chart())


# Project accounting utilities 
async def account_statistics(request:Request, project:dict=None)-> TEMPLATES.TemplateResponse:
    """Account Statistics Reporting"""
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)
    account:dict = {
        "current_balance": 0,
        "deposits": tally(project['account']['transactions']['deposit']),
        "withdrawals": tally(project['account']['transactions']['withdraw']),
        "expences": tally(project['account']['expences']),
        "paybills": tally(project['account']['records']['paybills']),
        "invoices": tally(project['account']['records']['invoices'])
    }
    account['current_balance'] = account["deposits"] - account["withdrawals"]
    
    return TEMPLATES.TemplateResponse(
        '/components/project/account/Stastics.html', 
        {
            "request": request, 
            "project": {"_id": project.get('_id'), 
                        "account": account
                        }
                        })


async def transact_deposit( request:Request, project:dict=None, data:dict=None )-> TEMPLATES.TemplateResponse:
    """Handle Funds Deposit records on a project's account"""
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)
    if data:  
        data['date'] = timestamp(date=data.get('date')) # Update timestamp to int
        deposit = DepositModel( **data ) # Validate data
                                            
        project['account']['transactions']['deposit'].append(deposit.model_dump())        
        project['account']['updated'] = timestamp()
        log_activity( title="Funds Deposit", message = f"""A deposit with refference {data.get('ref')} 
            was made on  Project  {project.get('_id')} Account . by { data.get('user') }""" ,
            project=project)  
        try:
            await update_project(data=project) # save changes
             
            return TEMPLATES.TemplateResponse(
                        '/components/project/account/Deposits.html', 
                        {
                            "request": request, 
                            "project": {
                                "_id": project.get('_id'), 
                                "account": {
                                    "transactions": {
                                        "deposit": project.get('account', {}).get('transactions', {}).get('deposit')
                                        }
                                }
                            } 
                        })

        except Exception as e:
                logger().exception(e)
        finally:                
                del(project) # clean up
                del(deposit)
    else:
        return TEMPLATES.TemplateResponse(
                        '/components/project/account/Deposits.html', 
                        {
                            "request": request, 
                            "project": {
                                "_id": project.get('_id'), 
                                "account": {
                                    "transactions": {
                                        "deposit": project.get('account', {}).get('transactions', {}).get('deposit')
                                        }
                                }
                            } 
                        })


async def update_deposit(request:Request, project:dict=None, data:dict=None )-> TEMPLATES.TemplateResponse:
    pass

async def delete_deposit(request:Request, project:dict=None, id:str=None )-> TEMPLATES.TemplateResponse:
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process deposit
    if id: 
        deposit = [doc for doc in project.get('account', {}).get('transactions', {}).get('deposit') if doc.get('id') == id] 
        if deposit:
            project['account']['transactions']['deposit'].remove(deposit[0])
            try:
                await update_project(data=project) 
                return TEMPLATES.TemplateResponse(
                        '/components/project/account/Deposits.html', 
                        {
                            "request": request, 
                            "project": {
                                "_id": project.get('_id'), 
                                "account": {
                                    "transactions": {
                                        "deposit": project.get('account', {}).get('transactions', {}).get('deposit')
                                        }
                                }
                            } 
                        })

            except Exception as e:
                    logger().exception(e)
            finally:                
                    del(project) # clean up
                    del(deposit)
    else:
        return TEMPLATES.TemplateResponse(
            '/components/project/account/Deposits.html', 
            {
                "request": request, 
                "project": {
                    "_id": project.get('_id'), 
                    "account": {
                        "transactions": {
                            "deposit": project.get('account', {}).get('transactions', {}).get('deposit')
                        }
                    }
                } 
            })


async def transact_withdrawal( request:Request, project:dict=None, data:dict=None )-> TEMPLATES.TemplateResponse:
    """Handle Withrawals records on a project's account
    
        Requires a project.account object or project's id string 
    """ 
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process withdrawals
    if data:   
        data['date'] = timestamp(date=data.get('date')) # Update timestamp to int
        withdrawal = WithdrawalModel( **data ) # Validate data                      
        project['account']['transactions']['withdraw'].append(withdrawal.model_dump())
        project['account']['updated'] = timestamp()
        log_activity( title="Funds Withdrawal", message = f"""A withdrawal with refference {data.get('ref')} 
            was drawn from Project  {project.get('_id')} Account . by { data.get('user') }""",
            project=project )  
        #processProjectAccountBallance()
        
        try:
            await update_project(data=project)           
            return TEMPLATES.TemplateResponse(
                '/components/project/account/Withdrawals.html', 
                {
                    "request": request, 
                    "project": {
                        "_id": project.get('_id'), 
                        "account": {
                        "transactions": {
                            "withdraw": project.get('account', {}).get('transactions', {}).get('withdraw')
                        }
                    }
                        
                    } 
                })

        except Exception as e:
                logger().exception(e)
        finally:                
                del(project) # clean up
    else:
        return TEMPLATES.TemplateResponse(
            '/components/project/account/Withdrawals.html', 
            {"request": request, "project": {
                        "_id": project.get('_id'), 
                        "account": {
                        "transactions": {
                            "withdraw": project.get('account', {}).get('transactions', {}).get('withdraw')
                        }
                    }
                        
                    }  })


async def delete_withdrawal(request:Request, project:dict=None, id:str=None )-> TEMPLATES.TemplateResponse:
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process withdrawals
    if id: 
        withdrawal = [doc for doc in project.get('account', {}).get('transactions', {}).get('withdraw') if doc.get('id') == id] 
        if withdrawal:
            project['account']['transactions']['withdraw'].remove(withdrawal[0])
            try:
                await update_project(data=project) 
                return TEMPLATES.TemplateResponse(
                        '/components/project/account/Withdrawals.html', 
                        {"request": request, "project": {
                        "_id": project.get('_id'), 
                        "account": {
                        "transactions": {
                            "withdraw": project.get('account', {}).get('transactions', {}).get('withdraw')
                        }
                    }
                        
                    }  })

            except Exception as e:
                    logger().exception(e)
            finally:                
                    del(project) # clean up
                    del(withdrawal)
    else:
        return TEMPLATES.TemplateResponse(
                        '/components/project/account/Withdrawals.html', 
                        {"request": request, "project": {
                        "_id": project.get('_id'), 
                        "account": {
                        "transactions": {
                            "withdraw": project.get('account', {}).get('transactions', {}).get('withdraw')
                        }
                    }
                        
                    }  })


async def record_expence( request:Request, project:dict=None, data:dict=None )-> TEMPLATES.TemplateResponse:
    """Handle Expence data recording
    
        Requires a project.account object or project's id string 
    """ 
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process withdrawals
    if data:   
        data['date'] = timestamp(date=data.get('date')) # Update timestamp to int
        expence = ExpenceModel( **data ) # Validate data                     
        project['account']['expences'].append(expence.model_dump())
        withdrawal = WithdrawalModel(date=expence.date, ref=expence.ref, amount=expence.total, recipient=expence.claimant)
        withdrawal.user=None
        project['account']['transactions']['withdraw'].append(withdrawal.model_dump())
        project['account']['updated'] = timestamp()
        log_activity( title="Expence Recorded", message = f"""Expence and withdrawal with refference {data.get('ref')} 
            was recorded and drawn from Project  {project.get('_id')} Account . by { data.get('user') }""",
            project=project )  
        #processProjectAccountBallance()
        
        try:
            await update_project(data=project)           
            return TEMPLATES.TemplateResponse(
                        '/components/project/account/Expences.html', 
                        {"request": request, "project": {"_id": project.get('_id'), "account": project.get('account')} })

        except Exception as e:
                logger().exception(e)
        finally:                
                del(project) # clean up
    else:
        return {"error": 501, "message": "You did not provide any data for processing."}


async def delete_expence(request:Request, project:dict=None, id:str=None )-> TEMPLATES.TemplateResponse:
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process expence
    if id: 
        expence = [doc for doc in project.get('account', {}).get('expences', []) if doc.get('id') == id] 
        if expence:
            # Remove withdrawal refferenec , Check for if refs in account withdrawals and remove 
            withdraw_ref = [doc for doc in project.get('account', {}).get('transactions', {}).get('withdraw') if doc.get('ref') == expence[0].get('ref')] 
            if  withdraw_ref:
                project['account']['transactions']['withdraw'].remove(withdraw_ref[0])
            project['account']['expences'].remove(expence[0])
            try:
                await update_project(data=project) 
                return TEMPLATES.TemplateResponse(
                        '/components/project/account/Expences.html', 
                        {
                            "request": request, 
                            "project": {
                                "_id": project.get('_id'), 
                                "account": { "expences": project.get('account',{}).get('expences', [])}
                            } })


            except Exception as e:
                    logger().exception(e)
            finally:                
                    del(project) # clean up
                    del(expence)
    else:
        return TEMPLATES.TemplateResponse(
                        '/components/project/account/Expences.html', 
                        {
                            "request": request, 
                            "project": {
                                "_id": project.get('_id'), 
                                "account": { "expences": project.get('account',{}).get('expences', [])}
                            } })

def can_record_invoice(project:dict=None, data:dict=None)->bool:
    """Check in the project repository if invoice is existing

    Args:
        project (dict, optional): The Project repository. Defaults to None.
        data (dict, optional): Invoice record to be saved Defaults to None.

    Returns:
        bool: True if it exist False if not
    """
    invoice = [ item for item in project['account']['records']['invoices'] if item.get('invoiceno') == data.get('invoiceno').strip() ]
    notice(title='Invoice Check', message=f"We found {invoice}")
    if invoice:
        
        return False
    else:
        
        return True


async def record_invoice( request:Request, project:dict=None, data:dict=None )-> TEMPLATES.TemplateResponse:
    """Handle Purchase data recording
    
        Requires a project.account object or project's id string 
    """ 
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process withdrawals
    invoices = project['account']['records']['invoices']
    suppliers = [ item.get('name') for item in await supplier_name_index()]          
    if data: 
        if can_record_invoice(project=project, data=data):# check if the invoice was already saved
            
            index = await get_supplier_key_index()
            id = index.get(data.get('name'))
            if id:
                supplier_data = await get_supplier(id=id ) 
            else:
                # create supplier or
                supplier_data = None

            if supplier_data:
                supplier = Supplier( **supplier_data )
                transaction =  SupplierInvoiceRecord( **data )
                supplier_data['account']['transactions'].append(transaction.model_dump())
                await update_supplier(data=supplier_data)
            else:
                supplier = Supplier( **data )
                # create a new supplier here
            data['supplier'] = supplier
            data['date'] = timestamp(date=data.get('date')) # Update timestamp to int
            invoice = InvoiceModel( **data ) # Validate data 
            in_data = invoice.model_dump()
            # get load items 
            db = SiteDb(db_name=_databases.get('invoice_db')) # Temporary invoice items store
            invoice_items =  [item for item in await db.get_items()if item.get('invoiceno') == invoice.invoiceno] # retreive items 
            in_data['items'] = invoice_items   

            invoices.append(in_data)
            withdrawal = WithdrawalModel(date=invoice.date, ref=invoice.invoiceno, amount=invoice.total, recipient=invoice.supplier.name)
            withdrawal.user=None
            project['account']['transactions']['withdraw'].append(withdrawal.model_dump())
            project['account']['updated'] = timestamp()
            log_activity( title="Invoice Recorded", message = f"""invoice and withdrawal with refference {invoice.invoiceno } 
                was recorded and drawn from Project  {project.get('_id')} Account . by { data.get('user') }""",
                project=project )  
            #processProjectAccountBallance()
            
            await update_project(data=project) 
        else:
            pass
        try:
           
            return TEMPLATES.TemplateResponse(
                '/components/project/account/Invoices.html', 
                {
                    "request": request, 
                    "suppliers": suppliers,
                    "project": {
                        "_id": project.get('_id'), 
                        "account": {
                            "records": {
                                "invoices": invoices
                            }
                        }
                    } 
                })

        except Exception as e:
                logger().exception(e)
        finally:                
                del(project) # clean up
                await reset_invoice_db() # resets the invoice items store
    else:        
        return TEMPLATES.TemplateResponse(
                '/components/project/account/Invoices.html', 
                {
                    "request": request, 
                    "suppliers": suppliers,
                    "project": {
                        "_id": project.get('_id'), 
                        "account": {
                            "records": {
                                "invoices": invoices
                            }
                        }
                    } 
                })


async def save_invoice_item(request:Request, data:dict=None )-> TEMPLATES.TemplateResponse:
    db = SiteDb(db_name=_databases.get('invoice_db'))
    if data:
        try: 
            data['itemno'] = doc_count()           
            inv_item = InvoiceItem( **data )
            invoices = await db.save_item(inv_item.model_dump())
            return TEMPLATES.TemplateResponse(
                    '/components/project/account/InvoiceItems.html', 
                    {
                        "request": request, 
                        "invoices": invoices
                    })
        except Exception as e:
                logger().exception(e)
        finally:                
                del(db) # clean up
    else:
        invoices =  await db.get_items()
        return TEMPLATES.TemplateResponse(
            '/components/project/account/InvoiceItems.html', 
            {
                "request": request, 
                "invoices": invoices
            })


async def get_invoice_items(request:Request )-> TEMPLATES.TemplateResponse:
    db = SiteDb(db_name=_databases.get('invoice_db'))
    invoices =  await db.get_items()
    
    try:
        return TEMPLATES.TemplateResponse(
            '/components/project/account/InvoiceItems.html', 
            {
                "request": request, 
                "invoices": invoices,
                
            })
        
    except Exception as e:
        logger().exception(e)
    finally:                
        del(db) # clean up
        del(invoices)
  

async def delete_invoice( request:Request, project:dict=None, id:str=None )-> TEMPLATES.TemplateResponse:
    """Handle deletion of invoice data recording
    
        Requires a project.account object or project's id string 
    """ 
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process withdrawals
    if id: 
        invoice = [doc for doc in project.get('account', {}).get('records', {}).get('invoices') if doc.get('inv_id') == id] 
        if invoice:
            # Remove withdrawal refferenec , Check for if refs in account withdrawals and remove 
            withdraw_ref = [doc for doc in project.get('account', {}).get('transactions', {}).get('withdraw') if doc.get('ref') == invoice[0].get('invoiceno') and invoice[0].get('supplier').get('name') == doc.get('recipient')] 
            if  withdraw_ref:
                log_activity( title="Invoice Deleted", message = f"""invoice and withdrawal with refference {invoice[0].get('invoiceno') } 
                    was deleted from Project  {project.get('_id')} Account .""",
                    project=project 
                )    
                project['account']['transactions']['withdraw'].remove(withdraw_ref[0])
            
            project['account']['records']['invoices'].remove(invoice[0])

            project['account']['updated'] = timestamp()
              
            try:
                suppliers = [ item.get('name') for item in await supplier_name_index()]
                await update_project(data=project)           
                return TEMPLATES.TemplateResponse(
                    '/components/project/account/Invoices.html', 
                    {
                        "request": request, 
                        "suppliers":suppliers,
                        "project": {
                            "_id": project.get('_id'), 
                            "account": {
                                "records": {
                                    "invoices": project.get('account', {}).get('records', {}).get('invoices')
                                }
                            }
                        } 
                    })

            except Exception as e:
                    logger().exception(e)
            finally:                
                    del(project) # clean up
    else:
        return TEMPLATES.TemplateResponse(
                '/components/project/account/Invoices.html', 
                {
                    "request": request, 
                    "project": {
                        "_id": project.get('_id'), 
                        "account": {
                            "records": {
                                "invoices": project.get('account', {}).get('records', {}).get('invoices')
                            }
                        }
                    } 
                })
   

async def create_paybill( request:Request, project:dict=None, data:dict=None )-> TEMPLATES.TemplateResponse:  
    """Creates new paybills
    
        Requires a project.account object or project's id string 
    """ 
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process withdrawals
    if data:   
        data['date'] = timestamp(date=data.get('date')) # Update timestamp to int
        data['date_starting'] = timestamp(date=data.get('date_starting'))
        data['date_ending'] = timestamp(date=data.get('date_ending'))
        data["project_id"] = project.get('_id')
        fees = BillFees( **data ) # Validate data  
        data['fees'] = fees
        paybill = PaybillModel(**data)                   
        project['account']['records']['paybills'].append(paybill.model_dump())
        log_activity( title="New Paybill", message = f"""Paybill {data.get('ref')} 
            was created for {project.get('_id')} by { data.get('user') }""",
            project=project )
        try:
            await update_project(data=project)           
            return TEMPLATES.TemplateResponse(
                '/components/project/account/PayBills.html', 
                {
                    "request": request, 
                    "project": {
                        "_id": project.get('_id'), 
                        "account": project.get('account')
                    } 
                })
        except Exception as e:
                logger().exception(e)
        finally:                
                del(project) # clean up
    else:
        return {"error": 501, "message": "You did not provide any data for processing."}


async def get_unpaid_tasks(project:dict=None)->list:
    #return [job.get('tasks') for job in project.get('jobs') ]
    tasks = []
    for job in project.get('jobs'):
        if job.get("progress") > 0:
            for task in job.get('tasks'):
                if task.get('progress') > 0:
                    unpaid_task = UnpaidTaskModel( **task )
                    unpaid_task.set_quantity_percent
                    unpaid_task.calculate_total
                    tasks.append(unpaid_task)#unpaid_task.model_dump())
    return tasks


async def get_paybill( request:Request, project:dict=None, bill_id:str=None )-> TEMPLATES.TemplateResponse:
    """Retreive a paybill object by given bill id """
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process withdrawals
    if bill_id:
        paybill = [bill for bill in project.get('account', {}).get('records', {}).get('paybills') if bill.get('id') == bill_id] 
        if paybill:
            current_bill = PaybillModel( **paybill[0] )
            current_bill.calculate_items_total
            current_bill.calculate_expence
            current_bill.calculate_total
            unpaid_tasks = await get_unpaid_tasks(project=project)
            try:                      
                return TEMPLATES.TemplateResponse(
                '/components/project/account/PayBill.html', 
                {
                    "request": request, 
                    "paybill": current_bill.model_dump(), #paybill[0],
                    "unpaid_tasks": unpaid_tasks
                })
            except Exception as e:
                    logger().exception(e)
            finally:                
                    del(project) # clean up
    else:
        return {"error": 501, "message": "Your Request was not processed."}


async def add_bill_item(request:Request, project:dict=None, iid:str=None )-> TEMPLATES.TemplateResponse:
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)  
    ids:list = iid.split('_')
    unpaid_tasks = await get_unpaid_tasks(project=project)
    task = [task for task in unpaid_tasks if task.id == ids[1]]
    paybill = [bill for bill in project.get('account').get('records').get('paybills') if bill.get('id') == ids[0]] 
        
    if task:
        if paybill:
            found_item = [item for item in paybill[0].get('items') if item.get('id') == task[0].id ]
            if found_item:
                notice(title='Check Paybill Item', message=f"Item with Id {task[0].id} was already added to the Bill.")
            else:

                paybill[0]['items'].append(task[0].model_dump())
                await update_project(data=project)
                # log the event
        try:                      
            return TEMPLATES.TemplateResponse(
                '/components/project/account/UpaidTasks.html', 
                {
                    "request": request,  
                    "paybill": paybill[0],              
                    "unpaid_tasks": unpaid_tasks
                })
        except Exception as e:
            logger().exception(e)
            return {"error": 501, "message": "Your Request was not processed."}
        finally:                
            del(project) # clean up
   
        



async def update_paybill( request:Request, project:dict=None, data:dict=None )-> TEMPLATES.TemplateResponse:
    """Retreive a paybill object by given bill id """

async def delete_paybill( request:Request, project:dict=None, bill_id:str=None )-> TEMPLATES.TemplateResponse:
    """Deletes a paybill object by given bill id """
    if type(project) == dict:
        pass
    elif type(project) == str:
        project = await get_project(id=project)         
    # process withdrawals
    if bill_id: 
        paybill:list = [bill for bill in project.get('account', {}).get('records', {}).get('paybills') if bill.get('id') == bill_id] 
        if paybill:
            # Remove withdrawal refferenec , Check for if refs in account withdrawals and remove 
            withdraw_ref = [doc for doc in project.get('account', {}).get('transactions', {}).get('withdraw') if doc.get('ref') == paybill[0].get('ref')] 
            if  withdraw_ref:
                project['account']['transactions']['withdraw'].remove(withdraw_ref[0])
            # delete paybill
            project['account']['records']['paybills'].remove(paybill[0])
            try:
                await update_project(data=project)           
                return TEMPLATES.TemplateResponse(
                    '/components/project/account/PayBills.html', 
                    {
                        "request": request, 
                        "project": {
                            "_id": project.get('_id'), 
                            "account": project.get('account')
                        } ,
                        
                    })
            except Exception as e:
                    logger().exception(e)
            finally:                
                    del(project) # clean up
    else:
        return {"error": 501, "message": "Your Request was not processed."}


class projectManager:
    """Handles Client side requests and responses 

        Returns an Html template 
    """
    id:str = None
    PROPERTIES_INDEX:list = ['index', 'phases', 'model']

    def __init__(self, id:str=None, properties:list=[]):
        self.id = id
        self.properties = properties
        
    
    async def create_new_project(self, request:Request):
        payload = project_template()
        async with request.form() as form:
            payload["name"] = form.get('name')
            payload["category"] = form.get('category')
            payload["standard"] = form.get('standard')
            payload["address"] = {
                    "lot": form.get('lot'), 
                    "street": form.get('street'), 
                    "town": form.get('town'),
                    "city_parish": form.get('city_parish'),
                    "country": form.get('country', "Jamaica") 
                }
            payload["owner"] = {
                "name": form.get('owner'),
                "contact": None,
                "address": {"lot": None, "street": None, "town": None,"city_parish": None,"country": None, }
                }
            payload["admin"]["leader"] =  form.get('lead')            
        try:     
            return await save_project(data=payload, user='ian') #username) 
        except Exception as e:
            return str(e)
        finally:            
            del(payload)
            
    
    async def _template(self, request:Request):
        # Process Create New and Delete Requests
        if request.method == 'POST':            
            if self.properties.__len__() > 0 and self.properties[0] == 'save':
                await self.create_new_project(request=request)
            else:
                pass
        elif request.method == 'DELETE':
            await delete_project(id=self.id) 
            await sleep(0.5)           
            self.id = 'index'                
        else:
            pass
        # Process Get Requests
        property_search = {
            'index': TEMPLATES.TemplateResponse('/components/project/Index.html', 
                        {"request": request, "projects": await all_projects()})
        }
        # 
        if self.id in self.PROPERTIES_INDEX:
            return property_search.get(self.id)
        else:
            pass
        # if self.id is a project id 
        self.project = await get_project(id=self.id)
        suppliers = [ item.get('name') for item in await supplier_name_index()]
        search_ = {
            'id': TEMPLATES.TemplateResponse(
                '/components/project/Project.html', 
                {"request": request, "project": self.project ,"suppliers":suppliers, "invoices": [] }),
            'account': TEMPLATES.TemplateResponse(
                '/components/project/Account.html', 
                {"request": request, "project": self.project }),
        }
        if self.properties:
            return search_.get(self.properties[0])
        else:
            return search_.get('id')



class ProjectClient:
    """Handles Api requests to the server  

        Returns Json 
    """
    id:str = None
    PROPERTIES_INDEX:list = ['index', 'phases', 'model', 'invoice_items']

    def __init__(self, id:str=None, properties:list=[]):
        self.id = id
        self.properties = properties   
    

    async def _jsonapi(self, request:Request):
        self._ids:list = await get_project_ids()
        _search:dict = {
            'index': TEMPLATES.TemplateResponse('/components/project/Index.html', 
                        {"request": request, "projects": await all_projects()}),
            'phases': JSONResponse( project_phases() ),
            'model': JSONResponse( project_template() ),
            'invoice_items': await get_invoice_items(request=request)
            
        }
        
        # Process Create New and Delete Requests
        if request.method == 'POST': 
            async with request.form() as form: # Aquire the form data
                form_data = dict(form) 
            
            if self.id == 'create': # checking... if request to create a project                 
                return JSONResponse({self.id: { key: val for key, val in form_data.items()}})
                # await self.create_new_project(request=request) 
                # self.id = 'index'   
            elif self.id == 'invoice_item':
                return await save_invoice_item(request=request, data=form_data )
            elif self.id in self._ids: # checking... if request to modify a project                
                self.project = await get_project(id=self.id)  #get and load the project
                
                if self.properties: # get instructions from properties
                    if self.properties[0] == 'deposit':  # Deposit Funds                      
                        return await transact_deposit(request=request, project=self.project, data=form_data)
                    elif self.properties[0] == 'withdraw':  # Withdraw Funds                      
                        return await transact_withdrawal(request=request, project=self.project, data=form_data)
                    elif self.properties[0] == 'expence':  # Record Expence                      
                        return await record_expence(request=request, project=self.project, data=form_data)
                    elif self.properties[0] == 'invoice':  # Record Invoice                      
                        return await record_invoice( request=request, project=self.project, data=form_data )
                    
                    elif self.properties[0] == 'paybill':  # Record Paybill                      
                        return await create_paybill( request=request, project=self.project, data=form_data )                   
                    elif self.properties[0] == 'billtask':  # Add item to paybill                      
                        return await add_bill_item( request=request, project=self.project, iid=self.properties[1] )  
                                  
                    

                    else:
                        return JSONResponse(self.project.get(self.properties[0]))
                else:
                    return JSONResponse({ self.id: self.project })

            else:
                pass
        elif request.method == 'DELETE':
            if self.properties:
                self.project = await get_project(id=self.id) 
                if self.properties.__len__() == 1:
                    pass
                elif self.properties.__len__() == 2:
                    if self.properties[0] == 'paybill':  # Delete Paybill                      
                        return await delete_paybill( request=request, project=self.project, bill_id=self.properties[1] )
                    elif self.properties[0] == 'deposit':  # Delete Paybill                      
                        return await delete_deposit( request=request, project=self.project, id=self.properties[1] )
                    elif self.properties[0] == 'withdraw':  # Delete witdrawal                     
                        return await delete_withdrawal( request=request, project=self.project, id=self.properties[1] )
                    elif self.properties[0] == 'expence':  # Delete expence                     
                        return await delete_expence( request=request, project=self.project, id=self.properties[1] )
                    elif self.properties[0] == 'invoice':  # Delete expence                     
                        return await delete_invoice( request=request, project=self.project, id=self.properties[1] )
                    
                    # other deletions
                   
                    

            else:
                if self.id in self._ids: #  request to delete project
                    await delete_project(id=self.id) 
                    await sleep(0.5)           
                    self.id = 'index'                
        else:
            pass
        # Process Get Requests
        
        # 
        if self.id in self.PROPERTIES_INDEX:
            return _search.get(self.id)
        else:
            pass
        # if self.id is a project id, 
        self.project = await get_project(id=self.id)  # get and load the project     
        #for item in self.project.get('days'):
        #    item['_id'] = item.get('id') 
        #    await sleep(0.05)
        #await update_project(data=self.project)

        _search['id'] = TEMPLATES.TemplateResponse(
                '/components/project/Home.html', 
                {"request": request, "project": self.project })
            
        
        if self.properties:
            if self.properties.__len__() == 1: 
                if self.properties[0] == 'chart':  # Statistics chart                      
                    return await piechart(request=request, project=self.project)
                elif self.properties[0] == 'stats':  # Account satatistics                      
                        return await account_statistics(request=request, project=self.project)
                elif self.properties[0] == 'withdraw':  # Withdraw Funds                      
                    return await transact_withdrawal(request=request, project=self.project)
                elif self.properties[0] == 'reset_invoice':
                    await reset_invoice_db()
                            

                else:
                    _search [self.properties[0]] = TEMPLATES.TemplateResponse(f'/components/project/{self.properties[0].capitalize()}.html', 
                    {"request": request, 'project': {'_id':self.id, self.properties[0]:  self.project.get(self.properties[0], {})}})
                    return _search.get(self.properties[0])
                
            elif self.properties.__len__() == 2:                
                prop:str = set_prop(self.properties[0])
                if self.properties[0] == 'paybill':
                    return await get_paybill( request=request, project=self.project, bill_id=self.properties[1] )  
                
                if type(self.project.get(self.properties[0]))  == list: 
                    # convert tasks list to task dictionary 
                    self.project[self.properties[0]] = {item.get('_id') if item.get('_id') else item.get('id'): item for item in self.project.get(self.properties[0])}

                return TEMPLATES.TemplateResponse(f'/components/project/{prop.capitalize()}.html', 
                    {"request": request, prop: self.project.get(self.properties[0], {}).get(self.properties[1]), "project": self.project})  
                             

                
        else:
            return _search.get('id')


class ProjectApi:
    """Handles Api requests to the server  

        Returns Json 
    """
    id:str = None
    PROPERTIES_INDEX:list = ['index', 'phases', 'model']

    def __init__(self, id:str=None, properties:list=[]):
        self.id = id
        self.properties = properties

    async def _jsonapi(self, request:Request):
        # Process Create New and Delete Requests
        if request.method == 'POST':            
            if self.properties.__len__() > 0 and self.properties[0] == 'logs':
                await self.create_new_project(request=request)
            else:
                pass
        elif request.method == 'DELETE':
            await delete_project(id=self.id) 
            await sleep(0.5)           
            self.id = 'index'                
        else:
            pass
        # Process Get Requests
        property_search = {
            'index': JSONResponse( await all_projects() ),
            'phases': JSONResponse( project_phases() ),
            'model': JSONResponse( project_template() )
        }
        # 
        if self.id in self.PROPERTIES_INDEX:
            return property_search.get(self.id)
        else:
            pass
        # if self.id is a project id 
        self.project = await get_project(id=self.id)        
        
        search_ = {
            'id': JSONResponse( self.project ),
            #'account': JSONResponse( self.project.get('account') ),
            
        }
        if self.properties:
            if self.properties.__len__() == 1: 
                search_[self.properties[0]] = JSONResponse( self.project.get(self.properties[0]) )
                return search_.get(self.properties[0])
            elif self.properties.__len__() == 2:
                if self.properties[0] == 'jobs': 
                    # convert tasks list to task dictionary 
                    self.project['jobs'] = {job.get('_id'): job for job in self.project.get('jobs')} 
                    return TEMPLATES.TemplateResponse('/components/project/Job.html', 
                    {"request": request, 'job': self.project.get(self.properties[0], {}).get(self.properties[1])})
                search_ [self.properties[0]] = JSONResponse( self.project.get(self.properties[0], {}).get(self.properties[1]) )
                return search_.get(self.properties[0])
        else:
            return search_.get('id')







