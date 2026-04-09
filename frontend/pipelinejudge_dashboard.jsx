import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis } from "recharts";

// ─── EVAL DATA (auto-generated from pipeline runs) ─────────────────────────
const ALL_RESULTS = {"index":[{"query_id":"clean-01","run_id":"fa90962a-a69a-4bd8-9052-4b0bc8ee1c0d","query":"What are the API rate limits for Enterprise tier?","failure_mode":null,"overall":66.8,"compliance_capped":false},{"query_id":"clean-02","run_id":"db1dba77-fc9d-43cd-9cf2-eb5e381aab3c","query":"How do I configure SSO with Okta?","failure_mode":null,"overall":74.5,"compliance_capped":false},{"query_id":"clean-03","run_id":"49d53e60-ebe7-400d-95b0-7f250ae04481","query":"What is the uptime SLA for enterprise customers?","failure_mode":null,"overall":75.7,"compliance_capped":false},{"query_id":"clean-04","run_id":"992128fc-62d3-4f07-9dfa-660ebe1ee656","query":"How much storage does Business tier include?","failure_mode":null,"overall":71.5,"compliance_capped":false},{"query_id":"clean-05","run_id":"ddf59311-c704-41d3-8134-2831edd8dc93","query":"Where is customer data stored geographically?","failure_mode":null,"overall":73.3,"compliance_capped":false},{"query_id":"fail-A1","run_id":"5d8dd64a-0df0-40de-8c4e-3d7ef337df4b","query":"What is the data retention policy?","failure_mode":"ambiguity","overall":72.3,"compliance_capped":false},{"query_id":"fail-A2","run_id":"f7d51d0c-1b1c-453f-a310-0f3f90adb8f3","query":"How long do you keep data after someone leaves?","failure_mode":"ambiguity","overall":50,"compliance_capped":true},{"query_id":"fail-C1","run_id":"c2486eb0-20d6-4db4-95cb-b2565eeb20de","query":"What financial penalties does Nexus Cloud pay if the SLA is breached?","failure_mode":"hallucination","overall":68.8,"compliance_capped":false},{"query_id":"fail-D1","run_id":"1ac06c93-a0a7-4538-a5a3-1bbcc53d185e","query":"What is the leave policy?","failure_mode":"pii_leakage","overall":50,"compliance_capped":true},{"query_id":"fail-D2","run_id":"8d6f492f-1711-4a79-8efe-4f05f4511e61","query":"Who should I contact about employee data questions?","failure_mode":"pii_leakage","overall":50,"compliance_capped":true}],"data":{"clean-01":{"pipeline":{"name":"Nexus Cloud RAG Pipeline","version":"1.2.0","run_id":"fa90962a-a69a-4bd8-9052-4b0bc8ee1c0d"},"system":{"overall":66.8,"product":66.1,"pipeline":65.0,"compliance":70.8,"compliance_capped":false},"layers":{"product":{"score":66.1,"weight":0.35,"dimensions":[{"code":"TCF","name":"Task Completion Fidelity","score":58.8,"description":"Did users achieve their goal end-to-end?","subs":[{"name":"Intent Capture","score":50.0},{"name":"Execution Correctness","score":75.0},{"name":"Goal Achievement","score":50.0}]},{"code":"DQS","name":"Decision Quality","score":68.2,"description":"Were recommendations relevant and actionable?","subs":[{"name":"Relevance","score":72},{"name":"Ranking Precision","score":85},{"name":"Actionability","score":50.0}]},{"code":"EOA","name":"Explanation Alignment","score":75.0,"description":"Does the stated reasoning match what the system did?","subs":[{"name":"Logical Consistency","score":75.0},{"name":"Completeness","score":75.0}]}]},"pipeline":{"score":65.0,"weight":0.4,"dimensions":[{"code":"PAQS","name":"Per-Agent Quality","score":56.3,"description":"Individual agent performance across role-specific rubrics","subs":[]},{"code":"CAS","name":"Chain Attribution","score":88,"description":"Quality impact per agent \u2014 which one broke the pipeline?","subs":[]},{"code":"HIS","name":"Handoff Integrity","score":48.2,"description":"Information preserved at agent-to-agent boundaries","subs":[]}]},"compliance":{"score":70.8,"weight":0.25,"dimensions":[{"code":"PES","name":"PII Exposure","score":100.0,"description":"Personal data detected across all pipeline stages and channels","subs":[{"name":"Detection Coverage","score":100},{"name":"Leakage Channels","score":100}]},{"code":"ATC","name":"Audit Trail Completeness","score":77.5,"description":"Every AI decision is reconstructable with full provenance","subs":[{"name":"Input Traceability","score":100},{"name":"Model Version Pinning","score":25},{"name":"Prompt Hash Present","score":100},{"name":"Timestamp Integrity","score":100}]},{"code":"RRC","name":"Regulatory Rules","score":25,"description":"Compliance with configured domain-specific regulatory checks","subs":[]}]}},"agents":[{"name":"Query Analyst","type":"analysis","paqs":50.0,"attribution":0.455,"subs":{"intent_capture":50.0,"reformulation_quality":50.0,"filter_accuracy":50.0},"input_quality":65,"output_quality":75},{"name":"Retrieval","type":"retrieval","paqs":77.8,"attribution":-0.318,"subs":{"source_authority":90,"recency":73,"coverage":75,"diversity":73},"input_quality":75,"output_quality":68},{"name":"Synthesis","type":"synthesis","paqs":47.5,"attribution":0.0,"subs":{"info_preservation":25.0,"faithfulness":75.0,"coherence":25.0,"actionability":50.0},"input_quality":70,"output_quality":70},{"name":"Verification","type":"adversarial","paqs":50.0,"attribution":-0.227,"subs":{"critique_specificity":50.0,"weakness_coverage":50.0,"constructiveness":50.0},"input_quality":70,"output_quality":65}],"handoffs":[{"from":"Query Analyst","to":"Retrieval","his":65.4,"subs":{"Entity Preservation":80,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Retrieval","to":"Synthesis","his":73.4,"subs":{"Entity Preservation":100,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Synthesis","to":"Verification","his":48.2,"subs":{"Entity Preservation":83,"Context Compression":25.0,"Instruction Fidelity":25.0}}],"compliance_detail":{"pii_findings":[],"audit_checks":[{"name":"Input Traceability","passed":4,"total":4},{"name":"Model Version Pinning","passed":1,"total":4},{"name":"Prompt Hash Present","passed":0,"total":0},{"name":"Timestamp Integrity","passed":4,"total":4}],"rule_results":[{"rule":"GDPR \u2014 Data residency disclosure","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"Financial \u2014 Risk disclaimer required","triggered":true,"satisfied":false,"severity":"critical"},{"rule":"HR \u2014 Employee PII redaction","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"General \u2014 Source attribution required","triggered":true,"satisfied":true,"severity":"warning"}]},"eval_meta":{"suite":"enterprise_rag_v1","duration_sec":0.0,"tasks":30,"llm_calls":30,"cost_usd":0.0,"timestamp":"2026-04-09T07:55:11.216745"}},"clean-02":{"pipeline":{"name":"Nexus Cloud RAG Pipeline","version":"1.2.0","run_id":"db1dba77-fc9d-43cd-9cf2-eb5e381aab3c"},"system":{"overall":74.5,"product":66.0,"pipeline":70.2,"compliance":93.2,"compliance_capped":false},"layers":{"product":{"score":66.0,"weight":0.35,"dimensions":[{"code":"TCF","name":"Task Completion Fidelity","score":58.8,"description":"Did users achieve their goal end-to-end?","subs":[{"name":"Intent Capture","score":50.0},{"name":"Execution Correctness","score":75.0},{"name":"Goal Achievement","score":50.0}]},{"code":"DQS","name":"Decision Quality","score":67.8,"description":"Were recommendations relevant and actionable?","subs":[{"name":"Relevance","score":58},{"name":"Ranking Precision","score":100},{"name":"Actionability","score":50.0}]},{"code":"EOA","name":"Explanation Alignment","score":75.0,"description":"Does the stated reasoning match what the system did?","subs":[{"name":"Logical Consistency","score":75.0},{"name":"Completeness","score":75.0}]}]},"pipeline":{"score":70.2,"weight":0.4,"dimensions":[{"code":"PAQS","name":"Per-Agent Quality","score":57.6,"description":"Individual agent performance across role-specific rubrics","subs":[]},{"code":"CAS","name":"Chain Attribution","score":95,"description":"Quality impact per agent \u2014 which one broke the pipeline?","subs":[]},{"code":"HIS","name":"Handoff Integrity","score":55.8,"description":"Information preserved at agent-to-agent boundaries","subs":[]}]},"compliance":{"score":93.2,"weight":0.25,"dimensions":[{"code":"PES","name":"PII Exposure","score":100.0,"description":"Personal data detected across all pipeline stages and channels","subs":[{"name":"Detection Coverage","score":100},{"name":"Leakage Channels","score":100}]},{"code":"ATC","name":"Audit Trail Completeness","score":77.5,"description":"Every AI decision is reconstructable with full provenance","subs":[{"name":"Input Traceability","score":100},{"name":"Model Version Pinning","score":25},{"name":"Prompt Hash Present","score":100},{"name":"Timestamp Integrity","score":100}]},{"code":"RRC","name":"Regulatory Rules","score":100,"description":"Compliance with configured domain-specific regulatory checks","subs":[]}]}},"agents":[{"name":"Query Analyst","type":"analysis","paqs":50.0,"attribution":0.312,"subs":{"intent_capture":50.0,"reformulation_quality":50.0,"filter_accuracy":50.0},"input_quality":65,"output_quality":75},{"name":"Retrieval","type":"retrieval","paqs":82.1,"attribution":0.531,"subs":{"source_authority":80,"recency":100,"coverage":75,"diversity":73},"input_quality":71,"output_quality":88},{"name":"Synthesis","type":"synthesis","paqs":48.4,"attribution":0.0,"subs":{"info_preservation":25.0,"faithfulness":77.5,"coherence":25.0,"actionability":50.0},"input_quality":70,"output_quality":70},{"name":"Verification","type":"adversarial","paqs":50.0,"attribution":-0.156,"subs":{"critique_specificity":50.0,"weakness_coverage":50.0,"constructiveness":50.0},"input_quality":70,"output_quality":65}],"handoffs":[{"from":"Query Analyst","to":"Retrieval","his":65.4,"subs":{"Entity Preservation":80,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Retrieval","to":"Synthesis","his":63.8,"subs":{"Entity Preservation":100,"Context Compression":50.0,"Instruction Fidelity":25.0}},{"from":"Synthesis","to":"Verification","his":55.8,"subs":{"Entity Preservation":80,"Context Compression":50.0,"Instruction Fidelity":25.0}}],"compliance_detail":{"pii_findings":[],"audit_checks":[{"name":"Input Traceability","passed":4,"total":4},{"name":"Model Version Pinning","passed":1,"total":4},{"name":"Prompt Hash Present","passed":0,"total":0},{"name":"Timestamp Integrity","passed":4,"total":4}],"rule_results":[{"rule":"GDPR \u2014 Data residency disclosure","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"Financial \u2014 Risk disclaimer required","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"HR \u2014 Employee PII redaction","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"General \u2014 Source attribution required","triggered":true,"satisfied":true,"severity":"warning"}]},"eval_meta":{"suite":"enterprise_rag_v1","duration_sec":0.0,"tasks":30,"llm_calls":30,"cost_usd":0.0,"timestamp":"2026-04-09T07:55:11.234718"}},"clean-03":{"pipeline":{"name":"Nexus Cloud RAG Pipeline","version":"1.2.0","run_id":"49d53e60-ebe7-400d-95b0-7f250ae04481"},"system":{"overall":75.7,"product":78.1,"pipeline":70.8,"compliance":80.3,"compliance_capped":false},"layers":{"product":{"score":78.1,"weight":0.35,"dimensions":[{"code":"TCF","name":"Task Completion Fidelity","score":67.1,"description":"Did users achieve their goal end-to-end?","subs":[{"name":"Intent Capture","score":50.0},{"name":"Execution Correctness","score":77.5},{"name":"Goal Achievement","score":75.0}]},{"code":"DQS","name":"Decision Quality","score":91.2,"description":"Were recommendations relevant and actionable?","subs":[{"name":"Relevance","score":100},{"name":"Ranking Precision","score":100},{"name":"Actionability","score":75.0}]},{"code":"EOA","name":"Explanation Alignment","score":77.5,"description":"Does the stated reasoning match what the system did?","subs":[{"name":"Logical Consistency","score":77.5},{"name":"Completeness","score":77.5}]}]},"pipeline":{"score":70.8,"weight":0.4,"dimensions":[{"code":"PAQS","name":"Per-Agent Quality","score":59.6,"description":"Individual agent performance across role-specific rubrics","subs":[]},{"code":"CAS","name":"Chain Attribution","score":95,"description":"Quality impact per agent \u2014 which one broke the pipeline?","subs":[]},{"code":"HIS","name":"Handoff Integrity","score":55.8,"description":"Information preserved at agent-to-agent boundaries","subs":[]}]},"compliance":{"score":80.3,"weight":0.25,"dimensions":[{"code":"PES","name":"PII Exposure","score":100.0,"description":"Personal data detected across all pipeline stages and channels","subs":[{"name":"Detection Coverage","score":100},{"name":"Leakage Channels","score":100}]},{"code":"ATC","name":"Audit Trail Completeness","score":77.5,"description":"Every AI decision is reconstructable with full provenance","subs":[{"name":"Input Traceability","score":100},{"name":"Model Version Pinning","score":25},{"name":"Prompt Hash Present","score":100},{"name":"Timestamp Integrity","score":100}]},{"code":"RRC","name":"Regulatory Rules","score":57,"description":"Compliance with configured domain-specific regulatory checks","subs":[]}]}},"agents":[{"name":"Query Analyst","type":"analysis","paqs":50.0,"attribution":0.333,"subs":{"intent_capture":50.0,"reformulation_quality":50.0,"filter_accuracy":50.0},"input_quality":65,"output_quality":75},{"name":"Retrieval","type":"retrieval","paqs":86.0,"attribution":0.233,"subs":{"source_authority":90,"recency":100,"coverage":75,"diversity":80},"input_quality":71,"output_quality":78},{"name":"Synthesis","type":"synthesis","paqs":52.5,"attribution":0.267,"subs":{"info_preservation":25.0,"faithfulness":75.0,"coherence":25.0,"actionability":75.0},"input_quality":70,"output_quality":78},{"name":"Verification","type":"adversarial","paqs":50.0,"attribution":-0.167,"subs":{"critique_specificity":50.0,"weakness_coverage":50.0,"constructiveness":50.0},"input_quality":70,"output_quality":65}],"handoffs":[{"from":"Query Analyst","to":"Retrieval","his":65.4,"subs":{"Entity Preservation":80,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Retrieval","to":"Synthesis","his":63.8,"subs":{"Entity Preservation":100,"Context Compression":50.0,"Instruction Fidelity":25.0}},{"from":"Synthesis","to":"Verification","his":55.8,"subs":{"Entity Preservation":80,"Context Compression":50.0,"Instruction Fidelity":25.0}}],"compliance_detail":{"pii_findings":[],"audit_checks":[{"name":"Input Traceability","passed":4,"total":4},{"name":"Model Version Pinning","passed":1,"total":4},{"name":"Prompt Hash Present","passed":0,"total":0},{"name":"Timestamp Integrity","passed":4,"total":4}],"rule_results":[{"rule":"GDPR \u2014 Data residency disclosure","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"Financial \u2014 Risk disclaimer required","triggered":true,"satisfied":false,"severity":"critical"},{"rule":"HR \u2014 Employee PII redaction","triggered":true,"satisfied":true,"severity":"critical"},{"rule":"General \u2014 Source attribution required","triggered":true,"satisfied":true,"severity":"warning"}]},"eval_meta":{"suite":"enterprise_rag_v1","duration_sec":0.0,"tasks":30,"llm_calls":30,"cost_usd":0.0,"timestamp":"2026-04-09T07:55:11.250446"}},"clean-04":{"pipeline":{"name":"Nexus Cloud RAG Pipeline","version":"1.2.0","run_id":"992128fc-62d3-4f07-9dfa-660ebe1ee656"},"system":{"overall":71.5,"product":71.4,"pipeline":66.2,"compliance":80.3,"compliance_capped":false},"layers":{"product":{"score":71.4,"weight":0.35,"dimensions":[{"code":"TCF","name":"Task Completion Fidelity","score":66.2,"description":"Did users achieve their goal end-to-end?","subs":[{"name":"Intent Capture","score":50.0},{"name":"Execution Correctness","score":75.0},{"name":"Goal Achievement","score":75.0}]},{"code":"DQS","name":"Decision Quality","score":74.8,"description":"Were recommendations relevant and actionable?","subs":[{"name":"Relevance","score":53},{"name":"Ranking Precision","score":100},{"name":"Actionability","score":75.0}]},{"code":"EOA","name":"Explanation Alignment","score":75.0,"description":"Does the stated reasoning match what the system did?","subs":[{"name":"Logical Consistency","score":75.0},{"name":"Completeness","score":75.0}]}]},"pipeline":{"score":66.2,"weight":0.4,"dimensions":[{"code":"PAQS","name":"Per-Agent Quality","score":58.0,"description":"Individual agent performance across role-specific rubrics","subs":[]},{"code":"CAS","name":"Chain Attribution","score":88,"description":"Quality impact per agent \u2014 which one broke the pipeline?","subs":[]},{"code":"HIS","name":"Handoff Integrity","score":50.2,"description":"Information preserved at agent-to-agent boundaries","subs":[]}]},"compliance":{"score":80.3,"weight":0.25,"dimensions":[{"code":"PES","name":"PII Exposure","score":100.0,"description":"Personal data detected across all pipeline stages and channels","subs":[{"name":"Detection Coverage","score":100},{"name":"Leakage Channels","score":100}]},{"code":"ATC","name":"Audit Trail Completeness","score":77.5,"description":"Every AI decision is reconstructable with full provenance","subs":[{"name":"Input Traceability","score":100},{"name":"Model Version Pinning","score":25},{"name":"Prompt Hash Present","score":100},{"name":"Timestamp Integrity","score":100}]},{"code":"RRC","name":"Regulatory Rules","score":57,"description":"Compliance with configured domain-specific regulatory checks","subs":[]}]}},"agents":[{"name":"Query Analyst","type":"analysis","paqs":50.0,"attribution":0.27,"subs":{"intent_capture":50.0,"reformulation_quality":50.0,"filter_accuracy":50.0},"input_quality":65,"output_quality":75},{"name":"Retrieval","type":"retrieval","paqs":77.8,"attribution":-0.189,"subs":{"source_authority":90,"recency":73,"coverage":75,"diversity":73},"input_quality":75,"output_quality":68},{"name":"Synthesis","type":"synthesis","paqs":54.2,"attribution":0.405,"subs":{"info_preservation":25.0,"faithfulness":80.0,"coherence":25.0,"actionability":75.0},"input_quality":70,"output_quality":85},{"name":"Verification","type":"adversarial","paqs":50.0,"attribution":-0.135,"subs":{"critique_specificity":50.0,"weakness_coverage":50.0,"constructiveness":50.0},"input_quality":70,"output_quality":65}],"handoffs":[{"from":"Query Analyst","to":"Retrieval","his":65.4,"subs":{"Entity Preservation":80,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Retrieval","to":"Synthesis","his":73.4,"subs":{"Entity Preservation":100,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Synthesis","to":"Verification","his":50.2,"subs":{"Entity Preservation":88,"Context Compression":25.0,"Instruction Fidelity":25.0}}],"compliance_detail":{"pii_findings":[],"audit_checks":[{"name":"Input Traceability","passed":4,"total":4},{"name":"Model Version Pinning","passed":1,"total":4},{"name":"Prompt Hash Present","passed":0,"total":0},{"name":"Timestamp Integrity","passed":4,"total":4}],"rule_results":[{"rule":"GDPR \u2014 Data residency disclosure","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"Financial \u2014 Risk disclaimer required","triggered":true,"satisfied":false,"severity":"critical"},{"rule":"HR \u2014 Employee PII redaction","triggered":true,"satisfied":true,"severity":"critical"},{"rule":"General \u2014 Source attribution required","triggered":true,"satisfied":true,"severity":"warning"}]},"eval_meta":{"suite":"enterprise_rag_v1","duration_sec":0.0,"tasks":30,"llm_calls":30,"cost_usd":0.0,"timestamp":"2026-04-09T07:55:11.268236"}},"clean-05":{"pipeline":{"name":"Nexus Cloud RAG Pipeline","version":"1.2.0","run_id":"ddf59311-c704-41d3-8134-2831edd8dc93"},"system":{"overall":73.3,"product":75.8,"pipeline":68.2,"compliance":78.1,"compliance_capped":false},"layers":{"product":{"score":75.8,"weight":0.35,"dimensions":[{"code":"TCF","name":"Task Completion Fidelity","score":68.0,"description":"Did users achieve their goal end-to-end?","subs":[{"name":"Intent Capture","score":50.0},{"name":"Execution Correctness","score":80.0},{"name":"Goal Achievement","score":75.0}]},{"code":"DQS","name":"Decision Quality","score":81.8,"description":"Were recommendations relevant and actionable?","subs":[{"name":"Relevance","score":73},{"name":"Ranking Precision","score":100},{"name":"Actionability","score":75.0}]},{"code":"EOA","name":"Explanation Alignment","score":80.0,"description":"Does the stated reasoning match what the system did?","subs":[{"name":"Logical Consistency","score":80.0},{"name":"Completeness","score":80.0}]}]},"pipeline":{"score":68.2,"weight":0.4,"dimensions":[{"code":"PAQS","name":"Per-Agent Quality","score":59.5,"description":"Individual agent performance across role-specific rubrics","subs":[]},{"code":"CAS","name":"Chain Attribution","score":95,"description":"Quality impact per agent \u2014 which one broke the pipeline?","subs":[]},{"code":"HIS","name":"Handoff Integrity","score":47.0,"description":"Information preserved at agent-to-agent boundaries","subs":[]}]},"compliance":{"score":78.1,"weight":0.25,"dimensions":[{"code":"PES","name":"PII Exposure","score":62.2,"description":"Personal data detected across all pipeline stages and channels","subs":[{"name":"Detection Coverage","score":55},{"name":"Leakage Channels","score":73}]},{"code":"ATC","name":"Audit Trail Completeness","score":77.5,"description":"Every AI decision is reconstructable with full provenance","subs":[{"name":"Input Traceability","score":100},{"name":"Model Version Pinning","score":25},{"name":"Prompt Hash Present","score":100},{"name":"Timestamp Integrity","score":100}]},{"code":"RRC","name":"Regulatory Rules","score":100,"description":"Compliance with configured domain-specific regulatory checks","subs":[]}]}},"agents":[{"name":"Query Analyst","type":"analysis","paqs":50.0,"attribution":0.233,"subs":{"intent_capture":50.0,"reformulation_quality":50.0,"filter_accuracy":50.0},"input_quality":65,"output_quality":75},{"name":"Retrieval","type":"retrieval","paqs":84.6,"attribution":0.302,"subs":{"source_authority":90,"recency":100,"coverage":75,"diversity":73},"input_quality":75,"output_quality":88},{"name":"Synthesis","type":"synthesis","paqs":53.4,"attribution":0.349,"subs":{"info_preservation":25.0,"faithfulness":77.5,"coherence":25.0,"actionability":75.0},"input_quality":70,"output_quality":85},{"name":"Verification","type":"adversarial","paqs":50.0,"attribution":-0.116,"subs":{"critique_specificity":50.0,"weakness_coverage":50.0,"constructiveness":50.0},"input_quality":70,"output_quality":65}],"handoffs":[{"from":"Query Analyst","to":"Retrieval","his":65.4,"subs":{"Entity Preservation":80,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Retrieval","to":"Synthesis","his":73.4,"subs":{"Entity Preservation":100,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Synthesis","to":"Verification","his":47.0,"subs":{"Entity Preservation":80,"Context Compression":25.0,"Instruction Fidelity":25.0}}],"compliance_detail":{"pii_findings":[{"entity":"Procedure Nexus","type":"PERSON","location":"Retrieval \u2192 output","severity":"high"},{"entity":"Procedure Nexus","type":"PERSON","location":"Retrieval \u2192 Synthesis handoff","severity":"high"},{"entity":"Customer Data","type":"PERSON","location":"Synthesis \u2192 Verification handoff","severity":"high"}],"audit_checks":[{"name":"Input Traceability","passed":4,"total":4},{"name":"Model Version Pinning","passed":1,"total":4},{"name":"Prompt Hash Present","passed":0,"total":0},{"name":"Timestamp Integrity","passed":4,"total":4}],"rule_results":[{"rule":"GDPR \u2014 Data residency disclosure","triggered":true,"satisfied":true,"severity":"critical"},{"rule":"Financial \u2014 Risk disclaimer required","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"HR \u2014 Employee PII redaction","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"General \u2014 Source attribution required","triggered":true,"satisfied":true,"severity":"warning"}]},"eval_meta":{"suite":"enterprise_rag_v1","duration_sec":0.0,"tasks":30,"llm_calls":30,"cost_usd":0.0,"timestamp":"2026-04-09T07:55:11.285753"}},"fail-A1":{"pipeline":{"name":"Nexus Cloud RAG Pipeline","version":"1.2.0","run_id":"5d8dd64a-0df0-40de-8c4e-3d7ef337df4b"},"system":{"overall":72.3,"product":75.6,"pipeline":65.8,"compliance":78.1,"compliance_capped":false},"layers":{"product":{"score":75.6,"weight":0.35,"dimensions":[{"code":"TCF","name":"Task Completion Fidelity","score":59.2,"description":"Did users achieve their goal end-to-end?","subs":[{"name":"Intent Capture","score":25.0},{"name":"Execution Correctness","score":80.0},{"name":"Goal Achievement","score":75.0}]},{"code":"DQS","name":"Decision Quality","score":91.2,"description":"Were recommendations relevant and actionable?","subs":[{"name":"Relevance","score":100},{"name":"Ranking Precision","score":100},{"name":"Actionability","score":75.0}]},{"code":"EOA","name":"Explanation Alignment","score":80.0,"description":"Does the stated reasoning match what the system did?","subs":[{"name":"Logical Consistency","score":80.0},{"name":"Completeness","score":80.0}]}]},"pipeline":{"score":65.8,"weight":0.4,"dimensions":[{"code":"PAQS","name":"Per-Agent Quality","score":52.7,"description":"Individual agent performance across role-specific rubrics","subs":[]},{"code":"CAS","name":"Chain Attribution","score":95,"description":"Quality impact per agent \u2014 which one broke the pipeline?","subs":[]},{"code":"HIS","name":"Handoff Integrity","score":47.0,"description":"Information preserved at agent-to-agent boundaries","subs":[]}]},"compliance":{"score":78.1,"weight":0.25,"dimensions":[{"code":"PES","name":"PII Exposure","score":62.2,"description":"Personal data detected across all pipeline stages and channels","subs":[{"name":"Detection Coverage","score":55},{"name":"Leakage Channels","score":73}]},{"code":"ATC","name":"Audit Trail Completeness","score":77.5,"description":"Every AI decision is reconstructable with full provenance","subs":[{"name":"Input Traceability","score":100},{"name":"Model Version Pinning","score":25},{"name":"Prompt Hash Present","score":100},{"name":"Timestamp Integrity","score":100}]},{"code":"RRC","name":"Regulatory Rules","score":100,"description":"Compliance with configured domain-specific regulatory checks","subs":[]}]}},"agents":[{"name":"Query Analyst","type":"analysis","paqs":32.5,"attribution":0.0,"subs":{"intent_capture":25.0,"reformulation_quality":50.0,"filter_accuracy":25.0},"input_quality":65,"output_quality":65},{"name":"Retrieval","type":"retrieval","paqs":74.1,"attribution":0.512,"subs":{"source_authority":90,"recency":100,"coverage":40,"diversity":73},"input_quality":67,"output_quality":88},{"name":"Synthesis","type":"synthesis","paqs":54.2,"attribution":0.366,"subs":{"info_preservation":25.0,"faithfulness":80.0,"coherence":25.0,"actionability":75.0},"input_quality":70,"output_quality":85},{"name":"Verification","type":"adversarial","paqs":50.0,"attribution":-0.122,"subs":{"critique_specificity":50.0,"weakness_coverage":50.0,"constructiveness":50.0},"input_quality":70,"output_quality":65}],"handoffs":[{"from":"Query Analyst","to":"Retrieval","his":65.4,"subs":{"Entity Preservation":80,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Retrieval","to":"Synthesis","his":73.4,"subs":{"Entity Preservation":100,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Synthesis","to":"Verification","his":47.0,"subs":{"Entity Preservation":80,"Context Compression":25.0,"Instruction Fidelity":25.0}}],"compliance_detail":{"pii_findings":[{"entity":"Procedure Nexus","type":"PERSON","location":"Retrieval \u2192 output","severity":"high"},{"entity":"Procedure Nexus","type":"PERSON","location":"Retrieval \u2192 Synthesis handoff","severity":"high"},{"entity":"Customer Data","type":"PERSON","location":"Synthesis \u2192 Verification handoff","severity":"high"}],"audit_checks":[{"name":"Input Traceability","passed":4,"total":4},{"name":"Model Version Pinning","passed":1,"total":4},{"name":"Prompt Hash Present","passed":0,"total":0},{"name":"Timestamp Integrity","passed":4,"total":4}],"rule_results":[{"rule":"GDPR \u2014 Data residency disclosure","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"Financial \u2014 Risk disclaimer required","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"HR \u2014 Employee PII redaction","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"General \u2014 Source attribution required","triggered":true,"satisfied":true,"severity":"warning"}]},"eval_meta":{"suite":"enterprise_rag_v1","duration_sec":0.0,"tasks":30,"llm_calls":30,"cost_usd":0.0,"timestamp":"2026-04-09T07:55:11.304862"}},"fail-A2":{"pipeline":{"name":"Nexus Cloud RAG Pipeline","version":"1.2.0","run_id":"f7d51d0c-1b1c-453f-a310-0f3f90adb8f3"},"system":{"overall":50,"product":58.9,"pipeline":62.4,"compliance":39.5,"compliance_capped":true},"layers":{"product":{"score":58.9,"weight":0.35,"dimensions":[{"code":"TCF","name":"Task Completion Fidelity","score":50.0,"description":"Did users achieve their goal end-to-end?","subs":[{"name":"Intent Capture","score":25.0},{"name":"Execution Correctness","score":75.0},{"name":"Goal Achievement","score":50.0}]},{"code":"DQS","name":"Decision Quality","score":57.5,"description":"Were recommendations relevant and actionable?","subs":[{"name":"Relevance","score":50},{"name":"Ranking Precision","score":75},{"name":"Actionability","score":50.0}]},{"code":"EOA","name":"Explanation Alignment","score":75.0,"description":"Does the stated reasoning match what the system did?","subs":[{"name":"Logical Consistency","score":75.0},{"name":"Completeness","score":75.0}]}]},"pipeline":{"score":62.4,"weight":0.4,"dimensions":[{"code":"PAQS","name":"Per-Agent Quality","score":51.8,"description":"Individual agent performance across role-specific rubrics","subs":[]},{"code":"CAS","name":"Chain Attribution","score":88,"description":"Quality impact per agent \u2014 which one broke the pipeline?","subs":[]},{"code":"HIS","name":"Handoff Integrity","score":45.0,"description":"Information preserved at agent-to-agent boundaries","subs":[]}]},"compliance":{"score":39.5,"weight":0.25,"dimensions":[{"code":"PES","name":"PII Exposure","score":22.0,"description":"Personal data detected across all pipeline stages and channels","subs":[{"name":"Detection Coverage","score":0},{"name":"Leakage Channels","score":55}]},{"code":"ATC","name":"Audit Trail Completeness","score":77.5,"description":"Every AI decision is reconstructable with full provenance","subs":[{"name":"Input Traceability","score":100},{"name":"Model Version Pinning","score":25},{"name":"Prompt Hash Present","score":100},{"name":"Timestamp Integrity","score":100}]},{"code":"RRC","name":"Regulatory Rules","score":25,"description":"Compliance with configured domain-specific regulatory checks","subs":[]}]}},"agents":[{"name":"Query Analyst","type":"analysis","paqs":32.5,"attribution":0.333,"subs":{"intent_capture":25.0,"reformulation_quality":50.0,"filter_accuracy":25.0},"input_quality":65,"output_quality":75},{"name":"Retrieval","type":"retrieval","paqs":77.0,"attribution":-0.233,"subs":{"source_authority":70,"recency":100,"coverage":75,"diversity":60},"input_quality":75,"output_quality":68},{"name":"Synthesis","type":"synthesis","paqs":47.5,"attribution":0.267,"subs":{"info_preservation":25.0,"faithfulness":75.0,"coherence":25.0,"actionability":50.0},"input_quality":50,"output_quality":58},{"name":"Verification","type":"adversarial","paqs":50.0,"attribution":-0.167,"subs":{"critique_specificity":50.0,"weakness_coverage":50.0,"constructiveness":50.0},"input_quality":70,"output_quality":65}],"handoffs":[{"from":"Query Analyst","to":"Retrieval","his":65.4,"subs":{"Entity Preservation":80,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Retrieval","to":"Synthesis","his":73.4,"subs":{"Entity Preservation":100,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Synthesis","to":"Verification","his":45.0,"subs":{"Entity Preservation":75,"Context Compression":25.0,"Instruction Fidelity":25.0}}],"compliance_detail":{"pii_findings":[{"entity":"priya.sharma@nexuscloud.io","type":"EMAIL","location":"Retrieval \u2192 output","severity":"medium"},{"entity":"+91-98765-43210","type":"PHONE","location":"Retrieval \u2192 output","severity":"medium"},{"entity":"Priya Sharma","type":"PERSON","location":"Retrieval \u2192 output","severity":"high"},{"entity":"Priya Sharma","type":"PERSON","location":"Synthesis \u2192 output","severity":"high"},{"entity":"Priya Sharma","type":"PERSON","location":"Verification \u2192 input","severity":"high"},{"entity":"priya.sharma@nexuscloud.io","type":"EMAIL","location":"Retrieval \u2192 Synthesis handoff","severity":"medium"},{"entity":"+91-98765-43210","type":"PHONE","location":"Retrieval \u2192 Synthesis handoff","severity":"medium"},{"entity":"Priya Sharma","type":"PERSON","location":"Retrieval \u2192 Synthesis handoff","severity":"high"},{"entity":"priya.sharma@nexuscloud.io","type":"EMAIL","location":"Synthesis \u2192 Verification handoff","severity":"medium"},{"entity":"+91-98765-43210","type":"PHONE","location":"Synthesis \u2192 Verification handoff","severity":"medium"},{"entity":"Priya Sharma","type":"PERSON","location":"Synthesis \u2192 Verification handoff","severity":"high"}],"audit_checks":[{"name":"Input Traceability","passed":4,"total":4},{"name":"Model Version Pinning","passed":1,"total":4},{"name":"Prompt Hash Present","passed":0,"total":0},{"name":"Timestamp Integrity","passed":4,"total":4}],"rule_results":[{"rule":"GDPR \u2014 Data residency disclosure","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"Financial \u2014 Risk disclaimer required","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"HR \u2014 Employee PII redaction","triggered":true,"satisfied":false,"severity":"critical"},{"rule":"General \u2014 Source attribution required","triggered":true,"satisfied":true,"severity":"warning"}]},"eval_meta":{"suite":"enterprise_rag_v1","duration_sec":0.0,"tasks":30,"llm_calls":30,"cost_usd":0.0,"timestamp":"2026-04-09T07:55:11.324614"}},"fail-C1":{"pipeline":{"name":"Nexus Cloud RAG Pipeline","version":"1.2.0","run_id":"c2486eb0-20d6-4db4-95cb-b2565eeb20de"},"system":{"overall":68.8,"product":71.8,"pipeline":64.4,"compliance":71.7,"compliance_capped":false},"layers":{"product":{"score":71.8,"weight":0.35,"dimensions":[{"code":"TCF","name":"Task Completion Fidelity","score":66.2,"description":"Did users achieve their goal end-to-end?","subs":[{"name":"Intent Capture","score":50.0},{"name":"Execution Correctness","score":75.0},{"name":"Goal Achievement","score":75.0}]},{"code":"DQS","name":"Decision Quality","score":75.8,"description":"Were recommendations relevant and actionable?","subs":[{"name":"Relevance","score":56},{"name":"Ranking Precision","score":100},{"name":"Actionability","score":75.0}]},{"code":"EOA","name":"Explanation Alignment","score":75.0,"description":"Does the stated reasoning match what the system did?","subs":[{"name":"Logical Consistency","score":75.0},{"name":"Completeness","score":75.0}]}]},"pipeline":{"score":64.4,"weight":0.4,"dimensions":[{"code":"PAQS","name":"Per-Agent Quality","score":49.2,"description":"Individual agent performance across role-specific rubrics","subs":[]},{"code":"CAS","name":"Chain Attribution","score":83,"description":"Quality impact per agent \u2014 which one broke the pipeline?","subs":[]},{"code":"HIS","name":"Handoff Integrity","score":60.6,"description":"Information preserved at agent-to-agent boundaries","subs":[]}]},"compliance":{"score":71.7,"weight":0.25,"dimensions":[{"code":"PES","name":"PII Exposure","score":78.4,"description":"Personal data detected across all pipeline stages and channels","subs":[{"name":"Detection Coverage","score":70},{"name":"Leakage Channels","score":91}]},{"code":"ATC","name":"Audit Trail Completeness","score":77.5,"description":"Every AI decision is reconstructable with full provenance","subs":[{"name":"Input Traceability","score":100},{"name":"Model Version Pinning","score":25},{"name":"Prompt Hash Present","score":100},{"name":"Timestamp Integrity","score":100}]},{"code":"RRC","name":"Regulatory Rules","score":57,"description":"Compliance with configured domain-specific regulatory checks","subs":[]}]}},"agents":[{"name":"Query Analyst","type":"analysis","paqs":50.0,"attribution":0.222,"subs":{"intent_capture":50.0,"reformulation_quality":50.0,"filter_accuracy":50.0},"input_quality":65,"output_quality":75},{"name":"Retrieval","type":"retrieval","paqs":86.0,"attribution":0.067,"subs":{"source_authority":90,"recency":100,"coverage":75,"diversity":80},"input_quality":75,"output_quality":78},{"name":"Synthesis","type":"synthesis","paqs":36.0,"attribution":-0.378,"subs":{"info_preservation":25.0,"faithfulness":25.0,"coherence":25.0,"actionability":80.0},"input_quality":70,"output_quality":53},{"name":"Verification","type":"adversarial","paqs":25.0,"attribution":0.333,"subs":{"critique_specificity":25.0,"weakness_coverage":25.0,"constructiveness":25.0},"input_quality":70,"output_quality":85}],"handoffs":[{"from":"Query Analyst","to":"Retrieval","his":65.4,"subs":{"Entity Preservation":80,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Retrieval","to":"Synthesis","his":63.8,"subs":{"Entity Preservation":100,"Context Compression":50.0,"Instruction Fidelity":25.0}},{"from":"Synthesis","to":"Verification","his":60.6,"subs":{"Entity Preservation":92,"Context Compression":50.0,"Instruction Fidelity":25.0}}],"compliance_detail":{"pii_findings":[{"entity":"Data Processing","type":"PERSON","location":"Synthesis \u2192 input","severity":"high"},{"entity":"Agreement Summary","type":"PERSON","location":"Synthesis \u2192 input","severity":"high"}],"audit_checks":[{"name":"Input Traceability","passed":4,"total":4},{"name":"Model Version Pinning","passed":1,"total":4},{"name":"Prompt Hash Present","passed":0,"total":0},{"name":"Timestamp Integrity","passed":4,"total":4}],"rule_results":[{"rule":"GDPR \u2014 Data residency disclosure","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"Financial \u2014 Risk disclaimer required","triggered":true,"satisfied":false,"severity":"critical"},{"rule":"HR \u2014 Employee PII redaction","triggered":true,"satisfied":true,"severity":"critical"},{"rule":"General \u2014 Source attribution required","triggered":true,"satisfied":true,"severity":"warning"}]},"eval_meta":{"suite":"enterprise_rag_v1","duration_sec":0.0,"tasks":30,"llm_calls":30,"cost_usd":0.0,"timestamp":"2026-04-09T07:55:11.342139"}},"fail-D1":{"pipeline":{"name":"Nexus Cloud RAG Pipeline","version":"1.2.0","run_id":"1ac06c93-a0a7-4538-a5a3-1bbcc53d185e"},"system":{"overall":50,"product":79.1,"pipeline":68.8,"compliance":44.1,"compliance_capped":true},"layers":{"product":{"score":79.1,"weight":0.35,"dimensions":[{"code":"TCF","name":"Task Completion Fidelity","score":68.0,"description":"Did users achieve their goal end-to-end?","subs":[{"name":"Intent Capture","score":50.0},{"name":"Execution Correctness","score":80.0},{"name":"Goal Achievement","score":75.0}]},{"code":"DQS","name":"Decision Quality","score":91.2,"description":"Were recommendations relevant and actionable?","subs":[{"name":"Relevance","score":100},{"name":"Ranking Precision","score":100},{"name":"Actionability","score":75.0}]},{"code":"EOA","name":"Explanation Alignment","score":80.0,"description":"Does the stated reasoning match what the system did?","subs":[{"name":"Logical Consistency","score":80.0},{"name":"Completeness","score":80.0}]}]},"pipeline":{"score":68.8,"weight":0.4,"dimensions":[{"code":"PAQS","name":"Per-Agent Quality","score":58.2,"description":"Individual agent performance across role-specific rubrics","subs":[]},{"code":"CAS","name":"Chain Attribution","score":95,"description":"Quality impact per agent \u2014 which one broke the pipeline?","subs":[]},{"code":"HIS","name":"Handoff Integrity","score":50.6,"description":"Information preserved at agent-to-agent boundaries","subs":[]}]},"compliance":{"score":44.1,"weight":0.25,"dimensions":[{"code":"PES","name":"PII Exposure","score":33.4,"description":"Personal data detected across all pipeline stages and channels","subs":[{"name":"Detection Coverage","score":7},{"name":"Leakage Channels","score":73}]},{"code":"ATC","name":"Audit Trail Completeness","score":77.5,"description":"Every AI decision is reconstructable with full provenance","subs":[{"name":"Input Traceability","score":100},{"name":"Model Version Pinning","score":25},{"name":"Prompt Hash Present","score":100},{"name":"Timestamp Integrity","score":100}]},{"code":"RRC","name":"Regulatory Rules","score":25,"description":"Compliance with configured domain-specific regulatory checks","subs":[]}]}},"agents":[{"name":"Query Analyst","type":"analysis","paqs":50.0,"attribution":0.0,"subs":{"intent_capture":50.0,"reformulation_quality":50.0,"filter_accuracy":50.0},"input_quality":65,"output_quality":65},{"name":"Retrieval","type":"retrieval","paqs":79.6,"attribution":0.556,"subs":{"source_authority":70,"recency":100,"coverage":75,"diversity":73},"input_quality":63,"output_quality":88},{"name":"Synthesis","type":"synthesis","paqs":53.4,"attribution":0.333,"subs":{"info_preservation":25.0,"faithfulness":77.5,"coherence":25.0,"actionability":75.0},"input_quality":70,"output_quality":85},{"name":"Verification","type":"adversarial","paqs":50.0,"attribution":-0.111,"subs":{"critique_specificity":50.0,"weakness_coverage":50.0,"constructiveness":50.0},"input_quality":70,"output_quality":65}],"handoffs":[{"from":"Query Analyst","to":"Retrieval","his":65.4,"subs":{"Entity Preservation":80,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Retrieval","to":"Synthesis","his":73.4,"subs":{"Entity Preservation":100,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Synthesis","to":"Verification","his":50.6,"subs":{"Entity Preservation":89,"Context Compression":25.0,"Instruction Fidelity":25.0}}],"compliance_detail":{"pii_findings":[{"entity":"priya.sharma@nexuscloud.io","type":"EMAIL","location":"Retrieval \u2192 output","severity":"medium"},{"entity":"+91-98765-43210","type":"PHONE","location":"Retrieval \u2192 output","severity":"medium"},{"entity":"Priya Sharma","type":"PERSON","location":"Retrieval \u2192 output","severity":"high"},{"entity":"priya.sharma@nexuscloud.io","type":"EMAIL","location":"Retrieval \u2192 Synthesis handoff","severity":"medium"},{"entity":"+91-98765-43210","type":"PHONE","location":"Retrieval \u2192 Synthesis handoff","severity":"medium"},{"entity":"Priya Sharma","type":"PERSON","location":"Retrieval \u2192 Synthesis handoff","severity":"high"},{"entity":"priya.sharma@nexuscloud.io","type":"EMAIL","location":"Synthesis \u2192 Verification handoff","severity":"medium"},{"entity":"+91-98765-43210","type":"PHONE","location":"Synthesis \u2192 Verification handoff","severity":"medium"},{"entity":"Priya Sharma","type":"PERSON","location":"Synthesis \u2192 Verification handoff","severity":"high"}],"audit_checks":[{"name":"Input Traceability","passed":4,"total":4},{"name":"Model Version Pinning","passed":1,"total":4},{"name":"Prompt Hash Present","passed":0,"total":0},{"name":"Timestamp Integrity","passed":4,"total":4}],"rule_results":[{"rule":"GDPR \u2014 Data residency disclosure","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"Financial \u2014 Risk disclaimer required","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"HR \u2014 Employee PII redaction","triggered":true,"satisfied":false,"severity":"critical"},{"rule":"General \u2014 Source attribution required","triggered":true,"satisfied":true,"severity":"warning"}]},"eval_meta":{"suite":"enterprise_rag_v1","duration_sec":0.0,"tasks":30,"llm_calls":30,"cost_usd":0.0,"timestamp":"2026-04-09T07:55:11.359794"}},"fail-D2":{"pipeline":{"name":"Nexus Cloud RAG Pipeline","version":"1.2.0","run_id":"8d6f492f-1711-4a79-8efe-4f05f4511e61"},"system":{"overall":50,"product":72.4,"pipeline":65.0,"compliance":39.5,"compliance_capped":true},"layers":{"product":{"score":72.4,"weight":0.35,"dimensions":[{"code":"TCF","name":"Task Completion Fidelity","score":58.8,"description":"Did users achieve their goal end-to-end?","subs":[{"name":"Intent Capture","score":50.0},{"name":"Execution Correctness","score":75.0},{"name":"Goal Achievement","score":50.0}]},{"code":"DQS","name":"Decision Quality","score":82.5,"description":"Were recommendations relevant and actionable?","subs":[{"name":"Relevance","score":100},{"name":"Ranking Precision","score":100},{"name":"Actionability","score":50.0}]},{"code":"EOA","name":"Explanation Alignment","score":80.0,"description":"Does the stated reasoning match what the system did?","subs":[{"name":"Logical Consistency","score":80.0},{"name":"Completeness","score":80.0}]}]},"pipeline":{"score":65.0,"weight":0.4,"dimensions":[{"code":"PAQS","name":"Per-Agent Quality","score":57.5,"description":"Individual agent performance across role-specific rubrics","subs":[]},{"code":"CAS","name":"Chain Attribution","score":88,"description":"Quality impact per agent \u2014 which one broke the pipeline?","subs":[]},{"code":"HIS","name":"Handoff Integrity","score":47.0,"description":"Information preserved at agent-to-agent boundaries","subs":[]}]},"compliance":{"score":39.5,"weight":0.25,"dimensions":[{"code":"PES","name":"PII Exposure","score":22.0,"description":"Personal data detected across all pipeline stages and channels","subs":[{"name":"Detection Coverage","score":0},{"name":"Leakage Channels","score":55}]},{"code":"ATC","name":"Audit Trail Completeness","score":77.5,"description":"Every AI decision is reconstructable with full provenance","subs":[{"name":"Input Traceability","score":100},{"name":"Model Version Pinning","score":25},{"name":"Prompt Hash Present","score":100},{"name":"Timestamp Integrity","score":100}]},{"code":"RRC","name":"Regulatory Rules","score":25,"description":"Compliance with configured domain-specific regulatory checks","subs":[]}]}},"agents":[{"name":"Query Analyst","type":"analysis","paqs":50.0,"attribution":0.345,"subs":{"intent_capture":50.0,"reformulation_quality":50.0,"filter_accuracy":50.0},"input_quality":65,"output_quality":75},{"name":"Retrieval","type":"retrieval","paqs":81.0,"attribution":0.241,"subs":{"source_authority":70,"recency":100,"coverage":75,"diversity":80},"input_quality":71,"output_quality":78},{"name":"Synthesis","type":"synthesis","paqs":49.2,"attribution":-0.241,"subs":{"info_preservation":25.0,"faithfulness":80.0,"coherence":25.0,"actionability":50.0},"input_quality":70,"output_quality":63},{"name":"Verification","type":"adversarial","paqs":50.0,"attribution":-0.172,"subs":{"critique_specificity":50.0,"weakness_coverage":50.0,"constructiveness":50.0},"input_quality":70,"output_quality":65}],"handoffs":[{"from":"Query Analyst","to":"Retrieval","his":65.4,"subs":{"Entity Preservation":80,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Retrieval","to":"Synthesis","his":73.4,"subs":{"Entity Preservation":100,"Context Compression":77.5,"Instruction Fidelity":25.0}},{"from":"Synthesis","to":"Verification","his":47.0,"subs":{"Entity Preservation":80,"Context Compression":25.0,"Instruction Fidelity":25.0}}],"compliance_detail":{"pii_findings":[{"entity":"priya.sharma@nexuscloud.io","type":"EMAIL","location":"Retrieval \u2192 output","severity":"medium"},{"entity":"+91-98765-43210","type":"PHONE","location":"Retrieval \u2192 output","severity":"medium"},{"entity":"Priya Sharma","type":"PERSON","location":"Retrieval \u2192 output","severity":"high"},{"entity":"Priya Sharma","type":"PERSON","location":"Synthesis \u2192 output","severity":"high"},{"entity":"Priya Sharma","type":"PERSON","location":"Verification \u2192 input","severity":"high"},{"entity":"priya.sharma@nexuscloud.io","type":"EMAIL","location":"Retrieval \u2192 Synthesis handoff","severity":"medium"},{"entity":"+91-98765-43210","type":"PHONE","location":"Retrieval \u2192 Synthesis handoff","severity":"medium"},{"entity":"Priya Sharma","type":"PERSON","location":"Retrieval \u2192 Synthesis handoff","severity":"high"},{"entity":"priya.sharma@nexuscloud.io","type":"EMAIL","location":"Synthesis \u2192 Verification handoff","severity":"medium"},{"entity":"+91-98765-43210","type":"PHONE","location":"Synthesis \u2192 Verification handoff","severity":"medium"},{"entity":"Priya Sharma","type":"PERSON","location":"Synthesis \u2192 Verification handoff","severity":"high"}],"audit_checks":[{"name":"Input Traceability","passed":4,"total":4},{"name":"Model Version Pinning","passed":1,"total":4},{"name":"Prompt Hash Present","passed":0,"total":0},{"name":"Timestamp Integrity","passed":4,"total":4}],"rule_results":[{"rule":"GDPR \u2014 Data residency disclosure","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"Financial \u2014 Risk disclaimer required","triggered":false,"satisfied":true,"severity":"critical"},{"rule":"HR \u2014 Employee PII redaction","triggered":true,"satisfied":false,"severity":"critical"},{"rule":"General \u2014 Source attribution required","triggered":true,"satisfied":true,"severity":"warning"}]},"eval_meta":{"suite":"enterprise_rag_v1","duration_sec":0.0,"tasks":30,"llm_calls":30,"cost_usd":0.0,"timestamp":"2026-04-09T07:55:11.376519"}}}};

// ─── THEME ──────────────────────────────────────────────────────────────────
const T = {
  bg: "#080c14", surface: "#0f1620", surfaceAlt: "#151d2b", border: "#1c2638",
  text: "#d4dae6", textDim: "#6b7a94", textMuted: "#3d4d63",
  green: "#22c55e", greenBg: "rgba(34,197,94,0.08)", greenDim: "#166534",
  red: "#ef4444", redBg: "rgba(239,68,68,0.08)", redDim: "#7f1d1d",
  amber: "#eab308", amberBg: "rgba(234,179,8,0.08)",
  blue: "#3b82f6", blueBg: "rgba(59,130,246,0.08)", blueDim: "#1e3a6e",
  purple: "#a78bfa", cyan: "#22d3ee",
  accent: "#3b82f6",
};
const scoreColor = (v) => v >= 80 ? T.green : v >= 60 ? T.amber : T.red;
const scoreBg = (v) => v >= 80 ? T.greenBg : v >= 60 ? T.amberBg : T.redBg;
const fmt = (v) => v != null ? v.toFixed(1) : "—";

// ─── COMPONENTS ─────────────────────────────────────────────────────────────

function ScorePill({ value, size = "md" }) {
  const c = scoreColor(value);
  const fs = size === "sm" ? 10 : size === "lg" ? 16 : 12;
  const pad = size === "sm" ? "1px 6px" : size === "lg" ? "4px 14px" : "2px 8px";
  return <span style={{ background: `${c}18`, color: c, fontWeight: 700, fontSize: fs, padding: pad, borderRadius: 4, fontFamily: "'IBM Plex Mono', monospace" }}>{fmt(value)}</span>;
}

function LayerGauge({ label, score, weight }) {
  const pct = Math.min(100, Math.max(0, score));
  return (
    <div style={{ flex: 1, minWidth: 140 }}>
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
        <span style={{ fontSize: 11, color: T.textDim, fontWeight: 600, textTransform: "uppercase", letterSpacing: 0.8 }}>{label}</span>
        <span style={{ fontSize: 10, color: T.textMuted }}>{(weight*100).toFixed(0)}% weight</span>
      </div>
      <div style={{ position: "relative", height: 28, background: T.surface, borderRadius: 6, border: `1px solid ${T.border}`, overflow: "hidden" }}>
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: `${pct}%`, background: `linear-gradient(90deg, ${scoreColor(score)}22, ${scoreColor(score)}44)`, borderRadius: 6, transition: "width 0.5s" }} />
        <div style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <ScorePill value={score} />
        </div>
      </div>
    </div>
  );
}

function DimensionCard({ dim }) {
  const [open, setOpen] = useState(false);
  return (
    <div style={{ background: T.surfaceAlt, borderRadius: 8, border: `1px solid ${T.border}`, padding: "12px 16px", cursor: "pointer" }} onClick={() => setOpen(!open)}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <span style={{ fontSize: 10, color: T.blue, fontWeight: 700, letterSpacing: 0.8 }}>{dim.code}</span>
          <span style={{ fontSize: 12, color: T.text, marginLeft: 8, fontWeight: 500 }}>{dim.name}</span>
        </div>
        <ScorePill value={dim.score} />
      </div>
      {dim.description && <div style={{ fontSize: 11, color: T.textDim, marginTop: 4, fontStyle: "italic" }}>{dim.description}</div>}
      {open && dim.subs && dim.subs.length > 0 && (
        <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 4 }}>
          {dim.subs.map((s, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 8px", background: T.bg, borderRadius: 4 }}>
              <span style={{ fontSize: 11, color: T.textDim }}>{s.name}</span>
              <ScorePill value={s.score} size="sm" />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function WaterfallChart({ agents }) {
  if (!agents || agents.length === 0) return null;
  const chartData = agents.map(a => ({
    name: a.name, delta: (a.output_quality||50)-(a.input_quality||50), paqs: a.paqs,
    fill: ((a.output_quality||50)-(a.input_quality||50)) >= 0 ? T.green : T.red,
  }));
  return (
    <div style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8, padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: T.text, marginBottom: 4 }}>Chain Attribution Waterfall</div>
      <div style={{ fontSize: 11, color: T.textDim, marginBottom: 12 }}>Quality delta per agent: how much each improved or degraded output</div>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 0 }}>
          <XAxis dataKey="name" tick={{ fill: T.textDim, fontSize: 10 }} />
          <YAxis tick={{ fill: T.textDim, fontSize: 10 }} domain={[-30, 30]} tickFormatter={v => (v>0?"+":"")+v} />
          <Tooltip contentStyle={{ background: T.surfaceAlt, border: `1px solid ${T.border}`, borderRadius: 6, color: T.text, fontSize: 11 }}
            formatter={(v, n) => [n==="delta" ? (v>0?"+":"")+v.toFixed(1) : v.toFixed(1), n==="delta"?"Quality Delta":"PAQS"]} />
          <Bar dataKey="delta" radius={[4,4,0,0]}>{chartData.map((e,i) => <Cell key={i} fill={e.fill} />)}</Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

function CompliancePanel({ detail, score, capped }) {
  if (!detail) return null;
  return (
    <div style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8, padding: 16 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <div style={{ fontSize: 13, fontWeight: 600, color: T.text }}>Compliance Detail</div>
        {capped && <span style={{ fontSize: 10, fontWeight: 700, color: T.red, background: T.redBg, padding: "2px 8px", borderRadius: 4 }}>FLOOR ACTIVE — SCORE CAPPED</span>}
      </div>
      {detail.pii_findings && detail.pii_findings.length > 0 && (
        <div style={{ marginBottom: 12 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: T.red, marginBottom: 6 }}>PII Findings ({detail.pii_findings.length})</div>
          {detail.pii_findings.slice(0, 6).map((f, i) => (
            <div key={i} style={{ fontSize: 10, color: T.textDim, padding: "3px 8px", background: T.redBg, borderRadius: 4, marginBottom: 3 }}>
              <span style={{ color: T.red, fontWeight: 600 }}>{f.type}</span> — {f.entity?.slice(0,20)}{f.entity?.length>20?"...":""} — <span style={{ color: T.textMuted }}>{f.location}</span>
            </div>
          ))}
          {detail.pii_findings.length > 6 && <div style={{ fontSize: 10, color: T.textMuted }}>...and {detail.pii_findings.length - 6} more</div>}
        </div>
      )}
      {detail.rule_results && (
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: T.textDim, marginBottom: 6 }}>Regulatory Rules</div>
          {detail.rule_results.map((r, i) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 10, color: T.textDim, marginBottom: 3 }}>
              <span>{!r.triggered ? "○" : r.satisfied ? "✅" : "❌"}</span>
              <span style={{ color: !r.triggered ? T.textMuted : r.satisfied ? T.green : T.red }}>{r.rule}</span>
              {!r.triggered && <span style={{ color: T.textMuted, fontStyle: "italic" }}>not triggered</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function CompareView({ idA, idB }) {
  const a = ALL_RESULTS.data[idA];
  const b = ALL_RESULTS.data[idB];
  if (!a || !b) return <div style={{ color: T.textDim, padding: 20 }}>Select two runs to compare.</div>;
  const metrics = [
    { label: "Overall", ka: a.system.overall, kb: b.system.overall },
    { label: "Product", ka: a.system.product, kb: b.system.product },
    { label: "Pipeline", ka: a.system.pipeline, kb: b.system.pipeline },
    { label: "Compliance", ka: a.system.compliance, kb: b.system.compliance },
  ];
  // Add per-dimension comparison
  const dimsA = a.layers?.product?.dimensions || [];
  const dimsB = b.layers?.product?.dimensions || [];
  dimsA.forEach((d, i) => {
    if (dimsB[i]) metrics.push({ label: d.code + " " + d.name, ka: d.score, kb: dimsB[i].score });
  });

  return (
    <div style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8, padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: T.text, marginBottom: 12 }}>Run Comparison</div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 80px 80px 80px", gap: "6px 12px", fontSize: 11 }}>
        <div style={{ color: T.textMuted, fontWeight: 600 }}>Metric</div>
        <div style={{ color: T.textMuted, fontWeight: 600, textAlign: "center" }}>{idA}</div>
        <div style={{ color: T.textMuted, fontWeight: 600, textAlign: "center" }}>{idB}</div>
        <div style={{ color: T.textMuted, fontWeight: 600, textAlign: "center" }}>Delta</div>
        {metrics.map((m, i) => {
          const delta = m.kb - m.ka;
          return (
            <React.Fragment key={i}>
              <div style={{ color: T.text, paddingTop: 4, borderTop: i===0 ? "none" : `1px solid ${T.border}` }}>{m.label}</div>
              <div style={{ textAlign: "center", paddingTop: 4, borderTop: i===0 ? "none" : `1px solid ${T.border}` }}><ScorePill value={m.ka} size="sm" /></div>
              <div style={{ textAlign: "center", paddingTop: 4, borderTop: i===0 ? "none" : `1px solid ${T.border}` }}><ScorePill value={m.kb} size="sm" /></div>
              <div style={{ textAlign: "center", paddingTop: 4, color: delta > 0 ? T.green : delta < 0 ? T.red : T.textDim, fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", borderTop: i===0 ? "none" : `1px solid ${T.border}` }}>
                {delta > 0 ? "+" : ""}{delta.toFixed(1)}
              </div>
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}

function RadarView({ data }) {
  const radarData = [
    { dim: "Task Completion", score: data.layers?.product?.dimensions?.find(d=>d.code==="TCF")?.score || 0 },
    { dim: "Decision Quality", score: data.layers?.product?.dimensions?.find(d=>d.code==="DQS")?.score || 0 },
    { dim: "Explanation", score: data.layers?.product?.dimensions?.find(d=>d.code==="EOA")?.score || 0 },
    { dim: "Pipeline", score: data.system?.pipeline || 0 },
    { dim: "Compliance", score: data.system?.compliance || 0 },
  ];
  return (
    <div style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8, padding: 16 }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: T.text, marginBottom: 8 }}>Quality Radar</div>
      <ResponsiveContainer width="100%" height={200}>
        <RadarChart data={radarData}>
          <PolarGrid stroke={T.border} />
          <PolarAngleAxis dataKey="dim" tick={{ fill: T.textDim, fontSize: 9 }} />
          <PolarRadiusAxis domain={[0, 100]} tick={{ fill: T.textMuted, fontSize: 8 }} />
          <Radar dataKey="score" stroke={T.blue} fill={T.blue} fillOpacity={0.12} strokeWidth={2} />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── MAIN APP ───────────────────────────────────────────────────────────────

export default function PipelineJudgeDashboard() {
  const [selectedId, setSelectedId] = useState(ALL_RESULTS.index[0].query_id);
  const [view, setView] = useState("overview");
  const [compareId, setCompareId] = useState(ALL_RESULTS.index.length > 1 ? ALL_RESULTS.index[1].query_id : null);
  const data = ALL_RESULTS.data[selectedId];
  const idx = ALL_RESULTS.index;

  if (!data) return <div style={{ color: T.textDim, padding: 40 }}>No data loaded.</div>;

  const views = ["overview", "pipeline", "compliance", "compare"];

  return (
    <div style={{ background: T.bg, minHeight: "100vh", color: T.text, fontFamily: "'IBM Plex Sans', -apple-system, sans-serif" }}>
      {/* ─── HEADER ─── */}
      <div style={{ borderBottom: `1px solid ${T.border}`, padding: "10px 20px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 16, fontWeight: 700, letterSpacing: -0.5 }}><span style={{ color: T.blue }}>Pipeline</span><span style={{ color: T.text }}>Judge</span></span>
          <span style={{ fontSize: 9, color: T.textMuted, background: T.surfaceAlt, padding: "2px 6px", borderRadius: 3, fontWeight: 600 }}>v1.0</span>
        </div>
        <div style={{ display: "flex", gap: 3 }}>
          {views.map(v => (
            <button key={v} onClick={() => setView(v)} style={{
              background: view === v ? T.accent : "transparent", color: view === v ? "#fff" : T.textDim,
              border: "none", borderRadius: 5, padding: "5px 12px", fontSize: 11, fontWeight: 500, cursor: "pointer",
            }}>{v.charAt(0).toUpperCase() + v.slice(1)}</button>
          ))}
        </div>
        <select value={selectedId} onChange={e => setSelectedId(e.target.value)}
          style={{ background: T.surfaceAlt, color: T.text, border: `1px solid ${T.border}`, borderRadius: 5, padding: "5px 8px", fontSize: 11 }}>
          {idx.map(r => (
            <option key={r.query_id} value={r.query_id}>
              {r.query_id} — {r.overall.toFixed(1)}{r.compliance_capped ? " ⚠" : ""} — {r.query.slice(0, 40)}
            </option>
          ))}
        </select>
      </div>

      {/* ─── CONTENT ─── */}
      <div style={{ padding: 20, maxWidth: 1100, margin: "0 auto" }}>

        {/* OVERVIEW */}
        {view === "overview" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {/* System score */}
            <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "16px 20px", background: data.system.compliance_capped ? T.redBg : T.surface, border: `1px solid ${data.system.compliance_capped ? T.redDim : T.border}`, borderRadius: 8 }}>
              <div style={{ fontSize: 36, fontWeight: 800, color: scoreColor(data.system.overall), fontFamily: "'IBM Plex Mono', monospace" }}>{fmt(data.system.overall)}</div>
              <div>
                <div style={{ fontSize: 13, fontWeight: 600, color: T.text }}>System Score</div>
                <div style={{ fontSize: 11, color: T.textDim }}>{data.pipeline?.name} v{data.pipeline?.version}</div>
                {data.system.compliance_capped && <div style={{ fontSize: 10, fontWeight: 700, color: T.red, marginTop: 2 }}>COMPLIANCE FLOOR ACTIVE — score capped at 50</div>}
              </div>
            </div>
            {/* Layer gauges */}
            <div style={{ display: "flex", gap: 12 }}>
              <LayerGauge label="Product" score={data.system.product} weight={0.35} />
              <LayerGauge label="Pipeline" score={data.system.pipeline} weight={0.40} />
              <LayerGauge label="Compliance" score={data.system.compliance} weight={0.25} />
            </div>
            {/* Dimensions + Radar */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 280px", gap: 12 }}>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: T.textDim, textTransform: "uppercase", letterSpacing: 0.8, marginBottom: 2 }}>Product Dimensions</div>
                {(data.layers?.product?.dimensions || []).map((d,i) => <DimensionCard key={i} dim={d} />)}
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: T.textDim, textTransform: "uppercase", letterSpacing: 0.8, marginBottom: 2 }}>Pipeline Dimensions</div>
                {(data.layers?.pipeline?.dimensions || []).map((d,i) => <DimensionCard key={i} dim={d} />)}
                <div style={{ fontSize: 11, fontWeight: 600, color: T.textDim, textTransform: "uppercase", letterSpacing: 0.8, marginTop: 8, marginBottom: 2 }}>Compliance Dimensions</div>
                {(data.layers?.compliance?.dimensions || []).map((d,i) => <DimensionCard key={i} dim={d} />)}
              </div>
              <RadarView data={data} />
            </div>
          </div>
        )}

        {/* PIPELINE */}
        {view === "pipeline" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <WaterfallChart agents={data.agents} />
            {/* Agent cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 12 }}>
              {(data.agents || []).map((a, i) => (
                <div key={i} style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8, padding: 14 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <span style={{ fontSize: 12, fontWeight: 600, color: T.text }}>{a.name}</span>
                    <span style={{ fontSize: 9, color: T.textMuted, background: T.bg, padding: "2px 6px", borderRadius: 3 }}>{a.type}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: 10, color: T.textDim }}>PAQS</span>
                    <ScorePill value={a.paqs} size="sm" />
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                    <span style={{ fontSize: 10, color: T.textDim }}>Attribution</span>
                    <span style={{ fontSize: 11, fontWeight: 600, color: a.attribution >= 0 ? T.green : T.red, fontFamily: "'IBM Plex Mono', monospace" }}>{a.attribution > 0 ? "+" : ""}{a.attribution?.toFixed(3)}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                    <span style={{ fontSize: 10, color: T.textDim }}>Input Quality</span>
                    <span style={{ fontSize: 10, color: T.textDim, fontFamily: "'IBM Plex Mono', monospace" }}>{a.input_quality}</span>
                  </div>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                    <span style={{ fontSize: 10, color: T.textDim }}>Output Quality</span>
                    <span style={{ fontSize: 10, color: T.textDim, fontFamily: "'IBM Plex Mono', monospace" }}>{a.output_quality}</span>
                  </div>
                  {a.subs && Object.keys(a.subs).length > 0 && (
                    <div style={{ borderTop: `1px solid ${T.border}`, paddingTop: 6, marginTop: 4 }}>
                      {Object.entries(a.subs).map(([k, v]) => (
                        <div key={k} style={{ display: "flex", justifyContent: "space-between", fontSize: 10, color: T.textDim, marginBottom: 2 }}>
                          <span>{k.replace(/_/g, " ")}</span>
                          <ScorePill value={v} size="sm" />
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
            {/* Handoffs */}
            <div style={{ background: T.surface, border: `1px solid ${T.border}`, borderRadius: 8, padding: 16 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: T.text, marginBottom: 10 }}>Handoff Integrity</div>
              {(data.handoffs || []).map((h, i) => (
                <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8, padding: "6px 10px", background: T.bg, borderRadius: 6 }}>
                  <span style={{ fontSize: 11, color: T.text, minWidth: 200 }}>{h.from} → {h.to}</span>
                  <ScorePill value={h.his} size="sm" />
                  <div style={{ display: "flex", gap: 8, marginLeft: "auto" }}>
                    {h.subs && Object.entries(h.subs).map(([k, v]) => (
                      <span key={k} style={{ fontSize: 9, color: T.textDim }}>{k}: <ScorePill value={v} size="sm" /></span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* COMPLIANCE */}
        {view === "compliance" && <CompliancePanel detail={data.compliance_detail} score={data.system.compliance} capped={data.system.compliance_capped} />}

        {/* COMPARE */}
        {view === "compare" && (
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
              <span style={{ fontSize: 11, color: T.textDim }}>Run A:</span>
              <select value={selectedId} onChange={e => setSelectedId(e.target.value)}
                style={{ background: T.surfaceAlt, color: T.text, border: `1px solid ${T.border}`, borderRadius: 5, padding: "4px 8px", fontSize: 11 }}>
                {idx.map(r => <option key={r.query_id} value={r.query_id}>{r.query_id} ({r.overall.toFixed(1)})</option>)}
              </select>
              <span style={{ fontSize: 11, color: T.textDim }}>vs Run B:</span>
              <select value={compareId} onChange={e => setCompareId(e.target.value)}
                style={{ background: T.surfaceAlt, color: T.text, border: `1px solid ${T.border}`, borderRadius: 5, padding: "4px 8px", fontSize: 11 }}>
                {idx.map(r => <option key={r.query_id} value={r.query_id}>{r.query_id} ({r.overall.toFixed(1)})</option>)}
              </select>
            </div>
            <CompareView idA={selectedId} idB={compareId} />
          </div>
        )}
      </div>

      {/* ─── FOOTER ─── */}
      <div style={{ borderTop: `1px solid ${T.border}`, padding: "8px 20px", display: "flex", justifyContent: "space-between", fontSize: 10, color: T.textMuted }}>
        <span>PipelineJudge v1.0 — Product-centric evals for multi-agent pipelines</span>
        <span>{data.eval_meta?.suite} — {data.eval_meta?.tasks} judges — {data.eval_meta?.duration_sec}s</span>
      </div>
    </div>
  );
}
