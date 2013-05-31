from decimal import Decimal
from math import *
from collections import OrderedDict
from copy import deepcopy
import json

def get_choicelist(choiceset, all_choices=False):
    lst = []
    if type(choiceset) is list: 
        lst = lst + choiceset
    else:
        for c in choiceset: 
            if all_choices: lst.append(c)          
            lst = lst + get_choicelist(choiceset[c], all_choices)
    return lst

def eval_function(func, parameters, variables):
    for p in parameters:
        exec '%s=%f'%(p,float(parameters[p]))
    for v in variables:
        exec '%s=%f'%(v,variables[v])
    return Decimal(eval(func))

class MultinomialLogit:
    Choiceset = None
    Parameter = None
    Variable = None
    Utility = None
    Availability = None
    Scale = None
    
    __final_choices = None
    __all_choices = None
    
    def calculate_logit_probability(self, choices, utility, availables, mu=1):
        probability = {}
        for c in choices:
            av = availables[c]
            ### mu = scales[c]
            probability[c] = Decimal(av) * Decimal(mu*utility[c]).exp()
        evsum = sum(probability.values())
        for choice in probability:
            probability[choice] = probability[choice]/evsum
            ##probability[choice] = choice+'*'
        return probability
    
    def calculate_probability(self, choiceset, utility, availables, scales, mu=1):
        probability = {}
        if type(choiceset) is list:
            ##print 'list=',choiceset
            probability = self.calculate_logit_probability(choiceset,utility,availables,mu)
        else:
            p1s = self.calculate_logit_probability(choiceset.keys(),utility,availables,mu)
            probability.update(p1s)
        
            for k in choiceset:
                p2s = self.calculate_probability(choiceset[k],utility,availables,scales,scales[k])
                for i in p2s:
                    probability[i] = p1s[k] * p2s[i]
                    ##print '%s=%s*%s'%(i,k,i)
    
        return probability
    
    def calculate_utility(self, result, choiceset, variables, scales):
        utility = {}
        if type(choiceset) is list:
            for c in choiceset:
                utility[c] = eval_function(self.Utility[c],self.Parameter,variables)
        else:
            for k in choiceset:
                u1 = eval_function(self.Utility[k],self.Parameter,variables)
                u2s = self.calculate_utility(result, choiceset[k], variables, scales)
                
                mu = scales[k]
                utility[k] = u1 + Decimal(sum([mu*Decimal(v).exp() for v in u2s.values()])).ln()/mu
                ###print k,'is calculated by',u2s.keys()
        result.update(utility)
        return utility
    
    def __pick_variable(self, data, default_value=0):
        variables = {}
        var_dict = self.Variable
        for k,v in var_dict.items():
            variables[k] = float(data[v]) if v in data else default_value
        return variables
    
    def __pick_choice_params(self, data, var_dict, default_value=1):
        params = {}
        choices = self.__all_choices
        for c in choices:
            if c in var_dict:
                v = var_dict[c]
                if v in data:
                    params[c] = float(data[v])
                else:
                    try:
                        params[c] = float(v)
                    except ValueError:
                        params[c] = default_value
            else:
                params[c] = default_value
        return params
    
    def simulate(self, data, verbose=False):
        if verbose: print data
        variables = self.__pick_variable(data)
        if verbose: print 'variables',variables
        availables = self.__pick_choice_params(data, self.Availability)
        if verbose: print 'availables',availables
        scales = self.__pick_choice_params(data, self.Scale)
        if verbose: print 'scales',scales
        
        utility = {}
        self.calculate_utility(utility, self.Choiceset, variables, scales)
        if verbose: print 'utility',utility
        
        probability = self.calculate_probability(self.Choiceset, utility, availables, scales)
        if verbose: print 'probability',probability
        
        final_choice = self.make_final_choice(probability)
        if verbose: print 'final_choice',final_choice
        
        return (utility,probability,final_choice)
    
    def make_final_choice(self, probability):
        ps = {}
        for c in self.__final_choices:
            ps[c] = probability[c]
        return max(ps.iterkeys(), key=(lambda key: ps[key]))
    
    def load_model(self, file_json):
        with open(file_json,'r') as f:
            model = json.load(f, object_pairs_hook=OrderedDict)
            
            ### compulsory
            self.Choiceset = deepcopy(model['Choiceset'])
            self.__final_choices = get_choicelist(self.Choiceset)
            self.__all_choices = get_choicelist(self.Choiceset,True)
            
            self.Parameter = OrderedDict(model['Parameter'])
            self.Variable = OrderedDict(model['Variable'])
            self.Utility = OrderedDict(model['Utility'])

            ### optional
            self.Availability = OrderedDict(model['Availability']) if 'Availability' in model else OrderedDict()
            self.Scale = OrderedDict(model['Scale']) if 'Scale' in model else OrderedDict()
    
    def save_model(self, file_json):
        with open(file_json,'w') as f:
            model = OrderedDict()
            model['Choiceset'] = self.Choiceset
            model['Parameter'] = self.Parameter
            model['Variable'] = self.Variable
            model['Utility'] = self.Utility
            
            if len(self.Availability)>0: model['Availability'] = self.Availability
            if len(self.Scale)>0: model['Scale'] = self.Scale
            
            json.dump(model, f, indent=4, separators=(',', ': '))
    
    def __repr__(self):
        return '\n'.join(['%s']*12) % ('Choiceset:', self.Choiceset,
                                        'Parameter:', self.Parameter,
                                        'Variable:', self.Variable,
                                        'Utility:', self.Utility,
                                        'Availability:', self.Availability,
                                        'Scale:', self.Scale)
    
if __name__ == "__main__":
    
    Data_Head = {}
    Data_Content = []
    with open('swissmetro.dat','rb') as f:
        import csv
        reader = csv.reader(f, delimiter='\t')
        header = reader.next()
        for i,c in enumerate(header):
            Data_Head[c] = i
        for row in reader: 
            data = {}
            for k,i in Data_Head.items():
                data[k] = row[i]
            break
    #print data
    
    ml = MultinomialLogit()
    ml.load_model('01logit.json')
    print ml.simulate(data)
    
    ml.Choiceset.append('fly')
    ml.save_model('01logit-2.json')
    