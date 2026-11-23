"""
VERITAS AI - Analysis History Audit Log.
Displays local SQLite forensic history records, filtering, record details,
CSV export, and deletion.
"""

import streamlit as st
import pandas as pd
from src.database.db_manager import ForensicDatabaseManager


def render_history_page():
    st.markdown("""
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 2.1rem; margin-bottom: 4px;">Forensic Audit & Examination History</h1>
            <p style="color: #94a3b8; font-size: 0.95rem; margin: 0;">
                Locally persisted forensic examination records stored in SQLite database.
            </p>
        </div>
    """, unsafe_allow_html=True)

    db = ForensicDatabaseManager()

    # Search & Filter controls
    f_c1, f_c2, f_c3 = st.columns([3, 2, 1])
    with f_c1:
        search_query = st.text_input("🔍 Search by Filename or UUID", placeholder="Type filename or ID...")
    with f_c2:
        verdict_filter = st.selectbox("Filter by Verdict", ["ALL", "Authentic", "Potentially Manipulated", "Inconclusive"])
    with f_c3:
        st.write("")
        st.write("")
        refresh_btn = st.button("Refresh", use_container_width=True)

    records = db.get_records(limit=200, search_query=search_query, verdict_filter=verdict_filter)

    if not records:
        st.markdown("""
            <div class="veritas-card" style="text-align: center; padding: 40px;">
                <div style="font-size: 2.5rem; margin-bottom: 10px;">📜</div>
                <div style="font-size: 1.1rem; font-weight: 600; color: #f8fafc;">No Forensic Records Found</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 6px;">
                    No past analyses match your search criteria. Execute an analysis to start building an audit trail.
                </div>
            </div>
        """, unsafe_allow_html=True)
        return

    # Aggregate stats on current view
    st.caption(f"Displaying **{len(records)}** examination record(s).")

    # Table preview
    df_data = []
    for r in records:
        df_data.append({
            "Rec ID": r["id"],
            "UUID": r["analysis_uuid"],
            "Timestamp": r["timestamp"],
            "Filename": r["filename"],
            "Dimensions": r["dimensions"],
            "Verdict": r["prediction"],
            "Confidence": f"{r['confidence_score'] * 100:.1f}%" if r["confidence_score"] else "N/A",
            "Copy-Move": "DETECTED" if r["copy_move_detected"] else "Clean",
            "Spliced Zones": r["num_suspicious_zones"],
            "Metadata Risk": r["metadata_risk"],
            "Model": r["model_version"],
        })

    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Detailed Record Inspection & Deletion
    st.markdown("### Record Detail & Actions")
    selected_id = st.selectbox(
        "Select Record ID to inspect or manage:",
        [r["id"] for r in records],
        format_func=lambda x: f"Record #{x} - {next((r['filename'] + ' [' + r['prediction'] + ']') for r in records if r['id'] == x)}"
    )

    if selected_id:
        rec = db.get_record_by_id(selected_id)
        if rec:
            with st.expander(f"🔍 Detailed Audit Record #{rec['id']} - {rec['filename']}", expanded=True):
                r_c1, r_c2, r_c3 = st.columns(3)
                with r_c1:
                    st.write(f"**UUID:** `{rec['analysis_uuid']}`")
                    st.write(f"**Timestamp:** {rec['timestamp']}")
                    st.write(f"**Dimensions:** {rec['dimensions']}")
                    st.write(f"**File Size:** {rec['file_size_kb']} KB")
                with r_c2:
                    st.write(f"**Verdict:** `{rec['prediction']}`")
                    st.write(f"**Confidence:** {rec['confidence_score'] * 100:.1f}%" if rec['confidence_score'] else "**Confidence:** N/A")
                    st.write(f"**Manipulated Probability:** {rec['manipulated_probability'] * 100:.1f}%" if rec['manipulated_probability'] else "**Manipulated Probability:** N/A")
                    st.write(f"**Model Architecture:** {rec['model_version']}")
                with r_c3:
                    st.write(f"**ELA Mean Error:** {rec['ela_mean_error']}")
                    st.write(f"**Noise Inconsistency:** {rec['noise_inconsistency_score']}")
                    st.write(f"**Copy-Move Found:** {'YES' if rec['copy_move_detected'] else 'NO'}")
                    st.write(f"**Splicing Zones:** {rec['num_suspicious_zones']}")

                st.markdown("###### Forensic Findings Notes:")
                st.info(rec["notes_summary"] or "No notes provided.")

                # Action: Delete individual record
                if st.button(f"🗑️ Delete Record #{rec['id']}", key=f"del_{rec['id']}"):
                    db.delete_record(rec["id"])
                    st.success(f"Record #{rec['id']} deleted from database.")
                    st.rerun()

    st.markdown("<br/>", unsafe_allow_html=True)

    # Export & Database Purge actions
    b_col1, b_col2 = st.columns([1, 1])
    with b_col1:
        csv_bytes = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Export History Log to CSV",
            data=csv_bytes,
            file_name="veritas_forensic_history.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with b_col2:
        with st.expander("⚠️ Database Purge Options"):
            st.warning("Permanently removes all examination audit records from the local SQLite database.")
            confirm = st.checkbox("I understand this action is irreversible.")
            if confirm and st.button("Purge All History Records", type="primary"):
                deleted_count = db.purge_history()
                st.success(f"Purged {deleted_count} records from database.")
                st.rerun()
