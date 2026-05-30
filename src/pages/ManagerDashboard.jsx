import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import ReactMarkdown from 'react-markdown';
import LogoutButton from '../components/LogoutButton';
import styles from './ManagerDashboard.module.css';
import { MOCK_EMPLOYEES, MOCK_AI_SUMMARY } from '../api/mockData';
import {
  getAllTasks, addTask, getTaskStats,
  getNeedsAttentionTasks, getEmployeeSummaries,
  getAuditTrail, getLogsForTask,
} from '../api/taskStore';
// import client from '../api/client'; // ← uncomment when backend is ready

// ─── Helpers ──────────────────────────────────────────────────────────────────
function isOverdue(task) {
  return task.status !== 'Done' && new Date(task.deadline) < new Date(new Date().toDateString());
}

function statusClass(status, overdue, s) {
  if (overdue) return s.statusOverdue;
  return { Pending: s.statusPending, 'In Progress': s.statusInProgress, Done: s.statusDone }[status] || s.statusPending;
}

function priorityClass(p, s) {
  return { High: s.priorityHigh, Medium: s.priorityMedium, Low: s.priorityLow }[p];
}

function confidenceClass(c, s) {
  return { High: s.confHigh, Medium: s.confMedium, Low: s.confLow }[c] || s.confMedium;
}

function fmt(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  return d.toLocaleString(undefined, { dateStyle: 'short', timeStyle: 'short' });
}

// ─── Problem 1 — Stats Bar ────────────────────────────────────────────────────
function StatsBar({ stats }) {
  return (
    <div className={styles.statsBar}>
      <div className={styles.statCard}>
        <span className={styles.statNum}>{stats.total}</span>
        <span className={styles.statLabel}>Total Tasks</span>
      </div>
      <div className={styles.statCard}>
        <span className={`${styles.statNum} ${styles.statPending}`}>{stats.pending}</span>
        <span className={styles.statLabel}>Pending</span>
      </div>
      <div className={styles.statCard}>
        <span className={`${styles.statNum} ${styles.statInProgress}`}>{stats.inProgress}</span>
        <span className={styles.statLabel}>In Progress</span>
      </div>
      <div className={styles.statCard}>
        <span className={`${styles.statNum} ${styles.statDone}`}>{stats.done}</span>
        <span className={styles.statLabel}>Done</span>
      </div>
      <div className={`${styles.statCard} ${stats.overdue > 0 ? styles.statCardAlert : ''}`}>
        <span className={`${styles.statNum} ${styles.statOverdue}`}>{stats.overdue}</span>
        <span className={styles.statLabel}>Overdue</span>
      </div>
    </div>
  );
}

// ─── Problem 3 — Employee Progress Panel ─────────────────────────────────────
function EmployeePanel({ summaries }) {
  return (
    <div className={styles.employeePanel}>
      <h3 className={styles.panelTitle}>👥 Team Overview</h3>
      <div className={styles.employeeGrid}>
        {summaries.map((emp) => {
          const completion = emp.total > 0 ? Math.round((emp.done / emp.total) * 100) : 0;
          const hasIssue = emp.overdue > 0 || emp.noLog > 0;
          return (
            <div key={emp.id} className={`${styles.empCard} ${hasIssue ? styles.empCardAlert : ''}`}>
              <div className={styles.empHeader}>
                <span className={styles.empName}>{emp.name}</span>
                {emp.overdue > 0 && (
                  <span className={styles.empBadgeOverdue}>⚠ {emp.overdue} overdue</span>
                )}
                {emp.noLog > 0 && (
                  <span className={styles.empBadgeNoLog}>📭 {emp.noLog} no log</span>
                )}
              </div>
              <div className={styles.empProgress}>
                <div className={styles.progressBar}>
                  <div className={styles.progressFill} style={{ width: `${completion}%` }} />
                </div>
                <span className={styles.progressLabel}>{completion}% done ({emp.done}/{emp.total})</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Problem 2 & 4 — Audit Drawer with Work Logs ─────────────────────────────
function AuditDrawer({ taskId, taskTitle, onClose }) {
  const { t } = useTranslation();
  const [tab, setTab] = useState('logs'); // default to logs tab — most relevant
  const [history, setHistory] = useState([]);
  const [logs, setLogs] = useState([]);
  const open = !!taskId;

  // Read fresh data from store
  function loadData() {
    if (!taskId) return;
    setHistory(getAuditTrail(taskId));
    setLogs(getLogsForTask(taskId));
  }

  // Load on open + poll every second while drawer is open so new
  // submissions from the employee appear in real time
  useEffect(() => {
    if (!taskId) return;
    loadData();
    const interval = setInterval(loadData, 1000);
    return () => clearInterval(interval);
  }, [taskId]);

  return (
    <>
      {open && <div className={styles.drawerOverlay} onClick={onClose} />}
      <aside className={`${styles.drawer} ${open ? styles.drawerOpen : ''}`}>
        <div className={styles.drawerHeader}>
          <div>
            <h3>{t('audit.title')}</h3>
            {taskTitle && <p className={styles.drawerTaskTitle}>{taskTitle}</p>}
          </div>
          <button className={styles.drawerClose} onClick={onClose} aria-label={t('audit.close')}>✕</button>
        </div>

        {/* Tab switcher */}
        <div className={styles.drawerTabs}>
          <button
            className={`${styles.drawerTab} ${tab === 'logs' ? styles.drawerTabActive : ''}`}
            onClick={() => setTab('logs')}
          >
            📝 Work Logs {logs.length > 0 && <span className={styles.tabBadge}>{logs.length}</span>}
          </button>
          <button
            className={`${styles.drawerTab} ${tab === 'audit' ? styles.drawerTabActive : ''}`}
            onClick={() => setTab('audit')}
          >
            📋 Audit Trail {history.length > 0 && <span className={styles.tabBadge}>{history.length}</span>}
          </button>
        </div>

        <div className={styles.drawerBody}>

          {/* ── Work Logs tab — proof of work with timestamps ── */}
          {tab === 'logs' && (
            logs.length === 0
              ? (
                <div className={styles.emptyDrawer}>
                  <span className={styles.emptyIcon}>📭</span>
                  <p>No work logs submitted yet.</p>
                  <p className={styles.emptyHint}>Logs will appear here in real time as the employee submits them.</p>
                </div>
              )
              : (
                <div className={styles.logList}>
                  {logs.map((log) => (
                    <div key={log.id} className={styles.logEntry}>
                      {/* Timestamp — prominent, always visible */}
                      <div className={styles.logTimestamp}>
                        🕐 Submitted: <strong>{fmt(log.submittedAt)}</strong>
                      </div>
                      <div className={styles.logMeta}>
                        <span className={styles.logActor}>{log.employeeName}</span>
                        <span className={`${styles.logStatusPill} ${log.status === 'Completed' ? styles.logStatusDone : styles.logStatusProgress}`}>
                          {log.status}
                        </span>
                        {log.hasProof && <span className={styles.logProof}>📎 Proof attached</span>}
                      </div>
                      <p className={styles.logText}>{log.logText}</p>
                      <div className={styles.logAI}>
                        <span className={`${styles.confPill} ${confidenceClass(log.aiConfidence, styles)}`}>
                          🤖 {log.aiConfidence} Confidence
                        </span>
                        <span className={styles.logFeedback}>{log.aiFeedback}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )
          )}

          {/* ── Audit Trail tab — full tamper-evident history ── */}
          {tab === 'audit' && (
            history.length === 0
              ? (
                <div className={styles.emptyDrawer}>
                  <span className={styles.emptyIcon}>📋</span>
                  <p>{t('audit.noHistory')}</p>
                </div>
              )
              : (
                <div className={styles.timeline}>
                  {history.map((entry) => (
                    <div key={entry.id} className={styles.timelineItem}>
                      <div className={styles.timelineTime}>🕐 {fmt(entry.timestamp)}</div>
                      <div>
                        <span className={styles.timelineActor}>{entry.actor}</span>
                        <span className={styles.timelineAction}> — {entry.action}</span>
                      </div>
                      <div className={styles.timelineDetail}>{entry.detail}</div>
                    </div>
                  ))}
                </div>
              )
          )}
        </div>
      </aside>
    </>
  );
}

// ─── Assign Task Modal ────────────────────────────────────────────────────────
function AssignTaskModal({ employees, onClose, onCreated }) {
  const { t } = useTranslation();
  const [form, setForm] = useState({
    title: '', description: '',
    assignedTo: employees[0]?.id || '',
    priority: 'Medium', deadline: '',
  });
  const [saving, setSaving] = useState(false);

  function set(field, value) { setForm((f) => ({ ...f, [field]: value })); }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);
    await new Promise((r) => setTimeout(r, 400));
    const emp = employees.find((e) => e.id === form.assignedTo);
    const newTask = {
      id: `t${Date.now()}`,
      ...form,
      assignedName: emp?.name || '',
      status: 'Pending',
    };
    onCreated(newTask);
    setSaving(false);
    onClose();
  }

  return (
    <div className={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal}>
        <h2>{t('assignModal.title')}</h2>
        <form onSubmit={handleSubmit} className={styles.modalForm}>
          <div className={styles.field}>
            <label>{t('assignModal.labelTitle')}</label>
            <input required value={form.title} onChange={(e) => set('title', e.target.value)} placeholder={t('assignModal.titlePlaceholder')} />
          </div>
          <div className={styles.field}>
            <label>{t('assignModal.labelDescription')}</label>
            <textarea value={form.description} onChange={(e) => set('description', e.target.value)} placeholder={t('assignModal.descriptionPlaceholder')} />
          </div>
          <div className={styles.field}>
            <label>{t('assignModal.labelAssignTo')}</label>
            <select value={form.assignedTo} onChange={(e) => set('assignedTo', e.target.value)}>
              {employees.map((emp) => <option key={emp.id} value={emp.id}>{emp.name}</option>)}
            </select>
          </div>
          <div className={styles.field}>
            <label>{t('assignModal.labelPriority')}</label>
            <select value={form.priority} onChange={(e) => set('priority', e.target.value)}>
              <option value="High">{t('priority.high')}</option>
              <option value="Medium">{t('priority.medium')}</option>
              <option value="Low">{t('priority.low')}</option>
            </select>
          </div>
          <div className={styles.field}>
            <label>{t('assignModal.labelDeadline')}</label>
            <input type="date" required value={form.deadline} onChange={(e) => set('deadline', e.target.value)} />
          </div>
          <div className={styles.modalActions}>
            <button type="button" className={styles.btnSecondary} onClick={onClose}>{t('assignModal.cancel')}</button>
            <button type="submit" className={styles.btnPrimary} disabled={saving}>
              {saving ? t('assignModal.saving') : t('assignModal.assignTask')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────
export default function ManagerDashboard() {
  const { t } = useTranslation();
  const [tasks, setTasks]           = useState(() => getAllTasks());
  const [stats, setStats]           = useState(() => getTaskStats());
  const [empSummaries, setEmpSummaries] = useState(() => getEmployeeSummaries());
  const [employees]                 = useState(MOCK_EMPLOYEES);
  const [showModal, setShowModal]   = useState(false);
  const [selectedTask, setSelectedTask] = useState(null); // { id, title }
  const [summary, setSummary]       = useState('');
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [showSummary, setShowSummary] = useState(false);
  // Problem 5 — filter
  const [filter, setFilter]         = useState('all'); // 'all' | 'attention'
  const [attentionCount, setAttentionCount] = useState(() => getNeedsAttentionTasks().length);

  // Refresh store instantly on localStorage change (storage event fires
  // when ANOTHER tab writes) + visibilitychange covers same-tab navigation.
  // Also keep a 2s fallback poll for same-tab same-page updates.
  function refresh() {
    setTasks(getAllTasks());
    setStats(getTaskStats());
    setEmpSummaries(getEmployeeSummaries());
    setAttentionCount(getNeedsAttentionTasks().length);
  }

  useEffect(() => {
    // Cross-tab: fires immediately when another tab writes to localStorage
    function onStorage(e) {
      if (e.key === 'wf_tasks' || e.key === 'wf_logs' || e.key === null) {
        refresh();
      }
    }
    // Same-tab navigation: fires when user switches back to this tab
    function onVisibility() {
      if (document.visibilityState === 'visible') refresh();
    }

    window.addEventListener('storage', onStorage);
    window.addEventListener('focus', refresh);
    document.addEventListener('visibilitychange', onVisibility);

    // 2s poll catches same-tab same-page updates (employee & manager
    // both open in the same tab via back/forward navigation)
    const interval = setInterval(refresh, 2000);

    return () => {
      window.removeEventListener('storage', onStorage);
      window.removeEventListener('focus', refresh);
      document.removeEventListener('visibilitychange', onVisibility);
      clearInterval(interval);
    };
  }, []);

  // Filtered task list
  const displayTasks = filter === 'attention' ? getNeedsAttentionTasks() : tasks;
  const overdueTasks = tasks.filter(isOverdue);

  async function handleSummary() {
    setShowSummary(true);
    setSummaryLoading(true);
    await new Promise((r) => setTimeout(r, 800));
    setSummary(MOCK_AI_SUMMARY);
    setSummaryLoading(false);
  }

  function handleTaskCreated(newTask) {
    addTask(newTask, 'Manager');
    refresh();
  }

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span>⚡</span>
          <h1>{t('app.name')}</h1>
          <span className={styles.badge}>{t('nav.managerBadge')}</span>
        </div>
        <div className={styles.headerRight}>
          {/* Problem 5 — attention badge in header */}
          {attentionCount > 0 && (
            <button
              className={`${styles.attentionBtn} ${filter === 'attention' ? styles.attentionBtnActive : ''}`}
              onClick={() => setFilter((f) => f === 'attention' ? 'all' : 'attention')}
              title="Tasks needing attention (overdue or no log submitted)"
            >
              🔔 {attentionCount} need attention
            </button>
          )}
          <LogoutButton />
        </div>
      </header>

      <main className={styles.main}>
        {/* Problem 1 — Stats bar */}
        <StatsBar stats={stats} />

        {/* Problem 3 — Employee progress panel */}
        <EmployeePanel summaries={empSummaries} />

        {/* Overdue alert banner */}
        {overdueTasks.length > 0 && (
          <div className={styles.overdueBanner}>
            <strong>{t('manager.overdueAlert')}</strong>
            <ul className={styles.overdueList}>
              {overdueTasks.map((t_) => (
                <li key={t_.id}>{t_.title} — {t_.assignedName}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Toolbar */}
        <div className={styles.toolbar}>
          <div className={styles.toolbarLeft}>
            <h2>
              {filter === 'attention' ? '🔔 Needs Attention' : t('manager.allTasks')}
              {' '}({displayTasks.length})
            </h2>
            {filter === 'attention' && (
              <button className={styles.clearFilter} onClick={() => setFilter('all')}>
                ✕ Show all
              </button>
            )}
          </div>
          <div className={styles.toolbarActions}>
            <button className={styles.btnSecondary} onClick={handleSummary} disabled={summaryLoading}>
              {summaryLoading ? t('manager.generating') : t('manager.whereIsMyTeam')}
            </button>
            <button className={styles.btnPrimary} onClick={() => setShowModal(true)}>
              {t('manager.assignTask')}
            </button>
          </div>
        </div>

        {/* Task table */}
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>{t('manager.tableTitle')}</th>
                <th>{t('manager.tableAssignedTo')}</th>
                <th>{t('manager.tablePriority')}</th>
                <th>{t('manager.tableDeadline')}</th>
                <th>{t('manager.tableStatus')}</th>
                {/* Problem 2 — log count column */}
                <th>Logs</th>
              </tr>
            </thead>
            <tbody>
              {displayTasks.map((task) => {
                const overdue = isOverdue(task);
                const logs = getLogsForTask(task.id);
                const lastLog = logs[0];
                return (
                  <tr
                    key={task.id}
                    className={overdue ? styles.rowOverdue : ''}
                    onClick={() => setSelectedTask({ id: task.id, title: task.title })}
                    title={t('manager.clickForAudit')}
                  >
                    <td>{task.title}</td>
                    <td>{task.assignedName}</td>
                    <td>
                      <span className={`${styles.priorityBadge} ${priorityClass(task.priority, styles)}`}>
                        {t(`priority.${task.priority.toLowerCase()}`)}
                      </span>
                    </td>
                    <td>{task.deadline}</td>
                    <td>
                      <span className={`${styles.statusBadge} ${statusClass(task.status, overdue, styles)}`}>
                        {overdue ? t('status.overdue') : t(`status.${task.status === 'In Progress' ? 'inProgress' : task.status.toLowerCase()}`)}
                      </span>
                    </td>
                    {/* Problem 2 — show log count + last AI confidence */}
                    <td>
                      {logs.length === 0
                        ? <span className={styles.noLog}>None</span>
                        : <span className={`${styles.confPill} ${confidenceClass(lastLog.aiConfidence, styles)}`}>
                            {logs.length} · {lastLog.aiConfidence}
                          </span>
                      }
                    </td>
                  </tr>
                );
              })}
              {displayTasks.length === 0 && (
                <tr><td colSpan={6} className={styles.emptyRow}>No tasks match this filter.</td></tr>
              )}
            </tbody>
          </table>
        </div>

        {/* AI Summary panel */}
        {showSummary && (
          <div className={styles.summaryPanel}>
            <h3>{t('manager.whereIsMyTeamTitle')}</h3>
            {summaryLoading
              ? <p className={styles.summaryLoading}>{t('manager.generatingSummary')}</p>
              : <div className={styles.summaryText}><ReactMarkdown>{summary}</ReactMarkdown></div>
            }
          </div>
        )}
      </main>

      {showModal && (
        <AssignTaskModal employees={employees} onClose={() => setShowModal(false)} onCreated={handleTaskCreated} />
      )}

      {/* Problem 2 & 4 — Audit drawer with work logs tab */}
      <AuditDrawer
        taskId={selectedTask?.id}
        taskTitle={selectedTask?.title}
        onClose={() => setSelectedTask(null)}
      />
    </div>
  );
}
