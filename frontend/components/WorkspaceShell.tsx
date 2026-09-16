import { ProjectControls } from "./ProjectControls";
import { CanonicalDisplayStage } from "./CanonicalDisplayStage";
import { EstimatePanel } from "./EstimatePanel";
import { VisualConceptPanel } from "./VisualConceptPanel";

export function WorkspaceShell() {
  return <div className="workspace-shell"><div className="configuration-row"><ProjectControls /><CanonicalDisplayStage /></div><div className="outputs-row"><EstimatePanel /><VisualConceptPanel /></div></div>;
}
