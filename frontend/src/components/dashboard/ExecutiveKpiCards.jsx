import React from 'react';
import { motion } from 'framer-motion';
import { IndianRupee, AlertTriangle, FileText, Activity } from 'lucide-react';
import MetricCard from '../common/MetricCard';

// INR Currency Formatter Helper
const formatInr = (amount) => {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(amount || 0);
};

// Container Stagger Animation Variants
const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
      delayChildren: 0.05,
    },
  },
};

// Card Item Entrance Variants
const cardItemVariants = {
  hidden: { opacity: 0, y: 14 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { type: 'spring', stiffness: 260, damping: 24 },
  },
};

/**
 * Motion Sparkline Curve with SVG pathLength stroke draw
 * Animated Bézier curve stroke drawing (0 -> 1) with spring terminus node
 */
export function MotionSparklineCurve({
  data = [10, 20, 15, 25, 30, 28, 40],
  color = 'emerald',
  width = 75,
  height = 28,
  className = '',
}) {
  const cleanData = Array.isArray(data)
    ? data.filter((v) => v !== null && v !== undefined && typeof v === 'number' && Number.isFinite(v))
    : [];

  if (cleanData.length < 2) return null;

  const padding = 3;
  const min = Math.min(...cleanData);
  const max = Math.max(...cleanData);
  const range = max - min || 1;
  const pw = width - padding * 2;
  const ph = height - padding * 2;

  // Normalized coordinates
  const points = cleanData.map((val, i) => ({
    x: padding + (i / (cleanData.length - 1)) * pw,
    y: height - padding - ((val - min) / range) * ph,
  }));

  // Cubic Bezier Spline Path
  const linePath = points.reduce((acc, pt, i, arr) => {
    if (i === 0) return `M ${pt.x},${pt.y}`;
    const prev = arr[i - 1];
    const cp1x = prev.x + (pt.x - prev.x) / 2;
    const cp1y = prev.y;
    const cp2x = prev.x + (pt.x - prev.x) / 2;
    const cp2y = pt.y;
    return `${acc} C ${cp1x},${cp1y} ${cp2x},${cp2y} ${pt.x},${pt.y}`;
  }, '');

  const areaPath = `${linePath} L ${points[points.length - 1].x},${height} L ${points[0].x},${height} Z`;

  const colorMap = {
    emerald: { stroke: '#059669', stop1: '#10B981', stop2: '#ECFDF5', dot: '#059669' },
    primary: { stroke: '#0284C7', stop1: '#38BDF8', stop2: '#F0F9FF', dot: '#0284C7' },
    brand: { stroke: '#0284C7', stop1: '#38BDF8', stop2: '#F0F9FF', dot: '#0284C7' },
    teal: { stroke: '#0D9488', stop1: '#14B8A6', stop2: '#F0FDFA', dot: '#0D9488' },
    amber: { stroke: '#D97706', stop1: '#FBBF24', stop2: '#FFFBEB', dot: '#D97706' },
    rose: { stroke: '#E11D48', stop1: '#FB7185', stop2: '#FFF1F2', dot: '#E11D48' },
    slate: { stroke: '#64748B', stop1: '#94A3B8', stop2: '#F8FAFC', dot: '#64748B' },
  };

  const c = colorMap[color] || colorMap.emerald;
  const lastPoint = points[points.length - 1];
  const gradId = `motion-spark-grad-${color}`;

  return (
    <div className={`relative flex-shrink-0 ${className}`}>
      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="overflow-visible">
        <defs>
          <linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={c.stop1} stopOpacity="0.25" />
            <stop offset="100%" stopColor={c.stop2} stopOpacity="0.02" />
          </linearGradient>
        </defs>
        {/* Shaded Area Under Curve with Delayed Fade */}
        <motion.path
          d={areaPath}
          fill={`url(#${gradId})`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        />
        {/* Drawn Bézier Trend Line */}
        <motion.path
          d={linePath}
          fill="none"
          stroke={c.stroke}
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
          initial={{ pathLength: 0, opacity: 0 }}
          animate={{ pathLength: 1, opacity: 1 }}
          transition={{ duration: 0.85, ease: 'easeOut' }}
        />
        {/* Terminus Highlight Node */}
        <motion.circle
          cx={lastPoint.x}
          cy={lastPoint.y}
          r="2.5"
          fill={c.dot}
          initial={{ scale: 0, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.75, duration: 0.25, type: 'spring', stiffness: 400 }}
        />
      </svg>
    </div>
  );
}

/**
 * 4 Executive Financial KPI Cards Grid
 */
export default function ExecutiveKpiCards({ stats = {}, claims = [], className = '' }) {
  const totalRecovered = stats?.total_recovered_amount ?? stats?.total_amount_recovered ?? null;
  const totalClaims = stats?.total_claims ?? (claims.length > 0 ? claims.length : null);
  const mismatchesFound = stats?.mismatches_found ?? null;
  const pendingAnalysis = stats?.pending_analysis ?? stats?.pending_claims ?? null;

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 ${className}`}
    >
      {/* 1. Total Recovered Amount */}
      <motion.div variants={cardItemVariants} className="hover:scale-101 active:scale-[0.98] transition-transform">
        <MetricCard
          label="Total Recovered Amount"
          value={totalRecovered == null ? 'Unavailable' : formatInr(totalRecovered)}
          icon={IndianRupee}
          variant="emerald"
          tooltip="Aggregate amount reported by the backend analysis records."
        />
      </motion.div>

      {/* 2. High-Risk / Flagged Claims */}
      <motion.div variants={cardItemVariants} className="hover:scale-101 active:scale-[0.98] transition-transform">
        <MetricCard
          label="Flagged / Discrepancies"
          value={mismatchesFound == null ? 'Unavailable' : mismatchesFound}
          icon={AlertTriangle}
          variant="rose"
          tooltip="Mismatch count reported by the backend."
        />
      </motion.div>

      {/* 3. Total Processed Claims */}
      <motion.div variants={cardItemVariants} className="hover:scale-101 active:scale-[0.98] transition-transform">
        <MetricCard
          label="Total Processed Claims"
          value={totalClaims == null ? 'Unavailable' : totalClaims.toLocaleString('en-IN')}
          icon={FileText}
          variant="primary"
          tooltip="Claim count reported by the backend."
        />
      </motion.div>

      {/* 4. Pending Analysis */}
      <motion.div variants={cardItemVariants} className="hover:scale-101 active:scale-[0.98] transition-transform">
        <MetricCard
          label="Pending Analysis"
          value={pendingAnalysis == null ? 'Unavailable' : pendingAnalysis}
          icon={Activity}
          variant="amber"
          tooltip="Claims awaiting analysis, as reported by the backend."
        />
      </motion.div>
    </motion.div>
  );
}
