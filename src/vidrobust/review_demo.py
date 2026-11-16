"""Streamlit page for the experimental review queue."""
import hashlib
import logging

import streamlit as st

from .inference import EXTENSIONS
from .review import MAX_CLIPS, ReviewService


@st.cache_resource(show_spinner=False)
def get_service(root):
    return ReviewService(root)


def main(root):
    st.set_page_config(page_title="Video Robustness", page_icon="🎞️", layout="centered")
    st.title("Prioritize for review")
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
