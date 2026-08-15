# VIDIT
### Variegated Intelligence & Data for Institutional Tracking

> **Notice:** VIDIT is an institutional development project maintained by the **IoTronics Club, NMIT**. The system is currently in its **initial prototyping phase**. Source repositories, firmware, and detailed hardware designs remain private until validation is complete.

---

## 1. Executive Summary

**VIDIT** is an RFID-enabled identification and data framework designed to unify campus digital identity. Rather than storing sensitive data locally on credentials, VIDIT uses RFID cards strictly as lightweight tokens to interface with a centralized backend for authentication, service delivery, and institutional analytics.

### Key Objectives
* **Unified Identity:** Consolidate disparate campus systems (attendance, library, cafeteria, access control).
* **Decoupled Security:** Map secure backend records to card UIDs without storing PII on physical credentials.
* **Operational Insights:** Aggregate usage data to generate campus-wide analytics and predictive crowd models.

---

## 2. System Architecture

```text
+-------------------+      +-------------------+      +-------------------+
|                   |      |                   |      |                   |
|  RFID Credential  | ---> |    Edge Reader    | ---> |    Backend API    |
|  (Physical UID)   |      | (Microcontroller) |      |     (FastAPI)     |
|                   |      |                   |      |                   |
+-------------------+      +-------------------+      +---------+---------+
                                                                |
                   +--------------------------------------------+--------------------------------------------+
                   |                                            |                                            |
                   v                                            v                                            v
          +-----------------+                          +-----------------+                          +-----------------+
          |                 |                          |                 |                          |                 |
          |    Database     |                          |    Services     |                          |    Analytics    |
          |  (SQLite/SQL)   |                          |  (Access/Mess)  |                          |  & Prediction   |
          |                 |                          |                 |                          |                 |
          +-----------------+                          +-----------------+                          +-----------------+
```

### Core Architecture Layers

| Layer | Technology | Primary Function |
| :--- | :--- | :--- |
| **Physical & Edge** | Microcontroller, RFID Scanner (C/C++) | Captures card UID and issues secure HTTP requests. |
| **Application / API** | FastAPI, Pydantic, Uvicorn (Python) | Validates payloads, processes business logic, and manages auth. |
| **Data Layer** | SQLite *(Dev)* / PostgreSQL *(Target Prod)* | Maintains student profiles, card-to-identity mappings, and event logs. |
| **Services & Insights**| REST Endpoints & Analytical Models | Powers downstream institutional services and crowd-estimation models. |

---

## 3. Identification Workflow

1. **Card Presentation:** RFID card is detected by the edge reader.
2. **UID Ingestion:** Edge controller extracts the identifier and dispatches an HTTP POST request to the API.
3. **Validation & Lookup:** The FastAPI backend authenticates the request and queries the database.
4. **Resolution:** 
   - **Match Found:** Returns identity authorization (`ALLOWED`) and associated profile data.
   - **No Match:** Returns an unauthorized response (`DENIED`).
5. **Action Execution:** Edge device triggers local feedback (e.g., relay toggle, indicator LED).

---

## 4. Planned Campus Services

* **Institutional Access Control:** Unified gate and facility entry verification.
* **Automated Attendance:** Centralized logging across departments without duplicate databases.
* **Cafeteria & Mess Analytics:** Meal tracking and historical load analysis for predictive crowd estimation.
* **Library Management:** Simplified checkout workflows tied to global digital identities.

---

## 5. Technology Stack

* **Embedded Systems:** Microcontroller (ESP32/Arduino-compatible), RFID Hardware, C/C++
* **Backend:** Python, FastAPI, Pydantic, Uvicorn
* **Data Storage:** SQLite (Prototyping), Relational SQL (Production target)
* **Tooling:** Visual Studio Code, Postman, Git

---

## 6. Project Roadmap

```text
[Phase 1] Architecture Design & Specs
   |
   v
[Phase 2] Hardware & API Prototyping (Current Phase)
   |
   v
[Phase 3] Institutional Service Integration
   |
   v
[Phase 4] Security Hardening & Edge Encryption
   |
   v
[Phase 5] Campus Pilot Deployment
```

---

## 7. Security & Privacy Strategy

* **Zero PII on Credentials:** Cards hold only non-identifying UIDs.
* **Centralized Authorization:** Access policies and credentials are evaluated server-side.
* **Hardening Measures:** Planned role-based access control (RBAC), encrypted payload transmission, and UID-spoofing mitigation.

---

## 8. Governance & Maintainers

* **Organization:** IoTronics Club
* **Institution:** Nitte Meenakshi Institute of Technology (NMIT)
* **Status:** Active Prototyping

*Disclaimer: This document outlines internal development specifications. Architecture, endpoints, and deployment roadmaps are subject to revision prior to institutional pilot testing.*
