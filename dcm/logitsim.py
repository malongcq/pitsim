import sys
import csv
import json
import datetime
import argparse
from decimal import Decimal
from math import *

def cal_probability(choices, utility, availability,mu=1):
    probability = {}
    for choice in choices:
        probability[choice] = Decimal(availability[choice]) * mu * Decimal(utility[choice]).exp()
    evsum = sum(probability.values())
    for choice in probability:
        probability[choice] = probability[choice]/evsum
        ##probability[choice] = choice+'*'
    return probability

def do_logit_probability(choiceset, utility, availability, mu=1):
    probability = {}
    if type(choiceset) is list:
        ##print 'list=',choiceset
        probability = cal_probability(choiceset,utility,availability,mu)
    else:
        p1s = cal_probability(choiceset.keys(),utility,availability,mu)
        probability.update(p1s)
        
        for k in choiceset:
            p2s = do_logit_probability(choiceset[k],utility,availability,mu)
            for i in p2s:
                probability[i] = p1s[k] * p2s[i]
                ##print '%s=%s*%s'%(i,k,i)
    
    return probability

def cal_utility(utl_func, params, data):
    for p in params:
        exec '%s=%f'%(p,float(params[p]))
    for v in data:
        exec '%s=%f'%(v,data[v])
    u = eval(utl_func)
    ### print '%s=%f'%(utl_func,u)
    return Decimal(u)

def do_logit_utility(result, choiceset, model_utility, params, data, mu=1):
    utility = {}
    if type(choiceset) is list:
        for choice in choiceset:
            utility[choice] = cal_utility(model_utility[choice],params,data)
    else:
        for k in choiceset:
            u1 = cal_utility(model_utility[k],params,data)
            u2s = do_logit_utility(result, choiceset[k], model_utility, params, data)
            utility[k] = u1 + Decimal(sum([mu*Decimal(v).exp() for v in u2s.values()])).ln()/mu
            ###print k,'is calculated by',u2s.keys()
    result.update(utility)
    return utility

def get_choicelist(choiceset, all_choices=False):
    lst = []
    if type(choiceset) is list:
        lst = lst + choiceset
    else:
        for c in choiceset: 
            if all_choices: lst.append(c)
            lst = lst + get_choicelist(choiceset[c], all_choices)
    return lst

def make_final_choice(final_choices, probability):
    ps = {}
    for c in final_choices:
        ps[c] = probability[c]
    return max(ps.iterkeys(), key=(lambda key: ps[key]))

def write_outfile_head(f_out, all_choices, input_head, with_input):
    if with_input:
        for col in input_head:
            f_out.write('\"%s\",'%(col))
    
    f_out.write(','.join(['\"Util.%s\",\"Prob.%s\"'%(c,c) for c in all_choices]))
    f_out.write('\n')
    #f_out.write(',\"Sim.Choice\"\n')

def write_outfile_row(f_out, all_choices, utility, probability, final_choice, row, with_input):
    if with_input:
        for col in row: f_out.write('\"%s\",'%(col))
        
    f_out.write(','.join(['\"%f\",\"%f\"'%(utility[c],probability[c]) for c in all_choices]))
    f_out.write('\n')
    #f_out.write(',\"%s\"\n'%final_choice)

def make_choice_availability(all_choices, availability, data, default_availability=1):
    avs = {}
    for c in all_choices:
        if c in availability:
            avs[c] = data[availability[c]]
        else:
            avs[c] = default_availability
    return avs

def get_row_subset(row, head, cols):
    data = {}
    for c in cols:
        col = cols[c]
        data[c] = float(row[head[col]])
    return data

def complete_availability(availability, all_choices, default_availability=1):
    for c in all_choices:
        if c in availability: continue
        availability[c] = default_availability

def do_main(file_model, file_csv, file_out, test_run=False, out_with_input=True):
    Data_Head = {}
    Data_Content = []
    with open(file_csv,'rb') as f:
        reader = csv.reader(f, delimiter='\t')
        header = reader.next()
        for i,c in enumerate(header):
            Data_Head[c] = i
        for row in reader: 
            Data_Content.append(row)
        Data_Content_len = len(Data_Content)
        print Data_Content_len, header
    
    Model = json.load(open(file_model))
    final_choices = get_choicelist(Model['Choiceset'])
    all_choices = get_choicelist(Model['Choiceset'], True)
    print 'final choices:',final_choices
    print 'all choices:',all_choices
    
    with open(file_out,'w') as f_out:
        write_outfile_head(f_out,all_choices,header,out_with_input)
        for idx,r in enumerate(Data_Content):
            data = get_row_subset(r, Data_Head, Model['Variable'])
            #print data
            
            availability = get_row_subset(r, Data_Head, Model['Availability'])
            complete_availability(availability, all_choices)
            #print availability
            
            choiceset = Model['Choiceset']

            utility = {}
            do_logit_utility(utility,choiceset,Model['Utility'],Model['Parameter'],data)
            ###print utility
        
            probability = do_logit_probability(choiceset,utility,availability)
            ###print probability
            
            final_choice = make_final_choice(final_choices, probability)
            #print final_choice
            
            write_outfile_row(f_out, all_choices, utility, probability, final_choice, r, out_with_input)
            
            if test_run: break
            sys.stdout.write('\r%d%%'%(100*idx/Data_Content_len))
            sys.stdout.flush()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("model", help="Model file in json format")
    parser.add_argument("input", help="input data file in csv format")
    parser.add_argument("output", help="output data file")
    parser.add_argument("--test", action="store_true",help="Test run, only process one iteration")
    args = parser.parse_args()
    
    Start = datetime.datetime.now()
    do_main(args.model,args.input,args.output, test_run=args.test)
    print '\rDone in %fs' %(datetime.datetime.now() - Start).total_seconds()