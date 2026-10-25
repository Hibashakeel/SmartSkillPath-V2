export type Cert = { name: string; provider: string; cost: string; level: string; url: string; skills: string };

export const certs: Cert[] = [
{name:'Google Data Analytics Professional Certificate',provider:'Google · Coursera',cost:'Paid subscription',level:'Beginner',url:'https://www.coursera.org/professional-certificates/google-data-analytics',skills:'SQL, spreadsheets, data cleaning and visualization'},
{name:'freeCodeCamp Responsive Web Design',provider:'freeCodeCamp',cost:'Free',level:'Beginner',url:'https://www.freecodecamp.org/learn/2022/responsive-web-design/',skills:'HTML, CSS, accessible responsive interfaces'},
{name:'AWS Certified Cloud Practitioner',provider:'Amazon Web Services',cost:'Paid exam',level:'Beginner',url:'https://aws.amazon.com/certification/certified-cloud-practitioner/',skills:'Cloud concepts, AWS services and security'},
{name:'Microsoft Azure Fundamentals',provider:'Microsoft Learn',cost:'Free learning · exam may cost',level:'Beginner',url:'https://learn.microsoft.com/credentials/certifications/azure-fundamentals/',skills:'Cloud concepts, Azure architecture and governance'},
{name:'IBM SkillsBuild',provider:'IBM',cost:'Free learning credentials vary',level:'Beginner',url:'https://skillsbuild.org/',skills:'AI, cybersecurity, data and workplace skills'},
{name:'Google Cybersecurity Professional Certificate',provider:'Google · Coursera',cost:'Paid subscription',level:'Beginner',url:'https://www.coursera.org/professional-certificates/google-cybersecurity',skills:'Security operations, Linux, SQL and SIEM'},
{name:'CS50 Introduction to Computer Science',provider:'Harvard University',cost:'Free to learn · verified certificate may cost',level:'Beginner',url:'https://cs50.harvard.edu/x/',skills:'Programming, algorithms and computer science'},
{name:'Meta Front-End Developer',provider:'Meta · Coursera',cost:'Paid subscription',level:'Beginner',url:'https://www.coursera.org/professional-certificates/meta-front-end-developer',skills:'HTML, CSS, JavaScript, React and UI development'}];

const curatedCertificationUrls = new Map(
  certs.map((certification) => [
    certification.name.toLowerCase().replace(/[^a-z0-9]+/g, ''),
    certification.url,
  ]),
);

export function resolveCertification(value: unknown): { name: string; url?: string } | null {
  if (typeof value === 'string') {
    const name = value.trim();
    if (!name) return null;
    const key = name.toLowerCase().replace(/[^a-z0-9]+/g, '');
    return { name, url: curatedCertificationUrls.get(key) };
  }

  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;
  const record = value as Record<string, unknown>;
  const rawName = record.name ?? record.title ?? record.certification;
  if (typeof rawName !== 'string' || !rawName.trim()) return null;
  const name = rawName.trim();
  const rawUrl = record.url ?? record.resource_url ?? record.link;
  if (typeof rawUrl === 'string' && isSafeHttpUrl(rawUrl)) {
    return { name, url: rawUrl };
  }
  const key = name.toLowerCase().replace(/[^a-z0-9]+/g, '');
  return { name, url: curatedCertificationUrls.get(key) };
}

function isSafeHttpUrl(value: string): boolean {
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}
