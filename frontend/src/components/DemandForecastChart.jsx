import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Area, CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip as RechartsTooltip, XAxis, YAxis } from 'recharts'
import { api } from '../api/client'
import { Empty, Loading } from './ui'
import { formatForecast, formatShortDate } from '../utils/presentation'

const dateOffset = (value, days) => {
  const date = new Date(`${value}T00:00:00Z`)
  date.setUTCDate(date.getUTCDate() + days)
  return date.toISOString().slice(0, 10)
}

export function DemandForecastChart({ forecast, reliability, productId, horizon = 28, productName, compact = false }) {
  const history = useQuery({
    queryKey: ['sales', 'forecast-history', productId, forecast?.history_end_date],
    enabled: Boolean(productId && forecast?.history_end_date),
    queryFn: () => api.sales({ product_id: productId, start_date: dateOffset(forecast.history_end_date, -27), end_date: forecast.history_end_date, limit: 28 }),
  })
  const chart = useMemo(() => {
    if (!forecast || !productId) return []
    const observed = [...(history.data || [])]
      .sort((left, right) => left.sale_date.localeCompare(right.sale_date))
      .map((row) => ({ date: row.sale_date, historical: Number(row.quantity_sold), forecast: null }))
    const intervalByHorizon = new Map((reliability?.intervals || []).map((item) => [item.horizon_day, item]))
    const future = forecast.values
      .filter((value) => value.product_id === Number(productId) && value.horizon_day <= horizon)
      .map((value) => {
        const interval = intervalByHorizon.get(value.horizon_day)?.['80']
        return {
          date: value.forecast_date, historical: null, forecast: Number(value.predicted_demand),
          interval80: interval ? [interval.lower, interval.upper] : null,
        }
      })
    return [...observed, ...future]
  }, [forecast, history.data, horizon, productId, reliability])

  if (history.isLoading) return <Loading />
  if (!chart.length) return <Empty title="Sales history is not available yet">Record or import sales for this product before viewing forecast context.</Empty>
  return <section className={`demand-forecast ${compact ? 'demand-forecast-compact' : ''}`}>
    <header>
      <div><p className="eyebrow">Demand outlook</p><h2>Sales history &amp; demand forecast</h2><p>{productName} · known sales through {formatShortDate(forecast.history_end_date)}</p></div>
    </header>
    <ResponsiveContainer width="100%" height={compact ? 260 : 340}>
      <LineChart data={chart} margin={{ top: 8, right: 12, bottom: 28, left: 0 }}>
        <CartesianGrid vertical={false}/>
        <XAxis dataKey="date" tickFormatter={formatShortDate} tick={{ fontSize: 11 }}/>
        <YAxis allowDecimals={false}/>
        <RechartsTooltip labelFormatter={formatShortDate} formatter={(value, name) => [Array.isArray(value) ? `${formatForecast(value[0])}–${formatForecast(value[1])}` : formatForecast(value), name === 'historical' ? 'Historical sales' : name === 'interval80' ? '80% historical uncertainty interval' : 'Point forecast']}/>
        <Legend wrapperStyle={{ paddingTop: 12 }} formatter={(value) => value === 'historical' ? 'Historical sales' : value === 'interval80' ? '80% historical uncertainty interval' : 'Point forecast'}/>
        <ReferenceLine x={forecast.forecast_start_date} stroke="#64748b" strokeDasharray="4 4" label={{ value: 'Forecast starts', position: 'insideTopRight', fill: '#64748b', fontSize: 11 }}/>
        {reliability?.available && <Area type="linear" dataKey="interval80" stroke="none" fill="#60a5fa" fillOpacity={.18} isAnimationActive={false}/>}
        <Line type="linear" dataKey="historical" stroke="#64748b" strokeWidth={2} dot={false}/>
        <Line type="linear" dataKey="forecast" stroke="#2563eb" strokeWidth={2.5} dot={false}/>
      </LineChart>
    </ResponsiveContainer>
  </section>
}
