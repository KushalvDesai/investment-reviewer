"use client";

interface InsightsListProps {
  highlights?: string[];
  warnings?: string[];
  recommendations?: string[];
  insights?: string[];
}

function Section({
  title,
  items,
  color,
  icon,
}: {
  title: string;
  items: string[];
  color: string;
  icon: string;
}) {
  if (!items || items.length === 0) return null;
  return (
    <div>
      <h3 className={`mb-2 flex items-center gap-2 text-sm font-semibold ${color}`}>
        <span>{icon}</span>
        {title}
      </h3>
      <ul className="space-y-1.5">
        {items.map((item, i) => (
          <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
            <span className={`mt-1 shrink-0 text-xs ${color}`}>•</span>
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function InsightsList({
  highlights = [],
  warnings = [],
  recommendations = [],
  insights = [],
}: InsightsListProps) {
  return (
    <div className="space-y-5">
      <Section
        title="Highlights"
        items={highlights}
        color="text-indigo-400"
        icon="✦"
      />
      <Section
        title="Insights"
        items={insights}
        color="text-sky-400"
        icon="◈"
      />
      <Section
        title="Warnings"
        items={warnings}
        color="text-amber-400"
        icon="⚠"
      />
      <Section
        title="Recommendations"
        items={recommendations}
        color="text-emerald-400"
        icon="→"
      />
    </div>
  );
}
