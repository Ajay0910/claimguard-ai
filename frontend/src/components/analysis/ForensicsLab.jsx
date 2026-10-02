import React from 'react';

const titleCase = (value) => String(value || '').replaceAll('_', ' ').toLowerCase().replace(/\b\w/g, (letter) => letter.toUpperCase());

function FindingsList({ title, items, descriptionFor }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h3 className="font-semibold text-slate-900">{title}</h3>
      {!items?.length ? (
        <p className="mt-2 text-sm text-slate-500">No findings were returned for this check.</p>
      ) : (
        <ul className="mt-3 space-y-3">
          {items.map((item, index) => (
            <li key={`${item.issue_type || item.anomaly_type || item.flag_type || title}-${index}`} className="rounded-lg bg-slate-50 p-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <strong className="text-sm text-slate-800">{titleCase(item.issue_type || item.anomaly_type || item.flag_type || item.mismatch_type || 'Finding')}</strong>
                {item.severity && <span className="text-xs text-slate-600">{titleCase(item.severity)} priority</span>}
              </div>
              <p className="mt-1 text-sm text-slate-700">{descriptionFor(item)}</p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export default function ForensicsLab({ forensics = null }) {
  if (!forensics) {
    return (
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-6" role="status">
        <h2 className="font-semibold text-amber-900">Document review signals unavailable</h2>
        <p className="mt-2 text-sm text-amber-800">No forensic results were returned for this claim.</p>
      </div>
    );
  }

  const ela = forensics.ela_result;
  const anomaly = forensics.anomaly_assessment;

  return (
    <div className="space-y-5">
      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="text-lg font-semibold text-slate-900">Document integrity and anomaly review</h2>
        <p className="mt-2 text-sm text-slate-700">{forensics.recommendation || 'No review recommendation was returned.'}</p>
        {forensics.disclaimer && <p className="mt-2 text-xs text-slate-500">{forensics.disclaimer}</p>}
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <div className="rounded-lg bg-slate-50 p-3">
            <div className="text-xs text-slate-500">Review level</div>
            <div className="mt-1 font-semibold text-slate-900">{titleCase(forensics.overall_risk || 'Unavailable')}</div>
          </div>
          <div className="rounded-lg bg-slate-50 p-3">
            <div className="text-xs text-slate-500">Anomaly density score</div>
            <div className="mt-1 font-semibold text-slate-900">{anomaly?.anomaly_density_score ?? 'Unavailable'}</div>
          </div>
        </div>
        {anomaly?.summary && <p className="mt-3 text-sm text-slate-700">{anomaly.summary}</p>}
      </section>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h3 className="font-semibold text-slate-900">Error level analysis</h3>
        {!ela ? (
          <p className="mt-2 text-sm text-slate-500">No image integrity result was returned.</p>
        ) : (
          <div className="mt-2 space-y-1 text-sm text-slate-700">
            <p>Assessment: {titleCase(ela.assessment)}</p>
            <p>Tamper score: {ela.assessment === 'NOT_ANALYZED' ? 'Unavailable' : (ela.tamper_score ?? 'Unavailable')}</p>
            {ela.details && <p>{ela.details}</p>}
            {ela.assessment !== 'NOT_ANALYZED' && <p>Suspicious regions: {ela.suspicious_regions?.length ?? 0}</p>}
          </div>
        )}
      </section>

      <FindingsList title="Document metadata flags" items={forensics.metadata_flags} descriptionFor={(item) => item.description || item.actual_value || 'No further details supplied.'} />
      <FindingsList title="Billing anomaly flags" items={forensics.bill_anomalies || forensics.bill_anomaly_flags} descriptionFor={(item) => item.description || 'No further details supplied.'} />
      <FindingsList title="Clinical consistency flags" items={forensics.consistency_flags} descriptionFor={(item) => item.description || item.details || 'No further details supplied.'} />
    </div>
  );
}
