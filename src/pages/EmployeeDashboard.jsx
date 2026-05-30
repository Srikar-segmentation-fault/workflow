import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import LogoutButton from '../components/LogoutButton';
import { useAuth } from '../context/AuthContext';
import styles from './EmployeeDashboard.module.css';
import { getMyTasks, updateTask, submitLog } from '../api/taskStore';
// import client from '../api/client'; // ← uncomment when backend is ready

// ── Helpers ──────────────────────────────────────────────────────────────────
function isOverdue(task) {
  return (
    task.status !== 'Done' &&
    new Date(task.deadline) < new Date(new Date().toDateString())
  );
}

function cardBorderClass(task, styles) {
  if (task.status === 'Done') return styles.cardDone;
  if (isOverdue(task)) return styles.cardOverdue;
  if (task.status === 'In Progress') return styles.cardInProgress;
  return styles.cardPending;
}

function statusClass(status, overdue, styles) {
  if (overdue) return styles.statusOverdue;
  const map = {
    Pending: styles.statusPending,
    'In Progress': styles.statusInProgress,
    Done: styles.statusDone,
  };
  return map[status] || styles.statusPending;
}

function priorityClass(p, styles) {
  return { High: styles.priorityHigh, Medium: styles.priorityMedium, Low: styles.priorityLow }[p];
}

// ── Task Card ─────────────────────────────────────────────────────────────────
function TaskCard({ task, onLogSubmitted, employeeName }) {
  const { t } = useTranslation();
  const [expanded, setExpanded] = useState(false);
  const [logText, setLogText] = useState('');
  const [logStatus, setLogStatus] = useState('In Progress');
  const [proofFile, setProofFile] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [aiResult, setAiResult] = useState(null);

  const overdue = isOverdue(task);
  const ACCEPTED_TYPES = 'image/jpeg,image/png,image/gif,image/webp,application/pdf,text/plain,text/csv,.docx,.xlsx';

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);

    // ── MOCK AI verification ──────────────────────────────────────────────────
    // TODO: replace with real API call using FormData:
    // const fd = new FormData();
    // fd.append('log_text', logText);
    // fd.append('status', logStatus);
    // if (proofFile) fd.append('proof_file', proofFile);
    // const { data } = await client.post(`/api/logs/${task.id}`, fd);
    await new Promise((r) => setTimeout(r, 600));
    const hasProof = !!proofFile;
    const mockConfidence = logText.length > 80 ? 'High' : logText.length > 30 ? 'Medium' : 'Low';
    const mockFeedback = {
      High: hasProof ? 'Good detail and proof file provided — log clearly supports the work done.' : 'Good detail — the log clearly describes the work done and progress made.',
      Medium: hasProof ? 'Acceptable entry with proof attached, but more specifics would help.' : 'Acceptable entry, but adding more specifics about what was completed would help.',
      Low: 'This log is too vague. Please describe exactly what was done and what remains.',
    }[mockConfidence];
    // ── END MOCK ──────────────────────────────────────────────────────────────

    // Persist log + audit trail to shared store (Problem 2 & 4)
    const submittedAt = new Date().toISOString();
    submitLog(task.id, {
      employeeName,
      logText,
      status: logStatus,
      hasProof,
      aiConfidence: mockConfidence,
      aiFeedback: mockFeedback,
    });

    // Update task status in shared store (Problem 1 & 3)
    onLogSubmitted(task.id, logStatus);
    setAiResult({ confidence: mockConfidence, feedback: mockFeedback, hasProof, submittedAt });
    setExpanded(false);
    setLogText('');
    setProofFile(null);
    setSubmitting(false);
  }

  function confidenceClass(c) {
    return { High: styles.confidenceHigh, Medium: styles.confidenceMedium, Low: styles.confidenceLow }[c];
  }

  return (
    <div className={`${styles.card} ${cardBorderClass(task, styles)}`}>
      <div className={styles.cardHeader}>
        <div>
          <p className={styles.cardTitle}>{task.title}</p>
          <div className={styles.cardMeta}>
            <span className={`${styles.priorityBadge} ${priorityClass(task.priority, styles)}`}>
              {t(`priority.${task.priority.toLowerCase()}`)}
            </span>
            <span className={`${styles.statusBadge} ${statusClass(task.status, overdue, styles)}`}>
              {overdue ? t('status.overdue') : t(`status.${task.status === 'In Progress' ? 'inProgress' : task.status.toLowerCase()}`)}
            </span>
          </div>
        </div>
      </div>

      {task.description && (
        <p className={styles.cardDesc}>{task.description}</p>
      )}

      <div className={styles.cardFooter}>
        <span className={`${styles.deadline} ${overdue ? styles.deadlineOverdue : ''}`}>
          {t('employee.due')} {task.deadline}{overdue ? ` — ${t('employee.overdue')}` : ''}
        </span>
        {task.status !== 'Done' && (
          <button
            className={styles.btnLog}
            onClick={() => setExpanded((v) => !v)}
          >
            {expanded ? t('employee.cancel') : t('employee.submitWorkLog')}
          </button>
        )}
        {task.status === 'Done' && (
          <span className={`${styles.btnLog} ${styles.btnLogDone}`}>{t('employee.completed')}</span>
        )}
      </div>

      {/* AI confidence result + submission timestamp */}
      {aiResult && (
        <div className={styles.aiResult}>
          <div className={styles.submittedAt}>
            🕐 Submitted: <strong>{new Date(aiResult.submittedAt).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'medium' })}</strong>
          </div>
          <div className={styles.aiResultRow}>
            <span className={styles.aiLabel}>{t('ai.verificationLabel')}</span>
            <span className={`${styles.confidencePill} ${confidenceClass(aiResult.confidence)}`}>
              {t(`ai.${aiResult.confidence.toLowerCase()}`)} {t('ai.confidence')}
            </span>
            {aiResult.hasProof && (
              <span className={styles.proofBadge}>📎 {t('employee.proofIncluded')}</span>
            )}
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
            placeholder={t('employee.logPlaceholder')}
            required
          />

          {/* Proof file upload */}
          <div className={styles.proofUpload}>
            <label className={styles.proofLabel}>
              📎 {t('employee.attachProof')}
              <input
                type="file"
                accept={ACCEPTED_TYPES}
                className={styles.proofInput}
                onChange={(e) => setProofFile(e.target.files?.[0] || null)}
              />
            </label>
            {proofFile && (
              <span className={styles.proofFileName}>
                {proofFile.name}
                <button
                  type="button"
                  className={styles.proofRemove}
                  onClick={() => setProofFile(null)}
                  aria-label="Remove file"
                >
                  ✕
                </button>
              </span>
            )}
            <p className={styles.proofHint}>{t('employee.proofHint')}</p>
          </div>

          <div className={styles.logFormRow}>
            <select value={logStatus} onChange={(e) => setLogStatus(e.target.value)}>
              <option value="In Progress">{t('employee.inProgress')}</option>
              <option value="Completed">{t('employee.completedStatus')}</option>
            </select>
            <button type="submit" className={styles.btnSubmit} disabled={submitting}>
              {submitting ? t('employee.submitting') : t('employee.submitLog')}
            </button>
            <button
              type="button"
              className={styles.btnCancel}
              onClick={() => setExpanded(false)}
            >
              {t('employee.cancel')}
            </button>
          </div>
        </form>
      )}
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function EmployeeDashboard() {
  const { t } = useTranslation();
  const { user } = useAuth();

  // Load from shared store, sorted by deadline
  const [tasks, setTasks] = useState(() =>
    getMyTasks(user?.id || '2').sort(
      (a, b) => new Date(a.deadline) - new Date(b.deadline)
    )
  );

  function handleLogSubmitted(taskId, newStatus) {
    const resolvedStatus = newStatus === 'Completed' ? 'Done' : 'In Progress';

    // 1. Write to shared localStorage store (persists across refresh + tabs)
    updateTask(taskId, { status: resolvedStatus }, user?.name || 'Employee');

    // 2. Update local React state immediately so the card re-renders now
    setTasks((prev) =>
      prev.map((t) => t.id === taskId ? { ...t, status: resolvedStatus } : t)
    );

    // 3. Fire storage events for both keys so the manager dashboard
    //    picks up the task status AND the new log entry instantly.
    window.dispatchEvent(new StorageEvent('storage', { key: 'wf_tasks' }));
    window.dispatchEvent(new StorageEvent('storage', { key: 'wf_logs' }));
  }

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span>⚡</span>
          <h1>{t('app.name')}</h1>
          <span className={styles.badge}>{t('nav.employeeBadge')}</span>
        </div>
        <LogoutButton />
      </header>

      <main className={styles.main}>
        <h2 className={styles.pageTitle}>{t('employee.myTasks')} ({tasks.length})</h2>

        {tasks.length === 0 ? (
          <p className={styles.empty}>{t('employee.noTasks')}</p>
        ) : (
          tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              employeeName={user?.name || 'Employee'}
              onLogSubmitted={handleLogSubmitted}
            />
          ))
        )}
      </main>
    </div>
  );
}
