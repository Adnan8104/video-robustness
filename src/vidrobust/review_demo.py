"""Streamlit page for the experimental review queue."""
import csv
import hashlib
import logging

import streamlit as st


@st.cache_resource(show_spinner=False)
def get_service(root):
    from .review import ReviewService

    return ReviewService(root)


def main(root):
    st.set_page_config(page_title="Video Robustness", page_icon="🎞️", layout="centered")
    st.title("Prioritize for review")
    source = st.radio("Clips", ["Published benchmark", "Upload videos"], horizontal=True, key="review_source")
    if source == "Published benchmark":
        show_benchmark(root)
    else:
        show_uploads(root)


def show_benchmark(root):
    path = root / "reports/review-budget/scores.csv"
    try:
        with path.open(newline="") as stream:
            clips = list(csv.DictReader(stream))
    except OSError:
        st.error("The benchmark scores are missing. Use a checkout with reports/review-budget/scores.csv.")
        return
    if not clips:
        st.error("The published batch is empty.")
        return
    ai_total = sum(clip["label"] == "ai" for clip in clips)
    st.write(f"Explore saved scores for {len(clips)} heavily compressed clips "
             f"with {ai_total} Veo 3 clips and {len(clips) - ai_total} real clips.")
    budget = st.slider("Clips to review", 1, len(clips), min(10, len(clips)),
                       help="The published benchmark used ten review slots.")
    queues = {}
    for column, (name, score) in zip(st.columns(2), [
        ("Released WaveRep", "released_margin"), ("Trained WaveRep head", "trained_margin")
    ], strict=True):
        ordered = sorted(clips, key=lambda clip: (-float(clip[score]), clip["source_sha256"]))
        queue = ordered[:budget]
        ai_count = sum(clip["label"] == "ai" for clip in queue)
        column.metric(name, f"{ai_count} / {ai_total} AI clips")
        column.caption(f"{budget - ai_count} of {budget} review slots used by real clips")
        queues[name] = [f'{clip["video_id"]} · {"Veo 3" if clip["label"] == "ai" else "Real"}'
                        for clip in queue]
    st.dataframe({"Rank": range(1, budget + 1), **queues}, hide_index=True, width="stretch")


def show_uploads(root):
    from .inference import EXTENSIONS
    from .review import MAX_CLIPS

    st.write("Rank clips with the experimental WaveRep head. Review the clips at the top first.")
    st.caption("The score is used for ordering. A person makes the authenticity decision.")
    uploads = st.file_uploader("Choose videos", type=list(EXTENSIONS), accept_multiple_files=True,
        max_upload_size=100, key="review_uploads",
        help="Up to 20 clips, 100 MiB each and 200 MiB combined. "
             "Landscape, 504 pixels high or more, 4–30 seconds and 24–60 fps.")
    if not (root / "models/linear-head-policy.npz").is_file():
        st.info("Set up the fitted head using the README to run this mode.")
    files = [(file.name, file.getvalue()) for file in uploads]
    identity = tuple((name, hashlib.sha256(content).hexdigest()) for name, content in files)
    if identity != st.session_state.get("review_identity"):
        st.session_state["review_identity"] = identity
        st.session_state.pop("review_queue", None)
        st.session_state.pop("review_error", None)
    limit = max(1, min(MAX_CLIPS, len(files)))
    budget = st.number_input("Clips to review", min_value=1, max_value=limit,
                             value=min(10, limit), key=f"review_budget_{limit}")
    if st.button("Rank clips", type="primary", disabled=not files or len(files) > MAX_CLIPS):
        st.session_state.pop("review_queue", None)
        st.session_state.pop("review_error", None)
        try:
            with st.status("Preparing clips…") as status:
                st.session_state["review_queue"] = get_service(str(root)).rank(files,
                    progress=lambda count, total: status.update(label=f"Scored {count} of {total} clips"))
                status.update(label="Ranking complete", state="complete")
        except (ValueError, OSError, RuntimeError) as error:
            st.session_state["review_error"] = str(error)
        except Exception:
            logging.exception("Review ranking failed")
            st.session_state["review_error"] = "Ranking could not finish. Check the local terminal for details."
    if len(files) > MAX_CLIPS:
        st.error(f"Choose up to {MAX_CLIPS} clips.")
    if st.session_state.get("review_error"):
        st.error(st.session_state["review_error"])
    queue = st.session_state.get("review_queue")
    if queue:
        st.subheader(f"Top {budget} of {len(queue)} clips")
        st.table([{"Rank": index, "Video": row["name"], "Ranking score": f'{row["margin"]:.4f}'}
                  for index, row in enumerate(queue[:budget], start=1)])
    st.caption("Clips stay on this computer. Each score uses the middle four seconds after a CRF 35 compression pass.")
