import streamlit as st
import subprocess
import json
import os
import tempfile

st.set_page_config(page_title="Newman Web Dashboard", layout="wide")

st.title("Newman Web Dashboard 🚀")
st.markdown("Upload your **Postman Collection** (and optionally an **Environment** file) to run tests directly from the browser using Newman!")

col1, col2 = st.columns(2)

with col1:
    collection_file = st.file_uploader("Upload Postman Collection (.json)", type=["json"], key="collection")
with col2:
    env_file = st.file_uploader("Upload Environment File (.json) - Optional", type=["json"], key="env")

if st.button("Run Tests with Newman", type="primary"):
    if not collection_file:
        st.error("Please upload a Postman Collection to run.")
    else:
        with st.spinner("Running Newman..."):
            with tempfile.TemporaryDirectory() as tmpdir:
                # Save collection
                coll_path = os.path.join(tmpdir, "collection.json")
                with open(coll_path, "wb") as f:
                    f.write(collection_file.getvalue())
                
                # Build command
                report_path = os.path.join(tmpdir, "report.json")
                cmd = ["newman", "run", coll_path, "--reporters", "cli,json", "--reporter-json-export", report_path]
                
                # Save env if provided
                if env_file:
                    env_path = os.path.join(tmpdir, "env.json")
                    with open(env_path, "wb") as f:
                        f.write(env_file.getvalue())
                    cmd.extend(["-e", env_path])

                # Execute
                try:
                    process = subprocess.run(cmd, capture_output=True, text=True)
                    stdout = process.stdout
                    stderr = process.stderr
                    
                    st.success("Execution Complete!")
                    
                    # Try to parse the report
                    if os.path.exists(report_path):
                        with open(report_path, "r", encoding="utf-8") as rf:
                            report_data = json.load(rf)
                            
                            run_stats = report_data.get("run", {}).get("stats", {})
                            
                            st.subheader("📊 Test Summary")
                            m1, m2, m3, m4 = st.columns(4)
                            
                            reqs = run_stats.get("requests", {})
                            m1.metric("Requests Executed", reqs.get("total", 0))
                            
                            assertions = run_stats.get("assertions", {})
                            passed = assertions.get("total", 0) - assertions.get("failed", 0)
                            m2.metric("Assertions Passed", passed)
                            m3.metric("Assertions Failed", assertions.get("failed", 0))
                            
                            timing = report_data.get("run", {}).get("timings", {})
                            m4.metric("Total Duration", f"{timing.get('completed', 0) - timing.get('started', 0)} ms")
                            
                    else:
                        st.warning("Could not find the JSON report file.")

                    with st.expander("Show Raw Newman CLI Output", expanded=True):
                        st.code(stdout, language="bash")
                        if stderr:
                            st.code(stderr, language="bash")

                except Exception as e:
                    st.error(f"Failed to execute Newman: {e}")
