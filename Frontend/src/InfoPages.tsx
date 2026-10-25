import {
  ArrowDown,
  ArrowRight,
  BookOpen,
  BrainCircuit,
  CheckCircle2,
  Compass,
  GraduationCap,
  LockKeyhole,
  Sparkles,
  Target,
  UserRound,
} from 'lucide-react';
import { useEffect, useRef, useState } from 'react';

const aboutFeatures = [
  {
    icon: Compass,
    title: 'Start with a career interest',
    description:
      'Choose a role you are curious about. It gives the explorer a direction for comparing your current skills with the skills associated with that career.',
  },
  {
    icon: BrainCircuit,
    title: 'Bring the skills you already have',
    description:
      'Select the skills you know, then get personalized suggestions from the existing SmartSkillPath recommendation model for the career you selected.',
  },
  {
    icon: GraduationCap,
    title: 'Explore skills and certifications',
    description:
      'Review skills to explore next and browse curated learning and certification options with links to their providers and cost guidance.',
  },
  {
    icon: Target,
    title: 'Give your learning a direction',
    description:
      'Use the suggested skills and resources to decide what you want to learn next, at a pace and in an order that works for you.',
  },
  {
    icon: BookOpen,
    title: 'Keep your journey organized',
    description:
      'The signed-in My Space view brings personal goals, saved recommendations, and progress overview into one place. These are marked as personal features in this demo; persistent saving is not yet connected.',
  },
  {
    icon: LockKeyhole,
    title: 'Choose guest or signed-in access',
    description:
      'Guests can explore careers, request recommendations, and browse learning resources. Sign in to open My Space and see its personal learning features; guest results are temporary and are not saved.',
  },
];

const steps = [
  {
    icon: Compass,
    title: 'Choose a Career Interest',
    description: 'Pick a career you would like to explore.',
  },
  {
    icon: CheckCircle2,
    title: 'Select Existing Skills',
    description: 'Select the skills you already have.',
  },
  {
    icon: BrainCircuit,
    title: 'Analyze Your Skills',
    description: 'Compare your selected skills with your career interest.',
  },
  {
    icon: GraduationCap,
    title: 'Explore Personalized Recommendations',
    description: 'Review skill suggestions returned by the recommendation model.',
  },
  {
    icon: UserRound,
    title: 'Set Learning Goals',
    description: 'Choose a next step for your own learning journey.',
  },
  {
    icon: Target,
    title: 'Track Your Progress',
    description: 'Keep your learning intentions and milestones in view.',
  },
];

export function AboutPage() {
  return (
    <section className="inner-page info-page">
      <div className="inner-hero">
        <span className="eyebrow">
          <Sparkles size={16} /> ABOUT SMARTSKILLPATH
        </span>
        <h1>
          A clearer way to plan
          <br />
          <span className="gradient-text">your learning journey.</span>
        </h1>
        <p>
          SmartSkillPath is a career discovery and learning guidance platform.
          It connects a career you are interested in with the skills you already
          have, suggested skills to explore, and learning resources to help you
          decide what comes next.
        </p>
      </div>

      <section className="about-purpose">
        <div className="about-purpose-icon">
          <BrainCircuit size={28} />
        </div>
        <div>
          <span className="section-kicker">WHY IT WAS DEVELOPED</span>
          <h2>Turn a big career question into manageable next steps.</h2>
          <p>
            Exploring a new career can feel scattered: it is hard to know which
            skills matter, how your experience fits, or where to begin learning.
            SmartSkillPath brings those pieces together in one guided flow so
            learners can compare their current skills with a role, review
            recommendations, and research learning options without needing an
            account to get started.
          </p>
        </div>
      </section>

      <div className="section-intro info-section-heading">
        <div>
          <span className="section-kicker">FROM INTEREST TO ACTION</span>
          <h2>One place to organize your next steps.</h2>
        </div>
      </div>
      <div className="about-feature-grid">
        {aboutFeatures.map(({ icon: Icon, title, description }, index) => (
          <article className="about-feature-card" key={title}>
            <span className="about-feature-icon">
              <Icon size={25} />
            </span>
            <span className="about-feature-number">
              {String(index + 1).padStart(2, '0')}
            </span>
            <h3>{title}</h3>
            <p>{description}</p>
          </article>
        ))}
      </div>

      <section className="about-access">
        <div>
          <span className="section-kicker">ACCESS THAT FITS YOUR STAGE</span>
          <h2>Explore first. Sign in when you want a personal space.</h2>
        </div>
        <div className="about-access-options">
          <article>
            <span className="about-feature-icon">
              <Compass size={24} />
            </span>
            <h3>As a guest</h3>
            <p>
              Choose a career, select current skills, get recommendations, and
              browse learning options. Recommendations are temporary and are
              not saved.
            </p>
          </article>
          <article>
            <span className="about-feature-icon">
              <UserRound size={24} />
            </span>
            <h3>When signed in</h3>
            <p>
              Open My Space to see personal goals, saved recommendations, and a
              progress overview. These personal features are presented in the
              current demo, while persistent saving is not yet connected.
            </p>
          </article>
        </div>
      </section>

      <div className="about-cta">
        <p>
          SmartSkillPath is a guide for organizing exploration—not a guarantee
          of employment or a substitute for researching a career and its
          learning providers.
        </p>
      </div>
    </section>
  );
}

export function HowItWorksPage() {
  const [activeStep, setActiveStep] = useState(0);
  const [paused, setPaused] = useState(false);
  const [reduceMotion, setReduceMotion] = useState(false);
  const resumeTimer = useRef<number | undefined>(undefined);
  const isHovering = useRef(false);
  const isFocused = useRef(false);

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const updateMotionPreference = () => setReduceMotion(mediaQuery.matches);
    updateMotionPreference();
    mediaQuery.addEventListener('change', updateMotionPreference);
    return () => {
      mediaQuery.removeEventListener('change', updateMotionPreference);
      window.clearTimeout(resumeTimer.current);
    };
  }, []);

  useEffect(() => {
    if (paused || reduceMotion) return;
    const interval = window.setInterval(
      () => setActiveStep((step) => (step + 1) % steps.length),
      3200,
    );
    return () => window.clearInterval(interval);
  }, [paused, reduceMotion]);

  const selectStep = (index: number) => {
    setActiveStep(index);
    setPaused(true);
    window.clearTimeout(resumeTimer.current);
    resumeTimer.current = window.setTimeout(() => {
      if (!isHovering.current && !isFocused.current) setPaused(false);
    }, 5000);
  };

  return (
    <section className="inner-page info-page how-page">
      <div className="inner-hero">
        <span className="eyebrow">
          <Sparkles size={16} /> HOW IT WORKS
        </span>
        <h1>
          From career curiosity
          <br />
          <span className="gradient-text">to a learning plan.</span>
        </h1>
        <p>
          Follow the path from a career interest to personalized suggestions
          and organized next steps. Explore recommendations as a guest, then
          sign in to open personal features.
        </p>
      </div>

      <div className="how-progress" aria-live="polite">
        <span>Step {activeStep + 1} of {steps.length}</span>
        <span className="how-progress-track" aria-hidden="true">
          <span style={{ width: `${((activeStep + 1) / steps.length) * 100}%` }} />
        </span>
        <span>{steps[activeStep].title}</span>
      </div>

      <div
        className="how-flow"
        aria-label="Six steps to use SmartSkillPath"
        onMouseEnter={() => {
          isHovering.current = true;
          setPaused(true);
        }}
        onMouseLeave={() => {
          isHovering.current = false;
          if (!isFocused.current) setPaused(false);
        }}
        onFocusCapture={() => {
          isFocused.current = true;
          setPaused(true);
        }}
        onBlurCapture={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget as Node | null)) {
            isFocused.current = false;
            if (!isHovering.current) setPaused(false);
          }
        }}
      >
        {steps.map(({ icon: Icon, title, description }, index) => (
          <div className="how-flow-item" key={title}>
            <button
              type="button"
              className={`how-step${activeStep === index ? ' is-active' : ''}`}
              aria-pressed={activeStep === index}
              onClick={() => selectStep(index)}
            >
              <span className="how-step-number">
                {String(index + 1).padStart(2, '0')}
              </span>
              <span className="how-step-icon">
                <Icon size={34} strokeWidth={1.8} />
              </span>
              <h2>{title}</h2>
              <p>{description}</p>
            </button>
            {index < steps.length - 1 && (
              <span className="how-connector" aria-hidden="true">
                <ArrowRight size={20} />
                <ArrowDown size={20} />
              </span>
            )}
            {index === steps.length - 1 && (
              <span className="how-connector how-loop-connector" aria-hidden="true">
                <ArrowRight size={20} />
              </span>
            )}
          </div>
        ))}
      </div>

      <div className="how-note">
        <LockKeyhole size={19} />
        <p>
          Guest recommendations are not saved. My Space displays personal
          learning features for signed-in users; persistent saving is not yet
          connected in this demo.
        </p>
      </div>
    </section>
  );
}
