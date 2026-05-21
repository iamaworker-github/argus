---
name: recon
description: OSINT, subdomain enumeration, port scanning, technology fingerprinting
category: tooling
---

# Reconnaissance Methodology

## Attack Surface
Reconnaissance is the first phase of any security assessment, mapping the target's attack surface.

## External Recon
1. **Subdomain Enumeration**
   - Passive: Certificate Transparency (crt.sh), DNS dumpster, Shodan, Censys
   - Active: Subfinder, DNS brute-force with common wordlists
   - Permutation: Generate permutations of discovered subdomains

2. **Technology Detection**
   - HTTP headers: Server, X-Powered-By, Set-Cookie
   - WAF detection: wafw00f
   - JavaScript library analysis: Retire.js
   - Framework detection from HTML/CSS patterns

3. **Port Scanning**
   - Top 1000 ports with service detection
   - SYN scan for speed (requires root)
   - Service version detection on open ports
   - NSE scripts for vulnerability detection

4. **Web Crawling**
   - Spider all accessible pages
   - Parse JS files for API endpoints
   - Look for hidden directories
   - Archive analysis (Wayback Machine)

## Internal Recon
- Network segmentation testing
- Service discovery on internal networks
- Active directory enumeration (if applicable)
- Cloud provider metadata endpoints

## Validation
- Confirm DNS resolution for discovered subdomains
- Verify HTTP response for scanned ports
- Screenshot discovered web services
- Prioritize live, responsive targets
