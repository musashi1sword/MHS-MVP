# MHS MVP Development Journal

**Project:** Mwafrika Health Services (MHS) - Investor Demo MVP
**Start Date:** [Insert Date]

---

## Entry 1: The Vision & Architecture
- Established the core problem: Fragmented healthcare in East Africa (geographic, financial, clinical capacity).
- Finalized the three-tier ecosystem: Patient access (urban/rural) -> Clinical workflow -> Pharmacy/Metrics.
- Defined the technical stack: Django backend, React frontend, dual-mode WebRTC video, mock USSD gateway.

## Entry 2: Setting up the Environment (Linux Mint)
- Encountered missing global dependencies (Node.js, pip3) during the initial build.
- Successfully bootstrapped local environments (`.venv` and `.nodeenv`) to bypass system restrictions.

## Entry 3: The Core MVP Build (Scaffolding)
- Successfully initialized the full stack using Claude Code.
- **Result:** 142 files created. 
- **Key Features Implemented:** 
  - Role-based authentication (Patient, Clinician, CHW, Admin).
  - Appointment scheduling and booking.
  - Real-time WebRTC video consultations.
  - Allergy / Interaction safety layer (Blocking & auditing).
  - E-Prescription generation & Pharmacy routing.
  - Live Metrics Dashboard.

## Entry 4: Validating the Flow (Test Phase)
- Successfully executed the end-to-end demo flow: 
  - Patient Booking -> Video Visit -> E-Prescription -> Pharmacy Handoff.
- Confirmed the complete loop is working locally without errors.
- **Next Step:** Prepare for live investor pitch with Cloudflare Tunnel.

## Entry 5: Production Deployment Prep (Hetzner + TLS)

- Drafted a reverse-proxy/TLS config for a Hetzner deployment at `deploy/nginx.conf.example`: HTTP→HTTPS redirect, static frontend serving, `/api/` and `/ws/` proxied to Daphne (ASGI).
- Since the plan is to reach the server by IP (`2.29.22.111`) rather than a domain initially, the config uses a self-signed certificate — Let's Encrypt only issues certs for domain names, not bare IPs.
- Set production values in `backend/.env` (untracked): a generated `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` scoped to `2.29.22.111`.
- **Not yet done / unverified as of this entry:** the server has not actually been provisioned or reached from this environment, Nginx has not been installed or started anywhere, and no DNS record connecting `mwafrikahealth.com` to `2.29.22.111` has been checked or confirmed. Deployment is a real task, not just config — this entry documents the prep work, not a live site.
- **Next Step:** Actually provision the Hetzner box, apply the Nginx config, verify `https://2.29.22.111` responds, and (if `mwafrikahealth.com` is meant to point here) confirm the DNS A record before treating it as live.

## Entry 6: Live Deployment to Hetzner Cloud (mwafrikahealth.com)

- **Server provisioned and deployed.** The Hetzner Cloud box is now live, the stack is running behind Nginx (static frontend + `/api/` and `/ws/` proxied to Daphne), and the end-to-end demo flow works over the public URL.
- **Real SSL certificate installed.** Now that a domain is in play, we moved off the self-signed cert from Entry 5 and issued a proper Let's Encrypt certificate for `mwafrikahealth.com` (and `www.`). `https://mwafrikahealth.com` serves with a valid, trusted chain and HTTP redirects to HTTPS.
- **DNS resolved.** Added/corrected the A records so `mwafrikahealth.com` and `www.mwafrikahealth.com` point at the server. Once propagation completed, Let's Encrypt's HTTP-01 challenge succeeded and the domain resolved correctly from outside.
- **Vite `allowedHosts` issue fixed.** The dev server was returning "Blocked request. This host is not allowed" when reached via the domain — Vite rejects any request whose `Host` header isn't in its allowlist. Added `allowedHosts: ['mwafrikahealth.com', 'www.mwafrikahealth.com', '2.29.22.111']` to the `server` block in `frontend/vite.config.ts`, which cleared it.
- Also updated `backend/.env` `DJANGO_ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` to include the domain alongside the bare IP.
- **Status:** `https://mwafrikahealth.com` is live and demo-ready with valid TLS.

