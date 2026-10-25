import { ArrowDown, ArrowUp, Plus, Save, X } from 'lucide-react';
import {
  isHttpUrl,
  roadmapStepTypes,
  type CareerRoadmapDraftStep,
} from './roadmapMetadata';

type Props = {
  career: string;
  title: string;
  targetCareer: string;
  description: string;
  targetDate: string;
  steps: CareerRoadmapDraftStep[];
  editing: boolean;
  saving: boolean;
  canSave: boolean;
  skillOptions: string[];
  onGoalChange: (field: 'title' | 'career' | 'description' | 'targetDate', value: string) => void;
  onStepChange: (index: number, changes: Partial<CareerRoadmapDraftStep>) => void;
  onMove: (index: number, direction: -1 | 1) => void;
  onAdd: () => void;
  onRemove: (index: number) => void;
  onEdit: () => void;
  onSave: () => void;
  onSignIn: () => void;
  onDiscard: () => void;
};

export default function RoadmapDraftPanel({
  career,
  title,
  targetCareer,
  description,
  targetDate,
  steps,
  editing,
  saving,
  canSave,
  skillOptions,
  onGoalChange,
  onStepChange,
  onMove,
  onAdd,
  onRemove,
  onEdit,
  onSave,
  onSignIn,
  onDiscard,
}: Props) {
  const canSubmit = steps.length > 0 && steps.every(
    (step) => step.title.trim() && step.phase.trim(),
  );

  return (
    <section className="roadmap-draft-panel" id="roadmap-draft" aria-labelledby="roadmap-draft-title">
      <div className="section-intro">
        <div>
          <span className="section-kicker">REVIEW BEFORE SAVING</span>
          <h2 id="roadmap-draft-title">Your {career} roadmap draft.</h2>
          <p>Skill gaps use returned recommendations and the available career skill checklist. Practice, project, portfolio, and preparation stages are rule-based draft suggestions. Review them before saving.</p>
        </div>
        <button type="button" className="text-action" onClick={onDiscard}>Discard draft</button>
      </div>

      <div className="career-goal-form">
        <label>Goal title<input value={title} maxLength={200} disabled={!editing} onChange={(event) => onGoalChange('title', event.target.value)} /></label>
        <label>Target career<input value={targetCareer} maxLength={100} disabled={!editing} onChange={(event) => onGoalChange('career', event.target.value)} /></label>
        <label>Description<input value={description} maxLength={2000} disabled={!editing} placeholder="Optional" onChange={(event) => onGoalChange('description', event.target.value)} /></label>
        <label>Target date<input type="date" value={targetDate} disabled={!editing} onChange={(event) => onGoalChange('targetDate', event.target.value)} /></label>
      </div>

      <ol className="draft-roadmap-list roadmap-timeline" aria-label={`${career} draft roadmap`}>
        {steps.map((step, index) => (
          <li className="draft-roadmap-item roadmap-timeline-step" key={`${index}-${step.title}`}>
            <span className="roadmap-step-marker" aria-hidden="true">{index + 1}</span>
            {editing ? (
              <div className="draft-roadmap-fields">
                <label>Step title<input value={step.title} maxLength={200} onChange={(event) => onStepChange(index, { title: event.target.value })} placeholder="Roadmap step title" /></label>
                <label>Description<textarea value={step.description} maxLength={1100} rows={2} onChange={(event) => onStepChange(index, { description: event.target.value })} /></label>
                <label>Phase<input value={step.phase} maxLength={80} onChange={(event) => onStepChange(index, { phase: event.target.value })} /></label>
                <label>Step type<select value={step.stepType} onChange={(event) => onStepChange(index, { stepType: event.target.value as CareerRoadmapDraftStep['stepType'] })}>{roadmapStepTypes.map((type) => <option key={type}>{type}</option>)}</select></label>
                <label>Skill or category<select value={step.category} onChange={(event) => onStepChange(index, { category: event.target.value })}><option value="">General / not specified</option>{skillOptions.map((skill) => <option key={skill}>{skill}</option>)}{step.category && !skillOptions.includes(step.category) && <option value={step.category}>{step.category}</option>}</select></label>
                <label>Priority<select value={step.priority} onChange={(event) => onStepChange(index, { priority: event.target.value as CareerRoadmapDraftStep['priority'] })}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></label>
                <label>Status<select value={step.status} onChange={(event) => onStepChange(index, { status: event.target.value as CareerRoadmapDraftStep['status'] })}><option value="not_started">Not Started</option><option value="in_progress">In Progress</option><option value="completed">Completed</option></select></label>
                <label>Resource link<input type="url" maxLength={500} value={step.resourceUrl} placeholder="https://…" onChange={(event) => onStepChange(index, { resourceUrl: event.target.value })} /></label>
                <div className="draft-step-actions">
                  <button type="button" className="workspace-icon-button" aria-label={`Move ${step.title || 'step'} up`} disabled={index === 0} onClick={() => onMove(index, -1)}><ArrowUp size={16} /></button>
                  <button type="button" className="workspace-icon-button" aria-label={`Move ${step.title || 'step'} down`} disabled={index === steps.length - 1} onClick={() => onMove(index, 1)}><ArrowDown size={16} /></button>
                  <button type="button" className="workspace-icon-button" aria-label={`Remove ${step.title || 'step'}`} onClick={() => onRemove(index)}><X size={15} /></button>
                </div>
              </div>
            ) : (
              <article className="roadmap-draft-card">
                <div className="roadmap-item-meta">
                  <span>{step.phase}</span><span>{step.stepType}</span>
                  <span className={`priority-${step.priority}`}>{step.priority} priority</span>
                  <span className="step-status-badge">{step.status === 'not_started' ? 'Not Started' : step.status === 'in_progress' ? 'In Progress' : 'Completed'}</span>
                </div>
                <h3>{step.title}</h3>
                <p>{step.description || 'No description provided.'}</p>
                {step.category && <small>Skill or category: {step.category}</small>}
                {isHttpUrl(step.resourceUrl)
                  ? <a className="roadmap-resource-link" href={step.resourceUrl} target="_blank" rel="noreferrer">Open resource</a>
                  : step.resourceUrl && <small>Resource link is not a valid http(s) address.</small>}
              </article>
            )}
          </li>
        ))}
      </ol>

      <div className="draft-roadmap-footer">
        {editing && <button className="button-secondary" type="button" onClick={onAdd}><Plus size={15} /> Add a manual step</button>}
        <button className="button-secondary" type="button" onClick={() => document.getElementById('roadmap-draft')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}>View Roadmap</button>
        <button className="button-secondary" type="button" onClick={onEdit}>{editing ? 'Preview Roadmap' : 'Edit Roadmap'}</button>
        <button className="button-primary" type="button" disabled={saving || !canSubmit} onClick={canSave ? onSave : onSignIn}>
          <Save size={15} />{saving ? 'Saving…' : canSave ? 'Save to My Space' : 'Sign in to save'}
        </button>
      </div>
    </section>
  );
}
