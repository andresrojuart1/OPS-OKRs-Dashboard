"""PDF parsing helpers — extract OKR data from uploaded PDF reports."""

import io
import json

import streamlit as st
from openai import OpenAI


def parse_okr_pdf_with_ai(pdf_file, sub_team: str, quarter: str, api_key: str) -> dict:
    """Extract text and images from PDF, then structure text with GPT-4o."""
    import pdfplumber
    from PIL import Image

    pdf_file.seek(0)
    text_content = ""
    images = []
    
    with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
        for page in pdf.pages:
            # Text
            extracted = page.extract_text()
            if extracted:
                text_content += extracted + "\n"
            
            # Images & Rects (potential charts)
            # Try to capture areas with image objects
            for img in page.images:
                try:
                    # Determine area
                    x0, top, x1, bottom = img["x0"], page.height - img["y1"], img["x1"], page.height - img["y0"]
                    width, height = x1 - x0, bottom - top
                    
                    if width > 100 and height > 100:
                        cropped = page.within_bbox((x0, top, x1, bottom)).to_image(resolution=200)
                        buf = io.BytesIO()
                        cropped.original.save(buf, format='PNG')
                        images.append({
                            "name": f"Chart_P{page.page_number}_{len(images)+1}.png",
                            "content": buf.getvalue(),
                            "type": "image/png"
                        })
                except Exception: continue
            
            # If no technical images found but it's a "Charts" page, capture regions
            if not images and any(kw in text_content.upper() for kw in ["CHART", "REVENUE", "GRAPH"]):
                try:
                    # Capturamos dos regiones: Mitad superior y Mitad inferior
                    areas = [
                        ("Top", (0, 0, page.width, page.height * 0.55)),
                        ("Bottom", (0, page.height * 0.45, page.width, page.height))
                    ]
                    for suffix, bbox in areas:
                        cropped = page.within_bbox(bbox).to_image(resolution=200)
                        buf = io.BytesIO()
                        cropped.original.save(buf, format='PNG')
                        images.append({
                            "name": f"Dashboard_{suffix}_P{page.page_number}.png",
                            "content": buf.getvalue(),
                            "type": "image/png"
                        })
                except Exception: continue

    client = OpenAI(api_key=api_key)

    prompt = f"""
Eres un experto en extraer datos de reportes de OKRs de Ops/Fintech.

Analiza el reporte del equipo {sub_team} para {quarter}.
Extrae la información en un JSON estricto.

SECCIONES ESPECIALES A BUSCAR:
- PAYINS: Extrae todos los comentarios narrativos numerados.
- PAYOUTS: Extrae todos los comentarios narrativos numerados.
- OKR Progress: Extrae títulos, valores actuales, targets y status.

TEXTO DEL REPORTE:
{text_content}

Retorna ÚNICAMENTE un JSON:
{{
  "objectives": [
    {{
      "title": "título del objective",
      "key_results": [
        {{
          "title": "título del KR",
          "current_value": 0.0,
          "target": 0.0,
          "unit": "% o $ o texto",
          "status": "IN PROGRESS|BLOCKED|NOT STARTED|MAINTAIN|COMPLETED",
          "progress_pct": 0
        }}
      ]
    }}
  ],
  "weekly_updates": [
    {{
      "section": "PAYINS",
      "content": "resumen de los puntos encontrados"
    }},
    {{
      "section": "PAYOUTS",
      "content": "resumen de los puntos encontrados"
    }}
  ]
}}

Reglas:
- Sé lo más fiel posible al texto original para los updates.
- Si hay varias notas bajo PAYINS, júntalas en un solo campo content con saltos de línea.
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        max_tokens=3000,
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    result = json.loads(raw)
    
    # Improved image split: Quadrants (Left/Right + Top/Bottom)
    if not images and any(kw in text_content.upper() for kw in ["REVENUE", "CHART", "PAYIN", "PAYOUT"]):
        with pdfplumber.open(io.BytesIO(pdf_file.read())) as pdf:
            for page in pdf.pages:
                if any(kw in (page.extract_text() or "").upper() for kw in ["REVENUE", "CHART"]):
                    # Dividimos en 4 cuadrantes para no fallar
                    mid_x = page.width / 2
                    mid_y = page.height / 2
                    quads = [
                        ("Top-Left", (0, 0, mid_x, mid_y * 1.1)),
                        ("Top-Right", (mid_x, 0, page.width, mid_y * 1.1)),
                        ("Bottom-Left", (0, mid_y * 0.9, mid_x, page.height)),
                        ("Bottom-Right", (mid_x, mid_y * 0.9, page.width, page.height))
                    ]
                    for name, bbox in quads:
                        try:
                            cropped = page.within_bbox(bbox).to_image(resolution=200)
                            buf = io.BytesIO()
                            cropped.original.save(buf, format='PNG')
                            images.append({
                                "name": f"{name}_P{page.page_number}.png",
                                "content": buf.getvalue(),
                                "type": "image/png"
                            })
                        except Exception: continue
    
    result["extracted_images"] = images
    return result


def render_pdf_preview_and_confirm(parsed_data: dict, sub_team: str, quarter: str) -> None:
    """Show parsed PDF data in an editable preview before saving."""
    from sheets import save_parsed_pdf_data

    st.markdown("### ✅ Review extracted data before saving")
    st.caption("Edit any incorrect values before confirming.")

    confirmed_data: dict = {"objectives": [], "weekly_updates": []}
    STATUS_OPTIONS = ["IN PROGRESS", "BLOCKED", "NOT STARTED", "MAINTAIN", "COMPLETED"]

    def _clean_float(val):
        if val is None or val == "": return 0.0
        if isinstance(val, (int, float)): return float(val)
        try:
            # Remove %, $, and other symbols, keep only digits and dots
            import re
            clean = re.sub(r'[^\d.]', '', str(val))
            return float(clean) if clean else 0.0
        except: return 0.0

    for obj_i, obj in enumerate(parsed_data.get("objectives", [])):
        st.markdown(f"**Objective: {obj['title']}**")

        confirmed_krs = []
        for kr_i, kr in enumerate(obj.get("key_results", [])):
            with st.expander(f"KR: {kr['title']}", expanded=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    kr_title = st.text_input(
                        "Title", value=str(kr.get("title", "")),
                        key=f"kr_title_{obj_i}_{kr_i}",
                    )
                with col2:
                    kr_current = st.number_input(
                        "Current", value=_clean_float(kr.get("current_value")),
                        key=f"kr_current_{obj_i}_{kr_i}",
                        format="%.2f"
                    )
                with col3:
                    kr_target = st.number_input(
                        "Target", value=_clean_float(kr.get("target")),
                        key=f"kr_target_{obj_i}_{kr_i}",
                        format="%.2f"
                    )

                status_val = kr.get("status") or "IN PROGRESS"
                if status_val not in STATUS_OPTIONS:
                    status_val = "IN PROGRESS"
                kr_status = st.selectbox(
                    "Status",
                    options=STATUS_OPTIONS,
                    index=STATUS_OPTIONS.index(status_val),
                    key=f"kr_status_{obj_i}_{kr_i}",
                )

                confirmed_krs.append({
                    "title":         kr_title,
                    "current_value": kr_current,
                    "target":        kr_target,
                    "status":        kr_status,
                    "unit":          kr.get("unit", ""),
                })

        confirmed_data["objectives"].append({
            "title":       obj["title"],
            "key_results": confirmed_krs,
        })

    if parsed_data.get("weekly_updates"):
        st.markdown("**Weekly narrative updates:**")
        for update in parsed_data["weekly_updates"]:
            st.info(f"**{update['section']}:** {update['content']}")
        confirmed_data["weekly_updates"] = parsed_data["weekly_updates"]

    extracted_imgs = parsed_data.get("extracted_images", [])
    if extracted_imgs:
        st.markdown(f"**Extracted Charts ({len(extracted_imgs)}):**")
        img_cols = st.columns(min(len(extracted_imgs), 3))
        for i, img in enumerate(extracted_imgs):
            with img_cols[i % 3]:
                st.image(img["content"], caption=img["name"])

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❌ Cancel Import", use_container_width=True, key="pdf_cancel"):
            st.session_state.pop("parsed_pdf_data", None)
            st.session_state.pop("show_pdf_import", None)
            st.rerun()
    with col2:
        if st.button("💾 Save to Dashboard", type="primary", use_container_width=True, key="pdf_save"):
            from sheets import upload_charts_to_drive, get_week_number
            email = st.session_state.get("user", {}).get("email", "unknown")
            
            # 1. Save OKR data & Weekly Note
            import_summary = save_parsed_pdf_data(confirmed_data, sub_team, quarter, email)
            
            # 2. Upload images and track their IDs
            if extracted_imgs:
                from collections import namedtuple
                MockFile = namedtuple("MockFile", ["name", "read", "type", "seek"])
                
                prepared_files = []
                for img in extracted_imgs:
                    def _read_content(c=img["content"]): return c
                    f = MockFile(img["name"], _read_content, img["type"], lambda x: None)
                    prepared_files.append(f)
                
                with st.spinner("Subiendo gráficas extraídas a Drive..."):
                    chart_ids = upload_charts_to_drive(prepared_files, sub_team, quarter, get_week_number(), email)
                    import_summary["chart_ids"] = chart_ids

            # 3. Store for Undo
            st.session_state["last_import_summary"] = import_summary
            st.session_state.pop("parsed_pdf_data", None)
            st.session_state.pop("show_pdf_import", None)
            st.cache_data.clear()
            st.success("✅ Data imported successfully!")
            st.rerun()
