from uuid import UUID
from sqlmodel import Field

from models.auditing import Auditing



class Invoice(Auditing, table=True):
    file_path: str
    file_name: str
    
    