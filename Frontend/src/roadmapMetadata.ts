export type RoadmapStepType =
  | 'Learn a Skill'
  | 'Complete a Course'
  | 'Earn a Certification'
  | 'Build a Project'
  | 'Practice'
  | 'Gain Experience'
  | 'Prepare a Portfolio'
  | 'Other';

export const roadmapStepTypes: RoadmapStepType[] = [
  'Learn a Skill',
  'Complete a Course',
  'Earn a Certification',
  'Build a Project',
  'Practice',
  'Gain Experience',
  'Prepare a Portfolio',
  'Other',
];

export type RoadmapMetadata = {
  notes: string;
  category: string;
  resourceUrl: string;
  stepType: RoadmapStepType;
};

export type CareerRoadmapDraftStep = {
  title: string;
  description: string;
  phase: string;
  priority: 'low' | 'medium' | 'high';
  stepType: RoadmapStepType;
  category: string;
  resourceUrl: string;
  status: 'not_started' | 'in_progress' | 'completed';
};

const metadataPrefix = 'SSP-ROADMAP-META:1\n';

export function decodeRoadmapDescription(value: string): RoadmapMetadata {
  if (!value.startsWith(metadataPrefix)) {
    return { notes: value, category: '', resourceUrl: '', stepType: 'Other' };
  }
  const newline = value.indexOf('\n', metadataPrefix.length);
  if (newline < 0) {
    return { notes: value, category: '', resourceUrl: '', stepType: 'Other' };
  }
  try {
    const metadata = JSON.parse(
      decodeURIComponent(value.slice(metadataPrefix.length, newline)),
    ) as Partial<RoadmapMetadata>;
    return {
      notes: value.slice(newline + 1),
      category: typeof metadata.category === 'string' ? metadata.category : '',
      resourceUrl: typeof metadata.resourceUrl === 'string' ? metadata.resourceUrl : '',
      stepType:
        roadmapStepTypes.includes(metadata.stepType as RoadmapStepType)
          ? (metadata.stepType as RoadmapStepType)
          : 'Other',
    };
  } catch {
    return { notes: value, category: '', resourceUrl: '', stepType: 'Other' };
  }
}

export function encodeRoadmapDescription(metadata: RoadmapMetadata): string {
  return `${metadataPrefix}${encodeURIComponent(JSON.stringify({
    category: metadata.category,
    resourceUrl: metadata.resourceUrl,
    stepType: metadata.stepType,
  }))}\n${metadata.notes}`;
}

export function isHttpUrl(value: string): boolean {
  if (!value) return false;
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}
