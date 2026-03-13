# **Architecting the Workflow, Agent, Tool (WAT) Paradigm: Transitioning Multi-Agent Executive Orchestration from Claude Code to Gemini CLI**

The paradigm of autonomous software development has undergone a structural revolution, shifting irrevocably from single-threaded, monolithic large language model (LLM) interactions to complex, topologically diverse multi-agent orchestrations. At the vanguard of this evolution is the Workflow, Agent, and Tool (WAT) architecture. In a fully realized WAT environment, a centralized executive orchestrator acts as an autonomous project manager. This executive evaluates the entire codebase, decomposes high-level user directives into discrete technical tasks, establishes dependency graphs, and dynamically delegates execution to specialized, parallel subagents—such as frontend engineers, backend developers, and quality assurance engineers. This distributed model maximizes the unique strengths of specialized LLMs by restricting their context windows to domain-specific concerns, thereby reducing hallucination rates, preventing context collapse during massive refactoring efforts, and enabling concurrent problem-solving.  
Currently, the Claude Code extension within visual studio environments provides a highly robust, deeply integrated ecosystem for executing these WAT topologies, utilizing proprietary Agent Teams and hierarchical Subagent architectures.1 However, the landscape of command-line interface (CLI) AI agents is rapidly expanding, and transitioning a WAT architecture to the Gemini CLI ecosystem introduces fundamental shifts in how parallel execution, tool delegation, system state, and context hierarchies are managed. The Gemini CLI ecosystem approaches multi-agent systems not merely as spawned parallel threads, but as a modular network of specialized extensions, native subagent schedulers, and advanced hierarchical context rendering algorithms.3  
The following analysis provides an exhaustive architectural teardown of both the Claude Code and Gemini CLI ecosystems. It details the mechanistic differences in multi-agent routing protocols, tool execution safeguards, and parallel orchestration scheduling. Furthermore, it outlines a comprehensive, step-by-step technical migration strategy and concludes with the definitive meta-prompt required to seamlessly transpile a Claude Code WAT environment into a fully functional, natively parallel Gemini CLI workspace.

## **Architectural Foundations of the Claude Code Subsystem**

To successfully mirror and reconstruct an existing WAT architecture within a new environment, it is necessary to first deconstruct how the source environment handles state and orchestration. Claude Code operates on two distinct parallelization primitives: Agent Teams and Subagents. Each primitive serves a unique operational purpose and is governed by strict protocols regarding context isolation, communication overhead, and tool access privileges. Understanding these mechanisms is essential for mapping them to Gemini's equivalent constructs.

### **Agent Teams and Peer-to-Peer Orchestration**

Agent Teams in Claude Code represent a decentralized, peer-to-peer orchestration model designed primarily for complex, non-deterministic problem-solving.1 Unlike traditional hierarchical setups where workers only speak to managers, an Agent Team consists of multiple, fully independent Claude Code instances operating concurrently.6 One instance is algorithmically designated as the "Team Lead," assuming the role of the WAT executive. This lead is responsible for synthesizing the overarching directive from the user, managing the initial task generation, and ultimately synthesizing the final deliverables into a coherent pull request or commit.2 The remaining instances, termed "Teammates," are spawned in completely separate context windows, ensuring that their reasoning paths do not pollute the executive's memory.6  
The defining characteristic of an Agent Team is direct inter-agent communication. Teammates possess the capability to message each other directly to challenge hypotheses, share intermediate findings, and coordinate cross-layer changes.1 For example, a backend teammate altering an API payload can directly notify the frontend teammate to adjust the corresponding data interfaces, bypassing the Team Lead.1 Coordination across the team is strictly managed through a shared task list stored locally within the \~/.claude/tasks/ directory on the host machine.6 To prevent race conditions during concurrent execution, Claude Code utilizes a filesystem locking mechanism. This allows teammates to autonomously "self-claim" tasks only when all upstream dependencies for that specific task have been marked as resolved in the shared state file.6  
This architecture is uniquely powerful for tasks requiring competing hypotheses or cross-layer coordination, such as debugging complex microservices where multiple root causes are plausible.2 From a user interface perspective within VS Code or terminal environments, teammates can be monitored in real-time using a tmux backend or split-pane terminal emulators.1 This allows the human developer to visualize the team working in parallel and interact with individual agents without routing messages through the Team Lead.1 However, this architectural independence incurs severe token costs and computational overhead, as each teammate maintains an active, concurrent, high-context session, rapidly consuming API credits and necessitating careful financial management.1

### **Hierarchical Subagents and Tool Restriction Protocols**

For highly structured, sequential tasks, or tasks requiring strict domain isolation, Claude Code utilizes Subagents. Unlike the decentralized nature of Agent Teams, Subagents operate within a single main session, adopting a strict, deterministic worker-to-manager hierarchy.2 When the main executive agent encounters a task matching a subagent's designated semantic description, it halts its own reasoning loop and delegates the workload via an internal tool call.6 The subagent then operates within an isolated context loop to preserve the primary context window. However, unlike teammates, subagents cannot communicate with one another; they must report their findings and execution status directly back to the main executive agent upon task completion.6  
Subagents are explicitly defined using Markdown files augmented with YAML frontmatter, creating a rigid behavioral contract.6 This configuration protocol strictly enforces the agent's identity, memory scope, permitted LLM model, and, most critically, tool access constraints.6 A standard Claude Code subagent configuration requires the explicit definition of tools (an allowlist of executable actions) and disallowedTools (a denylist of prohibited actions).6  
For example, Claude Code includes built-in subagents such as "Explore" and "Plan." The Explore subagent is optimized for read-only codebase analysis.6 In its YAML frontmatter, it is explicitly denied access to "Write" and "Edit" tools, ensuring that an exploratory task cannot accidentally mutate the codebase.6 Conversely, a "General-purpose" subagent inherits all tools available to the main conversation, including advanced integrations like Model Context Protocol (MCP) servers and the native code\_execution\_20250825 tool.6 This specific code execution tool provides secure sandbox access to Bash environments, package management, and direct file manipulation, allowing the subagent to autonomously compile code and run test suites.8  
Claude Code further enforces security and operational guardrails through sophisticated lifecycle hooks. The PreToolUse hook allows the system to run arbitrary validation scripts before an agent executes a tool—such as blocking SQL write operations from a database-reading subagent—while the PostToolUse hook can trigger formatters, linters, or testing suites immediately after an LLM-driven edit is completed, ensuring the output meets the repository's continuous integration standards.6

## **The Gemini CLI Architectural Paradigm**

Transitioning the WAT architecture requires adapting to the fundamental philosophical and structural differences of the Gemini CLI ecosystem. Gemini CLI approaches multi-agent orchestration not simply as a monolithic binary spawning threads, but as an extensible, highly customizable platform prioritizing massive context windows, high-speed asynchronous processing, and a diverse extension architecture.9 Replicating the executive assistant setup in Gemini requires a deep understanding of its context compilation techniques, native parallel execution protocols, and experimental agent declarations.

### **Context Modularity and State Persistence via GEMINI.md**

Where Claude Code frequently relies on a singular CLAUDE.md file to dictate project rules and executive routing instructions, Gemini CLI utilizes a highly modular, hierarchical context rendering system centered around GEMINI.md files.4 When the Gemini CLI initializes, it does not merely read a single prompt file; it aggregates instructions from the global directory (\~/.gemini/GEMINI.md), down through the project root, and explicitly scans sub-directories up to a trusted root boundary.4  
To support complex WAT architectures without overwhelming the initial context window or causing attention dilution within the LLM, Gemini CLI supports an advanced import syntax.4 Using the @file.md directive, a root GEMINI.md file can dynamically import specialized instruction sets based on the active phase of development.12 This methodology, often referred to as "gated execution through delayed instructions," ensures that the executive agent only processes instructions relevant to the current workflow state.14 For instance, the orchestrator might only import @/docs/testing-protocols.md when it officially transitions the project from the implementation phase to the quality assurance phase.14  
Users can interact with this loaded context via the /memory command interface. Commands such as /memory show display the fully concatenated, hierarchical memory being provided to the model, while /memory reload forces a dynamic re-scan of all context files, allowing the executive agent to absorb updated architectural guidelines mid-session without requiring a restart.4

### **Native Function Calling and Controlled Generation**

At the core of any agentic system is the ability of the LLM to interface with external tools. Gemini CLI leverages the underlying Gemini API's robust function calling capabilities, allowing the model to act as a bridge between natural language reasoning and deterministic real-world actions.15 The system operates by providing the model with a list of function declarations defined in OpenAPI schema format.16 When the model determines a tool is necessary, it outputs structured data specifying the tool and its requisite parameters, pausing its generation until the CLI executes the tool and returns the observation.16  
Crucially for executive routing, the Gemini ecosystem natively supports parallel function calling.16 This means the executive model can output multiple tool execution requests simultaneously within a single conversational turn.16 Furthermore, Gemini 1.5 and 2.0 models support controlled generation, an advancement built upon controlled decoding that forces the model to strictly adhere to a predefined JSON schema.18 By setting the response\_mime\_type to application/json, developers ensure that when an executive agent queries a subagent, the response is always a deterministically parsable object, preventing downstream parsing errors that frequently derail autonomous workflows.18

### **Extension Ecosystem and MCP Integration**

While Claude Code tightly integrates tools natively, Gemini CLI views tools, skills, and MCP servers as modular packages delivered via its Extension Ecosystem.10 An extension acts as a "shipping container" for custom functionalities, bundling MCP server configurations, context files, custom slash commands (via TOML files), and specific tool restrictions.10  
The Model Context Protocol (MCP) is fully supported in Gemini CLI, and the community has developed numerous extensions tailored for WAT setups. Extensions like google-workspace, firebase, and elasticsearch provide immediate database MCP integration, while specialized extensions like apify-agent-skills or code-review inject pre-configured skills directly into the CLI environment.19 Extension configuration has been streamlined via gemini-extension.json files and system settings, ensuring sensitive data like API keys are stored in secure system keychains rather than plain text.20

## **Orchestrating Multi-Agent Workflows in Gemini CLI**

To successfully mimic the Claude Code WAT executive assistant—which delegates to frontend, backend, and QA subagents—one must master Gemini CLI's subagent architecture. Gemini handles subagents through an experimental framework that relies heavily on YAML declarations, specialized extension frameworks, and native parallel batch schedulers.

### **Subagent Declaration and the YOLO Execution Protocol**

In the Gemini CLI, subagents are treated as localized "specialists" that the main orchestrator agent can invoke exactly as it would invoke a standard tool.22 To utilize subagents, the experimental flag must be activated by setting enableAgents to true within the settings.json file.22  
Subagents are defined as individual Markdown files containing YAML frontmatter and are located either in a project-scoped .gemini/agents/ directory (which takes priority for team workflows) or a global \~/.gemini/agents/ directory.22  
The YAML frontmatter schema for a Gemini CLI subagent is rigidly defined to dictate its behavior:

* **name**: The unique identifier (slug). This becomes the explicit tool name the main agent calls.22  
* **description**: The critical semantic trigger. Unlike imperative programming, the main agent evaluates this natural language description to determine when to route tasks to this specific specialist. For a WAT setup, descriptions must be mutually exclusive and exhaustive.22  
* **tools**: The isolated set of tools the subagent is permitted to use (e.g., restricting a QA subagent to read\_file and shell for testing, but denying write\_file).22  
* **model**: The specific LLM to be utilized. Gemini CLI permits model overriding at the subagent level. For example, a complex reasoning task can be routed to gemini-2.5-pro (or even open models like DeepSeek R1 if configured), while a simple bulk documentation task is handled by the cheaper, faster gemini-2.5-flash.3

When the executive orchestrator invokes a subagent, the interaction is pushed into a completely separate context loop.22 This shields the main executive thread from token bloat and context collapse, preserving its high-level strategic overview.  
A distinct operational characteristic of Gemini CLI subagents is their default operation in "YOLO mode".22 In YOLO mode, subagents execute their designated tools—such as terminal commands and file writes—autonomously, without pausing to request user confirmation for each individual step.22 While this dramatically accelerates background task completion, it requires rigorous prompt engineering and robust filesystem safety protocols to prevent catastrophic shell injections, unintended path traversals, or accidental deletion of critical infrastructure.24

### **Parallel Subagent Dispatch and Batch Scheduling**

Achieving true, concurrent parallel execution has been a core evolutionary focus for the Gemini CLI ecosystem, moving beyond the limitations of sequential tool execution. The system leverages the native Gemini subagent scheduler to facilitate parallel dispatch.5  
Under this protocol, parallel batches are executed as contiguous agent tool calls within a single conversational turn.5 When the WAT executive determines that the frontend UI update and the backend database schema update have no mutually blocking dependencies, it outputs a parallel function call invoking both the frontend-engineer and backend-engineer subagents simultaneously.16 The CLI infrastructure handles the concurrent spawning of these isolated context loops.  
To manage API rate limits and local compute resources, Gemini utilizes environment variables such as MAESTRO\_MAX\_CONCURRENT.5 This configuration controls exactly how many subagents are emitted per batch turn; setting it to 0 allows the entire ready batch to execute simultaneously, maximizing speed at the cost of high instantaneous API burst requests.5 Alternatively, for massive workloads, tasks can be routed through the Gemini Batch API, which processes high volumes of asynchronous requests via JSON Lines (JSONL) files at a 50% discount compared to real-time inference, ideal for deep codebase static analysis or comprehensive regression testing.27

### **Advanced Orchestration: The Maestro, Jules, and Superpowers Extensions**

To implement a fully featured WAT architecture without building the orchestration logic from scratch, the Gemini CLI community relies heavily on specialized workflow extensions. These extensions transform the CLI from a simple chat interface into a rigorous development platform.  
**The Maestro Extension** Maestro is the premier multi-agent orchestration extension for Gemini CLI, designed specifically to replicate and exceed the capabilities of Claude's Agent Teams.3 Instead of a single AI session handling everything, Maestro natively delegates work to up to 12 specialized subagents (including architect, coder, tester, debugger, and security-engineer).28  
Maestro coordinates these agents through a strict 4-phase workflow directed by a "TechLead" orchestrator:

1. **Design**: Structured requirements gathering with architectural trade-off analysis.29  
2. **Plan**: Automated phase decomposition, agent assignment, and dependency mapping.29  
3. **Execute**: Agents work their assigned phases, leveraging the native subagent scheduler to run in parallel where dependencies allow.24  
4. **Complete**: Final review, session archival, and deliverable summary synthesis.29

Maestro enforces security and state management via Gemini CLI's native hook system, injecting middleware directly at the agent boundaries.28 The BeforeAgent hook tracks which subagent is active, prunes stale state files, and injects live session context directly into the delegation turn.28 Crucially, the AfterAgent hook validates that every subagent's output strictly adheres to a predetermined JSON or Markdown structure (including a Task Report and Downstream Context section) before allowing the orchestrator to resume, ensuring the executive agent is never poisoned with malformed data.28  
**The Jules and Superpowers Extensions** Other extensions facilitate different WAT workflows. The Jules extension focuses on asynchronous multi-tasking and background execution.19 It allows the developer to delegate tedious tasks—such as resolving security vulnerabilities or updating dependencies across multiple GitHub repositories—to an isolated environment.19 Jules clones the repository into a virtual machine, executes the fixes in parallel, and opens a pull request, all without blocking the developer's active terminal session.19  
Similarly, the Superpowers extension injects proven methodologies directly into the agent's context.30 It forces the Gemini CLI to adhere to strict Test-Driven Development (TDD) protocols and utilizes lifecycle hooks to automatically refresh the agent's context between attempts, preventing the "context rot" that inevitably plagues long-running autonomous sessions.30

### **Enterprise Scalability: The Agent-to-Agent (A2A) Protocol**

For organizations where a WAT architecture must scale beyond local compute constraints, Gemini CLI supports the Agent-to-Agent (A2A) protocol.32 A2A is an open communication standard utilizing JSON-RPC 2.0 over HTTP(S), enabling agents from entirely different platforms to discover, collaborate, and securely delegate tasks.32  
In this setup, remote subagents are defined locally using kind: remote in their YAML frontmatter, alongside an agent\_card\_url pointing to the remote agent's endpoint.22 The remote agent advertises its capabilities via an "Agent Card" formatted in a strict JSON schema.34 This allows a local Gemini CLI executive agent to read the Agent Card, realize it lacks the required data access to fulfill a user request, and dynamically route the specific workload to an external, cloud-hosted micro-agent.35 This interaction handles rich data exchange, including text, binary files, and structured JSON, making it ideal for connecting a local coding agent to a remote enterprise database intelligence agent.34

## **Comparative Architectural Analysis: Claude Code vs. Gemini CLI**

Transitioning the WAT architecture is not merely a syntactic translation; it requires adapting to the fundamental performance, economic, and operational differences between the Anthropic and Google generative ecosystems. A developer must carefully weigh the trade-offs in reasoning depth, token economics, and execution speed.  
To provide clarity on these distinctions, the following table maps the comparative analytics of both systems based on extensive benchmarking and architectural documentation.1

| Feature Metric | Claude Code (Anthropic) | Gemini CLI (Google) | Architectural Implication |
| :---- | :---- | :---- | :---- |
| **Context Window Limit** | Standard limits (200K typically). | Massive scale (1M \- 2M+ tokens). | Gemini can ingest entire medium-sized repositories simultaneously, facilitating broader cross-file relationship understanding without relying strictly on RAG.37 |
| **Token Economics** | Extremely high cost for parallel tasks. | Highly cost-efficient, especially via Batch API. | Running concurrent Agent Teams in Claude quickly consumes API credits. Gemini permits extensive background parallelization at a fraction of the cost.1 |
| **Coding Quality & Precision** | Superior (Rated \~9.1/10). | High (Rated \~7.8/10). | Claude (especially Sonnet 3.7) consistently produces higher-quality code requiring fewer iterations and possesses superior error-handling heuristics.36 |
| **Execution & Prototyping Speed** | Moderate. Focuses on deep analysis. | Extremely rapid (Rated \~8.5/10). | Gemini generates output significantly faster, making it optimal for rapid prototyping and bulk documentation, though it may require manual "nudging" to close complex loops.11 |
| **Tool Execution Autonomy** | Strict PreToolUse hooks and permission flags. | "YOLO Mode" by default. | Gemini relies on external extensions (like Maestro's BeforeAgent hooks) to enforce safety, whereas Claude natively restricts actions more aggressively.6 |
| **Context Configuration** | Singular CLAUDE.md file. | Hierarchical GEMINI.md with @file.md imports. | Gemini allows for highly modular, state-dependent instruction loading, conserving context space.4 |
| **Subagent Delegation** | Internal context shifting. | Native subagent scheduler & parallel batching. | Gemini natively supports executing multiple subagents in a single turn, providing true concurrent throughput.5 |

The data indicates that while Claude Code excels at deep, complex refactoring where a single mistake could corrupt the repository, Gemini CLI is superior for vast multi-agent architectures where speed, context retention over massive codebases, and cost-efficiency are paramount.11 The Gemini WAT architecture will likely execute tasks much faster in parallel, but will require stricter prompt engineering to ensure the subagents output properly structured code and do not hallucinate file paths during YOLO mode execution.

## **Migration Protocol: Translating the State Machine**

To successfully execute the WAT strategy within Gemini CLI, the architecture must be constructed around a central orchestrator that leverages the native subagent capabilities. Because Gemini CLI requires manual enabling of experimental agent features, the workspace environment must be explicitly tailored.

### **Phase 1: Structuring the Base Environment and Strategist**

The translation begins at the configuration layer. Gemini CLI relies on settings.json.20 To support the WAT model, the experimental.enableAgents flag must be activated, and folderTrust should be set to allow autonomous background execution.22  
In Claude Code, the WAT executive is governed by CLAUDE.md. In Gemini, this is replaced by the root GEMINI.md file.4 The prompt must instruct the model to design this file not as a generic coding guideline, but as a rigid state-machine. The GEMINI.md file will define the "Strategist" persona. This Strategist must be explicitly instructed to maintain a "Master Plan" checklist in a designated markdown file (e.g., session-log.md), iteratively ticking off boxes as parallel tasks complete.39 To maintain token efficiency, the GEMINI.md file will utilize the import syntax, pulling in context only when necessary (e.g., @.gemini/context/frontend-rules.md).12

### **Phase 2: Architecting the Subagent Workforce**

The core of the WAT setup resides in the specialized subagents. The existing Claude configurations must be converted into Gemini's specific Markdown/YAML format, stored inside the .gemini/agents/ directory.22  
Each subagent (e.g., frontend-engineer.md, database-architect.md, qa-tester.md) must possess:

1. **A Precise Slug Name**: Used by the CLI to route the tool call.  
2. **A Hyper-Descriptive Trigger**: The description field must semantically map to the tasks the subagent is responsible for, ensuring the Strategist calls the correct agent.  
3. **Strict Tool Allowlists**: Replacing Claude's disallowedTools logic, Gemini agents must be given a strict subset of tools in the tools array (e.g., limiting QA to read-only capabilities).  
4. **A Structural Output Mandate**: Because Gemini agents operate in isolated YOLO loops, the system prompt must dictate that the agent concludes its work by writing a structured JSON or Markdown task report. This satisfies the return parameters expected by the Strategist and prevents infinite execution loops.28

### **Phase 3: Enforcing Parallel Execution and Hook Validation**

To mimic Claude Code's concurrent processing, the Gemini WAT setup must leverage the native subagent scheduler.5 The Strategist must be prompted to group independent tasks and execute contiguous agent tool calls within a single turn.5  
If interactive, real-time tracking is desired (similar to Claude's tmux split panes), the prompt will implement the advanced shell-spawning syntax: gemini \-i \<custom prompt path\>.39 This drops the subagent execution into an interactive terminal window, providing live-reloading visibility into the agent's actions while the main orchestrator awaits the exit code.39  
To mirror the rigorous quality control of the Claude Code environment, the migration must include hook scripts.31 Using Gemini's hook architecture, the setup will include shell scripts bound to BeforeAgent and AfterAgent lifecycle events.28 The AfterAgent hook will parse the output of the engineers. If a subagent fails to provide a formatted task report or introduces a syntax error, the hook will throw an error code. This forces the Gemini CLI to reject the subagent's output and enter a self-correction loop, protecting the Strategist's main context window from corruption.28

## **The Meta-Prompt Translation Directive**

To execute this architectural migration automatically, a highly technical, multi-part prompt must be fed to the existing Claude Code orchestrator. Claude is uniquely capable of parsing its own internal state, evaluating the current subagent configurations, and rewriting them into the Gemini CLI standard.  
The following prompt forces Claude to act as a cross-platform compilation engine, stripping out Anthropic-specific configurations (CLAUDE.md, hierarchical context suppression, disallowedTools) and injecting the Google Gemini equivalents (YAML frontmatter, @file.md imports, native parallel batching, and shell hooks).  
---

**System Directive: Transpile WAT Architecture to Gemini CLI Ecosystem**  
You are currently acting as the Executive Orchestrator in a Workflow, Agent, Tool (WAT) architecture within the Claude Code environment. Your objective is to analyze your current multi-agent configuration, operational guidelines, and subagent structures, and fully transpile this environment into a Gemini CLI compatible workspace. Gemini CLI operates on a fundamentally different orchestration paradigm utilizing native parallel batching, modular context imports, YAML-frontmatter agent files, and extensive lifecycle hooks.  
Execute the following steps systematically, generating the necessary files and directory structures directly into the root of this project. Do not execute external tools to look up Gemini documentation; rely on the architectural guidelines provided in this prompt.  
**Phase 1: Environment Initialization & Core Configuration**

1. Create a .gemini/ directory in the root of the project.  
2. Inside .gemini/, generate a settings.json file. Ensure the following configurations are set to enable experimental subagents, automated tool execution, and strict directory trust for background tasks:  
   JSON  
   {  
     "experimental": {  
       "enableAgents": true  
     },  
     "folderTrust": "always",  
     "autoAccept": true  
   }

**Phase 2: Translating the Subagent Workforce**  
Analyze every subagent currently available to you in this Claude Code setup (e.g., frontend engineer, backend engineer, QA). For each subagent, create a corresponding markdown file within the .gemini/agents/ directory (e.g., .gemini/agents/frontend-engineer.md).

* **YAML Frontmatter Requirements:** Each file MUST begin with valid YAML frontmatter containing name, description, tools, and model.  
* **Semantic Triggering:** The description field is hyper-critical. The Gemini orchestrator relies entirely on this text to decide when to invoke the agent as a tool. Write an exhaustive, mutually exclusive description detailing exactly what tasks this agent handles.  
* **Tool Constraints:** Replace Claude's disallowedTools logic by explicitly declaring ONLY the allowed tools in the tools array (e.g., \["read\_file", "write\_file", "shell"\]). Do not include tools the agent should not use.  
* **Output Protocol:** In the Markdown body of the subagent, instruct the agent that it operates in an isolated context loop (YOLO mode). It MUST conclude its work by writing a structured "Task Report" detailing files modified, tests run, and downstream dependencies affected.

## ***Example Subagent Skeleton:***

## **name: backend-engineer description: Invoked to modify server logic, database schemas, and API endpoints. tools: \["read\_file", "write\_file", "grep\_search", "shell"\] model: inherit**

# **Persona**

You are a senior backend systems engineer.

# **Protocol**

1. Execute the required modifications autonomously.  
2. Verify syntax using local linters via the shell tool.  
3. Return a structured JSON or Markdown Task Report to the Strategist.

**Phase 3: Architecting the Strategist Executive (GEMINI.md)**  
Analyze the current CLAUDE.md and your own internal executive system prompt. Transpile this logic into a new file located at GEMINI.md in the project root.

* **The Persona:** Define the role as the "Strategist/TechLead". The Strategist does not write code directly; it plans, delegates to the .gemini/agents/, and reviews the output.  
* **Parallel Execution Protocol:** Explicitly instruct the Strategist on how to invoke parallel subagents. Instruct it to use Gemini's native subagent scheduler by emitting contiguous agent tool calls in a single turn. When multiple independent tasks exist (e.g., updating UI while simultaneously modifying the DB), the Strategist MUST output tool calls for both the frontend and backend subagents concurrently.  
* **State Tracking:** Command the Strategist to maintain a session-log.md file using a markdown checklist to track phase progression and task completion.  
* **Modular Imports:** If the current CLAUDE.md is overly long, modularize it. Break specific phase instructions into separate files (e.g., .gemini/context/design-phase.md) and use Gemini's import syntax (@.gemini/context/design-phase.md) inside the main GEMINI.md to keep the context window highly targeted.

**Phase 4: Establishing Quality Gates (Hooks)**  
To mimic Claude's PreToolUse and PostToolUse security guarantees, implement Gemini hook scripts.

1. Create a .gemini/hooks/after-agent.sh script.  
2. Write a bash script that validates the subagent's execution state. It should parse the modified files to ensure the subagent successfully completed the task without introducing syntax errors (e.g., running npm run lint, cargo check, or executing the test suite).  
3. If the validation check fails, the hook must exit with a non-zero status code. This signals the Gemini CLI to reject the subagent's output, preventing context rot and forcing the subagent into a self-correction loop before returning control to the Strategist.

**Execution Directive:** Read all local configuration files, subagent system prompts, tool allowlists, and architectural guidelines currently active in this workspace. Synthesize this data and generate the corresponding .gemini/ structure immediately.  
---

By following this architectural blueprint and utilizing the provided meta-prompt, a development team can successfully migrate a complex, multi-agent WAT environment from the Claude Code ecosystem into the highly scalable, massively parallelized, and deeply modular Gemini CLI ecosystem. This transition leverages the latest advancements in native function calling and hierarchical context management, ultimately yielding an autonomous software factory capable of handling immense codebases with unprecedented speed and efficiency.

#### **Works cited**

1. Claude Code Agent Teams (Full Tutorial): The BEST FEATURE of Claude Code is HERE\!, accessed March 13, 2026, [https://www.youtube.com/watch?v=zm-BBZIAJ0c](https://www.youtube.com/watch?v=zm-BBZIAJ0c)  
2. Orchestrate teams of Claude Code sessions \- Claude Code Docs, accessed March 13, 2026, [https://code.claude.com/docs/en/agent-teams](https://code.claude.com/docs/en/agent-teams)  
3. GitHub \- josstei/maestro-gemini: Turn Gemini CLI into a multi-agent platform — 12 specialized subagents, parallel dispatch, 4-phase orchestration, and standalone dev tools for code review, debugging, security, and performance, accessed March 13, 2026, [https://github.com/josstei/maestro-gemini](https://github.com/josstei/maestro-gemini)  
4. Provide context with GEMINI.md files \- Gemini CLI, accessed March 13, 2026, [https://geminicli.com/docs/cli/gemini-md/](https://geminicli.com/docs/cli/gemini-md/)  
5. Update: Maestro v1.3.0 — Native parallel execution & smart execution mode gate for Gemini CLI : r/GeminiCLI \- Reddit, accessed March 13, 2026, [https://www.reddit.com/r/GeminiCLI/comments/1rn2w4e/update\_maestro\_v130\_native\_parallel\_execution/](https://www.reddit.com/r/GeminiCLI/comments/1rn2w4e/update_maestro_v130_native_parallel_execution/)  
6. Create custom subagents \- Claude Code Docs, accessed March 13, 2026, [https://code.claude.com/docs/en/sub-agents](https://code.claude.com/docs/en/sub-agents)  
7. Ability to choose subagent's LLM model on runtime : r/GithubCopilot \- Reddit, accessed March 13, 2026, [https://www.reddit.com/r/GithubCopilot/comments/1qxwim9/ability\_to\_choose\_subagents\_llm\_model\_on\_runtime/](https://www.reddit.com/r/GithubCopilot/comments/1qxwim9/ability_to_choose_subagents_llm_model_on_runtime/)  
8. Code execution tool \- Claude API Docs, accessed March 13, 2026, [https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool](https://platform.claude.com/docs/en/agents-and-tools/tool-use/code-execution-tool)  
9. Gemini CLI: Build, debug & deploy with AI, accessed March 13, 2026, [https://geminicli.com/](https://geminicli.com/)  
10. Getting Started with Gemini CLI Extensions \- Google Codelabs, accessed March 13, 2026, [https://codelabs.developers.google.com/getting-started-gemini-cli-extensions](https://codelabs.developers.google.com/getting-started-gemini-cli-extensions)  
11. Gemini CLi vs. Claude Code : The better coding agent \- Composio, accessed March 13, 2026, [https://composio.dev/blog/gemini-cli-vs-claude-code-the-better-coding-agent](https://composio.dev/blog/gemini-cli-vs-claude-code-the-better-coding-agent)  
12. Google Gemini CLI Cheatsheet \- Philschmid, accessed March 13, 2026, [https://www.philschmid.de/gemini-cli-cheatsheet](https://www.philschmid.de/gemini-cli-cheatsheet)  
13. Gemini CLI Tutorial Series — Part 9: Understanding Context, Memory and Conversational Branching | by Romin Irani | Google Cloud \- Medium, accessed March 13, 2026, [https://medium.com/google-cloud/gemini-cli-tutorial-series-part-9-understanding-context-memory-and-conversational-branching-095feb3e5a43](https://medium.com/google-cloud/gemini-cli-tutorial-series-part-9-understanding-context-memory-and-conversational-branching-095feb3e5a43)  
14. Practical Gemini CLI: Structured approach to bloated GEMINI.md | by Prashanth Subrahmanyam | Google Cloud \- Medium, accessed March 13, 2026, [https://medium.com/google-cloud/practical-gemini-cli-structured-approach-to-bloated-gemini-md-360d8a5c7487](https://medium.com/google-cloud/practical-gemini-cli-structured-approach-to-bloated-gemini-md-360d8a5c7487)  
15. Function calling using the Gemini API | Firebase AI Logic \- Google, accessed March 13, 2026, [https://firebase.google.com/docs/ai-logic/function-calling](https://firebase.google.com/docs/ai-logic/function-calling)  
16. Function calling with the Gemini API | Google AI for Developers, accessed March 13, 2026, [https://ai.google.dev/gemini-api/docs/function-calling](https://ai.google.dev/gemini-api/docs/function-calling)  
17. Introduction to function calling | Generative AI on Vertex AI \- Google Cloud Documentation, accessed March 13, 2026, [https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/multimodal/function-calling)  
18. How to consistently output JSON with the Gemini API using controlled generation \- Medium, accessed March 13, 2026, [https://medium.com/google-cloud/how-to-consistently-output-json-with-the-gemini-api-using-controlled-generation-887220525ae0](https://medium.com/google-cloud/how-to-consistently-output-json-with-the-gemini-api-using-controlled-generation-887220525ae0)  
19. Master multi-tasking with the Jules extension for Gemini CLI ..., accessed March 13, 2026, [https://cloud.google.com/blog/topics/developers-practitioners/master-multi-tasking-with-the-jules-extension-for-gemini-cli](https://cloud.google.com/blog/topics/developers-practitioners/master-multi-tasking-with-the-jules-extension-for-gemini-cli)  
20. Gemini CLI configuration, accessed March 13, 2026, [https://geminicli.com/docs/reference/configuration/](https://geminicli.com/docs/reference/configuration/)  
21. Making Gemini CLI extensions easier to use \- Google Developers Blog, accessed March 13, 2026, [https://developers.googleblog.com/making-gemini-cli-extensions-easier-to-use/](https://developers.googleblog.com/making-gemini-cli-extensions-easier-to-use/)  
22. Subagents (experimental) \- Gemini CLI, accessed March 13, 2026, [https://geminicli.com/docs/core/subagents/](https://geminicli.com/docs/core/subagents/)  
23. AI Code Editor \- Sub-Agents | Tencent Cloud Code Assistant CodeBuddy, accessed March 13, 2026, [https://www.codebuddy.ai/docs/cli/sub-agents](https://www.codebuddy.ai/docs/cli/sub-agents)  
24. Update: Maestro v1.1.0 — Multi-Agent Orchestration for Gemini CLI: Parallel Dispatch, Security Hardening, and Runtime Controls : r/GeminiAI \- Reddit, accessed March 13, 2026, [https://www.reddit.com/r/GeminiAI/comments/1r5wr3z/update\_maestro\_v110\_multiagent\_orchestration\_for/](https://www.reddit.com/r/GeminiAI/comments/1r5wr3z/update_maestro_v110_multiagent_orchestration_for/)  
25. Update: Maestro v1.3.0 — Native parallel execution & smart execution mode gate for Gemini CLI : r/Bard \- Reddit, accessed March 13, 2026, [https://www.reddit.com/r/Bard/comments/1rn2xil/update\_maestro\_v130\_native\_parallel\_execution/](https://www.reddit.com/r/Bard/comments/1rn2xil/update_maestro_v130_native_parallel_execution/)  
26. Parallel Execution of Subagents · Issue \#17749 · google-gemini/gemini-cli \- GitHub, accessed March 13, 2026, [https://github.com/google-gemini/gemini-cli/issues/17749](https://github.com/google-gemini/gemini-cli/issues/17749)  
27. Batch API | Gemini API \- Google AI for Developers, accessed March 13, 2026, [https://ai.google.dev/gemini-api/docs/batch-api](https://ai.google.dev/gemini-api/docs/batch-api)  
28. Update: Maestro v1.2.0 — Multi-Agent Orchestration for Gemini CLI: Lifecycle Hooks, Plan Mode, and Runtime Handoff Enforcement : r/GeminiCLI \- Reddit, accessed March 13, 2026, [https://www.reddit.com/r/GeminiCLI/comments/1r8rf73/update\_maestro\_v120\_multiagent\_orchestration\_for/](https://www.reddit.com/r/GeminiCLI/comments/1r8rf73/update_maestro_v120_multiagent_orchestration_for/)  
29. Update: Maestro v1.1.0 — Multi-Agent Orchestration for Gemini CLI: Parallel Dispatch, Security Hardening, and Runtime Controls : r/GeminiCLI \- Reddit, accessed March 13, 2026, [https://www.reddit.com/r/GeminiCLI/comments/1r5wo95/update\_maestro\_v110\_multiagent\_orchestration\_for/](https://www.reddit.com/r/GeminiCLI/comments/1r5wo95/update_maestro_v110_multiagent_orchestration_for/)  
30. barretstorck/gemini-superpowers \- GitHub, accessed March 13, 2026, [https://github.com/barretstorck/gemini-superpowers](https://github.com/barretstorck/gemini-superpowers)  
31. Tailor Gemini CLI to your workflow with hooks \- Google Developers Blog, accessed March 13, 2026, [https://developers.googleblog.com/tailor-gemini-cli-to-your-workflow-with-hooks/](https://developers.googleblog.com/tailor-gemini-cli-to-your-workflow-with-hooks/)  
32. Register and manage A2A agents | Gemini Enterprise \- Google Cloud Documentation, accessed March 13, 2026, [https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent](https://docs.cloud.google.com/gemini/enterprise/docs/register-and-manage-an-a2a-agent)  
33. Remote Subagents (experimental) \- Gemini CLI, accessed March 13, 2026, [https://geminicli.com/docs/core/remote-agents/](https://geminicli.com/docs/core/remote-agents/)  
34. Agent2Agent (A2A) is an open protocol enabling communication and interoperability between opaque agentic applications. · GitHub, accessed March 13, 2026, [https://github.com/a2aproject/A2A](https://github.com/a2aproject/A2A)  
35. Announcing the Agent2Agent Protocol (A2A) \- Google for Developers Blog, accessed March 13, 2026, [https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)  
36. Claude Code vs. Gemini CLI vs. Cursor vs. Qwen Code — Comparing Top AI Coding Assistant | by Fendy Feng | Medium, accessed March 13, 2026, [https://medium.com/@fendylike/top-ai-coding-assistants-claude-code-vs-gemini-cli-vs-cursor-vs-qwen-code-0bc759fc9d45](https://medium.com/@fendylike/top-ai-coding-assistants-claude-code-vs-gemini-cli-vs-cursor-vs-qwen-code-0bc759fc9d45)  
37. Claude Code vs Gemini CLI: Which One's the Real Dev Co-Pilot? \- Milvus, accessed March 13, 2026, [https://milvus.io/blog/claude-code-vs-gemini-cli-which-ones-the-real-dev-co-pilot.md](https://milvus.io/blog/claude-code-vs-gemini-cli-which-ones-the-real-dev-co-pilot.md)  
38. Gemini CLI Weekly Update \[v0.26.0\]: Skills, Hooks and the ability to take a step back with /rewind : r/GeminiCLI \- Reddit, accessed March 13, 2026, [https://www.reddit.com/r/GeminiCLI/comments/1qpoqf1/gemini\_cli\_weekly\_update\_v0260\_skills\_hooks\_and/](https://www.reddit.com/r/GeminiCLI/comments/1qpoqf1/gemini_cli_weekly_update_v0260_skills_hooks_and/)  
39. Advanced Gemini CLI: Part 3—Dynamic Isolated Agents | by ..., accessed March 13, 2026, [https://medium.com/google-cloud/advanced-gemini-cli-part-3-isolated-agents-b9dbab70eeff](https://medium.com/google-cloud/advanced-gemini-cli-part-3-isolated-agents-b9dbab70eeff)