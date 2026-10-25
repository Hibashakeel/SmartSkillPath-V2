export type UiPreferences = {
  reduceMotion: boolean;
  textSize: 'normal' | 'large';
  highContrast: boolean;
};

export const defaultUiPreferences: UiPreferences = {
  reduceMotion: false,
  textSize: 'normal',
  highContrast: false,
};

const storageKey = 'ssp_ui_preferences';

export function loadUiPreferences(): UiPreferences {
  try {
    const value: unknown = JSON.parse(localStorage.getItem(storageKey) || 'null');
    if (!value || typeof value !== 'object') return defaultUiPreferences;
    const stored = value as Partial<UiPreferences>;
    return {
      reduceMotion: stored.reduceMotion === true,
      textSize: stored.textSize === 'large' ? 'large' : 'normal',
      highContrast: stored.highContrast === true,
    };
  } catch {
    return defaultUiPreferences;
  }
}

export function saveUiPreferences(preferences: UiPreferences): void {
  try {
    localStorage.setItem(storageKey, JSON.stringify(preferences));
  } catch {
    throw new Error('Could not save your display preferences in this browser.');
  }
}
