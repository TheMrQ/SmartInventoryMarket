const demandPatterns = {
  "0-25% zero": {
    label: "Stable",
    explanation: "Sales were recorded on most historical days.",
  },
  "25-50% zero": {
    label: "Variable",
    explanation: "Sales were not recorded on some historical days, so demand varies over time.",
  },
  "50-75% zero": {
    label: "Irregular",
    explanation: "Sales were not recorded on many historical days, so future demand is harder to predict.",
  },
  "75-100% zero": {
    label: "Highly intermittent",
    explanation: "Sales were rarely recorded in the historical period, so future demand is especially hard to predict.",
  },
};

const reliabilityLabels = {
  HIGHER: "Higher",
  MODERATE: "Moderate",
  LIMITED: "Limited",
};

export function demandPatternFor(historical = {}) {
  return demandPatterns[historical.sparsity_band] || {
    label: "Variable",
    explanation: "Historical sales were not consistently recorded on every day.",
  };
}

export function recommendationReliabilityFor(historical = {}) {
  const pattern = demandPatternFor(historical);
  const level = reliabilityLabels[historical.evidence_level] || "Moderate";
  let explanation;

  if (level === "Higher") {
    explanation = "Demand has been relatively consistent and historical forecast error has been lower.";
  } else if (level === "Limited" && pattern.label === "Highly intermittent") {
    explanation = "Demand is highly intermittent, so future demand is harder to predict.";
  } else if (level === "Limited") {
    explanation = "Historical forecast error or uncertainty has been wider, so review this recommendation carefully.";
  } else if (pattern.label === "Irregular" || pattern.label === "Highly intermittent") {
    explanation = "This product has irregular sales, so future demand is harder to predict.";
  } else {
    explanation = "Historical evidence is mixed, so review the forecast range and current stock before ordering.";
  }

  return { level, explanation, pattern };
}

export function zeroSalesExplanation(historical = {}) {
  const rate = Math.round(Number(historical.zero_rate_56) * 100);
  if (!Number.isFinite(rate)) return "Shows how consistently this product sold in historical data.";
  return `No sales were recorded on ${rate}% of the last 56 historical days.`;
}

export function displayForecastModel(modelName) {
  if (modelName === "XGBOOST_V1") return "XGBoost V1";
  return String(modelName || "Forecast model").replaceAll("_", " ");
}
