from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class Movie:
    _id: str 
    title: str
    director: str
    year: int
    cast: list[str] = field(default_factory=list)
    series: list[str] = field(default_factory=list)
    last_watched:  datetime = None
    rating: int = 0
    tags: list[str] = field(default_factory=list)   
    description: str = None
    video_link: str = None


@dataclass
class User:
    _id: str
    username: str
    email: str
    password: str
    movies: list[str] = field(default_factory=list)