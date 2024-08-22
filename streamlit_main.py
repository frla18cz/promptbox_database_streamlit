import streamlit as st
import pymysql
import pandas as pd
import html
import re

# Custom CSS for better styling (unchanged)
st.markdown("""
<style>
    .section-divider {
        margin-top: 20px;
        margin-bottom: 20px;
        border-top: 1px solid #e0e0e0;
    }
    .section-header {
        font-weight: bold;
        font-size: 18px;
        margin-bottom: 10px;
        color: #4A4A4A;
    }
    .prompt-content {
        background-color: #f0f2f6;
        border-radius: 5px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .expander-title {
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .bold {
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

st.title('Prompt Box - ukázka promptů!')

# Read database connection configuration from secrets
db_config = st.secrets["mysql"]

# Initialize connection
conn = pymysql.connect(
    host=db_config["host"],
    port=db_config["port"],
    user=db_config["user"],
    password=db_config["password"],
    database=db_config["database"]
)

# Updated query (unchanged)
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

# Close the connection
conn.close()


def decode_text(text):
    if not isinstance(text, str):
        return text

    # Decode HTML entities
    text = html.unescape(text)

    # Replace escape sequences
    text = text.replace('\\n', '\n').replace('\\r', '\r').replace('\\t', '\t')

    # Replace Unicode escape sequences
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)

    # Remove any remaining backslashes
    text = text.replace('\\', '')

    return text


# Display the data with improved styling
for row in df.itertuples():
    with st.expander(f"**{decode_text(row.prompt_name)}**"):
        st.markdown(f"<div class='expander-title'>{decode_text(row.prompt_name)}</div>", unsafe_allow_html=True)

        st.markdown(f"<div class='section-header'>Prompt Version</div>", unsafe_allow_html=True)
        st.write(row.prompt_version)

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-header'>Description</div>", unsafe_allow_html=True)
        st.markdown(decode_text(row.description), unsafe_allow_html=True)

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-header'>Prompt</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prompt-content'>{decode_text(row.prompt)}</div>", unsafe_allow_html=True)

        if row.example_output:
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>Example Outputs</div>", unsafe_allow_html=True)
            examples = decode_text(row.example_output).split(';;')
            for i, example in enumerate(examples, 1):
                st.markdown(f"<div class='prompt-content'><strong>Example {i}:</strong><br>{example.strip()}</div>",
                            unsafe_allow_html=True)
                if i < len(examples):  # Add a small divider between examples, but not after the last one
                    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

        if row.followup_prompt:
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>Follow-up Prompts</div>", unsafe_allow_html=True)
            followups = decode_text(row.followup_prompt).split(';;')
            for i, followup in enumerate(followups, 1):
                st.markdown(f"<div class='prompt-content'>{i}. {followup.strip()}</div>", unsafe_allow_html=True)

        if row.instructions:
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>Instructions</div>", unsafe_allow_html=True)
            # Odrážky formátované správně s HTML <ul> a <li>
            instructions = decode_text(row.instructions).splitlines()
            st.markdown("<ul>" + "".join(f"<li>{line}</li>" for line in instructions if line.strip()) + "</ul>", unsafe_allow_html=True)

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-header'>Category</div>", unsafe_allow_html=True)
        st.write(decode_text(row.category_name))

        if row.subcategories:
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>Subcategories</div>", unsafe_allow_html=True)
            st.write(decode_text(row.subcategories))

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-header'>Tags</div>", unsafe_allow_html=True)
        st.write(decode_text(row.tags))

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-header'>Price</div>", unsafe_allow_html=True)
        st.write("Zdarma" if row.price == 0 else f"{row.price}")
