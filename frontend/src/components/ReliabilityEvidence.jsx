import { HelpCircle, ShieldCheck } from "lucide-react";
import {
  displayForecastModel,
  recommendationReliabilityFor,
  zeroSalesExplanation,
} from "../utils/reliabilityPresentation";
import { formatForecast, formatShortDate } from "../utils/presentation";
import { Tooltip } from "./ui";

function ReliabilityLabel({ children, tooltip }) {
  return (
    <span className="reliability-label">
      {children}
      <Tooltip label={tooltip}>
        <button type="button" className="reliability-help" aria-label={tooltip}>
          <HelpCircle size={14} aria-hidden="true" />
        </button>
      </Tooltip>
    </span>
  );
}

export function ReliabilityEvidence({ evidence, context = "forecast" }) {
  const historical = evidence.historical;
  const summary = recommendationReliabilityFor(historical);
  const firstInterval = evidence.intervals?.[0];
  const lastInterval = evidence.intervals?.at(-1);
  const typicalRange = firstInterval?.["80"];
  const widerRange = firstInterval?.["95"];
  const coverage = (evidence.calibration || []).find(
    (item) => item.coverage_level === 0.8,
  );
  const isRecommendation = context === "recommendation";

  return (
    <div className={`manager-reliability manager-reliability-${context}`}>
      <header className="manager-reliability-header">
        <div>
          <p className="eyebrow">
            {isRecommendation ? "Recommendation reliability" : "Forecast reliability"}
          </p>
          <h3>
            {isRecommendation
              ? "How much historical evidence supports this recommendation"
              : "What past results say about this forecast"}
          </h3>
        </div>
      </header>

      <section className="reliability-state" aria-label="Recommendation reliability summary">
        <div className="reliability-state-icon" aria-hidden="true">
          <ShieldCheck size={18} />
        </div>
        <div>
          <ReliabilityLabel tooltip="A summary of how much historical evidence supports this recommendation. It is not a guarantee.">
            {isRecommendation ? "Recommendation reliability" : "Forecast reliability"}
          </ReliabilityLabel>
          <strong>{summary.level}</strong>
          <p>{summary.explanation}</p>
        </div>
      </section>

      <div className="manager-evidence-grid">
        <article>
          <ReliabilityLabel tooltip="How far the forecast was from actual sales on average in historical tests.">
            Typical forecast error
          </ReliabilityLabel>
          <strong>About {formatForecast(historical.historical_mae)}</strong>
          <p>
            In historical tests, the forecast differed from actual sales by about {formatForecast(historical.historical_mae)} on average.
          </p>
        </article>
        <article>
          <ReliabilityLabel tooltip="Shows how consistently this product sold in historical data.">
            Demand pattern
          </ReliabilityLabel>
          <strong>{summary.pattern.label}</strong>
          <p>{zeroSalesExplanation(historical)}</p>
        </article>
        {typicalRange && (
          <article>
            <ReliabilityLabel tooltip="A wider range means historical demand was harder to predict. This range was designed to contain actual historical demand about 80% of the time; it does not mean the forecast itself is 80% accurate.">
              Typical range — 80% historical interval
            </ReliabilityLabel>
            <strong>
              {formatForecast(typicalRange.lower)}–{formatForecast(typicalRange.upper)}
            </strong>
            <p>Based on how much similar forecasts differed from actual sales in historical tests.</p>
          </article>
        )}
      </div>

      <dl className="manager-provenance">
        <div>
          <dt>Forecast model</dt>
          <dd>{displayForecastModel(evidence.model_name)}</dd>
        </div>
        <div>
          <dt>Based on historical data through</dt>
          <dd>{formatShortDate(evidence.history_end_date)}</dd>
        </div>
        {evidence.forecast_start_date && lastInterval?.forecast_date && (
          <div>
            <dt>Forecast period</dt>
            <dd>
              {formatShortDate(evidence.forecast_start_date)}–{formatShortDate(lastInterval.forecast_date)}
            </dd>
          </div>
        )}
      </dl>

      <aside className="manager-review-note">
        <strong>Manager review recommended</strong>
        <span>Forecasts are estimates, not guarantees. This is decision support, not an automatic purchase decision.</span>
      </aside>

      <details className="reliability-details">
        <summary>View technical details</summary>
        <div>
          <dl className="reliability-technical-grid">
            <div><dt>Historical MAE</dt><dd>{formatForecast(historical.historical_mae)}</dd></div>
            <div><dt>Historical RMSE</dt><dd>{formatForecast(historical.historical_rmse)}</dd></div>
            <div><dt>Zero-sales rate</dt><dd>{Math.round(Number(historical.zero_rate_56) * 100)}% over 56 days</dd></div>
            <div><dt>Reliability basis</dt><dd>{historical.evidence_reason}</dd></div>
            <div><dt>Forecast run</dt><dd>Run #{evidence.forecast_run_id}</dd></div>
            <div><dt>Feature set</dt><dd>{evidence.feature_set}</dd></div>
            <div><dt>80% historical check</dt><dd>{coverage ? `${coverage.empirical_coverage_percent.toFixed(1)}% of Fold 4 actuals were inside the range.` : "Unavailable"}</dd></div>
            {coverage && <div><dt>Calibration source</dt><dd>{coverage.calibration_folds.replaceAll("_", " ")}; checked against Fold 4.</dd></div>}
            {widerRange && <div><dt>Wider range — 95% historical interval</dt><dd>{formatForecast(widerRange.lower)}–{formatForecast(widerRange.upper)}</dd></div>}
          </dl>
          <p className="reliability-technical-note">MAE means Mean Absolute Error. The interval check uses pre-TEST rolling historical data; it is evidence for review, not a guarantee.</p>
        </div>
      </details>
    </div>
  );
}
