from typing import Union

from pydantic import BaseModel


class ScopeBase(BaseModel):
    name: str
    description: Union[str, None] = None


class ScopeCreate(ScopeBase):
    pass


class Scope(ScopeBase):
    id: int
    owner_id: int

    class Config:
        orm_mode = True


class UserBase(BaseModel):
    username: str
    password: str


class UserCreate(UserBase):
    scopes: list[Scope] = []


class User(UserBase):
    id: int

    class Config:
        orm_mode = True
