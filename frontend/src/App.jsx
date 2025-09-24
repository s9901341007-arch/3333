import { useCallback, useEffect, useState } from 'react'
import './App.css'
import {
  approveSong,
  createRoom,
  createSong,
  getCurrentRound,
  joinRoom,
  listSongs,
  rejectSong,
  sendSkip,
  startRound,
  submitGuess,
  fetchRoom,
} from './api/client'
import AdminSongManager from './components/AdminSongManager'
import GameDashboard from './components/GameDashboard'
import RoomSetup from './components/RoomSetup'

function App() {
  const [roomCode, setRoomCode] = useState('')
  const [room, setRoom] = useState(null)
  const [player, setPlayer] = useState(null)
  const [currentRound, setCurrentRound] = useState(null)
  const [approvedSongs, setApprovedSongs] = useState([])
  const [pendingSongs, setPendingSongs] = useState([])
  const [adminToken, setAdminToken] = useState('')
  const [loading, setLoading] = useState(false)
  const [startingRound, setStartingRound] = useState(false)
  const [feedback, setFeedback] = useState('')
  const [error, setError] = useState('')
  const [adminError, setAdminError] = useState('')

  const refreshSongs = useCallback(async () => {
    try {
      const [approved, pending] = await Promise.all([
        listSongs({ status: 'approved' }),
        listSongs({ status: 'pending' }),
      ])
      setApprovedSongs(approved)
      setPendingSongs(pending)
      setAdminError('')
    } catch (err) {
      setAdminError(err.message)
    }
  }, [])

  useEffect(() => {
    refreshSongs()
  }, [refreshSongs])

  const refreshRoomState = useCallback(async () => {
    if (!roomCode) {
      return
    }
    try {
      const updated = await fetchRoom(roomCode)
      setRoom(updated)
      setPlayer((prev) => {
        if (!prev) return prev
        const found = updated.players.find((entry) => entry.id === prev.id)
        return found ? { ...prev, ...found } : prev
      })
      setError('')
    } catch (err) {
      setError(err.message)
    }
  }, [roomCode])

  const refreshCurrentRound = useCallback(
    async ({ revealAnswer = false } = {}) => {
      if (!roomCode) {
        return
      }
      try {
        const round = await getCurrentRound(roomCode, { revealAnswer })
        setCurrentRound(round)
        setError('')
      } catch (err) {
        if (err.message.includes('No active round')) {
          setCurrentRound(null)
        } else {
          setError(err.message)
        }
      }
    },
    [roomCode],
  )

  useEffect(() => {
    if (!roomCode) {
      return
    }
    const interval = setInterval(() => {
      refreshRoomState()
      refreshCurrentRound()
    }, 5000)
    return () => clearInterval(interval)
  }, [roomCode, refreshRoomState, refreshCurrentRound])

  const handleCreateRoom = async ({ host_name, target_score, round_duration_seconds }) => {
    try {
      setLoading(true)
      setError('')
      const response = await createRoom({
        host_name,
        target_score,
        round_duration_seconds,
      })
      setRoom(response.room)
      setPlayer(response.player)
      setRoomCode(response.room.code)
      setFeedback(`房間 ${response.room.code} 建立成功！分享房間碼給朋友一起玩吧。`)
      const round = await getCurrentRound(response.room.code).catch(() => null)
      setCurrentRound(round)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleJoinRoom = async ({ code, nickname }) => {
    try {
      setLoading(true)
      setError('')
      const response = await joinRoom(code, { nickname })
      setRoom(response.room)
      setPlayer(response.player)
      setRoomCode(response.room.code)
      setFeedback(`歡迎加入房間 ${response.room.code}！`)
      const round = await getCurrentRound(response.room.code).catch(() => null)
      setCurrentRound(round)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const handleStartRound = async (songId) => {
    if (!roomCode) return
    try {
      setStartingRound(true)
      const payload = songId ? { song_id: songId } : {}
      const round = await startRound(roomCode, payload)
      setCurrentRound(round)
      setFeedback('新的一題開始囉！')
      await refreshRoomState()
    } catch (err) {
      setError(err.message)
    } finally {
      setStartingRound(false)
    }
  }

  const handleSubmitGuess = async (guessText) => {
    if (!roomCode || !player || !currentRound) return
    try {
      const response = await submitGuess(roomCode, currentRound.id, {
        player_id: player.id,
        guess_text: guessText,
      })
      setPlayer((prev) => (prev ? { ...prev, score: response.player_score } : prev))
      setFeedback(
        response.is_correct
          ? `太棒了！你答對了，相似度 ${(response.similarity * 100).toFixed(0)}%。`
          : `相似度 ${(response.similarity * 100).toFixed(0)}%，再試一次！`,
      )
      await refreshRoomState()
      if (response.round_status !== 'playing') {
        await refreshCurrentRound({ revealAnswer: true })
      } else {
        await refreshCurrentRound()
      }
    } catch (err) {
      setError(err.message)
    }
  }

  const handleSkipRound = async () => {
    if (!roomCode || !player || !currentRound) return
    try {
      const result = await sendSkip(roomCode, currentRound.id, { player_id: player.id })
      setFeedback(`已送出跳過票數：${result.skip_votes} / ${result.total_players}`)
      if (result.round_status !== 'playing') {
        await refreshCurrentRound({ revealAnswer: true })
        await refreshRoomState()
      } else {
        setCurrentRound((prev) =>
          prev ? { ...prev, skip_votes: result.skip_votes, total_players: result.total_players } : prev,
        )
      }
    } catch (err) {
      setError(err.message)
    }
  }

  const handleRevealAnswer = async () => {
    await refreshCurrentRound({ revealAnswer: true })
  }

  const handleCreateSong = async (payload) => {
    if (!adminToken.trim()) return
    try {
      setAdminError('')
      await createSong(payload, adminToken)
      await refreshSongs()
      setFeedback('題庫已更新！')
    } catch (err) {
      setAdminError(err.message)
    }
  }

  const handleApproveSong = async (songId) => {
    if (!adminToken.trim()) return
    try {
      setAdminError('')
      await approveSong(songId, adminToken)
      await refreshSongs()
    } catch (err) {
      setAdminError(err.message)
    }
  }

  const handleRejectSong = async (songId) => {
    if (!adminToken.trim()) return
    try {
      setAdminError('')
      await rejectSong(songId, adminToken)
      await refreshSongs()
    } catch (err) {
      setAdminError(err.message)
    }
  }

  const isInGame = Boolean(room && player)

  return (
    <main className="app">
      {!isInGame ? (
        <RoomSetup onCreateRoom={handleCreateRoom} onJoinRoom={handleJoinRoom} isLoading={loading} error={error} />
      ) : (
        <>
          <GameDashboard
            room={room}
            player={player}
            currentRound={currentRound}
            onStartRound={handleStartRound}
            onSubmitGuess={handleSubmitGuess}
            onSkipRound={handleSkipRound}
            onRevealAnswer={handleRevealAnswer}
            isStartingRound={startingRound}
            feedback={feedback}
            error={error}
            approvedSongs={approvedSongs}
          />
          {player?.is_host ? (
            <AdminSongManager
              adminToken={adminToken}
              onAdminTokenChange={setAdminToken}
              onCreateSong={handleCreateSong}
              onApproveSong={handleApproveSong}
              onRejectSong={handleRejectSong}
              pendingSongs={pendingSongs}
              approvedSongs={approvedSongs}
              onRefresh={refreshSongs}
              error={adminError}
            />
          ) : null}
        </>
      )}
    </main>
  )
}

export default App
