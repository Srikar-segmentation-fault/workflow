import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import LogoutButton from '../components/LogoutButton';
import styles from './ManagerDashboard.module.css';
import {
  MOCK_TASKS,
  MOCK_EMPLOYEES,
  MOCK_HISTORY,
  MOCK_AI_SUMMARY,
} from '../api/mockData';
// import client from '../api/client'; // ← uncomment when backend is ready

// ── Helpers ──────────────────────────────────────────────────────────────────
function isOverdue(task) {
  return (
    task.status !== 'Done' &&
    new Date(task.deadline) < new Date(new Date().toDateString())
  );
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

// ── Audit Drawer ──────────────────────────────────────────────────────────────
function AuditDrawer({ task, onClose }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const open = !!task;

  useEffect(() => {
    if (!task) return;
    setLoading(true);

    // ── MOCK history ──────────────────────────────────────────────────────────
    // TODO: replace with real API call:
    // const { data } = await client.get(`/api/tasks/${task.id}/history`);
    // setHistory(data);
    setTimeout(() => {
      setHistory(MOCK_HISTORY[task.id] || []);
      setLoading(false);
    }, 300);
    // ── END MOCK ──────────────────────────────────────────────────────────────
  }, [task]);

  return (
    <>
      {open && <div className={styles.drawerOverlay} onClick={onClose} />}
      <aside className={`${styles.drawer} ${open ? styles.drawerOpen : ''}`}>
        <div className={styles.drawerHeader}>
          <div>
            <h3>Audit Trail</h3>
            {task && <p>{task.title}</p>}
          </div>
          <button className={styles.drawerClose} onClick={onClose} aria-label="Close">✕</button>
        </div>
        <div className={styles.drawerBody}>
          {loading ? (
            <p className={styles.emptyHistory}>Loading history…</p>
          ) : history.length === 0 ? (
            <p className={styles.emptyHistory}>No history yet for this task.</p>
          ) : (
            <div className={styles.timeline}>
              {history.map((entry) => (
                <div key={entry.id} className={styles.timelineItem}>
                  <div className={styles.timelineTime}>{entry.timestamp}</div>
                  <div>
                    <span className={styles.timelineActor}>{entry.actorName}</span>
                    <span className={styles.timelineAction}>— {entry.action}</span>
                  </div>
                  <div className={styles.timelineDetail}>{entry.detail}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </aside>
    </>
  );
}

// ── Assign Task Modal ─────────────────────────────────────────────────────────
function AssignTaskModal({ employees, onClose, onCreated }) {
  const [form, setForm] = useState({
    title: '',
    description: '',
    assignedTo: employees[0]?.id || '',
    priority: 'Medium',
    deadline: '',
  });
  const [saving, setSaving] = useState(false);

  function set(field, value) {
    setForm((f) => ({ ...f, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setSaving(true);

    // ── MOCK create ───────────────────────────────────────────────────────────
    // TODO: replace with real API call:
    // const { data } = await client.post('/api/tasks', form);
    // onCreated(data);
    await new Promise((r) => setTimeout(r, 400));
    const emp = employees.find((e) => e.id === form.assignedTo);
    const newTask = {
      id: `t${Date.now()}`,
      ...form,
      assignedName: emp?.name || '',
      status: 'Pending',
    };
    onCreated(newTask);
    // ── END MOCK ──────────────────────────────────────────────────────────────

    setSaving(false);
    onClose();
  }

  return (
    <div className={styles.overlay} onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className={styles.modal}>
        <h2>Assign New Task</h2>
        <form onSubmit={handleSubmit} className={styles.modalForm}>
          <div className={styles.field}>
            <label>Title</label>
            <input
              required
              value={form.title}
              onChange={(e) => set('title', e.target.value)}
              placeholder="e.g. Prepare monthly report"
            />
          </div>
          <div className={styles.field}>
            <label>Description</label>
            <textarea
              value={form.description}
              onChange={(e) => set('description', e.target.value)}
              placeholder="What needs to be done?"
            />
          </div>
          <div className={styles.field}>
            <label>Assign To</label>
            <select value={form.assignedTo} onChange={(e) => set('assignedTo', e.target.value)}>
              {employees.map((emp) => (
                <option key={emp.id} value={emp.id}>{emp.name}</option>
              ))}
            </select>
          </div>
          <div className={styles.field}>
            <label>Priority</label>
            <select value={form.priority} onChange={(e) => set('priority', e.target.value)}>
              <option>High</option>
              <option>Medium</option>
              <option>Low</option>
            </select>
          </div>
          <div className={styles.field}>
            <label>Deadline</label>
            <input
              type="date"
              required
              value={form.deadline}
              onChange={(e) => set('deadline', e.target.value)}
            />
          </div>
          <div className={styles.modalActions}>
            <button type="button" className={styles.btnSecondary} onClick={onClose}>Cancel</button>
            <button type="submit" className={styles.btnPrimary} disabled={saving}>
              {saving ? 'Saving…' : 'Assign Task'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function ManagerDashboard() {
  const [tasks, setTasks] = useState([]);
  const [employees] = useState(MOCK_EMPLOYEES);
  const [showModal, setShowModal] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);
  const [summary, setSummary] = useState('');
  const [summaryLoading, setSummaryLoading] = useState(false);
  const [showSummary, setShowSummary] = useState(false);

  useEffect(() => {
    // ── MOCK fetch tasks ──────────────────────────────────────────────────────
    // TODO: replace with: const { data } = await client.get('/api/tasks');
    setTasks(MOCK_TASKS);
    // ── END MOCK ──────────────────────────────────────────────────────────────
  }, []);

  const overdueTasks = tasks.filter(isOverdue);

  async function handleSummary() {
    setShowSummary(true);
    setSummaryLoading(true);

    // ── MOCK AI summary ───────────────────────────────────────────────────────
    // TODO: replace with: const { data } = await client.get('/api/ai/summary');
    // setSummary(data.summary);
    await new Promise((r) => setTimeout(r, 800));
    setSummary(MOCK_AI_SUMMARY);
    // ── END MOCK ──────────────────────────────────────────────────────────────

    setSummaryLoading(false);
  }

  function handleTaskCreated(newTask) {
    setTasks((prev) => [newTask, ...prev]);
  }

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <span>⚡</span>
          <h1>WorkFlow</h1>
          <span className={styles.badge}>Manager</span>
        </div>
        <LogoutButton />
      </header>

      <main className={styles.main}>
        {/* Overdue alert banner */}
        {overdueTasks.length > 0 && (
          <div className={styles.overdueBanner}>
            <strong>⚠ Overdue:</strong>
            <ul className={styles.overdueList}>
              {overdueTasks.map((t) => (
                <li key={t.id}>
                  {t.title} — {t.assignedName}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Toolbar */}
        <div className={styles.toolbar}>
          <h2>All Tasks ({tasks.length})</h2>
          <div className={styles.toolbarActions}>
            <button
              className={styles.btnSecondary}
              onClick={handleSummary}
              disabled={summaryLoading}
            >
              {summaryLoading ? '⏳ Generating…' : '🤖 Where\'s my team?'}
            </button>
            <button className={styles.btnPrimary} onClick={() => setShowModal(true)}>
              + Assign Task
            </button>
          </div>
        </div>

        {/* Task table */}
        <div className={styles.tableWrap}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Task Title</th>
                <th>Assigned To</th>
                <th>Priority</th>
                <th>Deadline</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {tasks.map((task) => {
                const overdue = isOverdue(task);
                return (
                  <tr
                    key={task.id}
                    className={overdue ? styles.rowOverdue : ''}
                    onClick={() => setSelectedTask(task)}
                    title="Click to view audit trail"
                  >
                    <td>{task.title}</td>
                    <td>{task.assignedName}</td>
                    <td>
                      <span className={`${styles.priorityBadge} ${priorityClass(task.priority)}`}>
                        {task.priority}
                      </span>
                    </td>
                    <td>{task.deadline}</td>
                    <td>
                      <span className={`${styles.statusBadge} ${statusClass(task.status, overdue)}`}>
                        {overdue ? 'Overdue' : task.status}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* AI Summary panel */}
        {showSummary && (
          <div className={styles.summaryPanel}>
            <h3>🤖 Where&apos;s My Team?</h3>
            {summaryLoading ? (
              <p className={styles.summaryLoading}>Generating summary…</p>
            ) : (
              <div className={styles.summaryText}>
                <ReactMarkdown>{summary}</ReactMarkdown>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Assign Task Modal */}
      {showModal && (
        <AssignTaskModal
          employees={employees}
          onClose={() => setShowModal(false)}
          onCreated={handleTaskCreated}
        />
      )}

      {/* Audit Trail Drawer */}
      <AuditDrawer task={selectedTask} onClose={() => setSelectedTask(null)} />
    </div>
  );
}
