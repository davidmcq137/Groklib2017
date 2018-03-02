from __future__ import print_function
import cPickle as pickle

pf = open('read-remotes.pkl', 'rb')

Remote_Sys_List = pickle.load(pf)
Remote_Chan_List = pickle.load(pf)
Remote_Chan_Vals = pickle.load(pf)
Remote_Chan_Sys = pickle.load(pf)
watch_processes = pickle.load(pf)

pf.close()

print('len of Remote_Sys_List: ', len(Remote_Sys_List))
print('len of Remote_Chan_List: ', len(Remote_Chan_List))
print('len of Remote_Chan_Vals: ', len(Remote_Chan_Vals))
print('len of Remote_Chan_Sys: ', len(Remote_Chan_Sys))
print('len of watch_processes: ', len(watch_processes))    

print(Remote_Sys_List)
print('***********')
print(Remote_Chan_List)
print('***********')
print(Remote_Chan_Vals)
print('***********')
print(Remote_Chan_Sys)
print('***********')
print(watch_processes)





