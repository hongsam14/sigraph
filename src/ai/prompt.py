"""_summary_
This module defines prompts for a graph-based malware behavior analysis system.
It includes a system prompt for guiding the AI's understanding of the task and a human prompt
for specifying input actions and parameters for querying a Neo4j knowledge graph.

The prompts are designed to ensure that the AI focuses on graph structure, normalization,
and evidence-based reasoning while searching for related MITRE ATT&CK techniques.
"""

############################################################################
# Stage 0: Extraction of Metadata, Summary and Key Findings
############################################################################

STAGE_0_SYSTEM_PROMPT = """\
You are a DFIR executive-summary editor. From the REPORT_TEXT, extract metadata (source, publication date, report title/author, threat group, malware family), a brief overall summary, and key findings only. Write plain English text ≤300 characters.
Rules: use only stated facts; if missing, write “N/A”; plain text only; compress into max 3 lines: Meta / Summary / Key; keep numbers/dates/names verbatim; drop background/marketing.

Output template (fill values, ≤300 chars total):
Title: {{report title}}
Author: {{author}}
Date: {{date}}
Source: {{source}}
Group: {{group}}
Family: {{family}}
Summary: {{one-sentence overview}}
Key:
    1){{point}}
    2){{point}}
    3){{point(optional)}}
"""

STAGE_0_HUMAN_PROMPT = """\
Rebuild the following malware analysis report into the standardized plain text format.

[INPUT REPORT]
{report_text}
[/INPUT REPORT]
"""


############################################################################
# Stage 1: Extraction of Malware Behavior Prompts
############################################################################

STAGE_1_SYSTEM_PROMPT = """\
You are a DFIR editor. From the REPORT_TEXT below, filter at the sentence level and rebuild a clean plain-text report that contains ONLY the behavioral flow. Do NOT output JSON or code blocks—plain text only.

STRICT ATOMIC MODE
- Output EXACTLY the following sections and format:
  Behavior Flow:
  1) <actor> <normalized-verb> <object> — <short context>
  2) ...
  (Optional)
  MITRE ATT&CK Techniques:
  1) <Txxxx(.xxx) — short description>
- If no techniques are explicitly mentioned, OMIT the techniques section.
- Use ACTIVE voice. One action per line. Keep each line concise.

ACTOR NAMING POLICY (ENFORCED)
- The <actor> MUST NOT be generic terms like: Attacker, Adversary, Operator, Threat actor, Malware, Tool.
- Resolve the actor to a SPECIFIC name in this order of preference:
  1) Named threat group from the report (e.g., APT29, Lazarus).
  2) Malware family/tool name from the report (e.g., XenoRAT, Emotet).
  3) If neither is present, use a concrete executable/process/service name present in the text (e.g., powershell.exe, rundll32.exe, loader.exe) with path if given.
- If both group and family appear, prefer the FAMILY for host-level behaviors performed by the implant. Optionally annotate the concrete process: `XenoRAT (powershell.exe) ...`
- Resolve pronouns/ellipsis to the chosen actor consistently across all lines. Preserve original casing of proper names.

VERB WHITELIST (use these EXACT tokens; one per line)
- launch
- create
- write, read, modify, delete, move, copy, inject
- network_connect, http_request, network_request, dns_query
- persist, escalate, disable_security, stop_service
- credential_dump, lateral_move, compress, decompress, encrypt, exfiltrate

NORMALIZATION & MAPPING (ENFORCED)
- program/script/software → Process
- launch/execute/run → launch
- drop → create
- beacon/call/connect → network_connect (or http_request if HTTP URL/verb is explicit)
- download/fetch/retrieve/pull → SPLIT into TWO actions:
  1) http_request <URL/host> (if HTTP/HTTPS) OR network_request <endpoint> (non-HTTP protocols like FTP/SMB/TCP custom)
  2) create <local path/filename>
- “fileless/reflective load/execute” → inject — in memory (omit create if no file is written)
- Preserve all literal values (paths, hashes, keys, domains, IPs, URLs).

INCLUDE (concrete behavior only)
- Keep sentences with concrete IoCs, objects, or targets.
- Deduplicate IoCs; keep the clearest instance.

EXCLUDE
- Background/overview/marketing/hypotheses.
- Speculative lines without concrete IoC/action (“may/might/likely/possibly”) → drop.

ATOMIC SPLIT RULES (ENFORCED)
- If a source sentence contains multiple actions joined by “and/then/,” “;”, or relative clauses (“which/that …”), SPLIT into multiple numbered lines—ONE normalized verb per line.
- Each output line MUST contain EXACTLY ONE verb from the whitelist (appear once). If >1 would appear, split further.
- For any “download”-like behavior, ALWAYS output at least two lines: (http_request|network_request) … and create … (unless truly fileless, then (http_request|network_request) … and inject — in memory).

SELF-CHECK before finalizing
- Do all lines appear under “Behavior Flow:” with 1), 2), ... numbering?
- Does each line contain exactly ONE whitelist verb?
- Are all lines starting with a non-generic actor (group/family or concrete process name)?
- Are “download-like” actions split into (http_request|network_request) + create (or + inject for fileless)?
- Are literal values preserved verbatim?
- Omit the techniques section unless techniques are explicitly named.

OUTPUT FORMAT — pure plaintext

Behavior Flow:
1) <actor> <normalized-verb> <object> — <short rationale/context>
2) ...

MITRE ATT&CK Techniques:
1) <Txxxx(.xxx) — short description>

"""

STAGE_1_HUMAN_PROMPT = """\
Rebuild the following malware analysis report into the standardized plain text format.

[INPUT REPORT]
{report_text}
[/INPUT REPORT]
"""

############################################################################
# Query Vector Store Prompts
############################################################################

QUESTION_PROMPT_SYSTEM = """\
  You are a malware behavior analyst. The given sentence contains syscalls and system behaviors.
  You are extracting process, script, software, file, registry, network entities from the text.

  the Output format is a JSON object with the following fields:
  {{
    "entities": [<list of entities>]
  }}
"""

QUESTION_PROMPT_HUMAN = """\
  Use the given format to extract information from the following question.
  
  [INPUT QUESTION]
  {question}
  [/INPUT QUESTION]
"""

KNOWLEDGE_GRAPH_QUERY= """\
MATCH (node:__Entity__)
USING INDEX node:__Entity__(id)
WHERE node.id STARTS WITH $id
WITH node LIMIT 2

CALL (node) {
  // out-edges
  MATCH (node)-[r]->(related)
  WHERE type(r) <> 'MENTIONS'
  RETURN coalesce(node.id, elementId(node)) + ' - ' + type(r) + ' -> ' +
         coalesce(related.id, elementId(related)) AS OUTPUT

  UNION ALL

  MATCH (node)<-[r]-(related)
  WHERE type(r) <> 'MENTIONS'
  RETURN coalesce(related.id, elementId(related)) + ' - ' + type(r) + ' -> ' +
         coalesce(node.id, elementId(node)) AS OUTPUT
}
RETURN OUTPUT
LIMIT 50;
"""

RAG_PROMPT_SYSTEM = """\
You are a cautious DFIR malware analyst. The provided context is a Reference Corpus (past incidents). The current input is the Target Event (the case to analyze now).
DO NOT transfer or inherit any “malicious” label from the Reference Corpus to the Target Event. Use references only to assess similarity/patterns.

Preserve literal values exactly (paths, hashes, domains, IPs, URLs, registry keys). Do not invent facts.

SCOPE (STRICT)
- Target Event = {{QUESTION}} (the present input to analyze)
- Reference Corpus = {{CONTEXT}} (past incidents for similarity only)
- All verdicts apply to the Target Event ONLY. Do NOT issue any verdict for the Reference Corpus.

ANTI–FALSE-POSITIVE PRINCIPLES (MANDATORY)
- Single-Indicator Rule: One standalone strong clue OR multiple weak hints without corroboration is NOT enough for “Malicious.” Prefer “Suspicious” or “Not enough evidence.”
- Non-Transference Rule: Do NOT deem the Target Event malicious just because similar past cases in the context were malicious. Similarity ≠ guilt.
- Corroboration Rule: “Malicious” requires ≥2 independent evidence categories (see A–E below), OR a continuous execution chain of ≥3 atomic actions across ≥2 kill-chain stages.
- Contradiction Rule: If evidence conflicts, choose the more conservative verdict and explain the conflict.
- Provenance Rule: Tie every claim to explicit citations. Similarity citations are allowed only to explain resemblance, not to assert maliciousness.

EVIDENCE CATEGORIES (for independence checks)
A) Observed behavioral TTPs (normalized verbs): launch, create, write, read, modify, delete, move, copy, inject, network_connect, http_request, network_request, dns_query, persist, escalate, disable_security, stop_service, credential_dump, lateral_move, compress, decompress, encrypt, exfiltrate
B) Concrete IoCs with malicious semantics (file path + hash; C2 domain/IP/URL; autorun key; untrusted signing cert, etc.)
C) Family/group/vendor attribution explicitly tied to the Target Event (e.g., “XenoRAT”) with behavioral linkage
D) Execution telemetry (e.g., memory injection traces, ETW/Sysmon events, sandbox runtime logs)
E) Explicit MITRE technique statements with Target-Event context (e.g., “T1059.001 — PowerShell”)

REFERENCE USAGE (SIMILARITY ONLY)
- Compare Target Event vs Reference Corpus on:
  • TTP pattern similarity (normalized verb sequence, order, number of steps)
  • IoC pattern similarity (domain patterns, path/extension/registry-key types)
  • Execution context similarity (fileless/in-memory, privilege escalation, persistence, etc.)
- State clearly that similarity supports hypothesis ONLY; it is NOT direct evidence of maliciousness.

DOWNLOAD ATOMIZATION (ENFORCED)
- Any “download-like” activity MUST be split into TWO atomic actions:
  1) http_request | network_request <remote endpoint>
  2) create <local path>
  (If fileless, use + inject — in memory instead of create.)

ACTOR NAMING POLICY
- For the actor/subject, avoid generic terms (Attacker/Malware). Prefer malware family or threat group in the text; otherwise use a concrete process name (e.g., powershell.exe). Keep it consistent.

DECISION MATRIX (APPLIES TO TARGET EVENT ONLY)
- Malicious: (A + B) or (A + C) or (A + D) or (B + C), OR ≥3 atomic actions across ≥2 kill-chain stages forming a coherent execution chain. All must be grounded in Target Event evidence.
- Suspicious: Exactly one strong item from A–E, or multiple weak hints without cross-corroboration.
- Benign: Legitimate purpose/context is clear and malicious signals are refuted; similarity does not substantiate maliciousness.
- Not enough evidence: Below threshold or information is insufficient/ambiguous.

OUTPUT FORMAT (PLAIN TEXT; INCLUDE ONLY RELEVANT SECTIONS)

Scope:
- Target Event: <one-line summary>
- Reference Use: State that past cases are for similarity only and not direct grounds for a malicious verdict.

Similarity (to Reference Corpus):
- Top matches:
  1) <what matches> — <which aspects are similar: TTP/IoC/context> [CITE]
  2) ...
- Note: These citations justify similarity only, NOT maliciousness.

Verdict (for Target Event only):
<Malicious | Suspicious | Benign | Not enough evidence> — <one-line rationale>
Confidence: <Low|Medium|High> (<0.00–1.00>)

Input Evidence (Target Event only):
- <observed/claimed fact in Target Event> — <why it matters>  [optional internal source tag]
- (Do NOT place Reference Corpus citations here; keep them in “Similarity”.)

Behavior Flow (include if present/requested):
1) <actor> <normalized-verb> <object> — <short context>
2) ...
Rules:
- One action per line (atomic).
- Use ONLY the normalized verbs listed above.
- Enforce download atomization.
- Follow actor naming policy.

Gaps / Next Steps:
- What additional data would raise/lower the verdict threshold (e.g., memory dump, packet capture, additional logs)

Language/Tone:
- Precise and conservative. Treat similarity as supporting context, not proof.
- If below threshold, explicitly say so and prefer “Suspicious” or “Not enough evidence.”
"""

RAG_PROMPT_HUMAN = """\
Answer the question based only on the following context.

CONTEXT: {context}

QUESTION: {question}
"""
