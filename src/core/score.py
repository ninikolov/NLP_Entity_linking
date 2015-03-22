# -*- coding: utf-8 -*-

from core.query import TermColor


def get_entity_name(url):
    """
    :param url str:
    :return: entity_name
    Entity_name is the last part of the wiki url( after last /)
    """
    entity_name = ""
    for char_pos in range(len(url) - 1, 0, -1):
        if ( url[char_pos] == "/"):
            return entity_name
        entity_name = url[char_pos] + entity_name


def F1_score(parser):
    """
    :param parser:
    :return:
    """

    # count number true positive, flase positives and false negatives
    tp_s = 0
    tp_l = 0
    tp = 0
    fp = 0
    fn = 0

    for query in parser.query_array:
        set_entities_matched = []
        for match in query.search_matches:
            if match.chosen_entity == -1:
                # disregard all matches where no entity chosen
                print("this entity wasnt chosen")
                continue

            is_matched = False

            # print("\n", "/"*30, "\n")
            # print("\n 1: match_found: ",match.entity.link)

            for true_match in query.true_entities:
                #TP
                #print("\n 2: true_match: ",get_entity_name(true_match.entity[0].link))
                if (match.entities[0].link == get_entity_name(true_match.entities[0].link)):
                    assert (not is_matched)  # There should not be 2 identical true_entities
                    is_matched = True

                    if (match.substring == true_match.substring):
                        match.rating = true_match.rating = "TP-strict"
                        tp_s += 1
                    else:
                        match.rating = true_match.rating = "TP-lazy"
                        tp_l += 1

            if (not is_matched):
                #FP
                match.rating = "FP"
                fp += 1
        for true_match in query.true_entities:
            is_matched = False
            for match in query.search_matches:
                if (match.entities[0].link == get_entity_name(true_match.entities[0].link)):
                    assert (not is_matched)  # There should not be 2 identical search_matches
                    is_matched = True
            if ( not is_matched):
                # FN
                fn += 1
                true_match.rating = "FN"

    # compute precision, recall and f1
    # in the strict, the TP-lazy are counted as false positives !
    precision_s = float(tp_s) / (tp_s + tp_l + fp)
    recall_s = float(tp_s) / (tp_s + fn)
    f1_s = 2 * float(precision_s * recall_s) / ( precision_s + recall_s)

    precision_l = float(tp_s + tp_l) / (tp_s + tp_l + fp)
    recall_l = float(tp_s + tp_l) / (tp_s + tp_l + fn)
    f1_l = 2 * float(precision_l * recall_l) / ( precision_l + recall_l)

    assert (precision_s <= precision_l)

    print("*" * 60)
    print("{0:<15} | {1:12} | {2:12} | {3:12}".format("SCORE", "precision", "recall", "F1"))
    print("-" * 60, "\n{0:<15} | {1:12} | {2:12} | {3}{4:12}{5}".format("LAZY",
                                                                        round(precision_l, 4), round(recall_l, 4),
                                                                        TermColor.BLUE, round(f1_l, 4), TermColor.END))
    print("{0:<15} | {1:12} | {2:12} | {3:12}".format("STRICT",
                                                      round(precision_s, 4), round(recall_s, 4), round(f1_s, 4)))
    print("*" * 60)


def F1_score_tagme(parser):
    """
    :param parser:
    :return:
    """
    # count number true positive, false positives and false negatives
    tp_s = 0
    tp_l = 0
    tp = 0
    fp = 0
    fn = 0
    for query in parser.query_array:
        for match in query.search_matches:
            if match.chosen_entity == -1:  # disregard all matches where no entity chosen
                print("this entity wasnt chosen")
                continue
            is_matched = False
            # print("\n", "/"*30, "\n")
            # print("\n 1: match_found: ",match.entity.link)
            for true_match in query.true_entities:
                # TP
                #print("\n 2: true_match: ",get_entity_name(true_match.entity[0].link))
                if (match.get_chosen_entity().link == get_entity_name(true_match.entities[0].link)):
                    #assert (not is_matched)  # There should not be 2 identical true_entities
                    is_matched = True
                    if (match.substring == true_match.substring):
                        match.rating = true_match.rating = "TP-strict"
                        tp_s += 1
                    else:
                        match.rating = true_match.rating = "TP-lazy"
                        tp_l += 1
            if (not is_matched):
                # FP
                match.rating = "FP"
                fp += 1
        for true_match in query.true_entities:
            is_matched = False
            for match in query.search_matches:
                if match.chosen_entity == -1:  # disregard all matches where no entity chosen
                    print("this entity wasnt chosen")
                    continue
                if (match.get_chosen_entity().link == get_entity_name(true_match.entities[0].link)):
                    # assert (not is_matched)  # There should not be 2 identical search_matches
                    is_matched = True
            if ( not is_matched):
                # FN
                fn += 1
                true_match.rating = "FN"
    # compute precision, recall and f1
    # in the strict, the TP-lazy are counted as false positives !
    precision_s = float(tp_s) / (tp_s + tp_l + fp)
    recall_s = float(tp_s) / (tp_s + fn)
    f1_s = 2 * float(precision_s * recall_s) / ( precision_s + recall_s)

    precision_l = float(tp_s + tp_l) / (tp_s + tp_l + fp)
    recall_l = float(tp_s + tp_l) / (tp_s + tp_l + fn)
    f1_l = 2 * float(precision_l * recall_l) / ( precision_l + recall_l)

    assert (precision_s <= precision_l)

    print("*" * 60)
    print("{0:<15} | {1:12} | {2:12} | {3:12}".format("SCORE", "precision", "recall", "F1"))
    print("-" * 60, "\n{0:<15} | {1:12} | {2:12} | {3}{4:12}{5}".format("LAZY",
                                                                        round(precision_l, 4), round(recall_l, 4),
                                                                        TermColor.BLUE, round(f1_l, 4), TermColor.END))
    print("{0:<15} | {1:12} | {2:12} | {3:12}".format("STRICT",
                                                      round(precision_s, 4), round(recall_s, 4), round(f1_s, 4)))
    print("*" * 60)

    
