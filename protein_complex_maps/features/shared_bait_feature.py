
import argparse
import numpy as np
import pandas as pd
import scipy.stats as stats
import scipy.misc as misc
import math

pd.set_option('display.height', 1000)
pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def pval(k,n,m,N):
    print "%s %s %s %s" % (k,n,m,N)
    pv = 0.0
    for i in range(k,min(m,n)+1):
        pi = ( misc.comb(n,i) * misc.comb((N-n), (m-i)) ) / misc.comb(N,m)
        pv += pi
    return pv


def main():
    parser = argparse.ArgumentParser(description="Calculates pval for prey prey interactions in bait prey data")
    parser.add_argument("--input_feature_matrix", action="store", dest="feature_matrix", required=True, 
                                    help="Filename of input feature matrix")
    parser.add_argument("--output_file", action="store", dest="output_file", required=True, 
                                    help="Filename of output matrix")
    parser.add_argument("--sep", action="store", dest="sep", required=False, default='$',
                                    help="Separator for reading csv, default=$")
    parser.add_argument("--id_column", action="store", dest="id_column", required=False, default='gene_id',
                                    help="Name of column that specify ids in feature matrix, default=gene_id")
    parser.add_argument("--bait_id_column", action="store", dest="bait_id_column", required=False, default='bait_geneid',
                                    help="Name of column that specify bait ids in feature matrix, default=bait_geneid")

    args = parser.parse_args()

    feature_table = pd.read_csv(args.feature_matrix, sep=args.sep)
    output_df = shared_bait_feature(feature_table, args.bait_id_column, args.id_column)
    output_df.to_csv(args.output_file)

def shared_bait_feature(feature_table, bait_id_column, id_column):

    #kdrew: best to enforce ids as strings
    feature_table['bait_id_column_str'] = feature_table[bait_id_column].apply(str)

    #kdrew: merge table to itself to get pairs of proteins with same bait
    feature_shared_bait_table = feature_table.merge(feature_table, on='bait_id_column_str')

    print feature_shared_bait_table

    feature_shared_bait_table['gene_id1_str'] = feature_shared_bait_table[id_column+'_x'].apply(str)
    feature_shared_bait_table['gene_id2_str'] = feature_shared_bait_table[id_column+'_y'].apply(str)
    feature_shared_bait_table['frozenset_geneids'] = map(frozenset,feature_shared_bait_table[['gene_id1_str','gene_id2_str']].values)
    feature_shared_bait_table['frozenset_geneids_str_order'] = feature_shared_bait_table['frozenset_geneids'].apply(list).apply(sorted).apply(str)

    #kdrew: this way actually fails to deal with duplicate gene pairs properly, using above frozenset_geneids_str_order method
    ##kdrew: create set of id pairs (need set because merge generates duplicate gene pairs, also deals with order)
    #df_tmp = map(frozenset, feature_shared_bait_table[[args.id_column+'_x',args.id_column+'_y']].values)
    #feature_shared_bait_table['gene_id_set'] = df_tmp

    ##kdrew: generate tuple of set so groupby works, apparently cannot use cmp on sets
    #feature_shared_bait_table['gene_id_tup'] = feature_shared_bait_table['gene_id_set'].apply(tuple)


    ##kdrew: number of times pair is found (unique baits), 'k' in Hart etal 2007 
    #ks = feature_shared_bait_table.groupby('gene_id_tup')[args.bait_id_column].nunique()
    ##kdrew: number of times individual id is found (unique baits), 'm' and 'n' in Hart etal 2007 
    #ms = feature_shared_bait_table.groupby(args.id_column+'_x')[args.bait_id_column].nunique()
    ##kdrew: number of total experiments (unique baits), 'N' in Hart etal 2007 
    #N = feature_shared_bait_table[args.bait_id_column].nunique()

    #kdrew: number of times pair is found (unique baits), 'k' in Hart etal 2007 
    ks = feature_shared_bait_table.groupby('frozenset_geneids_str_order')['bait_id_column_str'].nunique()
    #kdrew: number of times individual id is found (unique baits), 'm' and 'n' in Hart etal 2007 
    ms = feature_shared_bait_table.groupby('gene_id1_str')['bait_id_column_str'].nunique()
    #kdrew: number of total experiments (unique baits), 'N' in Hart etal 2007 
    N = feature_shared_bait_table['bait_id_column_str'].nunique()

    #for gene_ids in bioplex_feature_shared_bait_table.gene_id_tup:
    output_dict = dict()
    output_dict['gene_id1'] = []
    output_dict['gene_id2'] = []
    output_dict['pair_count'] = []
    output_dict['neg_ln_pval'] = []
    print ks
    for gene_ids_str in ks.index:
        gene_ids_clean = gene_ids_str.translate(None, "[\'],")
        gene_ids = gene_ids_clean.split()
        if len(gene_ids) == 2:
            print gene_ids
            k = ks[gene_ids_str]
            m = ms[gene_ids[0]]
            n = ms[gene_ids[1]]
            #print k
            #print m
            #print n
            #p = stats.hypergeom.cdf(k, N, m, n)
            p = pval(k,n,m,N)
            neg_ln_p = -1.0*math.log(p)
            #print "%s k:%s n:%s m:%s -ln(p):%s" % (gene_ids, k, m, n, neg_ln_p)

            output_dict['gene_id1'].append(gene_ids[0])
            output_dict['gene_id2'].append(gene_ids[1])
            output_dict['pair_count'].append(k)
            output_dict['neg_ln_pval'].append(neg_ln_p)


    output_df = pd.DataFrame(output_dict)
    return output_df

if __name__ == "__main__":
    main()



