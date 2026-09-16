import type { Metadata } from "next";
import Link from "next/link";
import { WorkspaceShell } from "@/components/WorkspaceShell";

export const metadata: Metadata = { title: "Project workspace" };

export default function ProjectPage() {
  return <main id="main" className="workspace page-width"><div className="workspace-intro"><div><Link href="/" className="eyebrow text-link">Home /</Link><h1>Project workspace</h1></div><span className="workspace-badge">Foundation preview</span></div><WorkspaceShell /></main>;
}
