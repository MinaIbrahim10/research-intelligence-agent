import {
  useMemo,
  useRef,
  useState,
} from "react";

import {
  AlertTriangle,
  ArrowRight,
  BookOpen,
  Check,
  CheckCircle2,
  CircleAlert,
  Clipboard,
  Clock3,
  Download,
  ExternalLink,
  FileSearch,
  Gauge,
  Globe2,
  Layers3,
  LoaderCircle,
  Search,
  ShieldCheck,
  Sparkles,
  TriangleAlert,
  XCircle,
} from "lucide-react";

import {
  runResearchStream,
} from "./api/research";

import "./styles.css";


const EXAMPLE_QUERY =
  "Compare LangGraph and CrewAI for " +
  "building reliable production AI " +
  "agent systems";


function clamp(value) {
  return Math.max(
    0,
    Math.min(
      1,
      Number(value) || 0,
    ),
  );
}


function percent(value) {
  return Math.round(
    clamp(value) * 100,
  );
}


function confidenceLabel(value) {
  const score = clamp(value);

  if (score >= 0.85) {
    return "High";
  }

  if (score >= 0.65) {
    return "Moderate";
  }

  if (score > 0) {
    return "Limited";
  }

  return "No coverage";
}


function statusMeta(status) {
  switch (status) {
    case "VERIFIED":
      return {
        label: "Verified",
        icon: CheckCircle2,
        className: "verified",
      };

    case "PARTIALLY_VERIFIED":
      return {
        label: "Partially verified",
        icon: CircleAlert,
        className: "partial",
      };

    case "CONFLICTING":
      return {
        label: "Conflicting",
        icon: TriangleAlert,
        className: "conflicting",
      };

    case "UNSUPPORTED":
    default:
      return {
        label: "Unsupported",
        icon: XCircle,
        className: "unsupported",
      };
  }
}


function StatusBadge({
  status,
}) {
  const meta = statusMeta(
    status,
  );

  const Icon = meta.icon;

  return (
    <span
      className={
        "status-badge " +
        meta.className
      }
    >
      <Icon size={14} />
      {meta.label}
    </span>
  );
}


function ConfidenceBar({
  value,
  compact = false,
}) {
  const safe = clamp(value);

  return (
    <div
      className={
        compact
          ? "confidence confidence-compact"
          : "confidence"
      }
    >
      <div className="confidence-track">
        <div
          className="confidence-fill"
          style={{
            width:
              `${percent(safe)}%`,
          }}
        />
      </div>

      <span>
        {percent(safe)}%
      </span>
    </div>
  );
}


function MetricCard({
  icon: Icon,
  label,
  value,
  detail,
}) {
  return (
    <article className="metric-card">
      <div className="metric-icon">
        <Icon size={19} />
      </div>

      <div>
        <div className="metric-label">
          {label}
        </div>

        <div className="metric-value">
          {value}
        </div>

        {detail && (
          <div className="metric-detail">
            {detail}
          </div>
        )}
      </div>
    </article>
  );
}


function EmptyState() {
  return (
    <section className="empty-state">
      <div className="empty-orbit">
        <Search size={34} />
      </div>

      <h2>
        Research with evidence,
        not guesses.
      </h2>

      <p>
        Enter a research question.
        The system will plan,
        search, fetch full pages,
        extract evidence, verify
        claims, measure coverage,
        and build a cited report.
      </p>

      <div className="pipeline-preview">
        {[
          "Plan",
          "Search",
          "Fetch",
          "Evidence",
          "Verify",
          "Report",
        ].map(
          (stage, index) => (
            <div
              key={stage}
              className="pipeline-stage"
            >
              <span>
                {index + 1}
              </span>

              {stage}
            </div>
          ),
        )}
      </div>
    </section>
  );
}


const LIVE_STAGES = [
  {
    id: "planner",
    label:
      "Planning research questions",
  },
  {
    id: "search",
    label:
      "Searching the web",
  },
  {
    id: "fetch_sources",
    label:
      "Fetching full pages",
  },
  {
    id: "researcher",
    label:
      "Extracting evidence",
  },
  {
    id: "relevance",
    label:
      "Filtering relevance",
  },
  {
    id: "consolidator",
    label:
      "Consolidating claims",
  },
  {
    id: "verifier",
    label:
      "Verifying claims",
  },
  {
    id: "reporter",
    label:
      "Building final report",
  },
];


function RunningState({
  progress,
}) {
  const currentIndex =
    progress?.index ?? 0;

  return (
    <section className="agent-progress-card">
      <div className="agent-progress-header">
        <div className="running-icon">
          <LoaderCircle
            className="spin"
            size={25}
          />
        </div>

        <div>
          <div className="eyebrow">
            Live agent execution
          </div>

          <h3>
            {
              progress?.label ||
              "Starting research"
            }
          </h3>

          <p>
            {
              progress?.detail ||
              "Initializing the research pipeline."
            }
          </p>
        </div>

        <div className="progress-percentage">
          {Math.round(
            (
              progress
                ?.progress ?? 0
            ) * 100,
          )}
          %
        </div>
      </div>

      <div className="agent-progress-track">
        <div
          className="agent-progress-fill"
          style={{
            width:
              `${
                Math.round(
                  (
                    progress
                      ?.progress ??
                    0
                  ) * 100,
                )
              }%`,
          }}
        />
      </div>

      <div className="agent-stage-list">
        {LIVE_STAGES.map(
          (
            stage,
            index,
          ) => {
            let state =
              "pending";

            if (
              index <
              currentIndex
            ) {
              state =
                "complete";
            } else if (
              index ===
              currentIndex
            ) {
              state =
                progress
                  ?.status ||
                "running";
            }

            return (
              <div
                key={
                  stage.id
                }
                className={
                  "agent-stage " +
                  state
                }
              >
                <div className="stage-indicator">
                  {state ===
                  "complete" ? (
                    <Check
                      size={13}
                    />
                  ) : state ===
                    "running" ? (
                    <LoaderCircle
                      className="spin"
                      size={13}
                    />
                  ) : (
                    <span />
                  )}
                </div>

                <span>
                  {stage.label}
                </span>
              </div>
            );
          },
        )}
      </div>
    </section>
  );
}


function ResearchHeader({
  query,
  setQuery,
  running,
  onSubmit,
  onExample,
}) {
  return (
    <section className="hero">
      <div className="hero-glow hero-glow-one" />
      <div className="hero-glow hero-glow-two" />

      <div className="hero-content">
        <div className="eyebrow">
          <Sparkles size={15} />
          Agentic research engine
        </div>

        <h1>
          Research &
          <span>
            {" "}Intelligence
          </span>
          {" "}Agent
        </h1>

        <p className="hero-copy">
          Multi-stage web research
          with claim-level
          traceability, verification,
          confidence and explicit
          evidence gaps.
        </p>

        <form
          className="research-form"
          onSubmit={onSubmit}
        >
          <div className="query-box">
            <Search
              className="query-icon"
              size={21}
            />

            <textarea
              value={query}
              onChange={(event) =>
                setQuery(
                  event.target.value,
                )
              }
              placeholder={
                "Ask a deep research " +
                "question..."
              }
              rows={3}
              disabled={running}
            />
          </div>

          <div className="form-actions">
            <button
              className="example-button"
              type="button"
              onClick={onExample}
              disabled={running}
            >
              Use example
            </button>

            <button
              className="primary-button"
              type="submit"
              disabled={
                running ||
                !query.trim()
              }
            >
              {running ? (
                <>
                  <LoaderCircle
                    className="spin"
                    size={17}
                  />
                  Researching
                </>
              ) : (
                <>
                  Run research
                  <ArrowRight
                    size={17}
                  />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </section>
  );
}


function ErrorCard({
  error,
}) {
  return (
    <section className="error-card">
      <AlertTriangle size={22} />

      <div>
        <strong>
          Research failed
        </strong>

        <p>
          {error}
        </p>
      </div>
    </section>
  );
}


function ReportSummary({
  data,
}) {
  const report =
    data.report;

  const verification =
    data.verification;

  return (
    <>
      <section className="summary-card">
        <div className="summary-copy">
          <div className="eyebrow">
            <ShieldCheck size={15} />
            Research complete
          </div>

          <h2>
            Evidence-backed report
          </h2>

          <p>
            {
              report.executive_summary
            }
          </p>
        </div>

        <div className="overall-score">
          <div className="score-ring">
            <span>
              {percent(
                report
                  .overall_confidence,
              )}
            </span>

            <small>
              confidence
            </small>
          </div>

          <div>
            <strong>
              {confidenceLabel(
                report
                  .overall_confidence,
              )}
            </strong>

            <p>
              Coverage-adjusted
            </p>
          </div>
        </div>
      </section>

      <section className="metric-grid">
        <MetricCard
          icon={Globe2}
          label="Search sources"
          value={
            data.corpus
              .unique_sources
          }
          detail="Ranked & deduplicated"
        />

        <MetricCard
          icon={FileSearch}
          label="Pages fetched"
          value={
            data.sources
              .fetched_sources
          }
          detail={
            `${data.sources.failed_sources}` +
            " failed"
          }
        />

        <MetricCard
          icon={Layers3}
          label="Evidence"
          value={
            data.evidence
              .total_findings
          }
          detail={
            `${data.claims.total_claims}` +
            " consolidated claims"
          }
        />

        <MetricCard
          icon={ShieldCheck}
          label="Verified"
          value={
            verification
              .verified_claims
          }
          detail={
            `${
              verification
                .partially_verified_claims
            } partial`
          }
        />
      </section>
    </>
  );
}


function EntityCoverage({
  required,
  covered,
}) {
  if (!required?.length) {
    return null;
  }

  const coveredSet =
    new Set(
      covered.map(
        (item) =>
          item.toLowerCase(),
      ),
    );

  return (
    <div className="entity-row">
      {required.map(
        (entity) => {
          const isCovered =
            coveredSet.has(
              entity.toLowerCase(),
            );

          return (
            <span
              key={entity}
              className={
                isCovered
                  ? "entity-chip covered"
                  : "entity-chip missing"
              }
            >
              {isCovered ? (
                <Check size={13} />
              ) : (
                <CircleAlert
                  size={13}
                />
              )}

              {entity}
            </span>
          );
        },
      )}
    </div>
  );
}


function ClaimCard({
  claim,
}) {
  return (
    <article className="claim-card">
      <div className="claim-head">
        <StatusBadge
          status={claim.status}
        />

        <ConfidenceBar
          value={claim.confidence}
          compact
        />
      </div>

      <p className="claim-statement">
        {claim.statement}
      </p>

      {!!claim.source_ids?.length && (
        <div className="citation-row">
          {claim.source_ids.map(
            (sourceId) => (
              <span
                className="citation-chip"
                key={sourceId}
              >
                [{sourceId}]
              </span>
            ),
          )}
        </div>
      )}

      {!!claim.caveats?.length && (
        <div className="caveat-box">
          <strong>
            Caveats
          </strong>

          <ul>
            {claim.caveats.map(
              (caveat) => (
                <li key={caveat}>
                  {caveat}
                </li>
              ),
            )}
          </ul>
        </div>
      )}
    </article>
  );
}


function SectionCard({
  section,
  index,
}) {
  return (
    <article className="section-card">
      <header className="section-head">
        <div className="section-number">
          {String(
            index + 1,
          ).padStart(
            2,
            "0",
          )}
        </div>

        <div className="section-title">
          <h3>
            {section.question}
          </h3>

          <EntityCoverage
            required={
              section
                .required_entities
            }
            covered={
              section
                .covered_entities
            }
          />
        </div>
      </header>

      <div className="score-grid">
        <div>
          <span>
            Evidence strength
          </span>

          <ConfidenceBar
            value={
              section
                .evidence_confidence
            }
          />
        </div>

        <div>
          <span>
            Coverage
          </span>

          <ConfidenceBar
            value={
              section
                .coverage_ratio
            }
          />
        </div>

        <div>
          <span>
            Final confidence
          </span>

          <ConfidenceBar
            value={
              section.confidence
            }
          />
        </div>
      </div>

      <div className="claims-list">
        {section.claims?.length ? (
          section.claims.map(
            (claim) => (
              <ClaimCard
                key={
                  claim.claim_id
                }
                claim={claim}
              />
            ),
          )
        ) : (
          <div className="no-evidence">
            <CircleAlert
              size={18}
            />

            No sufficiently
            grounded claims were
            produced for this
            question.
          </div>
        )}
      </div>

      {!!section.gaps?.length && (
        <div className="gap-panel">
          <div className="gap-title">
            <TriangleAlert
              size={17}
            />

            Evidence gaps
          </div>

          <ul>
            {section.gaps.map(
              (gap) => (
                <li key={gap}>
                  {gap}
                </li>
              ),
            )}
          </ul>
        </div>
      )}
    </article>
  );
}


function SourcesPanel({
  sources,
}) {
  if (!sources?.length) {
    return null;
  }

  return (
    <section className="sources-section">
      <div className="section-label">
        <BookOpen size={18} />

        <div>
          <h2>
            Sources
          </h2>

          <p>
            Sources actually cited
            by verified or partial
            claims.
          </p>
        </div>
      </div>

      <div className="source-grid">
        {sources.map(
          (source) => (
            <a
              key={source.id}
              href={source.url}
              target="_blank"
              rel="noreferrer"
              className="source-card"
            >
              <div className="source-id">
                [{source.id}]
              </div>

              <div className="source-copy">
                <strong>
                  {source.title}
                </strong>

                <span>
                  {source.domain}
                </span>

                <small>
                  {
                    source
                      .source_category
                  }
                </small>
              </div>

              <ExternalLink
                size={16}
              />
            </a>
          ),
        )}
      </div>
    </section>
  );
}


function ReportActions({
  markdown,
}) {
  const [
    copied,
    setCopied,
  ] = useState(
    false,
  );

  async function copyMarkdown() {
    await navigator.clipboard.writeText(
      markdown,
    );

    setCopied(
      true,
    );

    window.setTimeout(
      () =>
        setCopied(
          false,
        ),
      1600,
    );
  }

  function downloadMarkdown() {
    const blob =
      new Blob(
        [markdown],
        {
          type:
            "text/markdown;charset=utf-8",
        },
      );

    const url =
      URL.createObjectURL(
        blob,
      );

    const anchor =
      document.createElement(
        "a",
      );

    anchor.href = url;

    anchor.download =
      "research-report.md";

    document.body.appendChild(
      anchor,
    );

    anchor.click();
    anchor.remove();

    URL.revokeObjectURL(
      url,
    );
  }

  return (
    <div className="report-actions">
      <button
        type="button"
        onClick={copyMarkdown}
      >
        {copied ? (
          <Check size={16} />
        ) : (
          <Clipboard
            size={16}
          />
        )}

        {copied
          ? "Copied"
          : "Copy Markdown"}
      </button>

      <button
        type="button"
        onClick={downloadMarkdown}
      >
        <Download size={16} />
        Download .md
      </button>
    </div>
  );
}


function App() {
  const [
    query,
    setQuery,
  ] = useState(
    "",
  );

  const [
    data,
    setData,
  ] = useState(
    null,
  );

  const [
    running,
    setRunning,
  ] = useState(
    false,
  );

  const [
    error,
    setError,
  ] = useState(
    "",
  );

  const [
    progress,
    setProgress,
  ] = useState(
    null,
  );

  const controllerRef =
    useRef(
      null,
    );

  const sections =
    useMemo(
      () =>
        data?.report
          ?.sections ?? [],
      [data],
    );

  async function handleSubmit(
    event,
  ) {
    event.preventDefault();

    const clean =
      query.trim();

    if (!clean || running) {
      return;
    }

    controllerRef.current
      ?.abort();

    const controller =
      new AbortController();

    controllerRef.current =
      controller;

    setRunning(
      true,
    );

    setError(
      "",
    );

    setData(
      null,
    );

    setProgress({
      stage: "planner",
      label:
        "Planning research questions",
      detail:
        "Breaking the objective into focused research questions.",
      status: "running",
      index: 0,
      total: 8,
      progress: 0,
    });

    try {
      const result =
        await runResearchStream(
          clean,
          {
            signal:
              controller.signal,

            onProgress:
              (
                update,
              ) => {
                setProgress(
                  update,
                );
              },
          },
        );

      setData(
        result,
      );
    } catch (requestError) {
      if (
        requestError.name ===
        "AbortError"
      ) {
        return;
      }

      setError(
        requestError.message ||
          "Unknown error",
      );
    } finally {
      setRunning(
        false,
      );
    }
  }

  return (
    <div className="app-shell">
      <nav className="topbar">
        <a
          href="#"
          className="brand"
        >
          <div className="brand-mark">
            R
          </div>

          <div>
            <strong>
              Research
            </strong>

            <span>
              Intelligence Agent
            </span>
          </div>
        </a>

        <div className="topbar-meta">
          <span className="live-dot" />

          Local research stack


        </div>
      </nav>

      <main>
        <ResearchHeader
          query={query}
          setQuery={setQuery}
          running={running}
          onSubmit={handleSubmit}
          onExample={() =>
            setQuery(
              EXAMPLE_QUERY,
            )
          }
        />

        <div className="content-wrap">
          {error && (
            <ErrorCard
              error={error}
            />
          )}

          {running && (
            <RunningState
              progress={
                progress
              }
            />
          )}

          {!running &&
            !data &&
            !error && (
              <EmptyState />
            )}

          {data && (
            <div className="report-stack">
              <div className="report-toolbar">
                <div>
                  <span>
                    Final research
                    output
                  </span>

                  <small>
                    {
                      data.report
                        .sections
                        .length
                    }{" "}
                    research questions
                  </small>
                </div>

                <ReportActions
                  markdown={
                    data.report
                      .markdown
                  }
                />
              </div>

              <ReportSummary
                data={data}
              />

              <section className="research-sections">
                <div className="section-label">
                  <Gauge size={19} />

                  <div>
                    <h2>
                      Research findings
                    </h2>

                    <p>
                      Confidence reflects
                      both evidence
                      strength and
                      comparison coverage.
                    </p>
                  </div>
                </div>

                <div className="sections-list">
                  {sections.map(
                    (
                      section,
                      index,
                    ) => (
                      <SectionCard
                        key={
                          section
                            .question_id
                        }
                        section={
                          section
                        }
                        index={
                          index
                        }
                      />
                    ),
                  )}
                </div>
              </section>

              {!!data.report
                .gaps?.length && (
                <section className="global-gap-card">
                  <div className="gap-title">
                    <TriangleAlert
                      size={18}
                    />
                    Remaining
                    research gaps
                  </div>

                  <ul>
                    {data.report.gaps.map(
                      (gap) => (
                        <li
                          key={gap}
                        >
                          {gap}
                        </li>
                      ),
                    )}
                  </ul>
                </section>
              )}

              <SourcesPanel
                sources={
                  data.report
                    .sources
                }
              />
            </div>
          )}
        </div>
      </main>

      <footer>
        <div>
          <ShieldCheck
            size={15}
          />
          Evidence-first agentic
          research
        </div>

        <div>
          <Clock3 size={15} />
          Local LLM + SearXNG
        </div>
      </footer>
    </div>
  );
}

export default App;
