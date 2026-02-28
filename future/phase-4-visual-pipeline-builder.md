# Phase 4: Visual Pipeline Builder

> React Flow DAG editor — see your data pipeline as an interactive graph

**Depends on:** Phase 3 (Desktop IDE)

---

## Goal

Add the visual heart of PipelineGPT: an interactive React Flow pipeline diagram where users can see, edit, and build data pipelines as directed acyclic graphs (DAGs). The AI generates the graph from conversation; users can also drag-and-drop nodes to build manually. Both approaches stay in sync — edit the graph, and the code updates; refine in chat, and the graph updates.

This is the feature that differentiates PipelineGPT from every other AI data tool. It makes the invisible (data flow) visible.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Chat Panel (35%)  │  Results Panel (65%)                   │
│                    │                                        │
│  "Join customer    │  ┌─ Pipeline Diagram ────────────────┐ │
│   data with orders │  │                                    │ │
│   and aggregate    │  │  ┌──────────┐    ┌──────────────┐ │ │
│   by region"       │  │  │ 📥 Read   │───▶│ ⚙️ Join       │ │ │
│                    │  │  │ Customers │    │ customer_id  │ │ │
│  ┌──────────────┐  │  │  └──────────┘    └──────┬───────┘ │ │
│  │ AI: Built a  │  │  │                         │         │ │
│  │ 5-step       │  │  │  ┌──────────┐           │         │ │
│  │ pipeline...  │  │  │  │ 📥 Read   │───────────┘         │ │
│  └──────────────┘  │  │  │ Orders   │    ┌──────────────┐ │ │
│                    │  │  └──────────┘    │ ⚙️ Aggregate  │ │ │
│                    │  │                  │ by region     │──│─│─▶ ...
│                    │  │                  └──────────────┘ │ │
│                    │  │                                    │ │
│                    │  │  [+] Add Step  │  Zoom │  Fit All │ │
│                    │  └────────────────────────────────────┘ │
│                    │                                        │
│                    │  ┌─ Step Inspector ───────────────────┐ │
│                    │  │  Selected: Join (⚙️ Transform)     │ │
│                    │  │  Join Key: customer_id             │ │
│                    │  │  Join Type: inner                  │ │
│                    │  │  Explanation: Combines customer    │ │
│                    │  │  records with their order history  │ │
│                    │  │  ⚠ Warning: No null handling       │ │
│                    │  └────────────────────────────────────┘ │
└────────────────────┴────────────────────────────────────────┘
```

---

## Pipeline Node Types

Following the PipelineGPT design spec, nodes are color-coded by type:

### Source Nodes (Blue — `#3b82f6`)
| Operation | Icon | Description |
|-----------|------|-------------|
| `read_csv` | 📄 | Read CSV file |
| `read_json` | 📋 | Read JSON file |
| `read_parquet` | 📦 | Read Parquet file |
| `read_delta` | △ | Read Delta table |
| `read_unity_catalog` | 🏛 | Read from Unity Catalog |
| `read_redshift` | 🔴 | Read from Redshift |
| `read_glue_catalog` | 📚 | Read from AWS Glue |
| `read_s3` | ☁️ | Read from S3 |

### Transform Nodes (Amber — `#f59e0b`)
| Operation | Icon | Description |
|-----------|------|-------------|
| `filter` | 🔍 | Filter rows |
| `join` | 🔗 | Join two sources |
| `aggregate` | 📊 | Group by + aggregate |
| `sort` | ↕️ | Sort rows |
| `rename_columns` | ✏️ | Rename columns |
| `cast_types` | 🔄 | Type casting |
| `deduplicate` | 🧹 | Remove duplicates |
| `fill_nulls` | 🩹 | Handle null values |
| `add_column` | ➕ | Computed column |
| `pivot` | 📐 | Pivot table |
| `window_function` | 🪟 | Window function |

### Destination Nodes (Green — `#22c55e`)
| Operation | Icon | Description |
|-----------|------|-------------|
| `write_delta` | △ | Write Delta table |
| `write_unity_catalog` | 🏛 | Write to Unity Catalog |
| `write_csv` | 📄 | Write CSV |
| `write_parquet` | 📦 | Write Parquet |
| `write_redshift` | 🔴 | Write to Redshift |
| `write_s3` | ☁️ | Write to S3 |
| `display_output` | 🖥 | Display results |

---

## Requirements

### R4.1: Pipeline Diagram Rendering

**User Story:** As a user, I want to see my data pipeline as a visual graph, so I can understand the flow of data at a glance.

**Acceptance Criteria:**
- WHEN a pipeline is generated THE SYSTEM SHALL render it as a React Flow DAG with left-to-right layout
- EACH NODE SHALL show: operation icon, step label, and step type color
- EDGES SHALL flow from source → transform → destination following `dependsOn` relationships
- THE DIAGRAM SHALL auto-layout using dagre or elkjs for clean node positioning
- WHEN no pipeline exists THE SYSTEM SHALL show an empty state: "Your pipeline will appear here. Describe what you need in the chat."
- THE DIAGRAM SHALL support zoom (scroll wheel), pan (drag background), and fit-to-view
- THE DIAGRAM SHALL have a minimap for large pipelines

### R4.2: Node Selection and Inspection

**User Story:** As a user, I want to click a pipeline step and see its details, so I can understand what each step does.

**Acceptance Criteria:**
- WHEN a node is clicked THE SYSTEM SHALL select it with a glowing ring in the node's type color
- WHEN a node is selected THE SYSTEM SHALL display the Step Inspector panel with:
  - Step name, type, and operation
  - Configuration details (join key, filter condition, aggregation, etc.)
  - Plain-English explanation (from the AI narration)
  - Warnings (if any) with severity indicators
  - Generated SQL or PySpark code snippet for that step
- WHEN a node with a warning is rendered THE SYSTEM SHALL show a colored warning dot in the top-right corner
- WHEN the user clicks the background THE SYSTEM SHALL deselect all nodes

### R4.3: Drag-and-Drop Pipeline Building

**User Story:** As a power user, I want to build pipelines visually by dragging nodes from a palette, so I can construct complex flows without typing.

**Acceptance Criteria:**
- THE SYSTEM SHALL provide a node palette (sidebar or floating panel) with all available operations grouped by type
- WHEN a user drags a node from the palette onto the canvas THE SYSTEM SHALL add it to the pipeline
- WHEN a user drags from one node's output handle to another node's input handle THE SYSTEM SHALL create an edge (dependency)
- WHEN a new node is added THE SYSTEM SHALL open a configuration form for that operation (e.g., join key, filter condition)
- WHEN the graph is modified manually THE SYSTEM SHALL update the pipeline definition and regenerate code
- WHEN an edge would create a cycle THE SYSTEM SHALL prevent it and show an error tooltip

### R4.4: Bidirectional Sync (Chat ↔ Graph)

**User Story:** As a user, I want changes in the chat to update the graph, and changes in the graph to be reflected in the pipeline.

**Acceptance Criteria:**
- WHEN the AI generates a pipeline from chat THE SYSTEM SHALL render/update the React Flow diagram
- WHEN the user manually adds/removes/connects nodes THE SYSTEM SHALL update the pipeline definition
- WHEN the pipeline definition changes (from any source) THE SYSTEM SHALL regenerate PySpark code
- WHEN the user sends a refinement in chat THE SYSTEM SHALL animate the graph transition (new nodes fade in, removed nodes fade out)
- THE SYSTEM SHALL support undo/redo for graph operations (Ctrl+Z / Ctrl+Shift+Z)

### R4.5: Live Data Preview

**User Story:** As a user, I want to see a preview of the data at each step, so I can verify the pipeline is producing correct results.

**Acceptance Criteria:**
- WHEN a node is selected THE SYSTEM SHALL show a "Preview" tab in the inspector with sample data (first 10 rows)
- THE PREVIEW SHALL show column names, types, and row count
- WHEN the preview data contains PII THE SYSTEM SHALL apply role-based redaction
- WHEN a transform node is selected THE SYSTEM SHALL show "before" and "after" previews (input vs output)
- THE PREVIEW SHALL update when the pipeline is re-executed

### R4.6: Pipeline Export as Image

**User Story:** As a presenter, I want to export my pipeline diagram as an image for slides and documentation.

**Acceptance Criteria:**
- WHEN the user clicks "Export Diagram" THE SYSTEM SHALL save the pipeline as a PNG or SVG
- THE EXPORT SHALL include node labels, colors, and edges
- THE EXPORT SHALL support transparent or dark background options
- THE EXPORT SHALL fit the pipeline to the image bounds with padding

---

## Custom React Flow Node Component

```tsx
// PipelineNode.tsx — custom node rendering
interface PipelineNodeData {
  label: string;
  stepType: "source" | "transform" | "destination";
  operation: string;
  icon: string;
  explanation?: string;
  warning?: { message: string; severity: "low" | "medium" | "high" };
  isSelected?: boolean;
  rowCount?: number;
}

// Node colors
const NODE_COLORS = {
  source:      { bg: "bg-blue-500/10",  border: "border-blue-500",  text: "text-blue-400"  },
  transform:   { bg: "bg-amber-500/10", border: "border-amber-500", text: "text-amber-400" },
  destination: { bg: "bg-green-500/10", border: "border-green-500", text: "text-green-400" },
};
```

---

## Tech Stack Additions

| Component | Technology |
|-----------|-----------|
| Pipeline Diagram | React Flow (@xyflow/react) |
| Auto-Layout | dagre or elkjs |
| Animation | Framer Motion (node transitions) |
| Drag-and-Drop | React DnD or React Flow built-in |

---

## Success Criteria

- [ ] Pipelines render as clean left-to-right DAGs
- [ ] Nodes are color-coded by type (blue/amber/green)
- [ ] Clicking a node shows the step inspector with details
- [ ] Drag-and-drop from palette creates new nodes
- [ ] Connecting nodes via handles creates edges
- [ ] Chat refinements animate graph updates (nodes fade in/out)
- [ ] Live data preview shows sample rows at each step
- [ ] Undo/redo works for all graph operations
- [ ] Export produces clean PNG/SVG images
- [ ] Large pipelines (20+ steps) render and pan smoothly
