// ── MOCK DATA ────────────────────────────────────────────────────────────────
// Replace these with real API calls once the backend is ready.

export const MOCK_EMPLOYEES = [
  { id: '2', name: 'Bob Employee' },
  { id: '3', name: 'Carol Smith' },
  { id: '4', name: 'David Lee' },
];

const today = new Date();
const daysFromNow = (n) => {
  const d = new Date(today);
  d.setDate(d.getDate() + n);
  return d.toISOString().split('T')[0];
};

export const MOCK_TASKS = [
  {
    id: 't1',
    title: 'Prepare Q2 Sales Report',
    description: 'Compile all Q2 sales figures and create a summary deck.',
    assignedTo: '2',
    assignedName: 'Bob Employee',
    priority: 'High',
    deadline: daysFromNow(-2), // overdue
    status: 'In Progress',
  },
  {
    id: 't2',
    title: 'Update Client Onboarding Docs',
    description: 'Revise the onboarding checklist with new product features.',
    assignedTo: '3',
    assignedName: 'Carol Smith',
    priority: 'Medium',
    deadline: daysFromNow(3),
    status: 'Pending',
  },
  {
    id: 't3',
    title: 'Fix Invoice Discrepancy',
    description: 'Investigate and resolve the $400 discrepancy in March invoices.',
    assignedTo: '4',
    assignedName: 'David Lee',
    priority: 'High',
    deadline: daysFromNow(-1), // overdue
    status: 'Pending',
  },
  {
    id: 't4',
    title: 'Schedule Team Training',
    description: 'Book a venue and send calendar invites for the Q3 training session.',
    assignedTo: '2',
    assignedName: 'Bob Employee',
    priority: 'Low',
    deadline: daysFromNow(7),
    status: 'Done',
  },
  {
    id: 't5',
    title: 'Review New Supplier Contracts',
    description: 'Read through the three new supplier contracts and flag any concerns.',
    assignedTo: '3',
    assignedName: 'Carol Smith',
    priority: 'Medium',
    deadline: daysFromNow(1),
    status: 'In Progress',
  },
];

export const MOCK_HISTORY = {
  t1: [
    {
      id: 'h1',
      timestamp: '2026-05-28 09:14',
      actorName: 'Alice Manager',
      action: 'Task Created',
      detail: 'Task assigned to Bob Employee with High priority.',
    },
    {
      id: 'h2',
      timestamp: '2026-05-28 11:30',
      actorName: 'Bob Employee',
      action: 'Status Updated',
      detail: 'Status changed from Pending → In Progress.',
    },
    {
      id: 'h3',
      timestamp: '2026-05-29 10:05',
      actorName: 'Bob Employee',
      action: 'Work Log Submitted',
      detail: 'Compiled raw sales data from CRM. Still need to build the deck.',
    },
    {
      id: 'h4',
      timestamp: '2026-05-29 10:06',
      actorName: 'AI Verifier',
      action: 'Log Verified',
      detail: 'Confidence: Medium — log describes partial progress but lacks specifics on completion.',
    },
    {
      id: 'h5',
      timestamp: '2026-05-30 08:00',
      actorName: 'System',
      action: 'Overdue Alert',
      detail: 'Task passed its deadline of 2026-05-28 without completion.',
    },
  ],
  t2: [
    {
      id: 'h6',
      timestamp: '2026-05-29 14:00',
      actorName: 'Alice Manager',
      action: 'Task Created',
      detail: 'Task assigned to Carol Smith with Medium priority.',
    },
    {
      id: 'h7',
      timestamp: '2026-05-30 09:20',
      actorName: 'Carol Smith',
      action: 'Status Updated',
      detail: 'Status changed from Pending → In Progress.',
    },
  ],
};

export const MOCK_MY_TASKS = MOCK_TASKS.filter((t) => t.assignedTo === '2');

export const MOCK_AI_SUMMARY = `**Team Status — May 30, 2026**

🔴 **Overdue (2 tasks):** Bob Employee's "Q2 Sales Report" is 2 days past deadline and still In Progress. David Lee's "Fix Invoice Discrepancy" is 1 day overdue with no log submitted — follow up immediately.

🟡 **At Risk (1 task):** Carol Smith's "Review New Supplier Contracts" is due tomorrow and currently In Progress. No blockers reported.

🟢 **On Track (1 task):** Carol Smith's "Update Client Onboarding Docs" is Pending with 3 days remaining.

✅ **Completed (1 task):** Bob Employee completed "Schedule Team Training" on time.

**Recommendation:** Prioritise a check-in with David Lee today — no activity has been logged on the overdue invoice task.`;
