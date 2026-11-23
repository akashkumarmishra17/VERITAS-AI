"""
VERITAS AI - High-Fidelity Screenshot Capture Pipeline via Chrome DevTools Protocol.
Captures genuine, full-color, fully-rendered browser screenshots of:
1. Dashboard View
2. New Analysis - Upload & Image Specifications
3. Forensic Verdict & ELA Analysis (Side-by-side Original vs ELA)
4. Splicing Localization Heatmap & Bounding Boxes Overlay
5. Forensic Radar & Feature Importances
6. Analysis History Log
7. Model Performance Benchmarks (Confusion Matrix & ROC Curve)
8. About & Forensic Methodology
"""

import os
import sys
import time
import json
import base64
import asyncio
import subprocess
import urllib.request
import websockets
from PIL import Image

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "assets", "screenshots"))
EDGE_PATH = os.environ.get("EDGE_PATH", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe")
PYTHON_PATH = sys.executable
APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))


async def eval_js(ws, expr, req_id=1):
    await ws.send(json.dumps({
        "id": req_id,
        "method": "Runtime.evaluate",
        "params": {"expression": expr, "returnByValue": True}
    }))
    while True:
        raw = await ws.recv()
        msg = json.loads(raw)
        if msg.get("id") == req_id:
            return msg.get("result", {}).get("result", {}).get("value")


async def take_screenshot(ws, output_path, req_id=99):
    await ws.send(json.dumps({
        "id": req_id,
        "method": "Page.captureScreenshot",
        "params": {"format": "png"}
    }))
    while True:
        raw = await ws.recv()
        msg = json.loads(raw)
        if msg.get("id") == req_id:
            img_bytes = base64.b64decode(msg["result"]["data"])
            with open(output_path, "wb") as f:
                f.write(img_bytes)
            print(f"Captured: {output_path} ({len(img_bytes)} bytes)")
            return img_bytes


async def wait_for_selector(ws, selector, timeout=20):
    start = time.time()
    while time.time() - start < timeout:
        found = await eval_js(ws, f"document.querySelector('{selector}') !== null")
        if found:
            return True
        await asyncio.sleep(0.5)
    return False


async def capture_all():
    os.makedirs(ASSETS_DIR, exist_ok=True)
    port = 8535
    cdp_port = 9255

    # 1. Start Edge with CDP
    b_proc = subprocess.Popen([
        EDGE_PATH,
        "--headless=new",
        f"--remote-debugging-port={cdp_port}",
        "--disable-gpu",
        "--hide-scrollbars",
        "about:blank"
    ])
    time.sleep(2)

    # 2. Start Streamlit
    env = os.environ.copy()
    s_proc = subprocess.Popen([
        PYTHON_PATH, "-m", "streamlit", "run", APP_PATH,
        f"--server.port={port}",
        "--server.address=127.0.0.1",
        "--server.headless=true",
        "--browser.gatherUsageStats=false"
    ], env=env)
    time.sleep(5)

    try:
        req = urllib.request.Request(f"http://127.0.0.1:{cdp_port}/json/new", method="PUT")
        resp = urllib.request.urlopen(req).read()
        ws_url = json.loads(resp)["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=30_000_000) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
            await ws.send(json.dumps({
                "id": 2,
                "method": "Emulation.setDeviceMetricsOverride",
                "params": {"width": 1440, "height": 1050, "deviceScaleFactor": 1, "mobile": False}
            }))

            # Navigate to Dashboard
            print("\nNavigating to Dashboard...")
            await ws.send(json.dumps({"id": 3, "method": "Page.navigate", "params": {"url": f"http://127.0.0.1:{port}"}}))
            await wait_for_selector(ws, "h1")
            await asyncio.sleep(4)  # Let CSS and metric cards settle
            await take_screenshot(ws, os.path.join(ASSETS_DIR, "01_dashboard.png"))

            # Navigate to New Analysis via Sidebar radio
            print("\nNavigating to New Analysis...")
            await eval_js(ws, """
                const radios = Array.from(document.querySelectorAll('label'));
                const newAnalysis = radios.find(el => el.innerText.includes('New Analysis'));
                if (newAnalysis) newAnalysis.click();
            """)
            await asyncio.sleep(3)
            await wait_for_selector(ws, "h1")
            await take_screenshot(ws, os.path.join(ASSETS_DIR, "02_new_analysis_upload.png"))

            # Return to Dashboard and click 'Analyze Spliced Sample' to trigger full analysis
            print("\nTriggering Spliced Sample Examination...")
            await eval_js(ws, """
                const radios = Array.from(document.querySelectorAll('label'));
                const dash = radios.find(el => el.innerText.includes('Dashboard'));
                if (dash) dash.click();
            """)
            await asyncio.sleep(3)
            
            # Click 'Analyze Spliced Sample' button
            await eval_js(ws, """
                const buttons = Array.from(document.querySelectorAll('button'));
                const btn = buttons.find(b => b.innerText.includes('Analyze Spliced Sample'));
                if (btn) btn.click();
            """)
            await asyncio.sleep(3)

            # Now we are on New Analysis with preloaded sample! Click 'Execute Forensic Inspection Pipeline'
            await eval_js(ws, """
                const buttons = Array.from(document.querySelectorAll('button'));
                const btn = buttons.find(b => b.innerText.includes('Execute Forensic Inspection Pipeline'));
                if (btn) btn.click();
            """)
            print("Running forensic pipeline (ELA, noise, copy-move, ML)...")
            await asyncio.sleep(8)  # Let pipeline run and render results

            # Capture Verdict & ELA View
            print("Capturing Verdict and ELA analysis...")
            await take_screenshot(ws, os.path.join(ASSETS_DIR, "03_verdict_and_ela.png"))

            # Scroll down to capture Localization Overlay and Bounding Boxes
            await eval_js(ws, "window.scrollBy(0, 500)")
            await asyncio.sleep(1)
            await take_screenshot(ws, os.path.join(ASSETS_DIR, "04_tamper_localization_overlay.png"))

            # Switch to Tab 2: 'Forensic Radar & Importances'
            print("Switching to Forensic Radar tab...")
            await eval_js(ws, """
                const tabs = Array.from(document.querySelectorAll('[data-baseweb="tab"]'));
                const radarTab = tabs.find(t => t.innerText.includes('Radar'));
                if (radarTab) radarTab.click();
            """)
            await asyncio.sleep(2)
            await take_screenshot(ws, os.path.join(ASSETS_DIR, "05_forensic_radar_and_features.png"))

            # Scroll to Action Buttons (Save DB & PDF Download)
            print("Capturing PDF Report & Database Save action area...")
            await eval_js(ws, "window.scrollBy(0, 450)")
            await asyncio.sleep(1)
            await take_screenshot(ws, os.path.join(ASSETS_DIR, "06_pdf_report_and_save.png"))

            # Navigate to Model Performance
            print("\nNavigating to Model Performance...")
            await eval_js(ws, """
                window.scrollTo(0, 0);
                const radios = Array.from(document.querySelectorAll('label'));
                const perf = radios.find(el => el.innerText.includes('Model Performance'));
                if (perf) perf.click();
            """)
            await asyncio.sleep(4)
            await take_screenshot(ws, os.path.join(ASSETS_DIR, "07_model_performance_benchmarks.png"))

            # Navigate to Analysis History
            print("\nNavigating to Analysis History...")
            await eval_js(ws, """
                const radios = Array.from(document.querySelectorAll('label'));
                const hist = radios.find(el => el.innerText.includes('Analysis History'));
                if (hist) hist.click();
            """)
            await asyncio.sleep(4)
            await take_screenshot(ws, os.path.join(ASSETS_DIR, "08_analysis_history_log.png"))

            # Navigate to About & Methodology
            print("\nNavigating to About & Methodology...")
            await eval_js(ws, """
                const radios = Array.from(document.querySelectorAll('label'));
                const about = radios.find(el => el.innerText.includes('About & Methodology'));
                if (about) about.click();
            """)
            await asyncio.sleep(3)
            await take_screenshot(ws, os.path.join(ASSETS_DIR, "09_about_methodology.png"))

        print("\nAll genuine screenshots captured successfully!")

    finally:
        b_proc.terminate()
        s_proc.terminate()
        try:
            b_proc.wait(timeout=3)
            s_proc.wait(timeout=3)
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(capture_all())
