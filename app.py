import hashlib
import logging

import streamlit as st
from sqlalchemy.exc import SQLAlchemyError

from database import (
    check_database,
    get_database_overview,
    list_database_records,
    list_recent_analyses,
    save_analysis,
)
from detector import analyze_text, extract_document


logger = logging.getLogger(__name__)


# Business-facing labels shown for the three rule-based score bands.
STATUS_TEXT = {
    "high": {
        "label": "Indikasi tinggi",
        "description": "Sejumlah pola penulisan terdeteksi. Tinjau temuan sebelum mengambil keputusan.",
    },
    "mixed": {
        "label": "Perlu ditinjau",
        "description": "Beberapa pola ditemukan, tetapi hasil belum menunjukkan kecenderungan yang kuat.",
    },
    "low": {
        "label": "Indikasi rendah",
        "description": "Sedikit pola yang diperiksa terdeteksi pada dokumen ini.",
    },
}


def apply_styles():
    """Apply the shared visual style for the dashboard."""
    st.markdown(
        """
        <style>
        :root {
            --ink: #172b4d;
            --muted: #64748b;
            --brand: #3157d5;
            --line: #e5eaf2;
            --surface: #ffffff;
            --canvas: #f5f7fb;
        }
        .stApp { background: var(--canvas); color: var(--ink); }
        [data-testid="stHeader"] { background: rgba(245, 247, 251, .92); }
        [data-testid="stSidebar"] {
            background: var(--surface);
            border-right: 1px solid var(--line);
        }
        [data-testid="stSidebar"] > div:first-child { padding-top: 1.5rem; }
        .block-container { max-width: 1180px; padding-top: 2rem; padding-bottom: 4rem; }
        .brand-lockup { display:flex; align-items:center; gap:.7rem; margin-bottom:2rem; }
        .brand-mark {
            width:2.5rem; height:2.5rem; border-radius:.8rem;
            display:flex; align-items:center; justify-content:center;
            background:#e9efff; color:var(--brand); font-weight:800; font-size:1.05rem;
        }
        .brand-name { color:var(--ink); font-size:1.03rem; font-weight:750; line-height:1.2; }
        .brand-caption { color:var(--muted); font-size:.78rem; margin-top:.2rem; }
        .eyebrow {
            color:var(--brand); font-size:.76rem; font-weight:750;
            letter-spacing:.1em; text-transform:uppercase; margin-bottom:.45rem;
        }
        .hero-title {
            color:var(--ink); font-size:2.1rem; line-height:1.2;
            letter-spacing:-.035em; font-weight:760; margin:0;
        }
        .hero-copy { color:var(--muted); font-size:1rem; margin-top:.65rem; max-width:760px; }
        .section-title { color:var(--ink); font-size:1.15rem; font-weight:720; margin:.2rem 0 .3rem; }
        .section-copy { color:var(--muted); font-size:.9rem; margin-bottom:1rem; }
        .upload-panel, .result-panel, .info-panel {
            background:var(--surface); border:1px solid var(--line);
            border-radius:1rem; padding:1.35rem 1.45rem;
            box-shadow:0 6px 20px rgba(27, 45, 80, .035);
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background:var(--surface); border-color:var(--line); border-radius:1rem;
        }
        .upload-hint { color:var(--muted); font-size:.82rem; margin-top:.45rem; }
        .privacy-note {
            color:#52637d; font-size:.82rem; line-height:1.5;
            background:#eef4ff; border:1px solid #dce7ff;
            border-radius:.75rem; padding:.85rem 1rem; margin-top:1rem;
        }
        .status-pill {
            display:inline-flex; align-items:center; gap:.45rem;
            border-radius:99px; padding:.38rem .75rem;
            font-size:.8rem; font-weight:700; margin-bottom:.6rem;
        }
        .pill-high { color:#a83232; background:#fff0ee; }
        .pill-mixed { color:#946200; background:#fff6dc; }
        .pill-low { color:#187448; background:#e9f8ef; }
        .result-heading { color:var(--ink); font-size:1.35rem; font-weight:740; margin:0 0 .35rem; }
        .result-copy { color:var(--muted); font-size:.9rem; margin:0; }
        .metric-card {
            border:1px solid var(--line); background:var(--surface);
            border-radius:.9rem; padding:.45rem .7rem;
        }
        .step-card {
            height:100%; padding:1rem; border:1px solid var(--line);
            border-radius:.85rem; background:var(--surface);
        }
        .step-number {
            width:1.7rem; height:1.7rem; border-radius:50%;
            display:flex; justify-content:center; align-items:center;
            background:#edf2ff; color:var(--brand); font-size:.8rem; font-weight:750;
            margin-bottom:.7rem;
        }
        .step-title { color:var(--ink); font-weight:700; font-size:.9rem; margin-bottom:.25rem; }
        .step-copy { color:var(--muted); font-size:.82rem; line-height:1.5; }
        div[data-testid="stMetric"] {
            background:var(--surface); border:1px solid var(--line);
            padding:1rem 1.05rem; border-radius:.85rem;
            box-shadow:0 4px 16px rgba(27, 45, 80, .025);
        }
        div[data-testid="stMetricLabel"] p { color:var(--muted); font-size:.82rem; }
        div[data-testid="stMetricValue"] { color:var(--ink); font-weight:750; }
        div[data-testid="stFileUploader"] section {
            border:1px dashed #aebde0; border-radius:.8rem; background:#fafbff;
        }
        div[data-testid="stExpander"] {
            background:var(--surface); border:1px solid var(--line); border-radius:.8rem;
        }
        .footer-note { color:#77849a; font-size:.78rem; text-align:center; margin-top:2rem; }
        @media (max-width: 700px) {
            .block-container { padding:1.2rem 1rem 3rem; }
            .hero-title { font-size:1.7rem; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar():
    """Render the product identity and local-demo usage warning."""
    with st.sidebar:
        st.markdown(
            """
            <div class="brand-lockup">
                <div class="brand-mark">V</div>
                <div>
                    <div class="brand-name">Veritas Review</div>
                    <div class="brand-caption">Document intelligence</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("**WORKSPACE**")
        st.markdown("📄 &nbsp; Analisis dokumen")
        st.divider()
        st.markdown("**Tentang analisis**")
        st.caption(
            "Pemeriksaan berbasis pola teks untuk membantu peninjauan dokumen. "
            "Hasil bukan keputusan otomatis."
        )
        st.warning(
            "Demo tanpa login: jangan publikasikan ke internet atau unggah dokumen sensitif."
        )


def show_findings(result, metadata):
    """Display each indicator and source metadata in separate expanders."""
    with st.expander("Karakter khusus", expanded=False):
        st.write(
            f"Skor indikator: **{result['special_score']}/25** "
            "(5 poin per kemunculan, maksimum 25)."
        )
        for label, count in result["special_counts"].items():
            st.write(f"- {label}: **{count}**")

    with st.expander("Frasa transisi yang ditemukan", expanded=False):
        st.write(
            f"Skor indikator: **{result['phrase_score']}/30** "
            "(5 poin per kemunculan, maksimum 30)."
        )
        if result["phrase_counts"]:
            for phrase, count in result["phrase_counts"].items():
                st.write(f"- “{phrase}”: **{count} kali**")
        else:
            st.write("Tidak ditemukan frasa dari daftar pemeriksaan.")

    with st.expander("Pola panjang kalimat", expanded=False):
        if result["sentence_stdev"] is None:
            st.write(
                f"Belum cukup kalimat untuk menghitung standar deviasi "
                f"({result['sentence_count']} kalimat ditemukan)."
            )
        else:
            st.write(
                f"Standar deviasi: **{result['sentence_stdev']:.2f} kata** "
                f"dari {result['sentence_count']} kalimat."
            )
        st.write(f"Skor indikator: **{result['burstiness_score']}/30**.")

    with st.expander("Pola daftar berpoin", expanded=False):
        st.write(
            f"Skor indikator: **{result['list_score']}/15** "
            "(5 poin per pola, maksimum 15)."
        )
        if result["list_matches"]:
            for match in result["list_matches"]:
                st.write(f"- `{match.strip()}`")
        else:
            st.write("Tidak ditemukan pola daftar dengan judul dan titik dua.")

    with st.expander("Metadata dokumen", expanded=False):
        st.write(f"- **Creator:** {metadata['Creator']}")
        st.write(f"- **Producer:** {metadata['Producer']}")


def show_empty_state():
    """Explain the upload workflow before a document is selected."""
    st.markdown('<div class="section-title">Mulai dalam tiga langkah</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Tidak perlu file pembanding atau dataset. '
        "Unggah dokumen untuk mendapatkan ringkasan pemeriksaan.</div>",
        unsafe_allow_html=True,
    )
    columns = st.columns(3)
    steps = (
        ("Unggah dokumen", "Pilih satu PDF atau dokumen Word (.docx)."),
        ("Analisis otomatis", "Sistem memeriksa empat kelompok pola tekstual."),
        ("Tinjau temuan", "Baca skor ringkasan dan rincian setiap indikator."),
    )
    for column, (title, copy), number in zip(columns, steps, range(1, 4)):
        with column:
            st.markdown(
                f'<div class="step-card"><div class="step-number">{number}</div>'
                f'<div class="step-title">{title}</div>'
                f'<div class="step-copy">{copy}</div></div>',
                unsafe_allow_html=True,
            )
    st.markdown(
        '<div class="privacy-note"><strong>Catatan penggunaan:</strong> '
        "Skor adalah indikasi berbasis aturan, bukan probabilitas terkalibrasi "
        "atau bukti kepengarangan. Selalu tinjau dokumen dan konteksnya secara manual."
        "</div>",
        unsafe_allow_html=True,
    )


def analyze_upload(uploaded_file):
    """Extract and score one upload, then save only its summary to PostgreSQL."""
    try:
        text, page_count, metadata = extract_document(uploaded_file)
    except ValueError as error:
        st.error(f"Dokumen belum dapat dianalisis. {error}")
        return

    result = analyze_text(text)
    document_type = uploaded_file.name.rsplit(".", 1)[-1].lower()
    try:
        record_id = save_analysis(document_type, page_count, result)
    except SQLAlchemyError:
        logger.exception("Failed to save analysis record to PostgreSQL")
        st.error(
            "Analisis berhasil dihitung, tetapi tidak dapat disimpan ke PostgreSQL. "
            "Periksa koneksi database dan coba lagi."
        )
        return
    st.session_state["current_analysis"] = {
        "upload_hash": hashlib.sha256(uploaded_file.getvalue()).hexdigest(),
        "document_type": document_type,
        "record_id": record_id,
        "page_count": page_count,
        "metadata": metadata,
        "findings": result,
    }


def show_analysis(analysis):
    """Render score status, headline metrics, and detailed findings."""
    result = analysis["findings"]
    metadata = analysis["metadata"]
    page_count = analysis["page_count"]
    score = result["total_score"]
    if score >= 65:
        status_key = "high"
    elif score >= 35:
        status_key = "mixed"
    else:
        status_key = "low"
    status = STATUS_TEXT[status_key]
    pill_class = f"pill-{status_key}"

    with st.container(border=True):
        st.markdown(
            f'<div class="status-pill {pill_class}">● {status["label"]}</div>'
            f'<div class="result-heading">Ringkasan pemeriksaan</div>'
            f'<p class="result-copy">{status["description"]}</p>',
            unsafe_allow_html=True,
        )
    st.write("")

    first, second, third = st.columns(3)
    first.metric("Skor indikasi", f"{score}%")
    second.metric(
        "Jumlah halaman",
        f"{page_count:,}" if page_count is not None else "Tidak tersedia",
        help="Informasi jumlah halaman disediakan untuk PDF. DOCX tidak menyimpan jumlah halaman tetap.",
    )
    third.metric("Jumlah kata", f"{result['word_count']:,}")
    st.progress(score / 100, text=f"Skor gabungan · {score} dari 100")
    st.caption(
        f"ID pemeriksaan `{analysis['record_id']}` · "
        f"Format {analysis['document_type'].upper()}"
    )
    st.caption(
        "Skor merupakan hasil penjumlahan indikator dan bukan probabilitas "
        "terverifikasi bahwa dokumen ditulis oleh AI."
    )

    st.markdown('<div class="section-title">Rincian pemeriksaan</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Buka bagian di bawah untuk melihat bukti '
        "dan nilai setiap indikator.</div>",
        unsafe_allow_html=True,
    )
    show_findings(result, metadata)


def show_history():
    """Display aggregate counts and bounded recent analysis history."""
    st.markdown('<div class="section-title">Riwayat pemeriksaan</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Ringkasan tersimpan di PostgreSQL. '
        "File dan teks dokumen tidak disimpan.</div>",
        unsafe_allow_html=True,
    )
    try:
        total, average, history = list_recent_analyses()
    except SQLAlchemyError:
        logger.exception("Failed to load analysis history from PostgreSQL")
        st.error("Riwayat tidak dapat dimuat. Periksa koneksi PostgreSQL.")
        return

    first, second = st.columns(2)
    first.metric("Total pemeriksaan tersimpan", f"{total:,}")
    second.metric(
        "Rata-rata skor",
        f"{average:.1f}%" if average is not None else "—",
    )
    if not history:
        st.info("Belum ada riwayat. Jalankan analisis pertama untuk mulai mengisi data.")
        return

    st.dataframe(
        [{key: value for key, value in item.items() if key != "Temuan"} for item in history],
        use_container_width=True,
        hide_index=True,
    )
    selected_id = st.selectbox(
        "Lihat rincian pemeriksaan",
        options=[item["ID"] for item in history],
    )
    selected = next(item for item in history if item["ID"] == selected_id)
    with st.expander(f"Temuan pemeriksaan {selected_id}", expanded=False):
        st.json(selected["Temuan"])


def show_database():
    """Show the live PostgreSQL connection and stored table rows in the web UI."""
    st.markdown('<div class="section-title">Data yang tersimpan di PostgreSQL</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Berikut isi tabel pemeriksaan yang benar-benar '
        "tersimpan di database, bukan contoh data.</div>",
        unsafe_allow_html=True,
    )
    try:
        overview = get_database_overview()
        total, records = list_database_records()
    except SQLAlchemyError:
        logger.exception("Failed to inspect PostgreSQL database")
        st.error("Data database tidak dapat dibaca. Periksa koneksi PostgreSQL.")
        return

    st.caption(f"Database: `{overview['database']}` · Server: {overview['server']}")
    first, second = st.columns(2)
    first.metric("Baris tersimpan di analysis_records", f"{total:,}")
    second.metric("Status ekstensi pgvector", str(overview["pgvector"]))
    st.info(
        "pgvector menyediakan dukungan tipe data vektor di PostgreSQL. "
        "Aplikasi saat ini belum membuat embeddings atau menyimpan kolom vector."
    )
    if not records:
        st.info(
            "Tabel `analysis_records` masih kosong. Buka tab Analisis dokumen, "
            "unggah PDF/DOCX, lalu tekan tombol Analisis dokumen."
        )
        return

    st.caption(
        f"Menampilkan {len(records)} dari {total} baris terbaru. "
        "File dan teks dokumen tidak disimpan."
    )
    table_rows = [
        {key: value for key, value in record.items() if key != "Rincian indikator"}
        for record in records
    ]
    st.dataframe(table_rows, use_container_width=True, hide_index=True)

    selected_id = st.selectbox(
        "Lihat nilai kolom rincian_indikator untuk satu baris",
        options=[record["ID lengkap"] for record in records],
        format_func=lambda record_id: record_id[:8],
        key="database_record_id",
    )
    selected_record = next(
        record for record in records if record["ID lengkap"] == selected_id
    )
    with st.expander(f"Kolom lengkap · pemeriksaan {selected_id}", expanded=False):
        st.json(selected_record)


def main():
    """Compose the application shell, upload flow, and history page."""
    st.set_page_config(
        page_title="Veritas Review | Analisis Dokumen",
        page_icon="📄",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    apply_styles()
    render_sidebar()
    try:
        check_database()
    except (ValueError, SQLAlchemyError) as error:
        st.error(f"Database belum siap: {error}")
        st.info("Jalankan layanan PostgreSQL dan migrasi sesuai petunjuk di README.md.")
        st.stop()

    st.markdown('<div class="eyebrow">DOCUMENT REVIEW WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown('<h1 class="hero-title">Analisis jejak AI pada dokumen</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="hero-copy">Periksa pola tekstual pada dokumen PDF atau Word melalui '
        "satu alur kerja yang ringkas dan transparan.</p>",
        unsafe_allow_html=True,
    )
    st.write("")

    analysis_tab, history_tab, database_tab = st.tabs(
        ["Analisis dokumen", "Riwayat", "Database"]
    )
    with analysis_tab:
        with st.container(border=True):
            st.markdown('<div class="section-title">Pilih dokumen untuk diperiksa</div>', unsafe_allow_html=True)
            st.markdown(
                '<div class="section-copy">PDF atau Word (.docx) · Satu dokumen per pemeriksaan</div>',
                unsafe_allow_html=True,
            )
            with st.form("analysis_form", clear_on_submit=False):
                uploaded_file = st.file_uploader(
                    "Seret file ke sini atau pilih dari perangkat",
                    type=["pdf", "docx"],
                    accept_multiple_files=False,
                    help="Format yang didukung: PDF dan Word (.docx). File .doc lama tidak didukung.",
                    label_visibility="collapsed",
                )
                submitted = st.form_submit_button(
                    "Analisis dokumen",
                    type="primary",
                    use_container_width=True,
                )
            st.markdown(
                '<div class="upload-hint">Dokumen harus berisi setidaknya 50 karakter teks. '
                "PDF hasil scan tanpa teks digital tidak didukung.</div>",
                unsafe_allow_html=True,
            )
        st.write("")
        if submitted:
            if uploaded_file is None:
                st.warning("Pilih dokumen PDF atau Word terlebih dahulu.")
            else:
                with st.spinner("Mengekstrak dan menganalisis dokumen..."):
                    analyze_upload(uploaded_file)

        current_analysis = st.session_state.get("current_analysis")
        current_hash = (
            hashlib.sha256(uploaded_file.getvalue()).hexdigest()
            if uploaded_file is not None
            else None
        )
        if current_analysis and current_analysis["upload_hash"] == current_hash:
            show_analysis(current_analysis)
        elif uploaded_file is None:
            show_empty_state()
        else:
            st.info("Tekan **Analisis dokumen** untuk memulai pemeriksaan.")

    with history_tab:
        show_history()

    with database_tab:
        show_database()

    st.markdown(
        '<div class="footer-note">Veritas Review · Alat bantu peninjauan, '
        "bukan pengganti evaluasi manusia.</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
