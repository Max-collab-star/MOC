import streamlit as st
from cnf import CFGConverter
from cyk import CYKParser

st.set_page_config(
    page_title="CYK Algorithm Visualizer", layout="wide"
)

st.markdown(
    """
    <style>
    /* Expand main container width to remove side dead space */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        padding-left: 3rem;
        padding-right: 3rem;
        max-width: 100% !important;
    }
    .stApp {
        background-color: #ffffff;
        color: #111827; 
    }

    /* Make text inputs and text areas black with white text */
    .stTextInput input, .stTextArea textarea {
        background-color: #0f172a !important;
        color: #ffffff !important;
        border: 1px solid #334155 !important;
        border-radius: 6px !important;
    }

    /* Style input labels for readability */
    .stTextInput label, .stTextArea label, .stSubheader {
        color: #1e293b !important;
    }

    div.stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
        font-weight: 600;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        width: 100%;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #4338ca 0%, #4f46e5 100%);
        box-shadow: 0 6px 16px rgba(79, 70, 229, 0.5);
    }
    
    /* Make table cells black with white text */
    .matrix-cell {
        background-color: #0f172a;
        border: 1px solid #334155;
        border-radius: 6px;
        text-align: center;
        padding: 10px;
        font-weight: bold;
        color: #ffffff;
        font-size: 1rem;
        min-height: 50px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    </style>
""",
    unsafe_allow_html=True,
)

st.title("CYK Algorithm Visualizer")

# Use well-proportioned columns for input fields
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("📝 Context-Free Grammar Input")
    default_grammar = (
        "S -> AB | BC\nA -> BA | a\nB -> CC | b\nC -> AB | a"
    )
    grammar_input = st.text_area(
        "Enter CFG Rules (Format: A -> BC | a)",
        default_grammar,
        height=140,
    )
    start_symbol = st.text_input("Start Symbol", "S")

with col2:
    st.subheader("🔍 Target String Verification")
    test_string = st.text_input("Enter String to Check", "baab")
    st.markdown("<br>", unsafe_allow_html=True)  # Spacer alignment
    run_btn = st.button("Execute CYK Algorithm")

if run_btn:
    st.markdown("---")
    converter = CFGConverter(grammar_input, start_symbol)
    grammar = converter.to_cnf()

    with st.expander(
        "🛠️ View Step-by-Step CNF Conversion Pipeline", expanded=True
    ):
        step_cols = st.columns(len(converter.steps))
        for idx, (step_name, rule_text) in enumerate(converter.steps.items()):
            with step_cols[idx]:
                st.markdown(f"**{step_name}**")
                st.code(rule_text, language="text")

    parser = CYKParser(grammar, converter.start_symbol)
    accepted, table = parser.parse(test_string)
    
    n = len(test_string)
    top_cell = table[n - 1][0] if n > 0 else set()
    is_accepted = accepted or (
        converter.start_symbol in top_cell or start_symbol in top_cell
    )

    if accepted:
        st.success(
            f"✅ Result: String '{test_string}' is **ACCEPTED** by the grammar!"
        )
    else:
        st.error(
            f"❌ Result: String '{test_string}' is **REJECTED** by the grammar."
        )


    st.subheader("Upper-Triangular Parsing Matrix (Indexed Grid)")
    st.markdown(
        "<p style='color: #64748b;'>Matrix rows correspond to substring lengths and indices map directly to your evaluation references.</p>",
        unsafe_allow_html=True,
    )

    n = len(test_string)

    # Dynamic column sizing ratios: first column slightly narrower for row labels, rest split equally
    col_ratios = [0.8] + [1.0] * (n + 1)

    # Render Header Indices matching the string characters
    header_cols = st.columns(col_ratios)
    header_cols[0].markdown(
        "<div class='matrix-cell' style='background:#0f172a; border:1px solid #334155; color:#ffffff;'>#</div>",
        unsafe_allow_html=True,
    )
    for idx, char in enumerate(test_string):
        header_cols[idx + 1].markdown(
            f"<div class='matrix-cell' style='background:#0f172a; color:#ffffff; border:1px solid #334155;'>{idx+1}<br><span style='font-size:0.75rem; color:#94a3b8;'>{char}</span></div>",
            unsafe_allow_html=True,
        )

    # Render Table Rows from top to bottom
    for i in range(n - 1, -1, -1):
        row_cols = st.columns(col_ratios)
        row_cols[0].markdown(
            f"<div class='matrix-cell' style='background:#0f172a; color:#ffffff; font-size:0.9rem; border:1px solid #334155;'>Row {i+1}</div>",
            unsafe_allow_html=True,
        )
        for j in range(n):
            if j < n - i:
                cell_vals = (
                    ", ".join(sorted(table[i][j]))
                    if table[i][j]
                    else "—"
                )
                row_cols[j + 1].markdown(
                    f"<div class='matrix-cell'>{cell_vals}</div>",
                    unsafe_allow_html=True,
                )
            else:
                row_cols[j + 1].markdown(
                    "<div class='matrix-cell' style='visibility: hidden; border:none;'></div>",
                    unsafe_allow_html=True,
                )