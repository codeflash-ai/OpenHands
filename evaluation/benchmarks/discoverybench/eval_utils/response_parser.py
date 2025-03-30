workflow_summary_markers = [
    "WORKFLOW SUMMARY",
    "WORKFLOW_SUMMARY",
    "WORKFLOW-SUMMARY",
    "Workflow Summary",
]

final_answer_markers = [
    "FINAL ANSWER",
    "FINAL_ANSWER",
    "FINAL-ANSWER",
    "Final Answer",
    "Scientific Hypothesis",
    "Hypothesis",
]

next_agent_markers = [
    "NEXT AGENT",
    "NEXT-AGENT",
    "NEXT_AGENT",
    "FEEDBACK",
]


def extract_between(content, start_markers, end_markers=None):
    content_len = len(content)
    for marker in start_markers:
        marker_pos = content.find(marker)
        if marker_pos != -1:
            result = content[marker_pos + len(marker) :]
            if end_markers:
                for end_marker in end_markers:
                    end_marker_pos = result.find(end_marker)
                    if end_marker_pos != -1:
                        result = result[:end_marker_pos]
                        break  # Exit after the first found end marker
            return result
    return ""


def extract_gen_hypo_from_logs(content: str):
    error = ""

    gen_workflow = extract_between(
        content, workflow_summary_markers, final_answer_markers
    )

    if not gen_workflow:
        error += "No Workflow Summary found in the line. | "

    gen_hypothesis = extract_between(content, final_answer_markers, next_agent_markers)

    if not gen_hypothesis:
        error += "No Final Answer in the line."

    return gen_hypothesis, gen_workflow, error
