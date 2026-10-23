export function PrivacyNotice({ variant }: { variant: string | null }) {
  return (
    <footer style={{ textAlign: 'center', marginTop: 24, paddingBottom: 16 }}>
      <p style={{ fontSize: '0.75rem', color: '#888', marginBottom: 4 }}>
        🔒 This demo does not ask for name, email, or phone. Please do not enter personal information.
        Location is approximate only. Anonymous session.
      </p>
      <p style={{ fontSize: '0.7rem', color: '#aaa' }}>
        Airify Platform V1 — Mock Data Only — Variant: {variant || 'loading'}
      </p>
    </footer>
  );
}
