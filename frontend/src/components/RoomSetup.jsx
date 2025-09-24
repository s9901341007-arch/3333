import { useState } from 'react'

function RoomSetup({ onCreateRoom, onJoinRoom, isLoading, error }) {
  const [hostName, setHostName] = useState('')
  const [targetScore, setTargetScore] = useState(5)
  const [roundDuration, setRoundDuration] = useState(120)
  const [joinCode, setJoinCode] = useState('')
  const [nickname, setNickname] = useState('')

  const handleCreate = (event) => {
    event.preventDefault()
    if (!hostName.trim()) {
      return
    }
    onCreateRoom({
      host_name: hostName.trim(),
      target_score: Number(targetScore) || 5,
      round_duration_seconds: Number(roundDuration) || 120,
    })
  }

  const handleJoin = (event) => {
    event.preventDefault()
    if (!joinCode.trim() || !nickname.trim()) {
      return
    }
    onJoinRoom({
      code: joinCode.trim().toUpperCase(),
      nickname: nickname.trim(),
    })
  }

  return (
    <div className="setup-container">
      <h1 className="app-title">Anime Quiz App</h1>
      <p className="app-subtitle">建立房間或透過房間碼加入，一起挑戰猜歌遊戲！</p>
      {error ? <div className="error-banner">{error}</div> : null}
      <div className="setup-grid">
        <form className="card" onSubmit={handleCreate}>
          <h2>建立新房間</h2>
          <label>
            房主暱稱
            <input value={hostName} onChange={(event) => setHostName(event.target.value)} required />
          </label>
          <label>
            目標分數
            <input
              type="number"
              min="1"
              max="50"
              value={targetScore}
              onChange={(event) => setTargetScore(event.target.value)}
            />
          </label>
          <label>
            每題作答時間 (秒)
            <input
              type="number"
              min="30"
              max="600"
              value={roundDuration}
              onChange={(event) => setRoundDuration(event.target.value)}
            />
          </label>
          <button type="submit" disabled={isLoading}>
            {isLoading ? '建立中…' : '建立房間'}
          </button>
        </form>
        <form className="card" onSubmit={handleJoin}>
          <h2>加入房間</h2>
          <label>
            房間碼
            <input value={joinCode} onChange={(event) => setJoinCode(event.target.value)} required />
          </label>
          <label>
            暱稱
            <input value={nickname} onChange={(event) => setNickname(event.target.value)} required />
          </label>
          <button type="submit" disabled={isLoading}>
            {isLoading ? '加入中…' : '加入遊戲'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default RoomSetup
