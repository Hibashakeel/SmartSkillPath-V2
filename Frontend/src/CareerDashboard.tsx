import { useEffect, useState } from 'react';
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUp, BookOpen, Check, CheckCircle2, Compass, Map, Plus, RefreshCw, Save, Target, Trash2, TrendingUp, UserRound } from 'lucide-react';
import AppNavbar, { type AppPage } from './AppNavbar';
import { resolveCertification } from './certificationData';
import {
  decodeRoadmapDescription,
  encodeRoadmapDescription,
  isHttpUrl,
  roadmapStepTypes,
  type RoadmapStepType,
} from './roadmapMetadata';

type RoadmapStatus = 'not_started' | 'in_progress' | 'completed';
type GoalStatus = 'active' | 'paused' | 'completed';
type StepType = RoadmapStepType;
const stepTypes = roadmapStepTypes;

function displayValues(values: unknown[] | undefined): string[] {
  if (!values) return [];
  return values
    .map((value) => {
      if (typeof value === 'string') return value.trim();
      if (value && typeof value === 'object') {
        const record = value as Record<string, unknown>;
        const label = record.role ?? record.name ?? record.title;
        return typeof label === 'string' ? label.trim() : '';
      }
      return '';
    })
    .filter(Boolean);
}
type RoadmapItem = {
  id: number;
  goal_id: number | null;
  title: string;
  description: string;
  phase: string;
  priority: 'high' | 'medium' | 'low';
  status: RoadmapStatus;
  position: number;
};
type CareerGoal = {
  id: number;
  title: string;
  target_career: string;
  description: string;
  target_date: string | null;
  created_at?: string;
  status: GoalStatus;
  completed_steps: number;
  total_steps: number;
  progress_percent: number;
  remaining_steps: number;
  next_steps: { id: number; title: string; status: RoadmapStatus; position: number }[];
};
type SavedRecommendation = {
  id: number;
  career: string;
  selected_skills: string[];
  results: {
    skill_gap?: string[];
    recommended_skills?: string[];
    certifications?: unknown[];
    matching_roles?: unknown[];
    [key: string]: unknown;
  };
  created_at: string;
};
type Request = (path: string, init?: RequestInit) => Promise<any>;
type WorkspaceView = 'overview' | 'recommendations' | 'goals' | 'roadmaps' | 'roadmap-detail';

type Props = {
  request: Request;
  initialNotice: string;
  activePage: AppPage;
  userEmail: string;
  skillOptions: string[];
  onNavigate: (page: AppPage) => void;
  onOpenAccountPage: (page: 'Profile' | 'Settings' | 'Accessibility') => void;
  onSwitchAccount: () => void;
  onSignOut: () => void;
};

export default function CareerDashboard({
  request,
  initialNotice,
  activePage,
  userEmail,
  skillOptions,
  onNavigate,
  onOpenAccountPage,
  onSwitchAccount,
  onSignOut,
}: Props) {
  const [careerGoals, setCareerGoals] = useState<CareerGoal[]>([]);
  const [workspaceView, setWorkspaceView] = useState<WorkspaceView>('overview');
  const [legacyGoals, setLegacyGoals] = useState<string[]>([]);
  const [recommendations, setRecommendations] = useState<SavedRecommendation[]>([]);
  const [roadmaps, setRoadmaps] = useState<Record<number, RoadmapItem[]>>({});
  const [activeGoalId, setActiveGoalId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState(initialNotice);
  const [title, setTitle] = useState('');
  const [career, setCareer] = useState('');
  const [description, setDescription] = useState('');
  const [targetDate, setTargetDate] = useState('');
  const [legacyGoalInput, setLegacyGoalInput] = useState('');
  const [stepTitle, setStepTitle] = useState('');
  const [stepDescription, setStepDescription] = useState('');
  const [stepType, setStepType] = useState<StepType>('Learn a Skill');
  const [stepCategory, setStepCategory] = useState('');
  const [stepResourceUrl, setStepResourceUrl] = useState('');
  const [stepPriority, setStepPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [stepStatus, setStepStatus] = useState<RoadmapStatus>('not_started');
  const [goalEdits, setGoalEdits] = useState<Record<number, Partial<CareerGoal>>>({});
  const [draggedItemId, setDraggedItemId] = useState<number | null>(null);

  const activeGoal = careerGoals.find((goal) => goal.id === activeGoalId) ?? null;
  const activeItems = activeGoal ? roadmaps[activeGoal.id] ?? [] : [];
  const activeRoadmapCount = careerGoals.filter(
    (goal) => goal.status === 'active' && (roadmaps[goal.id]?.length ?? 0) > 0,
  ).length;
  const roadmapCount = careerGoals.filter((goal) => (roadmaps[goal.id]?.length ?? 0) > 0).length;
  const getProgress = (goal: CareerGoal) => {
    const items = roadmaps[goal.id] ?? [];
    const completed = items.filter((item) => item.status === 'completed').length;
    return {
      completed,
      total: items.length,
      percent: items.length ? Math.round((completed / items.length) * 100) : 0,
      remaining: items.length - completed,
    };
  };
  const completedStepCount = Object.values(roadmaps)
    .flat()
    .filter((item) => item.status === 'completed').length;

  function openRoadmap(goalId: number) {
    setActiveGoalId(goalId);
    setWorkspaceView('roadmap-detail');
  }

  async function refresh() {
    setLoading(true);
    setError('');
    try {
      const [goalData, legacyData, recommendationData] = await Promise.all([
        request('/api/career-goals'),
        request('/api/goals'),
        request('/api/recommendations'),
      ]);
      const entries = await Promise.all(
        (goalData.goals as CareerGoal[]).map(async (goal) => {
          const response = await request(`/api/roadmap?goal_id=${goal.id}`);
          return [goal.id, response.items as RoadmapItem[]] as const;
        }),
      );
      const nextRoadmaps = Object.fromEntries(entries) as Record<number, RoadmapItem[]>;
      setCareerGoals(goalData.goals);
      setLegacyGoals(legacyData.goals);
      setRecommendations(recommendationData.recommendations);
      setRoadmaps(nextRoadmaps);
      setActiveGoalId((current) =>
        (goalData.goals as CareerGoal[]).some((goal) => goal.id === current)
          ? current
          : goalData.goals[0]?.id ?? null,
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not load your career dashboard.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function perform(action: () => Promise<void>, success: string) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action();
      await refresh();
      setNotice(success);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'The request could not be completed.');
    } finally {
      setBusy(false);
    }
  }

  async function createGoal() {
    const cleanTitle = title.trim();
    const cleanCareer = career.trim();
    if (!cleanTitle || !cleanCareer) {
      setError('Enter a goal title and target career.');
      return;
    }
    await perform(async () => {
      const created = await request('/api/career-goals', {
        method: 'POST',
        body: JSON.stringify({
          title: cleanTitle,
          target_career: cleanCareer,
          description: description.trim(),
          target_date: targetDate || null,
        }),
      });
      setTitle('');
      setCareer('');
      setDescription('');
      setTargetDate('');
      setActiveGoalId(created.id);
    }, 'Career goal created.');
  }

  async function saveGoal(goal: CareerGoal) {
    const changes = goalEdits[goal.id];
    if (!changes || !Object.keys(changes).length) return;
    await perform(async () => {
      await request(`/api/career-goals/${goal.id}`, {
        method: 'PATCH',
        body: JSON.stringify(changes),
      });
      setGoalEdits((current) => {
        const next = { ...current };
        delete next[goal.id];
        return next;
      });
    }, 'Career goal updated.');
  }

  async function changeGoalStatus(goal: CareerGoal, status: GoalStatus) {
    await perform(async () => {
      await request(`/api/career-goals/${goal.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
    }, 'Goal status updated.');
  }

  async function deleteGoal(goal: CareerGoal) {
    const count = roadmaps[goal.id]?.length ?? 0;
    if (!window.confirm(`Delete “${goal.title}” and its ${count} roadmap steps? This cannot be undone.`)) return;
    await perform(async () => {
      await request(`/api/career-goals/${goal.id}`, { method: 'DELETE' });
      setGoalEdits((current) => {
        const next = { ...current };
        delete next[goal.id];
        return next;
      });
    }, 'Career goal and its roadmap deleted.');
  }

  async function addStep(event: React.FormEvent) {
    event.preventDefault();
    if (!activeGoal) return;
    const cleanTitle = stepTitle.trim();
    if (!cleanTitle) {
      setError('Enter a title for the roadmap step.');
      return;
    }
    if (stepResourceUrl && !isHttpUrl(stepResourceUrl.trim())) {
      setError('Resource links must begin with http:// or https://.');
      return;
    }
    const encodedDescription = encodeRoadmapDescription({
      notes: stepDescription.trim(),
      category: stepCategory,
      resourceUrl: stepResourceUrl.trim(),
      stepType,
    });
    if (encodedDescription.length > 2000) {
      setError('Shorten the description or resource link to fit the saved step limit.');
      return;
    }
    await perform(async () => {
      await request('/api/roadmap', {
        method: 'POST',
        body: JSON.stringify({
          goal_id: activeGoal.id,
          title: cleanTitle,
          description: encodedDescription,
          phase: 'Skill Development',
          priority: stepPriority,
          status: stepStatus,
        }),
      });
      setStepTitle('');
      setStepDescription('');
      setStepType('Learn a Skill');
      setStepCategory('');
      setStepResourceUrl('');
      setStepPriority('medium');
      setStepStatus('not_started');
    }, 'Roadmap step added.');
  }

  async function updateStep(item: RoadmapItem, changes: Partial<RoadmapItem>) {
    await perform(async () => {
      await request(`/api/roadmap/${item.id}`, {
        method: 'PATCH',
        body: JSON.stringify(changes),
      });
    }, 'Roadmap step updated.');
  }

  async function updateStepStatus(item: RoadmapItem, status: RoadmapStatus) {
    await perform(async () => {
      if (!activeGoal) return;
      const updated = await request(`/api/roadmap/${item.id}/progress`, {
        method: 'PATCH',
        body: JSON.stringify({ status }),
      });
      const nextItems = (roadmaps[activeGoal.id] ?? []).map((step) =>
        step.id === item.id ? updated : step,
      );
      const completed = nextItems.filter((step) => step.status === 'completed').length;
      setRoadmaps((current) => ({ ...current, [activeGoal.id]: nextItems }));
      setCareerGoals((current) =>
        current.map((goal) =>
          goal.id === activeGoal.id
            ? {
                ...goal,
                completed_steps: completed,
                total_steps: nextItems.length,
                progress_percent: nextItems.length
                  ? Math.round((completed / nextItems.length) * 100)
                  : 0,
                remaining_steps: nextItems.length - completed,
                next_steps: nextItems
                  .filter((step) => step.status !== 'completed')
                  .sort((left, right) => left.position - right.position)
                  .slice(0, 3)
                  .map(({ id, title, status: stepStatus, position }) => ({
                    id,
                    title,
                    status: stepStatus,
                    position,
                  })),
              }
            : goal,
        ),
      );
    }, 'Roadmap progress updated.');
  }

  async function deleteStep(item: RoadmapItem) {
    if (!window.confirm(`Delete the roadmap step “${item.title}”?`)) return;
    await perform(async () => {
      await request(`/api/roadmap/${item.id}`, { method: 'DELETE' });
    }, 'Roadmap step deleted.');
  }

  async function reorder(items: RoadmapItem[]) {
    if (!activeGoal) return;
    setBusy(true);
    setError('');
    setNotice('');
    try {
      const response = await request(`/api/career-goals/${activeGoal.id}/roadmap/order`, {
        method: 'PUT',
        body: JSON.stringify({ item_ids: items.map((item) => item.id) }),
      });
      setRoadmaps((current) => ({ ...current, [activeGoal.id]: response.items }));
      await refresh();
      setNotice('Roadmap order saved.');
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Could not reorder roadmap steps.');
      await refresh();
    } finally {
      setBusy(false);
    }
  }

  async function addLegacyGoal(event: React.FormEvent) {
    event.preventDefault();
    const value = legacyGoalInput.trim();
    if (!value || value.length > 300) {
      setError('Enter a learning goal of up to 300 characters.');
      return;
    }
    await perform(async () => {
      if (legacyGoals.length >= 100) throw new Error('You can save up to 100 learning goals.');
      await request('/api/goals', {
        method: 'POST',
        body: JSON.stringify({ goals: [...legacyGoals, value] }),
      });
      setLegacyGoalInput('');
    }, 'Learning goal saved.');
  }

  async function removeLegacyGoal(index: number) {
    await perform(async () => {
      await request('/api/goals', {
        method: 'POST',
        body: JSON.stringify({ goals: legacyGoals.filter((_, itemIndex) => itemIndex !== index) }),
      });
    }, 'Learning goal removed.');
  }

  function moveStep(index: number, direction: -1 | 1) {
    const destination = index + direction;
    if (destination < 0 || destination >= activeItems.length) return;
    const next = [...activeItems];
    [next[index], next[destination]] = [next[destination], next[index]];
    void reorder(next);
  }

  function dropStep(targetIndex: number) {
    if (draggedItemId === null) return;
    const fromIndex = activeItems.findIndex((item) => item.id === draggedItemId);
    if (fromIndex < 0 || fromIndex === targetIndex) return;
    const next = [...activeItems];
    const [moving] = next.splice(fromIndex, 1);
    next.splice(targetIndex, 0, moving);
    setDraggedItemId(null);
    void reorder(next);
  }

  const progressPercent = activeGoal?.total_steps
    ? Math.round((activeGoal.completed_steps / activeGoal.total_steps) * 100)
    : 0;

  return (
    <div className="site-shell">
      <div className="glow glow-a" />
      <div className="glow glow-b" />
      <AppNavbar
        activePage={activePage}
        userEmail={userEmail}
        onNavigate={onNavigate}
        onOpenProfile={() => onOpenAccountPage('Profile')}
        onOpenSettings={() => onOpenAccountPage('Settings')}
        onOpenAccessibility={() => onOpenAccountPage('Accessibility')}
        onSwitchAccount={onSwitchAccount}
        onLogout={onSignOut}
      />
      <main>
        <section className="inner-page career-dashboard">
          <header className="workspace-hero">
            <div>
              <span className="eyebrow"><UserRound size={14} /> YOUR PERSONAL WORKSPACE</span>
              <h1>My Space</h1>
              <p>Your personal career development workspace.</p>
            </div>
            <div className="dashboard-heading-actions">
              <button className="button-secondary" onClick={() => void refresh()} disabled={loading}><RefreshCw size={15} /> Refresh</button>
              <button className="button-primary" onClick={() => onNavigate('Explore')}><Compass size={15} /> Explore careers</button>
            </div>
          </header>
          {error && <div className="error-message" role="alert">{error}</div>}
          {notice && <div className="notice-message" role="status"><Check size={16} />{notice}</div>}
          {loading && <div className="workspace-state" role="status">Loading your private career data…</div>}

          <nav className="workspace-section-nav" aria-label="My Space sections">
            <button className={workspaceView === 'overview' ? 'is-current' : ''} aria-current={workspaceView === 'overview' ? 'page' : undefined} onClick={() => setWorkspaceView('overview')}><UserRound size={16} /> Overview</button>
            <button className={workspaceView === 'recommendations' ? 'is-current' : ''} aria-current={workspaceView === 'recommendations' ? 'page' : undefined} onClick={() => setWorkspaceView('recommendations')}><BookOpen size={16} /> Recommendations</button>
            <button className={workspaceView === 'goals' ? 'is-current' : ''} aria-current={workspaceView === 'goals' ? 'page' : undefined} onClick={() => setWorkspaceView('goals')}><Target size={16} /> Career Goals</button>
            <button className={workspaceView === 'roadmaps' || workspaceView === 'roadmap-detail' ? 'is-current' : ''} aria-current={workspaceView === 'roadmaps' || workspaceView === 'roadmap-detail' ? 'page' : undefined} onClick={() => setWorkspaceView('roadmaps')}><Map size={16} /> Roadmaps</button>
          </nav>

          {workspaceView === 'overview' && (
            <section className="workspace-overview">
              <div className="workspace-stat-grid" aria-label="Workspace summary">
                <article className="workspace-stat-card stat-recommendations"><BookOpen size={19} /><span>Saved Recommendations</span><strong>{recommendations.length}</strong></article>
                <article className="workspace-stat-card stat-goals"><Target size={19} /><span>Career Goals</span><strong>{careerGoals.length}</strong></article>
                <article className="workspace-stat-card stat-roadmaps"><Map size={19} /><span>Active Roadmaps</span><strong>{activeRoadmapCount}</strong></article>
                <article className="workspace-stat-card stat-completed"><CheckCircle2 size={19} /><span>Completed Steps</span><strong>{completedStepCount}</strong></article>
              </div>
              <div className="section-intro workspace-overview-heading"><div><span className="section-kicker">YOUR WORKSPACE</span><h2>Choose where to continue.</h2></div></div>
              <div className="workspace-hub-grid">
                <button className="workspace-hub-card hub-recommendations" onClick={() => setWorkspaceView('recommendations')}>
                  <span className="hub-icon"><BookOpen size={20} /></span><span className="hub-count">{recommendations.length} saved</span>
                  <h3>My Recommendations</h3><p>Revisit career matches, skill suggestions, and certification details.</p><span className="hub-action">View All <ArrowRight size={15} /></span>
                </button>
                <button className="workspace-hub-card hub-goals" onClick={() => setWorkspaceView('goals')}>
                  <span className="hub-icon"><Target size={20} /></span><span className="hub-count">{careerGoals.length} goals</span>
                  <h3>My Career Goals</h3><p>Manage each target career and keep your plans independent.</p><span className="hub-action">View All <ArrowRight size={15} /></span>
                </button>
                <button className="workspace-hub-card hub-roadmaps" onClick={() => setWorkspaceView('roadmaps')}>
                  <span className="hub-icon"><Map size={20} /></span><span className="hub-count">{roadmapCount} roadmaps</span>
                  <h3>My Roadmaps</h3><p>Track steps and progress for each saved career path.</p><span className="hub-action">View All <ArrowRight size={15} /></span>
                </button>
              </div>
              {!loading && !careerGoals.length && !recommendations.length && (
                <div className="workspace-empty workspace-empty-card"><Compass size={25} /><h3>Your workspace is ready</h3><p>Explore a career to get recommendations, or create a goal to start a roadmap.</p><button className="button-primary" onClick={() => onNavigate('Explore')}>Explore Careers <ArrowRight size={15} /></button></div>
              )}
              <p className="workspace-disclaimer">Roadmap completion reflects saved task progress; it is not a career-readiness or employability guarantee.</p>
            </section>
          )}

          {workspaceView === 'goals' && <section className="workspace-data-section">
            <div className="section-intro"><div><span className="section-kicker">CAREER GOALS</span><h2>Your planning dashboard.</h2></div><button className="button-primary" onClick={() => document.getElementById('create-career-goal')?.scrollIntoView({ behavior: 'smooth', block: 'center' })}><Plus size={15} /> Create a goal</button></div>
            {careerGoals.length === 0 && !loading && <p className="workspace-empty">No career goals yet. Create one below or explore a career and generate a roadmap draft.</p>}
            <div className="career-goal-cards">
              {careerGoals.map((goal) => {
                const progress = getProgress(goal);
                return <button type="button" className={`career-goal-card${goal.id === activeGoalId ? ' is-active' : ''}`} key={goal.id} onClick={() => setActiveGoalId(goal.id)}>
                  <span className="section-kicker">{goal.target_career}</span>
                  <h3>{goal.title}</h3>
                  <span className={`goal-status goal-status-${goal.status}`}>{goal.status}</span>
                  {goal.created_at && <small>Created {new Date(goal.created_at).toLocaleDateString()}</small>}
                  <div className="goal-progress-track" role="progressbar" aria-label={`${goal.title} roadmap completion`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={progress.percent}><span style={{ width: `${progress.percent}%` }} /></div>
                  <small>{progress.completed} of {progress.total} steps complete · {progress.remaining} remaining</small>
                  <small>{roadmaps[goal.id]?.length ?? 0} roadmap steps</small>
                  {goal.next_steps.length > 0 && <span className="goal-next-step">Next: {goal.next_steps[0].title}</span>}
                  {progress.total > 0 && <small>Task completion—not a career-readiness assessment.</small>}
                  <span className="hub-action">Manage Goal <ArrowRight size={15} /></span>
                </button>;
              })}
            </div>
          </section>}

          {activeGoal && (workspaceView === 'goals' || workspaceView === 'roadmap-detail') && <section className="workspace-data-section">
            {workspaceView === 'roadmap-detail' && <div className="workspace-breadcrumb"><button className="text-action" onClick={() => setWorkspaceView('roadmaps')}><ArrowLeft size={16} /> Back to My Roadmaps</button><span> / {activeGoal.title}</span></div>}
            <div className="section-intro"><div><span className="section-kicker">{workspaceView === 'goals' ? 'GOAL DETAILS' : 'ROADMAP DETAIL'}</span><h2>{activeGoal.title}</h2><p>{activeGoal.target_career} · {activeGoal.status}</p></div></div>
            {workspaceView === 'goals' && <>
            <div className="career-goal-editor">
              <label>Goal title<input value={goalEdits[activeGoal.id]?.title ?? activeGoal.title} maxLength={200} disabled={busy} onChange={(event) => setGoalEdits((current) => ({ ...current, [activeGoal.id]: { ...current[activeGoal.id], title: event.target.value } }))} /></label>
              <label>Target career<input value={goalEdits[activeGoal.id]?.target_career ?? activeGoal.target_career} maxLength={100} disabled={busy} onChange={(event) => setGoalEdits((current) => ({ ...current, [activeGoal.id]: { ...current[activeGoal.id], target_career: event.target.value } }))} /></label>
              <label>Description<input value={goalEdits[activeGoal.id]?.description ?? activeGoal.description} maxLength={2000} disabled={busy} onChange={(event) => setGoalEdits((current) => ({ ...current, [activeGoal.id]: { ...current[activeGoal.id], description: event.target.value } }))} /></label>
              <label>Target date<input type="date" value={goalEdits[activeGoal.id]?.target_date ?? activeGoal.target_date ?? ''} disabled={busy} onChange={(event) => setGoalEdits((current) => ({ ...current, [activeGoal.id]: { ...current[activeGoal.id], target_date: event.target.value || null } }))} /></label>
              <div className="career-goal-actions">
                <label>Status<select value={activeGoal.status} disabled={busy} onChange={(event) => void changeGoalStatus(activeGoal, event.target.value as GoalStatus)}><option value="active">Active</option><option value="paused">Paused</option><option value="completed">Completed</option></select></label>
                <button className="button-primary" disabled={busy || !goalEdits[activeGoal.id]} onClick={() => void saveGoal(activeGoal)}><Save size={15} /> Save goal</button>
                <button className="workspace-icon-button" disabled={busy} aria-label={`Delete ${activeGoal.title}`} onClick={() => void deleteGoal(activeGoal)}><Trash2 size={16} /></button>
              </div>
            </div>
            <div className="goal-progress-summary"><TrendingUp size={17} /><span>{activeGoal.completed_steps} completed of {activeGoal.total_steps} steps; {activeGoal.remaining_steps} remaining. Roadmap completion is not a guarantee of employability.</span><strong>{progressPercent}%</strong></div>
            {activeGoal.next_steps.length > 0 && <div className="goal-next-list"><b>Next incomplete steps</b>{activeGoal.next_steps.map((step) => <button key={step.id} onClick={() => openRoadmap(activeGoal.id)}>{step.title} <ArrowRight size={14} /></button>)}</div>}
            <button className="button-secondary" onClick={() => setWorkspaceView('roadmaps')}>View this goal’s roadmap <ArrowRight size={15} /></button>
            </>}

            {workspaceView === 'roadmap-detail' && <>
            <div className="goal-progress-summary"><TrendingUp size={17} /><span>{activeGoal.completed_steps} completed of {activeGoal.total_steps} steps; {activeGoal.remaining_steps} remaining.</span><strong>{progressPercent}%</strong></div>
            <div className="goal-progress-track roadmap-detail-progress" role="progressbar" aria-label={`${activeGoal.title} roadmap progress`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={progressPercent}><span style={{ width: `${progressPercent}%` }} /></div>
            <div className="section-intro roadmap-heading"><div><span className="section-kicker">ROADMAP</span><h2>Learning steps</h2><p>Drag to reorder, use the arrow buttons, or choose a step status.</p></div></div>
            <form className="workspace-roadmap-form roadmap-create-form" onSubmit={(event) => void addStep(event)}>
              <label>Step title<input value={stepTitle} maxLength={200} onChange={(event) => setStepTitle(event.target.value)} placeholder="Roadmap step title" required /></label>
              <label>Step type<select value={stepType} onChange={(event) => setStepType(event.target.value as StepType)}>{stepTypes.map((type) => <option key={type}>{type}</option>)}</select></label>
              <label>Skill or category<select value={stepCategory} onChange={(event) => setStepCategory(event.target.value)}><option value="">General / not specified</option>{skillOptions.map((skill) => <option key={skill} value={skill}>{skill}</option>)}</select></label>
              <label>Priority<select value={stepPriority} onChange={(event) => setStepPriority(event.target.value as 'low' | 'medium' | 'high')}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label>
              <label>Status<select value={stepStatus} onChange={(event) => setStepStatus(event.target.value as RoadmapStatus)}><option value="not_started">Not Started</option><option value="in_progress">In Progress</option><option value="completed">Completed</option></select></label>
              <label>Resource link (optional)<input type="url" maxLength={500} value={stepResourceUrl} onChange={(event) => setStepResourceUrl(event.target.value)} placeholder="https://…" /></label>
              <label className="roadmap-description-field">Description (optional)<textarea value={stepDescription} maxLength={1100} onChange={(event) => setStepDescription(event.target.value)} rows={2} /></label>
              <button className="button-primary" type="submit" disabled={busy}><Plus size={16} /> Add step</button>
            </form>
            {!activeItems.length && !loading && <p className="workspace-empty">No roadmap steps yet. Add steps manually or generate a draft from a career recommendation.</p>}
            <ol className="workspace-roadmap-list" aria-label={`${activeGoal.title} roadmap`}>
              {activeItems.map((item, index) => {
                const metadata = decodeRoadmapDescription(item.description);
                return (
                  <li
                    id={`roadmap-${item.id}`}
                    className="workspace-roadmap-item"
                    key={item.id}
                    draggable={!busy}
                    onDragStart={(event) => {
                      setDraggedItemId(item.id);
                      event.dataTransfer.effectAllowed = 'move';
                      event.dataTransfer.setData('text/plain', String(item.id));
                    }}
                    onDragOver={(event) => event.preventDefault()}
                    onDrop={(event) => {
                      event.preventDefault();
                      dropStep(index);
                    }}
                    onDragEnd={() => setDraggedItemId(null)}
                  >
                    <span className="roadmap-step-marker" aria-hidden="true">{index + 1}</span>
                    <div className="workspace-roadmap-fields">
                      <div className="roadmap-item-meta">
                        <span>{item.phase}</span>
                        <span className="step-type-badge">{metadata.stepType}</span>
                        <span className={`priority-${item.priority}`}>{item.priority} priority</span>
                        <span className={`step-status-badge step-status-${item.status}`}>{item.status.replace('_', ' ')}</span>
                      </div>
                      <label>Step title
                        <input
                          maxLength={200}
                          value={item.title}
                          disabled={busy}
                          onChange={(event) => setRoadmaps((current) => ({
                            ...current,
                            [activeGoal.id]: current[activeGoal.id].map((row) =>
                              row.id === item.id ? { ...row, title: event.target.value } : row,
                            ),
                          }))}
                        />
                      </label>
                      <div className="roadmap-step-edit-grid">
                        <label>Step type
                          <select
                            value={metadata.stepType}
                            disabled={busy}
                            onChange={(event) => {
                              const nextMetadata = { ...metadata, stepType: event.target.value as StepType };
                              setRoadmaps((current) => ({
                                ...current,
                                [activeGoal.id]: current[activeGoal.id].map((row) =>
                                  row.id === item.id
                                    ? { ...row, description: encodeRoadmapDescription(nextMetadata) }
                                    : row,
                                ),
                              }));
                            }}
                          >
                            {stepTypes.map((type) => <option key={type}>{type}</option>)}
                          </select>
                        </label>
                        <label>Skill or category
                          <select
                            value={metadata.category}
                            disabled={busy}
                            onChange={(event) => {
                              const nextMetadata = { ...metadata, category: event.target.value };
                              setRoadmaps((current) => ({
                                ...current,
                                [activeGoal.id]: current[activeGoal.id].map((row) =>
                                  row.id === item.id
                                    ? { ...row, description: encodeRoadmapDescription(nextMetadata) }
                                    : row,
                                ),
                              }));
                            }}
                          >
                            <option value="">General / not specified</option>
                            {skillOptions.map((skill) => <option key={skill}>{skill}</option>)}
                            {metadata.category && !skillOptions.includes(metadata.category) && (
                              <option value={metadata.category}>{metadata.category}</option>
                            )}
                          </select>
                        </label>
                        <label>Resource link
                          <input
                            type="url"
                            maxLength={500}
                            value={metadata.resourceUrl}
                            disabled={busy}
                            placeholder="https://…"
                            onChange={(event) => {
                              const nextMetadata = { ...metadata, resourceUrl: event.target.value };
                              setRoadmaps((current) => ({
                                ...current,
                                [activeGoal.id]: current[activeGoal.id].map((row) =>
                                  row.id === item.id
                                    ? { ...row, description: encodeRoadmapDescription(nextMetadata) }
                                    : row,
                                ),
                              }));
                            }}
                          />
                        </label>
                        <label>Description
                          <textarea
                            maxLength={1100}
                            rows={2}
                            value={metadata.notes}
                            disabled={busy}
                            onChange={(event) => {
                              const nextMetadata = { ...metadata, notes: event.target.value };
                              setRoadmaps((current) => ({
                                ...current,
                                [activeGoal.id]: current[activeGoal.id].map((row) =>
                                  row.id === item.id
                                    ? { ...row, description: encodeRoadmapDescription(nextMetadata) }
                                    : row,
                                ),
                              }));
                            }}
                          />
                        </label>
                      </div>
                      {metadata.category && <p className="roadmap-category-label">Skill or category: {metadata.category}</p>}
                      {isHttpUrl(metadata.resourceUrl) && (
                        <a className="roadmap-resource-link" href={metadata.resourceUrl} target="_blank" rel="noreferrer">
                          Open saved resource
                        </a>
                      )}
                      <div className="workspace-roadmap-actions">
                        <label>Priority
                          <select
                            value={item.priority}
                            disabled={busy}
                            onChange={(event) => void updateStep(item, { priority: event.target.value as RoadmapItem['priority'] })}
                          >
                            <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option>
                          </select>
                        </label>
                        <label>Status
                          <select
                            value={item.status}
                            disabled={busy}
                            onChange={(event) => void updateStepStatus(item, event.target.value as RoadmapStatus)}
                          >
                            <option value="not_started">Not Started</option><option value="in_progress">In Progress</option><option value="completed">Completed</option>
                          </select>
                        </label>
                        <button type="button" className="workspace-icon-button" aria-label={`Move ${item.title} up`} disabled={busy || index === 0} onClick={() => moveStep(index, -1)}><ArrowUp size={16} /></button>
                        <button type="button" className="workspace-icon-button" aria-label={`Move ${item.title} down`} disabled={busy || index === activeItems.length - 1} onClick={() => moveStep(index, 1)}><ArrowDown size={16} /></button>
                        <button type="button" className="button-secondary" disabled={busy} onClick={() => {
                          if (metadata.resourceUrl && !isHttpUrl(metadata.resourceUrl)) {
                            setError('Resource links must begin with http:// or https://.');
                            return;
                          }
                          if (item.description.length > 2000) {
                            setError('Shorten the description or resource link to fit the saved step limit.');
                            return;
                          }
                          void updateStep(item, { title: item.title, description: item.description, position: index });
                        }}><Save size={15} /> Save step</button>
                        <button type="button" className="workspace-icon-button" aria-label={`Delete ${item.title}`} disabled={busy} onClick={() => void deleteStep(item)}><Trash2 size={16} /></button>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ol>
            </>}
          </section>}

          {workspaceView === 'roadmaps' && <section className="workspace-data-section">
            <div className="section-intro"><div><span className="section-kicker">MY ROADMAPS</span><h2>One plan for each career goal.</h2><p>Each roadmap and its progress remain tied to its own goal.</p></div><button className="button-primary" onClick={() => onNavigate('Explore')}><Plus size={15} /> Generate a roadmap</button></div>
            {!roadmapCount && !loading ? <div className="workspace-empty workspace-empty-card"><Map size={24} /><h3>No roadmaps yet</h3><p>Create a career goal or generate a roadmap from an explored career.</p><button className="button-primary" onClick={() => setWorkspaceView('goals')}>Create a goal <ArrowRight size={15} /></button></div> : (
              <div className="workspace-roadmap-cards">
                {careerGoals.filter((goal) => (roadmaps[goal.id]?.length ?? 0) > 0).map((goal) => {
                  const items = roadmaps[goal.id] ?? [];
                  const completed = items.filter((item) => item.status === 'completed').length;
                  const percent = items.length ? Math.round(completed / items.length * 100) : 0;
                  return (
                    <article className="workspace-roadmap-card" key={goal.id}>
                      <div className="workspace-roadmap-card-top"><span className="hub-icon"><Map size={19} /></span><span className={`goal-status goal-status-${goal.status}`}>{goal.status}</span></div>
                      <span className="section-kicker">{goal.target_career}</span>
                      <h3>{goal.title}</h3>
                      <p>{items.length} steps · {completed} completed</p>
                      <div className="goal-progress-track" role="progressbar" aria-label={`${goal.title} roadmap progress`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}><span style={{ width: `${percent}%` }} /></div>
                      <div className="roadmap-card-progress-label"><span>{completed} of {items.length} steps complete</span><strong>{percent}%</strong></div>
                      {items.length > 0 && <p className="roadmap-card-next">{items.find((item) => item.status !== 'completed')?.title ?? 'All steps completed'}</p>}
                      <button className="button-secondary" onClick={() => openRoadmap(goal.id)}>View Roadmap <ArrowRight size={15} /></button>
                    </article>
                  );
                })}
              </div>
            )}
          </section>}

          {workspaceView === 'goals' && <section className="workspace-data-section" id="create-career-goal">
            <div className="section-intro"><div><span className="section-kicker">CREATE A GOAL</span><h2>Plan another career path.</h2></div></div>
            <form className="career-goal-form" onSubmit={(event) => { event.preventDefault(); void createGoal(); }}>
              <input value={title} maxLength={200} onChange={(event) => setTitle(event.target.value)} placeholder="Goal title" aria-label="Goal title" required />
              <input value={career} maxLength={100} onChange={(event) => setCareer(event.target.value)} placeholder="Target career" aria-label="Target career" required />
              <input value={description} maxLength={2000} onChange={(event) => setDescription(event.target.value)} placeholder="Description (optional)" aria-label="Goal description" />
              <label>Target date<input type="date" value={targetDate} onChange={(event) => setTargetDate(event.target.value)} /></label>
              <button className="button-primary" type="submit" disabled={busy}><Plus size={16} /> Create goal</button>
            </form>
          </section>}

          {workspaceView === 'recommendations' && <section className="workspace-data-section">
            <div className="section-intro"><div><span className="section-kicker">SAVED RECOMMENDATIONS</span><h2>Career ideas to revisit.</h2></div></div>
            {!recommendations.length && !loading ? <div className="workspace-empty workspace-empty-card"><BookOpen size={24} /><h3>No saved recommendations yet</h3><p>Explore careers and save the recommendations you want to revisit.</p><button className="button-primary" onClick={() => onNavigate('Explore')}>Explore Careers <ArrowRight size={15} /></button></div> : <div className="workspace-recommendations">{recommendations.map((item) => {
              const skillSuggestions = [
                ...new Set([
                  ...(item.results.skill_gap ?? []),
                  ...(item.results.recommended_skills ?? []),
                ]),
              ];
              const roles = displayValues(item.results.matching_roles);
              const certifications = (item.results.certifications ?? [])
                .map(resolveCertification)
                .filter((certification): certification is { name: string; url?: string } => Boolean(certification));
              return (
                <article className="result-card workspace-recommendation" key={item.id}>
                  <div className="result-card-heading">
                    <div><h3>{item.career}</h3><p>Skills selected: {item.selected_skills.join(', ') || 'None recorded'}</p><p>{skillSuggestions.length ? `Recommended skills: ${skillSuggestions.slice(0, 3).join(', ')}` : 'No additional skill suggestions were returned.'}</p></div>
                    <small>{new Date(item.created_at).toLocaleDateString()}</small>
                  </div>
                  <details className="workspace-result-details">
                    <summary>View Details</summary>
                    <div className="workspace-results-grid">
                      <section><h4>Skills to explore</h4>{skillSuggestions.length ? <ul>{skillSuggestions.map((skill) => <li key={skill}>{skill}</li>)}</ul> : <p>No skill suggestions were returned.</p>}</section>
                      <section><h4>Matching roles</h4>{roles.length ? <ul>{roles.map((role) => <li key={role}>{role}</li>)}</ul> : <p>No matching roles were returned.</p>}</section>
                      <section><h4>Certifications</h4>{certifications.length ? <ul>{certifications.map((certification) => <li key={certification.name}>{certification.url ? <a className="saved-certification-link" href={certification.url} target="_blank" rel="noopener noreferrer">{certification.name}</a> : certification.name}</li>)}</ul> : <p>No certifications were returned.</p>}</section>
                    </div>
                  </details>
                </article>
              );
            })}</div>}
          </section>}

          {workspaceView === 'goals' && <section className="workspace-data-section">
            <div className="section-intro"><div><span className="section-kicker">LEARNING GOALS</span><h2>Other saved learning intentions.</h2><p>These legacy standalone goals remain separate from career goals.</p></div></div>
            <form className="workspace-inline-form" onSubmit={(event) => void addLegacyGoal(event)}><input value={legacyGoalInput} maxLength={300} onChange={(event) => setLegacyGoalInput(event.target.value)} placeholder="Add a learning goal" aria-label="New learning goal" /><button className="button-primary" type="submit" disabled={busy}><Plus size={16} /> Add</button></form>
            {!legacyGoals.length && !loading ? <p className="workspace-empty">No standalone learning goals saved.</p> : <ul className="workspace-list">{legacyGoals.map((goal, index) => <li key={`${index}-${goal}`}><span>{goal}</span><button className="workspace-icon-button" aria-label={`Remove goal: ${goal}`} disabled={busy} onClick={() => void removeLegacyGoal(index)}><Trash2 size={16} /></button></li>)}</ul>}
          </section>}
          {workspaceView !== 'overview' && <p className="workspace-disclaimer">Goals and roadmaps are private to your account. Roadmap completion measures saved task progress, not guaranteed career readiness.</p>}
        </section>
      </main>
    </div>
  );
}
