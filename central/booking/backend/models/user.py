from pydantic import BaseModel, Field
from typing import Optional, Literal
import bcrypt

class UserModel(BaseModel):
    name: str
    email: Optional[str] = None
    password: str = Field(..., min_length=6)
    role: Literal['customer', 'admin', 'manager']

    def set_password(self, password):
        bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(bytes, salt)

    def check_password(self, password) -> bool:
        bytes = password.encode('utf-8')
        return bcrypt.checkpw(bytes, self.password)
