// ── MOCK DATA ────────────────────────────────────────────────────────────────
// Replace these with real API calls once the backend is ready.

// ── All users (manager + employees) ──────────────────────────────────────────
export const MOCK_USERS = [
  { id: '1', name: 'Alice Manager', email: 'manager@demo.com',  role: 'manager',  password: 'password' },
  { id: '2', name: 'Bob Employee',  email: 'bob@demo.com',      role: 'employee', password: 'password' },
  { id: '3', name: 'Carol Smith',   email: 'carol@demo.com',    role: 'employee', password: 'password' },
  { id: '4', name: 'David Lee',     email: 'david@demo.com',    role: 'employee', password: 'password' },
];

export const MOCK_EMPLOYEES = MOCK_USERS.filter((u) => u.role === 'employee').map(
  ({ id, name }) => ({ id, name })
);

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
    deadline: daysFromNow(-2),
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
    deadline: daysFromNow(-1),
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
  {
    id: 't6',
    title: 'Reconcile Monthly Expenses',
    description: 'Cross-check all expense claims against receipts for May.',
    assignedTo: '4',
    assignedName: 'David Lee',
    priority: 'Medium',
    deadline: daysFromNow(4),
    status: 'Pending',
  },
  {
    id: 't7',
    title: 'Draft Q3 Marketing Plan',
    description: 'Outline campaigns, budget allocation, and KPIs for Q3.',
    assignedTo: '2',
    assignedName: 'Bob Employee',
    priority: 'Medium',
    deadline: daysFromNow(5),
    status: 'Pending',
  },
  {
    id: 't8',
    title: 'Conduct Vendor Evaluation',
    description: 'Evaluate three shortlisted vendors and submit a recommendation.',
    assignedTo: '3',
    assignedName: 'Carol Smith',
    priority: 'High',
    deadline: daysFromNow(2),
    status: 'In Progress',
  },
];

export const MOCK_AI_SUMMARY = `**Team Status — Today**

🔴 **Overdue:** Bob's "Q2 Sales Report" is 2 days past deadline. David's "Fix Invoice Discrepancy" is 1 day overdue with no log submitted.

🟡 **At Risk:** Carol's "Review New Supplier Contracts" is due tomorrow. Carol's "Vendor Evaluation" is due in 2 days and in progress.

🟢 **On Track:** Bob's "Q3 Marketing Plan" (5d), David's "Reconcile Expenses" (4d), Carol's "Onboarding Docs" (3d).

✅ **Completed:** Bob completed "Schedule Team Training" on time.

**Recommendation:** Follow up with David immediately — no activity logged on either of his tasks.`;
