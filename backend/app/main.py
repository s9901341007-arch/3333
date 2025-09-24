"""FastAPI application that powers the anime music quiz platform."""

from __future__ import annotations

import os
import random
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, func, select

from .database import get_session, init_db
from .models import Guess, Player, Room, Round, SkipVote, Song
from .schemas import (
    GuessCreate,
    GuessRead,
    GuessResponse,
    JoinRoomRequest,
    LeaderboardEntry,
    LeaderboardResponse,
    PlayerRead,
    RoomCreate,
    RoomJoinResponse,
    RoomState,
    RoundStartRequest,
    RoundState,
    SkipRequest,
    SkipResponse,
    SongCreate,
    SongPlaybackInfo,
    SongRead,
    SongUpdate,
)
from .utils import compute_similarity, extract_youtube_id


ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "changeme")
DEFAULT_ALLOWED_ORIGINS = {"http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:4173"}


app = FastAPI(title="Anime Music Quiz API", version="0.1.0")


@app.on_event("startup")
def startup() -> None:
    init_db()


cors_origins = os.getenv("CORS_ALLOW_ORIGINS")
if cors_origins:
    allow_origins = {
        origin.strip()
        for origin in cors_origins.split(",")
        if origin.strip()
    }
    if not allow_origins:
        allow_origins = set(DEFAULT_ALLOWED_ORIGINS)
    allow_all_origins = False
else:
    # 預設允許所有來源，方便玩家透過主機的區網 IP 連線。
    allow_origins = {"*"}
    allow_all_origins = True

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(allow_origins),
    allow_credentials=not allow_all_origins,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/health")
async def read_health() -> dict[str, str]:
    """Health check endpoint returning a simple status payload."""

    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Dependencies & helpers
# ---------------------------------------------------------------------------


def require_admin_token(x_admin_token: str = Header(..., alias="X-Admin-Token")) -> str:
    expected_token = ADMIN_TOKEN
    if not expected_token:
        return x_admin_token
    if x_admin_token != expected_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin token")
    return x_admin_token


def _generate_room_code(session: Session, length: int = 5) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    while True:
        code = "".join(random.choice(alphabet) for _ in range(length))
        existing = session.exec(select(Room).where(Room.code == code)).first()
        if not existing:
            return code


def _get_room_or_404(session: Session, code: str) -> Room:
    room = session.exec(select(Room).where(Room.code == code.upper())).first()
    if not room:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return room


def _get_active_round(session: Session, room_id: int) -> Optional[Round]:
    return session.exec(
        select(Round).where(Round.room_id == room_id, Round.status == "playing").order_by(Round.started_at.desc())
    ).first()


def _build_room_state(session: Session, room: Room) -> RoomState:
    players = session.exec(select(Player).where(Player.room_id == room.id).order_by(Player.joined_at)).all()
    return RoomState(
        id=room.id,
        code=room.code,
        status=room.status,
        target_score=room.target_score,
        max_players=room.max_players,
        round_duration_seconds=room.round_duration_seconds,
        host_name=room.host_name,
        created_at=room.created_at,
        updated_at=room.updated_at,
        winning_player_id=room.winning_player_id,
        players=[PlayerRead.model_validate(player, from_attributes=True) for player in players],
    )


def _build_round_state(
    session: Session,
    round_obj: Round,
    room: Optional[Room] = None,
    *,
    reveal_answer: bool = False,
) -> RoundState:
    room = room or session.get(Room, round_obj.room_id)
    if room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    song = session.get(Song, round_obj.song_id)
    if song is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    skip_votes_count = session.exec(
        select(func.count()).select_from(SkipVote).where(SkipVote.round_id == round_obj.id)
    ).scalar() or 0
    player_count = session.exec(
        select(func.count()).select_from(Player).where(Player.room_id == room.id)
    ).scalar() or 0

    reveal_solution = reveal_answer or round_obj.status != "playing"

    playback = SongPlaybackInfo(
        id=song.id,
        title=song.title,
        youtube_url=song.youtube_url,
        youtube_video_id=song.youtube_video_id,
        start_time_seconds=song.start_time_seconds,
        anime_title=song.anime_title if reveal_solution else None,
    )

    return RoundState(
        id=round_obj.id,
        room_code=room.code,
        status=round_obj.status,
        duration_seconds=round_obj.duration_seconds,
        started_at=round_obj.started_at,
        ends_at=round_obj.started_at + timedelta(seconds=round_obj.duration_seconds),
        winning_player_id=round_obj.winning_player_id,
        song=playback,
        skip_votes=int(skip_votes_count or 0),
        total_players=int(player_count or 0),
    )


# ---------------------------------------------------------------------------
# Song management (admin)
# ---------------------------------------------------------------------------


@app.post("/admin/songs", response_model=SongRead, status_code=status.HTTP_201_CREATED)
def create_song(
    song_in: SongCreate,
    session: Session = Depends(get_session),
    _: str = Depends(require_admin_token),
) -> SongRead:
    youtube_id = extract_youtube_id(song_in.youtube_url)
    song = Song(
        title=song_in.title.strip(),
        anime_title=song_in.anime_title.strip(),
        youtube_url=song_in.youtube_url.strip(),
        youtube_video_id=youtube_id,
        start_time_seconds=song_in.start_time_seconds,
        notes=song_in.notes,
        status=song_in.status or "pending",
    )
    session.add(song)
    session.commit()
    session.refresh(song)
    return SongRead.model_validate(song, from_attributes=True)


@app.get("/songs", response_model=list[SongRead])
def list_songs(
    status_filter: Optional[str] = Query(default="approved", alias="status"),
    session: Session = Depends(get_session),
) -> list[SongRead]:
    statement = select(Song)
    if status_filter:
        statement = statement.where(Song.status == status_filter)
    songs = session.exec(statement.order_by(Song.title)).all()
    return [SongRead.model_validate(song, from_attributes=True) for song in songs]


@app.patch("/admin/songs/{song_id}", response_model=SongRead)
def update_song(
    song_id: int,
    song_update: SongUpdate,
    session: Session = Depends(get_session),
    _: str = Depends(require_admin_token),
) -> SongRead:
    song = session.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    update_data = song_update.model_dump(exclude_unset=True)
    if "youtube_url" in update_data:
        youtube_id = extract_youtube_id(update_data["youtube_url"])
        update_data["youtube_video_id"] = youtube_id
    for field, value in update_data.items():
        setattr(song, field, value)
    song.updated_at = datetime.utcnow()
    session.add(song)
    session.commit()
    session.refresh(song)
    return SongRead.model_validate(song, from_attributes=True)


@app.post("/admin/songs/{song_id}/approve", response_model=SongRead)
def approve_song(
    song_id: int,
    session: Session = Depends(get_session),
    _: str = Depends(require_admin_token),
) -> SongRead:
    song = session.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    song.status = "approved"
    song.updated_at = datetime.utcnow()
    session.add(song)
    session.commit()
    session.refresh(song)
    return SongRead.model_validate(song, from_attributes=True)


@app.post("/admin/songs/{song_id}/reject", response_model=SongRead)
def reject_song(
    song_id: int,
    session: Session = Depends(get_session),
    _: str = Depends(require_admin_token),
) -> SongRead:
    song = session.get(Song, song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")
    song.status = "rejected"
    song.updated_at = datetime.utcnow()
    session.add(song)
    session.commit()
    session.refresh(song)
    return SongRead.model_validate(song, from_attributes=True)


# ---------------------------------------------------------------------------
# Room & player management
# ---------------------------------------------------------------------------


@app.post("/rooms", response_model=RoomJoinResponse, status_code=status.HTTP_201_CREATED)
def create_room(room_in: RoomCreate, session: Session = Depends(get_session)) -> RoomJoinResponse:
    code = (room_in.code or _generate_room_code(session)).upper()
    existing = session.exec(select(Room).where(Room.code == code)).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Room code already in use")

    room = Room(
        code=code,
        host_name=room_in.host_name.strip(),
        target_score=room_in.target_score,
        max_players=min(room_in.max_players, 8),
        round_duration_seconds=room_in.round_duration_seconds,
        status="waiting",
    )
    session.add(room)
    session.commit()
    session.refresh(room)

    host_player = Player(room_id=room.id, nickname=room.host_name, is_host=True)
    session.add(host_player)
    room.updated_at = datetime.utcnow()
    session.add(room)
    session.commit()
    session.refresh(host_player)
    session.refresh(room)

    return RoomJoinResponse(
        room=_build_room_state(session, room),
        player=PlayerRead.model_validate(host_player, from_attributes=True),
    )


@app.get("/rooms/{code}", response_model=RoomState)
def get_room(code: str, session: Session = Depends(get_session)) -> RoomState:
    room = _get_room_or_404(session, code)
    return _build_room_state(session, room)


@app.post("/rooms/{code}/join", response_model=RoomJoinResponse)
def join_room(code: str, join_request: JoinRoomRequest, session: Session = Depends(get_session)) -> RoomJoinResponse:
    room = _get_room_or_404(session, code)
    if room.status == "finished":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Room has already finished")

    players = session.exec(select(Player).where(Player.room_id == room.id)).all()
    if len(players) >= room.max_players:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Room is full")

    normalized_nickname = join_request.nickname.strip()
    if any(player.nickname.lower() == normalized_nickname.lower() for player in players):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nickname already taken")

    player = Player(room_id=room.id, nickname=normalized_nickname)
    session.add(player)
    room.updated_at = datetime.utcnow()
    session.add(room)
    session.commit()
    session.refresh(player)
    session.refresh(room)

    return RoomJoinResponse(
        room=_build_room_state(session, room),
        player=PlayerRead.model_validate(player, from_attributes=True),
    )


# ---------------------------------------------------------------------------
# Rounds and guessing
# ---------------------------------------------------------------------------


@app.post("/rooms/{code}/start_round", response_model=RoundState)
def start_round(
    code: str,
    payload: RoundStartRequest,
    session: Session = Depends(get_session),
) -> RoundState:
    room = _get_room_or_404(session, code)
    active_round = _get_active_round(session, room.id)
    if active_round:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A round is already in progress")

    player_total = session.exec(
        select(func.count()).select_from(Player).where(Player.room_id == room.id)
    ).scalar() or 0
    if player_total == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No players in room")

    song: Optional[Song]
    if payload.song_id is not None:
        song = session.get(Song, payload.song_id)
        if not song or song.status != "approved":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Song is not available")
    else:
        all_songs = session.exec(select(Song).where(Song.status == "approved")).all()
        if not all_songs:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No approved songs available")
        used_song_ids = {
            round_song_id
            for round_song_id in session.exec(select(Round.song_id).where(Round.room_id == room.id)).all()
        }
        available = [song_item for song_item in all_songs if song_item.id not in used_song_ids]
        song = random.choice(available or all_songs)

    duration = payload.duration_seconds or room.round_duration_seconds
    round_obj = Round(
        room_id=room.id,
        song_id=song.id,
        duration_seconds=duration,
        status="playing",
    )
    session.add(round_obj)
    room.status = "in_progress"
    room.updated_at = datetime.utcnow()
    session.add(room)
    session.commit()
    session.refresh(round_obj)
    session.refresh(room)

    return _build_round_state(session, round_obj, room=room, reveal_answer=payload.reveal_answer)


@app.get("/rooms/{code}/rounds/current", response_model=RoundState)
def get_current_round(
    code: str,
    reveal_answer: bool = Query(default=False),
    session: Session = Depends(get_session),
) -> RoundState:
    room = _get_room_or_404(session, code)
    round_obj = _get_active_round(session, room.id)
    if not round_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active round")
    return _build_round_state(session, round_obj, room=room, reveal_answer=reveal_answer)


@app.post("/rooms/{code}/rounds/{round_id}/guess", response_model=GuessResponse)
def submit_guess(
    code: str,
    round_id: int,
    guess_in: GuessCreate,
    session: Session = Depends(get_session),
) -> GuessResponse:
    room = _get_room_or_404(session, code)
    round_obj = session.get(Round, round_id)
    if not round_obj or round_obj.room_id != room.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Round not found")
    if round_obj.status != "playing":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Round is not accepting guesses")

    player = session.get(Player, guess_in.player_id)
    if not player or player.room_id != room.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found in this room")

    song = session.get(Song, round_obj.song_id)
    if not song:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    similarity = compute_similarity(song.anime_title, guess_in.guess_text)
    is_correct = similarity >= 0.8

    guess = Guess(
        round_id=round_obj.id,
        player_id=player.id,
        guess_text=guess_in.guess_text.strip(),
        similarity=similarity,
        is_correct=is_correct,
    )
    session.add(guess)

    if is_correct and round_obj.winning_player_id is None:
        round_obj.status = "completed"
        round_obj.winning_player_id = player.id
        round_obj.ended_at = datetime.utcnow()
        player.score += 1
        room.updated_at = datetime.utcnow()
        if player.score >= room.target_score:
            room.status = "finished"
            room.winning_player_id = player.id
        else:
            room.status = "waiting"
        session.add(round_obj)
        session.add(player)
        session.add(room)

    session.commit()
    session.refresh(guess)
    session.refresh(player)
    session.refresh(round_obj)
    session.refresh(room)

    return GuessResponse(
        guess=GuessRead.model_validate(guess, from_attributes=True),
        is_correct=is_correct,
        similarity=similarity,
        round_status=round_obj.status,
        player_score=player.score,
        room_status=room.status,
        target_score=room.target_score,
        winning_player_id=round_obj.winning_player_id,
    )


@app.post("/rooms/{code}/rounds/{round_id}/skip", response_model=SkipResponse)
def skip_round(
    code: str,
    round_id: int,
    request: SkipRequest,
    session: Session = Depends(get_session),
) -> SkipResponse:
    room = _get_room_or_404(session, code)
    round_obj = session.get(Round, round_id)
    if not round_obj or round_obj.room_id != room.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Round not found")

    player = session.get(Player, request.player_id)
    if not player or player.room_id != room.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Player not found in this room")

    if round_obj.status != "playing":
        skip_votes = session.exec(
            select(func.count()).select_from(SkipVote).where(SkipVote.round_id == round_obj.id)
        ).scalar() or 0
        total_players = session.exec(
            select(func.count()).select_from(Player).where(Player.room_id == room.id)
        ).scalar() or 0
        return SkipResponse(
            skip_votes=int(skip_votes),
            total_players=int(total_players),
            round_status=round_obj.status,
        )

    existing_vote = session.exec(
        select(SkipVote).where(SkipVote.round_id == round_obj.id, SkipVote.player_id == player.id)
    ).first()
    if not existing_vote:
        session.add(SkipVote(round_id=round_obj.id, player_id=player.id))
        session.commit()

    skip_votes_count = session.exec(
        select(func.count()).select_from(SkipVote).where(SkipVote.round_id == round_obj.id)
    ).scalar() or 0
    total_players = session.exec(
        select(func.count()).select_from(Player).where(Player.room_id == room.id)
    ).scalar() or 0

    if skip_votes_count >= total_players and round_obj.status == "playing":
        round_obj.status = "skipped"
        round_obj.ended_at = datetime.utcnow()
        room.status = "waiting"
        room.updated_at = datetime.utcnow()
        session.add(round_obj)
        session.add(room)
        session.commit()
        session.refresh(round_obj)
        session.refresh(room)

    return SkipResponse(
        skip_votes=int(skip_votes_count),
        total_players=int(total_players),
        round_status=round_obj.status,
    )


@app.get("/rooms/{code}/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard(code: str, session: Session = Depends(get_session)) -> LeaderboardResponse:
    room = _get_room_or_404(session, code)
    players = session.exec(
        select(Player).where(Player.room_id == room.id).order_by(Player.score.desc(), Player.joined_at)
    ).all()
    return LeaderboardResponse(
        room_code=room.code,
        players=[
            LeaderboardEntry(
                player_id=player.id,
                nickname=player.nickname,
                score=player.score,
                is_host=player.is_host,
            )
            for player in players
        ],
    )
