"""
VERITAS AI - UI Components and Interactive Visualization Helpers.
"""

from typing import Dict, Any, List, Optional
import streamlit as st
import plotly.graph_objects as go


def render_metric_card(title: str, value: str, subtext: str = ""):
    """Renders a styled metric card."""
    html = f"""
    <div class="veritas-card metric-box">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{subtext}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_verdict_banner(
    prediction: str,
    confidence: Optional[float],
    manipulated_probability: Optional[float],
    model_version: str,
    decision_zone: str,
    notes: str,
):
    """Renders the main forensic verdict banner with glowing border and details."""
    if prediction == "Authentic":
        css_class = "verdict-banner-authentic"
        icon = "🛡️"
        color_hex = "#10b981"
        verdict_text = "AUTHENTIC PHOTOGRAPH"
    elif prediction == "Potentially Manipulated":
        css_class = "verdict-banner-manipulated"
        icon = "⚠️"
        color_hex = "#ef4444"
        verdict_text = "POTENTIALLY MANIPULATED"
    elif prediction == "MODEL NOT TRAINED":
        css_class = "verdict-banner-untrained"
        icon = "⚙️"
        color_hex = "#94a3b8"
        verdict_text = "MODEL NOT TRAINED"
    else:
        css_class = "verdict-banner-inconclusive"
        icon = "🔍"
        color_hex = "#f59e0b"
        verdict_text = "INCONCLUSIVE / AMBIGUOUS"

    manip_str = f"{manipulated_probability * 100:.1f}%" if manipulated_probability is not None else "N/A"
    conf_str = f"{confidence * 100:.1f}%" if confidence is not None else "N/A"

    html = f"""
    <div class="{css_class}">
        <div style="font-size: 2.2rem; margin-bottom: 6px;">{icon}</div>
        <div style="font-size: 1.8rem; font-weight: 800; color: {color_hex}; letter-spacing: -0.01em;">
            {verdict_text}
        </div>
        <div style="font-size: 0.95rem; color: #94a3b8; margin-top: 6px;">
            Manipulated Probability: <b style="color: #f8fafc;">{manip_str}</b> &nbsp;|&nbsp;
            Decision Confidence: <b style="color: #f8fafc;">{conf_str}</b> &nbsp;|&nbsp;
            Zone: <b style="color: #f8fafc;">{decision_zone}</b>
        </div>
        <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 12px; max-width: 800px; margin-left: auto; margin-right: auto; line-height: 1.5; background: rgba(0,0,0,0.25); padding: 10px 16px; border-radius: 8px;">
            {notes}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def plot_forensic_radar(scores: Dict[str, float]) -> go.Figure:
    """Renders a modern dark-themed radar chart of forensic module scores."""
    categories = list(scores.keys())
    values = [min(max(v, 0.0), 1.0) for v in scores.values()]

    # Close the radar loop
    categories.append(categories[0])
    values.append(values[0])

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        fillcolor='rgba(2, 132, 199, 0.25)',
        line=dict(color='#38bdf8', width=2),
        name='Forensic Risk Vector'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1.0],
                showticklabels=True,
                gridcolor='rgba(255, 255, 255, 0.1)',
                color='#94a3b8',
            ),
            angularaxis=dict(
                gridcolor='rgba(255, 255, 255, 0.1)',
                color='#e2e8f0',
                tickfont=dict(size=11, color='#e2e8f0')
            ),
            bgcolor='rgba(15, 23, 42, 0.6)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=30, b=30),
        height=320,
        showlegend=False
    )
    return fig


def plot_feature_importances(importances: Dict[str, float], top_n: int = 10) -> go.Figure:
    """Renders horizontal bar chart of top Random Forest feature weights."""
    sorted_items = sorted(importances.items(), key=lambda x: x[1], reverse=True)[:top_n]
    sorted_items.reverse()  # For horizontal bar, top item at top

    labels = [k.replace('_', ' ').title() for k, _ in sorted_items]
    values = [v for _, v in sorted_items]

    fig = go.Figure(go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker=dict(
            color=values,
            colorscale=[[0, '#0284c7'], [1, '#38bdf8']],
        )
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=20, t=20, b=20),
        height=320,
        xaxis=dict(
            title="Gini Importance Weight",
            color='#94a3b8',
            gridcolor='rgba(255, 255, 255, 0.08)'
        ),
        yaxis=dict(color='#e2e8f0'),
    )
    return fig


def plot_confusion_matrix(cm_data: Dict[str, Any]) -> go.Figure:
    """Plots interactive confusion matrix heatmap."""
    matrix = cm_data.get("matrix", [[0, 0], [0, 0]])
    labels = ["Authentic", "Manipulated"]

    z = matrix
    annotations = []
    for i, row in enumerate(matrix):
        for j, val in enumerate(row):
            annotations.append(dict(
                x=labels[j],
                y=labels[i],
                text=str(val),
                showarrow=False,
                font=dict(color="#ffffff", size=18, family="Inter")
            ))

    fig = go.Figure(data=go.Heatmap(
        z=z,
        x=labels,
        y=labels,
        colorscale=[[0, '#0f172a'], [0.5, '#0284c7'], [1, '#38bdf8']],
        showscale=False
    ))

    fig.update_layout(
        annotations=annotations,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="Predicted Class", color="#94a3b8"),
        yaxis=dict(title="True Ground Truth Class", color="#94a3b8", autorange="reversed"),
        margin=dict(l=40, r=40, t=30, b=40),
        height=320,
    )
    return fig


def plot_roc_curve(roc_points: List[Dict[str, float]], auc_score: float) -> go.Figure:
    """Plots interactive ROC curve."""
    fpr = [p["fpr"] for p in roc_points]
    tpr = [p["tpr"] for p in roc_points]

    fig = go.Figure()
    # Random guess baseline
    fig.add_trace(go.Scatter(
        x=[0, 1], y=[0, 1],
        mode='lines',
        line=dict(color='#64748b', dash='dash'),
        name='Random Baseline (AUC = 0.50)'
    ))
    # Veritas Model ROC
    fig.add_trace(go.Scatter(
        x=fpr, y=tpr,
        mode='lines+markers',
        line=dict(color='#38bdf8', width=3),
        marker=dict(size=4),
        name=f'Random Forest (AUC = {auc_score:.3f})'
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(title="False Positive Rate", color="#94a3b8", gridcolor='rgba(255, 255, 255, 0.08)'),
        yaxis=dict(title="True Positive Rate (Recall)", color="#94a3b8", gridcolor='rgba(255, 255, 255, 0.08)'),
        legend=dict(x=0.45, y=0.15, font=dict(color="#cbd5e1")),
        margin=dict(l=40, r=40, t=30, b=40),
        height=320,
    )
    return fig
