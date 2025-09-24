"""Pydantic schemas used by the API."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SongCreate(BaseModel):
    title: str
    anime_title: str = Field(description="Expected answer when players guess the anime title.")
    youtube_url: str
    start_time_seconds: int = Field(default=0, ge=0)
    notes: Optional[str] = None
    status: Optional[str] = Field(default="pending")

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = {"pending", "approved", "rejected"}
        if value not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return value


class SongUpdate(BaseModel):
    title: Optional[str] = None
    anime_title: Optional[str] = None
    youtube_url: Optional[str] = None
    start_time_seconds: Optional[int] = Field(default=None, ge=0)
    notes: Optional[str] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        allowed = {"pending", "approved", "rejected"}
        if value not in allowed:
            raise ValueError(f"status must be one of {sorted(allowed)}")
        return value


class SongRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    anime_title: str
    youtube_url: str
    youtube_video_id: str
    start_time_seconds: int
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime


class SongPlaybackInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    youtube_url: str
    youtube_video_id: str
    start_time_seconds: int
    anime_title: Optional[str] = None


class RoomCreate(BaseModel):
    host_name: str = Field(description="Name of the room host (will become the first player).")
    code: Optional[str] = Field(default=None, min_length=3, max_length=12)
    target_score: int = Field(default=5, ge=1)
    max_players: int = Field(default=8, ge=1)
    round_duration_seconds: int = Field(default=120, ge=10)


class PlayerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nickname: str
    score: int
    is_host: bool
    joined_at: datetime


class RoomState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    status: str
    target_score: int
    max_players: int
    round_duration_seconds: int
    host_name: str
    created_at: datetime
    updated_at: datetime
    winning_player_id: Optional[int] = None
    players: List[PlayerRead]


class RoomJoinResponse(BaseModel):
    room: RoomState
    player: PlayerRead


class JoinRoomRequest(BaseModel):
    nickname: str = Field(min_length=1, max_length=32)


class RoundStartRequest(BaseModel):
    song_id: Optional[int] = None
    duration_seconds: Optional[int] = Field(default=None, ge=10)
    reveal_answer: bool = False


class RoundState(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    room_code: str
    status: str
    duration_seconds: int
    started_at: datetime
    ends_at: datetime
    winning_player_id: Optional[int]
    song: SongPlaybackInfo
    skip_votes: int
    total_players: int


class GuessCreate(BaseModel):
    player_id: int
    guess_text: str = Field(min_length=1, max_length=200)


class GuessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    player_id: int
    guess_text: str
    similarity: float
    is_correct: bool
    submitted_at: datetime


class GuessResponse(BaseModel):
    guess: GuessRead
    is_correct: bool
    similarity: float
    round_status: str
    player_score: int
    room_status: str
    target_score: int
    winning_player_id: Optional[int] = None


class SkipRequest(BaseModel):
    player_id: int


class SkipResponse(BaseModel):
    skip_votes: int
    total_players: int
    round_status: str


class LeaderboardEntry(BaseModel):
    player_id: int
    nickname: str
    score: int
    is_host: bool


class LeaderboardResponse(BaseModel):
    room_code: str
    players: List[LeaderboardEntry]
