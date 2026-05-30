import { useState, useEffect } from 'react';
import LogoutButton from '../components/LogoutButton';
import styles from './EmployeeDashboard.module.css';
import { MOCK_MY_TASKS } from '../api/mockData';
// import client from '../api/client'; // ← uncomment when backend is ready

// ── Helpers ──────────────────────────────────────────────────────────────────
function isOverdue(task) {
  return (
    task.status !== 'Done' &&
    new Date(task.deadline) < new Date(new Date().toDateString())
  );
}

function cardBorderClass(task) {
  if (task.status === 'Done') return styles.cardDone;
  if (isOverdue(task)) return styles.cardOverdue;
  if (task.status === 'In Progress') return styles.cardInProgress;
  return styles.cardPending;
}

function statusClass(status, overdue) {
  if (overdue) return styles.statusOverdue;
  const map = {
    Pending: styles.statusPending,
    'In Progress': styles.statusInProgress,
    Done: styles.statusDone,
  };
  return map[status] || styles.statusPending;
}

function priorityClass(p) {
  return { High: styles.priorityHigh, Medium: styles.priorityMedium, Low: styles.priorityLow }[p];
}

// ── Task Card ─────────────────────────────────────────────────────────────────
function TaskCard({ task, onLogSubmitted }) {
  const [expanded, setExpanded] = useState(false);
  const [logText, setLogText] = useState('');
  const [logStatus, setLogStatus] = useState('In Progress');
  const [submitting, setSubmitting] = useState(false);
  const [aiResult, setAiResult] = useState(null);

  const overdue = isOverdue(task);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);

    // ── MOCK log submission ───────────────────────────────────────────────────
    // TODO: replace with real API call:
    // const { data } = await client.post(`/api/tasks/${task.id}/log`, { logText, status: logStatus });
    // setAiResult({ confidence: data.confidence, feedback: data.feedback });
    await new Promise((r) => setTimeout(r, 600));
    const mockConfidence = logText.length > 80 ? 'High' : logText.length > 30 ? 'Medium' : 'Low';
    const mockFeedback = {
      High: 'Good detail — the log clearly describes the work done and progress made.',
      Medium: 'Acceptable entry, but adding more specifics about what was completed would help.',
      Low: 'This log is too vague. Please describe exactly what was done and what remains.',
    }[mockConfidence];
    setAiResult({ confidence: mockConfidence, feedback: mockFeedback });
    // ── END MOCK ──────────────────────────────────────────────────────────────

    onLogSubmitted(task.id, logStatus);
    setExpanded(false);
    setLogText('');
    setSubmitting(false);
  }

  function confidenceClass(c) {
    return { High: styles.confidenceHigh, Medium: styles.confidenceMedium, Low: styles.confidenceLow }[c];
  }

  return (
    <div className={`${styles.card} ${cardBorderClass(task)}`}>
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.cardTitle}>{task.title}</p>
          <div className={styles.cardMeta}>
            <span className={`${styles.priorityBadge} ${priorityClass(task.priority)}`}>
              {task.priority}
            </span>
            <span className={`${styles.statusBadge} ${statusClass(task.status, overdue)}`}>
              {overdue ? 'Overdue' : task.status}
            </span>
          </div>
        </div>
      </div>

      {task.description && (
        <p className={styles.cardDesc}>{task.description}</p>
      )}

      <div className={styles.cardFooter}>
        <span className={`${styles.deadline} ${overdue ? styles.deadlineOverdue : ''}`}>
          📅 Due: {task.deadline}{overdue ? ' — OVERDUE' : ''}
        </span>
        {task.status !== 'Done' && (
          <button
            className={styles.btnLog}
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? 'Cancel' : '+ Submit Work Log'}
          </button>
        )}
        {task.status === 'Done' && (
          <span className={`${styles.btnLog} ${styles.btnLogDone}`}>✓ Completed</span>
        )}
      </div>

      {/* AI confidence result (shown after submission) */}
      {aiResult && (
        <div className={styles.aiResult}>
          <div className={styles.aiResultRow}>
            <span className={styles.aiLabel}>AI Verification</span>
            <span className={`${styles.confidencePill} ${confidenceClass(aiResult.confidence)}`}>
              {aiResult.confidence} Confidence
            </span>
          </div>
          <p className={styles.aiFeedback}>{aiResult.feedback}</p>
        </div>
      )}

      {/* Log submission form */}
      {expanded && (
        <form onSubmit={handleSubmit} className={styles.logForm}>
          <textarea
            value={logText}
            onChange={(e) => setLogText(e.target.value)}
            placeholder="Describe what you worked on today — be specific about what was done and what remains…"
            required
          />
          <div className={styles.logFormRow}>
            <select value={logStatus} onChange={(e) => setLogStatus(e.target.value)}>
              <option value="In Progress">In Progress</option>
              <option value="Completed">Completed</option>
            </select>
            <button type="submit" className={styles.btnSubmit} disabled={submitting}>
              {submitting ? 'Submitting…' : 'Submit Log'}
            </button>
            <button
              type="button"
              className={styles.btnCancel}
              onClick={() => setExpanded(false)}
            >
              Cancel
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function EmployeeDashboard() {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    // ── MOCK fetch my tasks ───────────────────────────────────────────────────
    // TODO: replace with: const { data } = await client.get('/api/tasks/mine');
    // Sort by deadline soonest first
    const sorted = [...MOCK_MY_TASKS].sort(
      (a, b) => new Date(a.deadline) - new Date(b.deadline)
    );
    setTasks(sorted);
    // ── END MOCK ──────────────────────────────────────────────────────────────
  }, []);

  function handleLogSubmitted(taskId, newStatus) {
    setTasks((prev) =>
      prev.map((t) =>
        t.id === taskId
          ? { ...t, status: newStatus === 'Completed' ? 'Done' : 'In Progress' }
          : t
      )
    );
  }

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span>⚡</span>
          <h1>WorkFlow</h1>
          <span className={styles.badge}>Employee</span>
        </div>
        <LogoutButton />
      </header>

      <main className={styles.main}>
        <h2 className={styles.pageTitle}>My Tasks ({tasks.length})</h2>

        {tasks.length === 0 ? (
          <p className={styles.empty}>No tasks assigned to you yet.</p>
        ) : (
          tasks.map((task) => (
            <TaskCard key={task.id} task={task} onLogSubmitted={handleLogSubmitted} />
          ))
        )}
      </main>
    </div>
  );
}
