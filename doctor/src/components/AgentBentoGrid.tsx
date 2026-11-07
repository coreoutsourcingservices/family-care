import type { ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";
/** Adapted from VengeanceUI's FeatCard / AgentBentoGrid.
 * https://github.com/Ashutoshx7/VengeanceUI/blob/main/public/r/agent-bento-grid.json
 * Uses scoped CSS and actual practice data instead of the registry's AI-agent demos.
 */
export function FeatCard({
  title,
  description,
  children,
  tone = "violet",
}: {
  title: string;
  description: string;
  children: ReactNode;
  tone?: "violet" | "cyan" | "mint" | "peach";
}) {
  const reduced = useReducedMotion();
  return (
    <motion.section
      initial={reduced ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
      className={"dr-bento-card dr-bento-" + tone}
    >
      <div className="dr-bento-heading">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      <div className="dr-bento-visual">{children}</div>
    </motion.section>
  );
}
export default function AgentBentoGrid({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      aria-label="Practice data overview"
      className={"dr-bento-grid " + className}
    >
      {children}
    </section>
  );
}
