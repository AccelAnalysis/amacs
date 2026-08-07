# Fortune 1000 2026 breadth-pass findings

## Outcome

The current 2026 roster contains 1,000 organizations and 74 primary activity labels. A deterministic breadth pass against AMACS 0.2.0 found:

| Coverage in AMACS 0.2.0 | Activity labels | Organizations |
|---|---:|---:|
| Direct | 13 | 154 |
| Partial | 35 | 524 |
| No direct concept | 26 | 322 |
| **Total** | **74** | **1,000** |

The primary deficiency was structural, not merely lexical. AMACS 0.2.0 represented procured services and supporting functions well, but frequently lacked the core market operations by which large enterprises create, manufacture, operate, distribute, underwrite, or sell their principal products and services.

## Candidate 0.3.0 refinement

The breadth pass produced 25 additive families and 115 draft capabilities across 12 existing AMACS domains. The additions cover recurring enterprise market activities in:

- transportation-equipment, semiconductor, computing, communications, chemical, pharmaceutical, medical-device, material, consumer-product, and industrial-equipment manufacturing;
- banking, lending, underwriting, reinsurance, securities, investment, payment-network, financial-data, and asset-finance operations;
- energy exploration, production, refining, utility, midstream, terminal, pipeline, and mineral-extraction operations;
- retail, e-commerce, restaurant, lodging, casino, leisure, funeral, cremation, cemetery, and memorial operations;
- digital products, cloud services, marketplaces, discovery, social media, advertising platforms, telecommunications, media, publishing, printing, and streaming;
- airline, rail, maritime, package, postal, commercial-vehicle leasing, and wholesale distribution;
- health-plan, managed-care, pharmacy-benefit, hospital, outpatient, and senior-living operations;
- real estate development, homebuilding, ownership, leasing, investment, and trust operations; and
- primary agriculture, forestry, enterprise outsourcing, staffing, and formal education delivery.

Every source activity label now has at least one direct AMACS concept available for candidate mapping. This means the taxonomy can represent the roster's primary-activity breadth; it does **not** mean all 1,000 organizations have been verified to possess every candidate capability.

## Evidence and legal-entity findings

The exercise also exposed a separate evidence-architecture requirement. A ranked reporting entity may contain operating segments, subsidiaries, affiliates, brands, marketplaces, or acquired businesses. A consolidated rank cannot establish which legal or operating entity performs a capability.

AMACS therefore adds a research-only organization taxonomy observation contract that records:

- the entity scope being observed;
- the source, access date, locator, and content hash;
- the observation method;
- candidate AMACS mappings and confidence;
- the relationship between the observed entity and the possible capability; and
- a mandatory `not_for_profile_import: true` safeguard.

The generated 1,000-record corpus creates zero production organization-capability assertions.

## Sources and boundaries

- The authoritative current-list reference is the [2026 Fortune 500 ranking](https://fortune.com/ranking/fortune500/2026/). Fortune's company profiles and filtered ranking pages confirm the extended list boundaries, including [Louisiana-Pacific at position 1,000](https://fortune.com/company/louisiana-pacific/) and Knight-Swift Transportation Holdings at position 501.
- The machine-readable breadth roster is retrieved from [US500's 2026 Fortune 1000 page](https://us500.com/fortune-1000-companies) and its public data endpoint. The reviewed payload hash is recorded in the corpus manifest; raw third-party data and financial measures are not stored in this repository.
- First-party evidence is required for deeper organization definitions. For example, [Louisiana-Pacific describes itself as a building-products manufacturer](https://investor.lpcorp.com/news-releases/news-release-details/lp-building-solutions-reports-first-quarter-2026-results-updates/), supporting the new building-product-manufacturing concept. [Service Corporation International describes its funeral, cremation, and cemetery operations](https://www.sci-corp.com/), which exposed a gap hidden behind the source label “Miscellaneous.”
- FORTUNE is a trademark of Fortune Media IP Limited. AMACS and Accel Analysis are not affiliated with or endorsed by Fortune or US500.
