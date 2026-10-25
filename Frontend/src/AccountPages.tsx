import { ArrowLeft, Check, Contrast, Type, UserRound, Wind } from 'lucide-react';
import type { ReactNode } from 'react';
import type { UiPreferences } from './accountPreferences';

type Props = {
  userEmail: string;
  preferences: UiPreferences;
  onPreferenceChange: (preferences: UiPreferences) => void;
  onBack: () => void;
};

type ToggleProps = {
  checked: boolean;
  label: string;
  description: string;
  onChange: (checked: boolean) => void;
};

function PreferenceToggle({ checked, label, description, onChange }: ToggleProps) {
  return (
    <label className="preference-toggle-row">
      <span className="preference-toggle-copy">
        <strong>{label}</strong>
        <small>{description}</small>
      </span>
      <input
        type="checkbox"
        role="switch"
        aria-label={label}
        checked={checked}
        onChange={(event) => onChange(event.target.checked)}
      />
    </label>
  );
}

function AccountPageFrame({
  eyebrow,
  title,
  description,
  onBack,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  onBack: () => void;
  children: ReactNode;
}) {
  return (
    <section className="inner-page account-preferences-page">
      <button className="text-action account-page-back" onClick={onBack}>
        <ArrowLeft size={16} /> Back to My Space
      </button>
      <header className="workspace-hero">
        <div>
          <span className="eyebrow"><UserRound size={14} /> {eyebrow}</span>
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
      </header>
      {children}
    </section>
  );
}

export function MyProfilePage({ userEmail, onBack }: Pick<Props, 'userEmail' | 'onBack'>) {
  return (
    <AccountPageFrame
      eyebrow="ACCOUNT"
      title="My Profile"
      description="Account information currently available from your sign-in."
      onBack={onBack}
    >
      <section className="account-info-card" aria-label="Profile information">
        <span className="account-profile-avatar"><UserRound size={24} /></span>
        <div>
          <span className="section-kicker">EMAIL ADDRESS</span>
          <h2>{userEmail}</h2>
          <p>Your current account system provides an email address only. Name and profile editing are not available.</p>
        </div>
      </section>
    </AccountPageFrame>
  );
}

export function SettingsPage({ preferences, onPreferenceChange, onBack }: Omit<Props, 'userEmail'>) {
  return (
    <AccountPageFrame
      eyebrow="PREFERENCES"
      title="Settings"
      description="Choose how SmartSkillPath behaves on this device."
      onBack={onBack}
    >
      <section className="account-settings-card">
        <div className="account-setting-heading"><Wind size={19} /><div><h2>Motion</h2><p>Keep movement comfortable while navigating the app.</p></div></div>
        <PreferenceToggle
          checked={preferences.reduceMotion}
          label="Reduce animations"
          description="Minimize nonessential transitions and motion effects."
          onChange={(reduceMotion) => onPreferenceChange({ ...preferences, reduceMotion })}
        />
        <p className="preference-note">This is the same Reduce Motion preference available in Accessibility. Your operating system’s reduced-motion setting is also respected.</p>
      </section>
    </AccountPageFrame>
  );
}

export function AccessibilityPage({ preferences, onPreferenceChange, onBack }: Omit<Props, 'userEmail'>) {
  return (
    <AccountPageFrame
      eyebrow="ACCESSIBILITY"
      title="Accessibility"
      description="Adjust display and motion preferences across the application."
      onBack={onBack}
    >
      <section className="account-settings-card">
        <div className="account-setting-heading"><Wind size={19} /><div><h2>Motion</h2><p>Reduce movement throughout SmartSkillPath.</p></div></div>
        <PreferenceToggle
          checked={preferences.reduceMotion}
          label="Reduce Motion"
          description="Disable or minimize nonessential animations and transitions."
          onChange={(reduceMotion) => onPreferenceChange({ ...preferences, reduceMotion })}
        />
      </section>
      <section className="account-settings-card">
        <div className="account-setting-heading"><Type size={19} /><div><h2>Text Size</h2><p>Choose a comfortable reading size.</p></div></div>
        <fieldset className="preference-radio-group">
          <legend>Text Size</legend>
          {(['normal', 'large'] as const).map((textSize) => (
            <label key={textSize} className="preference-radio-option">
              <input
                type="radio"
                name="text-size"
                value={textSize}
                checked={preferences.textSize === textSize}
                onChange={() => onPreferenceChange({ ...preferences, textSize })}
              />
              <span>{textSize === 'normal' ? 'Normal' : 'Large'}</span>
            </label>
          ))}
        </fieldset>
      </section>
      <section className="account-settings-card">
        <div className="account-setting-heading"><Contrast size={19} /><div><h2>Contrast</h2><p>Increase contrast for text, controls, borders, and focus indicators.</p></div></div>
        <PreferenceToggle
          checked={preferences.highContrast}
          label="High Contrast"
          description="Use brighter text, clearer borders, and stronger keyboard focus."
          onChange={(highContrast) => onPreferenceChange({ ...preferences, highContrast })}
        />
      </section>
      <p className="preference-save-state" role="status"><Check size={15} /> Preferences save automatically on this device.</p>
    </AccountPageFrame>
  );
}
