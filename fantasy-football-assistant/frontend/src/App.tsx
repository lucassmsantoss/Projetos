import { useState } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

interface Recommendation {
  sleeper_id: string
  name: string
  position: string
  team: string | null
  final_score: number
  value_score: number
  my_need_score: number
  league_scarcity_score: number
  reasoning: string
}

function App() {
  const [myUserId, setMyUserId] = useState('')
  const [recommendations, setRecommendations] = useState<Recommendation[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function fetchRecommendations() {
    if (!myUserId) {
      setError('Informe seu Sleeper user_id')
      return
    }
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(
        `${API_BASE}/draft/recommendations?my_user_id=${encodeURIComponent(myUserId)}&top_n=15`,
      )
      if (!res.ok) throw new Error(`Erro ${res.status}: ${await res.text()}`)
      const data = await res.json()
      setRecommendations(data.recommendations)
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-container">
      <h1>Fantasy Football Draft Assistant</h1>
      <p className="subtitle">Recomendações de pick baseadas no seu roster, no dos adversários e em projeções/histórico.</p>

      <div className="controls">
        <input
          placeholder="Seu Sleeper user_id"
          value={myUserId}
          onChange={(e) => setMyUserId(e.target.value)}
        />
        <button onClick={fetchRecommendations} disabled={loading}>
          {loading ? 'Buscando...' : 'Buscar recomendações'}
        </button>
      </div>

      {error && <p className="error">{error}</p>}

      <table className="recommendations">
        <thead>
          <tr>
            <th>#</th>
            <th>Jogador</th>
            <th>Pos</th>
            <th>Time</th>
            <th>Score final</th>
            <th>Valor</th>
            <th>Sua necessidade</th>
            <th>Escassez liga</th>
            <th>Por quê</th>
          </tr>
        </thead>
        <tbody>
          {recommendations.map((r, i) => (
            <tr key={r.sleeper_id}>
              <td>{i + 1}</td>
              <td>{r.name}</td>
              <td>{r.position}</td>
              <td>{r.team ?? '-'}</td>
              <td>{r.final_score}</td>
              <td>{r.value_score}</td>
              <td>{r.my_need_score}</td>
              <td>{r.league_scarcity_score}</td>
              <td className="reasoning">{r.reasoning}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default App
