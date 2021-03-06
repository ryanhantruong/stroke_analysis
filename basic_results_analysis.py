import data_io
import pandas as pd
import parameters as param

# See files that are downloaded
# out = glob.glob(str(data_io.LOCAL_OUTPUT/
# f'times={times_path.stem}_hospitals={hospital_path.stem}_sex=*_age=*_race=*_symptom=*_nsim=*_*AHA.csv'))
# np.sort(out)

def get_basic_results(res_name):

    res = pd.read_csv(res_name,index_col='Location')
    center_cols = res.columns[9:]
    res['BestCenter'] = res[center_cols].idxmax(axis=1)
    res['BestCenterType'] = res['BestCenter'].apply(lambda x: "CSC" if x.split(' ')
                                                    [1] == '(CSC)' else "PSC")
    res['BestCenterKey'] = res['BestCenter'].apply(lambda x: x.split(' ')[0])
    return res, center_cols

BEST_CENTER_COLS = ['BestCenterKey','BestCenterType']

def read_agout(fname):
    return pd.read_csv(fname,header=[0,1],index_col=[0])

def _get_most_ce_strategy(agout):
    return agout.columns[agout.columns.get_level_values('Strategy').str.find('most C/E')>-1][0][0]

def get_variable_stats_from_aggregated_outcome(agout,var='QALY',strategies=None,suffixes=None):
    if strategies is None:
        # get most cost-effective strategy
        most_ce =  _get_most_ce_strategy(agout)
        for_join = agout.loc[var,most_ce].to_frame().T
        suffixes = ['af']
    # idx = pd.IndexSlice
    stats_df_l = []
    for strategy,suffix in zip(strategies,suffixes):
        stat_for_one_strategy = af_agout.loc[var,strategy].to_frame().T
        stat_for_one_strategy.drop("count",axis=1,inplace=True)
        stat_for_one_strategy.columns = [ '_'.join((c,var,suffix)) for c in stat_for_one_strategy.columns]
        stat_for_one_strategy[f"Strategy_{suffix}"] = strategy.replace('- most C/E','').strip()
        stats_df_l.append(stat_for_one_strategy)
    strategies_stats = pd.concat(stats_df_l,axis=1)
    return strategies_stats

for pid in range(500,501):
    print(pid)
    # get after AHA result
    res_name = list(data_io.LOCAL_OUTPUT.glob(f'pid={pid}*_afAHA.csv'))[0]
    a_res, center_cols = get_basic_results(res_name)
    # get before AHA result
    res_name = list(data_io.LOCAL_OUTPUT.glob(f'pid={pid}*_beAHA.csv'))[0]
    b_res, center_cols = get_basic_results(res_name)

    ab_res = b_res[BEST_CENTER_COLS].join(a_res[BEST_CENTER_COLS],
                                           rsuffix='_af',lsuffix='_be')
    # get list of all possible hospitals to go to, (where cell value is not nan)
    # ab_res = ab_res.join(
    #     pd.DataFrame.from_dict({
    #         idx: ','.join(center_cols[row.notna()])
    #         for idx, row in b_res[center_cols].iterrows()
    #     },
    #                            orient='index',
    #                            columns=['AllOptions']))
    ab_res.to_csv(
        data_io.BASIC_ANALYSIS_OUTPUT / res_name.stem.replace(
            'beAHA', 'summarized.csv'))

    # get changes
    changed_m = ab_res['BestCenterKey_be'] != ab_res['BestCenterKey_af']
    changed_res = ab_res[changed_m]
    changed_res.to_csv(
        data_io.BASIC_ANALYSIS_OUTPUT / res_name.stem.replace('beAHA','changed.csv'))

    qaly_stats_l = []
    for loc_id in changed_res.index:
        fname = list(data_io.LOCAL_OUTPUT.glob(f'pid={pid}*loc={loc_id}*afAHA*'))[0]
        af_agout = read_agout(fname)
        af_most_ce = _get_most_ce_strategy(af_agout)
        fname = list(data_io.LOCAL_OUTPUT.glob(f'pid={pid}*loc={loc_id}*beAHA*'))[0]
        be_agout = read_agout(fname)
        be_most_ce = _get_most_ce_strategy(be_agout)
        af_qaly_stats = get_variable_stats_from_aggregated_outcome(af_agout,'QALY',
                            [af_most_ce,be_most_ce.replace('- most C/E','').strip()],
                            suffixes=("af","be"))
        af_qaly_stats.index=[loc_id]
        # fname = list(data_io.LOCAL_OUTPUT.glob(f'pid={pid}*loc={loc_id}*beAHA*'))[0]
        # be_qaly_stats = get_variable_stats_from_aggregated_outcome(fname,'QALY')
        # be_qaly_stats.index=[loc_id]
        # qaly_stats = be_qaly_stats.join(af_qaly_stats,lsuffix='_be',rsuffix='_af')
        qaly_stats_l.append(af_qaly_stats)

    changed_res = changed_res.join(pd.concat(qaly_stats_l),how='left')
    changed_res.to_csv(
        data_io.BASIC_ANALYSIS_OUTPUT / res_name.stem.replace('beAHA','changed.csv'))
