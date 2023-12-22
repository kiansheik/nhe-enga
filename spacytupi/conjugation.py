import pandas as pd

def table_indicativo( verbo_tupi, show_subj = True ):
    pref_intr_df = pd.DataFrame( { '1ps':['a'] ,'1ppi':['îa'],'1ppe':['oro'],
                                   '2ps':['ere'],'2pp':['pe'] ,'3p':['o'] },
                                index = ['conjugacao'] )
    subject_intr_df = pd.DataFrame( { '1ps':['ixé '] ,'1ppi':['îandé '],'1ppe':['oré '],
                                   '2ps':['endé '],'2pp':['peê '] ,'3p':['a\'e '] },
                                index = ['conjugacao'] )
    pref_tr_df = pd.DataFrame( {'1ps': ['aîe' , ''  , ''  , 'oro', 'opo', 'aî'] ,
                                '1ppi':[''   , 'îaîe', ''  , 'oro', 'opo','îaî'],
                                '1ppe':[''   , ''  , 'oroîe', 'oro', 'opo','oroî'],
                                '2ps': ['xe ', 'îandé ','oré ', 'ereîe', ''  ,'ereî'],
                                '2pp': ['xe ', 'îandé ','oré ', ''  , 'peîe','peî'] ,
                                '3p':  ['xe ', 'îandé ','oré ', 'nde ', 'pe ','oî'] },
                                index = ['obj 1ps','obj 1ppi','obj 1ppe',
                                         'obj 2ps','obj 2pp','obj 3p'] )
    
    subject_tr_df = pd.DataFrame( {'1ps': ['îxé ','','','îxé ','îxé ','îxé '] ,
                                '1ppi':['','îandé ','','îandé ','îandé ','îandé '],
                                '1ppe':['','','oré ','oré ','oré ','oré '],
                                '2ps': ['', '','', 'endé ', '','endé '],
                                '2pp': ['', '','', '', 'peê ','peê '] ,
                                '3p':  ['a\'e ']*6 },
                                index = ['obj 1ps','obj 1ppi','obj 1ppe',
                                         'obj 2ps','obj 2pp','obj 3p'] )
    
    pref_tr_plr_df = pd.DataFrame( {'1ps': ['aîe', '', '', 'oro', 'opo', 'as'] ,
                                '1ppi':['', 'îaîe', '', 'oro', 'opo','îas'],
                                '1ppe':['', '', 'oroîe', 'oro', 'opo','oros'],
                                '2ps': ['xe r', 'îandé r','oré r', 'ereîe', '','eres'],
                                '2pp': ['xe r', 'îandé r','oré r', '', 'peîe','pes'] ,
                                '3p':  ['xe r', 'îandé r', 'oré r', 'nde r', 'pe r','os'] },
                                index = ['obj 1ps','obj 1ppi','obj 1ppe',
                                         'obj 2ps','obj 2pp','obj 3p'] )
    
    suf_tr_df =   pd.DataFrame( {'1ps':['', '', '', '', '', ''] ,
                                '1ppi':['', '', '', '', '', ''],
                                '1ppe':['', '', '', '', '', ''],
                                '2ps': ['îepé', 'îepé', 'îepé', '', '', ''],
                                '2pp': ['peîepé', 'peîepé', 'peîepé', '', '', ''] ,
                                '3p':  ['', '', '', '', '', ''] },
                                index = ['obj 1ps','obj 1ppi','obj 1ppe',
                                         'obj 2ps','obj 2pp','obj 3p'] )
    
    second_class_prefix_df = pd.DataFrame( { '1ps':['xe '] ,'1ppi':['îandé '],'1ppe':['oré '],
                                   '2ps':['nde '],'2pp':['pe '] ,'3p':['i '] },
                                index = ['conjugacao'] )
    
    second_class_plr_prefix_df = pd.DataFrame( { '1ps':['xe r'] ,'1ppi':['îandé r'],'1ppe':['oré r'],
                                   '2ps':['nde r'],'2pp':['pe r'] ,'3p':['s'] },
                                index = ['conjugacao'] )
    
    type = 0
    if ( "v" in verbo_tupi.verb_class ):
        if verbo_tupi.transitivo:
            type = 1
    elif ( "adj" in verbo_tupi.verb_class ):
        if verbo_tupi.pluriforme:
            type = 4
        else:
            type = 3

    print(show_subj)

    if type == 0:
        df_table = show_subj*subject_intr_df +pref_intr_df + verbo_tupi.verbete
    elif type == 1:
        df_table = show_subj*subject_tr_df + pref_tr_df +verbo_tupi.verbete+' '+suf_tr_df
        df_table = df_table.replace(verbo_tupi.verbete+' ', "--//--")
    elif type == 2:
        df_table = show_subj*subject_tr_df + pref_tr_plr_df + verbo_tupi.verbete+' '+suf_tr_df
        df_table = df_table.replace(verbo_tupi.verbete+' ', "--//--")
    elif type == 3:
        df_table = second_class_prefix_df + verbo_tupi.verbete
    elif type == 4:
        df_table = second_class_plr_prefix_df + verbo_tupi.verbete

    return df_table

def table_permissivo( verbo_tupi ):
    pref_intr_t_df = pd.DataFrame( { '1ps':["t'"] ,'1ppi':["t'"],'1ppe':["t'"],
                                   '2ps':["t'"],'2pp':["ta "] ,'3p':["t'"] },
                                index = ['conjugacao'] )
    
    pref_tr_df = pd.DataFrame( {'1ps': ["t'" ,"", "" , "t'", "t'", "t'"] ,
                                '1ppi':["" ,"t'", "" , "t'", "t'", "t'"] ,
                                '1ppe':["" ,"", "t'" , "t'", "t'", "t'"] ,
                                '2ps': ["ta " ,"t'", "t'" , "t'", "", "t'"] ,
                                '2pp': ["ta " ,"t'", "t'" , "", "ta ", "ta "]  ,
                                '3p':  ["ta " ,"t'", "t'" , "ta ", "ta ", "t'"]  },
                                index = ['obj 1ps','obj 1ppi','obj 1ppe',
                                         'obj 2ps','obj 2pp','obj 3p'] )
    
    second_class_t_df = pd.DataFrame( { '1ps':["ta "] ,'1ppi':["t'"],'1ppe':["t'"],
                                   '2ps':["ta "],'2pp':["ta "] ,'3p':["t'"] },
                                index = ['conjugacao'] )
    
    second_class_plr_t_df = pd.DataFrame( { '1ps':["ta "] ,'1ppi':["t'"],'1ppe':["t'"],
                                   '2ps':["ta "],'2pp':["ta "] ,'3p':["ta "] },
                                index = ['conjugacao'] )
    
    type = 0
    if ( "v" in verbo_tupi.verb_class ):
        if verbo_tupi.transitivo:
            type = 1
    elif ( "adj" in verbo_tupi.verb_class ):
        if verbo_tupi.pluriforme:
            type = 4
        else:
            type = 3
    
    if type == 1 or type == 2:
        return pref_tr_df + table_indicativo( verbo_tupi, False )
    elif type == 0:
        return pref_intr_t_df + table_indicativo( verbo_tupi, False )
    elif type == 3:
        return second_class_t_df + table_indicativo( verbo_tupi, False )
    elif type == 4:
        return second_class_plr_t_df + table_indicativo( verbo_tupi, False )

