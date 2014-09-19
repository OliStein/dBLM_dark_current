import numpy as np
import pandas as pd



def list2pandas(inputVector):
    output = pd.DataFrame(columns = ['U','hr','min','sec','ukendt','yr', 'Nmeas'])
    nentries = int(len(inputVector)/7)  #The length of the vector
    output['U'] = inputVector[0::7]
    output['hr'] = inputVector[1::7]
    output['min'] = inputVector[2::7]
    output['sec'] = inputVector[3::7]
    output['ukendt'] = inputVector[4::7]
    output['yr'] = inputVector[5::7]
    output['Nmeas'] = inputVector[6::7]
    return output
    
def list2pandasRelative(inputVector):
    output = pd.DataFrame(columns = ['U','sec','Nmeas'])
    nentries = int(len(inputVector)/3)  #The length of the vector
    output['U'] = inputVector[0::3]
    output['sec'] = inputVector[1::3]
    output['Nmeas'] = inputVector[2::3]
    return output