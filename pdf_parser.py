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
            
            # Images
            for img_obj in page.images:
                try:
                    # Crop and capture image
                    bbox = (img_obj["x0"], page.height - img_obj["y1"], img_obj["x1"], page.height - img_obj["y0"])
                    if (img_obj["x1"] - img_obj["x0"]) < 50: continue # Skip small icons
                    
                    cropped = page.within_bbox(bbox).to_image(resolution=200)
                    buf = io.BytesIO()
                    cropped.original.save(buf, format='PNG')
                    images.append({
                        "name": f"Chart_P{page.page_number}_{img_obj['index']}.png",
                        "content": buf.getvalue(),
                        "type": "image/png"
                    })
                except Exception:
                    continue

    client = OpenAI(api_key=api_key)

    prompt = f"""
Eres un asistente que extrae datos estructurados de reportes de OKRs.

Analiza el siguiente texto de un reporte OKR del equipo {sub_team} para {quarter}
y extrae la información en formato JSON estricto.

TEXTO DEL REPORTE:
{text_content}

Retorna ÚNICAMENTE un JSON válido con esta estructura exacta, sin texto adicional:
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
      "section": "nombre de sección (ej: PAYINS, PAYOUTS)",
      "content": "texto del update narrativo"
    }}
  ]
}}

Reglas:
- Si el progreso está expresado como porcentaje, úsalo directamente en progress_pct
- Si está expresado como valor actual vs target, calcula el porcentaje
- Si el status es MAINTAIN y hay un porcentaje como 100%, úsalo
- Los weekly_updates son los párrafos narrativos numerados del reporte
- Si no encuentras algún campo, usa null
"""

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=2000,
        temperature=0,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    result = json.loads(raw.strip())
    result["extracted_images"] = images
    return result


def render_pdf_preview_and_confirm(parsed_data: dict, sub_team: str, quarter: str) -> None:
    """Show parsed PDF data in an editable preview before saving."""
    from sheets import save_parsed_pdf_data

    st.markdown("### ✅ Review extracted data before saving")
    st.caption("Edit any incorrect values before confirming.")

    confirmed_data: dict = {"objectives": [], "weekly_updates": []}
    STATUS_OPTIONS = ["IN PROGRESS", "BLOCKED", "NOT STARTED", "MAINTAIN", "COMPLETED"]

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
                        "Current", value=float(kr.get("current_value") or 0),
                        key=f"kr_current_{obj_i}_{kr_i}",
                    )
                with col3:
                    kr_target = st.number_input(
                        "Target", value=float(kr.get("target") or 0),
                        key=f"kr_target_{obj_i}_{kr_i}",
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
            from sheets import upload_charts_to_drive
            email = st.session_state.get("user", {}).get("email", "unknown")
            
            # Save data and get IDs for Undo
            import_summary = save_parsed_pdf_data(confirmed_data, sub_team, quarter, email)
            
            # Upload images if any
            if extracted_imgs:
                from collections import namedtuple
                MockFile = namedtuple("MockFile", ["name", "read", "type", "seek"])
                
                prepared_files = []
                for img in extracted_imgs:
                    f = MockFile(img["name"], lambda: img["content"], img["type"], lambda x: None)
                    prepared_files.append(f)
                
                with st.spinner("Subiendo gráficas extraídas a Drive..."):
                    upload_charts_to_drive(prepared_files, sub_team, quarter, get_week_number(), email)

            st.session_state["last_import_summary"] = import_summary
            st.session_state.pop("parsed_pdf_data", None)
            st.session_state.pop("show_pdf_import", None)
            st.cache_data.clear()
            st.success("✅ Data imported successfully!")
            st.rerun()
