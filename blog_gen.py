import os
import sys
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langgraph.graph import START, StateGraph, END
from langgraph.constants import Send
from langgraph.checkpoint.memory import MemorySaver

os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')
os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_PROJECT'] = 'Blog_writer'

from shared import State, Blog, Workflow, Sentement  
from blog_web import Webloader, document_load

#---------Model---------
model = ChatGroq(model = "llama3-70b-8192")
blog_structured_output = model.with_structured_output(Blog)
feedback_sentement = model.with_structured_output(Sentement)

#-------Log Report------
from logger import logging

l1 = logging.getLogger('Error/Exception')
l1.setLevel(logging.DEBUG)

l2 = logging.getLogger('Status')
l2.setLevel(logging.DEBUG)


def get_state():
    return memory.get_state()

#-------Agents--------
def Orchestrator(state: State):
    try:
        if state.get('topic'):
            res = blog_structured_output.invoke(
            [
                {'role':'system', 'content':f'Genrate a plane for the blog, taking user feedback under consideration: {state["user_feedback"]}' if state.get("user_feedback") else 'Generate a indepth plan for the blog'},
                {'role':'user', 'content':f'Here is the topic: {state["topic"]}, meta data from user: {state["meta_data"]}'}
            ]
            )
            l2.info("Topic State")
            
        elif 'uploaded_file' in state:
            res = blog_structured_output.invoke(
            [
                {'role':'system', 'content':f'Genrate a plane for the blog, taking user feedback under consideration: {state["user_feedback"]}' if state.get("user_feedback") else 'Generate an indepth plan for the blog'},
                {'role':'user', 'content':f'Here is the data: {state["text_content"]}, meta data from user: {state["meta_data"]}'}
            ]
            )
            l2.info("Uploaded_File  State")
            
        elif state.get('url'):
            res = blog_structured_output.invoke(
                [
                    {'role':'system', 'content':f'Genrate a plane for the blog,  taking user feedback under consideration: {state["user_feedback"]}' if state.get("user_feedback") else 'Generate an indepth plan for the blog'},
                    {'role':'user', 'content':f'Here is the data from website: {state["text_content"]}, meta data from user: {state["meta_data"]}'}
                ]
            )
            l2.info('URL State')
        return {'section': res.sections}
    
    except:
        l1.error('State not found Orchestrator')
        sys.exit()
    

def Condition(state: State):
    l2.info("API Call Parallel")
    return [Send('Prallel Wokers',{'each_section':section, 'meta_data': state['meta_data'], 'user_feed': state['user_feedback'] if state.get('user_feedback') else None}) for section in state['section']]


#LLM call -- execution
def llm_call(state: Workflow):
    if state.get('user_feedback'):
        res = model.invoke(
            [
                {'role':'system', 'content':f"Write a section of blog, with the help of provided section header and its description. Structure the content such that its easily understandable by any person while providing core knowledge. Alos consider the user feedback: {state['user_feed']}"},
                {'role':'assistant', 'content':f'previous blog to improve upon: {state["final_content"]}'},
                {'role':'user', 'content':f"Here is blog section header: {state['each_section'].name}, and section description: {state['each_section'].description}. User adition data {state['meta_data']}, provide answer in makrdown format."}
            ]
        )
        l2.info("LLM call - User_Feedback")
    else:
        res = model.invoke(
            [
                {'role':'system', 'content':"Write a section of blog, with the help of provided section header and its description. Structure the content sutch that its easily understandable by any person."},
                {'role':'user', 'content':f"Here is blog section header: {state['each_section'].name}, and section description: {state['each_section'].description}. User adition data {state['meta_data']}, provide answer in makrdown format."}
            ]
        )
        l2.info("LLM call")
    return {'complete_section':[res.content]}

def User_feed(state: State):
    print('Review Blog - \n',state['final_content'])
    feed_back = input('Enter feedback (provide positive ): ')
    decision = feedback_sentement.invoke([
        {'role':'system','content':'Analyze the sentement of user feedback, and answer if its postive(meaning to further improvement required)or else negative'},
        {'role':'user','content':f"This is the user feedback: {feed_back}"}
    ])

    if decision['feedback'] == 'Positive':
        l2.info('User Feedback - NoImprovement')
        return 'Pass'
    
    state['user_feedback'] = feed_back
    l2.info('User Feedback - Improvement')
    return 'Polish'
   

# Combining all the sections ---
def final_output(state: State):
    data = state['complete_section']
    formated_data = '\n\n---\n\n'.join(data)
    state['final_content'] = formated_data
    print(state['final_content'])
    l2.info('Final Output')
    return state

def tool_node(state: State):
    if 'uploaded_file' in state:
        l1.info("Uploaded File - Tool Node")
        return document_load(state)
    
    elif 'url' in state:
        l1.info("URL - Tool Node")
        return Webloader(state)
    
    elif 'topic' in state:
        l1.info("Topic - Tool Node")
        pass

    else: 
        l2.exception('No data in State')
        sys.exit()

#--------Graph----------
memory = MemorySaver()
graph = (
    StateGraph(State)
    .add_node('Work Manager',Orchestrator)
    .add_node('Prallel Wokers',llm_call)
    .add_node('Combiner',final_output)
    .add_node('tool_loader', tool_node)

    .add_edge(START, 'tool_loader')
    .add_edge('tool_loader', 'Work Manager')
    .add_conditional_edges('Work Manager',Condition,['Prallel Wokers'])
    .add_edge('Prallel Wokers', 'Combiner')
    .add_conditional_edges('Combiner',User_feed,{'Pass':END, 'Polish':'Work Manager'})
    .compile(checkpointer=memory)
)

def run_graph():
    config = {'configurable': {'thread_id': '11'}}
    
    initial_input = {
        'topic': 'Unsupervised Learning',
        'meta_data':"explain the core functioning."
    }
    graph.invoke(initial_input, config=config)
    
if __name__ == "__main__":
    run_graph()

    from PIL import Image
    data = graph.get_graph().draw_mermaid_png()
    image = './assesment/blog.png'
    with open(image,'wb') as f:
        f.write(data)
    Image.open(image).show()