# -*- coding: utf-8 -*-

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


def strict_F1(query_dict, entities_xml):
    pass


def lazy_F1(parser):
    """
    :param parser:
    :return:
    """

    # count number true positive, flase positives and false negatives
    tp_strict = 0
    tp_lazy = 0
    tp = 0  
    fp = 0
    fn = 0

    for query in parser.query_array:
        set_entities_matched = []
        print("\n", query.search_string)
        for match in query.search_matches:
            is_matched = False

            #print("\n", "/"*30, "\n")
            #print("\n 1: match_found: ",match.entity.link)

            for true_match in query.true_entities:
                #TP
                #print("\n 2: true_match: ",get_entity_name(true_match.entity[0].link))
                if (match.entities[0].link == get_entity_name(true_match.entities[0].link)):
                    assert(not is_matched) #There should not be 2 identical true_entities
                    is_matched = True

                    
                    print("MATCH pos ", match.position, "-> ", match)
                    print("TRUTH pos ", true_match.position, "-> ", true_match.substring)

                    tp += 1
                    match.rating = "TP-Strict"
                    true_match.rating = "TP-Strict"

            if (not is_matched):
                #FP
                fp += 1
        for true_match in query.true_entities:
            is_matched = False
            for match in query.search_matches:
                if (match.entities[0].link == get_entity_name(true_match.entities[0].link)):
                    assert(not is_matched) #There should not be 2 identical search_matches
                    is_matched = True
            if ( not is_matched):
                #FN
                fn += 1
    #compute precision, recall and f1   
    precision = float(tp) / (tp + fp)
    recall = float(tp) / (tp + fn)
    f1 = 2 * float(precision * recall) / ( precision + recall)
    print("precision is: " + str(precision), "\n")
    print("recall is: " + str(recall), "\n")
    print("F1 is: " + str(f1), "\n")
    
