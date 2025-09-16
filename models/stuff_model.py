from uuid import UUID
from sqlmodel import Field, Relationship

from models.auditing import Auditing
from models.invoice_model import Invoice
from models.invoice_stuff_link_model import InvoiceStuffLink



class Stuff(Auditing, table=True):
    file_path: str
    file_name: str
    
    invoice: Invoice = Relationship(link_model=InvoiceStuffLink)