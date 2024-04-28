    
from langchain_community.callbacks import get_openai_callback
from langchain.prompts import HumanMessagePromptTemplate
from langchain_core.prompts  import ChatPromptTemplate
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
import os

system_content = """Based on the attached contract, please generate the invoice schedule starting from the initial invoice which is due upon effective date and ending at the end of 2026. In the invoice schedule, for each invoice please capture the following items. Its is very important that each invoice contains the following information:

Customer Name 
Invoice Number (formatted as first three letters of customer name, then dash, then number)
Invoice Date (in mm/dd/yyyy format)
Due Date (in mm/dd/yyyy format)
Product Name
Price (in plain number)

Please provide it in JSON format.
"""



generate_invoice_schedule_function = {
    "name": "generate_invoice_schedule",
    "description": "Creates an invoice schedule from a given contract text, detailing each invoice from the contract's effective date until the end of 2026. This includes customer details, invoice numbering, product descriptions, and pricing.",
    "parameters": {
        "type": "object",
        "properties": {
            "invoice_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "customer_name": {
                            "type": "string",
                            "description": "The name of the customer as stated in the contract.",
                        },
                        "invoice_number": {
                            "type": "string",
                            "description": "A unique identifier for the invoice, typically starting with the first three letters of the customer's name followed by a dash and a sequence number.",
                        },
                        "invoice_date": {
                            "type": "string",
                            "format": "date",
                            "description": "The date on which the invoice is issued, formatted as mm/dd/yyyy.",
                        },
                        "due_date": {
                            "type": "string",
                            "format": "date",
                            "description": "The date by which the invoice must be paid, formatted as mm/dd/yyyy.",
                        },
                        "product_name": {
                            "type": "string",
                            "description": "The name of the product or service being billed in the invoice.",
                        },
                        "price": {
                            "type": "number",
                            "description": "The amount to be paid for the product or service, represented as a plain number without formatting.",
                        },
                    },
                    "required": ["customer_name", "invoice_number", "invoice_date", "due_date", "product_name", "price"],
                },
                "description": "Details each invoice within the schedule, including customer details, dates, product information, and pricing.",
            },
        },
        "required": ["invoice_items"],
    },
}

def generate_invoice_schedule(document_text):
    # Call the OpenAI model to generate the invoice schedule
    functions = [generate_invoice_schedule_function]
    model =  os.environ.get("OPENAI_MODEL_NAME")
    llm = ChatOpenAI(model = model)
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(content=(system_content)),
            HumanMessagePromptTemplate.from_template("{document_text}"),
        ])
    chain =  prompt | llm.bind(function_call={"name": generate_invoice_schedule_function["name"]}, functions=functions) | JsonOutputFunctionsParser()

    
    return chain.invoke({"document_text":document_text})