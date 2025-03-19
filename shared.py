from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, Optional, Literal
from operator import add


#-----------Data--Format------------

class Headers(BaseModel):
    name : str = Field(description="Subheading of the blog")
    description : str = Field(description="Provide a short description of subheading")

class Blog(BaseModel):
    sections: list[Headers] = Field(description="Holdes list of Subheadings with their discription")


#----------Variable--Setup----------
class State(TypedDict):
    topic : Optional[str]
    meta_data : Optional[str]     # Meta data from user's end 
    section : list[Headers]
    url : Optional[list[str]]       # web parsing
    uploaded_file : Optional[list[str]]  # pdf data
    complete_section : Annotated[list[str], add]
    final_content : str
    user_feedback : Optional[str]  # user feedback
    text_content : Optional[str]

#----for--handling--parallel--processing-------
class Workflow(TypedDict):
    each_section : Headers
    meta_data : Optional[str]
    complete_section : Annotated[list[str], add]

#-------user--feedback--structure--------
class Sentement(TypedDict):
    feedback : Literal['Positive','Negative']