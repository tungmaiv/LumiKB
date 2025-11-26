# User Stories & Use Cases: LumiKB Work OS

This document outlines the functional requirements through User Stories and detailed Use Cases for the LumiKB expansion.

## 1. User Stories

### Workspace & Project Management
*   **US-01**: As a **Department Lead**, I want to create a **Workspace** (e.g., "Sales", "Legal") with specific default Agents and Knowledge Bases, so that my team has a focused environment.
*   **US-02**: As a **Project Manager**, I want to create a **Project** (e.g., "Q3 Audit") within a Workspace, so that I can organize tasks, documents, and workflows for a specific goal.
*   **US-03**: As a **User**, I want to upload **Artifacts** (documents) to a Project, so that Agents can use them as context for that specific case.

### Agents & Tools
*   **US-04**: As a **Developer**, I want to register **Custom Tools** (Python functions or SQL queries), so that Agents can interact with our internal systems (databases, CRMs).
*   **US-05**: As a **User**, I want to assign a **Task** to a specific **Agent Persona** (e.g., "Legal Reviewer"), so that the work is done with the right expertise and tone.
*   **US-06**: As a **User**, I want to invoke **Tools** directly in chat (e.g., `/run risk_calculator`), so that I can get quick answers without switching apps.

### Workflows
*   **US-07**: As a **Process Owner**, I want to define a **Workflow** (sequence of steps), so that complex standard operating procedures (SOPs) can be automated.
*   **US-08**: As a **User**, I want to trigger a **Workflow** from chat, so that I can start a multi-step process (like "Onboard Employee") with a single command.
*   **US-09**: As a **Manager**, I want to review **Human-in-the-Loop** steps in a workflow, so that I can approve critical outputs before the workflow continues.

---

## 2. Expanded Use Cases

### Use Case 1: Sales Enablement (Smart RFP Response)
**Scenario**: A Sales Rep needs to respond to a complex RFP from a large bank.

*   **Workspace**: Sales
*   **Project**: "Bank of America RFP 2025"
*   **Actors**: User (Sales Rep), Agent (Proposal Writer).
*   **Tools**: `crm_lookup` (Salesforce), `pricing_calculator`.
*   **Workflow**:
    1.  **Ingest**: User uploads `RFP_Requirements.docx` to the Project.
    2.  **Analyze**: Agent reads the doc and extracts 50 key requirements.
    3.  **Research (Parallel)**:
        *   Agent searches "Product Knowledge KB" for technical answers.
        *   Agent calls `crm_lookup` to find similar past winning proposals.
    4.  **Draft**: Agent synthesizes answers into a new `Draft_Response.docx`.
    5.  **Pricing**: Agent uses `pricing_calculator` to estimate costs based on the requirements.
    6.  **Review**: User reviews the draft, edits two sections, and approves.

### Use Case 2: Customer Support (Tier 2 Resolution)
**Scenario**: A Support Engineer investigates a reported API latency issue.

*   **Workspace**: Technical Support
*   **Project**: "Ticket #9928 - API Latency"
*   **Actors**: User (Support Eng), Agent (Log Analyst).
*   **Tools**: `log_fetcher` (Splunk/ELK), `jira_creator`.
*   **Workflow**:
    1.  **Triage**: User types `/investigate ticket-9928` in chat.
    2.  **Data Gathering**: Agent calls `log_fetcher` to pull error logs for the customer's tenant ID.
    3.  **Diagnosis**: Agent analyzes logs and searches "Troubleshooting KB" for matching error patterns.
    4.  **Recommendation**: Agent suggests: "High DB connection pool usage detected. Recommended fix: Increase pool size."
    5.  **Action**: User confirms. Agent calls `jira_creator` to log a bug for the Engineering team with all logs attached.

### Use Case 3: Legal (Contract Risk Review)
**Scenario**: A Legal Counsel reviews a vendor agreement.

*   **Workspace**: Legal
*   **Project**: "Vendor Agreement - AWS"
*   **Actors**: User (Counsel), Agent (Risk Assessor).
*   **Tools**: `clause_library` (Database of standard terms).
*   **Workflow**:
    1.  **Upload**: User uploads `AWS_Service_Terms.pdf`.
    2.  **Comparison**: Agent compares the document against the "Standard Terms" in `clause_library`.
    3.  **Highlight**: Agent flags 3 clauses that deviate significantly from company policy (e.g., "Unlimited Liability").
    4.  **Report**: Agent generates a "Risk Assessment Memo" citing the specific risky clauses and suggesting redlines.

### Use Case 4: HR (Employee Onboarding)
**Scenario**: HR Manager onboards a new hire.

*   **Workspace**: HR
*   **Project**: "Onboarding - John Doe"
*   **Actors**: User (HR Mgr), Agent (Onboarding Coordinator).
*   **Tools**: `hris_system` (Workday), `email_sender`, `provisioning_tool`.
*   **Workflow**:
    1.  **Trigger**: User runs `/onboard john.doe@example.com --role="Senior Dev"`.
    2.  **Provisioning**: Agent calls `provisioning_tool` to create AD account and email.
    3.  **Documentation**: Agent generates "Offer Letter" and "Welcome Packet" from templates.
    4.  **Communication**: Agent calls `email_sender` to send the Welcome Packet to the candidate.
    5.  **Task Assignment**: Agent creates a task "Verify I-9 Documents" assigned to the User (HR Mgr).

---

## 3. Recommended "Starter Kit"
To launch this enhancement successfully, we recommend shipping with these pre-built templates:

1.  **"General Research" Workspace**:
    *   **Agent**: Deep Researcher (Web Search + KB).
    *   **Workflow**: "Deep Dive Report" (Search -> Outline -> Draft -> Review).

2.  **"Sales" Workspace**:
    *   **Agent**: Proposal Architect.
    *   **Tool**: CRM Mockup (for demo).
    *   **Workflow**: "RFP Responder".

3.  **"Coding" Workspace**:
    *   **Agent**: Senior Engineer.
    *   **Tool**: GitHub/GitLab integration.
    *   **Workflow**: "Code Review Assistant".

---

## 4. Comprehensive Entity Management (CRUD)

This section details the requirements for managing the lifecycle (Create, Read, Update, Delete) of all system entities.

### 4.1 Workspace Management
*   **US-10 [Create]**: As an **Admin**, I want to create a new **Workspace** by defining its Name, Domain (e.g., Sales), and Description, so that I can set up a new department.
*   **US-11 [Configure]**: As a **Workspace Admin**, I want to configure **Default Settings** (e.g., link specific KBs, set default Agents), so that all projects in the workspace inherit the right context.
*   **US-12 [Update]**: As a **Workspace Admin**, I want to **Rename** or **Update Description** of a workspace to reflect organizational changes.
*   **US-13 [Archive/Delete]**: As an **Admin**, I want to **Archive** a workspace (making it read-only) or **Delete** it (if created in error), to keep the system clean.

### 4.2 Project Management
*   **US-14 [Create]**: As a **User**, I want to create a new **Project** from scratch OR from a **Template** (e.g., "Standard Audit Project"), to save setup time.
*   **US-15 [Update Status]**: As a **Project Manager**, I want to update the **Project Status** (Planning -> In Progress -> Completed), so stakeholders know the progress.
*   **US-16 [Manage Members]**: As a **Project Owner**, I want to add/remove **Members** to a project, controlling who has access to its sensitive artifacts.
*   **US-17 [Close]**: As a **Project Manager**, I want to **Close** a project upon completion, ensuring no further changes can be made to its artifacts.

### 4.3 Agent Management
*   **US-18 [Define Custom]**: As a **Power User**, I want to define a **Custom Agent** by specifying a Name, Role, Icon, and **System Prompt**, to create a specialized persona (e.g., "The Grumpy Editor").
*   **US-19 [Equip Tools]**: As a **Power User**, I want to select which **Tools** (from the registry) this agent can access, ensuring it has the right capabilities (and security boundaries).
*   **US-20 [Test Agent]**: As a **User**, I want to **Test** a new agent in a sandbox chat window before publishing it to the workspace.
*   **US-21 [Update/Version]**: As a **Power User**, I want to tweak an agent's System Prompt and save it, instantly updating the agent's behavior for new tasks.

### 4.4 Tool Management
*   **US-22 [Register Code Tool]**: As a **Developer**, I want to register a new **Python Tool** by providing the function code/path and schema definition, making it available for agents.
*   **US-23 [Register API Tool]**: As a **Developer**, I want to register an **MCP Tool** (Model Context Protocol) by providing the server URL, so we can connect to external microservices.
*   **US-24 [Configure Secrets]**: As an **Admin**, I want to securely store **API Keys/Secrets** for a tool (e.g., Salesforce API Key) so that agents can use the tool without seeing the credentials.
*   **US-25 [Disable]**: As an **Admin**, I want to **Disable** a malfunctioning tool globally, preventing any agent from calling it until fixed.

### 4.5 Workflow Management
*   **US-26 [Design]**: As a **Process Owner**, I want to use a **Visual Builder** (Drag & Drop) to define steps (Nodes) and dependencies (Edges), creating a workflow graph.
*   **US-27 [Configure Steps]**: As a **Process Owner**, I want to configure each step (e.g., "Select Agent: Researcher", "Input: Project Docs"), defining exactly what happens at each node.
*   **US-28 [Validate]**: As a **System**, I want to automatically **Validate** the workflow graph for cycles or missing inputs before allowing it to be saved.
*   **US-29 [Versioning]**: As a **Process Owner**, I want to save **Versions** (v1, v2) of a workflow, so I can safely iterate without breaking active projects using v1.

### 4.6 Artifact Management
*   **US-30 [Upload]**: As a **User**, I want to **Upload** files (PDF, DOCX, CSV) to a Project or Workspace, creating Source Artifacts.
*   **US-31 [Preview]**: As a **User**, I want to **Preview** an artifact (Source or Generated) directly in the browser without downloading it.
*   **US-32 [Version]**: As a **User**, I want to upload a **New Version** of a document (e.g., "Contract_v2.pdf"), keeping the history of previous versions.
*   **US-33 [Delete]**: As a **User**, I want to **Delete** an artifact, removing it from the system and vector database (if indexed).

### 4.7 Testing & Debugging
*   **US-34 [Test Tool]**: As a **Developer**, I want to **Test** a registered tool by providing JSON input and viewing the raw output, to ensure the code/API connection is correct before assigning it to an agent.
*   **US-35 [Dry Run Workflow]**: As a **Process Owner**, I want to **Dry Run** a workflow with test inputs, so I can verify the logic flow and data passing between nodes without affecting production data (where possible).
*   **US-36 [Inspect Execution]**: As a **User**, I want to **Inspect** the step-by-step logs (inputs, outputs, errors) of a workflow execution, to debug why it failed or produced unexpected results.
*   **US-37 [Replay Step]**: As a **Developer**, I want to **Replay** a specific failed step in a workflow with corrected code/inputs, to fix issues without restarting the entire long-running process.

---

## 5. Creative Intelligence Suite (CIS)

### 5.1 Innovation Workflows
*   **US-38 [Brainstorming Session]**: As a **Product Manager**, I want to start a **Brainstorming Session** with Agent "Carson", where he facilitates divergent thinking (e.g., "Yes, and..." technique) to generate 50+ ideas for a new feature.
*   **US-39 [Design Thinking]**: As a **UX Designer**, I want to run a **Design Thinking Workflow** (Empathize -> Test), so that I can systematically solve a user pain point with AI guidance at each stage.
*   **US-40 [Storytelling]**: As a **Founder**, I want to use the **Storytelling Workflow** with Agent "Sophia" to craft a compelling pitch deck narrative using the "Hero's Journey" framework.

### 5.2 Facilitation Tools
*   **US-41 [Facilitator Mode]**: As a **User**, I want the agent to ask **Probing Questions** (Facilitation) rather than just giving answers, to help me clarify my own thinking.
*   **US-42 [Idea Clustering]**: As a **User**, I want the system to automatically **Cluster** hundreds of brainstormed sticky notes into thematic groups, so I can spot patterns.
*   **US-43 [Persona Switch]**: As a **User**, I want to switch the facilitator persona (e.g., from "Optimistic Carson" to "Critical Dr. Quinn") to stress-test my ideas from different angles.

---

## 6. Quality Assurance (Quality Gates)

### 6.1 Gate Definition
*   **US-44 [Define Gate]**: As a **Process Owner**, I want to define a **Quality Gate** with a checklist of criteria (e.g., "Must have Executive Summary", "Must cite 3 sources"), so that I can standardize output quality.
*   **US-45 [Link to Artifact]**: As a **Process Owner**, I want to link a Quality Gate to a specific **Artifact Type** (e.g., "All RFP Responses"), so that the check is automatically applied whenever such a document is generated.

### 6.2 Gate Enforcement
*   **US-46 [Auto-Check]**: As a **User**, I want the **Evaluator Agent** to automatically check my draft against the Quality Gate and provide a Pass/Fail result with specific feedback, saving me manual review time.
*   **US-47 [Manual Override]**: As a **Manager**, I want to manually **Override** a failed gate (with a justification comment) if the criteria are not applicable to this specific case.
*   **US-48 [Workflow Blocker]**: As a **System**, I want to **Block** a workflow from proceeding to the next step until the required Quality Gate is passed, preventing low-quality work from moving downstream.

---

## 7. AI-Assisted Configuration (Recommendations)

To reduce setup friction, the system uses LLMs to recommend configurations.

*   **US-49 [Recommend Agent]**: As a **User** creating a task, I want the system to **Suggest** the most suitable Agent by analyzing the task requirements against Agent **Properties** (Role, Capabilities, Tools).
    *   *Example*: Task "Review Q3 Financials for compliance" -> System matches "Compliance" keyword and "Read-Only" requirement -> Suggests **"Auditor Agent"** (Role: Compliance, Tools: [Read-Only DB Access, Policy KB], Mode: Strict).
*   **US-50 [Recommend Workflow]**: As a **Project Manager** creating a project, I want the system to **Suggest** a Workflow template based on the project name and goal (e.g., "Q3 Audit" -> Suggest "Internal Audit Workflow").
*   **US-51 [Recommend Tools]**: As a **Developer** defining a new Agent, I want the system to **Suggest** relevant Tools from the library based on the Agent's Role and System Prompt (e.g., Role "Analyst" -> Suggest "Calculator", "Web Search").
*   **US-52 [Recommend Template]**: As a **User** inside a Workspace, I want the system to **Suggest** relevant Document/Project Templates based on the workspace domain (e.g., Sales Workspace -> Suggest "RFP Response Template").
*   **US-53 [Auto-Fill Metadata]**: As a **User** uploading an artifact, I want the system to **Auto-Fill** metadata (Tags, Description, Related Project) by analyzing the file content.
