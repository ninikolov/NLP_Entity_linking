# -*- coding: utf-8 -*-

from core.query import TermColor


def calc_tp_fp_fn(parser, use_chosen_entity=False):
    """
    :param parser:
    :return:
    """
    # count number true positive, flase positives and false negatives
    parser.tp_s = 0
    parser.tp_l = 0
    parser.fp = 0
    parser.fn = 0

    # count amount of queries and matches checked
    parser.total_matches = 0
    parser.queries_with_some_identical_true_entities = 0

    for query in parser.query_array:
        set_entities_matched = []
        for match in query.search_matches:
            parser.total_matches += 1
            if match.chosen_entity == -1:
                # disregard all matches where no entity chosen
                print("this entity wasnt chosen")
                continue

            is_matched = False

            # print("\n", "/"*30, "\n")
            # print("\n 1: match_found: ",match.entity.link)

            for true_match in query.true_entities:
                if use_chosen_entity:
                    match_entity = match.get_chosen_entity()
                else:
                    match_entity = match.entities[0]
                #print("2: true_match: ",get_entity_name(true_match.entities[0].link))
                if (match_entity.link == true_match.entities[0].link):
                    #assert(not ) #There should not be 2 identical true_entities
                    if is_matched == True:
                        parser.queries_with_some_identical_true_entities += 1
                    #TODO: if there are a lot of queries with 2 identical true_entities, then 
                    #we should imlement a check for the real TP-strict true-entities 

                    if (match.substring == true_match.substring):
                        match.rating = true_match.rating = "TP-strict"
                        parser.tp_s += 1
                        #print("2 strict")
                    else:
                        match.rating = true_match.rating = "TP-lazy"
                        parser.tp_l += 1
                        #print("2 lazy")
                    is_matched = True

            if (not is_matched):
                match.rating = "FP"
                parser.fp += 1
        for true_match in query.true_entities:
            is_matched = False
            for match in query.search_matches:
                if match.chosen_entity == -1:
                    # disregard all matches where no entity chosen
                    print("this entity wasnt chosen")
                    continue
                if use_chosen_entity:
                    match_entity = match.get_chosen_entity()
                else:
                    match_entity = match.entities[0]
                if (match_entity.link == true_match.entities[0].link):
                    #assert(not is_matched) #There should not be 2 identical search_matches
                    is_matched = True
            if ( not is_matched):
                parser.fn += 1
                true_match.rating = "FN"


def print_F1(parser):
    # compute precision, recall and f1
    # in the strict, the TP-lazy are counted as false positives !

    precision_s = float(parser.tp_s) / (parser.tp_s + parser.tp_l + parser.fp)
    recall_s = float(parser.tp_s) / (parser.tp_s + parser.fn)
    f1_s = 2 * float(precision_s * recall_s) / ( precision_s + recall_s)

    precision_l = float(parser.tp_s + parser.tp_l) / (parser.tp_s + parser.tp_l + parser.fp)
    recall_l = float(parser.tp_s + parser.tp_l) / (parser.tp_s + parser.tp_l + parser.fn)

    f1_l = 2 * float(precision_l * recall_l) / ( precision_l + recall_l)

    assert (precision_s <= precision_l)
    print("*" * 60)
    print("{0}{1}{2}{3}{4}{5}".format(TermColor.BOLD, "Total queries :", len(parser.query_array),
                                      "; Total matches :", parser.total_matches, TermColor.END))
    if parser.queries_with_some_identical_true_entities > 0:
        print("(Queries with identical true entities: %s)" % (parser.queries_with_some_identical_true_entities))
    print("{0}{1}{2}{3}".format(TermColor.GREEN, parser.tp_s, " Strict True Positives", TermColor.END))
    print("{0}{1}{2}{3}".format(TermColor.YELLOW, parser.tp_l, " Lazy True Positives ", TermColor.END))
    print("{0}{1}{2}{3}".format(TermColor.RED, parser.fp, " False Positives", TermColor.END))
    print("{0}{1}{2}{3}".format(TermColor.RED, parser.fn, " False Negatives", TermColor.END))
    print("*" * 60)
    print("{0:<15} | {1:12} | {2:12} | {3:12}".format("SCORE", "precision", "recall", "F1"))
    print("-" * 60, "\n{0:<15} | {1:12} | {2:12} | {3}{4:12}{5}".format("LAZY",
                                                                        round(precision_l, 4), round(recall_l, 4),
                                                                        TermColor.BOLD, round(f1_l, 4), TermColor.END))
    print("{0:<15} | {1:12} | {2:12} | {3}{4:12}{5}".format("STRICT",
                                                            round(precision_s, 4), round(recall_s, 4), TermColor.BOLD,
                                                            round(f1_s, 4), TermColor.END))
    print("*" * 60)


    
