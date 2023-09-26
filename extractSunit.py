from transformers import GPT2Tokenizer, GPT2Model
import json 
from methodCFG import Sunit

def extract(inputFile,outputFile): 
    try:
        with open(inputFile, 'r') as in_file:
            input='\n'.join(in_file)
        sunit=Sunit(input)
        sunit.composeSunit()
        with open(outputFile,'w') as out_file:
            out_file.write(sunit.source_code)
    except Exception as e:
        print(f"Error: {e}, {type(e)}")
