"""Eval suite configuration — hardcoded for MVP, mirrors YAML design artifact.

Defines all dimensions, subdimensions, weights, judge types, and prompt templates
for the three evaluation layers: product, pipeline, compliance.
"""

EVAL_SUITE = {
    "name": "enterprise_rag_v1",
    "version": "1.0",

    "layers": {
        "product": {
            "weight": 0.35,
            "dimensions": {
                "TCF": {
                    "name": "Task Completion Fidelity",
                    "description": "Did users achieve their goal end-to-end?",
                    "weight": 0.40,
                    "subdimensions": {
                        "intent_capture": {
                            "judge_type": "llm",
                            "prompt": (
                                "You are evaluating whether an AI system correctly understood the user's intent.\n\n"
                                "User query: {query}\n"
                                "System's parsed intent/reformulation: {agent_output}\n\n"
                                "Score on this rubric:\n"
                                "1 - Completely misunderstood the query\n"
                                "2 - Captured the general topic but missed key specifics\n"
                                "3 - Captured the main intent but missed secondary interpretations\n"
                                "4 - Correctly captured the primary intent with relevant details\n"
                                "5 - Perfectly captured all aspects including ambiguity and edge cases\n\n"
                                "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                            ),
                            "weight": 0.35,
                        },
                        "execution_correctness": {
                            "judge_type": "llm",
                            "prompt": (
                                "You are evaluating whether an AI pipeline executed the correct operations.\n\n"
                                "User query: {query}\n"
                                "Retrieved documents: {retrieval_output}\n"
                                "Generated answer: {synthesis_output}\n\n"
                                "Score on this rubric:\n"
                                "1 - Retrieved completely wrong documents, answer is irrelevant\n"
                                "2 - Some relevant documents but major gaps, answer partially addresses query\n"
                                "3 - Mostly relevant retrieval, answer addresses the query but with notable omissions\n"
                                "4 - Good retrieval and answer, minor gaps only\n"
                                "5 - Excellent retrieval, answer fully and accurately addresses the query\n\n"
                                "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                            ),
                            "weight": 0.35,
                        },
                        "goal_achievement": {
                            "judge_type": "llm",
                            "prompt": (
                                "You are evaluating whether a user could accomplish their goal based on this AI response.\n\n"
                                "User query: {query}\n"
                                "Final answer provided: {final_answer}\n\n"
                                "Score on this rubric:\n"
                                "1 - User would be completely unable to act on this answer\n"
                                "2 - User gets some information but cannot make a decision or take action\n"
                                "3 - User gets a partial answer, would need to ask follow-up questions\n"
                                "4 - User gets a good answer and can likely act on it with minor gaps\n"
                                "5 - User can immediately act on this answer with full confidence\n\n"
                                "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                            ),
                            "weight": 0.30,
                        },
                    },
                },
                "DQS": {
                    "name": "Decision Quality",
                    "description": "Were recommendations relevant and actionable?",
                    "weight": 0.35,
                    "subdimensions": {
                        "relevance": {
                            "judge_type": "programmatic",
                            "function": "retrieval_relevance",
                            "weight": 0.35,
                        },
                        "ranking_precision": {
                            "judge_type": "programmatic",
                            "function": "ranking_precision",
                            "weight": 0.30,
                        },
                        "actionability": {
                            "judge_type": "llm",
                            "prompt": (
                                "You are evaluating the actionability of an AI-generated answer.\n\n"
                                "User query: {query}\n"
                                "Answer: {final_answer}\n\n"
                                "Actionability means: can the user DO something with this answer without "
                                "needing additional research or clarification?\n\n"
                                "Score on this rubric:\n"
                                "1 - Answer is vague, generic, or just summarizes docs without guidance\n"
                                "2 - Answer provides some information but user needs significant follow-up\n"
                                "3 - Answer gives a direction but lacks specific steps or details\n"
                                "4 - Answer provides clear, specific guidance the user can act on\n"
                                "5 - Answer gives precise, step-by-step actionable guidance with all needed details\n\n"
                                "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                            ),
                            "weight": 0.35,
                        },
                    },
                },
                "EOA": {
                    "name": "Explanation Alignment",
                    "description": "Does the stated reasoning match what the system did?",
                    "weight": 0.25,
                    "subdimensions": {
                        "logical_consistency": {
                            "judge_type": "llm",
                            "prompt": (
                                "You are evaluating whether an AI's answer is logically consistent with its source documents.\n\n"
                                "Source documents retrieved:\n{retrieval_output}\n\n"
                                "Answer generated:\n{synthesis_output}\n\n"
                                "Check: does every claim in the answer logically follow from the source documents?\n"
                                "Flag any claims that go beyond what the sources state.\n\n"
                                "Score on this rubric:\n"
                                "1 - Multiple claims directly contradict or are absent from sources\n"
                                "2 - Some claims are unsupported, answer extrapolates significantly\n"
                                "3 - Most claims are supported, one or two minor extrapolations\n"
                                "4 - Nearly all claims are directly supported by sources\n"
                                "5 - Every claim is directly traceable to the source documents\n\n"
                                "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\", "
                                "\"unsupported_claims\": [\"...\"]}}"
                            ),
                            "weight": 0.55,
                        },
                        "completeness": {
                            "judge_type": "llm",
                            "prompt": (
                                "You are evaluating whether an AI's cited sources actually cover the claims made.\n\n"
                                "Citations listed: {citations}\n"
                                "Answer: {synthesis_output}\n"
                                "Source documents available:\n{retrieval_output}\n\n"
                                "Does the answer cite all the sources it actually drew from? "
                                "Are there claims that should cite a source but don't?\n\n"
                                "Score on this rubric:\n"
                                "1 - Citations are missing or wrong for most claims\n"
                                "2 - Some citations present but major gaps\n"
                                "3 - Most claims are cited, some gaps\n"
                                "4 - Nearly complete citation coverage\n"
                                "5 - Every claim is properly attributed to the correct source\n\n"
                                "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                            ),
                            "weight": 0.45,
                        },
                    },
                },
            },
        },

        "pipeline": {
            "weight": 0.40,
            "dimensions": {
                "PAQS": {
                    "name": "Per-Agent Quality",
                    "description": "Individual agent performance across role-specific rubrics",
                    "weight": 0.35,
                    "agent_rubrics": {
                        "analysis": {
                            "subdimensions": {
                                "intent_capture": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate this query analyst's output quality.\n\n"
                                        "Input query: {agent_input}\n"
                                        "Analyst output: {agent_output}\n\n"
                                        "Did it correctly identify intent, produce useful search terms, and flag ambiguity?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.4,
                                },
                                "reformulation_quality": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate the quality of the query reformulation.\n\n"
                                        "Original query: {agent_input}\n"
                                        "Reformulated output: {agent_output}\n\n"
                                        "Are the search terms specific enough? Is the category filter appropriate?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.3,
                                },
                                "filter_accuracy": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate whether the category filter is correct.\n\n"
                                        "Query: {agent_input}\n"
                                        "Category assigned: {agent_output}\n\n"
                                        "Is this the right category? Did it miss relevant categories for ambiguous queries?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.3,
                                },
                            },
                        },
                        "retrieval": {
                            "subdimensions": {
                                "source_authority": {
                                    "judge_type": "programmatic",
                                    "function": "source_authority",
                                    "weight": 0.25,
                                },
                                "recency": {
                                    "judge_type": "programmatic",
                                    "function": "source_recency",
                                    "weight": 0.25,
                                },
                                "coverage": {
                                    "judge_type": "programmatic",
                                    "function": "retrieval_coverage",
                                    "weight": 0.30,
                                },
                                "diversity": {
                                    "judge_type": "programmatic",
                                    "function": "retrieval_diversity",
                                    "weight": 0.20,
                                },
                            },
                        },
                        "synthesis": {
                            "subdimensions": {
                                "info_preservation": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate how well this synthesis preserves key information from sources.\n\n"
                                        "Source chunks: {agent_input}\n"
                                        "Synthesized answer: {agent_output}\n\n"
                                        "Did critical facts survive? Was important nuance lost?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.30,
                                },
                                "faithfulness": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate faithfulness of this answer to its source documents.\n\n"
                                        "Sources: {agent_input}\n"
                                        "Answer: {agent_output}\n\n"
                                        "Does EVERY claim in the answer trace back to the sources? Flag any hallucinations.\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\", "
                                        "\"hallucinations\": [\"...\"]}}"
                                    ),
                                    "weight": 0.35,
                                },
                                "coherence": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate the coherence of this synthesized answer.\n\n"
                                        "Answer: {agent_output}\n\n"
                                        "Does it read as a unified, well-structured response? Or a patchwork of fragments?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.15,
                                },
                                "actionability": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate the actionability of this answer.\n\n"
                                        "Query: {query}\n"
                                        "Answer: {agent_output}\n\n"
                                        "Can the user act on this without further research?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.20,
                                },
                            },
                        },
                        "adversarial": {
                            "subdimensions": {
                                "critique_specificity": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate how specific this verification agent's critique is.\n\n"
                                        "Verification output: {agent_output}\n\n"
                                        "Did it identify specific unsupported claims, or just give a vague thumbs up/down?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.35,
                                },
                                "weakness_coverage": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate whether this verifier caught the actual issues.\n\n"
                                        "Answer being verified: {agent_input}\n"
                                        "Verifier output: {agent_output}\n"
                                        "Source documents: {context}\n\n"
                                        "Were there unsupported claims the verifier missed?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.40,
                                },
                                "constructiveness": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate the constructiveness of this verification.\n\n"
                                        "Verifier output: {agent_output}\n\n"
                                        "Did it suggest what to fix, or just flag problems?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.25,
                                },
                            },
                        },
                        # Generic rubric for any agent type not listed above
                        # (transform, routing, custom, or any unknown type)
                        "custom": {
                            "subdimensions": {
                                "output_quality": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate the overall quality of this agent's output.\n\n"
                                        "Agent input: {agent_input}\n"
                                        "Agent output: {agent_output}\n\n"
                                        "Is the output well-structured, relevant to the input, and useful for the next step?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.50,
                                },
                                "value_added": {
                                    "judge_type": "llm",
                                    "prompt": (
                                        "Evaluate what value this agent added to the pipeline.\n\n"
                                        "What it received: {agent_input}\n"
                                        "What it produced: {agent_output}\n\n"
                                        "Did this agent meaningfully transform, enrich, or improve the data?\n"
                                        "Score 1-5.\n\n"
                                        "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                                    ),
                                    "weight": 0.50,
                                },
                            },
                        },
                    },
                },
                "CAS": {
                    "name": "Chain Attribution",
                    "description": "Quality impact per agent — which one broke the pipeline?",
                    "weight": 0.35,
                    # Computed by chain_attribution engine, not individual judges
                },
                "HIS": {
                    "name": "Handoff Integrity",
                    "description": "Information preserved at agent-to-agent boundaries",
                    "weight": 0.30,
                    "subdimensions": {
                        "entity_preservation": {
                            "judge_type": "programmatic",
                            "function": "entity_preservation",
                            "weight": 0.40,
                        },
                        "context_compression": {
                            "judge_type": "llm",
                            "prompt": (
                                "Evaluate whether critical information survived this handoff between agents.\n\n"
                                "Source agent output: {source_output}\n"
                                "Handoff payload: {handoff_payload}\n"
                                "Target agent input: {target_input}\n\n"
                                "Was key information preserved or lost in the handoff?\n"
                                "Score 1-5.\n\n"
                                "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                            ),
                            "weight": 0.35,
                        },
                        "instruction_fidelity": {
                            "judge_type": "llm",
                            "prompt": (
                                "Evaluate whether the receiving agent followed the intent of the sending agent.\n\n"
                                "Source agent output (intent/instructions): {source_output}\n"
                                "Target agent output (what it did): {target_output}\n\n"
                                "Did the target agent act on the instructions/context it received?\n"
                                "Score 1-5.\n\n"
                                "Respond ONLY with JSON: {{\"score\": <1-5>, \"reasoning\": \"<explanation>\"}}"
                            ),
                            "weight": 0.25,
                        },
                    },
                },
            },
        },

        "compliance": {
            "weight": 0.25,
            "floor_threshold": 70,
            "floor_cap": 50,
            "dimensions": {
                "PES": {
                    "name": "PII Exposure",
                    "description": "Personal data detected across all pipeline stages and channels",
                    "weight": 0.40,
                    "subdimensions": {
                        "detection_coverage": {
                            "judge_type": "programmatic",
                            "function": "pii_scan",
                            "weight": 0.60,
                        },
                        "leakage_channels": {
                            "judge_type": "programmatic",
                            "function": "pii_channel_scan",
                            "weight": 0.40,
                        },
                    },
                },
                "ATC": {
                    "name": "Audit Trail Completeness",
                    "description": "Every AI decision is reconstructable with full provenance",
                    "weight": 0.30,
                    "subdimensions": {
                        "input_traceability": {
                            "judge_type": "programmatic",
                            "function": "input_traceability",
                            "weight": 0.30,
                        },
                        "model_version_pinning": {
                            "judge_type": "programmatic",
                            "function": "model_version_check",
                            "weight": 0.30,
                        },
                        "prompt_hash_present": {
                            "judge_type": "programmatic",
                            "function": "prompt_hash_check",
                            "weight": 0.20,
                        },
                        "timestamp_integrity": {
                            "judge_type": "programmatic",
                            "function": "timestamp_check",
                            "weight": 0.20,
                        },
                    },
                },
                "RRC": {
                    "name": "Regulatory Rules",
                    "description": "Compliance with configured domain-specific regulatory checks",
                    "weight": 0.30,
                    "rules": [
                        {
                            "name": "GDPR — Data residency disclosure",
                            "trigger": ["data residen", "where is data stored", "geographic", "eu customer", "gdpr"],
                            "required_content": ["region", "US", "EU"],
                            "severity": "critical",
                        },
                        {
                            "name": "Financial — Risk disclaimer required",
                            "trigger": ["pricing", "cost", "refund", "credit", "financial", "penalt"],
                            "required_content": ["terms", "conditions", "policy"],
                            "severity": "critical",
                        },
                        {
                            "name": "HR — Employee PII redaction",
                            "trigger": ["employee", "hr", "leave", "personnel", "staff"],
                            "check_type": "pii_absent",  # special: checks that PII is NOT in the answer
                            "severity": "critical",
                        },
                        {
                            "name": "General — Source attribution required",
                            "trigger": [],  # always triggered
                            "required_content": ["citation", "source", "according to"],
                            "check_type": "has_citations",
                            "severity": "warning",
                        },
                    ],
                },
            },
        },
    },
}
