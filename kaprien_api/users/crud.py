from typing import List

import bcrypt
from sqlalchemy.orm import Session

from kaprien_api.users import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return (
        db.query(models.User).filter(models.User.username == username).first()
    )


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = bcrypt.hashpw(
        user.password.encode("utf-8"), bcrypt.gensalt()
    )
    db_user = models.User(username=user.username, password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_scopes(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Scope).offset(skip).limit(limit).all()


def get_scope_by_name(db: Session, name: str):
    return db.query(models.Scope).filter(models.Scope.name == name).first()


def create_user_scope(db: Session, scope: schemas.ScopeCreate):
    db_scope = models.Scope(**scope.dict())
    db.add(db_scope)
    db.commit()
    db.refresh(db_scope)
    return db_scope


def user_add_scopes(
    db: Session, user: schemas.User, scopes: List[schemas.Scope]
):
    user.scopes = scopes
    db.commit()
    db.refresh(user)
    return user
