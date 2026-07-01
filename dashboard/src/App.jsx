import { useEffect, useState } from 'react'
import './App.css'

const VERDICT_CLASS = {
  GROUNDED: 'v-grounded',
  UNSUPPORTED: 'v-unsupported',
  PARTIAL: 'v-partial',
  DEFER: 'v-defer',
}

function Metric({ label, value, total, hint }) {
  return (
    <div className="metric">
      <div className="metric-value">
        {value}<span className="metric-total">/{total}</span>
      </div>
      <div className="metric-label">{label}</div>
      <div className="metric-hint">{hint}</div>
    </div>
  )
}

export default function App() {
  const [report, setReport] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}report.json`)
      .then((r) => r.json())
      .then(setReport)
      .catch((e) => setError(String(e)))
  }, [])

  if (error) return <div className="wrap"><p className="err">Could not load report.json — {error}</p></div>
  if (!report) return <div className="wrap"><p className="muted">Loading validation report…</p></div>

  const m = report.metrics
  return (
    <div className="wrap">
      <header>
        <h1>RAG faithfulness validation</h1>
        <div className="sub">
          domain: <b>{report.domain}</b> · judge: <b>{report.backend}</b> · generated {report.generated_at}
        </div>
      </header>

      <section className="metrics">
        <Metric label="Accuracy vs. gold" value={m.accuracy[0]} total={m.accuracy[1]} hint="verdicts matching ground truth" />
        <Metric label="Hallucination catch" value={m.hallucination_catch[0]} total={m.hallucination_catch[1]} hint="unfaithful answers flagged — safety-critical" />
        <Metric label="False flags" value={m.false_flags[0]} total={m.false_flags[1]} hint="grounded answers wrongly rejected" />
        <Metric label="Coverage" value={m.coverage[0]} total={m.coverage[1]} hint="definite verdicts, not deferred" />
        <Metric label="Strict gate pass" value={m.gate_pass[0]} total={m.gate_pass[1]} hint="pass only if fully grounded — a bad claim is a fail" />
      </section>

      <section>
        <table>
          <thead>
            <tr>
              <th>Case</th><th>Question</th><th>Verdict</th><th>Gold</th><th>Match</th><th>Gate</th><th>Claims S/U/D</th><th>Trust tier</th>
            </tr>
          </thead>
          <tbody>
            {report.cases.map((c) => (
              <tr key={c.id}>
                <td className="mono">{c.id}</td>
                <td className="q">{c.question}</td>
                <td><span className={`pill ${VERDICT_CLASS[c.verdict]}`}>{c.verdict}</span></td>
                <td className="muted">{c.gold}</td>
                <td className={c.correct ? 'ok' : 'no'}>{c.correct ? '✓' : '✗'}</td>
                <td><span className={`gate ${c.gate_pass ? 'pass' : 'fail'}`}>{c.gate_pass ? 'PASS' : 'FAIL'}</span></td>
                <td className="mono">{c.supported}/{c.unsupported}/{c.deferred}</td>
                <td className="muted small">{c.tiers.join(', ')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <footer>
        Every <b>SUPPORTED</b> verdict carries evidence verified against the source. An unavailable or
        unfit judge degrades to <b>DEFER</b> — never a wrong verdict.
      </footer>
    </div>
  )
}
