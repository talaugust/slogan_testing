

def set_up_framings(slogans, index):
    science_slogans = [4, 6, 10, 12, 14, 18]
    learn_slogns = [1, 9, 16]
    fun_bored_slogans = [2, 3, 8, 13, 15]
    # bored_slogans = []
    compare_slogans = [5, 7, 11, 17]
    
    for s in slogans.iterrows():
        if s[1]['design_id'] in science_slogans:
            slogans.at[s[1][index], 'framing'] = 'science_framing'
        elif s[1]['design_id'] in learn_slogns:
            slogans.at[s[1][index], 'framing'] = 'self_learn_framing'
        elif s[1]['design_id'] in fun_bored_slogans:
            slogans.at[s[1][index], 'framing'] = 'fun_bored_framing'
        elif s[1]['design_id'] in compare_slogans:
            slogans.at[s[1][index], 'framing'] = 'compare_framing'
        