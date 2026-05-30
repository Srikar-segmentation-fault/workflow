/**
 * taskStore.js — Shared localStorage-backed task store.
 * Single source of truth for tasks, work logs, and audit trail.
 */
import { MOCK_TASKS } from './mockData';

const TASKS_KEY = 'wf_tasks';
const LOGS_KEY  = 'wf_logs';
const AUDIT_KEY = 'wf_audit';

// ─── Helpers ──────────────────────────────────────────────────────────────────
function nowISO() {
  return new Date().toISOString();
}

function readMap(key) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    // Must be a plain object (not null, not array)
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) return parsed;
    return null;
  } catch {
    return null;
  }
}

function readArray(key) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeJSON(key, value) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // storage quota exceeded — silently ignore
  }
}

// ─── Seed ─────────────────────────────────────────────────────────────────────
function seed() {
  if (readMap(TASKS_KEY)) return; // already seeded

  const map = {};
  MOCK_TASKS.forEach((t) => { map[t.id] = { ...t }; });
  writeJSON(TASKS_KEY, map);

  const audit = MOCK_TASKS.map((t) => ({
    id: `a_seed_${t.id}`,
    taskId: t.id,
    timestamp: '2026-05-28T09:00:00.000Z',
    actor: 'Alice Manager',
    action: 'Task Created',
    detail: `Assigned to ${t.assignedName} — ${t.priority} priority, due ${t.deadline}.`,
  }));
  writeJSON(AUDIT_KEY, audit);
}

// ─── Tasks ────────────────────────────────────────────────────────────────────
export function getAllTasks() {
  seed();
  const map = readMap(TASKS_KEY);
  return map ? Object.values(map) : [...MOCK_TASKS];
}

export function getMyTasks(employeeId) {
  return getAllTasks().filter((t) => t.assignedTo === employeeId);
}

export function updateTask(taskId, patch, actorName = 'Employee') {
  seed();
  const map = readMap(TASKS_KEY);
  if (!map) return;
  if (!map[taskId]) return;

  const prev = { ...map[taskId] };
  map[taskId] = { ...prev, ...patch };
  writeJSON(TASKS_KEY, map);

  // Audit every status change
  if (patch.status && patch.status !== prev.status) {
    appendAudit({
      taskId,
      actor: actorName,
      action: 'Status Updated',
      detail: `Status changed from ${prev.status} → ${patch.status}.`,
    });
  }
}

export function addTask(task, actorName = 'Manager') {
  seed();
  const map = readMap(TASKS_KEY) || {};
  map[task.id] = { ...task };
  writeJSON(TASKS_KEY, map);
  appendAudit({
    taskId: task.id,
    actor: actorName,
    action: 'Task Created',
    detail: `Assigned to ${task.assignedName} — ${task.priority} priority, due ${task.deadline}.`,
  });
}

// ─── Work Logs ────────────────────────────────────────────────────────────────
export function submitLog(taskId, { employeeName, logText, status, hasProof, aiConfidence, aiFeedback }) {
  const logsMap = readMap(LOGS_KEY) || {};
  if (!logsMap[taskId]) logsMap[taskId] = [];

  const entry = {
    id: `log_${Date.now()}_${Math.random().toString(36).slice(2, 5)}`,
    taskId,
    employeeName,
    logText,
    status,
    hasProof: !!hasProof,
    aiConfidence,
    aiFeedback,
    submittedAt: nowISO(),
  };
  logsMap[taskId].unshift(entry);
  writeJSON(LOGS_KEY, logsMap);

  // Use slightly different timestamps so audit IDs don't collide
  appendAudit({
    taskId,
    actor: employeeName,
    action: 'Work Log Submitted',
    detail: `"${logText.slice(0, 80)}${logText.length > 80 ? '…' : ''}"${hasProof ? ' 📎 Proof attached.' : ''}`,
  });

  // Small delay so the two audit entries get distinct timestamps
  setTimeout(() => {
    appendAudit({
      taskId,
      actor: 'AI Verifier',
      action: 'Log Verified',
      detail: `Confidence: ${aiConfidence} — ${aiFeedback}`,
    });
  }, 1);

  return entry;
}

export function getLogsForTask(taskId) {
  const logsMap = readMap(LOGS_KEY) || {};
  return logsMap[taskId] || [];
}

/**
 * Get ALL logs across every task, sorted newest-first.
 * Used by the manager's combined activity feed.
 */
export function getAllLogs() {
  const logsMap = readMap(LOGS_KEY) || {};
  const all = [];
  Object.values(logsMap).forEach((taskLogs) => {
    taskLogs.forEach((log) => all.push(log));
  });
  // Sort newest submission first
  return all.sort((a, b) => new Date(b.submittedAt) - new Date(a.submittedAt));
}

// ─── Audit Trail ──────────────────────────────────────────────────────────────
function appendAudit(entry) {
  const trail = readArray(AUDIT_KEY);
  trail.unshift({
    id: `a_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
    timestamp: nowISO(),
    ...entry,
  });
  writeJSON(AUDIT_KEY, trail);
}

export function getAuditTrail(taskId) {
  return readArray(AUDIT_KEY).filter((e) => e.taskId === taskId);
}

// ─── Stats ────────────────────────────────────────────────────────────────────
export function getTaskStats() {
  const tasks = getAllTasks();
  const today = new Date(new Date().toDateString());
  return {
    total:      tasks.length,
    pending:    tasks.filter((t) => t.status === 'Pending').length,
    inProgress: tasks.filter((t) => t.status === 'In Progress').length,
    done:       tasks.filter((t) => t.status === 'Done').length,
    overdue:    tasks.filter((t) => t.status !== 'Done' && new Date(t.deadline) < today).length,
  };
}

export function getNeedsAttentionTasks() {
  const tasks  = getAllTasks();
  const logsMap = readMap(LOGS_KEY) || {};
  const today  = new Date(new Date().toDateString());
  return tasks.filter((t) => {
    if (t.status === 'Done') return false;
    const isOverdue = new Date(t.deadline) < today;
    const hasNoLogs = !logsMap[t.id] || logsMap[t.id].length === 0;
    return isOverdue || hasNoLogs;
  });
}

export function getEmployeeSummaries() {
  const tasks   = getAllTasks();
  const logsMap = readMap(LOGS_KEY) || {};
  const today   = new Date(new Date().toDateString());
  const map     = {};

  tasks.forEach((t) => {
    if (!map[t.assignedTo]) {
      map[t.assignedTo] = { id: t.assignedTo, name: t.assignedName, total: 0, done: 0, overdue: 0, noLog: 0 };
    }
    const e = map[t.assignedTo];
    e.total++;
    if (t.status === 'Done') { e.done++; return; }
    if (new Date(t.deadline) < today) e.overdue++;
    if (!logsMap[t.id] || logsMap[t.id].length === 0) e.noLog++;
  });

  return Object.values(map);
}

// ─── Clear (logout) ───────────────────────────────────────────────────────────
// Tasks, logs, and audit trail are COMPANY data — they persist across sessions.
// Only call this when you want a full reset (e.g. dev/testing).
export function clearTasks() {
  localStorage.removeItem(TASKS_KEY);
  localStorage.removeItem(LOGS_KEY);
  localStorage.removeItem(AUDIT_KEY);
}

// Called on every logout — does NOT wipe task/log data.
export function clearSession() {
  // nothing to clear at store level; auth tokens are handled by AuthContext
}
