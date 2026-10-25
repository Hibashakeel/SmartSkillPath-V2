import { useEffect, useRef, useState, type KeyboardEvent as ReactKeyboardEvent } from 'react';
import { ArrowUpRight, ChevronDown, Contrast, LogOut, Menu, Settings, UserRound, UsersRound, X } from 'lucide-react';

export type AppPage =
  | 'Home'
  | 'About'
  | 'How It Works'
  | 'Explore'
  | 'Certifications'
  | 'My Space';

type Props = {
  activePage: AppPage;
  userEmail: string | null;
  onNavigate: (page: AppPage) => void;
  onLogin?: () => void;
  onRegister?: () => void;
  onOpenProfile: () => void;
  onOpenSettings: () => void;
  onOpenAccessibility: () => void;
  onSwitchAccount: () => void;
  onLogout: () => void;
};

const pages: AppPage[] = [
  'Home',
  'About',
  'How It Works',
  'Explore',
  'Certifications',
  'My Space',
];

export default function AppNavbar({
  activePage,
  userEmail,
  onNavigate,
  onLogin = () => {},
  onRegister = () => {},
  onOpenProfile,
  onOpenSettings,
  onOpenAccessibility,
  onSwitchAccount,
  onLogout,
}: Props) {
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const profileRef = useRef<HTMLDivElement>(null);
  const profileTriggerRef = useRef<HTMLButtonElement>(null);
  const firstMenuActionRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (profileOpen) firstMenuActionRef.current?.focus();
  }, [profileOpen]);

  useEffect(() => {
    if (!profileOpen) return;
    const closeOnOutsidePointer = (event: PointerEvent) => {
      if (event.target instanceof Node && !profileRef.current?.contains(event.target)) {
        setProfileOpen(false);
      }
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setProfileOpen(false);
        profileTriggerRef.current?.focus();
      }
    };
    document.addEventListener('pointerdown', closeOnOutsidePointer);
    document.addEventListener('keydown', closeOnEscape);
    return () => {
      document.removeEventListener('pointerdown', closeOnOutsidePointer);
      document.removeEventListener('keydown', closeOnEscape);
    };
  }, [profileOpen]);

  function navigate(page: AppPage) {
    onNavigate(page);
    setMobileOpen(false);
  }

  function runProfileAction(action: () => void) {
    setProfileOpen(false);
    action();
  }

  function moveMenuFocus(event: ReactKeyboardEvent<HTMLDivElement>) {
    const actions = Array.from(
      event.currentTarget.querySelectorAll<HTMLButtonElement>('[role="menuitem"]'),
    );
    const current = actions.indexOf(document.activeElement as HTMLButtonElement);
    let next = -1;
    if (event.key === 'ArrowDown') next = (current + 1) % actions.length;
    if (event.key === 'ArrowUp') next = (current - 1 + actions.length) % actions.length;
    if (event.key === 'Home') next = 0;
    if (event.key === 'End') next = actions.length - 1;
    if (next >= 0) {
      event.preventDefault();
      actions[next]?.focus();
    }
  }

  return (
    <header className="navbar">
      <button
        className="brand"
        onClick={() => navigate('Home')}
        aria-label="SmartSkillPath home"
      >
        <span className="brand-symbol"><span /><span /></span>
        <span className="brand-name">
          SmartSkill<span>Path</span>
          <small>CAREER DISCOVERY PLATFORM</small>
        </span>
      </button>
      <nav className={mobileOpen ? 'nav-items nav-open' : 'nav-items'} aria-label="Main navigation">
        {pages.map((page) => (
          <button
            key={page}
            className={activePage === page ? 'nav-current' : ''}
            aria-current={activePage === page ? 'page' : undefined}
            onClick={() => navigate(page)}
          >
            {page}
            {page === 'Explore' && <span className="nav-live" />}
          </button>
        ))}
        {!userEmail && (
          <>
            <button className="mobile-auth-link" onClick={() => { onLogin(); setMobileOpen(false); }}>Login</button>
            <button className="mobile-auth-link" onClick={() => { onRegister(); setMobileOpen(false); }}>Register</button>
          </>
        )}
      </nav>
      <div className="nav-actions">
        {userEmail ? (
          <div className="profile-menu" ref={profileRef}>
            <button
              ref={profileTriggerRef}
              className="account-chip"
              type="button"
              aria-haspopup="menu"
              aria-expanded={profileOpen}
              aria-controls="profile-menu-panel"
              onClick={() => setProfileOpen((open) => !open)}
            >
              <span className="profile-avatar"><UserRound size={16} /></span>
              <span className="profile-account-label">{userEmail}</span>
              <ChevronDown className={profileOpen ? 'profile-chevron is-open' : 'profile-chevron'} size={14} />
            </button>
            {profileOpen && (
              <div
                className="profile-menu-panel"
                id="profile-menu-panel"
                role="menu"
                aria-label="Account menu"
                onKeyDown={moveMenuFocus}
              >
                <div className="profile-menu-identity">
                  <span className="profile-avatar profile-avatar-large"><UserRound size={19} /></span>
                  <span><small>Signed in as</small><strong>{userEmail}</strong></span>
                </div>
                <div className="profile-menu-section">
                  <span className="profile-menu-heading">Account</span>
                  <button ref={firstMenuActionRef} role="menuitem" onClick={() => runProfileAction(onOpenProfile)}><UserRound size={16} /> My Profile</button>
                  <button role="menuitem" onClick={() => runProfileAction(onSwitchAccount)}><UsersRound size={16} /> Switch Account</button>
                </div>
                <div className="profile-menu-section">
                  <span className="profile-menu-heading">Preferences</span>
                  <button role="menuitem" onClick={() => runProfileAction(onOpenSettings)}><Settings size={16} /> Settings</button>
                  <button role="menuitem" onClick={() => runProfileAction(onOpenAccessibility)}><Contrast size={16} /> Accessibility</button>
                </div>
                <div className="profile-menu-section profile-menu-session">
                  <span className="profile-menu-heading">Session</span>
                  <button className="profile-logout" role="menuitem" onClick={() => runProfileAction(onLogout)}><LogOut size={16} /> Logout</button>
                </div>
              </div>
            )}
          </div>
        ) : (
          <>
            <button className="nav-login" onClick={onLogin}>Login</button>
            <button className="nav-cta" onClick={onRegister}>
              Register <ArrowUpRight size={16} />
            </button>
          </>
        )}
        <button
          className="mobile-menu"
          onClick={() => setMobileOpen((open) => !open)}
          aria-label={mobileOpen ? 'Close navigation menu' : 'Open navigation menu'}
          aria-expanded={mobileOpen}
        >
          {mobileOpen ? <X /> : <Menu />}
        </button>
      </div>
    </header>
  );
}
