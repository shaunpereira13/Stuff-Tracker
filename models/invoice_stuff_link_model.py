from uuid import UUID
from sqlmodel import Field, SQLModel




class InvoiceStuffLink(SQLModel, table=True):
    stuff_id: UUID = Field(foreign_key="stuff.id",primary_key=True)
    invoice_id: UUID = Field(foreign_key="invoice.id",primary_key=True)
    
    