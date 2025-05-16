import enum
from typing import List
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

db = SQLAlchemy()


class User(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(
        String(120), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(200), nullable=False)
    fullname: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean(), nullable=True, default=True)
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="user")

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "fullname": self.fullname,
            "isActive": self.is_active
            # do not serialize the password, its a security breach
        }

    def __repr__(self):
        return self.fullname


# Agrego un modelo para guardar los tokens bloquados por cierres de sesion
class TokenBlockedList(db.Model):
    id: Mapped[int] = mapped_column(primary_key=True)
    jti: Mapped[str] = mapped_column(String(50), nullable=False)


class Favorites_Types(enum.Enum):
    planet = 1
    people = 2
    vehicle = 3
    film = 4


class People(db.Model):
    __tablename__ = "people"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="people")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "favoriteCount": len(self.favorites)
        }

    def __repr__(self):
        return self.name

    def serialize_favorites(self):
        favorite_users = list(
            map(lambda fav: fav.user.first_name + " " + fav.user.last_name, self.favorites))
        return {
            "id": self.id,
            "name": self.name,
            "favoriteCount": len(self.favorites),
            "favoriteUsers": favorite_users
        }


class Planet(db.Model):
    __tablename__ = "planet"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    favorites: Mapped[List["Favorite"]] = relationship(back_populates="planet")

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "favoriteCount": len(self.favorites)
        }

    def __repr__(self):
        return self.name


class Favorite(db.Model):
    __tablename__ = "favorites"
    id: Mapped[int] = mapped_column(primary_key=True)
    type: Mapped[Favorites_Types] = mapped_column(Enum(Favorites_Types))
    planet_id: Mapped[int] = mapped_column(
        ForeignKey("planet.id"), nullable=True)
    planet: Mapped[Planet] = relationship(back_populates="favorites")
    people_id: Mapped[int] = mapped_column(
        ForeignKey("people.id"), nullable=True)
    people: Mapped[People] = relationship(back_populates="favorites")
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped[User] = relationship(back_populates="favorites")

    def serialize(self):
        favorite_item = None
        favorite_type = ""
        if self.type == Favorites_Types.people:
            favorite_type = "people"
            favorite_item = self.people.serialize()
        elif self.type == Favorites_Types.planet:
            favorite_type = "planet"
            favorite_item = self.planet.serialize()

        return {
            "id": self.id,
            "type": favorite_type,
            "favoriteItem": favorite_item
        }

    def __repr__(self):
        return "Favorite"
