
from conllu import parse_incr, parse_tree_incr
import sqlite3
import pymorphy2
import nltk
import time
nltk.download('punkt')

POS_TAGS = {'ADJ': 'Adj',
            'ADP': 'Prep',
            'ADV': 'Adv',
            'AUX': 'Verb',
            'CCONJ': 'Cconj',
            'DET': 'Pron',
            'INTJ': 'Intj',
            'NOUN': 'Noun',
            'NUM': 'Num',
            'PART': 'Part',
            'PRON': 'PronPers',
            'PROPN': 'Noun',
            'PUNCT': 'Punct',
            'SCONJ': 'Sconj',
            'SYM': 'Symb',
            'VERB': 'Verb',
            'X': 'X'}

POS_ATTRS = {'Sing': 'Sg',
             'Plur': 'Pl',
             'Imp': 'Ipfv',
             'Perf': 'Pfv',
             'Fut': 'Fut',
             'Past': 'Pst',
             'Pres': 'Pres'}


morph = pymorphy2.MorphAnalyzer()
con = sqlite3.connect('constr.db', timeout=10)  # подключение
cur = con.cursor()


cur.execute("""
CREATE TABLE data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sent_id INTEGER,
    word    TEXT,
    form    TEXT,
    lemma    TEXT,
    pos    TEXT,
    attr_1 TEXT,
    attr_2 TEXT, 
    head INTEGER,
    deprel TEXT
);""")

cur.execute("""
CREATE TABLE check_id (
    id INTEGER PRIMARY KEY
);""")


def persist_key_to(dict_db, key):
    cur.execute("""
        INSERT INTO data (sent_id, word, form, lemma, pos, attr_1, attr_2, head, deprel) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, key)
    dict_db.commit()


start = time.time()
sent_id = 0
for sentences in parse_incr(open('arzamas_403.txt')):
    if 'text' not in sentences.metadata.keys():
        continue
    # print(sentences.metadata['text'])
    for word in sentences:
        if '#' not in word:
            if word.get('upostag') == 'NOUN':
                try:
                    attr = (sent_id, word.get('form'), word.get('form').lower(), word.get('lemma'),
                            POS_TAGS[word.get('upostag')], word.get('feats')['Case'],
                            POS_ATTRS[word.get('feats')['Number']], word.get('head'), word.get('deprel'))
                except:
                    attr = (sent_id, word.get('form'), word.get('form').lower(), word.get('lemma'),
                            POS_TAGS[word.get('upostag')],'–',
                            '–', word.get('head'), word.get('deprel'))
            elif word.get('upostag') == 'VERB':
                try:
                    attr = (sent_id, word.get('form'), word.get('form').lower(), word.get('lemma'),
                            POS_TAGS[word.get('upostag')], POS_ATTRS[word.get('feats')['Aspect']],
                            POS_ATTRS[word.get('feats')['Tense']], word.get('head'), word.get('deprel'))
                except:
                    attr = (sent_id, word.get('form'), word.get('form').lower(), word.get('lemma'),
                            POS_TAGS[word.get('upostag')],'–',
                            '–', word.get('head'), word.get('deprel'))
            elif word.get('upostag') == 'PRON':
                try:
                    attr = (sent_id, word.get('form'), word.get('form').lower(), word.get('lemma'),
                            POS_TAGS[word.get('upostag')], word.get('feats')['Case'],
                            word.get('feats')['Person'], word.get('head'), word.get('deprel'))
                except:
                    attr = (sent_id, word.get('form'), word.get('form').lower(), word.get('lemma'),
                            POS_TAGS[word.get('upostag')],'–',
                            '–', word.get('head'), word.get('deprel'))
            elif word.get('upostag') == 'ADJ':
                try:
                    attr = (sent_id, word.get('form'), word.get('form').lower(), word.get('lemma'),
                            POS_TAGS[word.get('upostag')], word.get('feats')['Case'],
                            word.get('feats')['Degree'], word.get('head'), word.get('deprel'))
                except:
                    attr = (sent_id, word.get('form'), word.get('form').lower(), word.get('lemma'),
                            POS_TAGS[word.get('upostag')],'–',
                            '–', word.get('head'), word.get('deprel'))
            else:
                attr = (sent_id, word.get('form'), word.get('form').lower(), word.get('lemma'),
                        POS_TAGS[word.get('upostag')],'–', '–', word.get('head'), word.get('deprel'))
            persist_key_to(con, attr)
    sent_id += 1
    if sent_id % 1000 == 0:
        print('Обработано {} предложений'.format(sent_id))
cur.close()
end = time.time()
print(end - start)
