from blog_gen import graph, get_state

import streamlit as st

def metadata():
    with st.expander("Provide more context"):
        meta_data = st.text_input('Context: ')
        return meta_data

def invoke_llm(initial_input):
    config = {'Configurable':{'thread_id':'1'}}
    graph.invoke(initial_input, config= config)


def ui():
    with st.sidebar:
        st.header("Input Options: ")
        input_option = st.radio(label= "Choose one", options=['Topic','URL','PDF'])

    if input_option == 'PDF':
        file_input = st.file_uploader(label= "Upload file ", type= ['pdf'])
        meta_data = metadata()
        if st.button("Generate Bolg"):
            initial_input = {
                'uploaded_file': file_input,
                'meta_data': meta_data
            }

    elif input_option == 'URL':
        url = (st.text_input('Enter URLs comma seperated: ')).split(',')
        meta_data = metadata()
        if st.button("Generate Bolg"):
            initial_input = {
                'url': url,
                'meta_data': meta_data
            }

    elif input_option == 'Topic':
        topic = st.text_input("Enter Topic")
        meta_data = metadata()
        if st.button("Generate Bolg"):
            initial_input = {
                'topic':topic,
                'meta_data': meta_data
            }
    return initial_input

def main():
    initial_input = ui()
    state = get_state()
    pass

















if __name__ == "__main__":
    #run_graph()


    from PIL import Image

    data = graph.get_graph().draw_mermaid_png()
    image = r'D:\krish\assesment\bloog.png'
    with open(image,'wb') as f:
        f.write(data)
    Image.open(image).show()