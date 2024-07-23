import streamlit as st
import pandas as pd
import chromadb
from chromadb import Client

# Function to get ChromaDB client
def get_client(directory):
    return chromadb.PersistentClient(path=directory)

# Function to list all collections
def list_collections(client):
    return client.list_collections()

# Function to get collection data and convert to DataFrame
def get_collection_data(client, collection_name):
    coll = client.get_collection(collection_name)
    colldata = coll.get()

    # Check for None values and handle appropriately
    lengths = {key: (len(value) if value is not None else 0) for key, value in colldata.items()}
    max_length = max(lengths.values())

    normalized_data = {}
    for key, value in colldata.items():
        if value is None:
            normalized_data[key] = [None] * max_length
        elif len(value) < max_length:
            normalized_data[key] = value + [None] * (max_length - len(value))
        elif len(value) > max_length:
            normalized_data[key] = value[:max_length]
        else:
            normalized_data[key] = value

    df = pd.DataFrame(normalized_data)
    return df


# Streamlit App
st.title('ChromaDB Explorer')

# Directory path input
directory = st.text_input('Enter the directory path for persistent ChromaDB')

if directory:
    client = get_client(directory)

    # Button to list all collections
    if st.button('List Collections'):
        collections = list_collections(client)
        st.session_state['collections'] = {coll.name: coll.id for coll in collections}
        st.write('Available Collections:')
        for name, id_ in st.session_state['collections'].items():
            st.write(f"{name} (ID: {id_})")

    st.write("---")

# Dropdown to select collection name
if 'collections' in st.session_state and st.session_state['collections']:
    collection_name = st.selectbox('Select the collection name', list(st.session_state['collections'].keys()))

    if collection_name:
        # Button to get collection count
        if st.button('Get Collection Info'):
            coll = client.get_collection(collection_name)
            column_count = len(coll.get())
            count = coll.count()
            st.markdown(
                f"Collection **'{collection_name}'** has **<span style='color: orange;'>{column_count}</span> columns** and **<span style='color: orange;'>{count}</span> entries**.",
                unsafe_allow_html=True)

        st.write("---")

        # Filter criteria input
        filter_column = st.text_input('Enter column to filter (leave blank for no filter)')
        filter_word = st.text_input('Enter word to filter by (leave blank for no filter)')


        # Button to convert collection to DataFrame and display with pagination
        if st.button('Show Data '):
            df = get_collection_data(client, collection_name)

            # Apply filter if specified
            if filter_word and filter_column:
                df = df[df[filter_column].astype(str).str.contains(filter_word, na=False)]

            # Store DataFrame and pagination info in session state
            st.session_state['dataframe'] = df
            st.session_state['page'] = 1

        st.write("---")

        # Display DataFrame with pagination if available in session state

        if 'dataframe' in st.session_state:
            df = st.session_state['dataframe']

            # Display selected collection name
            st.subheader(f"Collection: {collection_name}")

            # Pagination settings
            rows_per_page = 10
            total_rows = len(df)
            total_pages = (total_rows + rows_per_page - 1) // rows_per_page

            # Add page navigation
            page = st.number_input('Page', min_value=1, max_value=total_pages, value=st.session_state['page'])
            st.session_state['page'] = page
            start_idx = (page - 1) * rows_per_page
            end_idx = start_idx + rows_per_page

            # Display the data for the current page
            st.write(df.iloc[start_idx:end_idx])

        st.write("---")

        # Button to delete collection
        if st.button('Delete Collection'):
            # Confirmation before deletion
            if st.button('Confirm Deletion'):
                client.delete_collection(collection_name)
                st.write(f"Collection '{collection_name}' has been deleted.")
