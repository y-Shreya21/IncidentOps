export type Severity = 'critical' | 'high' | 'medium' | 'low';
export type IncidentStatus = 'investigating' | 'mitigating' | 'mitigated' | 'escalated' | 'resolved';

export interface ServiceMetadata {
  name: string;
  tier: string;
  owner: string;
  health_endpoint: string;
  metrics_endpoint: string;
  logs_path: string;
  dependencies: string[];
}

export interface EvidenceItem {
  evidence_id: string;
  agent: string;
  finding: string;
  service: string;
  evidence_source: string;
  evidence_timestamp: string;
  raw_data: Record<string, any>;
}

export interface MitigationProposal {
  proposal_id: string;
  agent: string;
  proposed_action: string;
  target_service: string;
  reason: string;
  supporting_evidence: string[];
  risk_level: 'low' | 'medium' | 'high';
}

export interface CommanderDecision {
  incident_id: string;
  likely_root_cause: string;
  root_cause_evidence: string[];
  mitigation_decision: string;
  target_service: string;
  decision_reason: string;
  decision_status: string;
  incident_status: IncidentStatus;
  confidence: number;
  escalation_required: boolean;
  timestamp?: string;
}

export interface TimelineEvent {
  event_id: string;
  incident_id: string;
  agent: string;
  event_type: string;
  timestamp: string;
  payload: Record<string, any>;
  evidence_ids: string[];
}

export interface StatusUpdate {
  update_id: string;
  incident_id: string;
  severity: Severity;
  status: IncidentStatus;
  timestamp: string;
  headline: string;
  message: string;
  audience: string;
}

export interface IncidentState {
  incident_id: string;
  service: string;
  symptom: string;
  severity: Severity;
  status: IncidentStatus;
  created_at: string;
  description: string;
  evidence: EvidenceItem[];
  mitigation_proposals: MitigationProposal[];
  decision?: CommanderDecision | null;
  status_updates: StatusUpdate[];
  timeline: TimelineEvent[];
  escalation_status: string;
}

export interface PostmortemReport {
  incident_id: string;
  affected_service: string;
  severity: Severity;
  incident_description: string;
  likely_root_cause: string;
  root_cause_evidence: string[];
  logs_findings: string[];
  dependency_findings: string[];
  mitigation_recommendation?: string;
  commander_decision: string;
  decision_justification: string;
  timeline: TimelineEvent[];
  escalation_status: string;
  final_incident_status: IncidentStatus;
  status_page_message?: string;
  generated_at: string;
}

export type UserRole = 'Administrator' | 'IncidentResponder' | 'SREEngineer' | 'Stakeholder';
