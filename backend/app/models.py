"""Database models for the anime music quiz application."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


class Song(SQLModel, table=True):
    """Song information sourced from YouTube or manual input."""

    __tablename__ = "songs"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False, index=True)
    anime_title: str = Field(nullable=False, index=True)
    youtube_url: str = Field(nullable=False)
    youtube_video_id: str = Field(nullable=False, index=True)
    start_time_seconds: int = Field(default=0, ge=0)
    status: str = Field(default="pending", index=True)
    notes: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Room(SQLModel, table=True):
    """Represents a quiz room that players can join via a code."""

    __tablename__ = "rooms"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(nullable=False, unique=True, index=True)
    host_name: str = Field(nullable=False)
    target_score: int = Field(default=5, ge=1)
    max_players: int = Field(default=8, ge=1)
    round_duration_seconds: int = Field(default=120, ge=10)
    status: str = Field(default="waiting", index=True)
    winning_player_id: Optional[int] = Field(default=None, foreign_key="players.id")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Player(SQLModel, table=True):
    """Player participating in a room."""

    __tablename__ = "players"
    __table_args__ = (UniqueConstraint("room_id", "nickname", name="uq_room_nickname"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="rooms.id", nullable=False, index=True)
    nickname: str = Field(nullable=False)
    score: int = Field(default=0, ge=0)
    is_host: bool = Field(default=False)
    joined_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class Round(SQLModel, table=True):
    """Single round where one song is played and players guess."""

    __tablename__ = "rounds"

    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="rooms.id", nullable=False, index=True)
    song_id: int = Field(foreign_key="songs.id", nullable=False)
    status: str = Field(default="playing", index=True)
    started_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    ended_at: Optional[datetime] = Field(default=None)
    duration_seconds: int = Field(default=120, ge=10)
    winning_player_id: Optional[int] = Field(default=None, foreign_key="players.id")


class Guess(SQLModel, table=True):
    """Stores guesses players make during a round."""

    __tablename__ = "guesses"

    id: Optional[int] = Field(default=None, primary_key=True)
    round_id: int = Field(foreign_key="rounds.id", nullable=False, index=True)
    player_id: int = Field(foreign_key="players.id", nullable=False, index=True)
    guess_text: str = Field(nullable=False)
    similarity: float = Field(default=0.0, ge=0.0, le=1.0)
    is_correct: bool = Field(default=False)
    submitted_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class SkipVote(SQLModel, table=True):
    """Tracks players that voted to skip the current song."""

    __tablename__ = "skip_votes"
    __table_args__ = (UniqueConstraint("round_id", "player_id", name="uq_round_skip"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    round_id: int = Field(foreign_key="rounds.id", nullable=False, index=True)
    player_id: int = Field(foreign_key="players.id", nullable=False, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
