import pandas as pd
import streamlit as st
from pinotdb import connect
import plotly.express as px

# Set up Streamlit page configuration
st.set_page_config(layout="wide")
st.header("Real-Time Page Visit Tracking Dashboard")

# Connect to Pinot
conn = connect(host='47.129.163.101', port=8099, path='/query/sql', scheme='http')

# Queries dictionary with properly formatted keys
queries = {
    "Query 1": """
        SELECT GENDER, SEGMENT, AVG(VIEWTIME) AS avg_viewtime
        FROM Aggregate5
        WHERE VIEWTIME IS NOT NULL 
        GROUP BY GENDER, SEGMENT
        ORDER BY avg_viewtime DESC;""",

    "Query 2": """
        SELECT SEGMENT, SUM(VIEWTIME) AS total_viewtime
        FROM Aggregate5
        WHERE VIEWTIME IS NOT NULL
        GROUP BY SEGMENT
        ORDER BY total_viewtime DESC
        LIMIT 3;""",

    "Query 3": """
        SELECT SEGMENT, SUM(VIEWTIME) AS total_viewtime
        FROM Aggregate5
        GROUP BY SEGMENT
        ORDER BY total_viewtime ASC;""",

    "Query 4": """
        SELECT SEGMENT, GENDER, COUNT(*) AS total_views
        FROM Aggregate5
        GROUP BY SEGMENT, GENDER
        ORDER BY total_views DESC;"""
}

# Function to execute a query with error handling and caching
@st.cache_data(ttl=60)  # Cache results for 60 seconds to optimize performance
def execute_query(sql):
    try:
        cursor = conn.cursor()
        result = pd.DataFrame(cursor.execute(sql).fetchall(), columns=[col[0] for col in cursor.description])
        if result.empty:
            st.warning(f"No data returned for query: {sql}")
        return result
    except Exception as e:
        # Check if the error is related to unavailable segments
        error_message = str(e)  # Get the string representation of the error
        
        st.error(f"Error executing query: {error_message}")
        
        # Check for specific keywords related to unavailable segments in the error message
        if 'segments unavailable' in error_message:
            # Extract the list of unavailable segments from the error message
            try:
                # The unavailable segments are typically included as part of the error message string
                start_index = error_message.find('[') + 1
                end_index = error_message.find(']')
                unavailable_segments = error_message[start_index:end_index].split(',')
                unavailable_segments = [seg.strip() for seg in unavailable_segments]
                st.write(f"The following segments are unavailable: {', '.join(unavailable_segments)}")
            except Exception:
                st.write("Unable to extract unavailable segments from the error message.")
            
            st.write("These segments may be temporarily down. Please try again later or check the Pinot cluster.")
        
        return pd.DataFrame()  # Return an empty dataframe on error

# Display all four charts with improved error handling and user feedback
with st.container():
    col1, col2 = st.columns(2)

    # Chart 1: Average Viewtime by Gender and Segment
    with col1:
        st.subheader("Average Viewtime by Gender and Segment")
        result = execute_query(queries["Query 1"])
        if not result.empty:
            fig = px.bar(result, x="SEGMENT", y="avg_viewtime", color="GENDER", title="Average Viewtime by Gender and Segment")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No data available or unable to load data.")

    # Chart 2: Total Viewtime by Segment (Top 3)
    with col2:
        st.subheader("Total Viewtime by Segment (Top 3)")
        result = execute_query(queries["Query 2"])
        if not result.empty:
            fig = px.bar(result, x="SEGMENT", y="total_viewtime", title="Total Viewtime by Segment (Top 3)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No data available or unable to load data.")

with st.container():
    col3, col4 = st.columns(2)

    # Chart 3: Total Viewtime by Segment (Ascending Order)
    with col3:
        st.subheader("Total Viewtime by Segment (Ascending Order)")
        result = execute_query(queries["Query 3"])
        if not result.empty:
            fig = px.bar(result, x="SEGMENT", y="total_viewtime", title="Total Viewtime by Segment (Ascending Order)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No data available or unable to load data.")

    # Chart 4: Total Views by Segment and Gender
    with col4:
        st.subheader("Total Views by Segment and Gender")
        result = execute_query(queries["Query 4"])
        if not result.empty:
            fig = px.bar(result, x="SEGMENT", y="total_views", color="GENDER", title="Total Views by Segment and Gender")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("No data available or unable to load data.")
