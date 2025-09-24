import { useEffect, useMemo, useState } from 'react'
import { API_BASE_URL } from '../api/client'

function GameDashboard({
  room,
  player,
  currentRound,
  onStartRound,
  onSubmitGuess,
  onSkipRound,
  onRevealAnswer,
  isStartingRound,
  feedback,
  error,
  approvedSongs,
}) {
  const [guessText, setGuessText] = useState('')
  const [selectedSongId, setSelectedSongId] = useState('')
  const [videoRefreshKey, setVideoRefreshKey] = useState(0)

  useEffect(() => {
    setGuessText('')
    setVideoRefreshKey((key) => key + 1)
  }, [currentRound?.id])

  useEffect(() => {
    if (!approvedSongs.length) {
      setSelectedSongId('')
      return
    }
    const fallback = approvedSongs[0]?.id?.toString() ?? ''
    setSelectedSongId((value) => (value ? value : fallback))
  }, [approvedSongs])

  const youtubeEmbedSrc = useMemo(() => {
    if (!currentRound?.song?.youtube_video_id) {
      return null
    }
    const startSeconds = currentRound.song.start_time_seconds || 0
    const autoplay = 1
    return `https://www.youtube.com/embed/${currentRound.song.youtube_video_id}?start=${startSeconds}&autoplay=${autoplay}`
  }, [currentRound])

  const handleGuessSubmit = (event) => {
    event.preventDefault()
    if (!guessText.trim() || !currentRound) {
      return
    }
    onSubmitGuess(guessText.trim())
    setGuessText('')
  }

  const handleStartRound = () => {
    onStartRound(selectedSongId ? Number(selectedSongId) : undefined)
  }

  const handleReplay = () => {
    setVideoRefreshKey((key) => key + 1)
  }

  const isRoundActive = currentRound && currentRound.status === 'playing'

  return (
    <div className="dashboard">
      <header className="dashboard__header">
        <div>
          <h1>房間 {room.code}</h1>
          <p>
            目標分數 {room.target_score} 分 ・ 每題 {room.round_duration_seconds} 秒 ・ 人數上限 {room.max_players}
          </p>
        </div>
        <div className="dashboard__host-actions">
          <span className="badge">你是：{player.nickname}</span>
          {player.is_host ? <span className="badge badge--host">房主</span> : null}
        </div>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}
      {feedback ? <div className="info-banner">{feedback}</div> : null}

      <section className="card scoreboard">
        <h2>玩家列表</h2>
        <ul>
          {room.players.map((entry) => (
            <li key={entry.id} className={entry.id === player.id ? 'me' : undefined}>
              <span>
                {entry.nickname}
                {entry.is_host ? <span className="badge badge--host">房主</span> : null}
              </span>
              <span className="score">{entry.score} 分</span>
            </li>
          ))}
        </ul>
      </section>

      {room.status === 'finished' ? (
        <section className="card status-card">
          <h2>遊戲結束 🎉</h2>
          <p>
            {room.winning_player_id
              ? `獲勝者：${room.players.find((p) => p.id === room.winning_player_id)?.nickname ?? '未知玩家'}`
              : '本局已結束'}
          </p>
        </section>
      ) : null}

      {player.is_host ? (
        <section className="card host-controls">
          <h2>房主控制</h2>
          <div className="host-controls__content">
            <div>
              <label>
                指定題目（可選）
                <select value={selectedSongId} onChange={(event) => setSelectedSongId(event.target.value)}>
                  <option value="">隨機播放一首已核可歌曲</option>
                  {approvedSongs.map((song) => (
                    <option value={song.id} key={song.id}>
                      {song.title} ・ {song.anime_title}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <button type="button" onClick={handleStartRound} disabled={isStartingRound || isRoundActive}>
              {isStartingRound ? '準備中…' : '開始下一題'}
            </button>
            {currentRound ? (
              <button type="button" onClick={() => onRevealAnswer(true)} className="secondary">
                顯示答案
              </button>
            ) : null}
          </div>
        </section>
      ) : null}

      {currentRound ? (
        <section className="card round-card">
          <header className="round-card__header">
            <div>
              <h2>第 {currentRound.id} 題</h2>
              <p>
                狀態：{translateStatus(currentRound.status)} ・ 跳過 {currentRound.skip_votes} / {currentRound.total_players}
              </p>
            </div>
            <button type="button" onClick={handleReplay} className="secondary">
              重新播放影片
            </button>
          </header>
          {youtubeEmbedSrc ? (
            <div className="video-wrapper">
              <iframe
                key={videoRefreshKey}
                src={youtubeEmbedSrc}
                title="Anime Quiz Song"
                allow="autoplay; encrypted-media"
                allowFullScreen
              />
            </div>
          ) : (
            <p>找不到影片資訊，請確認歌曲設定。</p>
          )}
          {currentRound.song?.anime_title ? (
            <div className="answer-banner">答案：{currentRound.song.anime_title}</div>
          ) : null}
          {isRoundActive ? (
            <form className="guess-form" onSubmit={handleGuessSubmit}>
              <label>
                你的答案
                <input value={guessText} onChange={(event) => setGuessText(event.target.value)} placeholder="請輸入動畫名稱" />
              </label>
              <div className="guess-form__actions">
                <button type="submit" disabled={!guessText.trim()}>
                  送出答案
                </button>
                <button type="button" className="secondary" onClick={onSkipRound}>
                  我要跳過
                </button>
              </div>
            </form>
          ) : (
            <p className="round-complete">
              {currentRound.winning_player_id
                ? `由 ${room.players.find((p) => p.id === currentRound.winning_player_id)?.nickname ?? '玩家'} 率先答對！`
                : '本題已結束，等待房主開始下一題。'}
            </p>
          )}
        </section>
      ) : (
        <section className="card round-card">
          <h2>等待開始</h2>
          <p>房主可以選擇指定歌曲或直接開始下一題。</p>
        </section>
      )}

      <footer className="app-footer">
        後端服務：<code>{API_BASE_URL}</code>
      </footer>
    </div>
  )
}

function translateStatus(value) {
  switch (value) {
    case 'playing':
      return '播放中'
    case 'completed':
      return '答題完成'
    case 'skipped':
      return '已跳過'
    default:
      return value
  }
}

export default GameDashboard
