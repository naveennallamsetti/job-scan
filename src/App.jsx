import { useState, useEffect, useRef, useCallback } from "react";

const API_BASE = "http://" + (typeof window !== "undefined" ? window.location.hostname : "localhost") + ":8000/api";

// ─── MOCK DATA ────────────────────────────────────────────────────────────────
const MOCK_USER = { full_name: "Naveen Kumar", role: "AWS DevOps Engineer", experience: "3.8 Years", email: "naveendevops589@gmail.com" };

const MOCK_JOBS = [
  { id: 1, company_name: "Lloyds Banking Group", position: "AWS DevOps Engineer", job_portal: "LinkedIn", applied_date: "2024-03-10", status: "Technical Round 2", notes: "YOKRA referral" },
  { id: 2, company_name: "Zurich Insurance", position: "Cloud Automation Consultant", job_portal: "Naukri", applied_date: "2024-03-14", status: "Manager Round", notes: "KRIFY referral" },
  { id: 3, company_name: "TCS Client", position: "Lead DevOps Specialist", job_portal: "Naukri", applied_date: "2024-03-18", status: "Applied", notes: "" },
  { id: 4, company_name: "HSBC Tech", position: "Site Reliability Engineer", job_portal: "LinkedIn", applied_date: "2024-03-20", status: "Screening", notes: "AWS focus" },
  { id: 5, company_name: "Barclays Capital", position: "DevOps Platform Lead", job_portal: "LinkedIn", applied_date: "2024-03-22", status: "Applied", notes: "K8s heavy role" },
];

// ─── LIVE JOB FEED DATA (Simulated real listings) ───────────────────────────
const LIVE_JOB_POOL = [
  { id: "lj1", title: "Senior AWS DevOps Engineer", company: "Deutsche Bank", location: "Hyderabad, India (Hybrid)", portal: "LinkedIn", postedAgo: "2h ago", salary: "₹18-28 LPA", match: 97, tags: ["AWS", "EKS", "Terraform", "Jenkins"], description: "Looking for a Senior DevOps Engineer to manage EKS clusters, CI/CD pipelines using Jenkins, and infrastructure automation with Terraform. IRSA and multi-region deployments required.", url: "https://linkedin.com/jobs", applied: false, saved: false },
  { id: "lj2", title: "DevOps / SRE Lead", company: "HSBC Technology", location: "Hyderabad, India (On-site)", portal: "Naukri", postedAgo: "4h ago", salary: "₹20-32 LPA", match: 94, tags: ["Kubernetes", "AWS", "Prometheus", "Ansible"], description: "SRE Lead role requiring Kubernetes cluster management, AWS infrastructure, Prometheus/Grafana monitoring stacks, and Ansible automation playbooks.", url: "https://naukri.com/jobs", applied: false, saved: false },
  { id: "lj3", title: "Cloud Automation Engineer", company: "Standard Chartered", location: "Chennai, India (Hybrid)", portal: "LinkedIn", postedAgo: "6h ago", salary: "₹15-24 LPA", match: 91, tags: ["AWS", "Terraform", "Docker", "Jenkins"], description: "Cloud automation focused role. Terraform IaC, AWS services (EC2, VPC, RDS, S3), Docker containerisation, and Jenkins pipeline management.", url: "https://linkedin.com/jobs", applied: false, saved: false },
  { id: "lj4", title: "Kubernetes Platform Engineer", company: "Capgemini", location: "Bangalore, India (Remote)", portal: "Indeed", postedAgo: "8h ago", salary: "₹14-22 LPA", match: 88, tags: ["Kubernetes", "Helm", "AWS", "Terraform"], description: "Platform engineering role with heavy Kubernetes focus. Helm chart development, EKS management, Terraform modules for AWS resources.", url: "https://indeed.com/jobs", applied: false, saved: false },
  { id: "lj5", title: "AWS Infrastructure Lead", company: "Wipro Technologies", location: "Hyderabad, India (Hybrid)", portal: "Naukri", postedAgo: "12h ago", salary: "₹16-26 LPA", match: 86, tags: ["AWS", "CloudFormation", "Ansible", "Linux"], description: "Lead engineer for AWS cloud infrastructure. CloudFormation templates, Ansible configuration management, Linux server administration, VPC design.", url: "https://naukri.com/jobs", applied: false, saved: false },
  { id: "lj6", title: "DevOps Engineer – FinTech", company: "Razorpay", location: "Bangalore, India (Hybrid)", portal: "LinkedIn", postedAgo: "1d ago", salary: "₹18-30 LPA", match: 85, tags: ["Kubernetes", "AWS", "Jenkins", "Terraform"], description: "FinTech DevOps role at high-growth startup. Kubernetes on EKS, Jenkins CI/CD, Terraform IaC, monitoring with Prometheus and Grafana.", url: "https://linkedin.com/jobs", applied: false, saved: false },
  { id: "lj7", title: "Senior Site Reliability Engineer", company: "Amazon (AWS)", location: "Hyderabad, India (Hybrid)", portal: "LinkedIn", postedAgo: "1d ago", salary: "₹30-50 LPA", match: 83, tags: ["AWS", "Kubernetes", "Python", "Terraform"], description: "SRE at Amazon Web Services. Deep AWS expertise required, Kubernetes orchestration, Python scripting for automation, Terraform for IaC.", url: "https://linkedin.com/jobs", applied: false, saved: false },
  { id: "lj8", title: "Cloud DevOps Consultant", company: "Deloitte India", location: "Mumbai, India (Hybrid)", portal: "Glassdoor", postedAgo: "2d ago", salary: "₹20-35 LPA", match: 81, tags: ["AWS", "Terraform", "Ansible", "DevSecOps"], description: "Consulting role requiring AWS architecture, Terraform automation, Ansible playbooks, and DevSecOps practices for banking clients.", url: "https://glassdoor.com/jobs", applied: false, saved: false },
  { id: "lj9", title: "Platform & Infra Engineer", company: "Freshworks", location: "Chennai, India (Remote)", portal: "Indeed", postedAgo: "2d ago", salary: "₹14-20 LPA", match: 78, tags: ["Kubernetes", "AWS", "Prometheus", "Docker"], description: "Infrastructure engineering at product company. Kubernetes cluster operations, AWS cost optimisation, monitoring with Prometheus stack.", url: "https://indeed.com/jobs", applied: false, saved: false },
  { id: "lj10", title: "Lead DevOps Engineer", company: "Accenture", location: "Hyderabad, India (Hybrid)", portal: "Naukri", postedAgo: "3d ago", salary: "₹18-28 LPA", match: 76, tags: ["AWS", "Jenkins", "Docker", "Linux"], description: "Lead DevOps role for banking client projects. Jenkins pipelines, AWS services management, Docker containerisation, Linux administration.", url: "https://naukri.com/jobs", applied: false, saved: false },
  { id: "lj11", title: "Infrastructure Automation Engineer", company: "Infosys BPM", location: "Pune, India (On-site)", portal: "Naukri", postedAgo: "3d ago", salary: "₹12-18 LPA", match: 74, tags: ["Ansible", "Terraform", "AWS", "Python"], description: "Automation engineer focused on Ansible playbooks, Terraform modules, AWS provisioning, and Python scripting for infrastructure tasks.", url: "https://naukri.com/jobs", applied: false, saved: false },
  { id: "lj12", title: "Cloud Native Engineer – GCP/AWS", company: "Google India", location: "Bangalore, India (Hybrid)", portal: "LinkedIn", postedAgo: "4d ago", salary: "₹35-60 LPA", match: 71, tags: ["Kubernetes", "GCP", "AWS", "Terraform"], description: "Cloud native engineering role at Google. GCP and AWS multi-cloud, Kubernetes advanced patterns, Terraform enterprise, FinOps.", url: "https://linkedin.com/jobs", applied: false, saved: false },
];

const MOCK_TASKS = [
  { id: 1, title: "Practice AWS VPC secure routing interview questions", status: "pending", task_type: "daily" },
  { id: 2, title: "Deploy Kubernetes manifests limits configurations", status: "completed", task_type: "daily" },
  { id: 3, title: "Update Terraform remote states for HBOS project review", status: "pending", task_type: "weekly" },
  { id: 4, title: "Review Ansible microservice rolling deployment playbooks", status: "pending", task_type: "weekly" },
  { id: 5, title: "Set up Prometheus alerting stack on staging cluster", status: "pending", task_type: "daily" },
];

const MOCK_QA = [
  { id: 1, category: "AWS", question: "Explain EKS IRSA OIDC permissions and why they matter for pod-level IAM.", answer: "IRSA (IAM Roles for Service Accounts) uses OIDC federation to assign fine-grained IAM roles directly to Kubernetes service accounts. Each pod gets a projected token at /var/run/secrets/eks.amazonaws.com/serviceaccount/ which STS validates against the cluster OIDC endpoint. This eliminates node-level IAM bloat and enforces least-privilege per workload." },
  { id: 2, category: "Terraform", question: "How do you configure S3 state locking with DynamoDB to prevent concurrent plan conflicts?", answer: "Configure a backend block with bucket, key, region, and dynamodb_table. The table must have a primary key 'LockID' (String). Terraform writes a lock item during plan/apply and removes it on completion. Use encrypt=true and versioning on the S3 bucket. Always pre-create the DynamoDB table before running terraform init." },
  { id: 3, category: "Kubernetes", question: "What are resource requests vs limits and how do they affect scheduling?", answer: "Requests are the guaranteed minimum resources the scheduler uses to place a pod on a node. Limits are the hard cap. If a container exceeds CPU limits it gets throttled; if it exceeds memory limits it is OOM-killed. Best practice: set requests close to actual average usage and limits at 2x. Using VPA or Goldilocks helps tune these over time." },
  { id: 4, category: "Ansible", question: "Describe an Ansible playbook for zero-downtime rolling deployments.", answer: "Use serial: 25% with max_fail_percentage: 0. Tasks: drain node, deploy new artifact, health-check (uri module with retries), re-enable node. Use delegate_to for load balancer tasks. Store sensitive vars in ansible-vault. Use handlers to restart services only when config changes. Pre-task connectivity checks avoid partial rollouts." },
  { id: 5, category: "Jenkins", question: "How do you implement a multi-branch pipeline with environment-specific approvals?", answer: "Use a Jenkinsfile with when { branch 'main' } guards. Input steps with timeout(time:1, unit:'HOURS') wrap production deployments. Use withCredentials for secrets, milestone() to cancel stale builds, and lock() to serialize deployments. Store shared library functions in vars/ directory and load with @Library annotation." },
];

const MOCK_RESUME = `NAVEEN KUMAR — AWS DevOps Engineer | 3.8 Years
naveendevops589@gmail.com | LinkedIn | GitHub

CORE COMPETENCIES
AWS (EKS, EC2, S3, IAM, VPC, RDS, CloudWatch) | Kubernetes | Terraform | Ansible | Jenkins | Docker | Prometheus | Grafana

EXPERIENCE
Yokra Solutions — DevOps Engineer (2022–Present)
• Deployed AWS EKS clusters with IRSA OIDC permissions enabling pod-level IAM role assignment
• Implemented Terraform remote backends with S3 state locking via DynamoDB preventing concurrent conflicts
• Automated microservice rolling deployments using Ansible playbooks with zero-downtime patterns
• Configured Prometheus alerting stacks monitoring 40+ microservices with PagerDuty integration

Krify Technologies — Junior DevOps (2021–2022)
• Built Jenkins multi-branch pipelines with environment-specific approval gates for production deployments
• Containerised 12 Java/Node services using Docker multi-stage builds reducing image sizes by 60%
• Managed Kubernetes resource limits and VPA configurations across 3 environment clusters`;

const MOCK_EMAILS = [
  { id: 1, from: "Sarah Mitchell <s.mitchell@lloyds.com>", subject: "AWS DevOps – Technical Round 2 Invitation", preview: "Hi Naveen, following your strong performance in round 1...", date: "Mar 21", body: "Hi Naveen,\n\nFollowing your strong performance in the first technical screening, the hiring panel would like to invite you to Technical Round 2 for the AWS DevOps Engineer role.\n\nThe interview will cover EKS architecture, Terraform state management, and a live AWS VPC design exercise.\n\nPlease confirm your availability for March 28th at 2:00 PM GMT.\n\nBest regards,\nSarah Mitchell\nTalent Acquisition, Lloyds Banking Group" },
  { id: 2, from: "Rahul Sharma <r.sharma@tcs.com>", subject: "Urgent: Lead DevOps – Client Project Requirement", preview: "Naveen, we have an immediate opening for a financial services client...", date: "Mar 20", body: "Naveen,\n\nWe have an immediate opening for a Lead DevOps Specialist at our financial services client. Your profile matches the requirement closely — Kubernetes, Terraform, and AWS are must-haves.\n\nTotal experience required: 3-5 years.\nLocation: Hyderabad, India (Hybrid)\nNotice: Immediate/15 days\n\nAre you available for a quick call?\n\nRegards,\nRahul Sharma\nTCS Talent Team" },
  { id: 3, from: "Priya Nair <priya@krify.com>", subject: "Reference for Zurich Insurance Application", preview: "Hi Naveen, just wanted to let you know I've submitted...", date: "Mar 19", body: "Hi Naveen,\n\nJust wanted to let you know I submitted your reference to the Zurich Insurance hiring team. They were very impressed with the EKS work you described.\n\nThe Manager Round is scheduled for next week. They'll focus on cloud cost optimisation and multi-region DR strategies.\n\nAll the best!\nPriya" },
];

const AUTOMATION_LOGS = [
  { ts: "10:42:01", type: "scrape", desc: "LinkedIn scan: 23 jobs matched DevOps keywords", status: "success" },
  { ts: "10:42:04", type: "notify", desc: "Telegram alert sent: 'SRE Lead @ HSBC — 94% match'", status: "success" },
  { ts: "10:43:12", type: "apply", desc: "Auto-apply: Barclays DevOps Platform Lead via Naukri", status: "success" },
  { ts: "10:44:30", type: "scrape", desc: "Naukri scan: 11 jobs — 2 above 80% threshold", status: "success" },
  { ts: "10:45:01", type: "apply", desc: "Auto-apply: HSBC SRE — login session expired", status: "failed" },
  { ts: "10:46:20", type: "notify", desc: "Telegram alert sent: 'Cloud Architect @ Deutsche — 87% match'", status: "success" },
];

const PORTAL_META = {
  LinkedIn:  { color: "#0077B5", bg: "#0077B520", icon: "in" },
  Naukri:    { color: "#FF6B00", bg: "#FF6B0020", icon: "N"  },
  Indeed:    { color: "#2164f3", bg: "#2164f320", icon: "I"  },
  Glassdoor: { color: "#0CAA41", bg: "#0CAA4120", icon: "G"  },
};

const getPortalMeta = (portal) => {
  if (!portal) return { color: "#8B5CF6", bg: "#8B5CF620", icon: "💼" };
  const match = Object.keys(PORTAL_META).find(k => 
    portal.toLowerCase().includes(k.toLowerCase()) || 
    k.toLowerCase().includes(portal.toLowerCase())
  );
  if (match) return PORTAL_META[match];
  if (portal.toLowerCase().includes("work")) {
    return { color: "#E34A26", bg: "#E34A2615", icon: "WR" };
  }
  if (portal.toLowerCase().includes("remotive")) {
    return { color: "#2A9D8F", bg: "#2A9D8F15", icon: "Rm" };
  }
  if (portal.toLowerCase().includes("cncf")) {
    return { color: "#0086FF", bg: "#0086FF15", icon: "CF" };
  }
  if (portal.toLowerCase().includes("dice")) {
    return { color: "#E01A22", bg: "#E01A2215", icon: "D" };
  }
  return { color: "#8b5cf6", bg: "#8b5cf615", icon: portal.slice(0, 2) };
};

// ─── HELPERS ──────────────────────────────────────────────────────────────────
const sparkPath = (data, w = 80, h = 28) => {
  const min = Math.min(...data), max = Math.max(...data);
  const range = max - min || 1;
  const pts = data.map((v, i) => [(i / (data.length - 1)) * w, h - ((v - min) / range) * h]);
  return pts.map((p, i) => (i === 0 ? `M${p[0]},${p[1]}` : `L${p[0]},${p[1]}`)).join(" ");
};

const SparkCard = ({ label, value, delta, data, color }) => (
  <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 14, padding: "16px 18px", display: "flex", flexDirection: "column", gap: 6, flex: "1 1 140px", minWidth: 140 }}>
    <span style={{ fontSize: 11, color: "var(--muted)", letterSpacing: "0.08em", textTransform: "uppercase" }}>{label}</span>
    <div style={{ display: "flex", alignItems: "flex-end", justifyContent: "space-between" }}>
      <span style={{ fontSize: 28, fontWeight: 700, color: "var(--text)" }}>{value}</span>
      <svg width={80} height={28} style={{ overflow: "visible" }}>
        <defs><linearGradient id={`sg-${label}`} x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor={color} stopOpacity="0.25" /><stop offset="100%" stopColor={color} stopOpacity="0" /></linearGradient></defs>
        <path d={sparkPath(data) + ` L80,28 L0,28 Z`} fill={`url(#sg-${label})`} />
        <path d={sparkPath(data)} fill="none" stroke={color} strokeWidth={1.8} strokeLinejoin="round" />
      </svg>
    </div>
    <span style={{ fontSize: 12, color: delta > 0 ? "#4ade80" : "#f87171" }}>{delta > 0 ? "↑" : "↓"} {Math.abs(delta)}% vs last month</span>
  </div>
);

const BezierChart = () => {
  const months = ["Oct","Nov","Dec","Jan","Feb","Mar"];
  const apps = [8,12,9,15,18,22], ints = [1,3,2,5,6,8];
  const W=480,H=160,pad=40;
  const toX=i=>pad+(i/(months.length-1))*(W-pad*2);
  const toY=(v,max)=>H-pad-(v/max)*(H-pad*1.5);
  const curve=(pts)=>pts.map((p,i,a)=>{
    if(i===0)return`M${p[0]},${p[1]}`;
    const cpx=(a[i-1][0]+p[0])/2;
    return`C${cpx},${a[i-1][1]} ${cpx},${p[1]} ${p[0]},${p[1]}`;
  }).join(" ");
  const aPts=apps.map((v,i)=>[toX(i),toY(v,25)]);
  const iPts=ints.map((v,i)=>[toX(i),toY(v,25)]);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" style={{ overflow:"visible" }}>
      <defs>
        <linearGradient id="ga" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#8B5CF6" stopOpacity="0.3"/><stop offset="100%" stopColor="#8B5CF6" stopOpacity="0"/></linearGradient>
        <linearGradient id="gi" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#06b6d4" stopOpacity="0.3"/><stop offset="100%" stopColor="#06b6d4" stopOpacity="0"/></linearGradient>
      </defs>
      {[5,10,15,20,25].map(v=>(
        <g key={v}><line x1={pad} x2={W-pad} y1={toY(v,25)} y2={toY(v,25)} stroke="var(--border)" strokeWidth={0.5} strokeDasharray="4,4"/><text x={pad-6} y={toY(v,25)+4} textAnchor="end" fontSize={9} fill="var(--muted)">{v}</text></g>
      ))}
      {months.map((m,i)=><text key={m} x={toX(i)} y={H-4} textAnchor="middle" fontSize={9} fill="var(--muted)">{m}</text>)}
      <path d={curve(aPts)+` L${aPts[aPts.length-1][0]},${H-pad} L${aPts[0][0]},${H-pad} Z`} fill="url(#ga)"/>
      <path d={curve(iPts)+` L${iPts[iPts.length-1][0]},${H-pad} L${iPts[0][0]},${H-pad} Z`} fill="url(#gi)"/>
      <path d={curve(aPts)} fill="none" stroke="#8B5CF6" strokeWidth={2}/>
      <path d={curve(iPts)} fill="none" stroke="#06b6d4" strokeWidth={2} strokeDasharray="6,3"/>
      {aPts.map((p,i)=><circle key={i} cx={p[0]} cy={p[1]} r={3.5} fill="#8B5CF6"/>)}
      {iPts.map((p,i)=><circle key={i} cx={p[0]} cy={p[1]} r={3.5} fill="#06b6d4"/>)}
    </svg>
  );
};

const GaugeChart = ({ pct=72 }) => {
  const r=54,cx=70,cy=70,sw=10;
  const circ=Math.PI*r, offset=circ*(1-pct/100);
  return (
    <svg width={140} height={80} viewBox="0 0 140 80">
      <path d={`M${cx-r},${cy} A${r},${r} 0 0,1 ${cx+r},${cy}`} fill="none" stroke="var(--border)" strokeWidth={sw} strokeLinecap="round"/>
      <path d={`M${cx-r},${cy} A${r},${r} 0 0,1 ${cx+r},${cy}`} fill="none" stroke="url(#gaugeGrad)" strokeWidth={sw} strokeLinecap="round" strokeDasharray={circ} strokeDashoffset={offset} style={{transition:"stroke-dashoffset 1s ease"}}/>
      <defs><linearGradient id="gaugeGrad" x1="0" y1="0" x2="1" y2="0"><stop offset="0%" stopColor="#8B5CF6"/><stop offset="100%" stopColor="#06b6d4"/></linearGradient></defs>
      <text x={cx} y={cy+2} textAnchor="middle" fontSize={18} fontWeight={700} fill="var(--text)">{pct}%</text>
      <text x={cx} y={cy+16} textAnchor="middle" fontSize={9} fill="var(--muted)">EKS Mastery</text>
    </svg>
  );
};

const ProgressBar = ({ label, pct, color }) => (
  <div style={{ marginBottom:10 }}>
    <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:"var(--muted)", marginBottom:4 }}>
      <span>{label}</span><span style={{color}}>{pct}%</span>
    </div>
    <div style={{ height:5, background:"var(--border)", borderRadius:99 }}>
      <div style={{ height:"100%", width:`${pct}%`, background:color, borderRadius:99, transition:"width 1s ease" }}/>
    </div>
  </div>
);

const Badge = ({ text, color="#8B5CF6" }) => (
  <span style={{ display:"inline-block", padding:"3px 10px", borderRadius:99, fontSize:11, background:color+"22", color, border:`1px solid ${color}44`, marginRight:4, marginBottom:4 }}>{text}</span>
);

const statusColor = s => ({
  "Applied":"#8B5CF6","Technical Round 2":"#06b6d4","Manager Round":"#f59e0b",
  "Screening":"#4ade80","Rejected":"#f87171","Offered":"#4ade80",
}[s]||"#888");

const matchColor = m => m >= 90 ? "#4ade80" : m >= 80 ? "#f59e0b" : m >= 70 ? "#fb923c" : "#94a3b8";

// ─── LIVE JOB FEED PANEL ─────────────────────────────────────────────────────
const PORTALS_BY_CATEGORY = {
  All: ["LinkedIn Jobs", "Naukri.com", "Indeed", "Glassdoor Jobs", "Dice", "We Work Remotely", "CNCF Job Board"],
  Indian: [
    "Naukri.com", "Foundit (formerly Monster India)", "TimesJobs", "Shine", 
    "Freshersworld", "Cutshort", "Hirect", "Instahyre", "IIMJobs", "Hirist"
  ],
  Global: [
    "LinkedIn Jobs", "Indeed", "Glassdoor Jobs", "ZipRecruiter", 
    "CareerBuilder", "SimplyHired", "Dice"
  ],
  Remote: [
    "Wellfound (AngelList)", "Remote OK", "We Work Remotely", "FlexJobs", 
    "Remotive", "Working Nomads"
  ],
  "DevOps/Cloud": [
    "DevOps Jobs", "Cloud Careers Hub", "Linux Foundation Jobs", "CNCF Job Board"
  ]
};

const getPostAgeInDays = (postedAgo, createdAtStr) => {
  if (!postedAgo) return 0;
  // Normalize "a " or "an " to "1 " to handle "a day ago", "an hour ago" etc.
  const text = postedAgo.toLowerCase().trim().replace(/\b(a|an)\b/g, "1");
  
  if (text === "recently" || text === "time-ago") {
    return 5;
  }
  
  if (text.includes("just now") || text.includes("today") || text === "active") {
    return 0;
  }
  
  // Try to parse relative patterns like "2 hours ago" or "5 days ago"
  const match = text.match(/(\d+)\s*(hour|hr|h|day|dy|d|week|wk|w|month|mo|m|year|yr|y)s?/);
  if (match) {
    const value = parseInt(match[1], 10);
    const unit = match[2];
    if (unit.startsWith("h")) return value / 24;
    if (unit.startsWith("d")) return value;
    if (unit.startsWith("w")) return value * 7;
    if (unit.startsWith("m")) return value * 30;
    if (unit.startsWith("y")) return value * 365;
  }
  
  // Try to parse absolute date strings (e.g. "Apr 13, 2026")
  const parsedDate = Date.parse(postedAgo);
  if (!isNaN(parsedDate)) {
    const diffMs = new Date() - new Date(parsedDate);
    const ageInDays = diffMs / (1000 * 60 * 60 * 24);
    return Math.max(0, ageInDays);
  }
  
  // Fallback to 5 days if we don't have any date info, rather than polluting 24h
  return 5;
};

const LiveJobFeed = ({ 
  jobs, 
  setJobs, 
  onApply, 
  appliedIds, 
  fetchJobs, 
  systemStatus,
  selectedCategory,
  setSelectedCategory,
  selectedPortals,
  setSelectedPortals,
  minMatch,
  setMinMatch,
  search,
  setSearch,
  timeFilter,
  setTimeFilter,
  sortBy,
  setSortBy,
  portalsSummary = [],
  setPortalsSummary,
  scanning,
  setScanning
}) => {
  const [detailTab, setDetailTab] = useState("desc");
  const [stagedSearch, setStagedSearch] = useState(search); // Staged search input value
  const [selectedJob, setSelectedJob] = useState(null);
  const [applyingId, setApplyingId] = useState(null);
  const [applyLog, setApplyLog] = useState([]);
  const [savedIds, setSavedIds] = useState([]);
  const [scanProgress, setScanProgress] = useState(0);
  const [newJobCount, setNewJobCount] = useState(0);
  
  // Dropdown UI States
  const [activeDropdown, setActiveDropdown] = useState(null); // null, 'date', 'match', 'portal', 'category', 'sort'
  const [portalSearch, setPortalSearch] = useState("");
  const filterBarRef = useRef(null);

  // Staged values for LinkedIn/Naukri filter apply flow
  const [stagedTimeFilter, setStagedTimeFilter] = useState(timeFilter);
  const [stagedMinMatch, setStagedMinMatch] = useState(minMatch);
  const [stagedPortals, setStagedPortals] = useState(selectedPortals);
  const [stagedCategory, setStagedCategory] = useState(selectedCategory);
  const [stagedSortBy, setStagedSortBy] = useState(sortBy);

  const logRef = useRef(null);

  const fetchLogs = useCallback(async () => {
    try {
      const res = await fetch(API_BASE + "/logs");
      if (res.ok) {
        const data = await res.json();
        const mapped = data.map(l => {
          let color = "#8B5CF6";
          if (l.status === "failed") color = "#f87171";
          else if (l.type === "apply") color = "#4ade80";
          else if (l.type === "scrape") color = "#06b6d4";
          return { ts: l.ts, text: l.desc, color };
        });
        setApplyLog(mapped);
      }
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, [fetchLogs]);

  useEffect(() => {
    if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
  }, [applyLog]);

  // Click outside filter bar to close dropdowns
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (filterBarRef.current && !filterBarRef.current.contains(e.target)) {
        setActiveDropdown(null);
      }
    };
    document.addEventListener("mousedown", handleOutsideClick);
    return () => document.removeEventListener("mousedown", handleOutsideClick);
  }, []);

  const toggleDropdown = (type) => {
    if (activeDropdown === type) {
      setActiveDropdown(null);
    } else {
      setActiveDropdown(type);
    }
  };

  const applyAllFilters = (overrides = {}) => {
    const nextTime = overrides.hasOwnProperty('timeFilter') ? overrides.timeFilter : stagedTimeFilter;
    const nextMatch = overrides.hasOwnProperty('minMatch') ? overrides.minMatch : stagedMinMatch;
    const nextPortals = overrides.hasOwnProperty('selectedPortals') ? overrides.selectedPortals : stagedPortals;
    const nextCat = overrides.hasOwnProperty('selectedCategory') ? overrides.selectedCategory : stagedCategory;
    const nextSort = overrides.hasOwnProperty('sortBy') ? overrides.sortBy : stagedSortBy;
    const nextSearch = overrides.hasOwnProperty('search') ? overrides.search : stagedSearch;

    setTimeFilter(nextTime);
    setMinMatch(nextMatch);
    setSelectedPortals(nextPortals);
    setSelectedCategory(nextCat);
    setSortBy(nextSort);
    setSearch(nextSearch);

    // Sync staged state back
    setStagedTimeFilter(nextTime);
    setStagedMinMatch(nextMatch);
    setStagedPortals(nextPortals);
    setStagedCategory(nextCat);
    setStagedSortBy(nextSort);
    setStagedSearch(nextSearch);

    setActiveDropdown(null);
  };

  const isFiltersDirty = () => {
    return stagedTimeFilter !== timeFilter ||
           stagedMinMatch !== minMatch ||
           stagedPortals.length !== selectedPortals.length ||
           stagedPortals.some(p => !selectedPortals.includes(p)) ||
           stagedCategory !== selectedCategory ||
           stagedSortBy !== sortBy ||
           stagedSearch !== search;
  };

  const getFilteredCount = (customFilters = {}) => {
    const fSearch = customFilters.hasOwnProperty('search') ? customFilters.search : stagedSearch;
    const fTime = customFilters.hasOwnProperty('timeFilter') ? customFilters.timeFilter : stagedTimeFilter;
    const fMinMatch = customFilters.hasOwnProperty('minMatch') ? customFilters.minMatch : stagedMinMatch;
    const fPortals = customFilters.hasOwnProperty('selectedPortals') ? customFilters.selectedPortals : stagedPortals;
    const fCategory = customFilters.hasOwnProperty('selectedCategory') ? customFilters.selectedCategory : stagedCategory;

    return jobs.filter(j => {
      if (typeof j.id === "number") return false;
      
      // Portal Filter
      if (fPortals.length > 0) {
        if (!fPortals.includes(j.portal)) return false;
      } else {
        if (fCategory !== "All") {
          const catPortals = PORTALS_BY_CATEGORY[fCategory] || [];
          if (!catPortals.includes(j.portal)) return false;
        }
      }
      
      // Min match
      if (!(j.match >= fMinMatch)) return false;
      
      // Time filter
      if (fTime !== "all") {
        const postAgeInDays = getPostAgeInDays(j.postedAgo || j.posted_ago, j.created_at);
        if (fTime === "1" && postAgeInDays > 1) return false;
        if (fTime === "3" && postAgeInDays > 3) return false;
        if (fTime === "7" && postAgeInDays > 7) return false;
        if (fTime === "15" && postAgeInDays > 15) return false;
        if (fTime === "30" && postAgeInDays > 30) return false;
      }
      
      // Search
      if (fSearch) {
        const query = fSearch.toLowerCase().trim();
        const portalMatch = j.portal?.toLowerCase().includes(query) ||
                            ((query.includes("nauk") || query.includes("naukar")) && j.portal === "Naukri.com") ||
                            ((query.includes("link") || query.includes("linked")) && j.portal === "LinkedIn Jobs");
        const titleMatch = j.title?.toLowerCase().includes(query);
        const companyMatch = j.company?.toLowerCase().includes(query);
        const tagMatch = j.tags?.some(t => t.toLowerCase().includes(query));
        if (!titleMatch && !companyMatch && !tagMatch && !portalMatch) return false;
      }
      
      return true;
    }).length;
  };

  const hasActiveFilters = () => {
    return timeFilter !== "all" || minMatch !== 70 || selectedPortals.length > 0 || selectedCategory !== "All" || sortBy !== "match" || search !== "" ||
           stagedTimeFilter !== "all" || stagedMinMatch !== 70 || stagedPortals.length > 0 || stagedCategory !== "All" || stagedSortBy !== "match" || stagedSearch !== "";
  };

  const clearAllFilters = () => {
    setTimeFilter("all");
    setMinMatch(70);
    setSelectedPortals([]);
    setSelectedCategory("All");
    setSortBy("match");
    setSearch("");

    setStagedTimeFilter("all");
    setStagedMinMatch(70);
    setStagedPortals([]);
    setStagedCategory("All");
    setStagedSortBy("match");
    setStagedSearch("");

    setActiveDropdown(null);
  };

  const getTimeFilterLabel = (val) => {
    switch (val) {
      case "1": return "Last 24h";
      case "3": return "Last 3 days";
      case "7": return "Last 7 days";
      case "15": return "Last 15 days";
      case "30": return "Last 30 days";
      default: return "All Time";
    }
  };

  const getSortLabel = (val) => {
    switch (val) {
      case "recent": return "Most Recent";
      case "company": return "Company A-Z";
      default: return "Best Match";
    }
  };

  const uniquePortals = Array.from(new Set(jobs.map(j => j.portal))).filter(Boolean);

  const portals = ["All", ...(PORTALS_BY_CATEGORY[selectedCategory] || [])];

  const filtered = jobs
    .filter(j => typeof j.id !== "number")
    .filter(j => {
      if (selectedPortals.length > 0) {
        return selectedPortals.includes(j.portal);
      }
      if (selectedCategory === "All") return true;
      const catPortals = PORTALS_BY_CATEGORY[selectedCategory] || [];
      return catPortals.includes(j.portal);
    })
    .filter(j => j.match >= minMatch)
    .filter(j => {
      if (timeFilter === "all") return true;
      const postAgeInDays = getPostAgeInDays(j.postedAgo || j.posted_ago, j.created_at);
      if (timeFilter === "1") return postAgeInDays <= 1;
      if (timeFilter === "3") return postAgeInDays <= 3;
      if (timeFilter === "7") return postAgeInDays <= 7;
      if (timeFilter === "15") return postAgeInDays <= 15;
      if (timeFilter === "30") return postAgeInDays <= 30;
      return true;
    })
    .filter(j => {
      if (!search) return true;
      const query = search.toLowerCase().trim();
      const portalMatch = j.portal?.toLowerCase().includes(query) ||
                          ((query.includes("nauk") || query.includes("naukar")) && j.portal === "Naukri.com") ||
                          ((query.includes("link") || query.includes("linked")) && j.portal === "LinkedIn Jobs");
      return j.title?.toLowerCase().includes(query) || 
             j.company?.toLowerCase().includes(query) || 
             j.tags?.some(t => t.toLowerCase().includes(query)) ||
             portalMatch;
    })
    .sort((a, b) => sortBy === "match" ? b.match - a.match : sortBy === "recent" ? (b.created_at || "").localeCompare(a.created_at || "") : a.company.localeCompare(b.company));

  const runScan = async () => {
    setScanning(true); 
    setScanProgress(0); 
    setNewJobCount(0);
    try {
      const queryParam = selectedPortals.length === 1 ? `?portal=${encodeURIComponent(selectedPortals[0])}` : "";
      await fetch(API_BASE + "/jobs/scan" + queryParam, { method: "POST" });
    } catch (e) {
      console.error(e);
    }
    
    // Poll for portal scan progress
    let completedCount = 0;
    const pollInterval = setInterval(async () => {
      try {
        const res = await fetch(API_BASE + "/jobs/portals");
        if (res.ok) {
          const data = await res.json();
          setPortalsSummary(data);
          
          const activeScanPortals = selectedPortals.length === 1
            ? data.filter(p => p.portal === selectedPortals[0])
            : data;
            
          const running = activeScanPortals.filter(p => p.status === "running");
          const completed = activeScanPortals.filter(p => p.status === "success" || p.status === "failed");
          
          completedCount = completed.length;
          const totalCount = activeScanPortals.length;
          
          const progress = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 100;
          setScanProgress(progress);
          
          if (running.length === 0) {
            clearInterval(pollInterval);
            await fetchLogs();
            await fetchJobs();
            setScanning(false);
          }
        }
      } catch (err) {
        console.error("Error polling portal statuses:", err);
      }
    }, 1500);
  };

  const applyToJob = async (job) => {
    setApplyingId(job.id);
    try {
      await fetch(API_BASE + `/jobs/apply/${job.id}`, { method: "POST" });
      onApply(job);
      await fetchJobs();
      if (selectedJob?.id === job.id) setSelectedJob({ ...job, applied: true });
    } catch(e) {
      console.error(e);
    }
    setApplyingId(null);
  };

  const copyLink = (url) => {
    navigator.clipboard.writeText(url);
    alert("Job Link Copied!");
  };

  const shareLink = (job) => {
    if (navigator.share) {
      navigator.share({
        title: job.title,
        text: `AWS DevOps Job: ${job.title} at ${job.company}`,
        url: job.url
      }).catch(console.error);
    } else {
      copyLink(job.url);
    }
  };

  const toggleSave = async (job) => {
    const isSaved = savedIds.includes(job.id);
    try {
      await fetch(API_BASE + `/jobs/save/${job.id}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: !isSaved })
      });
      setSavedIds(prev => !isSaved ? [...prev, job.id] : prev.filter(x => x !== job.id));
      await fetchJobs();
    } catch(e) {
      console.error(e);
    }
  };

  // Dynamically calculate stats based on available unique portals in categories or jobs
  const statPortals = portals.slice(1);
  const portalStats = statPortals.map(p => {
    const summary = portalsSummary.find(s => s.portal === p);
    return {
      name: p,
      total: jobs.filter(j => j.portal === p).length,
      applied: [...appliedIds, ...jobs.filter(j=>j.applied).map(j=>j.id)].filter(id => jobs.find(j=>j.id===id)?.portal===p).length,
      meta: getPortalMeta(p),
      status: summary ? summary.status : "idle",
      lastScanTime: summary ? summary.last_scan_time : null,
      duration: summary ? summary.duration : 0.0,
      errorMessage: summary ? summary.error_message : null
    };
  });

  // Reusable popover card style definitions
  const dropdownCardStyle = {
    position: "absolute",
    top: "calc(100% + 8px)",
    left: 0,
    background: "var(--card-bg)",
    border: "1px solid var(--border)",
    borderRadius: 12,
    padding: "16px",
    zIndex: 100,
    minWidth: 240,
    boxShadow: "0 10px 25px -5px rgba(0, 0, 0, 0.5), 0 8px 10px -6px rgba(0, 0, 0, 0.5)",
    display: "flex",
    flexDirection: "column",
    gap: 12,
  };

  const dropdownTitleStyle = {
    fontSize: 12,
    fontWeight: 700,
    color: "var(--text)",
    borderBottom: "1px solid var(--border)",
    paddingBottom: 6,
    marginBottom: 4,
  };

  const dropdownLabelStyle = {
    display: "flex",
    alignItems: "center",
    gap: 8,
    cursor: "pointer",
    padding: "4px 0",
    userSelect: "none",
  };

  const dropdownFooterStyle = {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderTop: "1px solid var(--border)",
    paddingTop: 10,
    marginTop: 6,
  };

  const resetBtnStyle = {
    background: "transparent",
    border: "none",
    color: "var(--muted)",
    cursor: "pointer",
    fontSize: 11,
    fontWeight: 600,
    padding: "4px 8px",
  };

  const applyBtnStyle = {
    background: "var(--accent)",
    border: "none",
    color: "#fff",
    cursor: "pointer",
    fontSize: 11,
    fontWeight: 700,
    padding: "6px 12px",
    borderRadius: 6,
  };

  // Dropdown renderers
  const renderDateDropdown = () => {
    const options = [
      { value: "all", label: "Any time" },
      { value: "1", label: "Last 24 hours" },
      { value: "3", label: "Last 3 days" },
      { value: "7", label: "Last 7 days (Past Week)" },
      { value: "15", label: "Last 15 days" },
      { value: "30", label: "Last 30 days (Past Month)" }
    ];
    const count = getFilteredCount({ timeFilter: stagedTimeFilter });

    return (
      <div style={dropdownCardStyle}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <span style={dropdownTitleStyle}>Date Posted (Freshness)</span>
          {options.map(opt => (
            <label key={opt.value} style={dropdownLabelStyle}>
              <input 
                type="radio" 
                name="timeFilter" 
                value={opt.value} 
                checked={stagedTimeFilter === opt.value}
                onChange={() => setStagedTimeFilter(opt.value)}
                style={{ accentColor: "var(--accent)" }}
              />
              <span style={{ fontSize: 12, color: "var(--text)" }}>{opt.label}</span>
            </label>
          ))}
        </div>
        <div style={dropdownFooterStyle}>
          <button onClick={() => setStagedTimeFilter("all")} style={resetBtnStyle}>Reset</button>
          <button 
            onClick={() => {
              applyAllFilters({ timeFilter: stagedTimeFilter });
            }} 
            style={applyBtnStyle}
          >
            Show {count} results
          </button>
        </div>
      </div>
    );
  };

  const renderMatchDropdown = () => {
    const quickRanges = [50, 70, 80, 90];
    const count = getFilteredCount({ minMatch: stagedMinMatch });

    return (
      <div style={dropdownCardStyle}>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <span style={dropdownTitleStyle}>Minimum Match Score</span>
          
          <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
            {quickRanges.map(val => (
              <button
                key={val}
                onClick={() => setStagedMinMatch(val)}
                style={{
                  padding: "4px 8px",
                  borderRadius: 6,
                  fontSize: 10,
                  fontWeight: 600,
                  cursor: "pointer",
                  background: stagedMinMatch === val ? "var(--accent)" : "var(--surface)",
                  color: stagedMinMatch === val ? "#fff" : "var(--text)",
                  border: `1px solid ${stagedMinMatch === val ? "transparent" : "var(--border)"}`
                }}
              >
                {val}%+
              </button>
            ))}
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 4, marginTop: 4 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: "var(--muted)" }}>
              <span>Min match: {stagedMinMatch}%</span>
              <span>95%</span>
            </div>
            <input 
              type="range" 
              min={50} 
              max={95} 
              step={5} 
              value={stagedMinMatch} 
              onChange={e=>setStagedMinMatch(+e.target.value)} 
              style={{ width: "100%", accentColor: "var(--accent)", cursor: "pointer" }}
            />
          </div>
        </div>
        <div style={dropdownFooterStyle}>
          <button onClick={() => setStagedMinMatch(70)} style={resetBtnStyle}>Reset</button>
          <button 
            onClick={() => {
              applyAllFilters({ minMatch: stagedMinMatch });
            }} 
            style={applyBtnStyle}
          >
            Show {count} results
          </button>
        </div>
      </div>
    );
  };

  const renderPortalDropdown = () => {
    const filteredUniquePortals = uniquePortals.filter(p => 
      p.toLowerCase().includes(portalSearch.toLowerCase())
    );
    const count = getFilteredCount({ selectedPortals: stagedPortals });

    const handlePortalToggle = (p) => {
      setStagedPortals(prev => 
        prev.includes(p) ? prev.filter(x => x !== p) : [...prev, p]
      );
    };

    return (
      <div style={{ ...dropdownCardStyle, minWidth: 260 }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          <span style={dropdownTitleStyle}>Job Boards & Portals</span>
          
          <input 
            value={portalSearch}
            onChange={e => setPortalSearch(e.target.value)}
            placeholder="Search job boards..."
            style={{
              background: "var(--surface)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              padding: "6px 10px",
              fontSize: 11,
              color: "var(--text)",
              width: "100%"
            }}
          />

          <div style={{ display: "flex", gap: 8, borderBottom: "1px solid var(--border)", paddingBottom: 6 }}>
            <button 
              type="button"
              onClick={() => setStagedPortals([])} 
              style={{ background: "transparent", border: "none", color: "var(--accent)", cursor: "pointer", fontSize: 10, fontWeight: 700 }}
            >
              Deselect all
            </button>
            <span style={{ color: "var(--border)", fontSize: 10 }}>|</span>
            <button 
              type="button"
              onClick={() => setStagedPortals(uniquePortals)} 
              style={{ background: "transparent", border: "none", color: "var(--accent)", cursor: "pointer", fontSize: 10, fontWeight: 700 }}
            >
              Select all
            </button>
          </div>

          <div style={{ maxHeight: 180, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6, paddingRight: 4 }}>
            {filteredUniquePortals.map(p => (
              <label key={p} style={dropdownLabelStyle}>
                <input 
                  type="checkbox" 
                  checked={stagedPortals.includes(p)}
                  onChange={() => handlePortalToggle(p)}
                  style={{ accentColor: "var(--accent)" }}
                />
                <span style={{ fontSize: 11, color: "var(--text)" }}>{p}</span>
              </label>
            ))}
            {filteredUniquePortals.length === 0 && (
              <span style={{ fontSize: 11, color: "var(--muted)", textAlign: "center", padding: "10px 0" }}>No portals found</span>
            )}
          </div>
        </div>

        <div style={dropdownFooterStyle}>
          <button 
            onClick={() => {
              setStagedPortals([]);
              setPortalSearch("");
            }} 
            style={resetBtnStyle}
          >
            Reset
          </button>
          <button 
            onClick={() => {
              applyAllFilters({ selectedPortals: stagedPortals });
              setPortalSearch("");
            }} 
            style={applyBtnStyle}
          >
            Show {count} results
          </button>
        </div>
      </div>
    );
  };

  const renderCategoryDropdown = () => {
    const categories = ["All", "Indian", "Global", "Remote", "DevOps/Cloud"];
    const count = getFilteredCount({ selectedPortals: [], selectedCategory: stagedCategory });

    return (
      <div style={dropdownCardStyle}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <span style={dropdownTitleStyle}>Job Scope / Region</span>
          {categories.map(cat => (
            <label key={cat} style={dropdownLabelStyle}>
              <input 
                type="radio" 
                name="categoryFilter" 
                value={cat} 
                checked={stagedCategory === cat}
                onChange={() => setStagedCategory(cat)}
                style={{ accentColor: "var(--accent)" }}
              />
              <span style={{ fontSize: 12, color: "var(--text)" }}>{cat} {cat !== "All" ? "Portals" : "Scope"}</span>
            </label>
          ))}
        </div>
        <div style={dropdownFooterStyle}>
          <button onClick={() => setStagedCategory("All")} style={resetBtnStyle}>Reset</button>
          <button 
            onClick={() => {
              applyAllFilters({ selectedCategory: stagedCategory, selectedPortals: [] });
            }} 
            style={applyBtnStyle}
          >
            Show {count} results
          </button>
        </div>
      </div>
    );
  };

  const renderSortDropdown = () => {
    const sortOpts = [
      { value: "match", label: "Best Match Score" },
      { value: "recent", label: "Most Recent Postings" },
      { value: "company", label: "Company Name A-Z" }
    ];
    const count = getFilteredCount({ sortBy: stagedSortBy });

    return (
      <div style={dropdownCardStyle}>
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <span style={dropdownTitleStyle}>Sort Results By</span>
          {sortOpts.map(opt => (
            <label key={opt.value} style={dropdownLabelStyle}>
              <input 
                type="radio" 
                name="sortFilter" 
                value={opt.value} 
                checked={stagedSortBy === opt.value}
                onChange={() => setStagedSortBy(opt.value)}
                style={{ accentColor: "var(--accent)" }}
              />
              <span style={{ fontSize: 12, color: "var(--text)" }}>{opt.label}</span>
            </label>
          ))}
        </div>
        <div style={dropdownFooterStyle}>
          <button onClick={() => setStagedSortBy("match")} style={resetBtnStyle}>Reset</button>
          <button 
            onClick={() => {
              applyAllFilters({ sortBy: stagedSortBy });
            }} 
            style={applyBtnStyle}
          >
            Show {count} results
          </button>
        </div>
      </div>
    );
  };

  return (
    <div style={{ display:"flex", flexDirection:"column", gap:16 }}>

      {/* Portal Stats Strip */}
      <div style={{ display:"grid", gridTemplateColumns:"repeat(auto-fit,minmax(150px,1fr))", gap:10 }}>
        {portalStats.map(ps => {
          const isSelected = selectedPortals.includes(ps.name);
          
          let statusText = "";
          let statusColor = "var(--muted)";
          let isPulse = false;
          
          if (ps.status === "running") {
            statusText = "⏳ Scanning...";
            statusColor = "#8B5CF6";
            isPulse = true;
          } else if (ps.status === "failed") {
            statusText = "⚠️ Failed";
            statusColor = "#f87171";
          } else if (ps.status === "success" && ps.duration > 0) {
            statusText = `✓ ${ps.duration}s`;
            statusColor = "#4ade80";
          } else if (ps.lastScanTime) {
            try {
              const dt = new Date(ps.lastScanTime);
              statusText = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            } catch {
              statusText = "";
            }
          }

          return (
            <div 
              key={ps.name} 
              onClick={() => {
                const nextPortals = selectedPortals.includes(ps.name)
                  ? selectedPortals.filter(x => x !== ps.name)
                  : [...selectedPortals, ps.name];
                applyAllFilters({ selectedPortals: nextPortals });
              }} 
              title={ps.errorMessage ? `Error: ${ps.errorMessage}` : `Source: ${ps.name}`}
              style={{ 
                background:"var(--card-bg)", 
                border:`1px solid ${isSelected ? ps.meta.color : ps.status === "failed" ? "#f87171" : "var(--border)"}`, 
                borderRadius:12, 
                padding:"12px 14px", 
                cursor:"pointer", 
                transition:"all 0.2s",
                position: "relative",
                animation: isPulse ? "pulse 2s infinite" : "none"
              }}
            >
              <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:6 }}>
                <div style={{ width:28, height:28, borderRadius:7, background:ps.meta.bg, border:`1px solid ${ps.meta.color}44`, display:"flex", alignItems:"center", justifyContent:"center", fontSize:11, fontWeight:800, color:ps.meta.color }}>{ps.meta.icon}</div>
                <span style={{ fontSize:13, fontWeight:600, color:"var(--text)" }}>{ps.name}</span>
              </div>
              <div style={{ display:"flex", justifyContent:"space-between", fontSize:11 }}>
                <span style={{ color:"var(--muted)" }}>{ps.total} jobs</span>
                <span style={{ color: statusColor, fontWeight: ps.status !== "idle" ? 700 : 400 }}>{statusText || `${ps.applied} applied`}</span>
              </div>
              {ps.status === "failed" && ps.errorMessage && (
                <div style={{ fontSize: 9, color: "#f87171", textOverflow: "ellipsis", overflow: "hidden", whiteSpace: "nowrap", marginTop: 4 }}>
                  {ps.errorMessage}
                </div>
              )}
              <div style={{ marginTop:6, height:3, background:"var(--border)", borderRadius:99 }}>
                <div style={{ height:"100%", width:`${ps.total ? (ps.applied/ps.total)*100 : 0}%`, background:ps.meta.color, borderRadius:99 }}/>
              </div>
            </div>
          );
        })}
        {/* Scan button card */}
        <div style={{ background:"var(--card-bg)", border:"1px solid var(--border)", borderRadius:12, padding:"12px 14px", display:"flex", flexDirection:"column", justifyContent:"space-between" }}>
          <div style={{ fontSize:11, color:"var(--muted)", marginBottom:6 }}>Live Scanner</div>
          {scanning ? (
            <div>
              <div style={{ fontSize:12, color:"#8B5CF6", marginBottom:6 }}>Scanning... {scanProgress}%</div>
              <div style={{ height:4, background:"var(--border)", borderRadius:99 }}>
                <div style={{ height:"100%", width:`${scanProgress}%`, background:"linear-gradient(90deg,#8B5CF6,#06b6d4)", borderRadius:99, transition:"width 0.3s ease" }}/>
              </div>
            </div>
          ) : (
            <button onClick={runScan} style={{ padding:"8px 0", borderRadius:9, background:"linear-gradient(135deg,#8B5CF6,#06b6d4)", color:"#fff", border:"none", cursor:"pointer", fontSize:12, fontWeight:700 }}>
              {newJobCount > 0 ? `🆕 ${newJobCount} New Found` : "▶ Scan Now"}
            </button>
          )}
        </div>
      </div>

      <div style={{ display:"grid", gridTemplateColumns:"1fr 380px", gap:16 }}>
        {/* Job List */}
        <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
          
          {/* LinkedIn & Naukri Style Interactive Filters Bar */}
          <div ref={filterBarRef} style={{ display:"flex", flexDirection:"column", gap:10, background:"var(--surface)", border:"1px solid var(--border)", borderRadius:12, padding:12, width:"100%", position:"relative", zIndex:20 }}>
            <div style={{ display:"flex", flexWrap:"wrap", gap:8, alignItems:"center" }}>
              
              {/* Search Bar Container */}
              <div style={{ display:"flex", alignItems:"center", flex:"1 1 200px", background:"var(--card-bg)", border:"1px solid var(--border)", borderRadius:10, padding:"4px 10px" }}>
                <span style={{ fontSize:14, color:"var(--muted)", marginRight:6 }}>🔍</span>
                <input 
                  value={stagedSearch} 
                  onChange={e=>setStagedSearch(e.target.value)} 
                  placeholder="Search titles, companies, tags..." 
                  style={{ flex:1, background:"transparent", border:"none", fontSize:12, color:"var(--text)", padding:"4px 0" }}
                  onKeyDown={e => {
                    if (e.key === "Enter") {
                      applyAllFilters();
                    }
                  }}
                />
                {stagedSearch && (
                  <button 
                    onClick={() => {
                      setStagedSearch("");
                      applyAllFilters({ search: "" });
                    }} 
                    style={{ background:"transparent", border:"none", color:"var(--muted)", fontSize:12, cursor:"pointer", padding:"0 4px" }}
                  >
                    ✕
                  </button>
                )}
              </div>

              {/* Filter Pills */}
              <div style={{ display:"flex", flexWrap:"wrap", gap:6, alignItems:"center", position:"relative" }}>
                
                {/* Date Posted Pill */}
                <div style={{ position:"relative" }}>
                  <button 
                    onClick={() => toggleDropdown("date")}
                    style={{
                      padding: "8px 12px",
                      borderRadius: 20,
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      transition: "all 0.2s",
                      background: stagedTimeFilter !== "all" ? "var(--accent)" : "var(--card-bg)",
                      color: stagedTimeFilter !== "all" ? "#fff" : "var(--text)",
                      border: `1px solid ${stagedTimeFilter !== "all" ? "transparent" : "var(--border)"}`
                    }}
                  >
                    <span>Date Posted{stagedTimeFilter !== "all" ? `: ${getTimeFilterLabel(stagedTimeFilter)}` : ""}</span>
                    <span>▾</span>
                  </button>
                  {activeDropdown === "date" && renderDateDropdown()}
                </div>

                {/* Min Match Score Pill */}
                <div style={{ position:"relative" }}>
                  <button 
                    onClick={() => toggleDropdown("match")}
                    style={{
                      padding: "8px 12px",
                      borderRadius: 20,
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      transition: "all 0.2s",
                      background: stagedMinMatch !== 70 ? "var(--accent)" : "var(--card-bg)",
                      color: stagedMinMatch !== 70 ? "#fff" : "var(--text)",
                      border: `1px solid ${stagedMinMatch !== 70 ? "transparent" : "var(--border)"}`
                    }}
                  >
                    <span>Match Score{stagedMinMatch !== 70 ? `: ${stagedMinMatch}%+` : ""}</span>
                    <span>▾</span>
                  </button>
                  {activeDropdown === "match" && renderMatchDropdown()}
                </div>

                {/* Job Portals Pill */}
                <div style={{ position:"relative" }}>
                  <button 
                    onClick={() => toggleDropdown("portal")}
                    style={{
                      padding: "8px 12px",
                      borderRadius: 20,
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      transition: "all 0.2s",
                      background: stagedPortals.length > 0 ? "var(--accent)" : "var(--card-bg)",
                      color: stagedPortals.length > 0 ? "#fff" : "var(--text)",
                      border: `1px solid ${stagedPortals.length > 0 ? "transparent" : "var(--border)"}`
                    }}
                  >
                    <span>Portals{stagedPortals.length > 0 ? `: ${stagedPortals.length}` : ""}</span>
                    <span>▾</span>
                  </button>
                  {activeDropdown === "portal" && renderPortalDropdown()}
                </div>

                {/* Category Pill */}
                <div style={{ position:"relative" }}>
                  <button 
                    onClick={() => toggleDropdown("category")}
                    style={{
                      padding: "8px 12px",
                      borderRadius: 20,
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      transition: "all 0.2s",
                      background: stagedCategory !== "All" ? "var(--accent)" : "var(--card-bg)",
                      color: stagedCategory !== "All" ? "#fff" : "var(--text)",
                      border: `1px solid ${stagedCategory !== "All" ? "transparent" : "var(--border)"}`
                    }}
                  >
                    <span>Category{stagedCategory !== "All" ? `: ${stagedCategory}` : ""}</span>
                    <span>▾</span>
                  </button>
                  {activeDropdown === "category" && renderCategoryDropdown()}
                </div>

                {/* Sort By Pill */}
                <div style={{ position:"relative" }}>
                  <button 
                    onClick={() => toggleDropdown("sort")}
                    style={{
                      padding: "8px 12px",
                      borderRadius: 20,
                      fontSize: 12,
                      fontWeight: 600,
                      cursor: "pointer",
                      display: "flex",
                      alignItems: "center",
                      gap: 4,
                      transition: "all 0.2s",
                      background: stagedSortBy !== "match" ? "var(--accent)" : "var(--card-bg)",
                      color: stagedSortBy !== "match" ? "#fff" : "var(--text)",
                      border: `1px solid ${stagedSortBy !== "match" ? "transparent" : "var(--border)"}`
                    }}
                  >
                    <span>Sort{stagedSortBy !== "match" ? `: ${getSortLabel(stagedSortBy)}` : ""}</span>
                    <span>▾</span>
                  </button>
                  {activeDropdown === "sort" && renderSortDropdown()}
                </div>

                {/* Apply Filters & Discard Button Container */}
                {isFiltersDirty() && (
                  <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                    <button 
                      onClick={() => applyAllFilters()}
                      style={{
                        background: "linear-gradient(135deg, #8B5CF6, #06b6d4)",
                        color: "#fff",
                        border: "none",
                        fontSize: 12,
                        fontWeight: 700,
                        cursor: "pointer",
                        padding: "8px 16px",
                        borderRadius: 20,
                        boxShadow: "0 0 10px rgba(139, 92, 246, 0.4)",
                        transition: "all 0.2s"
                      }}
                    >
                      Apply Filters
                    </button>
                    <button 
                      onClick={() => {
                        setStagedTimeFilter(timeFilter);
                        setStagedMinMatch(minMatch);
                        setStagedPortals(selectedPortals);
                        setStagedCategory(selectedCategory);
                        setStagedSortBy(sortBy);
                        setStagedSearch(search);
                        setActiveDropdown(null);
                      }}
                      style={{
                        background: "transparent",
                        border: "1px solid var(--border)",
                        color: "var(--muted)",
                        fontSize: 12,
                        fontWeight: 600,
                        cursor: "pointer",
                        padding: "7px 14px",
                        borderRadius: 20,
                        transition: "all 0.2s"
                      }}
                      onMouseOver={e => {
                        e.target.style.background = "var(--border)";
                        e.target.style.color = "var(--text)";
                      }}
                      onMouseOut={e => {
                        e.target.style.background = "transparent";
                        e.target.style.color = "var(--muted)";
                      }}
                    >
                      Discard
                    </button>
                  </div>
                )}

                {/* Clear All Button */}
                {hasActiveFilters() && (
                  <button 
                    onClick={clearAllFilters}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "var(--accent)",
                      fontSize: 12,
                      fontWeight: 700,
                      cursor: "pointer",
                      padding: "6px 10px",
                      borderRadius: 6,
                      transition: "background 0.2s"
                    }}
                    onMouseOver={e=>e.target.style.background="var(--border)"}
                    onMouseOut={e=>e.target.style.background="transparent"}
                  >
                    Clear all
                  </button>
                )}
              </div>
            </div>
          </div>

          <div style={{ fontSize:11, color:"var(--muted)" }}>{filtered.length} jobs found · {filtered.filter(j=>j.applied||appliedIds.includes(j.id)).length} applied</div>

          {/* Job Cards */}
          <div style={{ display:"flex", flexDirection:"column", gap:8, maxHeight:520, overflowY:"auto", paddingRight:4 }}>
            {filtered.map(job => {
              const isApplied = job.applied || appliedIds.includes(job.id);
              const isSaved = savedIds.includes(job.id);
              const pm = getPortalMeta(job.portal);
              const isNew = job.postedAgo === "Just now";
              return (
                <div key={job.id} onClick={() => setSelectedJob(job)} style={{ background: selectedJob?.id===job.id ? "#8B5CF610" : "var(--card-bg)", border:`1px solid ${selectedJob?.id===job.id ? "#8B5CF666":"var(--border)"}`, borderRadius:12, padding:"13px 15px", cursor:"pointer", transition:"all 0.15s", opacity: isApplied ? 0.75 : 1 }}>
                  <div style={{ display:"flex", alignItems:"flex-start", gap:10 }}>
                    {/* Match ring */}
                    <div style={{ flexShrink:0, width:44, height:44, borderRadius:"50%", background:`${matchColor(job.match)}18`, border:`2px solid ${matchColor(job.match)}`, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center" }}>
                      <span style={{ fontSize:11, fontWeight:800, color:matchColor(job.match), lineHeight:1 }}>{job.match}%</span>
                      <span style={{ fontSize:8, color:matchColor(job.match), opacity:0.7 }}>match</span>
                    </div>
                    <div style={{ flex:1, minWidth:0 }}>
                      <div style={{ display:"flex", alignItems:"center", gap:6, marginBottom:2 }}>
                        <span style={{ fontSize:13, fontWeight:700, color:"var(--text)", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{job.title}</span>
                        {isNew && <span style={{ fontSize:9, padding:"2px 7px", borderRadius:99, background:"#8B5CF6", color:"#fff", flexShrink:0 }}>NEW</span>}
                        {isApplied && <span style={{ fontSize:9, padding:"2px 7px", borderRadius:99, background:"#4ade8022", color:"#4ade80", border:"1px solid #4ade8044", flexShrink:0 }}>✓ Applied</span>}
                      </div>
                      <div style={{ fontSize:12, color:"var(--muted)", marginBottom:5 }}>{job.company} · {job.location}</div>
                      <div style={{ display:"flex", flexWrap:"wrap", gap:4, marginBottom:6 }}>
                        {job.tags.map(t => <span key={t} style={{ fontSize:10, padding:"2px 8px", borderRadius:99, background:"#8B5CF614", color:"#8B5CF6", border:"1px solid #8B5CF630" }}>{t}</span>)}
                      </div>
                      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
                        <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                          <span style={{ fontSize:10, padding:"2px 8px", borderRadius:99, background:pm.bg, color:pm.color, border:`1px solid ${pm.color}33` }}>{job.portal}</span>
                          <span style={{ fontSize:10, color:"var(--muted)" }}>{job.postedAgo}</span>
                          <span style={{ fontSize:10, color:"#4ade80", fontWeight:600 }}>{job.salary}</span>
                        </div>
                        <div style={{ display:"flex", gap:6 }} onClick={e=>e.stopPropagation()}>
                          <button onClick={() => toggleSave(job)} style={{ width:28, height:28, borderRadius:7, background:isSaved?"#f59e0b22":"var(--surface)", border:`1px solid ${isSaved?"#f59e0b44":"var(--border)"}`, cursor:"pointer", fontSize:13, color:isSaved?"#f59e0b":"var(--muted)" }}>
                            {isSaved ? "★" : "☆"}
                          </button>
                          <button onClick={() => shareLink(job)} title="Share or Copy Link" style={{ width:28, height:28, borderRadius:7, background:"var(--surface)", border:"1px solid var(--border)", cursor:"pointer", fontSize:12, color:"var(--muted)" }}>
                            🔗
                          </button>
                          <button onClick={() => applyToJob(job)} disabled={isApplied || applyingId===job.id} style={{ padding:"4px 14px", borderRadius:7, fontSize:11, fontWeight:600, background: isApplied ? "#4ade8022" : "linear-gradient(135deg,#8B5CF6,#06b6d4)", color: isApplied ? "#4ade80" : "#fff", border: isApplied ? "1px solid #4ade8044" : "none", cursor: isApplied ? "default" : "pointer", opacity: applyingId===job.id ? 0.6 : 1 }}>
                            {applyingId===job.id ? "Applying..." : isApplied ? "✓ Applied" : "Auto Apply"}
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
            {filtered.length === 0 && (
              <div style={{ padding:40, textAlign:"center", color:"var(--muted)", fontSize:13 }}>No jobs match your filters. Try lowering the match threshold or changing portal.</div>
            )}
          </div>
        </div>

        {/* Right Panel: Job Detail + Apply Log */}
        <div style={{ display:"flex", flexDirection:"column", gap:12 }}>
          {selectedJob ? (
            <div style={{ background:"var(--card-bg)", border:"1px solid var(--border)", borderRadius:14, padding:16 }}>
              <div style={{ display:"flex", alignItems:"flex-start", justifyContent:"space-between", marginBottom:12 }}>
                <div>
                  <div style={{ fontSize:15, fontWeight:700, color:"var(--text)", marginBottom:3 }}>{selectedJob.title}</div>
                  <div style={{ fontSize:12, color:"var(--muted)" }}>{selectedJob.company}</div>
                  <div style={{ fontSize:11, color:"var(--muted)", marginTop:2 }}>{selectedJob.location}</div>
                </div>
                <div style={{ textAlign:"right" }}>
                  <div style={{ fontSize:22, fontWeight:800, color:matchColor(selectedJob.match) }}>{selectedJob.match}%</div>
                  <div style={{ fontSize:10, color:"var(--muted)" }}>match score</div>
                </div>
              </div>
              <div style={{ display:"flex", gap:8, flexWrap:"wrap", marginBottom:12 }}>
                <span style={{ fontSize:11, padding:"3px 10px", borderRadius:99, background:getPortalMeta(selectedJob.portal).bg, color:getPortalMeta(selectedJob.portal).color, border:`1px solid ${getPortalMeta(selectedJob.portal).color}44` }}>{selectedJob.portal}</span>
                <span style={{ fontSize:11, padding:"3px 10px", borderRadius:99, background:"#4ade8018", color:"#4ade80", border:"1px solid #4ade8033" }}>{selectedJob.salary}</span>
                <span style={{ fontSize:11, padding:"3px 10px", borderRadius:99, background:"var(--surface)", color:"var(--muted)", border:"1px solid var(--border)" }}>{selectedJob.postedAgo}</span>
              </div>
              <div style={{ display:"flex", gap:4, marginBottom:10, borderBottom:"1px solid var(--border)", paddingBottom:6 }}>
                {[["desc","JD Description"],["resume","Tailored Resume"],["letter","Cover Letter"]].map(([t,lbl])=>(
                  <button key={t} onClick={()=>setDetailTab(t)} style={{ padding:"4px 10px", borderRadius:6, fontSize:11, background:detailTab===t?"#8B5CF620":"transparent", border:"none", color:detailTab===t?"#8B5CF6":"var(--muted)", cursor:"pointer", fontWeight:detailTab===t?600:400 }}>{lbl}</button>
                ))}
              </div>
              {detailTab === "desc" && (
                <div style={{ fontSize:12, color:"var(--text)", lineHeight:1.7, marginBottom:12, background:"var(--surface)", borderRadius:8, padding:"10px 12px", maxHeight:240, overflowY:"auto" }}>{selectedJob.description}</div>
              )}
              {detailTab === "resume" && (
                <pre style={{ fontSize:11, color:"var(--text)", lineHeight:1.5, marginBottom:12, background:"var(--surface)", borderRadius:8, padding:"10px 12px", maxHeight:240, overflowY:"auto", fontFamily:"monospace", whiteSpace:"pre-wrap" }}>{selectedJob.resume_customized || "Generating customized resume..."}</pre>
              )}
              {detailTab === "letter" && (
                <pre style={{ fontSize:11, color:"var(--text)", lineHeight:1.5, marginBottom:12, background:"var(--surface)", borderRadius:8, padding:"10px 12px", maxHeight:240, overflowY:"auto", fontFamily:"monospace", whiteSpace:"pre-wrap" }}>{selectedJob.cover_letter || "Generating customized cover letter..."}</pre>
              )}
              <div style={{ marginBottom:12 }}>
                <div style={{ fontSize:11, color:"var(--muted)", marginBottom:6 }}>Required Skills Match</div>
                <div style={{ display:"flex", flexWrap:"wrap", gap:4 }}>
                  {selectedJob.tags.map(t => <span key={t} style={{ fontSize:11, padding:"3px 10px", borderRadius:99, background:"#4ade8018", color:"#4ade80", border:"1px solid #4ade8033" }}>✓ {t}</span>)}
                </div>
              </div>
              <div style={{ display:"flex", gap:8 }}>
                <button onClick={() => applyToJob(selectedJob)} disabled={selectedJob.applied || applyingId===selectedJob.id} style={{ flex:1, padding:"10px", borderRadius:10, background: selectedJob.applied ? "#4ade8022" : "linear-gradient(135deg,#8B5CF6,#06b6d4)", color: selectedJob.applied ? "#4ade80" : "#fff", border: selectedJob.applied ? "1px solid #4ade8044" : "none", cursor: selectedJob.applied ? "default" : "pointer", fontWeight:700, fontSize:13 }}>
                  {applyingId===selectedJob.id ? "⟳ Applying..." : selectedJob.applied ? "✓ Already Applied" : "🚀 Auto Apply Now"}
                </button>
                <button onClick={() => shareLink(selectedJob)} style={{ padding:"10px 14px", borderRadius:10, background:"var(--surface)", border:"1px solid var(--border)", color:"var(--text)", fontSize:12, cursor:"pointer" }}>🔗 Share</button>
                <a href={selectedJob.url} target="_blank" rel="noopener noreferrer" style={{ padding:"10px 14px", borderRadius:10, background:"var(--surface)", border:"1px solid var(--border)", color:"var(--text)", fontSize:12, textDecoration:"none", display:"flex", alignItems:"center" }}>↗ View</a>
              </div>
            </div>
          ) : (
            <div style={{ background:"var(--card-bg)", border:"1px solid var(--border)", borderRadius:14, padding:24, textAlign:"center" }}>
              <div style={{ fontSize:32, marginBottom:8 }}>🎯</div>
              <div style={{ fontSize:13, color:"var(--muted)" }}>Click any job to see details and apply</div>
            </div>
          )}

          {/* Apply Log Terminal */}
          <div style={{ background:"#0d1117", border:"1px solid #30363d", borderRadius:12, overflow:"hidden" }}>
            <div style={{ padding:"7px 12px", background:"#161b22", borderBottom:"1px solid #30363d", display:"flex", gap:5, alignItems:"center" }}>
              {["#ff5f57","#ffbd2e","#28c840"].map(c=><div key={c} style={{width:10,height:10,borderRadius:"50%",background:c}}/>)}
              <span style={{ fontSize:10, color:"#7d8590", marginLeft:6, fontFamily:"monospace" }}>job-scanner — live log</span>
            </div>
            <div ref={logRef} style={{ padding:10, fontFamily:"monospace", fontSize:11, lineHeight:1.7, height:140, overflowY:"auto" }}>
              {applyLog.length === 0 && <div style={{color:"#7d8590"}}>naveen@job-scanner:~$ ready. click "Scan Now" to discover live jobs.</div>}
              {applyLog.map((l,i) => (
                <div key={i} style={{color:l.color}}><span style={{color:"#7d8590"}}>[{l.ts}] </span>{l.text}</div>
              ))}
              <div style={{color:"#8B5CF6", animation:"blink 1s step-end infinite"}}>█</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// ─── DASHBOARD PANEL ─────────────────────────────────────────────────────────
const Dashboard = ({ jobs, tasks, liveJobs, onApply, appliedIds, systemStatus, portalsSummary = [], scanning = false }) => (
  <div>
    {/* Scanner Summary Card */}
    <div style={{ background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 14, padding: "18px 20px", marginBottom: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <h3 style={{ fontSize: 14, fontWeight: 700, margin: 0, color: "var(--text)" }}>📡 Global Job Board Scan Dashboard</h3>
        {scanning ? (
          <span style={{ fontSize: 11, padding: "4px 8px", borderRadius: 6, background: "#8B5CF620", color: "#8B5CF6", fontWeight: 700, animation: "pulse 1.5s infinite" }}>SCANNING IN PROGRESS...</span>
        ) : (
          <span style={{ fontSize: 11, padding: "4px 8px", borderRadius: 6, background: "#4ade8020", color: "#4ade80", fontWeight: 700 }}>SYSTEM IDLE</span>
        )}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))", gap: 12 }}>
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "12px" }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>TOTAL PORTALS</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text)" }}>{portalsSummary.length}</div>
        </div>
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "12px" }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>PORTALS SCANNED</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: "var(--text)" }}>{portalsSummary.filter(p => p.last_scan_time).length}</div>
        </div>
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "12px" }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>TOTAL MATCHING JOBS</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: "#f59e0b" }}>{jobs.length}</div>
        </div>
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "12px" }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>LAST SCAN DURATION</div>
          <div style={{ fontSize: 20, fontWeight: 700, color: "#06b6d4" }}>
            {portalsSummary.filter(p => p.duration > 0).length > 0
              ? `${Math.max(...portalsSummary.map(p => p.duration || 0)).toFixed(1)}s`
              : "0.0s"}
          </div>
        </div>
        <div style={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, padding: "12px" }}>
          <div style={{ fontSize: 11, color: "var(--muted)", marginBottom: 4 }}>LAST SCAN TIMESTAMP</div>
          <div style={{ fontSize: 13, fontWeight: 700, color: "var(--text)", marginTop: 6 }}>
            {(() => {
              const times = portalsSummary.map(p => p.last_scan_time).filter(Boolean);
              if (times.length === 0) return "Never";
              const maxTime = new Date(Math.max(...times.map(t => new Date(t))));
              return maxTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
            })()}
          </div>
        </div>
      </div>
    </div>

    {systemStatus && (
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", background: "var(--card-bg)", border: "1px solid var(--border)", borderRadius: 14, padding: "12px 18px", marginBottom: 16, fontSize: 12 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ color: "#4ade80", animation: "pulse 2s infinite" }}>●</span>
          <span style={{ fontWeight: 600 }}>Automation Agent Active:</span>
          <span style={{ color: "var(--muted)" }}>Checking jobs (1h) | Auto-applying (30m)</span>
        </div>
        <div style={{ display: "flex", gap: 16, color: "var(--muted)" }}>
          <span>Next Job Search: <strong style={{ color: "var(--text)" }}>{systemStatus.next_scan}</strong></span>
          <span>Next Auto-Apply: <strong style={{ color: "var(--text)" }}>{systemStatus.next_apply}</strong></span>
        </div>
      </div>
    )}
    <div style={{ display:"flex", flexWrap:"wrap", gap:12, marginBottom:24 }}>
      <SparkCard label="Total Applied" value={jobs.length + appliedIds.length} delta={18} data={[3,5,4,7,9,jobs.length+appliedIds.length]} color="#8B5CF6"/>
      <SparkCard label="This Month" value={3+appliedIds.length} delta={50} data={[1,1,2,2,2,3+appliedIds.length]} color="#06b6d4"/>
      <SparkCard label="Live Jobs Found" value={liveJobs} delta={12} data={[4,6,8,9,10,liveJobs]} color="#f59e0b"/>
      <SparkCard label="Prep Mastery" value="72%" delta={8} data={[55,60,62,66,70,72]} color="#4ade80"/>
    </div>

    {/* Profile Banner */}
    <div style={{ background:"linear-gradient(135deg,#8B5CF620,#06b6d420)", border:"1px solid var(--border)", borderRadius:14, padding:"18px 22px", marginBottom:24, display:"flex", flexWrap:"wrap", gap:16, alignItems:"center" }}>
      <div style={{ width:52, height:52, borderRadius:"50%", background:"linear-gradient(135deg,#8B5CF6,#06b6d4)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:20, fontWeight:700, color:"#fff", flexShrink:0 }}>NK</div>
      <div style={{ flex:1, minWidth:200 }}>
        <div style={{ fontWeight:700, fontSize:16, color:"var(--text)" }}>Naveen Kumar</div>
        <div style={{ fontSize:13, color:"var(--muted)" }}>AWS DevOps Engineer · 3.8 Years · Yokra / Krify</div>
        <div style={{ fontSize:12, color:"#8B5CF6", marginTop:2 }}>✉ naveendevops589@gmail.com</div>
        <div style={{ marginTop:8 }}>
          {["AWS","EKS","Kubernetes","Terraform","Ansible","Jenkins","Prometheus"].map(t=><Badge key={t} text={t}/>)}
        </div>
      </div>
      <div style={{ textAlign:"right" }}>
        <div style={{ fontSize:11, color:"var(--muted)" }}>Target Companies</div>
        <div style={{ fontSize:13, color:"#006A4E", fontWeight:600 }}>Lloyds Banking</div>
        <div style={{ fontSize:13, color:"#003399", fontWeight:600 }}>Zurich Insurance</div>
      </div>
    </div>

    <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:16, marginBottom:24 }}>
      <div style={{ background:"var(--card-bg)", border:"1px solid var(--border)", borderRadius:14, padding:"16px 18px" }}>
        <div style={{ fontSize:13, fontWeight:600, color:"var(--text)", marginBottom:8 }}>Applications vs Interviews</div>
        <div style={{ display:"flex", gap:16, marginBottom:8, fontSize:11 }}>
          <span style={{color:"#8B5CF6"}}>● Applications</span>
          <span style={{color:"#06b6d4"}}>– – Interviews</span>
        </div>
        <BezierChart/>
      </div>
      <div style={{ background:"var(--card-bg)", border:"1px solid var(--border)", borderRadius:14, padding:"16px 18px" }}>
        <div style={{ fontSize:13, fontWeight:600, color:"var(--text)", marginBottom:12 }}>DevOps Prep Progress</div>
        <div style={{ display:"flex", alignItems:"center", gap:12, marginBottom:16 }}>
          <GaugeChart pct={72}/>
          <div style={{flex:1}}>
            <ProgressBar label="Kubernetes" pct={85} color="#8B5CF6"/>
            <ProgressBar label="Terraform" pct={78} color="#06b6d4"/>
            <ProgressBar label="Jenkins/CI" pct={65} color="#f59e0b"/>
          </div>
        </div>
      </div>
    </div>

    {/* Live Job Feed Preview on Dashboard */}
    <div style={{ background:"var(--card-bg)", border:"1px solid var(--border)", borderRadius:14, overflow:"hidden", marginBottom:16 }}>
      <div style={{ padding:"14px 18px", borderBottom:"1px solid var(--border)", display:"flex", alignItems:"center", justifyContent:"space-between" }}>
        <span style={{ fontSize:13, fontWeight:600, color:"var(--text)" }}>🔴 Live Job Feed — Top Matches</span>
        <span style={{ fontSize:11, color:"#4ade80" }}>● {liveJobs} jobs tracked</span>
      </div>
      <div style={{ overflowX:"auto" }}>
        <table style={{ width:"100%", borderCollapse:"collapse", fontSize:12 }}>
          <thead><tr style={{background:"var(--surface)"}}>{["Company","Role","Portal","Match","Salary","Action"].map(h=><th key={h} style={{padding:"9px 14px",textAlign:"left",color:"var(--muted)",fontWeight:500,fontSize:10,textTransform:"uppercase",letterSpacing:"0.05em"}}>{h}</th>)}</tr></thead>
          <tbody>{jobs.filter(j => typeof j.id !== "number" && !j.applied).slice(0,6).map((j,i)=>{
            const pm=getPortalMeta(j.portal);
            const isApplied = appliedIds.includes(j.id);
            return (
              <tr key={j.id} style={{borderTop:"1px solid var(--border)",background:i%2?"var(--surface)":"transparent"}}>
                <td style={{padding:"9px 14px",fontWeight:600,color:"var(--text)"}}>{j.company}</td>
                <td style={{padding:"9px 14px",color:"var(--muted)"}}>{j.title}</td>
                <td style={{padding:"9px 14px"}}><span style={{fontSize:10,padding:"2px 8px",borderRadius:99,background:pm.bg,color:pm.color,border:`1px solid ${pm.color}33`}}>{j.portal}</span></td>
                <td style={{padding:"9px 14px"}}><span style={{fontWeight:700,color:matchColor(j.match)}}>{j.match}%</span></td>
                <td style={{padding:"9px 14px",color:"#4ade80",fontSize:11}}>{j.salary}</td>
                <td style={{padding:"9px 14px"}}>
                  <button onClick={()=>onApply({id:Date.now(),company_name:j.company,position:j.title,job_portal:j.portal,applied_date:new Date().toISOString().slice(0,10),status:"Applied",notes:`Dashboard quick apply. Match: ${j.match}%`})} disabled={isApplied} style={{padding:"4px 12px",borderRadius:7,fontSize:10,fontWeight:600,background:isApplied?"#4ade8022":"linear-gradient(135deg,#8B5CF6,#06b6d4)",color:isApplied?"#4ade80":"#fff",border:isApplied?"1px solid #4ade8044":"none",cursor:isApplied?"default":"pointer"}}>
                    {isApplied?"✓ Applied":"Quick Apply"}
                  </button>
                </td>
              </tr>
            );
          })}</tbody>
        </table>
      </div>
    </div>

    {/* Recent Applications */}
    <div style={{ background:"var(--card-bg)", border:"1px solid var(--border)", borderRadius:14, overflow:"hidden" }}>
      <div style={{ padding:"14px 18px", borderBottom:"1px solid var(--border)", fontSize:13, fontWeight:600, color:"var(--text)" }}>Recent Applications</div>
      <div style={{overflowX:"auto"}}>
        <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
          <thead><tr style={{background:"var(--surface)"}}>{["Company","Position","Portal","Date","Status"].map(h=><th key={h} style={{padding:"10px 16px",textAlign:"left",color:"var(--muted)",fontWeight:500,fontSize:11,textTransform:"uppercase",letterSpacing:"0.05em"}}>{h}</th>)}</tr></thead>
          <tbody>{jobs.filter(j => j.applied).slice(0,5).map((j,i)=>(
            <tr key={j.id} style={{borderTop:"1px solid var(--border)",background:i%2===0?"transparent":"var(--surface)"}}>
              <td style={{padding:"10px 16px",fontWeight:600,color:"var(--text)"}}>{j.company_name}</td>
              <td style={{padding:"10px 16px",color:"var(--muted)"}}>{j.position}</td>
              <td style={{padding:"10px 16px",color:"var(--muted)"}}>{j.job_portal}</td>
              <td style={{padding:"10px 16px",color:"var(--muted)"}}>{j.applied_date}</td>
              <td style={{padding:"10px 16px"}}><span style={{padding:"3px 10px",borderRadius:99,fontSize:11,background:statusColor(j.status)+"22",color:statusColor(j.status)}}>{j.status}</span></td>
            </tr>
          ))}</tbody>
        </table>
      </div>
    </div>
  </div>
);

// ─── JARVIS CHAT ──────────────────────────────────────────────────────────────
const JarvisChat = () => {
  const [messages, setMessages] = useState([
    { role:"assistant", content:"Hello Naveen! I'm JARVIS, your AI career commander. I can help you with DevOps interview prep, draft cover letters, analyse job descriptions, or just strategise your job hunt. What would you like to tackle today?" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [listening, setListening] = useState(false);
  const [bars] = useState(()=>Array.from({length:20},()=>Math.random()));
  const scrollRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => { if(scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight; }, [messages]);

  const getJarvisLocalResponse = (query) => {
    const q = query.toLowerCase();
    
    if (q.includes("interview") || q.includes("mock") || q.includes("question")) {
      return `Welcome to your DevOps Mock Interview, Naveen! Let's start with a crucial scenario for Lloyds Banking Group:

"Imagine you are deploying a secure, high-throughput microservice on AWS EKS. How would you configure IAM Roles for Service Accounts (IRSA) to grant the pods permission to access an RDS database, and what Terraform resources would you provision to automate this safely?"

Take your time to structure your response covering:
1. OIDC Provider configuration in Terraform.
2. IAM Policy and Role bindings.
3. EKS Service Account annotation.
4. Kubernetes Pod spec deployment.

I'm ready when you are!`;
    }
    
    if (q.includes("cover") || q.includes("letter") || q.includes("draft")) {
      return `Here is a custom tailored cover letter draft for **Lloyds Banking Group** matching your AWS DevOps Engineer profile:

***
**Subject: Application for AWS DevOps Engineer – Naveen Kumar**

Dear Hiring Team at Lloyds Banking Group,

I am writing to express my strong interest in the AWS DevOps Engineer position. With 3.8 years of dedicated experience automating cloud infrastructure, optimizing CI/CD workflows, and managing complex Kubernetes environments at Yokra Solutions and Krify Technologies, I am eager to bring my expertise to Lloyds Banking Group's platform engineering division.

In my recent projects, I successfully:
• Deployed AWS EKS clusters utilizing IAM Roles for Service Accounts (IRSA) with OIDC federation to enforce least-privilege pod-level security.
• Automated S3 remote backend setups with state locking via DynamoDB to avoid plan conflicts.
• Configured Jenkins multi-branch pipelines and Ansible deployment playbooks for rolling deployments.

I am highly skilled in Kubernetes container orchestration, Jenkins pipeline automation, and Prometheus/Grafana monitoring, which aligns perfectly with your engineering objectives. I am keen to help Lloyds Banking Group scale its secure cloud-native platforms.

Sincerely,
Naveen Kumar
naveendevops589@gmail.com
***

You can copy this and adjust the details as needed!`;
    }
    
    if (q.includes("irsa") || q.includes("oidc") || q.includes("iam")) {
      return `**EKS IRSA (IAM Roles for Service Accounts) & OIDC Explained:**

IRSA allows you to associate an AWS IAM role directly with a Kubernetes Service Account. This enables pod-level privilege separation instead of relying on the EKS Node's IAM instance profile.

**How it works under the hood:**
1. **OIDC Federation**: Your EKS cluster hosts a public OpenID Connect issuer URL. You register this URL as an Identity Provider (IdP) in AWS IAM.
2. **Kubernetes Service Account**: You annotate the Service Account with the ARN of your AWS IAM role:
   \`eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/my-pod-role\`
3. **Pod projection**: The EKS webhook projects a signed OIDC Web Token into the pod at \`/var/run/secrets/eks.amazonaws.com/serviceaccount/token\`, setting env vars like \`AWS_ROLE_ARN\`.
4. **SDK Authentication**: The AWS SDK in your container detects these variables and calls STS \`AssumeRoleWithWebIdentity\` to fetch temporary credentials automatically.

This is the gold standard for secure cloud-native IAM integration!`;
    }
    
    if (q.includes("strategy") || q.includes("job") || q.includes("hunt")) {
      return `Naveen, with **3.8 years of experience** as an AWS DevOps Engineer, you are in a very high-demand tier. Here is your tactical job hunt strategy for **Lloyds Banking Group** and **Zurich Insurance**:

1. **Focus on EKS and Infrastructure Security**:
   - Financial enterprises value EKS security (Network Policies, IRSA, KMS encryption) and Terraform state controls above all else. Highlight these heavily in your resume.
2. **Leverage Referrals**:
   - In your tracker, you noted referrals for Zurich (KRIFY referral) and Lloyds (YOKRA referral). Follow up with these contacts weekly. Referral candidates are 4x more likely to clear screening.
3. **Polish DevOps Prep masteries**:
   - Review EKS network topologies, AWS VPC peering vs Transit Gateway, and Terraform multi-environment workspaces.
4. **Utilize Auto-Apply**:
   - Run our Live Job Feed crawls daily, filter for Match Score > 80%, and trigger our Auto-Apply script for matched positions to maximize throughput.

Let me know if you want to run a mock interview on any of these topics!`;
    }

    if (q.includes("terraform")) {
      return `**Terraform Remote State & DynamoDB Locking Best Practices:**

To collaborate safely in Terraform, you must use a remote backend (like AWS S3) with state locking (via DynamoDB).

**Terraform Configuration Example:**
\`\`\`hcl
terraform {
  backend "s3" {
    bucket         = "naveen-terraform-states"
    key            = "global/s3/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "terraform-locks"
    encrypt        = true
  }
}
\`\`\`

**Key Points:**
1. **State Locking**: DynamoDB prevents concurrent applies by locking the state ID. Any other attempt will fail until the lock is released.
2. **Encryption**: Always enable \`encrypt = true\` on S3, as state files contain sensitive credentials.
3. **State Versioning**: Enable versioning on your S3 bucket to easily roll back if the state gets corrupted.`;
    }

    if (q.includes("kubernetes") || q.includes("eks")) {
      return `**AWS EKS and Kubernetes Architecture Core Concepts:**

As a DevOps Engineer, you should master:
1. **Control Plane**: Managed by AWS in EKS (API Server, etcd, Scheduler, Controller Manager).
2. **Data Plane**: Managed by you or AWS Fargate (Self-managed EC2 nodes, Managed Node Groups, or Karpenter for auto-scaling).
3. **Karpenter vs Cluster Autoscaler**: Karpenter is a high-performance Kubernetes autoscaler built for AWS. It bypasses EC2 Auto Scaling Groups and launches nodes directly via AWS EC2 Fleet APIs, scaling up in under 15 seconds!
4. **Networking (AWS VPC CNI)**: Assigns a real AWS VPC IP address to every pod directly from your subnets, avoiding overlay latency.`;
    }
    
    return `Acknowledged, Naveen. I am monitoring your job feed and command center status. 
    
You are currently targeting **AWS DevOps Engineer** roles at **Lloyds Banking Group** and **Zurich Insurance**. Your profile mastery stands at **72%** (Kubernetes, AWS, Terraform, Jenkins, Ansible).

How can I assist you further? You can ask me to:
• "Start DevOps Mock Interview"
• "Draft cover letter for Lloyds"
• "Explain EKS IRSA"
• "Analyze my application strategy"`;
  };

  const sendMessage = useCallback(async (text) => {
    if(!text.trim()) return;
    const userMsg = {role:"user",content:text};
    setMessages(prev=>[...prev,userMsg]);
    setInput(""); setLoading(true);
    try {
      const history = [...messages,userMsg].map(m=>({role:m.role,content:m.content}));
      const key = localStorage.getItem("anthropic_api_key") || "";
      if (!key) {
        // Fall back to local smart responses if key is missing
        await new Promise(r => setTimeout(r, 600)); // Slight artificial delay for realism
        const reply = getJarvisLocalResponse(text);
        setMessages(prev=>[...prev,{role:"assistant",content:reply}]);
        if(window.speechSynthesis){const u=new SpeechSynthesisUtterance(reply.slice(0,300));u.rate=1.05;window.speechSynthesis.speak(u);}
        setLoading(false);
        return;
      }
      const res = await fetch("/api/anthropic/v1/messages", {
        method:"POST",
        headers:{
          "Content-Type":"application/json",
          "x-api-key": key,
          "anthropic-version": "2023-06-01"
        },
        body:JSON.stringify({
          model:"claude-3-5-sonnet-latest", max_tokens:1000,
          system:`You are JARVIS, the personal AI career assistant for Naveen Kumar, an AWS DevOps Engineer with 3.8 years of experience. His key skills are AWS EKS, Kubernetes, Terraform, Ansible, Jenkins, Prometheus. He is targeting Lloyds Banking Group and Zurich Insurance. Be concise, tactical, and career-focused. When doing mock interviews, be rigorous and give scored feedback.`,
          messages:history,
        }),
      });
      if (!res.ok) {
        throw new Error("API error");
      }
      const data = await res.json();
      const reply = data.content?.[0]?.text || "I encountered an issue. Please try again.";
      setMessages(prev=>[...prev,{role:"assistant",content:reply}]);
      if(window.speechSynthesis){const u=new SpeechSynthesisUtterance(reply.slice(0,300));u.rate=1.05;window.speechSynthesis.speak(u);}
    } catch (e) { 
      // Fallback to local response on fetch/network error
      await new Promise(r => setTimeout(r, 400));
      const reply = getJarvisLocalResponse(text);
      setMessages(prev=>[...prev,{role:"assistant",content:reply}]);
      if(window.speechSynthesis){const u=new SpeechSynthesisUtterance(reply.slice(0,300));u.rate=1.05;window.speechSynthesis.speak(u);}
    }
    setLoading(false);
  }, [messages]);

  const toggleMic = () => {
    if(listening){recognitionRef.current?.stop();setListening(false);return;}
    const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
    if(!SR){alert("Speech recognition not supported.");return;}
    const rec=new SR();rec.lang="en-IN";rec.interimResults=false;
    rec.onresult=e=>{const t=e.results[0][0].transcript;setInput(t);setListening(false);sendMessage(t);};
    rec.onerror=()=>setListening(false);rec.onend=()=>setListening(false);
    recognitionRef.current=rec;rec.start();setListening(true);
  };

  const quickCmds = ["Start DevOps Mock Interview","Draft cover letter for Lloyds","Explain EKS IRSA","Analyse my application strategy"];

  return (
    <div style={{display:"flex",flexDirection:"column",height:560}}>
      <div style={{display:"flex",alignItems:"center",gap:3,height:36,padding:"0 16px",background:"var(--surface)",borderRadius:"12px 12px 0 0",border:"1px solid var(--border)",borderBottom:"none"}}>
        <div style={{width:8,height:8,borderRadius:"50%",background:"#4ade80",marginRight:8}}/>
        <span style={{fontSize:12,color:"var(--muted)",flex:1}}>JARVIS · Neural Interface Active</span>
        {bars.map((b,i)=><div key={i} style={{width:2,borderRadius:1,background:listening?"#8B5CF6":"var(--border)",height:listening?`${8+b*24}px`:"4px",transition:"height 0.15s ease"}}/>)}
      </div>
      <div ref={scrollRef} style={{flex:1,overflowY:"auto",padding:16,background:"var(--card-bg)",border:"1px solid var(--border)",borderTop:"none",display:"flex",flexDirection:"column",gap:12}}>
        {messages.map((m,i)=>(
          <div key={i} style={{display:"flex",flexDirection:m.role==="user"?"row-reverse":"row",gap:10,alignItems:"flex-start"}}>
            <div style={{width:30,height:30,borderRadius:"50%",background:m.role==="user"?"#8B5CF6":"linear-gradient(135deg,#8B5CF6,#06b6d4)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:700,color:"#fff",flexShrink:0}}>{m.role==="user"?"NK":"J"}</div>
            <div style={{maxWidth:"75%",padding:"10px 14px",borderRadius:m.role==="user"?"16px 4px 16px 16px":"4px 16px 16px 16px",background:m.role==="user"?"#8B5CF6":"var(--surface)",color:m.role==="user"?"#fff":"var(--text)",fontSize:13,lineHeight:1.6,border:m.role==="assistant"?"1px solid var(--border)":"none",whiteSpace:"pre-wrap"}}>{m.content}</div>
          </div>
        ))}
        {loading&&(
          <div style={{display:"flex",gap:10,alignItems:"flex-start"}}>
            <div style={{width:30,height:30,borderRadius:"50%",background:"linear-gradient(135deg,#8B5CF6,#06b6d4)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:700,color:"#fff"}}>J</div>
            <div style={{padding:"12px 16px",borderRadius:"4px 16px 16px 16px",background:"var(--surface)",border:"1px solid var(--border)",display:"flex",gap:6}}>
              {[0,1,2].map(d=><div key={d} style={{width:7,height:7,borderRadius:"50%",background:"#8B5CF6",animation:"pulse 1s ease-in-out infinite",animationDelay:`${d*200}ms`}}/>)}
            </div>
          </div>
        )}
      </div>
      <div style={{display:"flex",flexWrap:"wrap",gap:6,padding:"10px 12px",background:"var(--surface)",border:"1px solid var(--border)",borderTop:"none"}}>
        {quickCmds.map(c=><button key={c} onClick={()=>sendMessage(c)} style={{fontSize:11,padding:"5px 12px",borderRadius:99,background:"#8B5CF620",color:"#8B5CF6",border:"1px solid #8B5CF644",cursor:"pointer"}}>{c}</button>)}
      </div>
      <div style={{display:"flex",gap:8,padding:"10px 12px",background:"var(--card-bg)",border:"1px solid var(--border)",borderTop:"none",borderRadius:"0 0 12px 12px"}}>
        <input value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>e.key==="Enter"&&sendMessage(input)} placeholder="Ask JARVIS anything about your career..." style={{flex:1,background:"var(--surface)",border:"1px solid var(--border)",borderRadius:10,padding:"9px 14px",fontSize:13,color:"var(--text)"}}/>
        <button onClick={toggleMic} style={{width:38,height:38,borderRadius:"50%",background:listening?"#8B5CF6":"var(--surface)",border:"1px solid var(--border)",cursor:"pointer",fontSize:16}}>{listening?"🔴":"🎤"}</button>
        <button onClick={()=>sendMessage(input)} disabled={!input.trim()||loading} style={{width:38,height:38,borderRadius:"50%",background:"linear-gradient(135deg,#8B5CF6,#06b6d4)",border:"none",cursor:"pointer",color:"#fff",fontSize:16}}>→</button>
      </div>
    </div>
  );
};

// ─── AUTOMATION HUB ───────────────────────────────────────────────────────────
const AutomationHub = () => {
  const [keywords,setKeywords]=useState("AWS DevOps, Kubernetes, Terraform, Ansible");
  const [interval,setIntervalVal]=useState("30");
  const [scraping,setScraping]=useState(false);
  const [logs,setLogs]=useState(AUTOMATION_LOGS);

  const simulateScrape=()=>{
    setScraping(true);
    const newLog={ts:new Date().toTimeString().slice(0,8),type:"scrape",desc:`LinkedIn scan triggered: keywords "${keywords.split(",")[0].trim()}"`,status:"success"};
    setTimeout(()=>{setLogs(prev=>[newLog,...prev]);setScraping(false);},1800);
  };

  return (
    <div style={{display:"flex",flexDirection:"column",gap:16}}>
      <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,padding:"18px 20px"}}>
        <div style={{fontSize:13,fontWeight:600,color:"var(--text)",marginBottom:14}}>⚙️ Monitor Configuration</div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:12}}>
          {[["Search Keywords",keywords,setKeywords,"text"],["Telegram Bot Token","","","password"],["Telegram Chat ID","","","text"]].map(([lbl,val,setter,type])=>(
            <div key={lbl}>
              <label style={{fontSize:11,color:"var(--muted)",display:"block",marginBottom:4}}>{lbl}</label>
              <input type={type} value={val} onChange={setter?e=>setter(e.target.value):undefined} placeholder={lbl} style={{width:"100%",background:"var(--surface)",border:"1px solid var(--border)",borderRadius:8,padding:"8px 12px",fontSize:13,color:"var(--text)",boxSizing:"border-box"}}/>
            </div>
          ))}
          <div>
            <label style={{fontSize:11,color:"var(--muted)",display:"block",marginBottom:4}}>Scan Interval (min)</label>
            <select value={interval} onChange={e=>setIntervalVal(e.target.value)} style={{width:"100%",background:"var(--surface)",border:"1px solid var(--border)",borderRadius:8,padding:"8px 12px",fontSize:13,color:"var(--text)"}}>
              {["15","30","60","120"].map(v=><option key={v} value={v}>{v} minutes</option>)}
            </select>
          </div>
        </div>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(160px,1fr))",gap:12}}>
        {[["LinkedIn", `${jobs.filter(j => j.portal === "LinkedIn Jobs").length} found` ,"#0077B5"],["Naukri", `${jobs.filter(j => j.portal === "Naukri.com").length} found` ,"#FF6B00"],["Alerts Sent","4 today","#8B5CF6"],["Auto-Applied","2 today","#4ade80"]].map(([lbl,val,col])=>(
          <div key={lbl} style={{background:"var(--card-bg)",border:`1px solid ${col}44`,borderRadius:12,padding:"14px 16px"}}>
            <div style={{fontSize:11,color:"var(--muted)",marginBottom:4}}>{lbl}</div>
            <div style={{fontSize:22,fontWeight:700,color:col}}>{val}</div>
          </div>
        ))}
      </div>
      <div style={{display:"flex",gap:10}}>
        <button onClick={simulateScrape} disabled={scraping} style={{padding:"9px 20px",borderRadius:10,background:"linear-gradient(135deg,#8B5CF6,#06b6d4)",color:"#fff",border:"none",cursor:"pointer",fontSize:13,fontWeight:600}}>{scraping?"⟳ Scanning...":"▶ Run Scrape Now"}</button>
        <button style={{padding:"9px 20px",borderRadius:10,background:"var(--surface)",color:"var(--text)",border:"1px solid var(--border)",cursor:"pointer",fontSize:13}}>🤖 Enable Auto-Apply</button>
        <button style={{padding:"9px 20px",borderRadius:10,background:"var(--surface)",color:"var(--text)",border:"1px solid var(--border)",cursor:"pointer",fontSize:13}}>📱 Test Telegram Alert</button>
      </div>
      <div style={{background:"#0d1117",border:"1px solid #30363d",borderRadius:12,overflow:"hidden"}}>
        <div style={{padding:"8px 14px",background:"#161b22",borderBottom:"1px solid #30363d",display:"flex",gap:6,alignItems:"center"}}>
          {["#ff5f57","#ffbd2e","#28c840"].map(c=><div key={c} style={{width:11,height:11,borderRadius:"50%",background:c}}/>)}
          <span style={{fontSize:11,color:"#7d8590",marginLeft:8,fontFamily:"monospace"}}>automation-daemon — bash</span>
        </div>
        <div style={{padding:14,fontFamily:"monospace",fontSize:12,lineHeight:1.7,maxHeight:220,overflowY:"auto"}}>
          {logs.map((l,i)=>(
            <div key={i} style={{color:l.status==="failed"?"#f87171":l.type==="notify"?"#f59e0b":"#4ade80"}}>
              <span style={{color:"#7d8590"}}>[{l.ts}] </span><span style={{color:"#e6edf3"}}>[{l.type.toUpperCase()}] </span>{l.desc}
              {l.status==="failed"&&<span style={{color:"#f87171"}}> ✗ FAILED</span>}
            </div>
          ))}
          <div style={{color:"#8B5CF6",animation:"blink 1s step-end infinite"}}>█</div>
        </div>
      </div>
    </div>
  );
};

// ─── RESUME MANAGER ───────────────────────────────────────────────────────────
const ResumeManager = () => {
  const [jd,setJd]=useState("");const [result,setResult]=useState(null);const [loading,setLoading]=useState(false);const [resumeText,setResumeText]=useState(MOCK_RESUME);
  const analyzeMatch=async()=>{
    if(!jd.trim())return;setLoading(true);
    try{
      const key = localStorage.getItem("anthropic_api_key") || "";
      const res=await fetch("/api/anthropic/v1/messages",{method:"POST",headers:{"Content-Type":"application/json","x-api-key":key,"anthropic-version":"2023-06-01"},body:JSON.stringify({model:"claude-sonnet-4-20250514",max_tokens:1000,system:"You are an ATS resume expert. Respond ONLY in JSON with keys: score (0-100), matched_keywords (array), missing_keywords (array), cover_letter (string ~150 words), recruiter_email (string ~120 words). No markdown, no backticks.",messages:[{role:"user",content:`Resume:\n${resumeText}\n\nJob Description:\n${jd}\n\nAnalyse match.`}]})});
      const data=await res.json();setResult(JSON.parse(data.content?.[0]?.text.replace(/```json|```/g,"").trim()||"{}"));
    }catch{setResult({score:81,matched_keywords:["AWS","Kubernetes","Terraform","Jenkins","EKS"],missing_keywords:["Azure","GCP","ArgoCD"],cover_letter:"Dear Hiring Manager, I am excited to apply for this DevOps role. With 3.8 years of hands-on AWS EKS, Terraform, and Ansible experience at Yokra and Krify, I have delivered production Kubernetes workloads and automated infrastructure at scale.",recruiter_email:"Hi [Name], I came across this opportunity and believe my AWS DevOps background aligns closely with your requirements. I have implemented EKS IRSA, Terraform remote backends, and multi-service Prometheus alerting. Happy to connect for a quick call. Best, Naveen."});}
    setLoading(false);
  };
  return (
    <div style={{display:"grid",gridTemplateColumns:"1fr 1fr",gap:16}}>
      <div style={{display:"flex",flexDirection:"column",gap:12}}>
        <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,padding:16}}>
          <div style={{fontSize:13,fontWeight:600,color:"var(--text)",marginBottom:10}}>📋 Paste Job Description</div>
          <textarea value={jd} onChange={e=>setJd(e.target.value)} rows={8} placeholder="Paste the JD here for ATS analysis..." style={{width:"100%",background:"var(--surface)",border:"1px solid var(--border)",borderRadius:8,padding:"10px 12px",fontSize:12,color:"var(--text)",resize:"vertical",boxSizing:"border-box"}}/>
          <button onClick={analyzeMatch} disabled={loading||!jd.trim()} style={{marginTop:10,width:"100%",padding:"10px",borderRadius:10,background:"linear-gradient(135deg,#8B5CF6,#06b6d4)",color:"#fff",border:"none",cursor:"pointer",fontWeight:600}}>{loading?"Analysing...":"🔍 Analyse Match"}</button>
        </div>
        {result&&(
          <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,padding:16}}>
            <div style={{display:"flex",alignItems:"center",gap:12,marginBottom:12}}>
              <div style={{fontSize:36,fontWeight:700,color:result.score>=75?"#4ade80":"#f59e0b"}}>{result.score}%</div>
              <div><div style={{fontSize:13,fontWeight:600,color:"var(--text)"}}>ATS Match Score</div><div style={{fontSize:11,color:"var(--muted)"}}>{result.score>=75?"Strong match — proceed":"Moderate match"}</div></div>
            </div>
            <div style={{marginBottom:10}}><div style={{fontSize:11,color:"#4ade80",marginBottom:4}}>✓ Matched</div><div>{result.matched_keywords?.map(k=><Badge key={k} text={k} color="#4ade80"/>)}</div></div>
            <div><div style={{fontSize:11,color:"#f87171",marginBottom:4}}>✗ Missing</div><div>{result.missing_keywords?.map(k=><Badge key={k} text={k} color="#f87171"/>)}</div></div>
          </div>
        )}
      </div>
      <div style={{display:"flex",flexDirection:"column",gap:12}}>
        {result&&(
          <>
            <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,padding:16}}>
              <div style={{fontSize:13,fontWeight:600,color:"var(--text)",marginBottom:8}}>✉️ Cover Letter</div>
              <div style={{fontSize:12,color:"var(--text)",lineHeight:1.7,background:"var(--surface)",borderRadius:8,padding:12}}>{result.cover_letter}</div>
              <button onClick={()=>navigator.clipboard?.writeText(result.cover_letter)} style={{marginTop:8,fontSize:11,padding:"5px 14px",borderRadius:8,background:"var(--surface)",border:"1px solid var(--border)",cursor:"pointer",color:"var(--text)"}}>📋 Copy</button>
            </div>
            <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,padding:16}}>
              <div style={{fontSize:13,fontWeight:600,color:"var(--text)",marginBottom:8}}>📧 Recruiter Email</div>
              <div style={{fontSize:12,color:"var(--text)",lineHeight:1.7,background:"var(--surface)",borderRadius:8,padding:12}}>{result.recruiter_email}</div>
              <button onClick={()=>navigator.clipboard?.writeText(result.recruiter_email)} style={{marginTop:8,fontSize:11,padding:"5px 14px",borderRadius:8,background:"var(--surface)",border:"1px solid var(--border)",cursor:"pointer",color:"var(--text)"}}>📋 Copy</button>
            </div>
          </>
        )}
        <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,padding:16,flex:result?"none":1}}>
          <div style={{fontSize:13,fontWeight:600,color:"var(--text)",marginBottom:8}}>📄 Master Resume</div>
          <textarea value={resumeText} onChange={e=>setResumeText(e.target.value)} rows={12} style={{width:"100%",background:"var(--surface)",border:"1px solid var(--border)",borderRadius:8,padding:"10px 12px",fontSize:11,color:"var(--text)",resize:"vertical",fontFamily:"monospace",boxSizing:"border-box"}}/>
        </div>
      </div>
    </div>
  );
};

// ─── JOB TRACKER ─────────────────────────────────────────────────────────────
const JobTracker = ({ jobs, setJobs }) => {
  const [form,setForm]=useState({company_name:"",position:"",job_portal:"LinkedIn",applied_date:"",status:"Applied",notes:""});
  const statuses=["Applied","Screening","Technical Round 1","Technical Round 2","Manager Round","Offered","Rejected"];
  const addJob=()=>{if(!form.company_name||!form.position)return;setJobs(prev=>[...prev,{...form,id:Date.now()}]);setForm({company_name:"",position:"",job_portal:"LinkedIn",applied_date:"",status:"Applied",notes:""});};
  return (
    <div style={{display:"flex",flexDirection:"column",gap:16}}>
      <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,padding:16}}>
        <div style={{fontSize:13,fontWeight:600,color:"var(--text)",marginBottom:12}}>➕ Add Application</div>
        <div style={{display:"grid",gridTemplateColumns:"1fr 1fr 1fr",gap:10,marginBottom:10}}>
          {[["company_name","Company"],["position","Position"],["notes","Notes"]].map(([k,lbl])=>(
            <div key={k}><label style={{fontSize:11,color:"var(--muted)",display:"block",marginBottom:3}}>{lbl}</label><input value={form[k]} onChange={e=>setForm(p=>({...p,[k]:e.target.value}))} style={{width:"100%",background:"var(--surface)",border:"1px solid var(--border)",borderRadius:8,padding:"8px 10px",fontSize:12,color:"var(--text)",boxSizing:"border-box"}}/></div>
          ))}
          <div><label style={{fontSize:11,color:"var(--muted)",display:"block",marginBottom:3}}>Portal</label><select value={form.job_portal} onChange={e=>setForm(p=>({...p,job_portal:e.target.value}))} style={{width:"100%",background:"var(--surface)",border:"1px solid var(--border)",borderRadius:8,padding:"8px 10px",fontSize:12,color:"var(--text)"}}>{["LinkedIn","Naukri","Indeed","Glassdoor","Direct"].map(v=><option key={v}>{v}</option>)}</select></div>
          <div><label style={{fontSize:11,color:"var(--muted)",display:"block",marginBottom:3}}>Date</label><input type="date" value={form.applied_date} onChange={e=>setForm(p=>({...p,applied_date:e.target.value}))} style={{width:"100%",background:"var(--surface)",border:"1px solid var(--border)",borderRadius:8,padding:"8px 10px",fontSize:12,color:"var(--text)"}}/></div>
          <div><label style={{fontSize:11,color:"var(--muted)",display:"block",marginBottom:3}}>Status</label><select value={form.status} onChange={e=>setForm(p=>({...p,status:e.target.value}))} style={{width:"100%",background:"var(--surface)",border:"1px solid var(--border)",borderRadius:8,padding:"8px 10px",fontSize:12,color:"var(--text)"}}>{statuses.map(s=><option key={s}>{s}</option>)}</select></div>
        </div>
        <button onClick={addJob} style={{padding:"9px 22px",borderRadius:10,background:"linear-gradient(135deg,#8B5CF6,#06b6d4)",color:"#fff",border:"none",cursor:"pointer",fontWeight:600,fontSize:13}}>Add Application</button>
      </div>
      <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,overflow:"hidden"}}>
        <div style={{overflowX:"auto"}}>
          <table style={{width:"100%",borderCollapse:"collapse",fontSize:13}}>
            <thead><tr style={{background:"var(--surface)"}}>{["Company","Position","Portal","Date","Status","Notes"].map(h=><th key={h} style={{padding:"10px 14px",textAlign:"left",color:"var(--muted)",fontWeight:500,fontSize:11,textTransform:"uppercase"}}>{h}</th>)}</tr></thead>
            <tbody>{jobs.map((j,i)=>(
              <tr key={j.id} style={{borderTop:"1px solid var(--border)",background:i%2?"var(--surface)":"transparent"}}>
                <td style={{padding:"10px 14px",fontWeight:600,color:"var(--text)"}}>{j.company_name}</td>
                <td style={{padding:"10px 14px",color:"var(--muted)",fontSize:12}}>{j.position}</td>
                <td style={{padding:"10px 14px",color:"var(--muted)",fontSize:12}}>{j.job_portal}</td>
                <td style={{padding:"10px 14px",color:"var(--muted)",fontSize:12}}>{j.applied_date}</td>
                <td style={{padding:"10px 14px"}}><select value={j.status} onChange={e=>setJobs(prev=>prev.map(x=>x.id===j.id?{...x,status:e.target.value}:x))} style={{fontSize:11,padding:"3px 8px",borderRadius:8,background:statusColor(j.status)+"22",color:statusColor(j.status),border:`1px solid ${statusColor(j.status)}44`}}>{statuses.map(s=><option key={s}>{s}</option>)}</select></td>
                <td style={{padding:"10px 14px",color:"var(--muted)",fontSize:11}}>{j.notes}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// ─── TASK BOARD ───────────────────────────────────────────────────────────────
const TaskBoard = ({ tasks, setTasks }) => {
  const [newTask,setNewTask]=useState("");const [taskType,setTaskType]=useState("daily");
  const addTask=()=>{if(!newTask.trim())return;setTasks(prev=>[...prev,{id:Date.now(),title:newTask,status:"pending",task_type:taskType}]);setNewTask("");};
  const toggle=id=>setTasks(prev=>prev.map(t=>t.id===id?{...t,status:t.status==="completed"?"pending":"completed"}:t));
  return (
    <div style={{display:"flex",flexDirection:"column",gap:16}}>
      <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,padding:16}}>
        <div style={{display:"flex",gap:10}}>
          <input value={newTask} onChange={e=>setNewTask(e.target.value)} onKeyDown={e=>e.key==="Enter"&&addTask()} placeholder="Add a new action item..." style={{flex:1,background:"var(--surface)",border:"1px solid var(--border)",borderRadius:10,padding:"9px 14px",fontSize:13,color:"var(--text)"}}/>
          <select value={taskType} onChange={e=>setTaskType(e.target.value)} style={{background:"var(--surface)",border:"1px solid var(--border)",borderRadius:10,padding:"9px 12px",fontSize:13,color:"var(--text)"}}><option value="daily">Daily</option><option value="weekly">Weekly</option></select>
          <button onClick={addTask} style={{padding:"9px 18px",borderRadius:10,background:"linear-gradient(135deg,#8B5CF6,#06b6d4)",color:"#fff",border:"none",cursor:"pointer",fontWeight:600}}>Add</button>
        </div>
      </div>
      {["daily","weekly"].map(type=>(
        <div key={type} style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,overflow:"hidden"}}>
          <div style={{padding:"12px 16px",borderBottom:"1px solid var(--border)",display:"flex",alignItems:"center",gap:8}}>
            <div style={{width:8,height:8,borderRadius:"50%",background:type==="daily"?"#8B5CF6":"#06b6d4"}}/>
            <span style={{fontSize:12,fontWeight:600,color:"var(--text)",textTransform:"capitalize"}}>{type} Tasks</span>
            <span style={{marginLeft:"auto",fontSize:11,color:"var(--muted)"}}>{tasks.filter(t=>t.task_type===type&&t.status==="completed").length}/{tasks.filter(t=>t.task_type===type).length} done</span>
          </div>
          {tasks.filter(t=>t.task_type===type).map(t=>(
            <div key={t.id} onClick={()=>toggle(t.id)} style={{padding:"12px 16px",borderTop:"1px solid var(--border)",display:"flex",alignItems:"center",gap:12,cursor:"pointer",opacity:t.status==="completed"?0.5:1,transition:"opacity 0.2s"}}>
              <div style={{width:18,height:18,borderRadius:5,border:`2px solid ${t.status==="completed"?"#4ade80":"var(--border)"}`,background:t.status==="completed"?"#4ade80":"transparent",display:"flex",alignItems:"center",justifyContent:"center",flexShrink:0}}>
                {t.status==="completed"&&<span style={{fontSize:11,color:"#fff"}}>✓</span>}
              </div>
              <span style={{fontSize:13,color:"var(--text)",textDecoration:t.status==="completed"?"line-through":"none"}}>{t.title}</span>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
};

// ─── DEVOPS PREP ──────────────────────────────────────────────────────────────
const DevOpsPrepQA = () => {
  const [cat,setCat]=useState("AWS");const [selected,setSelected]=useState(MOCK_QA[0]);const [answer,setAnswer]=useState("");const [loading,setLoading]=useState(false);
  const [termLines,setTermLines]=useState([{text:"naveen@devops-prep:~$ ready",color:"#4ade80"}]);
  const cats=["AWS","Terraform","Kubernetes","Ansible","Jenkins"];
  const selectQuestion=q=>{setSelected(q);setAnswer("");setTermLines([{text:`naveen@devops-prep:~$ load-question --category ${q.category}`,color:"#4ade80"},{text:`> ${q.question}`,color:"#60a5fa"}]);};
  const submit=async()=>{
    if(!answer.trim())return;setLoading(true);
    setTermLines(prev=>[...prev,{text:`naveen@devops-prep:~$ submit-answer`,color:"#4ade80"},{text:answer,color:"#e6edf3"},{text:"Grading...",color:"#f59e0b"}]);
    try{
      const key = localStorage.getItem("anthropic_api_key") || "";
      const res=await fetch("/api/anthropic/v1/messages",{method:"POST",headers:{"Content-Type":"application/json","x-api-key":key,"anthropic-version":"2023-06-01"},body:JSON.stringify({model:"claude-sonnet-4-20250514",max_tokens:800,system:"You are a senior DevOps interview coach. Grade the candidate's answer. Respond ONLY in JSON with: score (0-10), critique (string), matched_competencies (array of strings), improvement (string). No markdown, no backticks.",messages:[{role:"user",content:`Question: ${selected.question}\n\nIdeal Answer: ${selected.answer}\n\nCandidate Answer: ${answer}\n\nGrade this.`}]})});
      const data=await res.json();
      const ev=JSON.parse(data.content?.[0]?.text.replace(/```json|```/g,"").trim()||"{}");
      setTermLines(prev=>[...prev.filter(l=>l.text!=="Grading..."),{text:`[SCORE] ${ev.score}/10`,color:ev.score>=7?"#4ade80":"#f87171"},{text:`[CRITIQUE] ${ev.critique}`,color:"#e6edf3"},{text:`[MATCHED] ${(ev.matched_competencies||[]).join(", ")}`,color:"#8B5CF6"},{text:`[IMPROVE] ${ev.improvement}`,color:"#f59e0b"},{text:"naveen@devops-prep:~$ █",color:"#4ade80"}]);
    }catch{setTermLines(prev=>[...prev,{text:"[ERROR] Evaluation failed. Mock score: 8/10 — Strong answer.",color:"#f87171"}]);}
    setLoading(false);
  };
  return (
    <div style={{display:"grid",gridTemplateColumns:"240px 1fr",gap:16,height:560}}>
      <div style={{display:"flex",flexDirection:"column",gap:8,overflowY:"auto"}}>
        <div style={{display:"flex",flexWrap:"wrap",gap:6,marginBottom:6}}>
          {cats.map(c=><button key={c} onClick={()=>setCat(c)} style={{padding:"5px 12px",borderRadius:99,fontSize:11,background:cat===c?"#8B5CF6":"var(--surface)",color:cat===c?"#fff":"var(--muted)",border:cat===c?"none":"1px solid var(--border)",cursor:"pointer"}}>{c}</button>)}
        </div>
        {MOCK_QA.filter(q=>q.category===cat).map(q=>(
          <div key={q.id} onClick={()=>selectQuestion(q)} style={{background:selected?.id===q.id?"#8B5CF620":"var(--card-bg)",border:`1px solid ${selected?.id===q.id?"#8B5CF6":"var(--border)"}`,borderRadius:10,padding:"10px 12px",cursor:"pointer",fontSize:12,color:"var(--text)",lineHeight:1.5}}>{q.question.slice(0,80)}...</div>
        ))}
      </div>
      <div style={{background:"#0d1117",border:"1px solid #30363d",borderRadius:12,overflow:"hidden",display:"flex",flexDirection:"column"}}>
        <div style={{padding:"8px 14px",background:"#161b22",borderBottom:"1px solid #30363d",display:"flex",gap:6,alignItems:"center"}}>
          {["#ff5f57","#ffbd2e","#28c840"].map(c=><div key={c} style={{width:11,height:11,borderRadius:"50%",background:c}}/>)}
          <span style={{fontSize:11,color:"#7d8590",marginLeft:8,fontFamily:"monospace"}}>devops-prep-terminal</span>
        </div>
        <div style={{flex:1,padding:14,fontFamily:"monospace",fontSize:12,lineHeight:1.7,overflowY:"auto"}}>
          {termLines.map((l,i)=><div key={i} style={{color:l.color}}>{l.text}</div>)}
        </div>
        <div style={{padding:"10px 14px",borderTop:"1px solid #30363d",display:"flex",gap:8}}>
          <span style={{color:"#4ade80",fontSize:12,fontFamily:"monospace",alignSelf:"center"}}>›</span>
          <input value={answer} onChange={e=>setAnswer(e.target.value)} onKeyDown={e=>e.key==="Enter"&&submit()} placeholder="Type your answer here..." style={{flex:1,background:"transparent",border:"none",color:"#e6edf3",fontFamily:"monospace",fontSize:12}}/>
          <button onClick={submit} disabled={loading||!answer.trim()} style={{padding:"6px 16px",borderRadius:8,background:"#8B5CF6",color:"#fff",border:"none",cursor:"pointer",fontSize:12}}>Submit</button>
        </div>
      </div>
    </div>
  );
};

// ─── RECRUITER EMAILS ─────────────────────────────────────────────────────────
const RecruiterEmails = () => {
  const [selected,setSelected]=useState(MOCK_EMAILS[0]);const [draft,setDraft]=useState("");const [loading,setLoading]=useState(false);
  const generateReply=async()=>{
    setLoading(true);
    try{
      const key = localStorage.getItem("anthropic_api_key") || "";
      const res=await fetch("/api/anthropic/v1/messages",{method:"POST",headers:{"Content-Type":"application/json","x-api-key":key,"anthropic-version":"2023-06-01"},body:JSON.stringify({model:"claude-sonnet-4-20250514",max_tokens:800,system:"You are drafting a professional email reply on behalf of Naveen Kumar, an AWS DevOps Engineer with 3.8 years of experience. Be professional, enthusiastic, and concise. Include relevant skills when appropriate.",messages:[{role:"user",content:`Draft a professional reply to this email:\n\n${selected.body}`}]})});
      const data=await res.json();setDraft(data.content?.[0]?.text||"Draft generation failed.");
    }catch{setDraft(`Dear ${selected.from.split("<")[0].trim()},\n\nThank you for reaching out regarding this opportunity. I am very interested in discussing this role further.\n\nMy background in AWS EKS, Terraform, and Kubernetes aligns closely with your requirements.\n\nBest regards,\nNaveen Kumar\nAWS DevOps Engineer`);}
    setLoading(false);
  };
  return (
    <div style={{display:"grid",gridTemplateColumns:"280px 1fr",gap:16,height:580}}>
      <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,overflow:"hidden",display:"flex",flexDirection:"column"}}>
        <div style={{padding:"12px 14px",borderBottom:"1px solid var(--border)",fontSize:13,fontWeight:600,color:"var(--text)"}}>📬 Recruiter Inbox</div>
        {MOCK_EMAILS.map(e=>(
          <div key={e.id} onClick={()=>{setSelected(e);setDraft("");}} style={{padding:"12px 14px",borderTop:"1px solid var(--border)",cursor:"pointer",background:selected?.id===e.id?"#8B5CF610":"transparent",borderLeft:selected?.id===e.id?"3px solid #8B5CF6":"3px solid transparent"}}>
            <div style={{fontSize:12,fontWeight:600,color:"var(--text)",marginBottom:2}}>{e.from.split("<")[0]}</div>
            <div style={{fontSize:11,color:"#8B5CF6",marginBottom:4}}>{e.subject}</div>
            <div style={{fontSize:11,color:"var(--muted)",whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis"}}>{e.preview}</div>
            <div style={{fontSize:10,color:"var(--muted)",marginTop:4}}>{e.date}</div>
          </div>
        ))}
      </div>
      <div style={{display:"flex",flexDirection:"column",gap:12}}>
        <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,padding:16,flex:1,overflow:"auto"}}>
          <div style={{fontSize:15,fontWeight:700,color:"var(--text)",marginBottom:6}}>{selected.subject}</div>
          <div style={{fontSize:11,color:"var(--muted)",marginBottom:12}}>From: {selected.from}</div>
          <div style={{fontSize:13,color:"var(--text)",lineHeight:1.7,whiteSpace:"pre-wrap"}}>{selected.body}</div>
          <button onClick={generateReply} disabled={loading} style={{marginTop:14,padding:"9px 20px",borderRadius:10,background:"linear-gradient(135deg,#8B5CF6,#06b6d4)",color:"#fff",border:"none",cursor:"pointer",fontWeight:600,fontSize:13}}>{loading?"Generating...":"🤖 Generate AI Reply"}</button>
        </div>
        {draft&&(
          <div style={{background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:14,padding:16}}>
            <div style={{fontSize:12,fontWeight:600,color:"var(--text)",marginBottom:8}}>✏️ Draft Reply</div>
            <textarea value={draft} onChange={e=>setDraft(e.target.value)} rows={8} style={{width:"100%",background:"var(--surface)",border:"1px solid var(--border)",borderRadius:8,padding:"10px 12px",fontSize:12,color:"var(--text)",resize:"vertical",boxSizing:"border-box"}}/>
            <div style={{display:"flex",gap:8,marginTop:8}}>
              <button onClick={()=>navigator.clipboard?.writeText(draft)} style={{padding:"7px 16px",borderRadius:8,background:"var(--surface)",border:"1px solid var(--border)",cursor:"pointer",fontSize:12,color:"var(--text)"}}>📋 Copy</button>
              <button style={{padding:"7px 16px",borderRadius:8,background:"#4ade8022",border:"1px solid #4ade8044",cursor:"pointer",fontSize:12,color:"#4ade80"}}>✉️ Open in Mail</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ─── MAIN APP ─────────────────────────────────────────────────────────────────
export default function App() {
  const [tab, setTab] = useState("dashboard");
  const [darkMode, setDarkMode] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [jobs, setJobs] = useState(MOCK_JOBS);
  const [tasks, setTasks] = useState(MOCK_TASKS);
  const [appliedLiveIds, setAppliedLiveIds] = useState([]);
  const [notifs, setNotifs] = useState(3);
  const [apiKey, setApiKey] = useState(() => localStorage.getItem("anthropic_api_key") || "");
  const [systemStatus, setSystemStatus] = useState(null);
  const [portalsSummary, setPortalsSummary] = useState([]);
  const [scanning, setScanning] = useState(false);

  // Lifted Job Feed Filter States
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [selectedPortals, setSelectedPortals] = useState([]);
  const [minMatch, setMinMatch] = useState(70);
  const [search, setSearch] = useState("");
  const [timeFilter, setTimeFilter] = useState("all");
  const [sortBy, setSortBy] = useState("match");

  // Dynamic filtered job counts for header and tab badges
  const getFilteredJobsCount = useCallback(() => {
    return jobs.filter(j => {
      if (typeof j.id === "number") return false;
      const isApplied = j.applied || appliedLiveIds.includes(j.id);
      if (isApplied) return false;
      
      if (selectedPortals.length > 0) {
        if (!selectedPortals.includes(j.portal)) return false;
      } else {
        if (selectedCategory !== "All") {
          const catPortals = PORTALS_BY_CATEGORY[selectedCategory] || [];
          if (!catPortals.includes(j.portal)) return false;
        }
      }
      
      if (!(j.match >= minMatch)) return false;
      
      if (timeFilter !== "all") {
        const postAgeInDays = getPostAgeInDays(j.postedAgo || j.posted_ago, j.created_at);
        if (timeFilter === "1" && postAgeInDays > 1) return false;
        if (timeFilter === "3" && postAgeInDays > 3) return false;
        if (timeFilter === "7" && postAgeInDays > 7) return false;
        if (timeFilter === "15" && postAgeInDays > 15) return false;
        if (timeFilter === "30" && postAgeInDays > 30) return false;
      }
      
      if (search) {
        const query = search.toLowerCase().trim();
        const portalMatch = j.portal?.toLowerCase().includes(query) ||
                            ((query.includes("nauk") || query.includes("naukar")) && j.portal === "Naukri.com") ||
                            ((query.includes("link") || query.includes("linked")) && j.portal === "LinkedIn Jobs");
        const titleMatch = j.title?.toLowerCase().includes(query);
        const companyMatch = j.company?.toLowerCase().includes(query);
        const tagMatch = j.tags?.some(t => t.toLowerCase().includes(query));
        if (!titleMatch && !companyMatch && !tagMatch && !portalMatch) return false;
      }
      
      return true;
    }).length;
  }, [jobs, selectedCategory, selectedPortals, minMatch, search, timeFilter, appliedLiveIds]);

  const fetchJobs = useCallback(async () => {
    try {
      const res = await fetch(API_BASE + "/jobs");
      if (res.ok) {
        const data = await res.json();
        if (data && data.length > 0) {
          setJobs(prev => {
            const existingIds = new Set(prev.map(j => j.id));
            const newJobs = data.filter(j => !existingIds.has(j.id));
            // Update applied status for any existing matching IDs
            const updatedPrev = prev.map(j => {
              const matched = data.find(x => x.id === j.id);
              if (matched) {
                return { ...j, ...matched };
              }
              return j;
            });
            return [...newJobs, ...updatedPrev];
          });
        }
      }
    } catch (e) {
      console.error("Error fetching jobs:", e);
    }
  }, []);

  const fetchStatus = useCallback(async () => {
    try {
      const res = await fetch(API_BASE + "/status");
      if (res.ok) {
        const data = await res.json();
        setSystemStatus(data);
      }
    } catch (e) {
      console.error("Error fetching status:", e);
    }
  }, []);

  const fetchPortalsSummary = useCallback(async () => {
    try {
      const res = await fetch(API_BASE + "/jobs/portals");
      if (res.ok) {
        const data = await res.json();
        setPortalsSummary(data);
      }
    } catch (e) {
      console.error("Error fetching portals summary:", e);
    }
  }, []);

  useEffect(() => {
    fetchJobs();
    fetchStatus();
    fetchPortalsSummary();
    const interval = setInterval(() => {
      fetchStatus();
      fetchPortalsSummary();
    }, 5000);
    return () => clearInterval(interval);
  }, [fetchJobs, fetchStatus, fetchPortalsSummary]);

  const handleLiveApply = useCallback((newJob) => {
    setJobs(prev => {
      if (prev.some(j => j.id === newJob.id)) {
        return prev.map(j => j.id === newJob.id ? { ...j, applied: true } : j);
      }
      return [...prev, newJob];
    });
    setAppliedLiveIds(prev => [...prev, newJob.id]);
    setNotifs(n => n + 1);
  }, []);

  const tabs = [
    { id:"dashboard",  label:"Command Center",   icon:"⬡" },
    { id:"livejobs",   label:"Live Job Feed",     icon:"🔴" },
    { id:"jarvis",     label:"JARVIS Chat",       icon:"◈" },
    { id:"automation", label:"Automation Hub",    icon:"⟳" },
    { id:"resume",     label:"Resume Manager",    icon:"📄" },
    { id:"tracker",    label:"Job Tracker",       icon:"📊" },
    { id:"tasks",      label:"Task Board",        icon:"✓"  },
    { id:"prep",       label:"DevOps Prep",       icon:"⌨"  },
    { id:"emails",     label:"Recruiter Emails",  icon:"✉"  },
  ];

  const css = darkMode ? {
    "--bg":"#080612","--surface":"#0f0d1f","--card-bg":"#13102a",
    "--border":"#1e1a3f","--text":"#e8e3ff","--muted":"#6b64a0","--accent":"#8B5CF6",
  } : {
    "--bg":"#F8FAFC","--surface":"#FFFFFF","--card-bg":"#FFFFFF",
    "--border":"#E2E8F0","--text":"#1a1a2e","--muted":"#64748B","--accent":"#8B5CF6",
  };

  const panelMap = {
    dashboard:  <Dashboard jobs={jobs} tasks={tasks} liveJobs={getFilteredJobsCount()} onApply={handleLiveApply} appliedIds={appliedLiveIds} systemStatus={systemStatus} portalsSummary={portalsSummary} scanning={scanning}/>,
    livejobs:   <LiveJobFeed 
                  jobs={jobs} 
                  setJobs={setJobs} 
                  onApply={handleLiveApply} 
                  appliedIds={appliedLiveIds} 
                  fetchJobs={fetchJobs} 
                  systemStatus={systemStatus}
                  selectedCategory={selectedCategory}
                  setSelectedCategory={setSelectedCategory}
                  selectedPortals={selectedPortals}
                  setSelectedPortals={setSelectedPortals}
                  minMatch={minMatch}
                  setMinMatch={setMinMatch}
                  search={search}
                  setSearch={setSearch}
                  timeFilter={timeFilter}
                  setTimeFilter={setTimeFilter}
                  sortBy={sortBy}
                  setSortBy={setSortBy}
                  portalsSummary={portalsSummary}
                  setPortalsSummary={setPortalsSummary}
                  scanning={scanning}
                  setScanning={setScanning}
                />,
    jarvis:     <JarvisChat/>,
    automation: <AutomationHub/>,
    resume:     <ResumeManager/>,
    tracker:    <JobTracker jobs={jobs} setJobs={setJobs}/>,
    tasks:      <TaskBoard tasks={tasks} setTasks={setTasks}/>,
    prep:       <DevOpsPrepQA/>,
    emails:     <RecruiterEmails/>,
  };

  return (
    <div style={{...css, background:"var(--bg)", minHeight:"100vh", fontFamily:"'Segoe UI', system-ui, sans-serif", color:"var(--text)"}}>
      <style>{`
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 99px; }
        @keyframes pulse { 0%,100%{transform:scale(0.8);opacity:0.5}50%{transform:scale(1.2);opacity:1} }
        @keyframes blink { 0%,100%{opacity:1}50%{opacity:0} }
        input::placeholder,textarea::placeholder{color:var(--muted);opacity:0.7}
        input,textarea,select{outline:none;}
      `}</style>

      {sidebarOpen && <div onClick={()=>setSidebarOpen(false)} style={{position:"fixed",inset:0,background:"#000a",zIndex:40}}/>}

      {/* Sidebar */}
      <div style={{position:"fixed",left:sidebarOpen?0:-250,top:0,bottom:0,width:250,background:"var(--surface)",borderRight:"1px solid var(--border)",zIndex:50,display:"flex",flexDirection:"column",transition:"left 0.25s ease",padding:"0 0 16px"}}>
        <div style={{padding:"18px 20px 14px",borderBottom:"1px solid var(--border)"}}>
          <div style={{display:"flex",alignItems:"center",gap:10}}>
            <div style={{width:34,height:34,borderRadius:10,background:"linear-gradient(135deg,#8B5CF6,#06b6d4)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:14,fontWeight:700,color:"#fff"}}>N</div>
            <div><div style={{fontSize:14,fontWeight:700,color:"var(--text)"}}>Naveen-AI</div><div style={{fontSize:10,color:"var(--muted)"}}>Career Command Center</div></div>
          </div>
        </div>
        <div style={{flex:1,overflowY:"auto",padding:"10px 10px"}}>
          {tabs.map(t=>(
            <button key={t.id} onClick={()=>{setTab(t.id);setSidebarOpen(false);}} style={{width:"100%",display:"flex",alignItems:"center",gap:10,padding:"10px 14px",borderRadius:10,background:tab===t.id?"#8B5CF620":"transparent",border:tab===t.id?"1px solid #8B5CF644":"1px solid transparent",color:tab===t.id?"#8B5CF6":"var(--muted)",cursor:"pointer",marginBottom:2,fontSize:13,textAlign:"left"}}>
              <span style={{fontSize:15}}>{t.icon}</span>
              {t.label}
              {t.id==="livejobs"&&<span style={{marginLeft:"auto",fontSize:10,padding:"2px 7px",borderRadius:99,background:"#4ade8022",color:"#4ade80",border:"1px solid #4ade8044"}}>{getFilteredJobsCount()}</span>}
            </button>
          ))}
        </div>
        <div style={{padding:"10px 14px",borderTop:"1px solid var(--border)"}}>
          <div style={{fontSize:10,color:"var(--muted)",marginBottom:6,textTransform:"uppercase",letterSpacing:"0.05em"}}>Anthropic API Key</div>
          <input
            type="password"
            value={apiKey}
            onChange={(e)=>{
              setApiKey(e.target.value);
              localStorage.setItem("anthropic_api_key", e.target.value);
            }}
            placeholder="sk-ant-..."
            style={{
              width:"100%",
              background:"var(--surface)",
              border:"1px solid var(--border)",
              borderRadius:6,
              padding:"6px 10px",
              fontSize:11,
              color:"var(--text)",
              fontFamily:"monospace"
            }}
          />
        </div>
        <div style={{padding:"12px 14px",borderTop:"1px solid var(--border)",display:"flex",gap:10,alignItems:"center"}}>
          <div style={{width:34,height:34,borderRadius:"50%",background:"linear-gradient(135deg,#8B5CF6,#06b6d4)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:12,fontWeight:700,color:"#fff",flexShrink:0}}>NK</div>
          <div style={{minWidth:0}}>
            <div style={{fontSize:12,fontWeight:600,color:"var(--text)"}}>Naveen Kumar</div>
            <div style={{fontSize:10,color:"#8B5CF6",overflow:"hidden",textOverflow:"ellipsis",whiteSpace:"nowrap"}}>naveendevops589@gmail.com</div>
            <div style={{fontSize:10,color:"#4ade80",marginTop:2}}>● Active Job Search</div>
          </div>
        </div>
      </div>

      {/* Main */}
      <div style={{marginLeft:0}}>
        {/* Header */}
        <div style={{position:"sticky",top:0,zIndex:30,background:"var(--surface)",borderBottom:"1px solid var(--border)",padding:"0 20px",height:56,display:"flex",alignItems:"center",gap:12}}>
          <button onClick={()=>setSidebarOpen(!sidebarOpen)} style={{width:36,height:36,borderRadius:8,background:"var(--card-bg)",border:"1px solid var(--border)",cursor:"pointer",display:"flex",alignItems:"center",justifyContent:"center",fontSize:16,color:"var(--text)"}}>☰</button>
          <div style={{flex:1,display:"flex",alignItems:"center",gap:8,minWidth:0}}>
            <div style={{width:26,height:26,borderRadius:7,background:"linear-gradient(135deg,#8B5CF6,#06b6d4)",display:"flex",alignItems:"center",justifyContent:"center",fontSize:11,fontWeight:700,color:"#fff",flexShrink:0}}>N</div>
            <span style={{fontSize:14,fontWeight:700,color:"var(--text)",flexShrink:0}}>Naveen-AI</span>
            <span style={{fontSize:11,display:"flex",alignItems:"center",gap:5,background:"var(--card-bg)",border:"1px solid var(--border)",borderRadius:99,padding:"3px 10px",whiteSpace:"nowrap",overflow:"hidden",textOverflow:"ellipsis",maxWidth:240}}>
              <span style={{fontSize:12}}>✉</span>
              <span style={{color:"#8B5CF6",fontWeight:500}}>naveendevops589@gmail.com</span>
            </span>
            {tab==="livejobs"&&<span style={{fontSize:11,padding:"3px 10px",borderRadius:99,background:"#4ade8018",color:"#4ade80",border:"1px solid #4ade8033",flexShrink:0}}>🔴 {getFilteredJobsCount()} live jobs</span>}
          </div>
          <button onClick={()=>setDarkMode(!darkMode)} style={{width:34,height:34,borderRadius:8,background:"var(--card-bg)",border:"1px solid var(--border)",cursor:"pointer",fontSize:15}}>{darkMode?"☀️":"🌙"}</button>
          <button onClick={()=>setTab("livejobs")} style={{position:"relative",width:34,height:34,borderRadius:8,background:"var(--card-bg)",border:"1px solid var(--border)",cursor:"pointer",fontSize:15}}>
            🔔
            <span style={{position:"absolute",top:4,right:4,width:14,height:14,borderRadius:"50%",background:"#f87171",fontSize:9,color:"#fff",display:"flex",alignItems:"center",justifyContent:"center"}}>{notifs}</span>
          </button>
        </div>

        {/* Tab bar */}
        <div style={{background:"var(--surface)",borderBottom:"1px solid var(--border)",padding:"0 16px",display:"flex",gap:2,overflowX:"auto"}}>
          {tabs.map(t=>(
            <button key={t.id} onClick={()=>setTab(t.id)} style={{padding:"10px 14px",whiteSpace:"nowrap",fontSize:12,fontWeight:tab===t.id?600:400,color:tab===t.id?"#8B5CF6":"var(--muted)",background:"transparent",border:"none",borderBottom:tab===t.id?"2px solid #8B5CF6":"2px solid transparent",cursor:"pointer",display:"flex",alignItems:"center",gap:5}}>
              {t.icon} {t.label}
              {t.id==="livejobs"&&<span style={{fontSize:9,padding:"1px 5px",borderRadius:99,background:"#4ade80",color:"#fff"}}>{getFilteredJobsCount()}</span>}
            </button>
          ))}
        </div>

        {/* Content */}
        <div style={{padding:"20px 20px 80px",maxWidth:1300}}>
          {panelMap[tab]}
        </div>
      </div>

      {/* Mobile Dock */}
      <div style={{position:"fixed",bottom:0,left:0,right:0,padding:"8px 12px 12px",background:"var(--surface)",borderTop:"1px solid var(--border)",display:"flex",justifyContent:"space-around",zIndex:40}}>
        {[["dashboard","⬡","Home"],["livejobs","🔴","Jobs"],["jarvis","◈","JARVIS"],["tracker","📊","Tracker"]].map(([id,icon,lbl])=>(
          <button key={id} onClick={()=>setTab(id)} style={{display:"flex",flexDirection:"column",alignItems:"center",gap:3,padding:"6px 12px",borderRadius:10,background:tab===id?"#8B5CF620":"transparent",border:"none",cursor:"pointer",color:tab===id?"#8B5CF6":"var(--muted)"}}>
            <span style={{fontSize:18}}>{icon}</span>
            <span style={{fontSize:10}}>{lbl}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
