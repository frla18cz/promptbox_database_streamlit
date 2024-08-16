import streamlit as st
import pymysql
import pandas as pd

# Custom CSS for better styling
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

# Query to describe the structure of promptbox_prompts
query_describe = "DESCRIBE promptbox_prompts;"
describe_df = pd.read_sql(query_describe, conn)

# Check if columns exist
columns = describe_df['Field'].tolist()
example_output_exists = 'example_output' in columns
followup_prompt_exists = 'followup_prompt' in columns

# Construct the query dynamically based on the existence of columns
select_fields = '''
    p.id AS prompt_id, p.name AS prompt_name, p.description, p.prompt, p.instructions, p.price,
    c.name AS category_name, GROUP_CONCAT(t.name) AS tags
'''

if example_output_exists:
    select_fields += ', p.example_output'

if followup_prompt_exists:
    select_fields += ', p.followup_prompt'

query = f'''
    SELECT {select_fields}
    FROM promptbox_prompts p
    JOIN promptbox_categories c ON p.category_id = c.id
    LEFT JOIN promptbox_prompts_tags pt ON p.id = pt.prompt_id
    LEFT JOIN promptbox_tags t ON pt.tag_id = t.id
    GROUP BY p.id, p.name, p.description, p.prompt, p.instructions, p.price, c.name
'''

if example_output_exists:
    query += ', p.example_output'

if followup_prompt_exists:
    query += ', p.followup_prompt'

df = pd.read_sql(query, conn)

# Close the connection
conn.close()

# Display the data with improved styling
for row in df.itertuples():
    with st.expander(f"**{row.prompt_name}**"):
        st.markdown(f"<div class='section-header'>Description</div>", unsafe_allow_html=True)
        st.write(row.description)

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-header'>Prompt</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='prompt-content'>{row.prompt}</div>", unsafe_allow_html=True)

        if example_output_exists and hasattr(row, 'example_output') and row.example_output:
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>Example Output</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='prompt-content'>{row.example_output}</div>", unsafe_allow_html=True)

        if followup_prompt_exists and hasattr(row, 'followup_prompt') and row.followup_prompt:
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>Follow-up Prompts</div>", unsafe_allow_html=True)
            followups = row.followup_prompt.split(';;')
            for i, followup in enumerate(followups, 1):
                st.markdown(f"<div class='prompt-content'>{i}. {followup.strip()}</div>", unsafe_allow_html=True)

        if row.instructions:
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            st.markdown(f"<div class='section-header'>Instructions</div>", unsafe_allow_html=True)
            st.write(row.instructions)

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-header'>Category</div>", unsafe_allow_html=True)
        st.write(row.category_name)

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-header'>Tags</div>", unsafe_allow_html=True)
        st.write(row.tags)

        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown(f"<div class='section-header'>Price</div>", unsafe_allow_html=True)
        st.write("Zdarma" if row.price == 0 else f"{row.price}")