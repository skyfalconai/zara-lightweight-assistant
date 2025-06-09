from pydantic import BaseModel, Field
from typing import Optional, Union, List
import time

class Chat(BaseModel):
    plugin: str
    query: Optional[str] = ""
    response: Optional[str] = ""
    media: Optional[Union[str, List[str]]] = ""  
    success: bool = True
    timestamp: float = Field(default_factory=time.time)
