import streamlit as st
import pandas as pd
from io import BytesIO
from parser_core import check_urls

st.set_page_config(page_title="Проверка отелей на 3D-тур", page_icon="🏨", layout="wide")

st.title("🏨 Проверка отелей на 3D-тур")
st.caption("Вставь ссылки на сайты отелей — скрипт проверит каждую и покажет, у кого нет 3D-тура.")

with st.sidebar:
    st.header("Настройки")
    only_no_tour = st.checkbox("Показать только отели БЕЗ тура", value=True)
    st.divider()
    st.markdown("**Как пользоваться:**")
    st.markdown("1. Вставь ссылки — по одной в строке\n2. Нажми «Проверить»\n3. Скачай CSV или Excel")

urls_text = st.text_area(
    "Ссылки на сайты отелей (по одной в строке):",
    height=200,
    placeholder="https://www.kdhotel.ru/\nhttps://garguli.ru\nhttps://filin76.ru/"
)

col_btn, _ = st.columns([1, 4])
with col_btn:
    start = st.button("🔍 Проверить", type="primary", use_container_width=True)

if start:
    urls = [u.strip() for u in urls_text.split('\n') if u.strip()]
    if not urls:
        st.warning("⚠️ Вставь хотя бы одну ссылку.")
    else:
        st.info(f"Проверяю {len(urls)} сайтов...")

        progress = st.progress(0.0, text="Начинаем проверку...")
        status = st.empty()

        def on_progress(i, total, res):
            progress.progress(i / total)
            status.text(f"[{i}/{total}] {res.get('url', '')}")

        with st.spinner("Идёт обход сайтов..."):
            results = check_urls(urls, on_progress=on_progress)

        progress.empty()
        status.empty()

        df = pd.DataFrame(results)

        # Порядок колонок
        order = ['url', 'has_tour', 'title', 'city', 'email', 'all_emails', 'phone', 'domain', 'status']
        cols = [c for c in order if c in df.columns]
        df = df[cols]

        if only_no_tour:
            df_filtered = df[df.get('has_tour') == 'Нет']
        else:
            df_filtered = df

        total_ok = len(df[df.get('has_tour') == 'Нет']) if 'has_tour' in df.columns else 0
        st.success(f"✅ Готово! Всего проверено: {len(df)}. Без тура: {total_ok}.")

        st.dataframe(df_filtered, use_container_width=True, hide_index=True)

        # CSV — с точкой с запятой и BOM, чтобы Excel/LibreOffice открывали сразу
        csv_bytes = df_filtered.to_csv(index=False, sep=';', decimal=',').encode('utf-8-sig')

        # Excel — родной формат .xlsx
        excel_buffer = BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df_filtered.to_excel(writer, index=False, sheet_name='Отели')
        excel_bytes = excel_buffer.getvalue()

        st.markdown("### 📥 Скачать результат")

        col1, col2, _ = st.columns([1, 1, 2])
        with col1:
            st.download_button(
                "📊 Excel",
                data=excel_bytes,
                file_name="no_tour.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary",
                use_container_width=True
            )
        with col2:
            st.download_button(
                "📄 CSV",
                data=csv_bytes,
                file_name="no_tour.csv",
                mime="text/csv",
                type="primary",
                use_container_width=True
            )