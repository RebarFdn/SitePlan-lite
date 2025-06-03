#from models import BillExpence , BillFees , PaybillModel, InvoiceModel, Supplier

from modules.site_db import SiteDb

trip = {
    "tid": "77997",
    "venue":"Florida",
    "name": "T Lewis"
}
db = SiteDb(db_name='trips')
items = db.save_item(trip)
print(items)

#print(db)
#db.reset_repo()
#print(db)

"""
paybill = dict(
    ref = "Bill-01",   # Bill to job refference no
    project_id = "DV0765", # Current project _id
    date = 1778965784,  # Paybill generation date
    date_starting = 1778965784, # Work period starting
    date_ending = 1778965784,   # Work period ending
    mainTitle = "Interim Paybill", # Bill heading
    subTitle = "Patio Floors, First Floor walls",
    # fees
    contractor = 20,
    insurance = 5,
    misc = 5,
    overhead = 2,
)
fees = BillFees( **paybill )
paybill['fees'] = fees


#bill = PaybillModel( **paybill )
mac = {
    "id": "7788",
    "name": "Mac's",
    "taxid": "34477789"
}
sup = Supplier( **mac )
print({
    #"fees": fees,
    #"expence": expence,
    "bill": InvoiceModel(supplier=sup)
    })
"""
