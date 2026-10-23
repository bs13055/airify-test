/** "Try Airify Health App" CTA — honest availability.
 *
 * Reads public URLs from Vite env vars. When a URL is empty, the button renders as a
 * disabled "Coming soon" / "Join beta" state — it NEVER fakes App Store / Play Store
 * availability. This is a demo; there is no published mobile app.
 */

const HEALTH_APP_URL = import.meta.env.VITE_HEALTH_APP_URL ?? '';
const APP_STORE_URL = import.meta.env.VITE_APP_STORE_URL ?? '';
const PLAY_STORE_URL = import.meta.env.VITE_PLAY_STORE_URL ?? '';

interface CtaItem { label: string; comingSoonLabel: string; url: string; icon: string }

const ITEMS: CtaItem[] = [
  { label: 'Open Web App', comingSoonLabel: 'Web App — coming soon', url: HEALTH_APP_URL, icon: '🌐' },
  { label: 'Download on the App Store', comingSoonLabel: 'App Store — coming soon', url: APP_STORE_URL, icon: '' },
  { label: 'Get it on Google Play', comingSoonLabel: 'Google Play — coming soon', url: PLAY_STORE_URL, icon: '▶' },
];

interface Props {
  title?: string;
  variant?: 'light' | 'onDark';
}

export function AppStoreCTA({ title = 'Try Airify Health App', variant = 'light' }: Props) {
  const anyAvailable = ITEMS.some(i => i.url);
  return (
    <div className={`app-cta ${variant === 'onDark' ? 'app-cta-on-dark' : ''}`}>
      <div className="app-cta-title">{title}</div>
      <div className="app-cta-row">
        {ITEMS.map(item =>
          item.url ? (
            <a key={item.label} className="app-cta-btn" href={item.url} target="_blank" rel="noopener noreferrer">
              {item.icon && <span aria-hidden="true">{item.icon}</span>} {item.label}
            </a>
          ) : (
            <span key={item.label} className="app-cta-btn app-cta-disabled" aria-disabled="true" title="Not published yet">
              {item.icon && <span aria-hidden="true">{item.icon}</span>} {item.comingSoonLabel}
            </span>
          ),
        )}
      </div>
      {!anyAvailable && (
        <div className="app-cta-note">Not published yet — join the beta waitlist. This is a demo; no store release exists.</div>
      )}
    </div>
  );
}
