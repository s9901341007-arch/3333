import { useState } from 'react'

function AdminSongManager({
  adminToken,
  onAdminTokenChange,
  onCreateSong,
  onApproveSong,
  onRejectSong,
  pendingSongs,
  approvedSongs,
  onRefresh,
  error,
}) {
  const [title, setTitle] = useState('')
  const [animeTitle, setAnimeTitle] = useState('')
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [autoApprove, setAutoApprove] = useState(true)
  const [notes, setNotes] = useState('')

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!title.trim() || !animeTitle.trim() || !youtubeUrl.trim()) {
      return
    }
    onCreateSong({
      title: title.trim(),
      anime_title: animeTitle.trim(),
      youtube_url: youtubeUrl.trim(),
      notes: notes.trim() || undefined,
      status: autoApprove ? 'approved' : 'pending',
    })
    setTitle('')
    setAnimeTitle('')
    setYoutubeUrl('')
    setNotes('')
  }

  return (
    <section className="card admin-panel">
      <header>
        <h2>題庫管理</h2>
        <button type="button" className="secondary" onClick={onRefresh}>
          重新整理清單
        </button>
      </header>
      {error ? <div className="error-banner">{error}</div> : null}
      <div className="admin-panel__grid">
        <form onSubmit={handleSubmit} className="admin-panel__form">
          <h3>新增歌曲</h3>
          <label>
            管理者 Token
            <input value={adminToken} onChange={(event) => onAdminTokenChange(event.target.value)} />
          </label>
          <label>
            歌曲名稱 / 歌手
            <input value={title} onChange={(event) => setTitle(event.target.value)} required />
          </label>
          <label>
            對應動畫名稱
            <input value={animeTitle} onChange={(event) => setAnimeTitle(event.target.value)} required />
          </label>
          <label>
            YouTube 連結或影片 ID
            <input value={youtubeUrl} onChange={(event) => setYoutubeUrl(event.target.value)} required />
          </label>
          <label>
            備註 (選填)
            <input value={notes} onChange={(event) => setNotes(event.target.value)} />
          </label>
          <label className="checkbox">
            <input
              type="checkbox"
              checked={autoApprove}
              onChange={(event) => setAutoApprove(event.target.checked)}
            />
            直接核可（取消勾選將進入審核）
          </label>
          <button type="submit" disabled={!adminToken.trim()}>
            新增歌曲
          </button>
        </form>
        <div className="admin-panel__lists">
          <div>
            <h3>待審核 ({pendingSongs.length})</h3>
            {pendingSongs.length === 0 ? <p className="muted">目前沒有待審核的歌曲。</p> : null}
            <ul>
              {pendingSongs.map((song) => (
                <li key={song.id}>
                  <div>
                    <strong>{song.title}</strong>
                    <span>{song.anime_title}</span>
                  </div>
                  <div className="admin-panel__list-actions">
                    <button type="button" onClick={() => onApproveSong(song.id)}>
                      核可
                    </button>
                    <button type="button" className="secondary" onClick={() => onRejectSong(song.id)}>
                      拒絕
                    </button>
                  </div>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <h3>已核可 ({approvedSongs.length})</h3>
            {approvedSongs.length === 0 ? <p className="muted">請先新增或核可題目。</p> : null}
            <ul>
              {approvedSongs.map((song) => (
                <li key={song.id}>
                  <div>
                    <strong>{song.title}</strong>
                    <span>{song.anime_title}</span>
                  </div>
                  <a href={song.youtube_url} target="_blank" rel="noreferrer">
                    前往影片
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}

export default AdminSongManager
