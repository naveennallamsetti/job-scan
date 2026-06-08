import logging
import hashlib
from backend.global_graph.ontology import hard_normalize, soft_normalize_title, normalize_date_iso

def route_to_health(envelope):
    logging.error(f"[HEALTH_LAYER] Envelope from {envelope.get('source')} FAILED due to {envelope.get('reason')}")

class GlobalJobGraph:
    def __init__(self):
        self.canonical_jobs = {}
        
    def _generate_fingerprint(self, title, company, location):
        raw = hard_normalize(title) + hard_normalize(company) + hard_normalize(location)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def ingest_envelope(self, envelope, ingestion_layer):
        status = envelope.get("status", "FAILED")
        source = envelope.get("source", "unknown")
        
        # RULE 3 - FIX PARTIAL STATE HANDLING
        if status == "FAILED":
            route_to_health(envelope)
            return
            
        if status == "NO_RESULTS":
            logging.info(f"[GRAPH] Market empty signal received from {source}")
            return
            
        if status not in ["SUCCESS", "PARTIAL"]:
            return

        raw_jobs = envelope.get("jobs", [])
        
        for job in raw_jobs:
            title = job.get("title", "").strip()
            company = job.get("company", "").strip()
            url = job.get("url", "").strip()
            
            # RULE 7 - INGESTION VALIDATION GATE
            if not title or not company or not url:
                logging.warning(f"[GRAPH_GATE] Dropped job missing critical fields from {source}")
                continue
                
            fp = self._generate_fingerprint(title, company, job.get("location", ""))
            job["job_fingerprint"] = fp
            
            # RULE 2 - PRESERVE REAL SOURCE IDENTITY
            job_source = job.get("source", source)
            
            if fp not in self.canonical_jobs:
                self.canonical_jobs[fp] = {
                    "title": title,
                    "soft_title": soft_normalize_title(title),
                    "company": company,
                    "location": job.get("location", ""),
                    "url": url, 
                    "posted_date": normalize_date_iso(job.get("posted_date", "")),
                    "salary": job.get("salary"),
                    "job_fingerprint": fp,
                    "sources": [job_source],
                    "layer_presence": {ingestion_layer: True},
                    "graph_score": 0
                }
            else:
                canonical = self.canonical_jobs[fp]
                if job_source not in canonical["sources"]:
                    canonical["sources"].append(job_source)
                canonical["layer_presence"][ingestion_layer] = True
                if ingestion_layer == "PHASE_B":
                    canonical["url"] = url 
                    
    def calculate_rankings(self):
        for fp, job in self.canonical_jobs.items():
            sources = job.get("sources", [])
            # RULE 9 - FIX SCORING SYSTEM (REMOVE UNBOUND INFLATION)
            # RULE 5 - REMOVE ATS SCORING BIAS
            ats_quality_score = min(15, len(sources) * 5)
            
            posted = job.get("posted_date")
            freshness_score = 25 if posted and "Z" in str(posted) else 5
            
            freshness = min(25, freshness_score)
            diversity = min(25, (len(sources) - 1) * 10)
            quality = min(20, ats_quality_score)
            recency = min(20, 10) # Stub recency
            
            graph_score = min(100, freshness + diversity + quality + recency)
            job["graph_score"] = graph_score
            
    def export_unified_feed(self):
        self.calculate_rankings()
        ranked_jobs = sorted(self.canonical_jobs.values(), key=lambda x: x["graph_score"], reverse=True)
        return {"total_canonical_jobs": len(ranked_jobs), "jobs": ranked_jobs}
