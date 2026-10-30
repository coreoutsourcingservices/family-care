import { useEffect, useState } from 'react';
import type { ImageKind } from '../onboarding/uploadImage';

export default function SetupImageField({ kind, label, file, savedUrl, onChange }: {
  kind: ImageKind; label: string; file?: File; savedUrl?: string;
  onChange: (kind: ImageKind, file?: File) => void;
}) {
  const [preview, setPreview] = useState('');
  const [error, setError] = useState('');
  useEffect(() => {
    if (!file) { setPreview(''); return; }
    const url = URL.createObjectURL(file); setPreview(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);
  return <label className="doctor-setup-image-field">{label} <small>Optional</small>
    {(preview || savedUrl) && <img src={preview || savedUrl} alt={`${label} preview`} />}
    <input type="file" name={kind} accept="image/jpeg,image/png,image/webp" onChange={event => {
      const selected = event.target.files?.[0];
      if (selected && (!['image/jpeg', 'image/png', 'image/webp'].includes(selected.type) || selected.size === 0 || selected.size > 5 * 1024 * 1024)) {
        setError('Choose a JPEG, PNG or WebP image up to 5 MB.'); event.target.value = ''; onChange(kind, undefined); return;
      }
      setError(''); onChange(kind, selected);
    }} />
    <small>JPEG, PNG or WebP · up to 5 MB</small>
    {savedUrl && !file && <small>Previously uploaded image saved.</small>}
    {error && <span role="alert" className="doctor-setup-error">{error}</span>}
  </label>;
}
