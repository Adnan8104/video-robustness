"""A local upload/check interface; inference stays in the reusable service."""
import hashlib
import json

import streamlit as st

from .inference import DetectionService, EXTENSIONS, score_summary


@st.cache_resource(show_spinner=False)
def get_service(root):
    return DetectionService(root)


def main(root):
    st.set_page_config(page_title="Video Robustness", page_icon="🎞️", layout="centered")
    st.caption("VIDEO ROBUSTNESS · LOCAL DEMO")
    st.title("Check a video")
    st.write("Compare how AEGIS and WaveRep respond to your clip.")
    st.info("Higher scores mean more AI-like. These scores are not confidence percentages, and the models can be wrong.")
    upload = st.file_uploader("Choose a video", type=list(EXTENSIONS), key="video_upload",
        help="Up to 100 MiB, 30 seconds and 1920 × 1080 pixels; 4–60 fps (portrait works too).")
    st.caption("Processed on this computer. Temporary video files are deleted after each check.")
    scan_sections = st.checkbox("Check beginning, middle and end", key="scan_sections",
        help="Adds two windows to see whether scores vary across the clip. Takes up to three times longer.")
    content = upload.getvalue() if upload is not None else None
    identity = (hashlib.sha256(content).hexdigest(), scan_sections) if content else None
    # A different upload must never display the previous video's result.
    if st.session_state.get("input_identity") != identity:
        st.session_state["input_identity"] = identity
        st.session_state.pop("result", None)
        st.session_state.pop("check_error", None)
    if content:
        with st.expander("Preview video"):
            st.video(content)
    if st.button("Check video", type="primary", disabled=not content):
        st.session_state.pop("result", None)
        st.session_state.pop("check_error", None)
        try:
            with st.status("Checking your video…", expanded=True) as status:
                st.write("Reading 16 frames per section." if scan_sections else "Reading 16 frames from the center of the clip.")
                result = get_service(str(root)).analyze(content, upload.name,
                    progress=lambda name: st.write(f"Running {name.upper()}…"), scan_sections=scan_sections)
                st.session_state["result"] = result
                status.update(label="Check complete", state="complete", expanded=False)
        except (ValueError, OSError, RuntimeError) as error:
            st.session_state["check_error"] = str(error)
        except Exception:
            st.session_state["check_error"] = "The detector could not finish. Check the local terminal for details."
            import logging
            logging.exception("Video check failed")
    if st.session_state.get("check_error"):
        st.error(st.session_state["check_error"])
    result = st.session_state.get("result")
    if result:
        scores = [row["ai_score"] for row in result["detectors"]]
        st.subheader(score_summary(scores))
        st.caption("Middle section")
        for column, row in zip(st.columns(len(scores)), result["detectors"]):
            with column:
                st.metric(row["detector"].upper(), f"{row['ai_score']:.4f}")
                st.progress(row["ai_score"])
                st.caption("More real-like ← score → More AI-like")
        st.caption("0.5 is a reference midpoint. Agreement between models does not prove that a video is real or AI-generated.")
        meta = result["metadata"]
        st.write(f"{meta['width']} × {meta['height']} · {result['duration_seconds']:.1f} seconds · 16 sampled frames")
        for warning in result["warnings"]:
            st.warning(warning)
        windows = result.get("windows", [])
        if result.get("scan_sections"):
            st.subheader("Scores by section")
            table = []
            for window in windows:
                times = window["sampled_time_seconds"]
                table.append({"Section": window["section"].title(), "Sampled time": f"{times[0]:.1f}–{times[-1]:.1f}s",
                    **{row["detector"].upper(): f"{row['ai_score']:.4f}" for row in window["detectors"]}})
            st.table(table)
            st.caption("Each section is scored separately. Scores are not averaged into a verdict.")
            if len(windows) == 1:
                st.caption("This clip is short enough that all three sections share the same window; it was checked once.")
        with st.expander("AEGIS component scores"):
            branches = []
            for window in windows or [dict(section="middle", detectors=result["detectors"])]:
                aegis = next((row for row in window["detectors"] if row["detector"] == "aegis"), None)
                if aegis and all(key in aegis for key in ("pixel_score", "motion_score", "consistency_score")):
                    branches.append({"Section": window["section"].title(), "Appearance": f"{aegis['pixel_score']:.4f}",
                        "Motion": f"{aegis['motion_score']:.4f}", "Consistency": f"{aegis['consistency_score']:.4f}"})
            if branches:
                st.table(branches)
            st.caption("These are separate learned scores, not explanations or contributions to the final score. A high appearance score does not identify a specific visual defect.")
        st.download_button("Download result", json.dumps(result, indent=2),
            file_name="video-check.json", mime="application/json")
        with st.expander("How this check works"):
            st.write(result["sampling"])
            for row in result["detectors"]:
                st.write(f"**{row['detector'].upper()}:** {row['preprocessing']}")
    st.divider()
    st.caption("First check may download about 764 MiB of model weights. CPU checks can take a few minutes. Keep this page open.")
