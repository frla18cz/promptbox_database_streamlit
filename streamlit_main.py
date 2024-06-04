import streamlit as st
import pymysql
import pandas as pd

st.title('Promt Box - ukázka promptů!')

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

# Check if example_output column exists
columns = describe_df['Field'].tolist()
example_output_exists = 'example_output' in columns

# Construct the query dynamically based on the existence of example_output
select_fields = '''
    p.id AS prompt_id, p.name AS prompt_name, p.description, p.prompt, p.instructions, p.price,
    c.name AS category_name, GROUP_CONCAT(t.name) AS tags
'''

if example_output_exists:
    select_fields = '''
        p.id AS prompt_id, p.name AS prompt_name, p.description, p.prompt, p.example_output, p.instructions, p.price,
        c.name AS category_name, GROUP_CONCAT(t.name) AS tags
    '''

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

df = pd.read_sql(query, conn)

# Close the connection
conn.close()

# Print results with expanders for additional details
for row in df.itertuples():
    with st.expander(f"**{row.prompt_name}**"):
        st.write(f"**Description:** {row.description}")
        st.divider()
        st.markdown(f"**Prompt:**\n{row.prompt}", unsafe_allow_html=True)
        st.divider()
        if example_output_exists and row.example_output:
            st.divider()
            st.write(f"**Example Output:** {row.example_output}")
        if row.instructions:
            st.divider()
            st.write(f"**Instructions:** {row.instructions}")
        st.write(f"**Category:** {row.category_name}")
        st.divider()
        st.write(f"**Tags:** {row.tags}")
        if row.price == 0:
            st.divider()
            st.write("**Price:** Zdarma")
        else:
            st.divider()
            st.write(f"**Price:** {row.price}")
