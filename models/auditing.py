from datetime import datetime

from sqlmodel import Field
from models.persistent import Persistent


class Auditing(Persistent):
    created_at:datetime = Field(default_factory=datetime.now)
    updated_at:datetime= Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})
    
    
    
    
    