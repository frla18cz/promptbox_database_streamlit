import streamlit as st
import pymysql
import pandas as pd
import html
import re

# Custom CSS for enhanced styling
st.markdown("""
<style>
    .section-divider {
        margin-top: 20px;
        margin-bottom: 20px;
        border-top: 1px solid #e0e0e0;
    }
    .section-header {
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 10px;
        color: #3A3A3A;
        padding-left: 10px;
        border-left: 5px solid #2ecc71;
    }
    .prompt-content {
        background-color: #f7f9fc;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 2px 2px 12px rgba(0, 0, 0, 0.1);
    }
    .expander-title {
        font-size: 24px;
        font-weight: bold;
        color: #2ecc71;
        margin-bottom: 10px;
        text-align: center;
    }
    .category-header {
        font-size: 26px;
        font-weight: bold;
        color: #2ecc71;
        margin-top: 20px;
        margin-bottom: 20px;
        text-align: center;
        padding: 10px;
        border: 2px solid #2ecc71;
        border-radius: 8px;
        background-color: #e8f5e9;
        box-shadow: 0px 4px 10px rgba(46, 204, 113, 0.2);
    }
    .subcategory-tab {
        font-size: 22px;
        font-weight: bold;
        color: #3498db;
        margin-top: 15px;
        margin-bottom: 15px;
        padding: 10px;
        border: 2px solid #3498db;
        border-radius: 8px;
        background-color: #eaf2fa;
        text-align: center;
        box-shadow: 0px 4px 8px rgba(52, 152, 219, 0.2);
    }
    .prompt-title {
        font-size: 20px;
        font-weight: bold;
        color: #2c3e50;
        margin-top: 10px;
        margin-bottom: 10px;
        padding: 8px;
        border-radius: 5px;
        background-color: #ecf0f1;
        text-align: left;
    }
    .stTabs > div[data-baseweb="tab"] > button {
        background-color: #2ecc71 !important;
        color: white !important;
        border: none;
        border-radius: 8px !important;
        padding: 10px 15px !important;
        margin: 5px !important;
        font-weight: bold !important;
        box-shadow: 0px 2px 5px rgba(46, 204, 113, 0.5) !important;
        transition: background-color 0.3s ease, transform 0.3s ease;
    }
    .stTabs > div[data-baseweb="tab"]:hover > button {
        background-color: #27ae60 !important;
        transform: translateY(-2px) !important;
    }
    .stTabs > div[data-baseweb="tab"][aria-selected="true"] > button {
        background-color: #1abc9c !important;
        color: #fff !important;
    }
    /* Vylepšení vzhledu tlačítek pro kategorie a podkategorie */
    .stTabs button {
        border: none;
        background-color: #e0e0e0;
        color: #333;
        font-weight: bold;
        border-radius: 6px;
        padding: 10px 15px;
        margin: 0 5px;
        transition: all 0.3s ease;
    }
    .stTabs button:hover {
        background-color: #3498db;
        color: white;
        box-shadow: 0px 4px 8px rgba(52, 152, 219, 0.2);
    }
    .stTabs button:focus {
        outline: none;
        background-color: #1abc9c;
        color: white;
    }
    .stTabs button:active {
        transform: translateY(2px);
    }
</style>
""", unsafe_allow_html=True)

st.title('Prompt Box - ukázka promptů!')

# Připojení k databázi a vykonání dotazu
db_config = st.secrets["mysql"]
conn = pymysql.connect(
    host=db_config["host"],
    port=db_config["port"],
    user=db_config["user"],
    password=db_config["password"],
    database=db_config["database"]
)

query = '''
    SELECT 
        p.id AS prompt_id, p.name AS prompt_name, p.description, p.prompt, 
        p.instructions, p.price, p.example_output, p.followup_prompt,
        c.name AS category_name, 
        GROUP_CONCAT(DISTINCT sc.name SEPARATOR ', ') AS subcategories,
        GROUP_CONCAT(DISTINCT t.name SEPARATOR ', ') AS tags, 
        p.prompt_version
    FROM promptbox_prompts p
    JOIN promptbox_categories c ON p.category_id = c.id
    LEFT JOIN promptbox_prompts_sub_categories psc ON p.id = psc.prompt_id
    LEFT JOIN promptbox_subcategories sc ON psc.subcategory_id = sc.id
    LEFT JOIN promptbox_prompts_tags pt ON p.id = pt.prompt_id
    LEFT JOIN promptbox_tags t ON pt.tag_id = t.id
    GROUP BY p.id, p.name, p.description, p.prompt, p.instructions, p.price, 
             c.name, p.prompt_version, p.example_output, p.followup_prompt
    ORDER BY p.id DESC
'''

df = pd.read_sql(query, conn)
conn.close()

# Pomocná funkce pro dekódování textu
def decode_text(text):
    if not isinstance(text, str):
        return text
    text = html.unescape(text)
    text = text.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
    text = text.replace('\\', '')
    return text

# Seznam unikátních kategorií
categories = df['category_name'].unique().tolist()

# Vytvoření záložek pro každou kategorii
tab_list = st.tabs(categories)

for i, category in enumerate(categories):
    with tab_list[i]:
        st.markdown(f"<div class='category-header'>{category}</div>", unsafe_allow_html=True)
        category_df = df[df['category_name'] == category]

        # Seznam unikátních podkategorií pro aktuální kategorii
        subcategories = category_df['subcategories'].str.split(', ').explode().unique().tolist()  # Konverze na seznam

        # Zobrazení podkategorií jako záložek
        subcategory_tab_list = st.tabs(subcategories)

        for j, subcategory in enumerate(subcategories):
            if subcategory:  # Ověření, zda podkategorie není prázdná
                subcategory_df = category_df[category_df['subcategories'].str.contains(subcategory, na=False)]

                with subcategory_tab_list[j]:
                    st.markdown(f"<div class='subcategory-tab'>{subcategory}</div>", unsafe_allow_html=True)
                    for row in subcategory_df.itertuples():
                        # Zobrazení jednotlivých promptů uvnitř záložek podkategorií
                        with st.expander(f"Prompt: {decode_text(row.prompt_name)}"):
                            st.markdown(f"<div class='prompt-title'>{decode_text(row.prompt_name)}</div>", unsafe_allow_html=True)

                            st.markdown(f"<div class='section-header'>Verze promptu</div>", unsafe_allow_html=True)
                            st.write(row.prompt_version)

                            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='section-header'>Popis</div>", unsafe_allow_html=True)
                            st.markdown(decode_text(row.description), unsafe_allow_html=True)

                            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='section-header'>Prompt</div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='prompt-content'>{decode_text(row.prompt)}</div>", unsafe_allow_html=True)

                            if row.followup_prompt:
                                st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='section-header'>Následující prompty</div>", unsafe_allow_html=True)
                                followups = decode_text(row.followup_prompt).split(';;')
                                for i, followup in enumerate(followups, 1):
                                    st.markdown(f"<div class='prompt-content'>{i}. {followup.strip()}</div>", unsafe_allow_html=True)

                            if row.instructions:
                                st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='section-header'>Instrukce</div>", unsafe_allow_html=True)
                                instructions = decode_text(row.instructions).splitlines()
                                st.markdown("<ul>" + "".join(f"<li>{line}</li>" for line in instructions if line.strip()) + "</ul>", unsafe_allow_html=True)

                            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='section-header'>Tagy</div>", unsafe_allow_html=True)
                            st.write(decode_text(row.tags))

                            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
                            st.markdown(f"<div class='section-header'>Cena</div>", unsafe_allow_html=True)
                            st.write("Zdarma" if row.price == 0 else f"{row.price}")

                            if row.example_output:
                                st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
                                st.markdown(f"<div class='section-header'>Ukázky výstupů</div>", unsafe_allow_html=True)
                                examples = decode_text(row.example_output).split(';;')
                                for i, example in enumerate(examples, 1):
                                    formatted_example = example.strip().replace('\n', '<br>')
                                    st.markdown(f"<div class='prompt-content'><strong>Ukázka {i}:</strong><br>{formatted_example}</div>", unsafe_allow_html=True)
                                    if i < len(examples):
                                        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
