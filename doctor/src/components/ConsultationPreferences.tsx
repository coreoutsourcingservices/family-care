import { useEffect, useState } from "react";
import { careApi } from "../../../app/src/lib/careApi";
export type ConsultationOptions = {
  physical_enabled: boolean;
  video_enabled: boolean;
  physical_fee_paise: number | null;
  video_fee_paise: number | null;
};
export const defaultConsultationOptions: ConsultationOptions = {
  physical_enabled: true,
  video_enabled: false,
  physical_fee_paise: null,
  video_fee_paise: null,
};
export function ConsultationModeFields({
  value,
  onChange,
  disabled = false,
}: {
  value: ConsultationOptions;
  onChange: (value: ConsultationOptions) => void;
  disabled?: boolean;
}) {
  return (
    <fieldset
      disabled={disabled}
      style={{ border: 0, padding: 0, minWidth: 0 }}
    >
      <legend>Consultation modes & fees</legend>
      <p>
        Only enabled modes appear to patients. Set a fee in INR for every mode
        you offer.
      </p>
      {(["physical", "video"] as const).map((mode) => (
        <div
          key={mode}
          style={{
            padding: "14px",
            margin: "12px 0",
            border: "1px solid #d8e2f0",
            borderRadius: 14,
            background: mode === "physical" ? "#edf9f5" : "#f2efff",
          }}
        >
          <label style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <input
              type="checkbox"
              style={{ width: "auto" }}
              checked={value[`${mode}_enabled`]}
              onChange={(e) =>
                onChange({ ...value, [`${mode}_enabled`]: e.target.checked })
              }
            />
            {mode === "physical"
              ? "In-person consultation"
              : "Video consultation"}
          </label>
          {value[`${mode}_enabled`] && (
            <label>
              Consultation fee (INR)
              <input
                aria-label={`${mode} consultation fee`}
                type="number"
                min="0"
                max="1000000"
                step="0.01"
                required
                value={
                  value[`${mode}_fee_paise`] == null
                    ? ""
                    : value[`${mode}_fee_paise`]! / 100
                }
                onChange={(e) =>
                  onChange({
                    ...value,
                    [`${mode}_fee_paise`]:
                      e.target.value === ""
                        ? null
                        : Math.round(Number(e.target.value) * 100),
                  })
                }
              />
            </label>
          )}
        </div>
      ))}
      {!value.physical_enabled && !value.video_enabled && (
        <p role="alert">Enable at least one consultation mode.</p>
      )}
    </fieldset>
  );
}
export default function ConsultationPreferences() {
  const [value, setValue] = useState(defaultConsultationOptions),
    [loading, setLoading] = useState(true),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [ids, setIds] = useState({ referral_id: "", doctor_id: "" });
  useEffect(() => {
    let active = true;
    careApi<{
      consultation_options: ConsultationOptions;
      referral_id: string;
      doctor_id: string;
    }>("/doctors/consultation-settings")
      .then((data) => {
        if (active) {
          setValue(data.consultation_options);
          setIds(data);
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);
  return (
    <form
      className="dw-panel dw-form"
      onSubmit={async (e) => {
        e.preventDefault();
        if (busy) return;
        setBusy(true);
        setError("");
        setNotice("");
        try {
          await careApi("/doctors/consultation-settings", value, true, "PUT");
          setNotice("Consultation modes and fees saved.");
        } catch (e) {
          setError((e as Error).message);
        } finally {
          setBusy(false);
        }
      }}
    >
      <h2>Consultation preferences</h2>
      <dl className="dw-detail-list">
        <div>
          <dt>Doctor ID</dt>
          <dd>{ids.doctor_id || "Not set"}</dd>
        </div>
        <div>
          <dt>Referral ID</dt>
          <dd style={{ overflowWrap: "anywhere" }}>
            {ids.referral_id || "Not set"}
          </dd>
        </div>
      </dl>
      {loading ? (
        <p role="status">Loading consultation preferences...</p>
      ) : (
        <ConsultationModeFields
          value={value}
          onChange={setValue}
          disabled={busy}
        />
      )}
      <p>
        Appointment time windows and patient capacity are managed in
        Appointments.
      </p>
      {error && (
        <p role="alert" className="dw-error">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      <button
        className="dw-primary"
        disabled={
          loading || busy || (!value.physical_enabled && !value.video_enabled)
        }
      >
        {busy ? "Saving..." : "Save consultation preferences"}
      </button>
    </form>
  );
}
